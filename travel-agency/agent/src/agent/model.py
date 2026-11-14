"""El modelo del agente para LangGraph, con la configuración del entorno.

Como `crear_modelo()` de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/modelo_lc.py` (`temperature 0`).
Desvío: `ChatOllama` (API nativa `/api/chat`) en vez de `ChatOpenAI` sobre `/v1`, para tener los tiempos de Ollama.
"""

import os

import httpx
from langchain_ollama import ChatOllama
from ollama import ResponseError

from text2sql import ComponentError


def base_url() -> str:
    """El Ollama de `OLLAMA_BASE_URL`, sin `/v1` (API nativa)."""
    return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def as_component_error(exc: Exception) -> ComponentError | None:
    """Traduce un error de `ChatOllama` al mismo código y mensaje que da `text2sql` (`_post` de `text2sql/ollama.py`,
    como `chat()` de `sesion_3/asistente/ollama.py`). None si no es un error de Ollama.

    `ChatOllama` pide en streaming: si no hay nadie escuchando, el cliente `ollama` deja pasar el `httpx.ConnectError`
    (sin streaming lo cambia por `ConnectionError`).
    """
    url = f"{base_url()}/api/chat"
    if isinstance(exc, httpx.ConnectError | ConnectionError):
        return ComponentError(
            "ollama_unavailable",
            "ollama",
            f"No hay respuesta de Ollama en {url}. ¿Está en marcha? (systemctl status ollama)",
        )
    if isinstance(exc, ResponseError) and exc.status_code == 404:
        model = model_name()
        return ComponentError(
            "model_not_installed", "ollama", f"Ollama no tiene el modelo {model}: ollama pull {model}"
        )
    return None


def model_name() -> str:
    """El modelo del agente, `AGENT_MODEL`."""
    return os.environ.get("AGENT_MODEL", "qwen3:4b-instruct")


def build_model() -> ChatOllama:
    """El modelo de `AGENT_MODEL` en el Ollama de `OLLAMA_BASE_URL` (sin `/v1`)."""
    return ChatOllama(
        base_url=base_url(),
        model=model_name(),
        temperature=0,
        # Un único num_ctx y keep_alive para Qwen3-4B en todo el proyecto, los mismos que lee text2sql
        # (PROYECTO.md §5): si el agente pidiera otros, Ollama recargaría el modelo en cada pregunta.
        num_ctx=int(os.environ.get("OLLAMA_NUM_CTX", "8192")),
        keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE", "30m"),
        reasoning=False,  # sin modo razonamiento (`think: false`), como text2sql
    )
