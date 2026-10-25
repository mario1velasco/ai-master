"""Tiempos internos que devuelve Ollama en cada respuesta de su API nativa (/api/chat, /api/generate)."""

from collections.abc import Mapping
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from contracts.metrics.base import check_or_fill

_NS_PER_MS = 1_000_000
_NS_PER_S = 1_000_000_000
COLD_START_THRESHOLD_MS = 500.0

_RAW_FIELDS = (
    "total_duration",
    "load_duration",
    "prompt_eval_count",
    "prompt_eval_duration",
    "eval_count",
    "eval_duration",
)


def _ns_to_ms(value: int | None) -> float | None:
    return None if value is None else round(value / _NS_PER_MS, 3)


def _rate(count: int | None, duration_ns: int | None) -> float | None:
    if count is None or not duration_ns:
        return None
    return round(count / (duration_ns / _NS_PER_S), 2)


class OllamaTimings(BaseModel):
    """Tiempos crudos de Ollama (en nanosegundos, con sus nombres) y sus derivados en ms y tokens/s."""

    model_config = ConfigDict(extra="forbid")

    total_duration: int | None = Field(default=None, ge=0, description="Tiempo total de la llamada en Ollama (ns).")
    load_duration: int | None = Field(default=None, ge=0, description="Tiempo cargando el modelo en memoria (ns).")
    prompt_eval_count: int | None = Field(default=None, ge=0, description="Tokens del prompt procesados.")
    prompt_eval_duration: int | None = Field(default=None, ge=0, description="Tiempo leyendo el prompt (ns).")
    eval_count: int | None = Field(default=None, ge=0, description="Tokens generados.")
    eval_duration: int | None = Field(default=None, ge=0, description="Tiempo generando la respuesta (ns).")

    total_ms: float | None = Field(default=None, ge=0, description="Derivado: total_duration en ms.")
    load_ms: float | None = Field(default=None, ge=0, description="Derivado: load_duration en ms.")
    prompt_eval_ms: float | None = Field(default=None, ge=0, description="Derivado: prompt_eval_duration en ms.")
    eval_ms: float | None = Field(default=None, ge=0, description="Derivado: eval_duration en ms.")
    prompt_tokens_per_second: float | None = Field(
        default=None, ge=0, description="Derivado: velocidad leyendo el prompt (tokens/s)."
    )
    eval_tokens_per_second: float | None = Field(
        default=None, ge=0, description="Derivado: velocidad generando (tokens/s)."
    )
    cold_start: bool | None = Field(
        default=None,
        description=f"Derivado: true si cargar el modelo tardó más de {COLD_START_THRESHOLD_MS:.0f} ms.",
    )

    @classmethod
    def from_ollama_response(cls, data: Mapping[str, Any]) -> Self:
        """Crea los tiempos a partir del JSON de respuesta de Ollama, ignorando el resto de claves."""
        return cls(**{name: data[name] for name in _RAW_FIELDS if data.get(name) is not None})

    @model_validator(mode="after")
    def _fill_derived(self) -> Self:
        load_ms = _ns_to_ms(self.load_duration)
        check_or_fill(self, "total_ms", _ns_to_ms(self.total_duration))
        check_or_fill(self, "load_ms", load_ms)
        check_or_fill(self, "prompt_eval_ms", _ns_to_ms(self.prompt_eval_duration))
        check_or_fill(self, "eval_ms", _ns_to_ms(self.eval_duration))
        check_or_fill(self, "prompt_tokens_per_second", _rate(self.prompt_eval_count, self.prompt_eval_duration))
        check_or_fill(self, "eval_tokens_per_second", _rate(self.eval_count, self.eval_duration))
        check_or_fill(self, "cold_start", None if load_ms is None else load_ms > COLD_START_THRESHOLD_MS)
        return self
