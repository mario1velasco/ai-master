"""TRAVEL-010: la vista `v_tramos`, una fila por vuelo de cada reserva (lo que más pregunta un cliente por chat)."""

import duckdb

from database.semantic_layer import open_db


def test_one_row_per_flight_of_each_booking(con: duckdb.DuckDBPyConnection) -> None:
    legs = con.execute("SELECT COUNT(*) FROM v_tramos").fetchone()
    flights_in_bookings = con.execute("SELECT SUM(tramos) FROM v_reservas_cliente").fetchone()

    assert legs == (12,)
    assert flights_in_bookings == (12,)
    data_con = open_db()  # data/, la base que abre la app
    try:
        assert data_con.execute("SELECT COUNT(*) FROM v_tramos").fetchone() == (3855,)
    finally:
        data_con.close()
