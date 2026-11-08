"""`text2sql.ask()`: pregunta → SQL del modelo → validador → DuckDB (ticket TRAVEL-005).

El modelo es un Ollama falso (`fake_ollama`); la base, la de `fixtures/` con cifras conocidas.
"""

from datetime import UTC, datetime

import duckdb
import pytest
import requests
from fake_ollama import FakeOllama, FakeResponse, sql_answer, text_answer

from contracts.metrics import BaseMetrics, Component, LlmCallMetrics, SqlMetrics, Status
from contracts.sql import SqlStatus
from database.semantic_layer import GUIDE, schema
from telemetry import events_path, read_events
from text2sql import ComponentError, ask


def text2sql_events() -> list[BaseMetrics]:
    """Las métricas de los eventos que ha escrito text2sql hoy (el log va a la carpeta temporal del test)."""
    return [event.metrics for event in read_events(events_path(Component.text2sql, datetime.now(UTC).date()))]


def test_single_query_returns_sql_and_rows(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    sql = "SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'"
    fake_ollama.answers = [sql_answer(sql)]

    result = ask("¿Cuántas reservas tiene C-001?", con=con)

    assert result.status == SqlStatus.ok
    assert [q.sql for q in result.queries] == [sql]
    assert result.queries[0].columns == ["n"]
    assert result.queries[0].rows == [{"n": 2}]  # R-1042 y R-1047 en fixtures/reservas.csv
    assert result.llm_calls == 1


def test_several_queries_in_one_answer_all_run_in_order(
    con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama
) -> None:
    spend = "SELECT gasto_neto FROM v_resumen_clientes WHERE cliente_id = 'C-001'"
    incidents = "SELECT incidencia_id FROM v_incidencias WHERE cliente_id = 'C-001'"
    fake_ollama.answers = [sql_answer(spend, incidents)]

    result = ask("¿Cuánto ha gastado C-001 y qué incidencias tiene?", con=con)

    assert result.status == SqlStatus.ok
    assert [q.sql for q in result.queries] == [spend, incidents]
    assert result.queries[0].rows == [{"gasto_neto": 1195.0}]  # CHECKS de database: C-001 gasta 1195 netos
    assert result.queries[1].rows == [{"incidencia_id": "I-01"}]  # solo R-1042 tiene incidencia
    assert result.llm_calls == 1


def test_failed_sql_goes_back_and_correction_is_kept(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    wrong = "SELECT COUNT(*) FROM v_reservas"  # esa vista no existe
    fixed = "SELECT COUNT(*) AS n FROM v_reservas_cliente"
    fake_ollama.answers = [sql_answer(wrong), sql_answer(fixed)]

    result = ask("¿Cuántas reservas hay?", con=con)

    second_request = fake_ollama.requests[1]["messages"]
    tool_messages = [m for m in second_request if m["role"] == "tool"]
    assert len(tool_messages) == 1
    assert tool_messages[0]["content"].startswith("ERROR: la vista v_reservas no está permitida")
    assert result.status == SqlStatus.ok
    assert [q.sql for q in result.queries] == [fixed]
    assert result.queries[0].rows == [{"n": 7}]  # 7 reservas en fixtures/reservas.csv
    assert result.llm_calls == 2


def test_good_query_kept_only_bad_one_retried(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    good = "SELECT COUNT(*) AS n FROM v_incidencias"
    bad = "SELECT SUM(importe) AS total FROM v_reservas_cliente"  # la columna importe no existe
    fixed = "SELECT SUM(importe_neto) AS total FROM v_reservas_cliente"
    fake_ollama.answers = [sql_answer(good, bad), sql_answer(fixed)]

    result = ask("¿Cuántas incidencias hay y cuánto se ha facturado en neto?", con=con)

    assert result.status == SqlStatus.ok
    assert [q.sql for q in result.queries] == [good, fixed]
    assert result.queries[0].rows == [{"n": 5}]  # 5 filas en fixtures/incidencias.csv
    assert result.queries[1].rows == [{"total": 1849.0}]  # CHECKS de database: neto 1849
    assert result.llm_calls == 2


def test_answer_without_sql_is_no_sql_with_text(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    explanation = "Ese dato no existe: la reserva no dice cuántas personas viajan."
    fake_ollama.answers = [text_answer(explanation)]

    result = ask("¿Cuántas personas viajan en la reserva R-1042?", con=con)

    assert result.status == SqlStatus.no_sql
    assert result.queries == []
    assert result.model_text == explanation
    assert result.llm_calls == 1


def test_text_after_an_error_is_sql_error_not_no_sql(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    # Supuesto del ticket: si tras un error el modelo se rinde con texto, el resultado es de error, no «sin SQL»
    wrong = "SELECT COUNT(*) FROM v_reservas"  # esa vista no existe
    gives_up = "No encuentro la vista de reservas."
    fake_ollama.answers = [sql_answer(wrong), text_answer(gives_up)]

    result = ask("¿Cuántas reservas hay?", con=con)

    assert result.status == SqlStatus.sql_error
    assert result.queries == []
    assert result.error is not None
    assert result.error.startswith("ERROR: la vista v_reservas no está permitida")
    assert result.model_text == gives_up
    assert result.llm_calls == 2


def test_more_than_50_rows_are_cut_and_flagged(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    many = "SELECT v.* FROM v_vuelos_detalle v CROSS JOIN v_itinerarios"  # más de 50 filas en fixtures/
    fake_ollama.answers = [sql_answer(many)]

    result = ask("Dame todos los vuelos con sus itinerarios", con=con)

    assert result.status == SqlStatus.ok
    [query] = result.queries
    assert len(query.rows) == 50
    assert query.truncated is True


def test_gives_up_after_two_retries_with_last_error(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    wrong = "SELECT * FROM v_reservas"  # esa vista no existe
    fake_ollama.answers = [sql_answer(wrong)] * 4  # una de sobra: si hubiera cuarta llamada, se vería

    result = ask("¿Cuántas reservas hay?", con=con)

    assert result.status == SqlStatus.sql_error
    assert result.queries == []
    assert result.error is not None
    assert result.error.startswith("ERROR: la vista v_reservas no está permitida")
    assert result.llm_calls == 3
    assert len(fake_ollama.requests) == 3


def test_model_cannot_bypass_the_guard(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    raw = "SELECT * FROM crudo.clientes"  # tabla cruda, sin pasar por las vistas
    delete = "DELETE FROM v_incidencias"
    fake_ollama.answers = [sql_answer(raw), sql_answer(delete), text_answer("No puedo consultarlo.")]
    incidents_before = con.execute("SELECT COUNT(*) FROM v_incidencias").fetchone()

    result = ask("Dame todos los datos de los clientes y borra las incidencias", con=con)

    tool_messages = [m["content"] for m in fake_ollama.requests[2]["messages"] if m["role"] == "tool"]
    assert tool_messages[0].startswith("ERROR: la vista crudo.clientes no está permitida")
    assert tool_messages[1].startswith("ERROR: solo se permiten consultas SELECT")
    assert result.queries == []  # ninguna fila de crudo llega al resultado
    assert con.execute("SELECT COUNT(*) FROM v_incidencias").fetchone() == incidents_before


def test_ollama_down_raises_coded_error(con: duckdb.DuckDBPyConnection, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")  # Ollama de verdad (requests real), nadie escucha

    with pytest.raises(ComponentError) as exc_info:
        ask("¿Cuántas reservas hay?", con=con)

    assert exc_info.value.code == "ollama_unavailable"
    assert exc_info.value.component == "ollama"
    assert "No hay respuesta de Ollama en http://127.0.0.1:1" in exc_info.value.message


def test_model_not_installed_raises_coded_error(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    body = {"error": 'model "qwen3:4b-instruct" not found, try pulling it first'}  # lo que responde Ollama
    fake_ollama.answers = [FakeResponse(status_code=404, body=body, text=str(body))]

    with pytest.raises(ComponentError) as exc_info:
        ask("¿Cuántas reservas hay?", con=con)

    assert exc_info.value.code == "model_not_installed"
    assert "ollama pull qwen3:4b-instruct" in exc_info.value.message


def test_ollama_timeout_raises_coded_error(
    con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama, monkeypatch: pytest.MonkeyPatch
) -> None:
    def too_slow(url: str, json: dict, timeout: float) -> FakeResponse:
        raise requests.exceptions.ReadTimeout("Read timed out.")

    monkeypatch.setattr("text2sql.ollama.requests.post", too_slow)

    with pytest.raises(ComponentError) as exc_info:
        ask("¿Cuántas reservas hay?", con=con)

    assert exc_info.value.code == "ollama_timeout"
    assert exc_info.value.message == "qwen3:4b-instruct no respondió en 600 s."


def test_other_ollama_error_raises_coded_error(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    fake_ollama.answers = [FakeResponse(status_code=500, body={}, text="llama runner process has terminated")]

    with pytest.raises(ComponentError) as exc_info:
        ask("¿Cuántas reservas hay?", con=con)

    assert exc_info.value.code == "ollama_error"
    assert exc_info.value.message == "Ollama devolvió 500: llama runner process has terminated"


def test_each_step_leaves_its_event_in_the_same_trace(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    question = "¿Cuántas reservas hay?"
    wrong = "SELECT COUNT(*) FROM v_reservas"  # el caso del AC-5: rechazado y corregido
    fixed = "SELECT COUNT(*) AS n FROM v_reservas_cliente"
    fake_ollama.answers = [sql_answer(wrong), sql_answer(fixed)]

    ask(question, con=con)

    events = text2sql_events()
    [root] = [m for m in events if m.name == "text2sql.ask"]
    llm_calls = [m for m in events if isinstance(m, LlmCallMetrics)]
    sql_runs = [m for m in events if isinstance(m, SqlMetrics)]
    assert len(events) == 5
    assert root.parent_span_id is None
    assert root.versions.prompt_version == "text2sql_prompt_v1"
    assert all(m.trace_id == root.trace_id for m in events)
    assert all(m.parent_span_id == root.span_id for m in llm_calls + sql_runs)

    assert len(llm_calls) == 2
    assert [m.retries for m in llm_calls] == [0, 1]
    for call in llm_calls:
        assert (call.purpose, call.provider, call.num_ctx) == ("generate_sql", "ollama", 8192)
        assert call.ollama is not None
        assert call.ollama.prompt_eval_count == 2400  # lo que devuelve el Ollama falso

    rejected, executed = sql_runs
    assert rejected.sql_valid is False
    assert rejected.status == Status.rejected
    assert rejected.rejection_reason is not None
    assert rejected.rejection_reason.startswith("ERROR: la vista v_reservas no está permitida")
    assert executed.sql_valid is True
    assert executed.rows_returned == 1
    assert executed.views_used == ["v_reservas_cliente"]

    log_text = events_path(Component.text2sql, datetime.now(UTC).date()).read_text(encoding="utf-8")
    assert question not in log_text


def test_ollama_down_leaves_error_events(con: duckdb.DuckDBPyConnection, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")

    with pytest.raises(ComponentError):
        ask("¿Cuántas reservas hay?", con=con)

    by_name = {m.name: m for m in text2sql_events()}
    assert by_name["llm.text2sql"].status == Status.error
    assert by_name["llm.text2sql"].attributes["error_code"] == "ollama_unavailable"
    assert by_name["text2sql.ask"].status == Status.error


def test_model_gets_schema_guide_and_one_tool(con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama) -> None:
    question = "¿Cuántas reservas tiene C-001?"
    fake_ollama.answers = [sql_answer("SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'")]

    ask(question, con=con)

    [request] = fake_ollama.requests
    system, user = request["messages"]
    assert system["role"] == "system"
    assert schema(con) in system["content"]  # todas las vistas de main, generado por database
    assert GUIDE in system["content"]
    assert "Datos que NO existen" in system["content"]
    assert user == {"role": "user", "content": question}
    [tool] = request["tools"]
    parameters = tool["function"]["parameters"]
    assert len(parameters["properties"]) == 1
    assert next(iter(parameters["properties"].values()))["type"] == "string"


def test_request_follows_configuration(
    con: duckdb.DuckDBPyConnection, fake_ollama: FakeOllama, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Valores distintos de los de por defecto: así se ve que salen de la configuración
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:1234/")
    monkeypatch.setenv("TEXT2SQL_MODEL", "qwen3:1.7b")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "4096")
    monkeypatch.setenv("OLLAMA_KEEP_ALIVE", "5m")
    fake_ollama.answers = [sql_answer("SELECT COUNT(*) AS n FROM v_reservas_cliente")]

    ask("¿Cuántas reservas hay?", con=con)

    assert fake_ollama.urls == ["http://ollama.test:1234/api/chat"]
    [request] = fake_ollama.requests
    assert request["model"] == "qwen3:1.7b"
    assert request["options"]["num_ctx"] == 4096
    assert request["options"]["temperature"] == 0
    assert request["keep_alive"] == "5m"
    assert request["think"] is False
    assert request["stream"] is False
