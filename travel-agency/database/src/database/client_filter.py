"""Lo que la base sabe de los clientes para los guardarraíles del agente (TRAVEL-011).

- `open_client_filtered_connection`: una conexión que solo ve los datos de un cliente (capa 2).
- `owner_of` y `OWNER_COLUMNS`: de quién es un id y qué columnas lo traen (capas 1 y 3).
- `clients_personal_data`: el email y el nombre completo de cada cliente (salida).

Las reglas (bloquear lo de otro cliente, sustituir la respuesta) son del agente (`agent/guardrails.py`); aquí solo
dónde está cada cosa en la base.

La conexión filtrada:

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

from database.schema import _FINGERPRINT_VARIABLE, _scalar, cached_schema

CLIENT_FILTERED_SCHEMA = "client_filtered_schema"
# De quién es cada id: la vista donde se busca, según su letra (cliente, reserva o incidencia)
_OWNER_QUERIES = {
    "C": "SELECT cliente_id FROM v_resumen_clientes WHERE cliente_id = ?",
    "R": "SELECT cliente_id FROM v_reservas_cliente WHERE reserva_id = ? LIMIT 1",
    "I": "SELECT cliente_id FROM v_incidencias WHERE incidencia_id = ?",
}
# Las columnas con dueño que puede traer una fila de las vistas (sin alias)
OWNER_COLUMNS = ("cliente_id", "reserva_id", "incidencia_id")
# El email y el nombre completo de cada cliente. El email solo está en `crudo.clientes` (lo lee el código de los
# guardarraíles, no el SQL del modelo, que el validador de text2sql no deja pasar de las vistas)
_CLIENTS_PERSONAL_DATA = "SELECT cliente_id, email, nombre || ' ' || apellidos FROM crudo.clientes"
# Las vistas con dueño se filtran por su `cliente_id`
OWNED_VIEWS = ("v_reservas_cliente", "v_tramos", "v_itinerarios", "v_incidencias", "v_resumen_clientes")


def _filtered_view_sql(view: str, where: str) -> str:
    """La vista de `main` con el mismo nombre en el esquema filtrado, con solo las filas que cumplen `where`."""
    return f"CREATE OR REPLACE VIEW {CLIENT_FILTERED_SCHEMA}.{view} AS SELECT * FROM main.{view} WHERE {where}"


@contextmanager
def open_client_filtered_connection(
    con: duckdb.DuckDBPyConnection, client_id: str
) -> Generator[duckdb.DuckDBPyConnection]:
    """Una conexión sobre `con` que solo ve los datos de `client_id`, abierta mientras dura el `with`."""
    quoted_client_id = "'" + client_id.replace("'", "''") + "'"  # una vista no admite parámetros: va escrito
    # El esquema de las vistas (`cached_schema`, el que ve el modelo de text2sql) es uno para todos: se prepara con
    # `con`, que lo ve todo, antes de filtrar. Y el cursor lleva la misma huella que `con`: sin ella (las variables
    # de DuckDB son de cada conexión) no encontraría el guardado y lo generaría desde las vistas filtradas, con los
    # valores de este cliente, y así se guardaría para todos.
    cached_schema(con)
    fingerprint = _scalar(con, f"SELECT getvariable('{_FINGERPRINT_VARIABLE}')")  # como la lee `cached_schema`
    cursor = con.cursor()
    try:
        cursor.execute(f"SET VARIABLE {_FINGERPRINT_VARIABLE} = ?", [fingerprint])
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {CLIENT_FILTERED_SCHEMA}")
        for view in OWNED_VIEWS:
            cursor.execute(_filtered_view_sql(view, f"cliente_id = {quoted_client_id}"))
        # `v_vuelos_detalle` no tiene dueño (son todos los vuelos de la empresa): solo los vuelos de sus reservas
        own_flights = f"vuelo_id IN (SELECT vuelo_id FROM main.v_tramos WHERE cliente_id = {quoted_client_id})"
        cursor.execute(_filtered_view_sql("v_vuelos_detalle", own_flights))
        cursor.execute(f"SET search_path = '{CLIENT_FILTERED_SCHEMA},main'")
        yield cursor
    finally:
        cursor.execute(f"DROP SCHEMA IF EXISTS {CLIENT_FILTERED_SCHEMA} CASCADE")
        cursor.close()


def owner_of(con: duckdb.DuckDBPyConnection, owned_id: str) -> str | None:
    """El cliente dueño de un id (`C-…`, `R-…` o `I-…`), o None si no existe o no es un id con dueño."""
    query = _OWNER_QUERIES.get(owned_id[:1])
    rows = con.execute(query, [owned_id]).fetchall() if query is not None else []
    return rows[0][0] if rows else None


def clients_personal_data(con: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    """Los datos personales de cada cliente (email y nombre completo), por su `cliente_id`. Sin los vacíos."""
    return {
        client_id: [value for value in personal if value]
        for client_id, *personal in con.execute(_CLIENTS_PERSONAL_DATA).fetchall()
    }
