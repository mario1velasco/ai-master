"""Escritura y lectura de eventos JSONL (misma idea que write_jsonl / read_jsonl del tema 4)."""

import json
from datetime import date
from pathlib import Path

from contracts.metrics import Component
from telemetry.config import get_config
from telemetry.event import Event


def events_path(component: Component | str, day: date) -> Path:
    """Archivo de eventos de un componente y un día: `<log_dir>/<componente>/events-AAAA-MM-DD.jsonl`."""
    return get_config().log_dir / str(component) / f"events-{day.isoformat()}.jsonl"


def write_event(event: Event) -> Path:
    """Añade el evento como una línea al archivo de su componente y del día en que empezó el span."""
    path = events_path(event.metrics.component, event.metrics.started_at.date())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(event.model_dump_json() + "\n")
    return path


def read_events(path: Path | str) -> list[Event]:
    """Lee y valida todos los eventos de un archivo; lista vacía si no existe."""
    log_path = Path(path)
    if not log_path.exists():
        return []
    with log_path.open("r", encoding="utf-8") as f:
        return [Event.model_validate(json.loads(line)) for line in f if line.strip()]
