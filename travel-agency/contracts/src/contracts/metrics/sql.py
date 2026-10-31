"""Métricas de una consulta text-to-SQL completa: generar, validar y ejecutar."""

from typing import Self

from pydantic import Field, model_validator

from contracts.metrics.base import BaseMetrics


class SqlMetrics(BaseMetrics):
    """Métricas del span `text2sql.consultar`. El detalle de la llamada al LLM va en su propio span."""

    generation_ms: float | None = Field(default=None, ge=0, description="Tiempo del LLM generando el SQL.")
    validation_ms: float | None = Field(default=None, ge=0, description="Tiempo del validador.")
    execution_ms: float | None = Field(
        default=None, ge=0, description="Tiempo de DuckDB ejecutando; null si el SQL no se ejecutó."
    )

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
        if not self.sql_valid and (self.execution_ms is not None or self.rows_returned is not None):
            raise ValueError("un SQL rechazado nunca se ejecuta: execution_ms y rows_returned deben ser null")
        return self
