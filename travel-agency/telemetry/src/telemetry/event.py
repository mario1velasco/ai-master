"""Evento JSONL: una línea por span, con el contexto de ejecución y las métricas del paso."""

import subprocess
from functools import cache
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, model_validator

from contracts.metrics import AgentMetrics, ApiMetrics, BaseMetrics, LlmCallMetrics, RagMetrics, SqlMetrics

EVENT_SCHEMA_VERSION = "event_v1"

# Clases de métricas que se saben releer. Cada clase nueva de contracts se añade aquí.
METRICS_TYPES: dict[str, type[BaseMetrics]] = {
    cls.__name__: cls for cls in (BaseMetrics, LlmCallMetrics, SqlMetrics, RagMetrics, AgentMetrics, ApiMetrics)
}


@cache
def git_commit() -> str | None:
    """Commit corto de git del código que se está ejecutando; None si no hay git. Se calcula una sola vez."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


class Event(BaseModel):
    """Un evento del log: contexto de ejecución + métricas de un span."""

    model_config = ConfigDict(extra="forbid")

    event_schema_version: str = Field(
        default=EVENT_SCHEMA_VERSION,
        description="Versión de este esquema de evento, para poder leer logs antiguos.",
    )
    environment: str = Field(min_length=1, description="Entorno en el que se ejecutó: local, test…")
    git_commit: str | None = Field(default=None, description="Commit corto de git del código ejecutado.")
    metrics_type: str = Field(description="Clase de las métricas, p. ej. 'LlmCallMetrics'; dice cómo releerlas.")
    metrics: SerializeAsAny[BaseMetrics] = Field(description="Métricas del span, de la clase que dice metrics_type.")

    @model_validator(mode="before")
    @classmethod
    def _parse_metrics_by_type(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("metrics"), dict):
            metrics_cls = METRICS_TYPES.get(data.get("metrics_type", ""))
            if metrics_cls is None:
                raise ValueError(f"metrics_type desconocido: {data.get('metrics_type')!r}")
            data = data | {"metrics": metrics_cls.model_validate(data["metrics"])}
        return data

    @model_validator(mode="after")
    def _check_metrics_type(self) -> Self:
        if type(self.metrics).__name__ != self.metrics_type:
            raise ValueError(f"metrics_type={self.metrics_type!r} no cuadra con {type(self.metrics).__name__}")
        return self

    @classmethod
    def from_metrics(cls, metrics: BaseMetrics, *, environment: str) -> Self:
        """Envuelve unas métricas en un evento con el contexto de ejecución actual."""
        return cls(
            environment=environment,
            git_commit=git_commit(),
            metrics_type=type(metrics).__name__,
            metrics=metrics,
        )
