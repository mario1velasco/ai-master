"""Coste estimado de una llamada: en local es 0, pero se compara con un proveedor de referencia."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field


class CostRate(BaseModel):
    """Tarifa de referencia; mismas claves que el bloque `cost:` del config.yml de triage."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(
        min_length=1, description="Modelo o proveedor con el que se compara, p. ej. 'claude-haiku-4-5'."
    )
    input_cost_per_1m_tokens: float = Field(ge=0, description="Precio por millón de tokens de entrada.")
    output_cost_per_1m_tokens: float = Field(ge=0, description="Precio por millón de tokens de salida.")
    currency: str = Field(min_length=3, max_length=3, description="Moneda ISO 4217, p. ej. 'USD' o 'EUR'.")


class CostEstimate(BaseModel):
    """Lo que costaría la llamada con la tarifa de referencia, y lo que costó de verdad."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(description="Tarifa de referencia usada.")
    currency: str = Field(min_length=3, max_length=3, description="Moneda ISO 4217.")
    input_cost: float = Field(ge=0, description="Coste estimado de los tokens de entrada.")
    output_cost: float = Field(ge=0, description="Coste estimado de los tokens de salida.")
    total_cost: float = Field(ge=0, description="Coste estimado total (misma fórmula que estimate_cost de triage).")
    actual_cost: float = Field(default=0.0, ge=0, description="Coste real; 0 con modelos locales.")

    @classmethod
    def from_tokens(cls, input_tokens: int, output_tokens: int, rate: CostRate) -> Self:
        """Calcula el coste estimado con la fórmula de `estimate_cost` de triage."""
        input_cost = input_tokens * rate.input_cost_per_1m_tokens / 1_000_000
        output_cost = output_tokens * rate.output_cost_per_1m_tokens / 1_000_000
        return cls(
            reference=rate.reference,
            currency=rate.currency,
            input_cost=round(input_cost, 8),
            output_cost=round(output_cost, 8),
            total_cost=round(input_cost + output_cost, 8),
        )
