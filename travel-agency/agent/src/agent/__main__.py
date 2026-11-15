"""Probar el agente a mano con el Qwen real: `uv run python -m agent -q "¿Cuántas reservas tiene C-001?"`.

Con `--no-trace` no enseña el bloque con los eventos de cada paso: solo la pregunta y la respuesta entera (con sus
fuentes, el SQL de cada una y las métricas del turno).

Como `text2sql/__main__.py` (el `main()` de `07_llm_open_source/clase_01/Ejercicios/practica/04_conectar_ollama.py`:
bloques `[…]` con `print`). Enseña la pregunta, la respuesta entera del agente y las métricas de cada paso de esa
traza (el agente, sus llamadas al modelo, text2sql y cada SQL), que salen de los eventos de telemetría (`logs/`). La
configuración, por variables de entorno (`agent/.env.example`).
"""

import argparse
from datetime import UTC, datetime
from pathlib import Path

from agent.respond import respond
from contracts.metrics import BaseMetrics, Component
from database.semantic_layer import DATA_DIR, open_db
from telemetry import events_path, read_events

QUESTION = "¿Cuántas reservas tiene C-001?"
BAR = "=" * 72
LINE = "-" * 72


def _trace_metrics(trace_id: str) -> list[BaseMetrics]:
    """Los eventos de la traza, del agente y de text2sql, ordenados por inicio: primero `agent.respond`."""
    today = datetime.now(UTC).date()
    metrics = [
        event.metrics
        for component in (Component.agent, Component.text2sql)
        for event in read_events(events_path(component, today))
    ]
    return sorted((m for m in metrics if m.trace_id == trace_id), key=lambda m: m.started_at)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pregunta → agente (y text2sql si hace falta) → respuesta y métricas.")
    parser.add_argument("--question", "-q", default=QUESTION, help="Pregunta a enviar.")
    parser.add_argument("--data", type=Path, default=DATA_DIR, help="Carpeta con los 8 CSV (por defecto data/).")
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="No enseñar el bloque [MÉTRICAS] con los eventos de cada paso (la respuesta sí trae los totales).",
    )
    args = parser.parse_args(argv)

    answer = respond(args.question, con=open_db(args.data))

    print(f"{BAR}\n[PREGUNTA]\n{BAR}")
    print(args.question)
    print(f"\n{BAR}\n[RESPUESTA DEL AGENTE]\n{BAR}")
    print(answer.model_dump_json(indent=2))
    if args.no_trace:  # los eventos siguen en los logs: búscalos por el trace_id de la respuesta
        return

    events = _trace_metrics(answer.trace_id)
    print(f"\n{BAR}\n[MÉTRICAS] traza {answer.trace_id} · {len(events)} eventos\n{BAR}")
    for m in events:
        print(f"{LINE}\n{m.name} · {type(m).__name__} · {m.latency_ms:.0f} ms · {m.status}\n{LINE}")
        print(m.model_dump_json(indent=2, exclude_none=True))  # sin los campos vacíos: si no, la mitad son null


if __name__ == "__main__":
    main()
