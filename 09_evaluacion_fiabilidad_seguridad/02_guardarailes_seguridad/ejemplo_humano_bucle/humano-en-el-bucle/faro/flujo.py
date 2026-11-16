"""Cómo se ejecuta el equipo: encargos, pausas, avisos a la persona y reanudación.

El estado del equipo lo guarda LangGraph en SQLite (checkpoints). Además llevamos un
registro sencillo de encargos para la bandeja: estado, a quién está asignada la tarea
y desde cuándo espera. Lo usan las cuatro demos.
"""
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from faro import agencia, config
from faro.equipo import construir_equipo
from faro.utilidades import ahora

ICONOS = {"supervisor": "🧭", "estratega": "📊", "redactor": "✍️ ", "entregar": "📦"}
_cerrojo = threading.Lock()   # una ejecución del equipo cada vez sobre la misma base de datos

ESQUEMA = """CREATE TABLE IF NOT EXISTS encargos (
    id TEXT PRIMARY KEY, cliente_id TEXT, estado TEXT, asignado_a TEXT,
    esperando_desde TEXT, recordatorios INTEGER DEFAULT 0, creado TEXT, actualizado TEXT, error TEXT)"""


class Faro:
    """Une el equipo de agentes (grafo con checkpoints) y el registro de encargos."""

    def __init__(self, conexion: sqlite3.Connection, modelo=None, mostrar=True):
        self.bd = conexion
        self.bd.row_factory = sqlite3.Row
        self.bd.execute(ESQUEMA)
        self.equipo = construir_equipo(modelo or config.crear_modelo(), SqliteSaver(conexion))
        self.mostrar = mostrar

    # --- Registro de encargos ---------------------------------------------------
    def encargos(self) -> list[dict]:
        return [dict(f) for f in self.bd.execute("SELECT * FROM encargos ORDER BY creado DESC")]

    def encargo(self, id_encargo: str) -> dict | None:
        fila = self.bd.execute("SELECT * FROM encargos WHERE id = ?", (id_encargo,)).fetchone()
        return dict(fila) if fila else None

    def _actualizar(self, id_encargo: str, **campos):
        campos["actualizado"] = ahora()
        asignaciones = ", ".join(f"{k} = ?" for k in campos)
        self.bd.execute(f"UPDATE encargos SET {asignaciones} WHERE id = ?", (*campos.values(), id_encargo))
        self.bd.commit()

    def _nuevo_id(self) -> str:
        return f"ENC-{self.bd.execute('SELECT COUNT(*) FROM encargos').fetchone()[0] + 1:03d}"

    # --- Estado del equipo (lo guarda LangGraph) -------------------------------------
    @staticmethod
    def _config(id_encargo: str) -> dict:
        # el thread_id une todas las ejecuciones del mismo encargo: así vuelve al MISMO equipo
        return {"configurable": {"thread_id": id_encargo}, "recursion_limit": 60}

    def estado(self, id_encargo: str) -> dict:
        return self.equipo.get_state(self._config(id_encargo)).values

    def tarea_pendiente(self, id_encargo: str) -> dict | None:
        """Si el equipo está esperando a la persona, devuelve la tarea que le ha delegado."""
        snapshot = self.equipo.get_state(self._config(id_encargo))
        for tarea in snapshot.tasks:
            if tarea.interrupts:
                return tarea.interrupts[0].value
        return None

    # --- Ejecutar el equipo -------------------------------------------------------
    def nuevo_encargo(self, cliente_id: str, brief: str | None = None) -> str:
        if cliente_id not in agencia.CLIENTES:
            raise ValueError(f"Cliente desconocido: {cliente_id}. Clientes: {', '.join(agencia.CLIENTES)}")
        id_encargo = self._nuevo_id()
        self.bd.execute("INSERT INTO encargos (id, cliente_id, estado, creado, actualizado) VALUES (?, ?, ?, ?, ?)",
                        (id_encargo, cliente_id, "trabajando", ahora(), ahora()))
        self.bd.commit()
        encargo = {"id": id_encargo, "cliente_id": cliente_id, "brief": brief or agencia.CLIENTES[cliente_id]["brief"]}
        self._ejecutar(id_encargo, {"encargo": encargo, "historial": [], "tokens": {}})
        return id_encargo

    def responder(self, id_encargo: str, respuesta: dict):
        """La persona ha hecho su parte: el mismo equipo continúa donde lo dejó."""
        if not self.tarea_pendiente(id_encargo):
            raise ValueError(f"El encargo {id_encargo} no está esperando a ninguna persona")
        asignado = self.encargo(id_encargo)["asignado_a"] or agencia.PERSONA_POR_DEFECTO
        respuesta = respuesta | {"respondida_por": agencia.PERSONAS[asignado]["nombre"]}
        self._actualizar(id_encargo, estado="trabajando", esperando_desde=None)
        self._ejecutar(id_encargo, Command(resume=respuesta))

    def _ejecutar(self, id_encargo: str, entrada):
        with _cerrojo:
            try:
                # stream() devuelve lo que hace cada miembro del equipo según va ocurriendo
                for paso in self.equipo.stream(entrada, self._config(id_encargo), stream_mode="updates"):
                    for nodo, cambios in paso.items():
                        for apunte in (cambios or {}).get("historial", []) if isinstance(cambios, dict) else []:
                            self._mostrar(apunte)
            except Exception as e:  # nunca perder un encargo: si algo falla, queda registrado
                self._actualizar(id_encargo, estado="error", error=str(e)[:500])
                if self.mostrar:
                    print(f"❌ Error en {id_encargo}: {e}")
                return
        if tarea := self.tarea_pendiente(id_encargo):
            asignado = self.encargo(id_encargo)["asignado_a"] or agencia.PERSONA_POR_DEFECTO
            self._actualizar(id_encargo, estado="esperando_persona", asignado_a=asignado,
                             esperando_desde=ahora(), recordatorios=0)
            # El aviso se envía AQUÍ, fuera del grafo: dentro del nodo se repetiría al reanudar
            avisar(id_encargo, tarea, asignado)
            if self.mostrar:
                print(f"⏸️  El equipo espera a {agencia.PERSONAS[asignado]['nombre']}: {tarea['titulo']}")
        else:
            estado = self.estado(id_encargo)
            self._actualizar(id_encargo, estado="terminado")
            guardar_entrega(id_encargo, estado.get("entrega", ""))
            if self.mostrar:
                print(f"✅ Encargo terminado. Propuesta en entregas/{id_encargo}.md")

    def _mostrar(self, apunte: dict):
        if self.mostrar:
            icono = ICONOS.get(apunte["quien"], "🙋")
            print(f"{icono} {apunte['quien']}: {apunte['que']}")

    # --- Plazos (demo 4) -----------------------------------------------------------
    def horas_esperando(self, encargo: dict, ahora_simulado: datetime | None = None) -> float:
        if not encargo.get("esperando_desde"):
            return 0.0
        desde = datetime.fromisoformat(encargo["esperando_desde"])
        return ((ahora_simulado or datetime.now()) - desde).total_seconds() / 3600

    def recordar(self, id_encargo: str):
        encargo = self.encargo(id_encargo)
        self._actualizar(id_encargo, recordatorios=encargo["recordatorios"] + 1)
        avisar(id_encargo, self.tarea_pendiente(id_encargo), encargo["asignado_a"], recordatorio=True)

    def escalar(self, id_encargo: str, a: str):
        self._actualizar(id_encargo, asignado_a=a, recordatorios=1)   # el email de escalado ya cuenta como aviso
        avisar(id_encargo, self.tarea_pendiente(id_encargo), a, escalado=True)


