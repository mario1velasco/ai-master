"""`respond()`: una pregunta al agente, de principio a fin.

Como `conversar()` de `08_ia_agentica_automatiz_agentes/tema8-agentes/sesion3/agente_langgraph.py`: el grafo de
`construir_agente` con las instrucciones y las tools, `invoke` con la pregunta y la respuesta es el último mensaje.
Las fuentes y las herramientas usadas salen de los mensajes que deja el grafo, sin contadores propios.
"""

import duckdb
from langchain_core.messages import ToolMessage

from agent.graph import build_agent
from agent.model import build_model
from agent.tools import build_query_db_tool
from contracts.agent import AgentAnswer, AgentStatus, Source, SourceType
from contracts.sql import SqlResult

INSTRUCTIONS = (
    "Eres el asistente de los empleados de Viajes Nimbo, una agencia de viajes. "
    "Consulta los datos con las herramientas y nunca los inventes. Responde en español, breve y claro."
)


def respond(question: str, *, con: duckdb.DuckDBPyConnection) -> AgentAnswer:
    """Responde la pregunta con el agente: decide si consulta la base y redacta con los datos."""
    agent = build_agent(build_model(), [build_query_db_tool(con)], INSTRUCTIONS)
    messages = agent.invoke({"messages": [("user", question)]})["messages"]

    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    results = [m.artifact for m in tool_messages if isinstance(m.artifact, SqlResult)]
    sources = [
        Source(type=SourceType.db, views=q.metrics.views_used if q.metrics else [], rows=len(q.rows))
        for result in results
        for q in result.queries
    ]
    return AgentAnswer(
        answer=str(messages[-1].content),
        status=AgentStatus.ok,
        answered_without_data=not sources,
        sources=sources,
        tools_used=list(dict.fromkeys(m.name for m in tool_messages if m.name)),
    )
