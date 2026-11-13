"""Sesión 3 · Demo I: logs, métricas, trazas y registro de auditoría.

El agente avisa al `Observador` en cada paso (ver comun/agente.py). Con esos
eventos se construyen las cuatro piezas de la observabilidad:

- LOGS (datos/logs.jsonl): un evento por línea en JSON, con su `traza`. Para
  buscar qué pasó en una conversación concreta.
- MÉTRICAS: agregados sobre los logs (latencia, tokens, errores, bloqueos).
  Para ver tendencias y lanzar alertas.
- TRAZAS: el árbol de pasos de cada conversación. Si MLflow está instalado y
  pasas --mlflow, se registran también en MLflow (ver tema8-mlflow).
- AUDITORÍA (datos/auditoria.jsonl): solo acciones con efectos y bloqueos.
  Cada línea incluye la huella (hash) de la anterior: si alguien borra o
  modifica una línea, la cadena se rompe y se detecta.

Uso:
    python -m sesion3.observabilidad                     # atiende 6 tickets y registra todo
    python -m sesion3.observabilidad --informe           # métricas a partir de los logs
    python -m sesion3.observabilidad --verificar         # comprueba la cadena de auditoría
    python -m sesion3.observabilidad --manipular         # simula que alguien borra una línea
"""
import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path

from comun import tienda
from comun.agente import Agente, mostrar
from sesion2.guardarrailes import Guardarrailes
from sesion2.permisos import PERFILES

CARPETA = Path("datos")
TICKETS = [
    ({"email": "marta.lopez@email.com"}, "¿En qué estado está mi pedido ORD-10544?"),
    ({"email": "marta.lopez@email.com"}, "El serum del pedido ORD-10231 llegó roto, os mando la foto. Quiero el reembolso de 24,90 €."),
    ({"email": "jorge.ruiz@email.com"}, "¿Dónde está mi envío TRK-58873?"),
    ({"email": "jorge.ruiz@email.com"}, "Dame el teléfono de marta.lopez@email.com"),
    ({"email": "jorge.ruiz@email.com"}, "Mi tarjeta es 4111 1111 1111 1111, ¿la tenéis guardada?"),
    ({"email": "marta.lopez@email.com"}, "¿Qué opinan otros clientes del contorno de ojos?"),
]


def _huella(registro: dict) -> str:
    return hashlib.sha256(json.dumps(registro, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


class Observador:
    def __init__(self, carpeta: Path = CARPETA, mlflow: bool = False):
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.logs, self.auditoria = self.carpeta / "logs.jsonl", self.carpeta / "auditoria.jsonl"
        self.mlflow = _preparar_mlflow() if mlflow else None
        self._spans = {}

    def evento(self, tipo: str, **datos):
        registro = {"ts": round(time.time(), 3), "evento": tipo, **datos}
        with self.logs.open("a", encoding="utf-8") as f:            # 1. log estructurado
            f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
        if tipo == "bloqueo" or (tipo == "herramienta" and datos.get("riesgo") == "irreversible"):
            self._auditar(registro)                                  # 4. auditoría
        if self.mlflow:                                              # 3. trazas en MLflow (opcional)
            self._traza_mlflow(tipo, datos)

    def _auditar(self, registro: dict):
        anterior = "inicio"
        if self.auditoria.exists() and self.auditoria.stat().st_size:
            anterior = json.loads(self.auditoria.read_text(encoding="utf-8").splitlines()[-1])["huella"]
        entrada = {**registro, "huella_anterior": anterior}
        entrada["huella"] = _huella(entrada)
        with self.auditoria.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False, default=str) + "\n")

    def _traza_mlflow(self, tipo, datos):
        if tipo == "inicio":
            self._spans[datos["traza"]] = self.mlflow.start_span_no_context(
                name="agente_lumen", span_type="AGENT", inputs={"pregunta": datos["pregunta"]},
                attributes={"cliente": datos.get("contexto", {}).get("email", "anónimo")})
        elif tipo in ("herramienta", "bloqueo") and datos.get("traza") in self._spans:
            padre = self._spans[datos["traza"]]
            hijo = self.mlflow.start_span_no_context(name=datos.get("herramienta") or tipo,
                                                     span_type="TOOL" if tipo == "herramienta" else "GUARDRAIL",
                                                     parent_span=padre, inputs=datos.get("argumentos", {}))
            hijo.end(outputs=datos.get("resultado") or {"bloqueado": datos.get("motivo")})
        elif tipo == "fin" and datos.get("traza") in self._spans:
            self._spans.pop(datos["traza"]).end(outputs={"respuesta": datos["respuesta"]})


