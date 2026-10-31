"""Logger, spans, IDs de traza y eventos JSONL."""

from telemetry.config import TelemetryConfig, configure, get_config
from telemetry.context import current_trace_id
from telemetry.event import EVENT_SCHEMA_VERSION, METRICS_TYPES, Event
from telemetry.logger import close_log_files, get_logger
from telemetry.span import Span, span
from telemetry.writer import events_path, read_events, write_event

__version__ = "0.1.0"

__all__ = [
    "EVENT_SCHEMA_VERSION",
    "METRICS_TYPES",
    "Event",
    "Span",
    "TelemetryConfig",
    "close_log_files",
    "configure",
    "current_trace_id",
    "events_path",
    "get_config",
    "get_logger",
    "read_events",
    "span",
    "write_event",
]
