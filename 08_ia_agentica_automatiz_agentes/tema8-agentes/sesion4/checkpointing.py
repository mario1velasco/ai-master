"""Sesión 4 · Demo II: estado persistente con checkpointing.

Cada paso del grafo se guarda en una base de datos SQLite. Eso permite:
- Retomar una conversación aunque el proceso se haya reiniciado.
- Ver el historial de estados de un hilo.
- Volver a un punto anterior (time travel) y continuar desde ahí.

Uso:
  python -m sesion4.checkpointing --hilo ticket-42 "Soy jorge.ruiz@email.com, ¿cómo va mi pedido?"
  python -m sesion4.checkpointing --hilo ticket-42 "¿Y cuándo llegará?"      ← recuerda el contexto
  python -m sesion4.checkpointing --hilo ticket-42 --historial
  python -m sesion4.checkpointing --hilo ticket-42 --volver 3 "En realidad mi email es marta.lopez@email.com"
"""
import argparse
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from comun.grafo import construir_agente
from comun.herramientas_lc import LECTURA
from comun.modelo_lc import crear_modelo

RUTA_BD = Path("datos/checkpoints.sqlite")


def crear_agente(conexion, modelo=None):
    return construir_agente(modelo or crear_modelo(), LECTURA,
                            "Eres el agente de Lumen Shop. Usa las herramientas y no inventes datos.",
                            checkpointer=SqliteSaver(conexion))


def historial(agente, hilo: str) -> list:
    estados = list(agente.get_state_history({"configurable": {"thread_id": hilo}}))[::-1]
    for i, estado in enumerate(estados):
        ultimo = estado.values.get("messages", [None])[-1] if estado.values.get("messages") else None
        descripcion = "(inicio)" if ultimo is None else (ultimo.content or f"pide {[t['name'] for t in ultimo.tool_calls]}")
        print(f"  [{i}] {ultimo.type if ultimo else '-':>6} · {str(descripcion)[:80]}")
    return estados


def enviar(agente, hilo: str, mensaje: str, volver_a: int | None = None) -> str:
    config = {"configurable": {"thread_id": hilo}}
    if volver_a is not None:  # time travel: continuamos desde un checkpoint anterior
        config = historial(agente, hilo)[volver_a].config
        print(f"⏪ Continuando desde el estado {volver_a}")
    return agente.invoke({"messages": [("user", mensaje)]}, config)["messages"][-1].content


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hilo", required=True)
    parser.add_argument("mensaje", nargs="?")
    parser.add_argument("--historial", action="store_true")
    parser.add_argument("--volver", type=int, help="Índice del estado desde el que continuar")
    args = parser.parse_args()
    RUTA_BD.parent.mkdir(exist_ok=True)
    with sqlite3.connect(RUTA_BD, check_same_thread=False) as conexion:
        agente = crear_agente(conexion)
        if args.historial:
            historial(agente, args.hilo)
        else:
            print("🤖", enviar(agente, args.hilo, args.mensaje or input("Cliente: "), args.volver))
