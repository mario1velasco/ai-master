"""`respond()`: una pregunta al agente, de principio a fin.

Como `conversar()` de `08_ia_agentica_automatiz_agentes/tema8-agentes/sesion3/agente_langgraph.py`: el grafo de
`construir_agente` con las instrucciones y las tools, `invoke` con la pregunta y la respuesta es el último mensaje.
Las fuentes y las herramientas usadas salen de los mensajes que deja el grafo, sin contadores propios.
"""

import os
from typing import Any

import duckdb
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError

from agent.graph import build_agent
from agent.guardrails import check_client
from agent.model import as_component_error, build_model
from agent.profiles import PROFILES, profile
from agent.tools import TOOL_BUILDERS, QueryDbRun
from contracts.agent import AgentAnswer, AgentStatus, Session, Source, SourceType
from contracts.errors import ComponentError
from contracts.metrics import AgentMetrics, Component, Status, Versions
from telemetry import span

# Las de `sesion3/agente_langgraph.py` adaptadas a Viajes Nimbo, más la regla de `construir_system_prompt()` de
# `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py`. Sin el esquema: lo ve text2sql.
# Desde TRAVEL-011, el chat es solo para clientes (decisión 3 de `PROYECTO.md` §10).
INSTRUCTIONS = (
    "Eres el asistente de Viajes Nimbo, una agencia de viajes, y atiendes a sus clientes. "
    "Consulta los datos con las herramientas y nunca los inventes. "
    "Si el dato que se pide no existe, dilo claramente en lugar de aproximarlo. "
    "Responde en español, breve y claro."
)

# Como «Cliente autenticado en esta sesión: …» de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/comun/agente.py`
# («identificado»: el chat no tiene login, el cliente lo pone la sesión), más lo que solo ve (como `HUESPED` de
# `albor/configuracion.py`, FIX03). Depende de que haya cliente, no de los guardarraíles: así TRAVEL-012 compara con y
# sin ellos cambiando una sola cosa. Que la cifra sea solo la suya lo impide el código (capa 2); esto evita que el
# modelo la presente como si fuera de la empresa.
CLIENT_LINE = (
    "\nCliente identificado en esta sesión: {client_id}. Solo ves los datos de este cliente: si te preguntan por la "
    "empresa o por otros clientes, di que no puedes dar esos datos en vez de dar una cifra."
)


# Va en las Versions de las métricas y en la respuesta: cámbiala si cambias el prompt
PROMPT_VERSION = "agent_prompt_v2"

# El mensaje de `agente_minimo.py` de la sesión 1 al llegar al límite de pasos: al usuario no le habla de pasos.
LIMIT_MESSAGE = "No he podido completar la consulta. Te paso con un compañero del equipo."


def _sources(runs: list[QueryDbRun]) -> list[Source]:
    """Una fuente por cada consulta que salió bien, en el orden en que se pidieron."""
    return [
        Source(type=SourceType.db, views=q.metrics.views_used if q.metrics else [], rows=len(q.rows), sql=q.sql)
        for run in runs
        for q in run.result.queries
    ]


def _metrics_fields(
    messages: list[BaseMessage], tool_messages: list[ToolMessage], runs: list[QueryDbRun], sources: list[Source]
) -> dict[str, Any]:
    """Los totales de `AgentMetrics`, sacados de los mensajes que deja el grafo (sin contadores propios).

    `iterations` = llamadas al modelo del agente, como el «paso» de `agente_minimo.py`. Los tokens y `llm_ms` salen de
    la respuesta de Ollama de cada llamada (`response_metadata`); `tools_ms`, de lo que midió cada `query_db`.
    """
    answers = [m for m in messages if isinstance(m, AIMessage)]
    return {
        "iterations": len(answers),
        "llm_call_count": len(answers),
        "tool_call_count": len(tool_messages),
        "tools_used": list(dict.fromkeys(m.name for m in tool_messages if m.name)),
        "input_tokens": sum(m.response_metadata.get("prompt_eval_count") or 0 for m in answers),
        "output_tokens": sum(m.response_metadata.get("eval_count") or 0 for m in answers),
        "llm_ms": round(sum(m.response_metadata.get("total_duration") or 0 for m in answers) / 1_000_000, 3),
        "tools_ms": round(sum(run.latency_ms for run in runs), 3),
        "answered_without_data": not sources,
    }


