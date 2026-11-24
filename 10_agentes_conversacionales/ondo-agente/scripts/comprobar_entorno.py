"""Comprueba que tu entorno está listo para el Tema 10.

    python scripts/comprobar_entorno.py

Revisa: versión de Python, dependencias, fichero .env, clave del proveedor
del modelo (OpenAI o Anthropic, según LLM_PROVEEDOR, con una llamada mínima
que cuesta una fracción de céntimo), los embeddings de Ollama si
RAG_EMBEDDINGS=ollama, servidor MCP de Ondo y ngrok. No imprime nunca tus claves.
"""

import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
OK, KO, AVISO = "  ✔", "  ✘", "  !"
fallos = 0


def mal(msg):
    global fallos
    fallos += 1
    print(f"{KO} {msg}")


def comprobar_python():
    v = sys.version_info
    if sys.prefix == sys.base_prefix:
        mal("No estás dentro del entorno virtual. Actívalo (guía, «Antes de empezar») y vuelve a ejecutar este script")
    if v >= (3, 11):
        print(f"{OK} Python {v.major}.{v.minor}")
    else:
        mal(f"Python {v.major}.{v.minor}: necesitas 3.11 o superior (la guía de preparación recomienda 3.12)")


def comprobar_dependencias():
    try:
        import fastapi, langchain_openai, langgraph, mcp, telegram  # noqa: F401
        print(f"{OK} Dependencias instaladas")
    except ImportError as e:
        mal(f"Falta una dependencia ({e.name}). Activa el entorno virtual y ejecuta «python -m pip install -r requirements.txt»")


def comprobar_env():
    from dotenv import load_dotenv
    if not (RAIZ / ".env").exists():
        mal("No existe el fichero .env. Cópialo de .env.example y rellena tu clave")
        return False
    load_dotenv(RAIZ / ".env")
    proveedor = os.getenv("LLM_PROVEEDOR", "openai").strip().lower()
    variable, prefijo = ("ANTHROPIC_API_KEY", "sk-ant-") if proveedor == "anthropic" else ("OPENAI_API_KEY", "sk-")
    if not os.getenv(variable, "").startswith(prefijo):
        mal(f"{variable} no está en el .env o no empieza por «{prefijo}» (LLM_PROVEEDOR={proveedor})")
        return False
    print(f"{OK} Fichero .env con {variable} (LLM_PROVEEDOR={proveedor})")
    return True


def comprobar_modelo():
    try:
        from agente.llm import MODELO, PROVEEDOR, modelo
        r = modelo().invoke("Responde solo: ok")
        print(f"{OK} {PROVEEDOR} responde con el modelo {MODELO} ({r.content.strip()!r})")
    except Exception as e:  # noqa: BLE001
        mal(f"La llamada al modelo de chat falla: {type(e).__name__}: {str(e)[:160]}")


def comprobar_embeddings():
    if os.getenv("RAG_EMBEDDINGS", "openai").strip().lower() != "ollama":
        return  # con OpenAI vale la misma clave que ya se ha comprobado
    try:
        from ondo_mcp.conocimiento import MODELO_EMBEDDINGS, _embeddings
        n = len(_embeddings().embed_query("prueba"))
        print(f"{OK} Ollama calcula embeddings con {MODELO_EMBEDDINGS} ({n} dimensiones)")
    except Exception as e:  # noqa: BLE001
        mal(f"Los embeddings de Ollama fallan (¿está Ollama arrancado y hecho «ollama pull bge-m3»?): "
            f"{type(e).__name__}: {str(e)[:120]}")


async def _mcp():
    from agente.herramientas import conectar_ondo
    async with conectar_ondo() as h:
        r = await h.llamar("buscar_cliente", email="lucia.martin@example.com")
        assert r.get("encontrado"), r
        return len(h.tools)


def comprobar_mcp():
    try:
        n = asyncio.run(_mcp())
        print(f"{OK} Servidor MCP de Ondo con {n} herramientas")
    except Exception as e:  # noqa: BLE001
        mal(f"El servidor MCP de Ondo no arranca: {type(e).__name__}: {str(e)[:160]}")


def comprobar_ngrok():
    if not shutil.which("ngrok"):
        print(f"{AVISO} ngrok no está instalado (no lo necesitas hasta el día 3: guía de preparación, paso 5)")
        return
    r = subprocess.run(["ngrok", "config", "check"], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"{OK} ngrok instalado y configurado")
    else:
        print(f"{AVISO} ngrok instalado pero sin configurar: «ngrok config add-authtoken TU_TOKEN»")


if __name__ == "__main__":
    print("Comprobando el entorno del Tema 10...\n")
    comprobar_python()
    comprobar_dependencias()
    if comprobar_env():
        comprobar_modelo()
        comprobar_embeddings()
    comprobar_mcp()
    comprobar_ngrok()
    print()
    print("Todo listo." if not fallos else f"Hay {fallos} cosa(s) por arreglar: revisa la guía de preparación.")
    sys.exit(1 if fallos else 0)
