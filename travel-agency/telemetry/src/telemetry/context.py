"""Traza y span activos, guardados en `contextvars` para que viajen solos por las llamadas anidadas.

Los IDs siguen el formato de OpenTelemetry (32 hex la traza, 16 hex el span) para exportarlos a MLflow tal cual.
"""

import secrets
from contextvars import ContextVar

current_trace: ContextVar[str | None] = ContextVar("trace_id", default=None)
current_span: ContextVar[str | None] = ContextVar("span_id", default=None)


def new_trace_id() -> str:
    """Devuelve un trace_id nuevo de 32 caracteres hex."""
    return secrets.token_hex(16)


def new_span_id() -> str:
    """Devuelve un span_id nuevo de 16 caracteres hex."""
    return secrets.token_hex(8)


def current_trace_id() -> str | None:
    """Devuelve el trace_id activo, o None si no hay ningún span abierto."""
    return current_trace.get()
