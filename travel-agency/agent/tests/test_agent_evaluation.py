"""Evaluar el agente con un examen: corrector, juez, métricas e informe (ticket TRAVEL-012).

El modelo es un Ollama falso (`ollama`) que responde lo que dice cada test, al agente y a `text2sql`; la base, la de
`fixtures/` (cliente de la sesión C-001, dueño de la reserva R-1042).
"""

import duckdb
from fake_ollama_server import FakeOllamaServer, query_db_answer, sql_answer, text_answer

from agent.evaluation.measure import run_cases

STATUS_R1042 = "SELECT reserva_id, estado FROM v_reservas_cliente WHERE reserva_id = 'R-1042'"


def test_well_answered_case_passes_with_every_check_shown(
    con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer
) -> None:
    case = {
        "id": "N1",
        "category": "normal",
        "question": "¿En qué estado está mi reserva R-1042?",
        "client_id": "C-001",
        "expected_tools": ["query_db"],
        "must_contain": ["R-1042"],
    }
    ollama.agent_answers = [
        query_db_answer("Estado de la reserva R-1042"),
        text_answer("Tu reserva R-1042 está confirmada."),
    ]
    ollama.text2sql_answers = [sql_answer(STATUS_R1042)]

    [row] = run_cases([case], con, repetitions=1, verbose=False)

    assert row["success"] is True
    assert row["checks"] == {"must_contain": True, "expected_tools": True, "no_technical_error": True}
    assert row["steps"] == 2  # llamadas al modelo del agente: pide la tool y redacta
