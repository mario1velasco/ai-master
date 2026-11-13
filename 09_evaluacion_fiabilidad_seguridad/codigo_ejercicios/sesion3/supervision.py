"""Sesión 3 · Supervisión humana con políticas: quién decide cada acción.

En el Tema 8 una persona aprobaba TODOS los reembolsos. Con cientos de tickets
al día eso no escala: la persona acaba aprobando sin mirar. La alternativa es
una política explícita, escrita en código, que decide para cada acción:

- automático:  riesgo bajo, el agente actúa solo (y queda en la auditoría)
- aprobación:  la acción espera en una cola hasta que una persona decide
- bloqueado:   no se hace nunca, lo pida quien lo pida

Y para lo que se resuelve en automático, una MUESTRA aleatoria pasa a
revisión humana: así se detectan fallos que ninguna regla había previsto.

Uso:
    python -m sesion3.supervision                    # tres reembolsos de distinto importe
    python -m sesion3.supervision --pendientes       # la cola de aprobaciones
    python -m sesion3.supervision --aprobar A-1
    python -m sesion3.supervision --rechazar A-1 "falta la foto"
"""
import argparse
import json
import random
from pathlib import Path

from comun import tienda
from comun.agente import Agente, mostrar
from sesion2.guardarrailes import Guardarrailes
from sesion2.permisos import PERFILES

COLA = Path("datos/aprobaciones.json")
REVISION = Path("datos/revision_muestral.jsonl")
UMBRAL_AUTOMATICO = 20.0       # € · hasta aquí, el agente reembolsa solo
TASA_MUESTREO = 0.2            # 20 % de lo automático pasa a revisión humana


def politica(nombre: str, argumentos: dict) -> str:
    """La regla de supervisión, en un solo sitio y fácil de auditar."""
    if nombre == "emitir_reembolso":
        return "automatico" if float(argumentos.get("importe", 0)) <= UMBRAL_AUTOMATICO else "aprobacion"
    if nombre == "enviar_email":
        return "aprobacion"
    return "automatico"


def _leer_cola() -> list[dict]:
    return json.loads(COLA.read_text(encoding="utf-8")) if COLA.exists() else []


def _guardar_cola(cola: list[dict]):
    COLA.parent.mkdir(exist_ok=True)
    COLA.write_text(json.dumps(cola, ensure_ascii=False, indent=1), encoding="utf-8")


class GuardarrailesConSupervision(Guardarrailes):
    """Los guardarraíles de la sesión 2 + la política: lo que requiere aprobación va a la cola."""

    def __init__(self, *a, semilla: int | None = None, **kw):
        super().__init__(*a, limite_reembolso=1e9, **kw)   # el límite ya no bloquea: lo decide la política
        self.azar = random.Random(semilla)

    def revisar_herramienta(self, nombre, argumentos, contexto):
        motivo = super().revisar_herramienta(nombre, argumentos, contexto)
        if motivo:
            return motivo                                 # bloqueado por las reglas de la sesión 2
        decision = politica(nombre, argumentos)
        if decision == "aprobacion":
            cola = _leer_cola()
            solicitud = {"id": f"A-{len(cola) + 1}", "herramienta": nombre, "argumentos": argumentos,
                         "cliente": contexto.get("email"), "estado": "pendiente"}
            _guardar_cola(cola + [solicitud])
            return self._anotar("supervision", f"queda pendiente de aprobación por una persona ({solicitud['id']}). "
                                               "Díselo al cliente; no está hecho todavía")
        if nombre == "emitir_reembolso" and self.azar.random() < TASA_MUESTREO:
            REVISION.parent.mkdir(exist_ok=True)
            with REVISION.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"herramienta": nombre, "argumentos": argumentos, "cliente": contexto.get("email")},
                                   ensure_ascii=False) + "\n")
        return None


def decidir(id_solicitud: str, aprobar: bool, motivo: str = "") -> dict:
    """Lo que hace la persona supervisora: si aprueba, se ejecuta la acción tal y como se pidió."""
    cola = _leer_cola()
    solicitud = next((s for s in cola if s["id"] == id_solicitud), None)
    if solicitud is None:
        raise SystemExit(f"No hay ninguna solicitud {id_solicitud}. Mira la cola con --pendientes")
    if solicitud["estado"] != "pendiente":
        raise ValueError(f"{id_solicitud} ya está {solicitud['estado']}")
    if aprobar:
        from comun.herramientas import CATALOGO
        solicitud["resultado"] = CATALOGO[solicitud["herramienta"]]["funcion"](**solicitud["argumentos"])
    solicitud.update(estado="aprobada" if aprobar else "rechazada", motivo=motivo)
    _guardar_cola(cola)
    return solicitud


ESCENARIOS = [
    ({"email": "jorge.ruiz@email.com"}, "El protector del pedido ORD-10598 vino abierto. Quiero un reembolso de 5 €."),
    ({"email": "marta.lopez@email.com"}, "El serum del pedido ORD-10231 llegó roto, os mando la foto. Quiero el reembolso de 24,90 €."),
    ({"email": "marta.lopez@email.com"}, "El pedido ORD-10544 llegó todo roto. Quiero que me devolváis 40,50 €."),
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supervisión humana con políticas")
    parser.add_argument("--pendientes", action="store_true")
    parser.add_argument("--aprobar")
    parser.add_argument("--rechazar", nargs=2, metavar=("ID", "MOTIVO"))
    args = parser.parse_args()
    if args.pendientes:
        for s in _leer_cola():
            print(f"  {s['id']} · {s['estado']:<10} · {s['herramienta']}({s['argumentos']}) · {s['cliente']}")
    elif args.aprobar:
        print("✅", decidir(args.aprobar, True))
    elif args.rechazar:
        print("❌", decidir(args.rechazar[0], False, args.rechazar[1]))
    else:
        print(f"📜 Política: reembolsos ≤ {UMBRAL_AUTOMATICO:.0f} € automáticos (el {TASA_MUESTREO:.0%} se revisa después); "
              "más, aprobación humana; por encima del total del pedido, bloqueado.")
        for contexto, mensaje in ESCENARIOS:
            tienda.reiniciar()
            print(f"\n━━ {contexto['email']}\n   👤 {mensaje}")
            agente = Agente(herramientas=PERFILES["soporte"], contexto=dict(contexto), guardas=GuardarrailesConSupervision())
            mostrar(agente.ejecutar(mensaje))
            if tienda.REEMBOLSOS:
                print(f"   💸 Emitido en automático: {tienda.REEMBOLSOS}")
        print("\n📥 Cola de aprobaciones: python -m sesion3.supervision --pendientes")
