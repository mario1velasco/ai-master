"""La tool `query_db`: el agente pide datos en lenguaje natural y `text2sql.ask()` los saca de la base.

Como las tools de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/herramientas_lc.py` (`@tool`, el docstring es
la descripción que lee el modelo). Desvío: `response_format="content_and_artifact"`, para que el modelo reciba el
texto y el código se quede con el `SqlResult` entero (las fuentes salen de ahí) y con lo que tardó (`tools_ms`).
"""

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

import duckdb
from langchain_core.tools import BaseTool, tool

from agent.guardrails import Guardrails
from contracts.agent import Block, BlockType, Session
from contracts.sql import SqlResult, SqlStatus
from text2sql import ask

# Lo que lee el modelo para decidir. Reparte el trabajo: el agente decide qué datos necesita y text2sql cómo sacarlos
# (solo él ve el esquema). En una constante y no en el docstring, para que no le lleguen saltos de línea ni sangría.
# Desde TRAVEL-011, la primera frase dice el alcance: solo los datos del cliente de la sesión (lo impone la capa 2).
QUERY_DB_DESCRIPTION = (
    "Consulta la base de datos de Viajes Nimbo: solo consulta los datos del cliente identificado en esta sesión. "
    "Pasa una pregunta en lenguaje natural que se entienda sola: no "
    "conoce la conversación, así que incluye los identificadores (cliente, reserva, vuelo). Puedes pedir varios "
    "datos en la misma pregunta. Si un dato depende de otro (por ejemplo, el vuelo de la última reserva de un "
    "cliente), pide primero el que falta y usa su resultado en la siguiente pregunta."
)

# Desvío: si el modelo pide varias `query_db` en la misma respuesta, `ToolNode` las ejecuta en paralelo, y DuckDB no
# admite dos llamadas a la vez en la misma conexión («connection is busy»). El candado las pone en fila. En clase no
# pasa porque las tools de `tienda.py` leen diccionarios en memoria. No se pierde velocidad: Ollama atiende al Qwen
# de una en una en la GPU de 4 GB.
_DB_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class QueryDbRun:
    """El `artifact` de cada llamada a `query_db`: lo que el código guarda y el modelo no ve."""

    result: SqlResult
    latency_ms: float  # lo que tardó `ask()`, para `AgentMetrics.tools_ms`


def _for_model(result: SqlResult) -> str:
    """Lo que lee el modelo: por cada consulta, su SQL, sus filas y si se recortó. Sin métricas.

    Como la tool de datos de `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/15_analista.py`, que
    solo devuelve el resultado; aquí, además, el SQL. Las métricas ya están en los logs de la traza.
    Si text2sql respondió con texto sin SQL (`no_sql`, p. ej. «ese dato no existe»), el modelo recibe ese texto; si
    acabó con un SQL que el validador no dejó pasar (`sql_error`), las consultas que sí salieron bien (si las hay) y,
    en la línea siguiente, el último error del validador: así ve lo mismo que cuentan las fuentes.
    """
    if result.status is SqlStatus.no_sql:
        return result.model_text or ""
    queries = json.dumps(
        [{"sql": q.sql, "rows": q.rows, "truncated": q.truncated} for q in result.queries], ensure_ascii=False
    )
    if result.status is not SqlStatus.sql_error:
        return queries
    error = result.error or ""
    return f"{queries}\n{error}" if result.queries else error


def _blocked(reason: str) -> tuple[str, Block]:
    """Lo que recibe el modelo cuando un guardarraíl bloquea `query_db` («Acción no permitida: …», como en clase).

    El artifact es el mismo bloqueo que queda en `AgentAnswer.blocks`: así la llamada no cuenta como herramienta usada
    ni como fuente, y un error de LangGraph (tool inventada, argumentos mal), que no lo trae, sí cuenta.
    """
    return f"Acción no permitida: {reason}", Block(type=BlockType.tool, reason=reason)


def _timed_ask(question: str, con: duckdb.DuckDBPyConnection) -> QueryDbRun:
    """`text2sql.ask()` y lo que tardó (para `AgentMetrics.tools_ms`)."""
    start = perf_counter()
    result = ask(question, con=con)
    return QueryDbRun(result=result, latency_ms=round((perf_counter() - start) * 1000, 3))


def build_query_db_tool(con: duckdb.DuckDBPyConnection, guards: Guardrails | None, session: Session | None) -> BaseTool:
    """La tool sobre la conexión `con`, con los guardarraíles del turno (None si están apagados)."""
    if guards is not None and session is None:  # fallo cerrado: sin sesión no se puede comprobar nada
        raise ValueError("Con guardarraíles, query_db necesita la sesión del cliente.")

    @tool(description=QUERY_DB_DESCRIPTION, response_format="content_and_artifact")
    def query_db(question: str) -> tuple[str, QueryDbRun | Block]:
        with _DB_LOCK:  # también las comprobaciones, que consultan la misma conexión
            # Capa 1, antes de ejecutar (`revisar_herramienta` de clase)
            if guards is not None and session is not None:
                if (reason := guards.check_tool("query_db", {"question": question}, session)) is not None:
                    return _blocked(reason)
            run = _timed_ask(question, con)
            # Capa 3, antes de que el modelo vea las filas: si alguna es de otro cliente, no ve ninguna
            if guards is not None and session is not None:
                if (reason := guards.check_result(run.result, session)) is not None:
                    return _blocked(reason)
        return _for_model(run.result), run

    return query_db


# El catálogo de tools por nombre, como `CATALOGO` de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/comun/
# herramientas.py`: los perfiles (`profiles.py`) eligen de aquí. Cada una se construye sobre la conexión del turno,
# con sus guardarraíles y la sesión.
TOOL_BUILDERS: dict[str, Callable[[duckdb.DuckDBPyConnection, Guardrails | None, Session | None], BaseTool]] = {
    "query_db": build_query_db_tool,
}
