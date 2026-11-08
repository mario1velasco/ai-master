"""Resultado de `text2sql.ask()`: lo que recibe el agente cuando pide datos a la base."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contracts.metrics import SqlMetrics


class SqlStatus(StrEnum):
    """Cómo terminó la pregunta a la base."""

    ok = "ok"
    no_sql = "no_sql"  # el modelo respondió con texto sin pedir SQL (p. ej. «ese dato no existe»)
    sql_error = "sql_error"  # tras los reintentos, alguna consulta seguía sin pasar el validador


class SqlQuery(BaseModel):
    """Un SQL escrito por el modelo que pasó el validador, con lo que devolvió DuckDB."""

    model_config = ConfigDict(extra="forbid")

    sql: str = Field(min_length=1, description="El SQL tal como lo escribió el modelo.")
    columns: list[str] = Field(description="Columnas del resultado, en orden.")
    rows: list[dict[str, Any]] = Field(description="Filas del resultado (importes redondeados a 2 decimales).")
    truncated: bool = Field(default=False, description="True si DuckDB devolvió más filas y se recortó a 50.")
    metrics: SqlMetrics | None = Field(
        default=None, description="Métricas de su span `sql.run`; null solo si la telemetría no pudo registrarlas."
    )


class SqlResult(BaseModel):
    """Respuesta de text2sql a una pregunta: las consultas ejecutadas y sus filas, sin redactar."""

    model_config = ConfigDict(extra="forbid")

    status: SqlStatus = Field(description="Estado final de la pregunta.")
    queries: list[SqlQuery] = Field(default_factory=list, description="Consultas ejecutadas, en el orden pedido.")
    model_text: str | None = Field(
        default=None, description="Texto del modelo cuando respondió sin pedir SQL (p. ej. qué dato no existe)."
    )
    error: str | None = Field(
        default=None, description="Último mensaje del validador cuando el estado es sql_error (lo que vio el modelo)."
    )
    llm_calls: int = Field(ge=0, description="Llamadas al modelo que hicieron falta.")
