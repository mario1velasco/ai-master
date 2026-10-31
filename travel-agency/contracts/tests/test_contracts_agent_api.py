from http import HTTPMethod
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from contracts.metrics import AgentMetrics, ApiMetrics, RagMetrics, ScoreStats, SqlMetrics


@pytest.fixture
def agent_fields(base_fields: dict[str, Any]) -> dict[str, Any]:
    """Campos de un AgentMetrics válido: el turno del árbol de ejemplo de la sección 8."""
    return base_fields | {
        "component": "agent",
        "name": "agent.responder",
        "iterations": 2,
        "llm_call_count": 3,
        "tool_call_count": 2,
        "tools_used": ["consultar_bbdd", "buscar_documentos"],
        "input_tokens": 3120,
        "output_tokens": 412,
        "llm_ms": 7300.0,
        "tools_ms": 980.0,
    }


@pytest.fixture
def api_fields(base_fields: dict[str, Any]) -> dict[str, Any]:
    """Campos de un ApiMetrics válido: POST de un mensaje."""
    return base_fields | {
        "component": "api",
        "name": "api.messages",
        "parent_span_id": None,
        "session_id": "s-001",
        "endpoint": "/sessions/{session_id}/messages",
        "http_method": "POST",
        "status_code": 200,
        "request_bytes": 96,
        "response_bytes": 1450,
        "session_turn": 3,
    }


def test_agent_metrics_fills_total_tokens(agent_fields: dict[str, Any]) -> None:
    metrics = AgentMetrics.model_validate(agent_fields)

    assert metrics.total_tokens == 3532
    assert metrics.abstained is False


def test_agent_metrics_rejects_wrong_total(agent_fields: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="no cuadra"):
        AgentMetrics.model_validate(agent_fields | {"total_tokens": 1})


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"tools_used": ["consultar_bbdd", "consultar_bbdd"]}, "repetir"),
        ({"tool_call_count": 1}, "menor"),
    ],
)
def test_agent_metrics_rejects_incoherent_tools(
    agent_fields: dict[str, Any], changes: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        AgentMetrics.model_validate(agent_fields | changes)


def test_api_metrics_valid(api_fields: dict[str, Any]) -> None:
    metrics = ApiMetrics.model_validate(api_fields)

    assert metrics.http_method is HTTPMethod.POST
    assert metrics.summary_applied is False


def test_api_metrics_health_has_no_session(api_fields: dict[str, Any]) -> None:
    health = api_fields | {"endpoint": "/health", "http_method": "GET", "session_id": None, "session_turn": None}

    assert ApiMetrics.model_validate(health).session_id is None


@pytest.mark.parametrize(("field", "value"), [("status_code", 700), ("http_method", "BORRAR"), ("session_turn", 0)])
def test_api_metrics_rejects_bad_values(api_fields: dict[str, Any], field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        ApiMetrics.model_validate(api_fields | {field: value})


@pytest.mark.parametrize("model", [SqlMetrics, RagMetrics, ScoreStats, AgentMetrics, ApiMetrics])
def test_every_new_field_has_description(model: type[BaseModel]) -> None:
    properties = model.model_json_schema()["properties"]
    missing = [name for name, prop in properties.items() if not prop.get("description")]
    assert missing == []