def respond(
    question: str, *, con: duckdb.DuckDBPyConnection, session: Session | None = None, guardrails: bool = True
) -> AgentAnswer:
    """Responde la pregunta con el agente: decide si consulta la base y redacta con los datos.

    `session` es quién pregunta (el `contexto` de clase): el cliente identificado y su rol. `guardrails` enciende los
    guardarraíles (TRAVEL-011), como `crear_agente(…, guardas=True)` de `sesion2/permisos.py` del tema 9: por
    defecto encendidos y, con ellos, el cliente es obligatorio.
    """
    # Como `estado_inicial()` de `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/asistente/flujo.py`
    if not (question or "").strip():
        raise ComponentError("empty_question", "agent", "La pregunta está vacía.")
    if guardrails and session is None:
        raise ComponentError("missing_client", "agent", "Falta el cliente de la sesión: el chat es solo para clientes.")
    role = profile(session)
    if guardrails and session is not None:
        check_client(con, session)
    question = question.strip()
    versions = Versions(prompt_version=PROMPT_VERSION)
    # `recursion_limit: 20` como `conversar()` de la sesión 3; 1 vuelta = agente → herramientas = 2 pasos
    recursion_limit = int(os.environ.get("AGENT_RECURSION_LIMIT", "20"))
    # Telemetría: un span `agent.respond` por pregunta; los `llm.agent` y los de text2sql cuelgan de él. input_text:
    # solo se guardan su longitud y un hash, nunca el texto de la pregunta.
    with span(
        "agent.respond", component=Component.agent, metrics_cls=AgentMetrics, input_text=question, versions=versions
    ) as s:
        instructions = INSTRUCTIONS
        if session is not None:
            instructions += CLIENT_LINE.format(client_id=session.client_id)
        # Mínimo privilegio, capa de perfil: el modelo solo recibe las tools de su rol (`PERFILES` de clase)
        tools = [TOOL_BUILDERS[name](con) for name in PROFILES[role]]
        agent = build_agent(build_model(), tools, instructions, versions)
        config: RunnableConfig = {"recursion_limit": recursion_limit}
        try:
            messages = agent.invoke({"messages": [("user", question)]}, config)["messages"]
        except GraphRecursionError:
            # Desvío: en clase no se captura. Aquí se corta con el mensaje fijo de la sesión 1 y la API decide si
            # escala. `invoke` pierde los mensajes al cortar: el evento queda como error, con las métricas base (el
            # span se cierra y se escribe igual al salir del `with` con este return).
            s.status = Status.error
            s.error_type = AgentStatus.recursion_limit_reached.value
            s.error_message = f"Se alcanzó el límite de {recursion_limit} pasos del grafo sin respuesta final."
            return AgentAnswer(
                answer=LIMIT_MESSAGE,
                status=AgentStatus.recursion_limit_reached,
                answered_without_data=True,
                versions=versions,
                trace_id=s.trace_id,
            )
        except Exception as exc:
            if (error := as_component_error(exc)) is None:
                raise
            raise error from exc
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        runs = [m.artifact for m in tool_messages if isinstance(m.artifact, QueryDbRun)]
        sources = _sources(runs)
        answer_text = str(messages[-1].content)
        fields = _metrics_fields(messages, tool_messages, runs, sources)
        s.output_text = answer_text
        s.fields.update(fields)

    # Las métricas se validan al cerrar el span: por eso la respuesta se crea fuera del `with` (como en text2sql)
    metrics = s.metrics if isinstance(s.metrics, AgentMetrics) else None
    return AgentAnswer(
        answer=answer_text,
        status=AgentStatus.ok,
        answered_without_data=fields["answered_without_data"],
        sources=sources,
        tools_used=fields["tools_used"],
        versions=versions,
        trace_id=s.trace_id,
        metrics=metrics,
    )
