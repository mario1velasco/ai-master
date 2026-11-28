"""Una conexión que solo ve los datos de un cliente (TRAVEL-011, capa 2 de los guardarraíles del agente).

Sin ejemplo en clase (probado el 2026-11-27). Abre una conexión (un cursor de `con`) y le aplica los filtros del
cliente: crea el esquema `client_filtered_schema` con las vistas de `main` filtradas, con el mismo nombre, y hace que
se busque primero en él (`search_path`). Así cualquier SQL sobre esa conexión, el del modelo de text2sql o una
consulta fija, solo lee las filas del cliente, sin cambiar las vistas ni el SQL. La conexión de quien llama no cambia:
al salir del `with` se borra el esquema y se cierra el cursor.

Vive aquí, junto a las vistas (`semantic_layer.py`), porque qué vistas tienen dueño y cómo se filtra cada una depende
de cómo están definidas. Cuándo se usa lo decide quien llama: en el agente, `respond()` con los guardarraíles
encendidos.
"""

from collections.abc import Generator
from contextlib import contextmanager

import duckdb

from database.schema import _FINGERPRINT_VARIABLE, cached_schema

CLIENT_FILTERED_SCHEMA = "client_filtered_schema"
# Las vistas con dueño se filtran por su `cliente_id`
OWNED_VIEWS = ("v_reservas_cliente", "v_tramos", "v_itinerarios", "v_incidencias", "v_resumen_clientes")


@contextmanager
def open_client_filtered_connection(
    con: duckdb.DuckDBPyConnection, client_id: str
) -> Generator[duckdb.DuckDBPyConnection]:
    """Una conexión sobre `con` que solo ve los datos de `client_id`, abierta mientras dura el `with`."""
    client = client_id.replace("'", "''")  # una vista no admite parámetros: el id va escrito en el SQL
    # El esquema de las vistas (`cached_schema`, el que ve el modelo de text2sql) es uno para todos: se prepara con
    # `con`, que lo ve todo, antes de filtrar. Y el cursor lleva la misma huella que `con`: sin ella (las variables
    # de DuckDB son de cada conexión) no encontraría el guardado y lo generaría desde las vistas filtradas, con los
    # valores de este cliente, y así se guardaría para todos.
    cached_schema(con)
    [(fingerprint,)] = con.execute(f"SELECT getvariable('{_FINGERPRINT_VARIABLE}')").fetchall()
    cursor = con.cursor()
    try:
        cursor.execute(f"SET VARIABLE {_FINGERPRINT_VARIABLE} = ?", [fingerprint])
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {CLIENT_FILTERED_SCHEMA}")
        for view in OWNED_VIEWS:
            cursor.execute(
                f"CREATE OR REPLACE VIEW {CLIENT_FILTERED_SCHEMA}.{view} AS "
                f"SELECT * FROM main.{view} WHERE cliente_id = '{client}'"
            )
        # `v_vuelos_detalle` no tiene dueño (son todos los vuelos de la empresa): solo los vuelos de sus reservas
        cursor.execute(
            f"CREATE OR REPLACE VIEW {CLIENT_FILTERED_SCHEMA}.v_vuelos_detalle AS "
            "SELECT * FROM main.v_vuelos_detalle "
            f"WHERE vuelo_id IN (SELECT vuelo_id FROM main.v_tramos WHERE cliente_id = '{client}')"
        )
        cursor.execute(f"SET search_path = '{CLIENT_FILTERED_SCHEMA},main'")
        yield cursor
    finally:
        cursor.execute(f"DROP SCHEMA IF EXISTS {CLIENT_FILTERED_SCHEMA} CASCADE")
        cursor.close()
