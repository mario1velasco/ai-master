"""Métricas de una petición HTTP a la API."""

from http import HTTPMethod

from pydantic import Field

from contracts.metrics.base import BaseMetrics


class ApiMetrics(BaseMetrics):
    """Métricas del span raíz de cada petición (`api.<endpoint>`).

    La duración total es `latency_ms` y el identificador de la petición es `trace_id`: no se repiten aquí.
    """

    session_id: str | None = Field(default=None, description="Sesión de la conversación; null en /health.")
    endpoint: str = Field(
        min_length=1,
        description="Plantilla de la ruta, p. ej. '/sessions/{session_id}/messages', para agrupar peticiones.",
    )
    http_method: HTTPMethod = Field(description="Verbo HTTP de la petición recibida.")
    status_code: int = Field(ge=100, le=599, description="Código HTTP de la respuesta.")
    request_bytes: int = Field(ge=0, description="Tamaño del cuerpo de la petición.")
    response_bytes: int = Field(ge=0, description="Tamaño del cuerpo de la respuesta.")
    session_turn: int | None = Field(default=None, ge=1, description="Número de turno dentro de la sesión.")
    summary_applied: bool = Field(default=False, description="True si en este turno se resumió el historial.")