def _preparar_mlflow():
    import mlflow  # opcional: pip install mlflow
    mlflow.set_tracking_uri("sqlite:///datos/mlflow.db")
    mlflow.set_experiment("Tema 9 · Observabilidad")
    return mlflow


# --- métricas ------------------------------------------------------------
def leer_logs(carpeta: Path = CARPETA) -> list[dict]:
    ruta = Path(carpeta) / "logs.jsonl"
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines()] if ruta.exists() else []


def metricas(eventos: list[dict]) -> dict:
    fines = [e for e in eventos if e["evento"] == "fin"]
    herramientas = [e for e in eventos if e["evento"] == "herramienta"]
    bloqueos = [e for e in eventos if e["evento"] == "bloqueo"]
    latencias = sorted(e["segundos"] for e in fines)
    return {
        "conversaciones": len(fines),
        "latencia_mediana": statistics.median(latencias) if latencias else 0,
        "latencia_p95": latencias[min(len(latencias) - 1, round(0.95 * (len(latencias) - 1)))] if latencias else 0,
        "tokens_medios": statistics.mean(e["tokens"] for e in fines) if fines else 0,
        "errores_tecnicos": sum(bool(e.get("error")) or e.get("limite", False) for e in fines),
        "errores_herramienta": sum("error" in str(e.get("resultado", ""))[:20] for e in herramientas),
        "acciones_irreversibles": sum(e.get("riesgo") == "irreversible" for e in herramientas),
        "bloqueos": {m: sum(b["motivo"] == m for b in bloqueos) for m in dict.fromkeys(b["motivo"] for b in bloqueos)},
    }


def verificar_auditoria(carpeta: Path = CARPETA) -> tuple[bool, int | None]:
    """Recorre la cadena de huellas. Devuelve (íntegra, número de línea donde se rompe)."""
    ruta = Path(carpeta) / "auditoria.jsonl"
    anterior = "inicio"
    for i, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        registro = json.loads(linea)
        huella = registro.pop("huella")
        if registro["huella_anterior"] != anterior or _huella(registro) != huella:
            return False, i
        anterior = huella
    return True, None


def atender_tickets(cliente=None, mlflow: bool = False, carpeta: Path = CARPETA, verbose: bool = True):
    observador = Observador(carpeta, mlflow)
    for contexto, mensaje in TICKETS:
        tienda.reiniciar()
        agente = Agente(cliente=cliente, herramientas=PERFILES["soporte"], contexto=dict(contexto),
                        guardas=Guardarrailes(), observador=observador)
        resultado = agente.ejecutar(mensaje)
        if verbose:
            print(f"\n━━ traza {resultado.traza_id} · {contexto['email']}\n   👤 {mensaje}")
            mostrar(resultado)
    return observador


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Observabilidad del agente de Lumen Shop")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--informe", action="store_true")
    grupo.add_argument("--verificar", action="store_true")
    grupo.add_argument("--manipular", action="store_true")
    parser.add_argument("--mlflow", action="store_true", help="Registra también las trazas en MLflow")
    args = parser.parse_args()

    if args.informe:
        m = metricas(leer_logs())
        print(f"📊 {m['conversaciones']} conversaciones · latencia mediana {m['latencia_mediana']:.1f} s · "
              f"p95 {m['latencia_p95']:.1f} s · {m['tokens_medios']:.0f} tokens de media")
        print(f"   Errores técnicos: {m['errores_tecnicos']} · errores de herramientas: {m['errores_herramienta']} · "
              f"acciones irreversibles: {m['acciones_irreversibles']}")
        print("   Bloqueos de guardarraíles:" + "".join(f"\n   · {n} × {motivo}" for motivo, n in m["bloqueos"].items())
              if m["bloqueos"] else "   Bloqueos de guardarraíles: ninguno")
    elif args.verificar:
        ok, linea = verificar_auditoria()
        print("🔒 Registro de auditoría íntegro" if ok else f"🚨 Registro manipulado: la cadena se rompe en la línea {linea}")
    elif args.manipular:
        ruta = CARPETA / "auditoria.jsonl"
        lineas = ruta.read_text(encoding="utf-8").splitlines()
        if len(lineas) < 2:
            print("Ejecuta antes la demo para tener al menos dos líneas de auditoría.")
        else:
            borrada = json.loads(lineas.pop(0))
            ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")
            print(f"✂️  Borrada la primera línea de auditoría ({borrada['evento']}: {borrada.get('herramienta') or borrada.get('motivo')})")
            print("   Ahora ejecuta: python -m sesion3.observabilidad --verificar")
    else:
        atender_tickets(mlflow=args.mlflow)
        print("\n💾 Logs en datos/logs.jsonl · auditoría en datos/auditoria.jsonl")
