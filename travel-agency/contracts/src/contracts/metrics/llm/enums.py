"""Valores cerrados de las llamadas a un LLM."""

from enum import StrEnum


class LlmProvider(StrEnum):
    """Quién respondió la llamada."""

    ollama = "ollama"
    mock = "mock"


class LlmPurpose(StrEnum):
    """Para qué se llamó al LLM."""

    route_tool = "route_tool"
    generate_sql = "generate_sql"
    answer = "answer"
    summarize = "summarize"
    judge = "judge"
    other = "other"


class FinishReason(StrEnum):
    """Por qué dejó de generar el modelo."""

    stop = "stop"
    length = "length"
    tool_call = "tool_call"
    error = "error"
    unknown = "unknown"
