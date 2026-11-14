"""`agent.respond()`: pregunta → el agente decide consultar la BBDD → responde con esos datos (ticket TRAVEL-006).

El modelo es un Ollama falso (`ollama`) que responde lo que dice cada test, tanto al agente como a `text2sql`; la
base, la de `fixtures/` con cifras conocidas.
"""

import json
from typing import Any

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


def tool_contents(request: dict[str, Any]) -> list[str]:
    """Los mensajes de la tool que llevan una petición del agente a Ollama."""
    return [m["content"] for m in request["messages"] if m["role"] == "tool"]


def test_tool_message_has_sql_and_rows_without_metrics(
    con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer
) -> None:
    ollama.agent_answers = [query_db_answer(QUESTION), text_answer("C-001 tiene 2 reservas.")]
    ollama.text2sql_answers = [sql_answer(COUNT_C001)]

    respond(QUESTION, con=con)

    [content] = tool_contents(ollama.agent_requests[1])
    # Por cada consulta, su SQL, sus filas y la marca de recorte (R-1042 y R-1047 en fixtures/reservas.csv)
    assert json.loads(content) == [{"sql": COUNT_C001, "rows": [{"n": 2}], "truncated": False}]
    for metric in ("latency_ms", "trace_id", "rows_returned", "metrics"):
        assert metric not in content


def test_model_sees_rules_and_one_tool_never_schema(con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer) -> None:
    ollama.agent_answers = [text_answer("No tengo ese dato.")]

    respond(QUESTION, con=con)

    request = ollama.agent_requests[0]
    system, user = request["messages"]
    assert system["role"] == "system"
    assert "no existe" in system["content"].lower()  # la regla «si el dato no existe, dilo»
    assert "v_reservas_cliente" not in system["content"]  # ni el esquema ni la guía: los tiene text2sql
    assert user == {"role": "user", "content": QUESTION}

    [tool] = request["tools"]
    function = tool["function"]
    assert function["name"] == "consultar_bbdd"
    assert function["parameters"]["properties"] == {"pregunta": {"type": "string"}}
    assert function["parameters"]["required"] == ["pregunta"]
    description = function["description"].lower()
    assert "se entienda sola" in description  # sin la conversación…
    assert "identificadores" in description  # …así que con sus identificadores
    assert "varios datos" in description  # y puede pedir varios a la vez
