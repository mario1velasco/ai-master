"""Guardarraíles del agente (ticket TRAVEL-011, tema 9 sesión 2): entrada, herramientas en tres capas y salida.

La sesión es de C-001 (Ana López García: reservas R-1042 y R-1047, incidencia I-01, vuelos IB3166, IB3167 e IB0731);
los otros clientes, C-004 (Ana López Pérez: R-1043, I-02, VY1234 y VY1235) y C-002 (Javier Martín Ruiz). Datos de
`database/fixtures/`. El modelo es el Ollama falso (`ollama`), con el guion de cada test.
"""

import duckdb
import pytest
from fake_ollama_server import FakeOllamaServer, query_db_answer, sql_answer, text_answer

from agent import respond
from agent.profiles import PROFILES
from contracts.agent import Session, SourceType
from contracts.errors import ComponentError

C001 = Session(client_id="C-001")
OWN_BOOKINGS = "SELECT reserva_id FROM v_reservas_cliente WHERE cliente_id = 'C-001' ORDER BY reserva_id"


def test_own_question_passes_without_blocks(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [query_db_answer("¿Qué reservas tiene C-001?"), text_answer("Tienes R-1042 y R-1047.")]
    ollama.text2sql_answers = [sql_answer(OWN_BOOKINGS)]

    answer = respond("¿Qué reservas tengo?", con=con, session=C001)

    assert [(s.type, s.views, s.rows, s.sql) for s in answer.sources] == [
        (SourceType.db, ["v_reservas_cliente"], 2, OWN_BOOKINGS)
    ]
    assert answer.blocks == []


def test_missing_client_rejected_without_model(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("Tienes dos reservas.")]

    with pytest.raises(ComponentError) as excinfo:
        respond("¿Qué reservas tengo?", con=con)

    assert excinfo.value.code == "missing_client"
    assert ollama.agent_requests == []


def test_unknown_client_rejected_without_model(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("No tienes reservas.")]

    with pytest.raises(ComponentError) as excinfo:
        respond("¿Qué reservas tengo?", con=con, session=Session(client_id="C-999"))

    assert excinfo.value.code == "unknown_client"
    assert ollama.agent_requests == []


def test_role_without_chat_rejected(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("Hay dos cancelaciones pendientes.")]

    with pytest.raises(ComponentError) as excinfo:
        respond("¿Qué cancelaciones tengo que aprobar?", con=con, session=Session(client_id="C-001", role="manager"))

    assert excinfo.value.code == "unknown_role"
    assert ollama.agent_requests == []


def test_model_knows_the_client_and_its_scope(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("¿En qué te ayudo?")]

    respond("Hola", con=con, session=C001)

    request = ollama.agent_requests[0]
    system = request["messages"][0]["content"]
    assert "asistente de los empleados" not in system
    assert "atiendes a sus clientes" in system
    assert "Cliente identificado en esta sesión: C-001." in system
    assert "Solo ves los datos de este cliente" in system
    assert "por la empresa o por otros clientes" in system
    assert "en vez de dar una cifra" in system
    [tool] = request["tools"]
    assert "solo consulta los datos del cliente identificado" in tool["function"]["description"].lower()


def test_client_profile_only_gets_its_tools(
    con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    ollama.agent_answers = [text_answer("¿En qué te ayudo?"), text_answer("¿En qué te ayudo?")]

    respond("Hola", con=con, session=C001)
    monkeypatch.setitem(PROFILES, "client", [])  # un perfil sin herramientas: el modelo no debe recibir ninguna
    respond("Hola", con=con, session=C001)

    assert [t["function"]["name"] for t in ollama.agent_requests[0]["tools"]] == ["query_db"]
    assert not ollama.agent_requests[1].get("tools")
