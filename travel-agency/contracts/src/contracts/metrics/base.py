"""Métricas comunes a cualquier paso (span) de cualquier componente."""

import hashlib
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from contracts.metrics.enums import Component, Status

METRICS_SCHEMA_VERSION = "metrics_v1"

type AttributeValue = str | int | float | bool


def short_hash(text: str) -> str:
    """Devuelve los 16 primeros caracteres del sha256 de `text`.

    Sirve para agrupar entradas iguales en los logs sin guardar el texto.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def check_or_fill(model: BaseModel, field: str, expected: object) -> None:
    """Rellena un campo derivado o, si ya viene relleno (p. ej. al releer un JSONL), comprueba que cuadra.

    Los derivados son campos normales y no `computed_field`: con `extra="forbid"`, un `computed_field`
    aparece en `model_dump` pero hace fallar el `model_validate` de ese mismo volcado.
    """
    current = getattr(model, field)
    if current is None:
        setattr(model, field, expected)
    elif current != expected:
        raise ValueError(f"{field}={current!r} no cuadra con el valor calculado {expected!r}")


class Versions(BaseModel):
    """Versiones de todo lo que influye en el resultado de un paso."""

    model_config = ConfigDict(extra="forbid")

    prompt_version: str | None = Field(default=None, description="Versión del prompt usado, p. ej. 'agent_prompt_v1'.")
    schema_version: str | None = Field(default=None, description="Versión del esquema de salida esperado.")
    rules_version: str | None = Field(default=None, description="Versión de las reglas de negocio aplicadas.")
    dataset_version: str | None = Field(default=None, description="Versión del dataset (text2sql, eval).")
    corpus_version: str | None = Field(default=None, description="Versión del corpus documental del RAG.")
    index_version: str | None = Field(default=None, description="Versión del índice vectorial / BM25.")
    adapter_hash: str | None = Field(default=None, description="Hash del adaptador LoRA si el modelo está afinado.")
    package_version: str | None = Field(default=None, description="Versión del paquete que produjo la métrica.")


class BaseMetrics(BaseModel):
    """Métricas que lleva todo paso: traza, tiempos, resultado, tamaños y versiones."""

    model_config = ConfigDict(extra="forbid")

    metrics_schema_version: str = Field(
        default=METRICS_SCHEMA_VERSION,
        description="Versión de este esquema de métricas, para poder leer logs antiguos.",
    )

    trace_id: str = Field(
        min_length=1, description="Identificador de la petición completa; lo comparten todos sus pasos."
    )
    span_id: str = Field(min_length=1, description="Identificador de este paso dentro de la traza.")
    parent_span_id: str | None = Field(default=None, description="Paso que contiene a este; null si es la raíz.")
    component: Component = Field(description="Paquete o proceso que ejecutó el paso.")
    name: str = Field(
        min_length=1, max_length=120, description="Nombre del paso, p. ej. 'llm.text2sql' o 'sql.validar'."
    )

    started_at: datetime = Field(description="Inicio del paso, con zona horaria (UTC recomendado).")
    ended_at: datetime = Field(description="Fin del paso, con zona horaria.")
    latency_ms: float = Field(ge=0, description="Duración medida con perf_counter, en milisegundos.")

    status: Status = Field(description="Cómo terminó el paso: ok, error o rejected.")
    error_type: str | None = Field(
        default=None,
        max_length=120,
        description="Tipo de error (p. ej. '504_timeout'); obligatorio si status es error.",
    )
    error_message: str | None = Field(default=None, max_length=500, description="Mensaje de error recortado.")

    input_chars: int | None = Field(default=None, ge=0, description="Caracteres de la entrada del paso.")
    output_chars: int | None = Field(default=None, ge=0, description="Caracteres de la salida del paso.")
    input_hash: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{16}$",
        description="sha256 corto de la entrada (ver short_hash); agrupa entradas iguales sin guardar el texto.",
    )

    versions: Versions = Field(default_factory=Versions, description="Versiones de lo que influyó en el paso.")
    attributes: dict[str, AttributeValue] = Field(
        default_factory=dict,
        description="Métricas extra sin cambiar el esquema (equivalen a los span attributes de MLflow).",
    )

    @model_validator(mode="after")
    def _check_times_and_status(self) -> Self:
        if self.started_at.tzinfo is None or self.ended_at.tzinfo is None:
            raise ValueError("started_at y ended_at deben llevar zona horaria")
        if self.ended_at < self.started_at:
            raise ValueError("ended_at no puede ser anterior a started_at")
        if self.status is Status.error and self.error_type is None:
            raise ValueError("status 'error' necesita error_type")
        if self.status is Status.ok and self.error_type is not None:
            raise ValueError("status 'ok' no puede llevar error_type")
        return self
