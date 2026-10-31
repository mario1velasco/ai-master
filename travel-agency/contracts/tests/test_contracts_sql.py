from typing import Any

import pytest
from pydantic import ValidationError

from contracts.metrics import SqlMetrics


@pytest.fixture
def sql_fields(base_fields: dict[str, Any]) -> dict[str, Any]:
    """Campos de un SqlMetrics válido: SQL generado, validado y ejecutado."""
    return base_fields | {
        "name": "text2sql.consultar",
        "generation_ms": 2100.0,
        "validation_ms": 3.0,
        "execution_ms": 12.0,
        "sql_valid": True,
        "views_used": ["v_vuelos_detalle"],
        "sql_chars": 84,
        "rows_returned": 1,
        "column_count": 4,
    }


def test_sql_metrics_valid(sql_fields: dict[str, Any]) -> None:
    metrics = SqlMetrics.model_validate(sql_fields)

    assert metrics.sql_valid is True
    assert metrics.views_used == ["v_vuelos_detalle"]
    assert metrics.limit_applied is False
    assert metrics.timed_out is False


def test_sql_metrics_rejected_without_execution(sql_fields: dict[str, Any]) -> None:
    rejected = sql_fields | {
        "status": "rejected",
        "sql_valid": False,
        "rejection_reason": "ddl_prohibido",
        "execution_ms": None,
        "rows_returned": None,
        "column_count": None,
    }

    metrics = SqlMetrics.model_validate(rejected)

    assert metrics.rejection_reason == "ddl_prohibido"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"sql_valid": False, "execution_ms": None, "rows_returned": None}, "necesita rejection_reason"),
        ({"rejection_reason": "ddl_prohibido"}, "no puede llevar rejection_reason"),
        ({"sql_valid": False, "rejection_reason": "ddl_prohibido"}, "nunca se ejecuta"),
    ],
)
def test_sql_metrics_rejects_incoherent_validation(
    sql_fields: dict[str, Any], changes: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        SqlMetrics.model_validate(sql_fields | changes)


def test_sql_metrics_rejects_unknown_field(sql_fields: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="extra"):
        SqlMetrics.model_validate(sql_fields | {"filas_devueltas": 1})
