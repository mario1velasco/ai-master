"""`python -m agent -q "…"`: el comando para probar el agente a mano (ticket TRAVEL-006, AC-4 y AC-14)."""

import json

import pytest
from fake_ollama_server import FakeOllamaServer, query_db_answer, sql_answer, text_answer

from agent.__main__ import main
from database.seed import FIXTURES_DIR

QUESTION = "¿Cuántas reservas tiene C-001?"
QUESTION_HEADER = "[PREGUNTA]"
ANSWER_HEADER = "[RESPUESTA DEL AGENTE]"
METRICS_HEADER = "[MÉTRICAS]"


def block(out: str, header: str, next_header: str | None = None) -> str:
    """El texto de un bloque: desde su cabecera hasta la siguiente, sin las barras de «=»."""
    text = out.split(header, 1)[1]
    if next_header is not None:
        text = text.split(next_header, 1)[0]
    return "\n".join(line for line in text.splitlines() if not set(line) <= {"="}).strip()


def test_cli_shows_question_answer_and_metrics(ollama: FakeOllamaServer, capsys: pytest.CaptureFixture[str]) -> None:
    ollama.agent_answers = [query_db_answer(QUESTION), text_answer("C-001 tiene 2 reservas.")]
    ollama.text2sql_answers = [sql_answer("SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'")]

    main(["-q", QUESTION, "--data", str(FIXTURES_DIR)])  # sin SystemExit: el comando termina con código 0

    out = capsys.readouterr().out
    assert out.index(QUESTION_HEADER) < out.index(ANSWER_HEADER) < out.index(METRICS_HEADER)
    assert block(out, QUESTION_HEADER, ANSWER_HEADER) == QUESTION

    answer = json.loads(block(out, ANSWER_HEADER, METRICS_HEADER))  # el AgentAnswer entero, en JSON
    assert answer["answer"] == "C-001 tiene 2 reservas."
    assert answer["tools_used"] == ["query_db"]

    metrics = block(out, METRICS_HEADER)
    for name in ("agent.respond", "llm.agent", "text2sql.ask", "llm.text2sql", "sql.run"):  # el agente y sus pasos
        assert name in metrics


def test_cli_without_trace_keeps_turn_metrics(ollama: FakeOllamaServer, capsys: pytest.CaptureFixture[str]) -> None:
    sql = "SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'"
    ollama.agent_answers = [query_db_answer(QUESTION), text_answer("C-001 tiene 2 reservas.")]
    ollama.text2sql_answers = [sql_answer(sql)]

    main(["-q", QUESTION, "--data", str(FIXTURES_DIR), "--no-trace"])

    out = capsys.readouterr().out
    assert METRICS_HEADER not in out  # sin el detalle de cada paso
    answer = json.loads(block(out, ANSWER_HEADER))
    assert answer["metrics"]["name"] == "agent.respond"  # pero con los totales del turno
    assert [source["sql"] for source in answer["sources"]] == [sql]
