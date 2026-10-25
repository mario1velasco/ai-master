from typing import Any

import pytest
from pydantic import ValidationError

from contracts.metrics import CostEstimate, CostRate, OllamaTimings


def _triage_estimate_cost(input_tokens: int, output_tokens: int, config: dict[str, Any]) -> float:
    """Copia de estimate_cost de 04_api_sdks_ia/Clases/06/app/utils/observability.py."""
    input_cost = input_tokens * config["cost"]["input_cost_per_1m_tokens"] / 1_000_000
    output_cost = output_tokens * config["cost"]["output_cost_per_1m_tokens"] / 1_000_000
    return round(input_cost + output_cost, 8)


def test_ollama_timings_from_response_ignores_other_keys(ollama_response: dict[str, Any]) -> None:
    timings = OllamaTimings.from_ollama_response(ollama_response)

    assert timings.eval_count == 42
    assert timings.load_ms == 1200.0
    assert timings.prompt_eval_ms == 300.0
    assert timings.eval_ms == 560.0
    assert timings.total_ms == 2090.0
    assert timings.prompt_tokens_per_second == 2000.0
    assert timings.eval_tokens_per_second == 75.0
    assert timings.cold_start is True


def test_ollama_timings_warm_model_is_not_cold_start(ollama_response: dict[str, Any]) -> None:
    ollama_response["load_duration"] = 40_000_000
    assert OllamaTimings.from_ollama_response(ollama_response).cold_start is False


def test_ollama_timings_without_data_leaves_derived_empty() -> None:
    timings = OllamaTimings.from_ollama_response({"model": "qwen3:4b-instruct"})

    assert timings.eval_tokens_per_second is None
    assert timings.cold_start is None


def test_ollama_timings_rejects_inconsistent_derived(ollama_response: dict[str, Any]) -> None:
    dumped = OllamaTimings.from_ollama_response(ollama_response).model_dump()
    dumped["eval_ms"] = 1.0
    with pytest.raises(ValidationError, match="no cuadra"):
        OllamaTimings.model_validate(dumped)


def test_cost_estimate_matches_triage_formula() -> None:
    triage_config = {"cost": {"currency": "USD", "input_cost_per_1m_tokens": 0.80, "output_cost_per_1m_tokens": 4.00}}
    rate = CostRate.model_validate(triage_config["cost"] | {"reference": "claude-haiku-4-5"})

    cost = CostEstimate.from_tokens(1600, 120, rate)

    assert cost.total_cost == _triage_estimate_cost(1600, 120, triage_config)
    assert cost.input_cost == 0.00128
    assert cost.output_cost == 0.00048
    assert cost.actual_cost == 0.0
    assert cost.currency == "USD"


def test_cost_rate_rejects_bad_currency() -> None:
    with pytest.raises(ValidationError):
        CostRate(reference="x", input_cost_per_1m_tokens=1, output_cost_per_1m_tokens=1, currency="dollars")
