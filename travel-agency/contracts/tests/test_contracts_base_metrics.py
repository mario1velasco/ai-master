from datetime import datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from contracts.metrics import METRICS_SCHEMA_VERSION, BaseMetrics, Component, Status, Versions, short_hash


def test_base_metrics_valid(base_fields: dict[str, Any]) -> None:
    metrics = BaseMetrics.model_validate(base_fields | {"versions": Versions(prompt_version="sql_prompt_v1")})

    assert metrics.metrics_schema_version == METRICS_SCHEMA_VERSION
    assert metrics.component is Component.text2sql
    assert metrics.status is Status.ok
    assert metrics.versions.prompt_version == "sql_prompt_v1"
    assert metrics.attributes == {}


def test_base_metrics_rejects_unknown_field(base_fields: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="extra"):
        BaseMetrics.model_validate(base_fields | {"latencia_ms": 1.0})


def test_base_metrics_rejects_end_before_start(base_fields: dict[str, Any]) -> None:
    base_fields["ended_at"] = base_fields["started_at"] - timedelta(seconds=1)
    with pytest.raises(ValidationError, match="anterior"):
        BaseMetrics.model_validate(base_fields)


def test_base_metrics_rejects_naive_datetime(base_fields: dict[str, Any]) -> None:
    base_fields["started_at"] = datetime(2026, 10, 25, 12, 0, 0)
    with pytest.raises(ValidationError, match="zona horaria"):
        BaseMetrics.model_validate(base_fields)


@pytest.mark.parametrize(
    ("status", "error_type"),
    [("error", None), ("ok", "504_timeout")],
)
def test_base_metrics_error_type_matches_status(
    base_fields: dict[str, Any], status: str, error_type: str | None
) -> None:
    base_fields |= {"status": status, "error_type": error_type}
    with pytest.raises(ValidationError):
        BaseMetrics.model_validate(base_fields)


def test_base_metrics_rejected_status_without_error_is_valid(base_fields: dict[str, Any]) -> None:
    metrics = BaseMetrics.model_validate(base_fields | {"status": "rejected"})
    assert metrics.status is Status.rejected


def test_short_hash_is_stable_and_valid_input_hash(base_fields: dict[str, Any]) -> None:
    value = short_hash("¿Qué retraso tuvo el vuelo IB3166?")

    assert value == short_hash("¿Qué retraso tuvo el vuelo IB3166?")
    assert len(value) == 16
    assert BaseMetrics.model_validate(base_fields | {"input_hash": value}).input_hash == value


def test_base_metrics_attributes_accept_scalars(base_fields: dict[str, Any]) -> None:
    attributes = {"rows": 3, "view": "v_vuelos_detalle", "cached": False, "score": 0.82}
    assert BaseMetrics.model_validate(base_fields | {"attributes": attributes}).attributes == attributes
