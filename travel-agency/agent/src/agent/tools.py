"""La tool `consultar_bbdd`: el agente pide datos en lenguaje natural y `text2sql.ask()` los saca de la base.

Como las tools de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/herramientas_lc.py` (`@tool`, el docstring es
la descripción que lee el modelo). Desvío: `response_format="content_and_artifact"`, para que el modelo reciba el
texto y el código se quede con el `SqlResult` entero (las fuentes salen de ahí).
"""

import json

import duckdb
from langchain_core.tools import BaseTool, tool

from contracts.sql import SqlResult
from text2sql import ask


def _for_model(result: SqlResult) -> str:
    """Lo que lee el modelo: por cada consulta, su SQL, sus filas y si se recortó. Sin métricas.

    Como la tool de datos de `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/15_analista.py`, que
    solo devuelve el resultado; aquí, además, el SQL. Las métricas ya están en los logs de la traza.
    """
    queries = [{"sql": q.sql, "rows": q.rows, "truncated": q.truncated} for q in result.queries]
    return json.dumps(queries, ensure_ascii=False)


def build_query_db_tool(con: duckdb.DuckDBPyConnection) -> BaseTool:
    """La tool sobre la conexión `con`."""

    @tool(response_format="content_and_artifact")
    def consultar_bbdd(pregunta: str) -> tuple[str, SqlResult]:
        """Consulta la base de datos de Viajes Nimbo con una pregunta en lenguaje natural."""
        result = ask(pregunta, con=con)
        return _for_model(result), result

    return consultar_bbdd
