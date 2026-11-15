"""Resultado de `agent.respond()`: la respuesta del agente a una pregunta, con sus fuentes."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from contracts.metrics import AgentMetrics, Versions


class AgentStatus(StrEnum):
    """Cómo terminó el turno del agente."""

    ok = "ok"
    recursion_limit_reached = "recursion_limit_reached"  # se cortó al llegar al límite de pasos del grafo


class SourceType(StrEnum):
    """De dónde salen los datos de una fuente."""

    db = "db"


class Source(BaseModel):
    """Una consulta a la base que respaldó la respuesta."""

    model_config = ConfigDict(extra="forbid")

    type: SourceType = Field(description="Tipo de fuente (hoy solo la base de datos).")
    views: list[str] = Field(description="Vistas que leyó la consulta.")
    rows: int = Field(ge=0, description="Filas que devolvió la consulta (tras el recorte a 50).")
    sql: str = Field(
        min_length=1, description="El SQL que escribió text2sql, tal cual se ejecutó (los logs no lo guardan)."
    )


class AgentAnswer(BaseModel):
    """Respuesta del agente a una pregunta."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(description="Texto de la respuesta que redactó el modelo.")
    status: AgentStatus = Field(description="Estado final del turno.")
    answered_without_data: bool = Field(
        description="True si ninguna consulta a la base salió bien: la respuesta no se apoya en datos."
    )
    sources: list[Source] = Field(default_factory=list, description="Una por cada consulta que salió bien.")
    tools_used: list[str] = Field(
        default_factory=list, description="Herramientas distintas que usó el agente, en orden de primer uso."
    )
    versions: Versions = Field(default_factory=Versions, description="Versiones de lo que influyó en la respuesta.")
    trace_id: str = Field(min_length=1, description="Traza del turno: en los logs están el detalle de cada paso.")
    metrics: AgentMetrics | None = Field(
        default=None, description="Métricas del span `agent.respond`; null si la telemetría no pudo registrarlas."
    )
