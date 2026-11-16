"""TRAVEL-010: la vista `v_tramos`, una fila por vuelo de cada reserva (lo que más pregunta un cliente por chat)."""

import duckdb

from database.semantic_layer import COMMENTS, GUIDE, open_db


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


def test_leg_without_checked_bag_is_boolean_false(con: duckdb.DuckDBPyConnection) -> None:
    row = con.execute(
        "SELECT equipaje_facturado FROM v_tramos WHERE reserva_id = 'R-1043' AND trayecto = 'ida'"
    ).fetchone()

    assert row is not None
    assert row[0] is False  # booleano, no el 0 del CSV (el modelo no lo lee como «cero maletas»)


def test_each_flight_of_a_layover_has_its_airline(con: duckdb.DuckDBPyConnection) -> None:
    legs = con.execute(
        "SELECT trayecto, orden, codigo_vuelo, aerolinea FROM v_tramos WHERE reserva_id = 'R-1044' ORDER BY orden"
    ).fetchall()

    assert legs == [("ida", 1, "KL1701", "KLM"), ("ida", 2, "VY1002", "Vueling")]


def test_unassigned_seat_is_null_not_empty(con: duckdb.DuckDBPyConnection) -> None:
    leg = con.execute(
        "SELECT asiento, retraso_salida_min, retraso_llegada_min FROM v_tramos WHERE reserva_id = 'R-1047'"
    ).fetchall()

    assert leg == [(None, None, None)]  # IB0731 aún no ha volado: ni asiento ni retraso (NULL, no '' ni 0)


def test_cancelled_flight_leg_has_no_arrival_delay(con: duckdb.DuckDBPyConnection) -> None:
    leg = con.execute(
        "SELECT codigo_vuelo, estado_vuelo, retraso_llegada_min, clase FROM v_tramos "
        "WHERE reserva_id = 'R-1045' AND trayecto = 'ida'"
    ).fetchall()

    assert leg == [("AF1001", "cancelado", None, "business")]


def test_same_flight_in_two_bookings_keeps_each_booking_data(con: duckdb.DuckDBPyConnection) -> None:
    legs = con.execute(
        "SELECT reserva_id, clase, equipaje_facturado FROM v_tramos WHERE codigo_vuelo = 'AF1300' ORDER BY reserva_id"
    ).fetchall()

    assert legs == [("R-1045", "business", True), ("R-1048", "turista", False)]


def test_model_sees_the_view_with_its_comments_and_when_to_use_it(schema_text: str) -> None:
    description, columns = COMMENTS["v_tramos"]

    assert "Tabla v_tramos (" in schema_text
    assert description in schema_text
    for column in ("clase", "asiento", "equipaje_facturado", "retraso_salida_min", "retraso_llegada_min"):
        assert columns[column] in schema_text
    guide_line = next(line for line in GUIDE.splitlines() if "v_tramos" in line)
    for word in ("clase", "asiento", "maleta", "aerolínea"):
        assert word in guide_line
