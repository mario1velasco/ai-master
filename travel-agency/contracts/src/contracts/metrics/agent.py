"""Métricas de un turno completo del agente: totales de todos sus pasos."""

from typing import Self

from pydantic import Field, model_validator

from contracts.metrics.base import BaseMetrics, check_or_fill


class AgentMetrics(BaseMetrics):
    """Métricas del span `agent.responder`.

    Solo totales: el detalle de cada paso (cada llamada al LLM, cada herramienta) está en su propio span,
    colgando de este por `parent_span_id`. Así nada se guarda dos veces.
    """

    iterations: int = Field(ge=0, description="Vueltas del bucle agéntico.")
    llm_call_count: int = Field(ge=0, description="Llamadas al LLM en el turno.")
    tool_call_count: int = Field(ge=0, description="Llamadas a herramientas en el turno.")
    tools_used: list[str] = Field(
        default_factory=list, description="Herramientas distintas usadas, en orden de primer uso."
    )

    input_tokens: int = Field(ge=0, description="Suma de tokens de entrada de todas las llamadas al LLM.")
    output_tokens: int = Field(ge=0, description="Suma de tokens de salida de todas las llamadas al LLM.")
    total_tokens: int | None = Field(default=None, ge=0, description="Derivado: input_tokens + output_tokens.")

    llm_ms: float = Field(ge=0, description="Tiempo total en llamadas al LLM.")
    tools_ms: float = Field(ge=0, description="Tiempo total en herramientas.")
    abstained: bool = Field(default=False, description="True si el agente respondió que no lo sabe.")

    @model_validator(mode="after")
    def _check_and_fill(self) -> Self:
        if len(set(self.tools_used)) != len(self.tools_used):
            raise ValueError("tools_used no puede repetir herramientas")
        if self.tool_call_count < len(self.tools_used):
            raise ValueError("tool_call_count no puede ser menor que las herramientas distintas usadas")
        check_or_fill(self, "total_tokens", self.input_tokens + self.output_tokens)
        return self
