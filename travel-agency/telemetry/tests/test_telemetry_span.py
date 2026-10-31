from pathlib import Path

import pytest

from contracts.metrics import BaseMetrics, Component, LlmCallMetrics, Status, Versions, short_hash
from telemetry import EVENT_SCHEMA_VERSION, Event, configure, current_trace_id, read_events, span


def _events(log_dir: Path, component: str = "text2sql") -> list[Event]:
    files = sorted((log_dir / component).glob("events-*.jsonl"))
    return [event for file in files for event in read_events(file)]


def test_span_writes_valid_event(log_dir: Path) -> None:
    with span("sql.validar", component=Component.text2sql, input_text="SELECT 1") as s:
        s.output_text = "ok"
        s.attributes["vistas"] = 2

    [event] = _events(log_dir)
    assert event.event_schema_version == EVENT_SCHEMA_VERSION
    assert event.environment == "test"
    assert event.metrics_type == "BaseMetrics"
    metrics = event.metrics
    assert metrics.name == "sql.validar"
    assert metrics.status is Status.ok
    assert metrics.parent_span_id is None
    assert len(metrics.trace_id) == 32
    assert len(metrics.span_id) == 16
    assert metrics.latency_ms >= 0
    assert metrics.input_chars == 8
    assert metrics.input_hash == short_hash("SELECT 1")
    assert metrics.output_chars == 2
    assert metrics.attributes == {"vistas": 2}
    assert s.metrics == metrics


def test_span_file_is_per_component_and_day(log_dir: Path) -> None:
    with span("sql.validar", component=Component.text2sql) as s:
        pass

    assert s.metrics is not None
    day = s.metrics.started_at.date().isoformat()
    assert (log_dir / "text2sql" / f"events-{day}.jsonl").is_file()


def test_nested_spans_share_trace_and_point_to_parent(log_dir: Path) -> None:
    with span("text2sql.consultar", component=Component.text2sql) as parent:
        with span("sql.validar", component=Component.text2sql) as child:
            assert current_trace_id() == parent.trace_id
        with span("sql.ejecutar", component=Component.text2sql) as sibling:
            pass
    assert current_trace_id() is None

    assert child.trace_id == sibling.trace_id == parent.trace_id
    assert child.parent_span_id == sibling.parent_span_id == parent.span_id
    assert parent.parent_span_id is None
    # Los hijos cierran antes y se escriben antes que el padre.
    assert [e.metrics.name for e in _events(log_dir)] == ["sql.validar", "sql.ejecutar", "text2sql.consultar"]


def test_span_uses_given_trace_id() -> None:
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    with span("api.messages", component=Component.api, trace_id=trace_id) as s:
        pass

    assert s.trace_id == trace_id


def test_span_records_error_and_reraises(log_dir: Path) -> None:
    with pytest.raises(TimeoutError, match="Ollama"):
        with span("sql.ejecutar", component=Component.text2sql):
            raise TimeoutError("Ollama no respondió")

    [event] = _events(log_dir)
    assert event.metrics.status is Status.error
    assert event.metrics.error_type == "TimeoutError"
    assert event.metrics.error_message == "Ollama no respondió"


def test_span_reject_without_exception(log_dir: Path) -> None:
    with span("sql.validar", component=Component.text2sql) as s:
        s.reject("ddl_prohibido")

    [event] = _events(log_dir)
    assert event.metrics.status is Status.rejected
    assert event.metrics.error_type == "ddl_prohibido"


def test_span_with_llm_call_metrics_roundtrip(log_dir: Path) -> None:
    with span(
        "llm.text2sql",
        component=Component.text2sql,
        metrics_cls=LlmCallMetrics,
        versions=Versions(prompt_version="sql_prompt_v1"),
    ) as s:
        s.fields.update(
            provider="ollama",
            model="qwen3:4b-instruct",
            purpose="generate_sql",
            temperature=0.0,
            max_tokens=700,
            input_tokens=600,
            output_tokens=42,
            finish_reason="stop",
        )

    [event] = _events(log_dir)
    assert event.metrics_type == "LlmCallMetrics"
    assert isinstance(event.metrics, LlmCallMetrics)
    assert event.metrics.total_tokens == 642
    assert event.metrics.versions.prompt_version == "sql_prompt_v1"


def test_failed_llm_call_falls_back_to_base_metrics(log_dir: Path) -> None:
    with pytest.raises(ConnectionError):
        with span("llm.text2sql", component=Component.text2sql, metrics_cls=LlmCallMetrics):
            raise ConnectionError("Ollama apagado")

    [event] = _events(log_dir)
    assert event.metrics_type == "BaseMetrics"
    assert event.metrics.status is Status.error
    assert event.metrics.attributes == {"expected_metrics_type": "LlmCallMetrics"}


def test_invalid_metrics_raise_in_strict_mode() -> None:
    with pytest.raises(ValueError, match="input_tokens"):
        with span("llm.text2sql", component=Component.text2sql, metrics_cls=LlmCallMetrics):
            pass


def test_invalid_metrics_do_not_break_without_strict(log_dir: Path) -> None:
    configure(strict=False)

    with span("llm.text2sql", component=Component.text2sql, metrics_cls=LlmCallMetrics) as s:
        result = "SELECT 1"

    assert result == "SELECT 1"
    assert s.metrics is None
    assert _events(log_dir) == []
    assert "No se pudo registrar el span llm.text2sql" in (log_dir / "telemetry" / "app.log").read_text()


def test_span_never_stores_input_text(log_dir: Path) -> None:
    secret = "Calle Falsa 123, Madrid"
    with span("agent.responder", component=Component.agent, input_text=secret):
        pass

    content = next((log_dir / "agent").glob("events-*.jsonl")).read_text(encoding="utf-8")
    assert secret not in content


def test_base_metrics_is_default_class(log_dir: Path) -> None:
    with span("rag.buscar", component=Component.rag) as s:
        pass

    assert type(s.metrics) is BaseMetrics
