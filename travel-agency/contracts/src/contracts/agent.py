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


class Session(BaseModel):
    """Quién habla con el agente: el `contexto` de la sesión de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/
    comun/agente.py`. Lo pone quien llama (el comando, la API), nunca el modelo.

    `role` elige el perfil de herramientas, como `perfil(contexto)` del caso Hoteles Albor; es texto libre para que un
    rol sin chat llegue al agente y lo rechace con su código.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    client_id: str = Field(min_length=1, description="Cliente identificado en esta sesión, p. ej. 'C-001'.")
    role: str = Field(default="client", min_length=1, description="Rol de la sesión: hoy solo 'client' tiene chat.")


class BlockType(StrEnum):
    """En qué punto de control se bloqueó o se modificó algo (la `etapa` del registro de clase)."""

    input = "input"
    tool = "tool"
    output = "output"


class Block(BaseModel):
    """Algo que los guardarraíles bloquearon o modificaron en el turno, con su motivo."""

    model_config = ConfigDict(extra="forbid")

    type: BlockType = Field(description="Punto de control: entrada, herramienta o salida.")
    reason: str = Field(min_length=1, description="Motivo, p. ej. 'tarjeta enmascarada'.")


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
    blocks: list[Block] = Field(
        default_factory=list, description="Lo que bloquearon o modificaron los guardarraíles, en orden."
    )
    versions: Versions = Field(default_factory=Versions, description="Versiones de lo que influyó en la respuesta.")
    trace_id: str = Field(min_length=1, description="Traza del turno: en los logs están el detalle de cada paso.")
    metrics: AgentMetrics | None = Field(
        default=None, description="Métricas del span `agent.respond`; null si la telemetría no pudo registrarlas."
    )
