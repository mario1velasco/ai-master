from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts.metrics import BaseMetrics
from telemetry import Event, events_path, read_events, write_event

STARTED_AT = datetime(2026, 10, 31, 12, 0, 0, tzinfo=UTC)


def _metrics(name: str = "sql.validar") -> BaseMetrics:
    return BaseMetrics.model_validate(
        {
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "component": "text2sql",
            "name": name,
            "started_at": STARTED_AT,
            "ended_at": STARTED_AT + timedelta(milliseconds=3),
            "latency_ms": 3.0,
            "status": "ok",
        }
    )


def test_write_and_read_roundtrip(log_dir: Path) -> None:
    event = Event.from_metrics(_metrics(), environment="test")

    path = write_event(event)

    assert path == log_dir / "text2sql" / "events-2026-10-31.jsonl"
    assert read_events(path) == [event]


def test_write_appends_one_line_per_event() -> None:
    write_event(Event.from_metrics(_metrics("a"), environment="test"))
    path = write_event(Event.from_metrics(_metrics("b"), environment="test"))

    assert [e.metrics.name for e in read_events(path)] == ["a", "b"]
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_write_keeps_accents_unescaped() -> None:
    path = write_event(Event.from_metrics(_metrics("sql.validación"), environment="test"))

    assert "sql.validación" in path.read_text(encoding="utf-8")


def test_read_missing_file_returns_empty(log_dir: Path) -> None:
    assert read_events(log_dir / "no_existe.jsonl") == []


def test_events_path_uses_component_and_day(log_dir: Path) -> None:
    assert events_path("rag", date(2026, 1, 2)) == log_dir / "rag" / "events-2026-01-02.jsonl"


def test_event_rejects_unknown_metrics_type() -> None:
    data = Event.from_metrics(_metrics(), environment="test").model_dump(mode="json")
    data["metrics_type"] = "SqlMetrics"

    with pytest.raises(ValidationError, match="metrics_type desconocido"):
        Event.model_validate(data)


def test_event_rejects_mismatched_metrics_type() -> None:
    with pytest.raises(ValidationError, match="no cuadra"):
        Event(environment="test", metrics_type="LlmCallMetrics", metrics=_metrics())


def test_every_event_field_has_description() -> None:
    properties = Event.model_json_schema()["properties"]
    missing = [name for name, prop in properties.items() if not prop.get("description")]
    assert missing == []
