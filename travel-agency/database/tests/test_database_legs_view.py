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


def test_leg_has_class_seat_baggage_and_its_flight(con: duckdb.DuckDBPyConnection) -> None:
    leg = con.execute(
        "SELECT codigo_vuelo, aerolinea, origen, ciudad_origen, destino, ciudad_destino, clase, asiento, "
        "equipaje_facturado FROM v_tramos WHERE reserva_id = 'R-1042' AND trayecto = 'ida'"
    ).fetchall()

    assert leg == [("IB3166", "Iberia", "MAD", "Madrid", "JFK", "Nueva York", "turista", "23A", True)]


def test_leg_has_delay_and_status_of_its_flight(con: duckdb.DuckDBPyConnection) -> None:
    leg = con.execute(
        "SELECT retraso_salida_min, retraso_llegada_min, estado_vuelo FROM v_tramos "
        "WHERE reserva_id = 'R-1042' AND trayecto = 'ida'"
    ).fetchall()
    flight = con.execute(
        "SELECT retraso_salida_min, retraso_llegada_min, estado FROM v_vuelos_detalle WHERE codigo_vuelo = 'IB3166'"
    ).fetchall()

    assert leg == [(297, 312, "retrasado")]
    assert leg == flight
