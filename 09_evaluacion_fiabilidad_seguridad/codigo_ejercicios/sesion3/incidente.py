"""Sesión 3 · Actividad: análisis de un incidente (postmortem sin culpables).

Reconstruye la cronología del incidente T-77 a partir de los registros
(sesion3/incidente_T-77.jsonl) y deja las preguntas de la plantilla de
postmortem. La actividad se hace en grupo: el objetivo no es encontrar a
quién culpar, sino qué cambiar para que no vuelva a pasar.

Uso:  python -m sesion3.incidente
"""
import json
from pathlib import Path

RUTA = Path(__file__).with_name("incidente_T-77.jsonl")
ICONOS = {"inicio": "👤", "herramienta": "🔧", "fin": "🤖", "nota": "📝", "alerta": "🚨"}

PLANTILLA = [
    "1. ¿Qué pasó? Resume el incidente en dos frases y su impacto (dinero, datos, clientes).",
    "2. ¿Cuándo empezó y cuándo se detectó? ¿Cuánto tiempo pasó entre una cosa y otra?",
    "3. ¿Por qué pasó? Cinco porqués: del síntoma a la causa de fondo.",
    "4. ¿Qué capas de defensa faltaron? (permisos, guardarraíles, aprobación humana, alertas)",
    "5. ¿Qué cambiamos? Acciones concretas, con responsable, y un caso de regresión para que no vuelva.",
]


def cronologia(ruta: Path = RUTA) -> list[dict]:
    eventos = [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    return sorted(eventos, key=lambda e: e["ts"])


if __name__ == "__main__":
    print("🗂  Incidente T-77 · cronología reconstruida desde los registros\n")
    for e in cronologia():
        detalle = (e.get("pregunta") or e.get("texto") or e.get("respuesta")
                   or f"{e.get('herramienta')}({e.get('argumentos')}) [{e.get('riesgo')}]")
        print(f"  {e['ts'].replace('T', ' ')}  {ICONOS.get(e['evento'], '·')} {detalle}")
    print("\n📋 Plantilla de postmortem (sin culpables)\n")
    for pregunta in PLANTILLA:
        print(f"  {pregunta}")
