"""Sesión 3 · Demo II: un agente con herramientas de varias fuentes.

El Tema 6 explicó cómo funciona MCP. Aquí lo aplicamos: el agente combina
- las herramientas que expone el servidor MCP de Lumen Shop (las mantiene el
  equipo dueño del sistema y las pueden usar otros clientes: el IDE, Claude
  Desktop, otro agente...), y
- una herramienta local sobre una API externa (convertir_precio).

Si se añade una herramienta al servidor, el agente la usa en la siguiente
ejecución sin cambiar una línea de su código.

Uso:  python -m sesion3.agente_mcp "¿Cuánto cuesta el contorno de ojos en dólares y cuántas unidades quedan?"
"""
import asyncio
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient

from comun.apis_externas import convertir_precio
from comun.grafo import construir_agente
from comun.modelo_lc import crear_modelo

SERVIDORES = {"lumen-shop": {"command": sys.executable, "args": ["-m", "sesion3.servidor_mcp"],
                             "transport": "stdio"}}
HERRAMIENTAS_LOCALES = [convertir_precio]


async def preguntar(pregunta: str, modelo=None) -> str:
    remotas = await MultiServerMCPClient(SERVIDORES).get_tools()
    print("🔌 Herramientas del servidor MCP:", [h.name for h in remotas])
    print("🧰 Herramientas locales:", [h.name for h in HERRAMIENTAS_LOCALES])
    agente = construir_agente(modelo or crear_modelo(), remotas + HERRAMIENTAS_LOCALES,
                              "Eres el agente de Lumen Shop. Usa las herramientas y no inventes datos.")
    resultado = await agente.ainvoke({"messages": [("user", pregunta)]})
    return resultado["messages"][-1].content


if __name__ == "__main__":
    print("🤖", asyncio.run(preguntar(sys.argv[1] if len(sys.argv) > 1 else input("Cliente: "))))
