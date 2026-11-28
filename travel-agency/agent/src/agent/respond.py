"""`respond()`: una pregunta al agente, de principio a fin.

Como `conversar()` de `08_ia_agentica_automatiz_agentes/tema8-agentes/sesion3/agente_langgraph.py`: el grafo de
`construir_agente` con las instrucciones y las tools, `invoke` con la pregunta y la respuesta es el último mensaje.
Las fuentes y las herramientas usadas salen de los mensajes que deja el grafo, sin contadores propios.
"""

import os
from contextlib import AbstractContextManager, nullcontext
from typing import Any

import duckdb
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError

from agent.graph import build_agent
from agent.guardrails import Guardrails
from agent.model import as_component_error, build_model
from agent.profiles import PROFILES, profile
from agent.tools import TOOL_BUILDERS, QueryDbRun
from contracts.agent import AgentAnswer, AgentStatus, Block, BlockType, Session, Source, SourceType
from contracts.errors import ComponentError
from contracts.metrics import AgentMetrics, Component, Status, Versions
from database.client_filter import open_client_filtered_connection
from telemetry import Span, span

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


def _validated_question(question: str) -> str:
    """La pregunta sin espacios alrededor; vacía, `empty_question`.

    Como `estado_inicial()` de `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/asistente/flujo.py`.
    """
    question = (question or "").strip()
    if not question:
        raise ComponentError("empty_question", "agent", "La pregunta está vacía.")
    return question


def _guard_input(
    con: duckdb.DuckDBPyConnection, session: Session | None, question: str
) -> tuple[Guardrails, str, str | None]:
    """Con los guardarraíles: la sesión (cliente que existe) y la entrada, antes del span y del modelo.

    Devuelve los guardarraíles del turno (un registro por turno), la pregunta ya enmascarada y, si el mensaje no debe
    llegar al modelo, la respuesta para el cliente (o None). La entrada va antes del primer log, como en
    `comun/agente.py`: el hash que guarda el span es el del texto enmascarado.
    """
    guards = Guardrails(con)
    guards.check_session(session)
    question, refusal = guards.check_input(question)
    return guards, question, refusal


def _instructions(session: Session | None) -> str:
    """Las instrucciones, con la línea del cliente si hay sesión (no depende de los guardarraíles)."""
    if session is None:
        return INSTRUCTIONS
    return INSTRUCTIONS + CLIENT_LINE.format(client_id=session.client_id)


def _turn_connection(
    con: duckdb.DuckDBPyConnection, guards: Guardrails | None, session: Session | None
) -> AbstractContextManager[duckdb.DuckDBPyConnection]:
    """La conexión que consulta text2sql en este turno, para usar con `with`.

    Capa 2: con los guardarraíles, una que solo ve las filas del cliente (las vistas filtradas de
    `database.client_filter`); sin ellos, la de siempre.
    """
    if guards is not None and session is not None:
        return open_client_filtered_connection(con, session.client_id)
    return nullcontext(con)


def _run_graph(
    question: str,
    *,
    turn_con: duckdb.DuckDBPyConnection,
    guards: Guardrails | None,
    session: Session | None,
    role: str,
    versions: Versions,
    recursion_limit: int,
) -> list[BaseMessage]:
    """El grafo de `construir_agente` con las tools del perfil: devuelve los mensajes que deja.

    `GraphRecursionError` sube tal cual (lo responde `respond()`); los errores de Ollama, como `ComponentError`.
    """
    # Mínimo privilegio, capa de perfil: el modelo solo recibe las tools de su rol (`PERFILES` de clase)
    tools = [TOOL_BUILDERS[name](turn_con, guards, session) for name in PROFILES[role]]
    agent = build_agent(build_model(), tools, _instructions(session), versions)
    config: RunnableConfig = {"recursion_limit": recursion_limit}
    try:
        return agent.invoke({"messages": [("user", question)]}, config)["messages"]
    except GraphRecursionError:
        raise
    except Exception as exc:
        if (error := as_component_error(exc)) is None:
            raise
        raise error from exc


def _recursion_limit_answer(
    agent_span: Span, recursion_limit: int, blocks: list[Block], versions: Versions
) -> AgentAnswer:
    """La respuesta al llegar al límite de pasos: el mensaje fijo de la sesión 1, sin lanzar error.

    Desvío: en clase no se captura. Aquí se corta y la API decide si escala. `invoke` pierde los mensajes al cortar: el
    evento queda como error, con las métricas base (el span se escribe igual al salir del `with`).
    """
    agent_span.status = Status.error
    agent_span.error_type = AgentStatus.recursion_limit_reached.value
    agent_span.error_message = f"Se alcanzó el límite de {recursion_limit} pasos del grafo sin respuesta final."
    return AgentAnswer(
        answer=LIMIT_MESSAGE,
        status=AgentStatus.recursion_limit_reached,
        answered_without_data=True,
        blocks=blocks,
        versions=versions,
        trace_id=agent_span.trace_id,
    )


