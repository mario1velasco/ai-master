"""Métricas de una llamada a un LLM."""

from typing import Self

from pydantic import Field, model_validator

from contracts.metrics.base import BaseMetrics, check_or_fill
from contracts.metrics.llm.cost import CostEstimate
from contracts.metrics.llm.enums import FinishReason, LlmProvider, LlmPurpose
from contracts.metrics.llm.ollama import OllamaTimings


class LlmCallMetrics(BaseMetrics):
    """Todo lo medible de una llamada a un LLM: modelo, parámetros, tokens, velocidad y salida."""

    provider: LlmProvider = Field(description="Quién respondió: ollama o mock.")
    model: str = Field(min_length=1, description="Nombre del modelo, p. ej. 'qwen3:4b-instruct'.")
    model_digest: str | None = Field(default=None, description="Digest de Ollama: identifica los pesos exactos.")
    parameter_size: str | None = Field(default=None, description="Tamaño del modelo, p. ej. '4B'.")
    quantization: str | None = Field(default=None, description="Cuantización, p. ej. 'Q4_K_M'.")

    purpose: LlmPurpose = Field(description="Paso del flujo que hizo la llamada (decidir herramienta, generar SQL…).")
    temperature: float = Field(ge=0, le=2, description="Temperatura de muestreo.")
    max_tokens: int = Field(gt=0, description="Máximo de tokens de salida pedidos.")
    top_p: float | None = Field(default=None, gt=0, le=1, description="Top-p de muestreo, si se fijó.")
    seed: int | None = Field(default=None, description="Semilla, si se fijó (reproducibilidad).")
    num_ctx: int | None = Field(
        default=None,
        gt=0,
        description="Ventana de contexto configurada; si se supera, Ollama recorta el prompt sin avisar.",
    )

    message_count: int = Field(default=1, ge=1, description="Mensajes enviados (system + historial + usuario).")
    system_prompt_chars: int | None = Field(default=None, ge=0, description="Caracteres del prompt de sistema.")

    structured_output: bool = Field(default=False, description="True si se pidió salida con esquema (tool o JSON).")
    output_schema: str | None = Field(default=None, description="Nombre del esquema pedido, p. ej. 'SqlProposal'.")
    output_valid: bool | None = Field(default=None, description="True si la salida pasó la validación Pydantic.")
    validation_errors: int = Field(default=0, ge=0, description="Errores de validación de la salida estructurada.")

    tools_offered: int = Field(default=0, ge=0, description="Herramientas ofrecidas al modelo.")
    tool_calls: list[str] = Field(default_factory=list, description="Herramientas que pidió llamar el modelo.")

    thinking_enabled: bool = Field(default=False, description="True si el modo razonamiento (Qwen3) estaba activo.")
    thinking_tokens: int | None = Field(default=None, ge=0, description="Tokens dedicados a razonar.")

    input_tokens: int = Field(ge=0, description="Tokens de entrada.")
    output_tokens: int = Field(ge=0, description="Tokens de salida.")
    total_tokens: int | None = Field(default=None, ge=0, description="Derivado: input_tokens + output_tokens.")
    context_usage_pct: float | None = Field(
        default=None, ge=0, description="Derivado: % de num_ctx ocupado por la entrada; cerca de 100 hay recorte."
    )

    time_to_first_token_ms: float | None = Field(
        default=None, ge=0, description="Tiempo hasta el primer token (solo con streaming)."
    )
    tokens_per_second: float | None = Field(
        default=None,
        ge=0,
        description="Derivado: velocidad de generación; de los tiempos de Ollama si los hay, si no de latency_ms.",
    )

    finish_reason: FinishReason = Field(description="Motivo de fin que dio el proveedor (done_reason en Ollama).")
    truncated: bool | None = Field(default=None, description="Derivado: true si finish_reason es 'length'.")
    retries: int = Field(default=0, ge=0, description="Reintentos antes de la respuesta final.")

    ollama: OllamaTimings | None = Field(default=None, description="Tiempos internos de Ollama, si los dio.")
    cost: CostEstimate | None = Field(default=None, description="Coste estimado frente a la tarifa de referencia.")

    @model_validator(mode="after")
    def _check_consistency_and_fill(self) -> Self:
        if not self.structured_output and (self.output_schema is not None or self.output_valid is not None):
            raise ValueError("output_schema y output_valid solo tienen sentido con structured_output")
        if not self.thinking_enabled and self.thinking_tokens:
            raise ValueError("thinking_tokens > 0 sin thinking_enabled")

        check_or_fill(self, "total_tokens", self.input_tokens + self.output_tokens)
        check_or_fill(self, "truncated", self.finish_reason is FinishReason.length)
        if self.num_ctx is not None:
            check_or_fill(self, "context_usage_pct", round(self.input_tokens / self.num_ctx * 100, 2))
        check_or_fill(self, "tokens_per_second", self._generation_speed())
        return self

    def _generation_speed(self) -> float | None:
        if self.ollama is not None and self.ollama.eval_tokens_per_second is not None:
            return self.ollama.eval_tokens_per_second
        if self.latency_ms > 0:
            return round(self.output_tokens / (self.latency_ms / 1000), 2)
        return None
