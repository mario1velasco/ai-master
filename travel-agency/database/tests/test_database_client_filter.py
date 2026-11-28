"""La conexión filtrada por cliente (TRAVEL-011, capa 2): `database.client_filter.open_client_filtered_connection`.

Lo que ve el modelo con ella (solo las filas del cliente) se prueba en el agente
(`agent/tests/test_agent_guardrails.py`); aquí, que cubre todas las vistas y que deja la base como estaba.
"""

import duckdb

from database.client_filter import CLIENT_FILTERED_SCHEMA, open_client_filtered_connection

TABLES_IN = "SELECT table_name FROM information_schema.tables WHERE table_schema = ? ORDER BY 1"


def test_every_view_has_its_client_filtered_version(con: duckdb.DuckDBPyConnection) -> None:
    # Si se añade una vista a `main` y no se filtra, la conexión filtrada la leería entera: con todos los clientes
    main_views = [r[0] for r in con.execute(TABLES_IN, ["main"]).fetchall()]

    with open_client_filtered_connection(con, "C-001") as db:
        filtered_views = [r[0] for r in db.execute(TABLES_IN, [CLIENT_FILTERED_SCHEMA]).fetchall()]

    assert filtered_views == main_views


def test_filtered_schema_removed_on_close(con: duckdb.DuckDBPyConnection) -> None:
    with open_client_filtered_connection(con, "C-001"):
        pass

    assert con.execute(TABLES_IN, [CLIENT_FILTERED_SCHEMA]).fetchall() == []
