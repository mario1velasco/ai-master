"""Sesión 3 · Actividad en clase: ¿qué le pasa a esta herramienta?

El agente la usa mal o no la usa. Sin cambiar la función que hay debajo,
¿qué cambiaríais en el nombre, la descripción, los parámetros y lo que
devuelve? Tenéis 5 minutos.

Uso:  python -m sesion3.actividad_herramienta "¿Cuánto cuesta el serum de vitamina C?"
"""
import sys

from langchain_core.tools import tool

from comun import tienda
from comun.grafo import construir_agente
from comun.modelo_lc import crear_modelo


@tool
def fn_q(q: str, t: str = "p") -> str:
    """Consulta."""
    if t == "p":
        return str(tienda.PRODUCTOS) + str(tienda.PEDIDOS) + str(tienda.CLIENTES)  # todo, siempre
    return "Error 500"


if __name__ == "__main__":
    agente = construir_agente(crear_modelo(), [fn_q], "Eres el agente de Lumen Shop.")
    resultado = agente.invoke({"messages": [("user", sys.argv[1] if len(sys.argv) > 1 else input("Cliente: "))]})
    for m in resultado["messages"]:
        print(f"[{m.type}] {m.content or m.tool_calls}")
