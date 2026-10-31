"""Auditoría de integridad de los CSV, como 07_llm_open_source/clase_01/.../practica/02_auditoria_integridad.py.

Allí se hace con pandas; aquí con SQL sobre el esquema `crudo`, porque los CSV ya están cargados en DuckDB.
"""

import duckdb
import pytest

# == 1. Claves únicas ==
KEYS = [
    ("aerolineas", "aerolinea_id"),
    ("aeropuertos", "aeropuerto_id"),
    ("clientes", "cliente_id"),
    ("vuelos", "vuelo_id"),
    ("reservas", "reserva_id"),
    ("reservas_tramos", "reserva_id, orden"),
    ("pagos", "pago_id"),
    ("incidencias", "incidencia_id"),
]

# == 2. Integridad referencial: (tabla, columna) → (tabla, clave) ==
REFERENCES = [
    ("vuelos", "aerolinea_id", "aerolineas", "aerolinea_id"),
    ("vuelos", "origen", "aeropuertos", "aeropuerto_id"),
    ("vuelos", "destino", "aeropuertos", "aeropuerto_id"),
    ("reservas", "cliente_id", "clientes", "cliente_id"),
    ("reservas_tramos", "reserva_id", "reservas", "reserva_id"),
    ("reservas_tramos", "vuelo_id", "vuelos", "vuelo_id"),
    ("pagos", "reserva_id", "reservas", "reserva_id"),
    ("incidencias", "reserva_id", "reservas", "reserva_id"),
    ("incidencias", "vuelo_id", "vuelos", "vuelo_id"),
]


@pytest.mark.parametrize(("table", "key"), KEYS)
def test_database_unique_key(con: duckdb.DuckDBPyConnection, table: str, key: str) -> None:
    duplicates = con.execute(f"SELECT {key}, COUNT(*) FROM crudo.{table} GROUP BY ALL HAVING COUNT(*) > 1").fetchall()
    assert duplicates == []


@pytest.mark.parametrize(("table", "column", "target", "key"), REFERENCES)
def test_database_reference_exists(
    con: duckdb.DuckDBPyConnection, table: str, column: str, target: str, key: str
) -> None:
    orphans = con.execute(
        f"SELECT DISTINCT t.{column} FROM crudo.{table} t ANTI JOIN crudo.{target} d ON t.{column} = d.{key}"
    ).fetchall()
    assert orphans == []


def test_database_incident_on_flight_of_its_booking(con: duckdb.DuckDBPyConnection) -> None:
    loose = con.execute(
        "SELECT incidencia_id FROM crudo.incidencias i ANTI JOIN crudo.reservas_tramos rt USING (reserva_id, vuelo_id)"
    ).fetchall()
    assert loose == []


def test_database_every_booking_has_legs(con: duckdb.DuckDBPyConnection) -> None:
    without_legs = con.execute(
        "SELECT reserva_id FROM crudo.reservas ANTI JOIN crudo.reservas_tramos USING (reserva_id)"
    )
    assert without_legs.fetchall() == []


def test_database_payment_sign(con: duckdb.DuckDBPyConnection) -> None:
    wrong = con.execute(
        "SELECT pago_id FROM crudo.pagos "
        "WHERE (tipo = 'cargo' AND importe <= 0) OR (tipo = 'reembolso' AND importe >= 0)"
    ).fetchall()
    assert wrong == []


def test_database_charged_equals_total_amount(con: duckdb.DuckDBPyConnection) -> None:
    mismatches = con.execute(
        "SELECT r.reserva_id FROM crudo.reservas r JOIN v_reservas_cliente v USING (reserva_id) "
        "WHERE r.importe_total <> v.importe_cobrado"
    ).fetchall()
    assert mismatches == []


# == 3. Trampa del doble conteo ==
def test_database_join_trap_double_counts(con: duckdb.DuckDBPyConnection) -> None:
    """Unir reservas con tramos y pagos sin agregar antes repite cada pago una vez por tramo."""
    direct_join = con.execute(
        "SELECT SUM(p.importe) FROM crudo.reservas_tramos t JOIN crudo.pagos p USING (reserva_id)"
    ).fetchone()
    correct = con.execute("SELECT SUM(importe_neto) FROM v_reservas_cliente").fetchone()

    assert direct_join == (3543.0,)
    assert correct == (1849.0,)
