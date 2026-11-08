"""Probar `ask` a mano con el Qwen real: `uv run python -m text2sql -q "¿Cuántas reservas tiene C-001?"`.

Como el `main()` de `07_llm_open_source/clase_01/Ejercicios/practica/04_conectar_ollama.py`: bloques `[…]` con
`print`. Enseña la pregunta, lo que recibiría el agente (el `SqlResult` entero) y las métricas de cada paso, que salen
de los eventos de telemetría de esa pregunta (`logs/text2sql/`). La configuración, por variables de entorno
(`OLLAMA_BASE_URL`, `TEXT2SQL_MODEL`, `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`).
"""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from contracts.metrics import BaseMetrics, Component
from database.semantic_layer import DATA_DIR, open_db
from telemetry import events_path, read_events
from text2sql.loop import ask
from text2sql.ollama import ComponentError

QUESTION = "¿Cuántas reservas canceladas tiene C-001?"
BAR = "=" * 72
LINE = "-" * 72


def _trace_metrics() -> list[BaseMetrics]:
    """Los eventos de la última pregunta, ordenados por inicio: primero `text2sql.ask` y luego sus pasos.

    `ask` no devuelve su `trace_id`: se toma el del último `text2sql.ask` escrito, que es el de esta pregunta.
    """
    metrics = [event.metrics for event in read_events(events_path(Component.text2sql, datetime.now(UTC).date()))]
    trace_id = [m for m in metrics if m.name == "text2sql.ask"][-1].trace_id
    return sorted((m for m in metrics if m.trace_id == trace_id), key=lambda m: m.started_at)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pregunta → SQL del modelo → validador → DuckDB, con sus métricas.")
    parser.add_argument("--question", "-q", default=QUESTION, help="Pregunta a enviar.")
    parser.add_argument("--data", type=Path, default=DATA_DIR, help="Carpeta con los 8 CSV (por defecto data/).")
    args = parser.parse_args(argv)

    try:
        result = ask(args.question, con=open_db(args.data))
    except ComponentError as exc:  # Como el «[ERROR] …» del 04: el código y el mensaje, sin traza de Python
        print(f"[ERROR] {exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(1) from None

    print(f"{BAR}\n[PREGUNTA]\n{BAR}")
    print(args.question)
    print(f"\n{BAR}\n[LO QUE RECIBIRÍA EL AGENTE]\n{BAR}")
    print(result.model_dump_json(indent=2))

    events = _trace_metrics()
    print(f"\n{BAR}\n[MÉTRICAS] traza {events[0].trace_id} · {len(events)} eventos\n{BAR}")
    for m in events:
        print(f"{LINE}\n{m.name} · {type(m).__name__} · {m.latency_ms:.0f} ms · {m.status}\n{LINE}")
        print(m.model_dump_json(indent=2, exclude_none=True))  # sin los campos vacíos: si no, la mitad son null


if __name__ == "__main__":
    main()
