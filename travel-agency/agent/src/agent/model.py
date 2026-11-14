"""El modelo del agente para LangGraph, con la configuración del entorno.

Como `crear_modelo()` de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/modelo_lc.py` (`temperature 0`).
Desvío: `ChatOllama` (API nativa `/api/chat`) en vez de `ChatOpenAI` sobre `/v1`, para tener los tiempos de Ollama.
"""

import os

from langchain_ollama import ChatOllama


def build_model() -> ChatOllama:
    """El modelo de `AGENT_MODEL` en el Ollama de `OLLAMA_BASE_URL` (sin `/v1`)."""
    return ChatOllama(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.environ.get("AGENT_MODEL", "qwen3:4b-instruct"),
        temperature=0,
        # Un único num_ctx y keep_alive para Qwen3-4B en todo el proyecto, los mismos que lee text2sql
        # (PROYECTO.md §5): si el agente pidiera otros, Ollama recargaría el modelo en cada pregunta.
        num_ctx=int(os.environ.get("OLLAMA_NUM_CTX", "8192")),
        keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE", "30m"),
        reasoning=False,  # sin modo razonamiento (`think: false`), como text2sql
    )
