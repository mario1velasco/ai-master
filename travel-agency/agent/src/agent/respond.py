"""`respond()`: una pregunta al agente, de principio a fin.

Como `conversar()` de `08_ia_agentica_automatiz_agentes/tema8-agentes/sesion3/agente_langgraph.py`: el grafo de
`construir_agente` con las instrucciones y las tools, `invoke` con la pregunta y la respuesta es el último mensaje.
Las fuentes y las herramientas usadas salen de los mensajes que deja el grafo, sin contadores propios.
"""

import os

import duckdb
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError

from agent.graph import build_agent
from agent.model import build_model
from agent.tools import build_query_db_tool
from contracts.agent import AgentAnswer, AgentStatus, Source, SourceType
from contracts.sql import SqlResult

# Las de `sesion3/agente_langgraph.py` adaptadas a Viajes Nimbo, más la regla de `construir_system_prompt()` de
# `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py`. Sin el esquema: lo ve text2sql.
INSTRUCTIONS = (
    "Eres el asistente de los empleados de Viajes Nimbo, una agencia de viajes. "
    "Consulta los datos con las herramientas y nunca los inventes. "
    "Si el dato que se pide no existe, dilo claramente en lugar de aproximarlo. "
    "Responde en español, breve y claro."
)


# El mensaje de `agente_minimo.py` de la sesión 1 al llegar al límite de pasos: al usuario no le habla de pasos.
LIMIT_MESSAGE = "No he podido completar la consulta. Te paso con un compañero del equipo."


def respond(question: str, *, con: duckdb.DuckDBPyConnection) -> AgentAnswer:
    """Responde la pregunta con el agente: decide si consulta la base y redacta con los datos."""
    agent = build_agent(build_model(), [build_query_db_tool(con)], INSTRUCTIONS)
    # `recursion_limit: 20` como `conversar()` de la sesión 3; 1 vuelta = agente → herramientas = 2 pasos
    config: RunnableConfig = {"recursion_limit": int(os.environ.get("AGENT_RECURSION_LIMIT", "20"))}
    try:
        messages = agent.invoke({"messages": [("user", question)]}, config)["messages"]
    except GraphRecursionError:
        # Desvío: en clase no se captura. Aquí se corta con el mensaje fijo de la sesión 1 y la API decide si escala
        return AgentAnswer(answer=LIMIT_MESSAGE, status=AgentStatus.recursion_limit_reached, answered_without_data=True)

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
