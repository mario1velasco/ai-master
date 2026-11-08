"""Cliente mínimo de Ollama por la API nativa `/api/chat`.

Como `chat()` de `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/asistente/ollama.py`, con las
`tools` del bucle de `07_herramienta_funcion.py`. Se usa `requests`, como en clase, para ver qué se envía. Cada
llamada deja su evento `LlmCallMetrics` (span `llm.text2sql`) con los tiempos que da Ollama, los mismos que
`Respuesta.tiempos()` de S3.
"""

import os
from typing import Any

import requests

from contracts.metrics import Component, LlmCallMetrics, Versions
from contracts.metrics.llm import FinishReason, LlmProvider, LlmPurpose, OllamaTimings
from telemetry import span
from text2sql.prompt import PROMPT_VERSION


class ComponentError(Exception):
    """Un error que dice qué pieza ha fallado. Como `ErrorComponente` de S3, con el código en inglés."""

    def __init__(self, code: str, component: str, message: str) -> None:
        super().__init__(message)
        self.code, self.component, self.message = code, component, message

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "component": self.component, "message": self.message}


def _post(url: str, payload: dict[str, Any], model: str, timeout: int) -> requests.Response:
    """La petición y sus errores con nombre, como en `chat()` de S3."""
    try:
        r = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError as exc:
        raise ComponentError(
            "ollama_unavailable",
            "ollama",
            f"No hay respuesta de Ollama en {url}. ¿Está en marcha? (systemctl status ollama)",
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise ComponentError("ollama_timeout", "ollama", f"{model} no respondió en {timeout} s.") from exc
    if r.status_code == 404:
        raise ComponentError("model_not_installed", "ollama", f"Ollama no tiene el modelo {model}: ollama pull {model}")
    if r.status_code != 200:
        raise ComponentError("ollama_error", "ollama", f"Ollama devolvió {r.status_code}: {r.text[:300]}")
    return r


def chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]], *, retries: int = 0) -> dict[str, Any]:
    """Una llamada a /api/chat sin streaming. Devuelve el JSON de Ollama tal cual.

    `retries` es cuántos reintentos van antes de esta llamada; solo se apunta en las métricas.
    """
    url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/") + "/api/chat"
    model = os.environ.get("TEXT2SQL_MODEL", "qwen3:4b-instruct")
    timeout = 600  # segundos, como el timeout por defecto de chat() en S3
    temperature, num_predict = 0.0, 1024
    # Un único num_ctx y keep_alive para Qwen3-4B en todo el proyecto (PROYECTO.md §5): si text2sql y el agente
    # pidieran valores distintos, Ollama recargaría el modelo en cada pregunta (CTX_TEXTO de S3/config.py).
    num_ctx = int(os.environ.get("OLLAMA_NUM_CTX", "8192"))
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "stream": False,
        "think": False,
        "keep_alive": os.environ.get("OLLAMA_KEEP_ALIVE", "30m"),
        "options": {"temperature": temperature, "num_ctx": num_ctx, "num_predict": num_predict},
    }
    with span(
        "llm.text2sql",
        component=Component.text2sql,
        metrics_cls=LlmCallMetrics,
        versions=Versions(prompt_version=PROMPT_VERSION),
    ) as s:
        try:
            r = _post(url, payload, model, timeout)
        except ComponentError as exc:  # el span solo guarda el nombre de la clase: el código va aparte
            s.attributes["error_code"] = exc.code
            raise
        body = r.json()
        message = body.get("message") or {}
        done_reason = body.get("done_reason")
        s.fields.update(
            provider=LlmProvider.ollama,
            model=model,
            purpose=LlmPurpose.generate_sql,
            temperature=temperature,
            max_tokens=num_predict,
            num_ctx=num_ctx,
            message_count=len(messages),
            system_prompt_chars=len(messages[0]["content"]),  # ask() siempre empieza por el system
            tools_offered=len(tools),
            tool_calls=[call["function"]["name"] for call in message.get("tool_calls") or []],
            input_tokens=body.get("prompt_eval_count") or 0,
            output_tokens=body.get("eval_count") or 0,
            finish_reason=done_reason if done_reason in FinishReason.__members__ else FinishReason.unknown,
            retries=retries,
            ollama=OllamaTimings.from_ollama_response(body),
        )
    return body
