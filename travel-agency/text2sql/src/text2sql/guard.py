"""Barrera del SQL que escribe el modelo: el modelo propone, el código decide.

Igual que `ejecutar_sql_seguro` de `07_llm_open_source/clase_01/Ejercicios/practica/08_herramienta_sql.py`.
Desvío: lista blanca de vistas (`PROYECTO.md` §6). Solo se pueden leer las vistas de «main», las mismas que
el esquema le enseña al modelo; las tablas del SQL salen de su árbol (`json_serialize_sql` de DuckDB).
"""

import json
from typing import cast

import duckdb

MAX_ROWS = 50


def _allowed_views(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Lo que hay en «main» (las vistas): la misma consulta que `esquema()` en DropLab S2."""
    return [
        r[0]
        for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1"
        ).fetchall()
    ]


def _source_name(ref: dict) -> str | None:
    """Qué lee un nodo del FROM. None si solo junta o envuelve otros (JOIN, subconsulta…), que se miran por dentro."""
    match ref["type"]:
        case "BASE_TABLE":
            schema, table = ref["schema_name"], ref["table_name"]
            return f"{schema}.{table}" if schema else table
        case "TABLE_FUNCTION":  # duckdb_tables(), read_csv_auto()…: nunca son vistas
            return f"{ref['function']['function_name']}()"
        case "JOIN" | "SUBQUERY" | "EXPRESSION_LIST" | "EMPTY":
            return None
        case other:  # SHOW_REF (SHOW ALL TABLES) o cualquier tipo nuevo de DuckDB: no es una vista
            return other


def _referenced_tables(con: duckdb.DuckDBPyConnection, query: str) -> list[str]:
    """Las tablas que lee el SQL, con su esquema si lo lleva (p. ej. «crudo.clientes»). Los CTE no cuentan."""
    [(tree_json,)] = con.execute("SELECT json_serialize_sql(?)", [query]).fetchall()
    tables: list[str] = []
    ctes: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if "cte_map" in node:
                ctes.update(cte["key"].lower() for cte in node["cte_map"]["map"])
            for key, value in node.items():
                # Lo que se lee va en el FROM (from_table) o a un lado de un JOIN; las expresiones llevan «class»
                if key in ("from_table", "left", "right") and isinstance(value, dict) and "class" not in value:
                    name = _source_name(value)
                    if name is not None:
                        tables.append(name)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(json.loads(tree_json))
    # Un CTE se nombra sin esquema: «crudo.r» sigue siendo una tabla aunque exista un CTE «r»
    return [table for table in tables if table.lower() not in ctes]


def run_safe_sql(con: duckdb.DuckDBPyConnection, query: str) -> tuple[bool, str]:
    """Ejecuta el SQL del modelo con las barreras puestas en el código."""
    query = (query or "").strip().rstrip(";")
    if not query:
        return False, "ERROR: la consulta está vacía."
    try:
        statements = duckdb.extract_statements(query)
    except duckdb.Error as exc:
        return False, f"ERROR de sintaxis: {exc}"
    if len(statements) != 1:
        return False, "ERROR: envía exactamente una sentencia."
    if statements[0].type != duckdb.StatementType.SELECT:
        return False, f"ERROR: solo se permiten consultas SELECT (recibido: {statements[0].type.name})."
    views = _allowed_views(con)
    allowed = {view.lower() for view in views}  # DuckDB no distingue mayúsculas en los nombres
    for table in _referenced_tables(con, query):
        if table.lower() not in allowed:
            return False, f"ERROR: la vista {table} no está permitida. Vistas permitidas: {', '.join(views)}."
    try:
        df = con.execute(query).fetchdf()
    except duckdb.Error as exc:
        return False, f"ERROR al ejecutar: {exc}"
    truncated = len(df) > MAX_ROWS
    df = df.head(MAX_ROWS)
    for col in df.select_dtypes("float").columns:  # importes exactos a 2 decimales
        df[col] = df[col].round(2)
    # Sin archivo de destino, pandas siempre devuelve el texto (su tipo dice str | None)
    text = cast(str, df.to_json(orient="records", force_ascii=False, date_format="iso"))
    if truncated:
        text += f"  (resultado recortado a {MAX_ROWS} filas)"
    return True, text
