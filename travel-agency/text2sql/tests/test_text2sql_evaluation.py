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


def normal_question(sql: str, question: str = "Pregunta de prueba") -> dict[str, Any]:
    """Una pregunta normal, sin trampa, con su SQL de referencia."""
    return {"id": "N1", "category": "normal", "trap": None, "question": question, "sql": sql}


def evaluate_attempt(
    tmp_path: Path,
    con: duckdb.DuckDBPyConnection,
    fake_ollama: FakeOllama,
    question: dict[str, Any],
    answer: dict[str, Any],
) -> dict[str, Any]:
    """Carga la pregunta como examen, deja que el modelo falso responda `answer` y corrige ese intento."""
    [loaded] = load_exam(write_exam(tmp_path, [question]), con)
    fake_ollama.answers = [answer]
    return evaluate_case(loaded, ask(loaded["question"], con=con))


def test_extra_columns_or_other_order_pass(
    tmp_path: Path, data_con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    reference = "SELECT COUNT(*) AS total FROM v_reservas_cliente WHERE cliente_id = 'C-001'"  # {total: 2}
    attempt = (
        "SELECT cliente_id, COUNT(*) AS total FROM v_reservas_cliente WHERE cliente_id = 'C-001' GROUP BY cliente_id"
    )  # {cliente_id: "C-001", total: 2}: una columna de más, y delante

    verdict = evaluate_attempt(tmp_path, data_con, fake_ollama, normal_question(reference), sql_answer(attempt))

    assert verdict["success"] is True
    assert verdict["reason"] is None


def test_extra_or_missing_rows_fail_with_reason(
    tmp_path: Path, data_con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    reference = "SELECT cliente_id, reservas FROM v_resumen_clientes WHERE cliente_id = 'C-001'"  # 1 fila
    attempt = (
        "SELECT cliente_id, reservas FROM v_resumen_clientes WHERE cliente LIKE 'Ana López%'"
    )  # 3 filas: las tres Ana López de data/ (C-001, C-004 y C-0388), entre ellas la de la referencia

    verdict = evaluate_attempt(tmp_path, data_con, fake_ollama, normal_question(reference), sql_answer(attempt))

    assert verdict["success"] is False
    assert "3 filas en vez de 1" in verdict["reason"]
