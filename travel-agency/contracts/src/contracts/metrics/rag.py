"""Métricas de una búsqueda en el corpus: híbrida (BM25 + denso + RRF) y reranking."""

from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from contracts.metrics.base import BaseMetrics


class ScoreStats(BaseModel):
    """Resumen de los scores de los pasajes devueltos (del reranker si lo hubo)."""

    model_config = ConfigDict(extra="forbid")

    max: float = Field(description="Score más alto.")
    min: float = Field(description="Score más bajo.")
    mean: float = Field(description="Score medio.")

    @model_validator(mode="after")
    def _check_order(self) -> Self:
        if not self.min <= self.mean <= self.max:
            raise ValueError("debe cumplirse min <= mean <= max")
        return self

    @classmethod
    def from_scores(cls, scores: Sequence[float]) -> Self | None:
        """Calcula el resumen; None si no hay pasajes."""
        if not scores:
            return None
        return cls(max=max(scores), min=min(scores), mean=round(sum(scores) / len(scores), 6))


class RagMetrics(BaseMetrics):
    """Métricas del span `rag.search`."""

    search_ms: float = Field(ge=0, description="Tiempo de la búsqueda híbrida (BM25 + denso + RRF).")
    rerank_ms: float | None = Field(default=None, ge=0, description="Tiempo del reranker; null si no se usó.")

    candidate_count: int = Field(ge=0, description="Candidatos que salen de la fusión RRF.")
    passages_returned: int = Field(ge=0, description="Pasajes que se devuelven al LLM.")
    scores: ScoreStats | None = Field(default=None, description="Máximo, mínimo y media de los scores devueltos.")
    distinct_docs: int = Field(ge=0, description="Documentos distintos entre los pasajes devueltos.")

    context_chars: int = Field(ge=0, description="Caracteres del contexto que llega al LLM.")
    context_tokens: int | None = Field(default=None, ge=0, description="Tokens de ese contexto, si se contaron.")
    abstained: bool = Field(default=False, description="True si no hubo evidencia suficiente para responder.")

    @model_validator(mode="after")
    def _check_counts(self) -> Self:
        if self.passages_returned > self.candidate_count:
            raise ValueError("passages_returned no puede superar a candidate_count")
        if self.distinct_docs > self.passages_returned:
            raise ValueError("distinct_docs no puede superar a passages_returned")
        if (self.scores is None) != (self.passages_returned == 0):
            raise ValueError("scores debe venir si y solo si hay pasajes devueltos")
        return self
