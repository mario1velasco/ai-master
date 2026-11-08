"""Pregunta → el modelo escribe SQL → el código lo valida y lo ejecuta.

El bucle de `conversar()` en `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/01_preguntar_datos.py`
(el modelo pide `run_sql`, nuestro código lo ejecuta con las barreras) y el resultado de `preguntar()` en
`sesion_3/asistente/datos.py` (las consultas con su SQL y sus filas, para que otro paso redacte).

Telemetría: un span `text2sql.ask` por pregunta y, colgando de él, uno `llm.text2sql` por llamada al modelo
(en `ollama.chat`) y uno `sql.run` por cada SQL.
"""

import json

import duckdb

from contracts.metrics import Component, SqlMetrics, Versions
from contracts.sql import SqlQuery, SqlResult, SqlStatus
from telemetry import span
from text2sql import ollama
from text2sql.guard import TRUNCATION_NOTE, referenced_tables, run_safe_sql
from text2sql.prompt import PROMPT_VERSION, build_system_prompt

MAX_LLM_CALLS = 3  # 1 + 2 reintentos (PROYECTO.md §6); en clase el bucle permitía 4-6 rondas
_REJECTION_REASON_CHARS = 200  # el máximo de SqlMetrics.rejection_reason

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": (
                "Ejecuta UNA consulta SELECT (dialecto DuckDB) sobre las vistas de Viajes Nimbo y devuelve el "
                "resultado en JSON."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Consulta SELECT en DuckDB."}},
                "required": ["query"],
            },
        },
    }
]


def _run_sql(con: duckdb.DuckDBPyConnection, query: str) -> tuple[SqlQuery | None, str]:
    """Un SQL del modelo por el validador, con su span `sql.run`.

    Devuelve la consulta (None si no pasó) y el texto que vuelve al modelo: las filas en JSON o el error.
    """
    with span("sql.run", component=Component.text2sql, metrics_cls=SqlMetrics) as s:
        ok, text = run_safe_sql(con, query)
        s.fields.update(sql_valid=ok, sql_chars=len(query))
        if not ok:
            s.reject("sql_rejected")
            s.fields["rejection_reason"] = text[:_REJECTION_REASON_CHARS]
            return None, text
        truncated = text.endswith(TRUNCATION_NOTE)  # el validador pone el aviso detrás del JSON
        rows = json.loads(text.removesuffix(TRUNCATION_NOTE))
        columns = list(rows[0]) if rows else []
        s.fields.update(
            views_used=list(dict.fromkeys(referenced_tables(con, query))),
            rows_returned=len(rows),
            column_count=len(columns),
            limit_applied=truncated,
        )
    # Las métricas se validan al cerrar el span: por eso la consulta se crea fuera del `with`
    metrics = s.metrics if isinstance(s.metrics, SqlMetrics) else None
    return SqlQuery(sql=query, columns=columns, rows=rows, truncated=truncated, metrics=metrics), text


def ask(question: str, *, con: duckdb.DuckDBPyConnection) -> SqlResult:
    """Pide al modelo el SQL de la pregunta, lo ejecuta con `run_safe_sql` y devuelve las consultas con sus filas."""
    # input_text: el span solo guarda su longitud y un hash, nunca el texto de la pregunta
    with span(
        "text2sql.ask",
        component=Component.text2sql,
        input_text=question,
        versions=Versions(prompt_version=PROMPT_VERSION),
    ):
        messages = [
            {"role": "system", "content": build_system_prompt(con)},
            {"role": "user", "content": question},
        ]
        queries: list[SqlQuery] = []
        llm_calls = 0
        model_text = None
        error = None  # error de la última ronda que el modelo aún no ha corregido
        for attempt in range(MAX_LLM_CALLS):
            message = ollama.chat(messages, TOOLS, retries=attempt)["message"]
            llm_calls += 1
            calls = message.get("tool_calls") or []
            if not calls:  # Responde con texto: no se reintenta (puede ser «ese dato no existe»)
                model_text = (message.get("content") or "").strip()
                break
            messages.append({"role": "assistant", "content": message.get("content", ""), "tool_calls": calls})
            error = None
            for call in calls:
                args = call["function"].get("arguments") or {}
                query = args.get("consulta") or args.get("query") or args.get("sql") or ""
                sql_query, text = _run_sql(con, query)
                if sql_query is not None:
                    queries.append(sql_query)
                else:
                    error = text
                # El resultado (o el error) vuelve al modelo, como en clase: con el error, corrige el SQL
                messages.append({"role": "tool", "content": text, "tool_name": "run_sql"})
            if error is None:  # Todas las consultas pedidas fueron bien: no hace falta otra llamada
                break
        if error is not None:  # Se acabaron los reintentos (o respondió con texto) con un error sin corregir
            status = SqlStatus.sql_error
        elif queries:
            status = SqlStatus.ok
        else:
            status = SqlStatus.no_sql
        return SqlResult(status=status, queries=queries, model_text=model_text, error=error, llm_calls=llm_calls)
