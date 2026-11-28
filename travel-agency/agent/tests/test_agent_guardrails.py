"""Guardarraíles del agente (ticket TRAVEL-011, tema 9 sesión 2): entrada, herramientas en tres capas y salida.

La sesión es de C-001 (Ana López García: reservas R-1042 y R-1047, incidencia I-01, vuelos IB3166, IB3167 e IB0731);
los otros clientes, C-004 (Ana López Pérez: R-1043, I-02, VY1234 y VY1235) y C-002 (Javier Martín Ruiz). Datos de
`database/fixtures/`. El modelo es el Ollama falso (`ollama`), con el guion de cada test.
"""

import duckdb
import pytest
from fake_ollama_server import FakeOllamaServer, query_db_answer, sql_answer, text_answer

from agent import respond
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
