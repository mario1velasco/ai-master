"""Demo 3 · Volver al equipo: qué ha pasado por dentro.

Muestra la línea temporal de un encargo: quién ha trabajado, cuándo se ha parado el
equipo esperando a la persona, qué ha aportado ella y cómo ha seguido el equipo. Lo saca
de los checkpoints que guarda LangGraph en datos/faro.sqlite.

Uso:
  python 03_historial.py                ← lista los encargos
  python 03_historial.py ENC-001        ← línea temporal de un encargo
  python 03_historial.py ENC-001 --checkpoints   ← además, cada estado guardado
"""
import argparse
from datetime import datetime

from faro import agencia
from faro.flujo import abrir_faro

parser = argparse.ArgumentParser()
parser.add_argument("encargo", nargs="?")
parser.add_argument("--checkpoints", action="store_true", help="Lista todos los estados guardados")
args = parser.parse_args()

with abrir_faro(mostrar=False) as faro:
    if not args.encargo:
        for e in faro.encargos():
            print(f"{e['id']}  {agencia.CLIENTES[e['cliente_id']]['nombre']:<16} {e['estado']}")
        raise SystemExit

    estado = faro.estado(args.encargo)
    historial = estado.get("historial", [])
    agentes = {"supervisor", "estratega", "redactor", "entregar"}
    print(f"🕒 Línea temporal de {args.encargo}\n")
    anterior = None
    espera_persona, trabajo_equipo = 0.0, 0.0
    for apunte in historial:
        momento = datetime.fromisoformat(apunte["cuando"])
        segundos = (momento - anterior).total_seconds() if anterior else 0
        if apunte["quien"] in agentes:
            trabajo_equipo += segundos
            icono = "🤖"
        else:
            espera_persona += segundos   # lo que ha tardado la persona en responder
            icono = "🙋"
        print(f"  {apunte['cuando'][11:19]}  +{segundos:6.0f} s  {icono} {apunte['quien']}: {apunte['que']}")
        anterior = momento

    if tarea := faro.tarea_pendiente(args.encargo):
        print(f"\n⏸️  Ahora mismo el equipo espera a una persona: {tarea['titulo']}")
    print(f"\n⏱️  Trabajo de los agentes: {trabajo_equipo:.0f} s · Espera a la persona: {espera_persona:.0f} s")
    tokens = estado.get("tokens", {})
    print(f"🔢 Tokens por agente: {tokens} · total {sum(tokens.values())}")
    if estado.get("datos_cliente"):
        print("\n📋 Lo que ha aportado la persona y han usado los agentes:")
        for pregunta, respuesta in estado["datos_cliente"].items():
            print(f"   · {pregunta}: {respuesta}")

    if args.checkpoints:
        # Cada paso del grafo es un checkpoint. Con su config se podría reanudar desde ese punto.
        snapshots = list(faro.equipo.get_state_history(faro._config(args.encargo)))[::-1]
        print(f"\n💾 {len(snapshots)} estados guardados:")
        for i, s in enumerate(snapshots):
            siguiente = ", ".join(s.next) or "fin"
            espera = " ⏸️ esperando a la persona" if any(t.interrupts for t in s.tasks) else ""
            print(f"  [{i:2}] siguiente: {siguiente:<10}{espera}")
