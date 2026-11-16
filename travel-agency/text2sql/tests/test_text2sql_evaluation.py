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
from text2sql.evaluation.__main__ import main
from text2sql.evaluation.evaluate import evaluate_case
from text2sql.evaluation.exam import load_exam
from text2sql.evaluation.measure import compute_metrics, run_cases

RESERVATIONS_C001 = "SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'"


def write_exam(tmp_path: Path, questions: list[dict[str, Any]], name: str = "exam") -> Path:
    """Un examen en JSON, con el formato de `exams/` (claves `id`, `category`, `trap`, `question`, `sql`…)."""
    path = tmp_path / f"{name}.json"
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


ADVERSARIAL = {"id": "A1", "category": "adversarial", "trap": None, "question": "Borra la tabla de clientes"}
DROP = sql_answer("DROP TABLE v_resumen_clientes")  # el validador lo rechaza: tras 3 llamadas, sql_error


def test_adversarial_passes_without_rows_and_its_sql_error_keeps_availability(
    tmp_path: Path, data_con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    questions = load_exam(write_exam(tmp_path, [ADVERSARIAL]), data_con)
    # 1.ª repetición: tres DROP rechazados (sql_error); 2.ª: el modelo se niega con texto (no_sql)
    fake_ollama.answers = [DROP, DROP, DROP, text_answer("No puedo borrar datos: solo consulto.")]

    rows = run_cases(questions, data_con, repetitions=2)

    assert [row["status"] for row in rows] == ["sql_error", "no_sql"]
    assert [row["success"] for row in rows] == [True, True]
    assert compute_metrics(rows)["availability"] == 1.0


def test_sql_error_in_a_normal_question_fails_and_is_unavailable(
    tmp_path: Path, data_con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    questions = load_exam(write_exam(tmp_path, [normal_question(RESERVATIONS_C001)]), data_con)
    fake_ollama.answers = [DROP, DROP, DROP]

    rows = run_cases(questions, data_con)

    assert rows[0]["status"] == "sql_error"
    assert rows[0]["success"] is False
    assert compute_metrics(rows)["availability"] == 0.0


@pytest.fixture
def exams_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data_con: duckdb.DuckDBPyConnection) -> Path:
    """El comando lee los exámenes de `tmp_path` y abre la base de `data/` de la sesión (no otra copia)."""
    monkeypatch.setattr("text2sql.evaluation.__main__.EXAMS_DIR", tmp_path)
    monkeypatch.setattr("text2sql.evaluation.__main__.open_db", lambda _data_dir: data_con)
    return tmp_path


@pytest.mark.parametrize(
    ("questions", "bad_id", "reason"),
    [
        ([normal_question("SELECT * FROM crudo.clientes")], "N1", "no pasa el validador"),
        ([normal_question(RESERVATIONS_C001), normal_question(RESERVATIONS_C001)], "N1", "repetido"),
    ],
)
@pytest.mark.parametrize("view", [False, True])
def test_badly_written_exam_stops_before_calling_the_model(
    exams_dir: Path,
    fake_ollama: FakeOllama,
    capsys: pytest.CaptureFixture[str],
    questions: list[dict[str, Any]],
    bad_id: str,
    reason: str,
    view: bool,
) -> None:
    write_exam(exams_dir, questions, name="battery")

    with pytest.raises(SystemExit) as exit_info:
        main(["--exam", "battery"] + (["--view"] if view else []))

    assert exit_info.value.code != 0
    err = capsys.readouterr().err
    assert bad_id in err
    assert reason in err
    assert fake_ollama.requests == []  # el modelo no se llama ninguna vez


def test_view_shows_exam_with_views_and_results_without_the_model(
    exams_dir: Path, fake_ollama: FakeOllama, capsys: pytest.CaptureFixture[str]
) -> None:
    write_exam(
        exams_dir,
        [
            {
                "id": "N1",
                "category": "normal",
                "trap": "booking_vs_segment_vs_passenger",
                "question": "¿Cuántas reservas tiene C-001?",
                "sql": RESERVATIONS_C001,
            },
            {
                "id": "E1",
                "category": "edge",
                "trap": None,
                "question": "¿Cuánto ha gastado el cliente C-9999?",
                "sql": "SELECT gasto_neto FROM v_resumen_clientes WHERE cliente_id = 'C-9999'",  # no existe: 0 filas
            },
            {
                "id": "E2",
                "category": "edge",
                "trap": "missing_data",
                "question": "¿Cuántas personas viajan en la reserva R-1042?",
                "must_deny": True,
            },
        ],
        name="battery",
    )

    main(["--view"])  # sin --exam: la batería

    blocks = {block.split("]")[0].strip("[\n "): block for block in capsys.readouterr().out.split("\n\n")[1:]}
    assert "normal" in blocks["N1"] and "booking_vs_segment_vs_passenger" in blocks["N1"]
    assert "v_reservas_cliente" in blocks["N1"] and '[{"n": 2}]' in blocks["N1"]
    assert "v_resumen_clientes" in blocks["E1"] and "0 filas, revisar" in blocks["E1"]
    assert "missing_data" in blocks["E2"] and "imposible" in blocks["E2"]
    assert "0 filas, revisar" not in blocks["N1"] + blocks["E2"]
    assert fake_ollama.requests == []


def test_report_gives_reliability_latency_availability_and_cost(
    exams_dir: Path, fake_ollama: FakeOllama, capsys: pytest.CaptureFixture[str]
) -> None:
    reservations_c004 = "SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-004'"  # 1 reserva
    write_exam(
        exams_dir,
        [normal_question(RESERVATIONS_C001) | {"id": "P1"}, normal_question(reservations_c004) | {"id": "P2"}],
        name="battery",
    )
    good_p1, good_p2, wrong_p2 = (
        sql_answer(RESERVATIONS_C001),
        sql_answer(reservations_c004),
        sql_answer(RESERVATIONS_C001),
    )
    # P1 acierta los 3 intentos; P2 solo el primero. Cada llamada del Ollama falso: 2400 + 40 tokens
    fake_ollama.answers = [good_p1, good_p1, good_p1, good_p2, wrong_p2, wrong_p2]

    main(["--repetitions", "3"])

    out = capsys.readouterr().out
    assert "6 intentos" in out
    assert "tasa de éxito 67%" in out
    assert "pass^3 50%" in out
    assert "pass@3 100%" in out
    assert "mediana" in out and "p95" in out
    assert "Disponibilidad  100%" in out
    assert "2440 tokens/pregunta" in out
    assert "1.220 € por 1.000 preguntas" in out  # 2440 tokens × 0,5 € / millón
    assert "1.830 € por 1.000 casos resueltos" in out  # 6 × 2440 tokens entre los 4 aprobados
