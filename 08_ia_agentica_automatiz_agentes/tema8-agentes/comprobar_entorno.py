"""Comprueba que el entorno está listo para las sesiones del Tema 8.

Uso:  python comprobar_entorno.py
"""
import sys

OK, FALLO = "✅", "❌"


def comprobar() -> bool:
    print("Comprobando el entorno del Tema 8...\n")

    if sys.version_info < (3, 10):
        print(f"{FALLO} Python {sys.version.split()[0]}: se necesita la versión 3.10 o superior.")
        return False
    print(f"{OK} Python {sys.version.split()[0]}")

    try:
        import dotenv  # noqa: F401
        import openai
        print(f"{OK} Librerías instaladas (openai {openai.__version__})")
    except ImportError as e:
        print(f"{FALLO} Falta una librería ({e.name}). Ejecuta: pip install -r requirements.txt")
        return False

    from comun.llm import BASE_URL, MODELO, crear_cliente
    print(f"   Proveedor: {BASE_URL}\n   Modelo:    {MODELO}")

    try:
        respuesta = crear_cliente().chat.completions.create(
            model=MODELO,
            messages=[{"role": "user", "content": "¿Qué hora es en Madrid? Usa la herramienta."}],
            tools=[{"type": "function", "function": {
                "name": "hora_actual", "description": "Devuelve la hora actual de una ciudad.",
                "parameters": {"type": "object", "properties": {"ciudad": {"type": "string"}},
                               "required": ["ciudad"]}}}],
        )
    except Exception as e:
        print(f"{FALLO} No se puede conectar con el modelo: {e}")
        print("   ¿Está Ollama abierto? ¿Has descargado el modelo con 'ollama pull'? Revisa tu archivo .env.")
        return False
    print(f"{OK} Conexión con el modelo")

    if not respuesta.choices[0].message.tool_calls:
        print(f"{FALLO} El modelo responde, pero no ha usado la herramienta.")
        print("   Prueba con otro modelo con soporte de tool calling (consulta la guía de instalación).")
        return False
    print(f"{OK} El modelo usa herramientas (tool calling)")
    return True


if __name__ == "__main__":
    listo = comprobar()
    print("\n🎉 Todo listo para el Tema 8." if listo else "\nRevisa los pasos marcados con ❌.")
    sys.exit(0 if listo else 1)
