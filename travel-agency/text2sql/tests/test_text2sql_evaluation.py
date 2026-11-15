"""Evaluar text2sql: examen, corrector, métricas e informe (ticket TRAVEL-007).

El modelo es un Ollama falso (`fake_ollama`); la base, la de `data/` (`data_con`), con la que se mide de verdad.
"""

import json
from pathlib import Path
from typing import Any

import duckdb
import pytest
from fake_ollama import FakeOllama, sql_answer, text_answer

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
    # {cliente_id: "C-001", total: 2}: una columna de más, y delante
    attempt = "SELECT cliente_id, COUNT(*) AS total FROM v_reservas_cliente WHERE cliente_id = 'C-001' GROUP BY 1"

    verdict = evaluate_attempt(tmp_path, data_con, fake_ollama, normal_question(reference), sql_answer(attempt))

    assert verdict["success"] is True
    assert verdict["reason"] is None


def test_extra_or_missing_rows_fail_with_reason(
    tmp_path: Path, data_con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    reference = "SELECT cliente_id, reservas FROM v_resumen_clientes WHERE cliente_id = 'C-001'"  # 1 fila
    # 3 filas: las tres Ana López de data/ (C-001, C-004 y C-0388), entre ellas la de la referencia
    attempt = "SELECT cliente_id, reservas FROM v_resumen_clientes WHERE cliente LIKE 'Ana López%'"

    verdict = evaluate_attempt(tmp_path, data_con, fake_ollama, normal_question(reference), sql_answer(attempt))

    assert verdict["success"] is False
    assert "3 filas en vez de 1" in verdict["reason"]


def test_values_crossed_between_rows_fail(
    tmp_path: Path, data_con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    reference = "SELECT * FROM (VALUES ('MAD', 10), ('BCN', 5)) AS t(origen, reservas)"
    attempt = "SELECT * FROM (VALUES ('MAD', 5), ('BCN', 10)) AS t(origen, reservas)"  # Madrid con 5: falso

    verdict = evaluate_attempt(tmp_path, data_con, fake_ollama, normal_question(reference), sql_answer(attempt))

    assert verdict["success"] is False  # aunque MAD, BCN, 10 y 5 aparezcan todos en algún sitio


@pytest.mark.parametrize(
    ("amount", "city", "passes"),
    [
        ("24.904", "malaga", True),  # dentro de ±0,011; texto sin tilde ni mayúscula
        ("24.92", "Málaga", False),  # 0,02 de diferencia: fuera de la tolerancia
        ("24.90", "MALAGA", True),  # texto en mayúsculas
        ("24.91", "Málaga", True),  # justo 0,01: con ±0,01 suspendería por el redondeo de los float
    ],
)
def test_numbers_with_tolerance_and_normalized_text(
    tmp_path: Path,
    data_con: duckdb.DuckDBPyConnection,
    fake_ollama: FakeOllama,
    amount: str,
    city: str,
    passes: bool,
) -> None:
    reference = "SELECT 24.90 AS importe, 'Málaga' AS ciudad"
    attempt = f"SELECT {amount} AS importe, '{city}' AS ciudad"

    verdict = evaluate_attempt(tmp_path, data_con, fake_ollama, normal_question(reference), sql_answer(attempt))

    assert verdict["success"] is passes


@pytest.mark.parametrize(
    ("answer", "passes"),
    [
        (text_answer("Ese dato no existe: una reserva no dice cuántas personas viajan."), True),  # acaba en no_sql
        (sql_answer("SELECT tramos FROM v_reservas_cliente WHERE reserva_id = 'R-1042'"), False),  # ok, con filas
    ],
)
def test_must_deny_passes_only_with_no_sql(
    tmp_path: Path,
    data_con: duckdb.DuckDBPyConnection,
    fake_ollama: FakeOllama,
    answer: dict[str, Any],
    passes: bool,
) -> None:
    impossible = {
        "id": "E1",
        "category": "edge",
        "trap": None,
        "question": "¿Cuántas personas viajan en la reserva R-1042?",
        "must_deny": True,
    }

    verdict = evaluate_attempt(tmp_path, data_con, fake_ollama, impossible, answer)

    assert verdict["success"] is passes
