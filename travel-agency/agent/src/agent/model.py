"""El modelo del agente para LangGraph, con la configuración del entorno.

Como `crear_modelo()` de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/modelo_lc.py` (`temperature 0`).
Desvío: `ChatOllama` (API nativa `/api/chat`) en vez de `ChatOpenAI` sobre `/v1`, para tener los tiempos de Ollama.
"""

import os
from collections.abc import Sequence
from typing import Any

import httpx
from langchain_core.messages import AIMessage, BaseMessage
from langchain_ollama import ChatOllama
from ollama import ResponseError

from contracts.errors import ComponentError
from contracts.metrics import FinishReason, LlmProvider, LlmPurpose, OllamaTimings

TIMEOUT_S = 600  # segundos, como `chat()` de text2sql (el timeout por defecto de chat() en S3)
NUM_PREDICT = 1024  # máximo de tokens de salida, como text2sql (01_preguntar_datos.py)


def base_url() -> str:
    """El Ollama de `OLLAMA_BASE_URL`, sin `/v1` (API nativa)."""
    return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def as_component_error(exc: Exception) -> ComponentError | None:
    """Traduce un error de `ChatOllama` al mismo código y mensaje que da `text2sql` (`_post` de `text2sql/ollama.py`,
    como `chat()` de `sesion_3/asistente/ollama.py`). None si no es un error de Ollama.

    `ChatOllama` pide en streaming: si no hay nadie escuchando, el cliente `ollama` deja pasar el `httpx.ConnectError`
    (sin streaming lo cambia por `ConnectionError`).
    """
    if isinstance(exc, httpx.ConnectError | ConnectionError):
        url = f"{base_url()}/api/chat"
        return ComponentError(
            "ollama_unavailable",
            "ollama",
            f"No hay respuesta de Ollama en {url}. ¿Está en marcha? (systemctl status ollama)",
        )
    model = model_name()
    if isinstance(exc, httpx.TimeoutException):
        return ComponentError("ollama_timeout", "ollama", f"{model} no respondió en {TIMEOUT_S} s.")
    if isinstance(exc, ResponseError):
        if exc.status_code == 404:
            return ComponentError(
                "model_not_installed", "ollama", f"Ollama no tiene el modelo {model}: ollama pull {model}"
            )
        return ComponentError("ollama_error", "ollama", f"Ollama devolvió {exc.status_code}: {exc.error[:300]}")
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
        num_predict=NUM_PREDICT,
        client_kwargs={"timeout": TIMEOUT_S},  # el cliente `ollama` se lo pasa a httpx
    )


def llm_call_fields(
    model: ChatOllama, messages: Sequence[BaseMessage], tools_offered: int, response: AIMessage
) -> dict[str, Any]:
    """Los campos de `LlmCallMetrics` de una llamada al modelo del agente, como los de `chat()` de text2sql.

    Salen de la configuración del modelo y de la respuesta de `ChatOllama`: `response_metadata` trae el JSON final de
    `/api/chat` (tiempos de Ollama, tokens y `done_reason`).
    """
    metadata = response.response_metadata
    done_reason = metadata.get("done_reason")
    return {
        "provider": LlmProvider.ollama,
        "model": model.model,
        # El supuesto del ticket: route_tool si pide herramientas, answer si responde con texto
        "purpose": LlmPurpose.route_tool if response.tool_calls else LlmPurpose.answer,
        "temperature": model.temperature,
        "max_tokens": model.num_predict,
        "num_ctx": model.num_ctx,
        "message_count": len(messages),
        "system_prompt_chars": len(str(messages[0].content)),  # el nodo `agent` siempre empieza por el system
        "tools_offered": tools_offered,
        "tool_calls": [call["name"] for call in response.tool_calls],
        "input_tokens": metadata.get("prompt_eval_count") or 0,
        "output_tokens": metadata.get("eval_count") or 0,
        "finish_reason": done_reason if done_reason in FinishReason.__members__ else FinishReason.unknown,
        "ollama": OllamaTimings.from_ollama_response(metadata),
    }
