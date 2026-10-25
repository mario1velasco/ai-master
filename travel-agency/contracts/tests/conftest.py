from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

STARTED_AT = datetime(2026, 10, 25, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def base_fields() -> dict[str, Any]:
    """Campos mínimos válidos de BaseMetrics."""
    return {
        "trace_id": "t-7f3a",
        "span_id": "s-0002",
        "parent_span_id": "s-0001",
        "component": "text2sql",
        "name": "llm.text2sql",
        "started_at": STARTED_AT,
        "ended_at": STARTED_AT + timedelta(milliseconds=2100),
        "latency_ms": 2100.0,
        "status": "ok",
    }


@pytest.fixture
def llm_fields(base_fields: dict[str, Any]) -> dict[str, Any]:
    """Campos mínimos válidos de LlmCallMetrics."""
    return base_fields | {
        "provider": "ollama",
        "model": "qwen3:4b-instruct",
        "purpose": "generate_sql",
        "temperature": 0.0,
        "max_tokens": 700,
        "input_tokens": 600,
        "output_tokens": 42,
        "finish_reason": "stop",
    }


@pytest.fixture
def ollama_response() -> dict[str, Any]:
    """Respuesta real (recortada) de POST /api/chat de Ollama, sin streaming."""
    return {
        "model": "qwen3:4b-instruct",
        "created_at": "2026-10-25T12:00:02.1Z",
        "message": {"role": "assistant", "content": "SELECT 1"},
        "done_reason": "stop",
        "done": True,
        "total_duration": 2_090_000_000,
        "load_duration": 1_200_000_000,
        "prompt_eval_count": 600,
        "prompt_eval_duration": 300_000_000,
        "eval_count": 42,
        "eval_duration": 560_000_000,
    }
