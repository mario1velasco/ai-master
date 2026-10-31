from typing import Any

import pytest
from pydantic import ValidationError

from contracts.metrics import RagMetrics, ScoreStats


@pytest.fixture
def rag_fields(base_fields: dict[str, Any]) -> dict[str, Any]:
    """Campos de un RagMetrics válido: 20 candidatos, 4 pasajes de 3 documentos."""
    return base_fields | {
        "component": "rag",
        "name": "rag.search",
        "search_ms": 35.0,
        "rerank_ms": 1450.0,
        "candidate_count": 20,
        "passages_returned": 4,
        "scores": ScoreStats.from_scores([0.91, 0.84, 0.62, 0.55]),
        "distinct_docs": 3,
        "context_chars": 5200,
    }


def test_rag_metrics_valid(rag_fields: dict[str, Any]) -> None:
    metrics = RagMetrics.model_validate(rag_fields)

    assert metrics.scores == ScoreStats(max=0.91, min=0.55, mean=0.73)
    assert metrics.abstained is False
    assert metrics.context_tokens is None


def test_rag_metrics_abstention_without_passages(rag_fields: dict[str, Any]) -> None:
    empty = rag_fields | {"passages_returned": 0, "scores": None, "distinct_docs": 0, "abstained": True}

    assert RagMetrics.model_validate(empty).abstained is True


def test_score_stats_from_empty_is_none() -> None:
    assert ScoreStats.from_scores([]) is None


def test_score_stats_rejects_bad_order() -> None:
    with pytest.raises(ValidationError, match="min <= mean <= max"):
        ScoreStats(max=0.5, min=0.6, mean=0.55)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"passages_returned": 25}, "candidate_count"),
        ({"distinct_docs": 5}, "passages_returned"),
        ({"scores": None}, "scores"),
        ({"passages_returned": 0, "distinct_docs": 0}, "scores"),
    ],
)
def test_rag_metrics_rejects_incoherent_counts(
    rag_fields: dict[str, Any], changes: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        RagMetrics.model_validate(rag_fields | changes)
