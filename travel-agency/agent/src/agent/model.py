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
    )