@contextmanager
def abrir_faro(modelo=None, mostrar=True):
    config.RUTA_BD.parent.mkdir(exist_ok=True)
    conexion = sqlite3.connect(config.RUTA_BD, check_same_thread=False, timeout=30)
    conexion.execute("PRAGMA journal_mode=WAL")   # varios procesos (demos y bandeja) a la vez
    try:
        yield Faro(conexion, modelo, mostrar)
    finally:
        conexion.close()


# --- Avisos por email (simulados) y entregas -----------------------------------------
def avisar(id_encargo: str, tarea: dict, persona_id: str, recordatorio=False, escalado=False) -> str:
    """Escribe en buzon/ el email que recibiría la persona. En empresa este es el canal habitual."""
    persona = agencia.PERSONAS[persona_id]
    prefijo = "Recordatorio: " if recordatorio else "Escalado: " if escalado else ""
    cuerpo = (f"Hola, {persona['nombre'].split()[0]}:\n\n"
              + ("La tarea sigue pendiente y el equipo de agentes está parado esperándote.\n\n" if recordatorio else "")
              + ("Te llega porque la persona asignada no ha respondido a tiempo.\n\n" if escalado else "")
              + f"El equipo de agentes necesita que hagas esto en el encargo {id_encargo} "
              f"({tarea['cliente']}):\n\n  {tarea['titulo']}\n\n{tarea['instrucciones']}\n\n"
              f"Respóndela en la bandeja: {config.URL_BANDEJA}/encargo/{id_encargo}\n\n— El equipo de agentes de Faro Digital\n")
    config.CARPETA_BUZON.mkdir(exist_ok=True)
    nombre = f"{datetime.now():%Y%m%d-%H%M%S-%f}_{id_encargo}_{persona_id}.txt"
    (config.CARPETA_BUZON / nombre).write_text(
        f"Para: {persona['email']}\nAsunto: [Faro] {prefijo}{tarea['titulo']} · {id_encargo}\n\n{cuerpo}", encoding="utf-8")
    return nombre


def guardar_entrega(id_encargo: str, texto: str):
    config.CARPETA_ENTREGAS.mkdir(exist_ok=True)
    (config.CARPETA_ENTREGAS / f"{id_encargo}.md").write_text(texto, encoding="utf-8")
