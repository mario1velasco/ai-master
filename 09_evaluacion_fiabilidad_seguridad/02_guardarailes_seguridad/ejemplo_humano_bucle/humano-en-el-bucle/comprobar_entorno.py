"""Comprueba que todo está listo para las demos de humano en el bucle del Tema 8.

Revisa, en este orden: la versión de Python, las librerías, la conexión con el modelo,
que el modelo sabe usar herramientas, que un grafo se puede pausar y reanudar
(interrupt + checkpoint en SQLite) y que el puerto de la bandeja está libre.

Uso:  python comprobar_entorno.py
"""
import os
import socket
import sqlite3
import sys

OK, FALLO = "✅", "❌"


def comprobar() -> bool:
    print("Comprobando el entorno de las demos de humano en el bucle...\n")

    # 1. Python
    if sys.version_info < (3, 10):
        print(f"{FALLO} Python {sys.version.split()[0]}: se necesita la versión 3.10 o superior.")
        return False
    print(f"{OK} Python {sys.version.split()[0]}")

    # 2. Librerías
    try:
        import fastapi
        import langgraph  # noqa: F401
        import uvicorn  # noqa: F401
        from importlib.metadata import version
        from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: F401
    except ImportError as e:
        print(f"{FALLO} Falta una librería ({e.name}). Activa el entorno y ejecuta: pip install -r requirements.txt")
        return False
    print(f"{OK} Librerías instaladas (langgraph {version('langgraph')}, fastapi {fastapi.__version__})")

    # 3. Modelo de lenguaje
    if not os.path.exists(".env"):
        print("   Aviso: no hay archivo .env; se usan los valores por defecto (Ollama en local).")
    from langchain_core.tools import tool

    from faro.config import BASE_URL, MODELO, crear_modelo
    print(f"   Proveedor: {BASE_URL}\n   Modelo:    {MODELO}")

    @tool
    def consultar_tarifas(canal: str) -> str:
        """Devuelve el coste de anunciarse en un canal, por ejemplo instagram_ads."""
        return "6,5 € por mil impresiones"

    try:
        respuesta = crear_modelo().bind_tools([consultar_tarifas]).invoke(
            "¿Cuánto cuesta anunciarse en instagram_ads? Usa la herramienta.")
    except Exception as e:
        print(f"{FALLO} No se puede conectar con el modelo: {e}")
        print("   ¿Está Ollama abierto? ¿Has descargado el modelo con 'ollama pull'? Revisa tu archivo .env.")
        return False
    print(f"{OK} Conexión con el modelo")
    if not respuesta.tool_calls:
        print(f"{FALLO} El modelo responde, pero no ha usado la herramienta.")
        print("   Usa un modelo con soporte de tool calling, por ejemplo qwen2.5:7b.")
        return False
    print(f"{OK} El modelo usa herramientas (tool calling)")

    # 4. Pausar y reanudar un grafo: lo que hace el equipo cuando delega en una persona
    from typing import TypedDict

    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Command, interrupt

    class Estado(TypedDict):
        respuesta: str

    def persona(estado: Estado):
        return {"respuesta": interrupt("¿Apruebas?")}

    grafo = StateGraph(Estado)
    grafo.add_node("persona", persona)
    grafo.add_edge(START, "persona")
    grafo.add_edge("persona", END)
    try:
        with sqlite3.connect(":memory:", check_same_thread=False) as conexion:
            app = grafo.compile(checkpointer=SqliteSaver(conexion))
            hilo = {"configurable": {"thread_id": "prueba"}}
            pausado = app.invoke({"respuesta": ""}, hilo)
            assert "__interrupt__" in pausado
            assert app.invoke(Command(resume="sí"), hilo)["respuesta"] == "sí"
    except Exception as e:
        print(f"{FALLO} LangGraph no puede pausar y reanudar un grafo: {e}")
        return False
    print(f"{OK} El grafo se pausa con interrupt() y se reanuda con Command(resume=...)")

    # 5. Puerto de la bandeja (no bloquea)
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", 8000)) == 0:
            print("   Aviso: el puerto 8000 ya está en uso. ¿Tienes la bandeja (o la sesión 6) abierta en otra terminal?")
    return True


if __name__ == "__main__":
    listo = comprobar()
    print("\n🎉 Todo listo. Sigue con la demo 1: python 01_delegar.py" if listo else "\nRevisa los pasos marcados con ❌.")
    sys.exit(0 if listo else 1)
