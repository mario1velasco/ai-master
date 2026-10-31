"""Métricas que acompañan a cada resultado de cada paquete (sección 8 de PROYECTO.md)."""

from contracts.metrics.agent import AgentMetrics
from contracts.metrics.api import ApiMetrics
from contracts.metrics.base import METRICS_SCHEMA_VERSION, BaseMetrics, Versions, short_hash
from contracts.metrics.enums import Component, Status
from contracts.metrics.llm import (
    CostEstimate,
    CostRate,
    FinishReason,
    LlmCallMetrics,
    LlmProvider,
    LlmPurpose,
    OllamaTimings,
)
from contracts.metrics.rag import RagMetrics, ScoreStats
from contracts.metrics.sql import SqlMetrics

__all__ = [
    "METRICS_SCHEMA_VERSION",
    "AgentMetrics",
    "ApiMetrics",
    "BaseMetrics",
    "Component",
    "CostEstimate",
    "CostRate",
    "FinishReason",
    "LlmCallMetrics",
    "LlmProvider",
    "LlmPurpose",
    "OllamaTimings",
    "RagMetrics",
    "ScoreStats",
    "SqlMetrics",
    "Status",
    "Versions",
    "short_hash",
]
