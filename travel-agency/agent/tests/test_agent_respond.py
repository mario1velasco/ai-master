"""`agent.respond()`: pregunta → el agente decide consultar la BBDD → responde con esos datos (ticket TRAVEL-006).

El modelo es un Ollama falso (`ollama`) que responde lo que dice cada test, tanto al agente como a `text2sql`; la
base, la de `fixtures/` con cifras conocidas.
"""

import duckdb
from fake_ollama_server import FakeOllamaServer, query_db_answer, sql_answer, text_answer

from agent import respond
from contracts.agent import AgentStatus, SourceType

QUESTION = "¿Cuántas reservas tiene C-001?"
COUNT_C001 = "SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'"


def test_db_question_answered_with_query_source(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [query_db_answer(QUESTION), text_answer("C-001 tiene 2 reservas.")]
    ollama.text2sql_answers = [sql_answer(COUNT_C001)]

    answer = respond(QUESTION, con=con)

    assert answer.answer == "C-001 tiene 2 reservas."
    assert answer.status == AgentStatus.ok
    assert answer.answered_without_data is False
    assert [(s.type, s.views, s.rows) for s in answer.sources] == [(SourceType.db, ["v_reservas_cliente"], 1)]
    assert answer.tools_used == ["consultar_bbdd"]
