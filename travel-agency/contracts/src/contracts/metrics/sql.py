"""Métricas de cada SQL que escribe el modelo: si pasó el validador y qué devolvió DuckDB."""

from typing import Self

from pydantic import Field, model_validator

from contracts.metrics.base import BaseMetrics


class SqlMetrics(BaseMetrics):
    """Métricas del span `sql.run`, uno por cada SQL que pide el modelo (una respuesta puede traer varios).

    La llamada al LLM va en su propio span. El validador valida y ejecuta a la vez, así que su duración es la
    `latency_ms` del span.
    """

    sql_valid: bool = Field(description="True si el SQL pasó el validador (solo SELECT, solo vistas permitidas…).")
    rejection_reason: str | None = Field(
        default=None,
        max_length=200,
        description="Por qué el validador lo rechazó; obligatorio si sql_valid es false.",
    )
    views_used: list[str] = Field(default_factory=list, description="Vistas DuckDB que lee el SQL.")
    sql_chars: int = Field(ge=0, description="Caracteres del SQL generado.")

    rows_returned: int | None = Field(default=None, ge=0, description="Filas devueltas; null si no se ejecutó.")
    column_count: int | None = Field(default=None, ge=0, description="Columnas devueltas; null si no se ejecutó.")
    limit_applied: bool = Field(default=False, description="True si el código añadió o recortó el LIMIT máximo.")
    timed_out: bool = Field(default=False, description="True si la consulta se cortó por tiempo máximo.")

    @model_validator(mode="after")
    def _check_validation(self) -> Self:
        if not self.sql_valid and self.rejection_reason is None:
            raise ValueError("sql_valid false necesita rejection_reason")
        if self.sql_valid and self.rejection_reason is not None:
            raise ValueError("sql_valid true no puede llevar rejection_reason")
        if not self.sql_valid and self.rows_returned is not None:
            raise ValueError("un SQL rechazado nunca se ejecuta: rows_returned debe ser null")
        return self
