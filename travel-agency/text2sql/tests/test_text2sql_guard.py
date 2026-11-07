import json

import duckdb
import pytest

from text2sql.guard import run_safe_sql


def test_select_on_allowed_view_returns_json_rows(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "SELECT COUNT(*) AS n FROM v_reservas_cliente")

    assert ok is True
    # 7 reservas en los CSV (ver la tabla de trampas de database/AGENTS.md)
    assert json.loads(text) == [{"n": 7}]


@pytest.mark.parametrize("query", ["", "SELEC * FROM v_incidencias"])
def test_empty_or_invalid_sql_returns_controlled_error(con: duckdb.DuckDBPyConnection, query: str) -> None:
    ok, text = run_safe_sql(con, query)

    assert ok is False
    assert text.startswith("ERROR")


def test_rejects_multiple_statements(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "SELECT 1 FROM v_incidencias; SELECT 2 FROM v_incidencias")

    assert ok is False
    assert text == "ERROR: envía exactamente una sentencia."


def test_rejects_non_select_statement(con: duckdb.DuckDBPyConnection) -> None:
    count = "SELECT COUNT(*) FROM v_incidencias"
    rows_before = con.execute(count).fetchone()

    ok, text = run_safe_sql(con, "DELETE FROM v_incidencias")

    assert ok is False
    assert text == "ERROR: solo se permiten consultas SELECT (recibido: DELETE)."
    assert con.execute(count).fetchone() == rows_before


def test_trailing_semicolon_and_spaces_are_ignored(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "  SELECT COUNT(*) FROM v_incidencias;  ")

    assert ok is True, text


def test_join_between_allowed_views_is_accepted(con: duckdb.DuckDBPyConnection) -> None:
    query = """
        SELECT COUNT(*) AS n
        FROM v_reservas_cliente r
        JOIN v_resumen_clientes c ON r.cliente_id = c.cliente_id
    """

    ok, text = run_safe_sql(con, query)

    assert ok is True, text
    # Cada una de las 7 reservas tiene un solo cliente: el JOIN no duplica filas
    assert json.loads(text) == [{"n": 7}]


def test_truncates_to_50_rows_with_notice(con: duckdb.DuckDBPyConnection) -> None:
    # Ninguna vista llega a 50 filas: 11 vuelos × 11 itinerarios = 121 filas
    query = "SELECT v.* FROM v_vuelos_detalle v CROSS JOIN v_itinerarios"

    ok, text = run_safe_sql(con, query)

    assert ok is True, text
    rows, _ = json.JSONDecoder().raw_decode(text)
    assert len(rows) == 50
    assert text.endswith("(resultado recortado a 50 filas)")


def test_decimals_are_rounded_to_two_places(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "SELECT 10 / 3 AS x FROM v_incidencias LIMIT 1")

    assert ok is True, text
    assert json.loads(text) == [{"x": 3.33}]


def test_cannot_read_files_from_disk(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "SELECT * FROM read_csv_auto('/etc/passwd')")

    assert ok is False
    assert text.startswith("ERROR")
    # La primera línea de /etc/passwd en Linux es la del usuario root
    assert "root:" not in text


SEMANTIC_VIEWS = ["v_incidencias", "v_itinerarios", "v_reservas_cliente", "v_resumen_clientes", "v_vuelos_detalle"]


def test_rejects_raw_table_and_lists_allowed_views(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "SELECT * FROM crudo.clientes")

    assert ok is False
    assert "crudo.clientes no está permitida" in text
    assert all(view in text for view in SEMANTIC_VIEWS)
    # crudo.clientes tiene la columna email, que ninguna vista enseña: si la consulta se ejecutara, saldría
    assert "@" not in text


def test_rejects_database_catalog(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "SELECT * FROM information_schema.tables")

    assert ok is False
    assert "information_schema.tables no está permitida" in text
    # Si el catálogo se leyera, saldrían los nombres de las tablas de crudo
    assert "crudo" not in text


def test_cte_over_allowed_views_is_accepted(con: duckdb.DuckDBPyConnection) -> None:
    query = "WITH r AS (SELECT * FROM v_reservas_cliente) SELECT COUNT(*) FROM r"

    ok, text = run_safe_sql(con, query)

    assert ok is True, text
    # Las 7 reservas: el CTE se ejecutó de verdad
    assert [list(row.values()) for row in json.loads(text)] == [[7]]


def test_rejects_table_functions(con: duckdb.DuckDBPyConnection) -> None:
    ok, text = run_safe_sql(con, "SELECT * FROM duckdb_tables()")

    assert ok is False
    assert "duckdb_tables() no está permitida" in text
    # duckdb_tables() lista las tablas de crudo: no pueden salir en la respuesta
    assert "crudo" not in text


@pytest.mark.parametrize(
    ("query", "raw_table"),
    [
        # Un CTE que se llama como una vista permitida, pero lee una tabla cruda
        ("WITH v_incidencias AS (SELECT * FROM crudo.clientes) SELECT * FROM v_incidencias", "crudo.clientes"),
        ("WITH r AS (SELECT * FROM crudo.pagos) SELECT * FROM r", "crudo.pagos"),
    ],
)
def test_cte_cannot_hide_raw_table(con: duckdb.DuckDBPyConnection, query: str, raw_table: str) -> None:
    ok, text = run_safe_sql(con, query)

    assert ok is False
    assert f"{raw_table} no está permitida" in text


def test_rejects_reading_from_anything_but_views(con: duckdb.DuckDBPyConnection) -> None:
    # DuckDB convierte SHOW ALL TABLES en un SELECT sobre un SHOW_REF, que lista todas las tablas
    ok, text = run_safe_sql(con, "SHOW ALL TABLES")

    assert ok is False
    assert text.startswith("ERROR")
    assert "crudo" not in text
