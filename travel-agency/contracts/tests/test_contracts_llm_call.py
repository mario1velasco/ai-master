from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from contracts.metrics import CostEstimate, CostRate, LlmCallMetrics, OllamaTimings


def test_llm_call_fills_derived_fields(llm_fields: dict[str, Any]) -> None:
    metrics = LlmCallMetrics.model_validate(llm_fields | {"num_ctx": 8192})

    assert metrics.total_tokens == 642
    assert metrics.truncated is False
    assert metrics.context_usage_pct == 7.32
    assert metrics.tokens_per_second == 20.0  # 42 tokens / 2,1 s, sin tiempos de Ollama


def test_llm_call_prefers_ollama_speed(llm_fields: dict[str, Any], ollama_response: dict[str, Any]) -> None:
    metrics = LlmCallMetrics.model_validate(
        llm_fields | {"ollama": OllamaTimings.from_ollama_response(ollama_response)}
    )
    assert metrics.tokens_per_second == 75.0


def test_llm_call_length_means_truncated(llm_fields: dict[str, Any]) -> None:
    assert LlmCallMetrics.model_validate(llm_fields | {"finish_reason": "length"}).truncated is True


def test_llm_call_round_trip_through_json(llm_fields: dict[str, Any], ollama_response: dict[str, Any]) -> None:
    rate = CostRate(
        reference="claude-haiku-4-5", input_cost_per_1m_tokens=0.8, output_cost_per_1m_tokens=4.0, currency="USD"
    )
    metrics = LlmCallMetrics.model_validate(
        llm_fields
        | {
            "num_ctx": 8192,
            "structured_output": True,
            "output_schema": "SqlProposal",
            "output_valid": True,
            "tools_offered": 1,
            "tool_calls": ["proponer_sql"],
            "ollama": OllamaTimings.from_ollama_response(ollama_response),
            "cost": CostEstimate.from_tokens(600, 42, rate),
            "attributes": {"view": "v_vuelos_detalle"},
        }
    )

    reloaded = LlmCallMetrics.model_validate_json(metrics.model_dump_json())

    assert reloaded == metrics
    assert LlmCallMetrics.model_validate(metrics.model_dump(mode="json")) == metrics


def test_llm_call_rejects_inconsistent_total_tokens(llm_fields: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="no cuadra"):
        LlmCallMetrics.model_validate(llm_fields | {"total_tokens": 1})


def test_llm_call_rejects_unknown_field(llm_fields: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="extra"):
        LlmCallMetrics.model_validate(llm_fields | {"latency": 12})


@pytest.mark.parametrize(
    ("field", "value"),
    [("input_tokens", -1), ("output_tokens", -5), ("temperature", 3.0), ("max_tokens", 0), ("top_p", 0.0)],
)
def test_llm_call_rejects_out_of_range(llm_fields: dict[str, Any], field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        LlmCallMetrics.model_validate(llm_fields | {field: value})


@pytest.mark.parametrize(
    "extra",
    [{"output_schema": "SqlProposal"}, {"output_valid": True}, {"thinking_tokens": 30}],
)
def test_llm_call_rejects_incoherent_flags(llm_fields: dict[str, Any], extra: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        LlmCallMetrics.model_validate(llm_fields | extra)


@pytest.mark.parametrize("model", [LlmCallMetrics, OllamaTimings, CostEstimate, CostRate])
def test_every_field_has_description(model: type[BaseModel]) -> None:
    properties = model.model_json_schema()["properties"]
    missing = [name for name, prop in properties.items() if not prop.get("description")]
    assert missing == []
