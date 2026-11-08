"""`python -m text2sql -q "…"`: el comando para probar `ask` a mano (ticket TRAVEL-005, AC-4)."""

import json

import pytest
from fake_ollama import FakeOllama, sql_answer

from database.seed import FIXTURES_DIR
from text2sql.__main__ import main

QUESTION_HEADER = "[PREGUNTA]"
AGENT_HEADER = "[LO QUE RECIBIRÍA EL AGENTE]"
METRICS_HEADER = "[MÉTRICAS]"


def block(out: str, header: str, next_header: str | None = None) -> str:
    """El texto de un bloque: desde su cabecera hasta la siguiente, sin las barras de «=»."""
    text = out.split(header, 1)[1]
    if next_header is not None:
        text = text.split(next_header, 1)[0]
    return "\n".join(line for line in text.splitlines() if not set(line) <= {"="}).strip()


def test_cli_shows_question_result_and_metrics(fake_ollama: FakeOllama, capsys: pytest.CaptureFixture[str]) -> None:
    question = "¿Cuántas reservas tiene C-001?"
    fake_ollama.answers = [sql_answer("SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'")]

    main(["-q", question, "--data", str(FIXTURES_DIR)])  # sin SystemExit: el comando termina con código 0

    out = capsys.readouterr().out
    assert out.index(QUESTION_HEADER) < out.index(AGENT_HEADER) < out.index(METRICS_HEADER)
    assert block(out, QUESTION_HEADER, AGENT_HEADER) == question

    result = json.loads(block(out, AGENT_HEADER, METRICS_HEADER))  # el SqlResult entero, en JSON
    assert result["status"] == "ok"
    assert result["queries"][0]["rows"] == [{"n": 2}]
    assert result["llm_calls"] == 1

    metrics = block(out, METRICS_HEADER)
    for name in ("text2sql.ask", "llm.text2sql", "sql.run"):
        assert name in metrics
    assert '"prompt_eval_count": 2400' in metrics  # los tiempos de Ollama de la llamada al modelo


def test_cli_with_ollama_down_explains_without_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")  # Ollama de verdad (requests real), nadie escucha

    with pytest.raises(SystemExit) as exit_info:
        main(["-q", "¿Cuántas reservas tiene C-001?", "--data", str(FIXTURES_DIR)])

    assert exit_info.value.code != 0
    captured = capsys.readouterr()
    assert "ollama_unavailable" in captured.err
    assert "No hay respuesta de Ollama en http://127.0.0.1:1" in captured.err
    assert "Traceback" not in captured.out + captured.err
