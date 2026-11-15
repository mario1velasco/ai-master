"""Evaluar text2sql: examen, corrector, métricas e informe (ticket TRAVEL-007).

El modelo es un Ollama falso (`fake_ollama`); la base, la de `data/` (`data_con`), con la que se mide de verdad.
"""

import json
from pathlib import Path
from typing import Any

import duckdb
from fake_ollama import FakeOllama, sql_answer

from text2sql import ask
from text2sql.evaluation.evaluate import evaluate_case
from text2sql.evaluation.exam import load_exam

RESERVATIONS_C001 = "SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'"


def write_exam(tmp_path: Path, questions: list[dict[str, Any]]) -> Path:
    """Un examen en JSON, con el formato de `exams/` (claves `id`, `category`, `trap`, `question`, `sql`…)."""
    path = tmp_path / "exam.json"
    path.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")
    return path


def test_attempt_with_reference_rows_passes(
    tmp_path: Path, data_con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    exam = write_exam(
        tmp_path,
        [
            {
                "id": "N1",
                "category": "normal",
                "trap": None,
                "question": "¿Cuántas reservas tiene C-001?",
                "sql": RESERVATIONS_C001,
            }
        ],
    )
    [question] = load_exam(exam, data_con)
    fake_ollama.answers = [sql_answer(RESERVATIONS_C001)]  # el modelo escribe el mismo SQL que la referencia

    verdict = evaluate_case(question, ask(question["question"], con=data_con))

    assert verdict["success"] is True
    assert verdict["reason"] is None