def _executed_tool_messages(messages: list[BaseMessage]) -> list[ToolMessage]:
    """Los mensajes de las herramientas que cuentan como usadas: todas menos las que bloquearon los guardarraíles.

    Una bloqueada trae como artifact el `Block` de su bloqueo y no cuenta (como en clase, `comun/agente.py`); que el
    modelo lo intentó se ve en `blocks`. Un error de LangGraph (tool inventada, argumentos mal) sí cuenta.
    """
    return [m for m in messages if isinstance(m, ToolMessage) and not isinstance(m.artifact, Block)]


def _checked_answer(messages: list[BaseMessage], guards: Guardrails | None, session: Session | None) -> str:
    """La respuesta del modelo (el último mensaje), revisada por la salida si hay guardarraíles.

    Va antes de enviarla y de guardarla en la telemetría, como en `comun/agente.py`.
    """
    answer_text = str(messages[-1].content)
    if guards is not None and session is not None:
        answer_text, _output_block = guards.check_output(answer_text, session)  # el motivo ya está en `guards.log`
    return answer_text


def _block_counts(blocks: list[Block]) -> dict[str, int]:
    """Los recuentos por punto de control para `AgentMetrics` (el detalle va en `AgentAnswer.blocks`)."""
    return {
        "input_blocks": sum(b.type is BlockType.input for b in blocks),
        "tool_blocks": sum(b.type is BlockType.tool for b in blocks),
        "output_blocks": sum(b.type is BlockType.output for b in blocks),
    }


def respond(
    question: str, *, con: duckdb.DuckDBPyConnection, session: Session | None = None, guardrails: bool = True
) -> AgentAnswer:
    """Responde la pregunta con el agente: decide si consulta la base y redacta con los datos.

    `session` es quién pregunta (el `contexto` de clase): el cliente identificado y su rol. `guardrails` enciende los
    guardarraíles (TRAVEL-011), como `crear_agente(…, guardas=True)` de `sesion2/permisos.py` del tema 9: por
    defecto encendidos y, con ellos, el cliente es obligatorio. El orden es el del bucle de clase: entrada → modelo y
    herramientas → salida.
    """
    question = _validated_question(question)
    role = profile(session)  # el perfil se aplica siempre, también sin guardarraíles (como `PERFILES` de clase)
    guards, question, refusal = _guard_input(con, session, question) if guardrails else (None, question, None)
    # La misma lista que `guards.log`: las tools y la salida le siguen añadiendo bloqueos durante el turno
    blocks = guards.log if guards is not None else []
    versions = Versions(prompt_version=PROMPT_VERSION)
    # `recursion_limit: 20` como `conversar()` de la sesión 3; 1 vuelta = agente → herramientas = 2 pasos
    recursion_limit = int(os.environ.get("AGENT_RECURSION_LIMIT", "20"))
    # Telemetría: un span `agent.respond` por pregunta; los `llm.agent` y los de text2sql cuelgan de él. input_text:
    # solo se guardan su longitud y un hash, nunca el texto de la pregunta.
    with (
        span(
            "agent.respond", component=Component.agent, metrics_cls=AgentMetrics, input_text=question, versions=versions
        ) as agent_span,
        _turn_connection(con, guards, session) as turn_con,
    ):
        # Como el bloqueo de entrada de `comun/agente.py`: si la entrada se bloqueó, el mensaje no llega al modelo y
        # el turno acaba con la respuesta del guardarraíl (sin datos; un bloqueo no es un error)
        try:
            messages = (
                []
                if refusal is not None
                else _run_graph(
                    question,
                    turn_con=turn_con,
                    guards=guards,
                    session=session,
                    role=role,
                    versions=versions,
                    recursion_limit=recursion_limit,
                )
            )
        except GraphRecursionError:
            return _recursion_limit_answer(agent_span, recursion_limit, blocks, versions)
        tool_messages = _executed_tool_messages(messages)
        runs = [m.artifact for m in tool_messages if isinstance(m.artifact, QueryDbRun)]
        sources = _sources(runs)
        answer_text = refusal if refusal is not None else _checked_answer(messages, guards, session)
        fields = _metrics_fields(messages, tool_messages, runs, sources)
        agent_span.output_text = answer_text
        agent_span.fields.update(fields | _block_counts(blocks))

    # Las métricas se validan al cerrar el span: por eso la respuesta se crea fuera del `with` (como en text2sql)
    metrics = agent_span.metrics if isinstance(agent_span.metrics, AgentMetrics) else None
    return AgentAnswer(
        answer=answer_text,
        status=AgentStatus.ok,
        answered_without_data=not sources,
        sources=sources,
        tools_used=fields["tools_used"],
        blocks=blocks,
        versions=versions,
        trace_id=agent_span.trace_id,
        metrics=metrics,
    )
