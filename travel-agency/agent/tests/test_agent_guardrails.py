"""Guardarraíles del agente (ticket TRAVEL-011, tema 9 sesión 2): entrada, herramientas en tres capas y salida.

La sesión es de C-001 (Ana López García: reservas R-1042 y R-1047, incidencia I-01, vuelos IB3166, IB3167 e IB0731);
los otros clientes, C-004 (Ana López Pérez: R-1043, I-02, VY1234 y VY1235) y C-002 (Javier Martín Ruiz). Datos de
`database/fixtures/`. El modelo es el Ollama falso (`ollama`), con el guion de cada test.
"""

import json

import duckdb
import pytest
from fake_ollama_server import FakeOllamaServer, query_db_answer, sql_answer, text_answer

from agent import respond
from agent.profiles import PROFILES
from contracts.agent import AgentStatus, Block, BlockType, Session, SourceType
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


def user_message(ollama: FakeOllamaServer) -> str:
    """Lo que escribió el cliente, tal como le llegó al modelo en la primera llamada."""
    [user] = [m["content"] for m in ollama.agent_requests[0]["messages"] if m["role"] == "user"]
    return user


def test_valid_card_masked_before_model(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("No guardes la tarjeta en el chat.")]

    answer = respond("Mi tarjeta es 4111 1111 1111 1111", con=con, session=C001)

    assert user_message(ollama) == "Mi tarjeta es [TARJETA ****1111]"
    assert answer.blocks == [Block(type=BlockType.input, reason="tarjeta enmascarada")]


def test_iban_and_dni_masked(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("No compartas esos datos en el chat.")]

    answer = respond("Mi IBAN es ES91 2100 0418 4502 0005 1332 y mi DNI 12345678Z", con=con, session=C001)

    assert user_message(ollama) == "Mi IBAN es [IBAN] y mi DNI [DNI]"
    assert answer.blocks == [
        Block(type=BlockType.input, reason="IBAN enmascarado"),
        Block(type=BlockType.input, reason="DNI enmascarado"),
    ]


def test_long_number_failing_luhn_untouched(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("Lo miro.")]
    # 16 cifras, como una tarjeta, pero el dígito de control no cuadra (4111 1111 1111 1111 sí lo pasa)
    question = "Mi localizador de la aerolínea es 4111 1111 1111 1112"

    answer = respond(question, con=con, session=C001)

    assert user_message(ollama) == question
    assert answer.blocks == []


TOO_LONG = "Mensaje demasiado largo. Resume tu consulta, por favor."


def test_too_long_message_never_reaches_model(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("Lo miro.")]

    blocked = respond("a" * 2001, con=con, session=C001)

    assert blocked.answer == TOO_LONG
    assert ollama.agent_requests == []
    # Un bloqueo no es un error: el turno acaba bien, sin datos (supuesto aprobado del ticket)
    assert blocked.status == AgentStatus.ok
    assert blocked.answered_without_data is True
    assert blocked.blocks == [Block(type=BlockType.input, reason=TOO_LONG)]

    passed = respond("a" * 2000, con=con, session=C001)

    assert passed.answer == "Lo miro."
    assert len(ollama.agent_requests) == 1


NOT_ALLOWED = "solo puedes consultar los datos del cliente identificado"


@pytest.mark.parametrize(
    "question",
    ["¿Cuánto pagó la reserva R-1043?", "¿Qué reservas tiene C-004?", "¿Cómo va la incidencia I-02?"],
)
def test_question_naming_other_client_data_not_run(
    con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer, question: str
) -> None:
    ollama.agent_answers = [query_db_answer(question), text_answer("No puedo darte ese dato.")]
    ollama.text2sql_answers = [sql_answer("SELECT importe_neto FROM v_reservas_cliente WHERE reserva_id = 'R-1043'")]

    answer = respond(question, con=con, session=C001)

    assert ollama.text2sql_requests == []  # text2sql no se llama
    [tool] = [m["content"] for m in ollama.agent_requests[1]["messages"] if m["role"] == "tool"]
    assert tool == f"Acción no permitida: {NOT_ALLOWED}"
    assert answer.sources == []
    assert answer.blocks == [Block(type=BlockType.tool, reason=NOT_ALLOWED)]
    # Como `Resultado.herramientas` de clase: la llamada bloqueada no cuenta como herramienta usada
    assert answer.tools_used == []
    assert answer.metrics is not None
    assert answer.metrics.tool_call_count == 0


def tool_content(ollama: FakeOllamaServer) -> str:
    """Lo que devolvió `query_db` al modelo en la segunda llamada del agente."""
    [tool] = [m["content"] for m in ollama.agent_requests[1]["messages"] if m["role"] == "tool"]
    return tool


def test_sql_without_ids_cannot_read_other_booking(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    # La pregunta no nombra ningún id (la capa 1 la deja pasar), pero el SQL pide la reserva de C-004
    other_booking = "SELECT importe_neto FROM v_reservas_cliente WHERE reserva_id = 'R-1043'"
    ollama.agent_answers = [query_db_answer("¿Cuánto pagué en mi última reserva?"), text_answer("No lo encuentro.")]
    ollama.text2sql_answers = [sql_answer(other_booking)]

    answer = respond("¿Cuánto pagué en mi última reserva?", con=con, session=C001)

    assert json.loads(tool_content(ollama)) == [{"sql": other_booking, "rows": [], "truncated": False}]
    assert [s.rows for s in answer.sources] == [0]


def test_text2sql_gets_the_same_schema_with_client_filter(
    con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer
) -> None:
    question = "¿Qué reservas tiene C-001?"
    ollama.agent_answers = [
        query_db_answer(question),
        text_answer("Dos."),
        query_db_answer(question),
        text_answer("Dos."),
    ]
    ollama.text2sql_answers = [sql_answer(OWN_BOOKINGS), sql_answer(OWN_BOOKINGS)]

    respond("¿Qué reservas tengo?", con=con, session=C001)  # con la conexión filtrada
    respond("¿Qué reservas tengo?", con=con, session=C001, guardrails=False)  # con la de siempre

    filtered, normal = [request["messages"][0]["content"] for request in ollama.text2sql_requests]
    assert "Tabla v_incidencias (5 filas)" in normal  # el esquema completo: las 5 incidencias de fixtures/
    assert filtered == normal


def test_aggregates_only_count_session_client(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    count = "SELECT COUNT(*) AS n FROM v_resumen_clientes"
    total = "SELECT SUM(importe_neto) AS total FROM v_reservas_cliente"
    ollama.agent_answers = [query_db_answer("¿Cuántos clientes tenéis y cuánto facturáis?"), text_answer("…")]
    ollama.text2sql_answers = [sql_answer(count, total)]

    answer = respond("¿Cuántos clientes tenéis y cuánto facturáis?", con=con, session=C001)

    # A mano, de fixtures/pagos.csv: R-1042 1.250 − 150 de reembolso = 1.100, más R-1047 95 = 1.195 (la empresa: 1.849)
    assert json.loads(tool_content(ollama)) == [
        {"sql": count, "rows": [{"n": 1}], "truncated": False},
        {"sql": total, "rows": [{"total": 1195.0}], "truncated": False},
    ]
    assert answer.blocks == []
