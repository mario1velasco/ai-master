"""Sesión 2 · Comparativa: la misma tarea con cuatro estrategias.

Mide llamadas al modelo, tokens y tiempo de cada una. Ejecútalo varias veces:
con modelos pequeños los resultados varían bastante entre ejecuciones, y eso
también es parte de la lección.

Uso:  python -m sesion2.comparar_estrategias
"""
import sys

from comun.herramientas import FUNCIONES, HERRAMIENTAS
from comun.llm import crear_cliente
from comun.medidor import ClienteMedido
from sesion1.agente_minimo import ejecutar_agente
from sesion2.plan_and_execute import plan_and_execute
from sesion2.react_prompting import ejecutar_react
from sesion2.reflexion import responder_con_reflexion

TAREA = ("Soy marta.lopez@email.com. Quiero repetir exactamente mi último pedido. "
         "¿Tenéis stock de todo lo que pedí?")

ESTRATEGIAS = {
    "Tool calling nativo": lambda t, c: ejecutar_agente(t, cliente=c, herramientas=HERRAMIENTAS,
                                                        funciones=FUNCIONES, verbose=False),
    "ReAct prompting": lambda t, c: ejecutar_react(t, cliente=c, verbose=False),
    "Plan-and-execute": lambda t, c: plan_and_execute(t, cliente=c, verbose=False),
    "Con reflexión": lambda t, c: responder_con_reflexion(t, cliente=c, verbose=False),
}


def comparar(tarea: str = TAREA, crear=crear_cliente) -> dict:
    resultados = {}
    for nombre, estrategia in ESTRATEGIAS.items():
        cliente = ClienteMedido(crear())
        try:
            respuesta = estrategia(tarea, cliente)
        except Exception as e:
            respuesta = f"ERROR: {e}"
        resultados[nombre] = (cliente, respuesta)
        print(f"\n■ {nombre} — {cliente.resumen()}\n  {respuesta}")
    return resultados


if __name__ == "__main__":
    comparar(sys.argv[1] if len(sys.argv) > 1 else TAREA)
