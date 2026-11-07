"""El generador de datos sintéticos (fase 2b): amplía los CSV a mano sin tocarlos (ticket TRAVEL-001)."""

import csv
import shutil
from collections.abc import Generator
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import pytest
from test_database_audit import AUDIT_QUERIES

from database.seed import GENERATED_DIR, generate, main
from database.semantic_layer import CHECKS, DATA_DIR, Row, open_db, rounded_rows

TABLES = [
    "aerolineas",
    "aeropuertos",
    "clientes",
    "incidencias",
    "pagos",
    "reservas",
    "reservas_tramos",
    "vuelos",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_header(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


@pytest.fixture(scope="session")
def generated_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """El conjunto generado con la semilla por defecto, una sola vez para todos los tests."""
    out_dir = tmp_path_factory.mktemp("data_generated")
    generate(DATA_DIR, out_dir, seed=42)
    return out_dir


@pytest.fixture(scope="session")
def generated_con(generated_dir: Path) -> Generator[duckdb.DuckDBPyConnection]:
    """El conjunto generado abierto con la capa semántica, como `con` sobre `data/`."""
    connection = open_db(generated_dir)
    yield connection
    connection.close()


def test_database_seed_writes_large_dataset_with_same_columns(generated_dir: Path) -> None:
    for table in TABLES:
        assert read_header(generated_dir / f"{table}.csv") == read_header(DATA_DIR / f"{table}.csv"), table

    assert len(read_rows(generated_dir / "clientes.csv")) >= 1_000
    assert len(read_rows(generated_dir / "vuelos.csv")) >= 2_000
    assert len(read_rows(generated_dir / "reservas.csv")) >= 3_000


@pytest.mark.parametrize("table", TABLES)
def test_database_seed_keeps_hand_written_rows(generated_dir: Path, table: str) -> None:
    generated = read_rows(generated_dir / f"{table}.csv")

    missing = [row for row in read_rows(DATA_DIR / f"{table}.csv") if row not in generated]

    assert missing == []


@pytest.mark.parametrize(("name", "sql"), AUDIT_QUERIES, ids=[name for name, _ in AUDIT_QUERIES])
def test_database_seed_passes_integrity_audit(generated_con: duckdb.DuckDBPyConnection, name: str, sql: str) -> None:
    assert generated_con.execute(sql).fetchall()[:5] == []


def test_database_seed_flight_codes_are_unique(generated_con: duckdb.DuckDBPyConnection) -> None:
    repeated = generated_con.execute(
        "SELECT codigo_vuelo, COUNT(*) FROM crudo.vuelos GROUP BY 1 HAVING COUNT(*) > 1 ORDER BY 1"
    ).fetchall()

    assert repeated[:5] == []


def test_database_seed_offsets_match_airport_time_zone(generated_dir: Path) -> None:
    zones = {r["aeropuerto_id"]: ZoneInfo(r["zona_horaria"]) for r in read_rows(generated_dir / "aeropuertos.csv")}
    wrong = []
    for flight in read_rows(generated_dir / "vuelos.csv"):
        for column, airport in [
            ("salida_prevista", "origen"),
            ("salida_real", "origen"),
            ("llegada_prevista", "destino"),
            ("llegada_real", "destino"),
        ]:
            if not flight[column]:
                continue
            moment = datetime.fromisoformat(flight[column])
            # El desfase escrito tiene que ser el de la zona en ese instante
            # (Madrid: +02:00 en julio, +01:00 en diciembre)
            if moment.utcoffset() != zones[flight[airport]].utcoffset(moment):
                wrong.append((flight["vuelo_id"], column, flight[column]))
        if datetime.fromisoformat(flight["llegada_prevista"]) <= datetime.fromisoformat(flight["salida_prevista"]):
            wrong.append((flight["vuelo_id"], "llega antes de salir", flight["llegada_prevista"]))

    assert wrong[:5] == []


CUTOFF = date(2026, 11, 1)


def test_database_seed_flights_after_cutoff_are_scheduled(generated_dir: Path) -> None:
    wrong = []
    for flight in read_rows(generated_dir / "vuelos.csv"):
        departs_after_cutoff = datetime.fromisoformat(flight["salida_prevista"]).date() >= CUTOFF
        if departs_after_cutoff and (
            flight["estado"] != "programado" or flight["salida_real"] or flight["llegada_real"]
        ):
            wrong.append((flight["vuelo_id"], "futuro", flight["estado"]))
        if not departs_after_cutoff and flight["estado"] == "programado":
            wrong.append((flight["vuelo_id"], "pasado", flight["salida_prevista"]))

    assert wrong[:5] == []


def arrival_delay_min(flight: dict[str, str]) -> float:
    return (
        datetime.fromisoformat(flight["llegada_real"]) - datetime.fromisoformat(flight["llegada_prevista"])
    ).total_seconds() / 60


def test_database_seed_flight_state_matches_its_times(generated_dir: Path) -> None:
    wrong = []
    for flight in read_rows(generated_dir / "vuelos.csv"):
        match flight["estado"]:
            case "cancelado":
                ok = not flight["salida_real"] and not flight["llegada_real"]
            case "en_hora":
                ok = arrival_delay_min(flight) <= 15
            case "retrasado":
                ok = arrival_delay_min(flight) > 15
            case _:
                ok = flight["estado"] == "programado"
        if not ok:
            wrong.append((flight["vuelo_id"], flight["estado"], flight["llegada_prevista"], flight["llegada_real"]))

    assert wrong[:5] == []


def test_database_seed_itineraries_chain(generated_dir: Path) -> None:
    flights = {f["vuelo_id"]: f for f in read_rows(generated_dir / "vuelos.csv")}
    trips: dict[tuple[str, str], list[dict[str, str]]] = {}
    for leg in sorted(read_rows(generated_dir / "reservas_tramos.csv"), key=lambda r: int(r["orden"])):
        trips.setdefault((leg["reserva_id"], leg["trayecto"]), []).append(flights[leg["vuelo_id"]])

    wrong = []
    for (booking, direction), legs in trips.items():
        # Cada tramo sale de donde llegó el anterior, y después de que llegue
        for previous, current in zip(legs, legs[1:], strict=False):
            if current["origen"] != previous["destino"] or (
                datetime.fromisoformat(current["salida_prevista"])
                <= datetime.fromisoformat(previous["llegada_prevista"])
            ):
                wrong.append((booking, direction, previous["vuelo_id"], current["vuelo_id"]))
        # La vuelta sale del destino final de la ida, después de que la ida llegue
        outbound = trips.get((booking, "ida"))
        if direction == "vuelta" and outbound:
            if legs[0]["origen"] != outbound[-1]["destino"] or (
                datetime.fromisoformat(legs[0]["salida_prevista"])
                <= datetime.fromisoformat(outbound[-1]["llegada_prevista"])
            ):
                wrong.append((booking, "ida → vuelta", outbound[-1]["vuelo_id"], legs[0]["vuelo_id"]))

    assert wrong[:5] == []


def test_database_seed_dates_are_in_order(generated_dir: Path) -> None:
    signed_up = {
        c["cliente_id"]: date.fromisoformat(c["fecha_alta"]) for c in read_rows(generated_dir / "clientes.csv")
    }
    departures = {
        f["vuelo_id"]: datetime.fromisoformat(f["salida_prevista"]).date()
        for f in read_rows(generated_dir / "vuelos.csv")
    }
    first_leg = {}
    for leg in sorted(read_rows(generated_dir / "reservas_tramos.csv"), key=lambda r: -int(r["orden"])):
        first_leg[leg["reserva_id"]] = leg["vuelo_id"]  # el de menor orden se escribe el último
    booked = {}
    wrong = []
    for booking in read_rows(generated_dir / "reservas.csv"):
        booked[booking["reserva_id"]] = day = date.fromisoformat(booking["fecha_reserva"])
        # fecha_alta ≤ fecha_reserva ≤ salida prevista del primer tramo
        if not signed_up[booking["cliente_id"]] <= day <= departures[first_leg[booking["reserva_id"]]]:
            wrong.append((booking["reserva_id"], "reserva", booking["fecha_reserva"]))
    for payment in read_rows(generated_dir / "pagos.csv"):
        if date.fromisoformat(payment["fecha"]) < booked[payment["reserva_id"]]:
            wrong.append((payment["pago_id"], "pago", payment["fecha"]))

    assert wrong[:5] == []


def test_database_seed_no_booking_after_cutoff(generated_dir: Path) -> None:
    late = [
        (b["reserva_id"], b["fecha_reserva"])
        for b in read_rows(generated_dir / "reservas.csv")
        if date.fromisoformat(b["fecha_reserva"]) >= CUTOFF
    ]

    assert late[:5] == []


def test_database_seed_booking_state_matches_its_flights(generated_dir: Path) -> None:
    departures = {
        f["vuelo_id"]: datetime.fromisoformat(f["salida_prevista"]).date()
        for f in read_rows(generated_dir / "vuelos.csv")
    }
    last_leg = {}
    for leg in sorted(read_rows(generated_dir / "reservas_tramos.csv"), key=lambda r: int(r["orden"])):
        last_leg[leg["reserva_id"]] = leg["vuelo_id"]  # el de mayor orden se escribe el último
    wrong = []
    for booking in read_rows(generated_dir / "reservas.csv"):
        finished = departures[last_leg[booking["reserva_id"]]] < CUTOFF
        allowed = {"completada", "cancelada"} if finished else {"confirmada", "cancelada"}
        if booking["estado"] not in allowed:
            wrong.append((booking["reserva_id"], booking["estado"], "terminado" if finished else "por volar"))

    assert wrong[:5] == []


def test_database_seed_payments_match_booking_state(generated_con: duckdb.DuckDBPyConnection) -> None:
    cancelled_without_refund = generated_con.execute(
        "SELECT reserva_id FROM crudo.reservas r WHERE estado = 'cancelada' AND NOT EXISTS "
        "(SELECT 1 FROM crudo.pagos p WHERE p.reserva_id = r.reserva_id AND p.tipo = 'reembolso') ORDER BY 1"
    ).fetchall()
    negative_net = generated_con.execute(
        "SELECT reserva_id, importe_neto FROM v_reservas_cliente WHERE importe_neto < 0 ORDER BY 1"
    ).fetchall()

    assert cancelled_without_refund[:5] == []
    assert negative_net[:5] == []


# Incidencias con el viaje y el tramo de compensación del Reglamento 261/2004, escrito a mano (simplificado: ticket)
INCIDENTS_261 = """
    SELECT i.incidencia_id, i.tipo, i.estado, i.compensacion, i.retraso_llegada_destino_min AS retraso,
           CASE WHEN i.distancia_itinerario_km <= 1500 THEN 250
                WHEN (ao.es_ue AND ad.es_ue) OR i.distancia_itinerario_km <= 3500 THEN 400
                ELSE 600 END AS tramo
    FROM v_incidencias i
    JOIN crudo.aeropuertos ao ON ao.aeropuerto_id = i.origen
    JOIN crudo.aeropuertos ad ON ad.aeropuerto_id = i.destino_final
"""


def test_database_seed_compensation_follows_regulation_261(generated_con: duckdb.DuckDBPyConnection) -> None:
    rows = generated_con.execute(INCIDENTS_261).fetchall()
    wrong = []
    for incident_id, kind, state, amount, delay, band in rows:
        entitled = kind == "cancelacion" or (kind == "retraso" and delay >= 180)
        if entitled and state == "resuelta" and amount != band:
            wrong.append((incident_id, "importe", amount, band))
        if kind == "retraso" and delay < 180 and (state != "rechazada" or amount is not None):
            wrong.append((incident_id, "menos de 180 min", state, amount))
        if (kind == "equipaje" or state == "abierta") and amount is not None:
            wrong.append((incident_id, "sin importe", kind, state, amount))

    assert wrong[:5] == []
    # Que haya de todo entre las generadas: sin incidencias, las reglas de arriba no prueban nada
    hand_written = {r["incidencia_id"] for r in read_rows(DATA_DIR / "incidencias.csv")}
    generated = [r for r in rows if r[0] not in hand_written]
    paid = {amount for _, _, state, amount, _, _ in generated if state == "resuelta" and amount is not None}
    assert paid == {250, 400, 600}
    assert {(kind, state) for _, kind, state, *_ in generated} >= {
        ("retraso", "resuelta"),
        ("retraso", "rechazada"),
        ("retraso", "abierta"),
        ("cancelacion", "resuelta"),
        ("equipaje", "abierta"),
    }


def test_database_seed_booking_on_cancelled_flight_is_cancelled(generated_con: duckdb.DuckDBPyConnection) -> None:
    not_cancelled = generated_con.execute(
        "SELECT DISTINCT r.reserva_id, r.estado FROM crudo.reservas r "
        "JOIN crudo.reservas_tramos rt USING (reserva_id) JOIN crudo.vuelos v USING (vuelo_id) "
        "WHERE v.estado = 'cancelado' AND r.estado <> 'cancelada' ORDER BY 1"
    ).fetchall()

    assert not_cancelled[:5] == []


# Cada trampa de PROYECTO.md §3, buscada solo en las filas generadas: (tabla de data/ cuyos ids se excluyen, consulta)
TRAPS = {
    "dos clientes con el mismo nombre y apellidos": (
        "clientes",
        "SELECT nombre, apellidos FROM crudo.clientes WHERE NOT list_contains(?, cliente_id) "
        "GROUP BY ALL HAVING COUNT(*) > 1",
    ),
    "cliente sin reservas": (
        "clientes",
        "SELECT cliente_id FROM crudo.clientes WHERE NOT list_contains(?, cliente_id) "
        "AND cliente_id NOT IN (SELECT cliente_id FROM crudo.reservas)",
    ),
    "reserva con escala": (
        "reservas",
        "SELECT reserva_id FROM crudo.reservas_tramos WHERE NOT list_contains(?, reserva_id) "
        "GROUP BY reserva_id, trayecto HAVING COUNT(*) > 1",
    ),
    "ida y vuelta": (
        "reservas",
        "SELECT reserva_id FROM crudo.reservas_tramos WHERE NOT list_contains(?, reserva_id) AND trayecto = 'vuelta'",
    ),
    "reembolso parcial": (
        "reservas",
        "SELECT reserva_id FROM v_reservas_cliente WHERE NOT list_contains(?, reserva_id) "
        "AND importe_reembolsado > 0 AND importe_neto > 0",
    ),
    "cancelación con reembolso total": (
        "reservas",
        "SELECT reserva_id FROM v_reservas_cliente WHERE NOT list_contains(?, reserva_id) "
        "AND estado = 'cancelada' AND importe_reembolsado > 0 AND importe_neto = 0",
    ),
    "vuelo que llega pasada la medianoche por el retraso": (
        "vuelos",
        "SELECT vuelo_id FROM v_vuelos_detalle WHERE NOT list_contains(?, vuelo_id) "
        "AND CAST(llegada_real_local AS DATE) > CAST(llegada_prevista_local AS DATE)",
    ),
    "vuelo programado": (
        "vuelos",
        "SELECT vuelo_id FROM crudo.vuelos WHERE NOT list_contains(?, vuelo_id) AND estado = 'programado'",
    ),
    "vuelo cancelado": (
        "vuelos",
        "SELECT vuelo_id FROM crudo.vuelos WHERE NOT list_contains(?, vuelo_id) AND estado = 'cancelado'",
    ),
}
ID_COLUMN = {"clientes": "cliente_id", "reservas": "reserva_id", "vuelos": "vuelo_id"}


def test_database_seed_traps_are_in_generated_rows(generated_con: duckdb.DuckDBPyConnection) -> None:
    missing = []
    for trap, (table, sql) in TRAPS.items():
        hand_ids = [r[ID_COLUMN[table]] for r in read_rows(DATA_DIR / f"{table}.csv")]
        if not generated_con.execute(sql, [hand_ids]).fetchall():
            missing.append(trap)

    assert missing == []


# Los CHECKS globales (total de reservas, facturación, «Ana López%») cambian al añadir filas: los demás miran un id
GLOBAL_CHECKS = {
    "Reservas y vuelos reservados (una reserva NO es un vuelo)",
    "Facturación: cobrado, reembolsado y neto",
    "Dos clientes llamados Ana López, distintos por cliente_id",
}
ID_CHECKS = [check for check in CHECKS if check[0] not in GLOBAL_CHECKS]


@pytest.mark.parametrize(("name", "sql", "expected"), ID_CHECKS, ids=[c[0] for c in ID_CHECKS])
def test_database_seed_id_checks_keep_their_figures(
    generated_con: duckdb.DuckDBPyConnection, name: str, sql: str, expected: list[Row]
) -> None:
    assert rounded_rows(generated_con, sql) == expected


def test_database_seed_other_seed_gives_other_data(generated_dir: Path, tmp_path: Path) -> None:
    generate(DATA_DIR, tmp_path, seed=7)

    for table in TABLES:
        hand = read_rows(DATA_DIR / f"{table}.csv")
        with_42, with_7 = read_rows(generated_dir / f"{table}.csv"), read_rows(tmp_path / f"{table}.csv")
        # Las filas a mano, las mismas y al principio con las dos semillas
        assert with_42[: len(hand)] == with_7[: len(hand)] == hand, table
        if table not in ("aerolineas", "aeropuertos"):  # estas dos no tienen filas generadas
            assert with_42[len(hand) :] != with_7[len(hand) :], table


def snapshot(folder: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(folder.glob("*.csv"))}


def test_database_seed_rejects_non_integer_seed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    generate(DATA_DIR, tmp_path, seed=42)
    before = snapshot(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        main(["--seed", "abc", "--out", str(tmp_path)])

    assert exit_info.value.code == 2  # error de uso de argparse
    assert "la semilla debe ser un número entero" in capsys.readouterr().err
    assert snapshot(tmp_path) == before


def test_database_seed_missing_csv_is_named(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source, out = tmp_path / "source", tmp_path / "out"
    shutil.copytree(DATA_DIR, source)
    (source / "vuelos.csv").unlink()

    with pytest.raises(SystemExit) as exit_info:
        main(["--source", str(source), "--out", str(out)])

    assert exit_info.value.code != 0
    assert "vuelos.csv" in capsys.readouterr().err
    assert list(out.glob("*.csv")) == []  # nada a medias


def test_database_seed_same_seed_same_bytes(tmp_path: Path) -> None:
    generate(DATA_DIR, tmp_path / "first", seed=42)
    generate(DATA_DIR, tmp_path / "second", seed=42)
    first, second, committed = (snapshot(tmp_path / "first"), snapshot(tmp_path / "second"), snapshot(GENERATED_DIR))

    assert sorted(first) == sorted(committed) == [f"{table}.csv" for table in TABLES]
    assert [name for name in first if first[name] != second[name]] == []
    # Si falla tras cambiar el generador: regenerar con «uv run python -m database.seed» y subirlo
    assert [name for name in first if first[name] != committed[name]] == []


# Las 8 filas de aeropuertos.csv de la fase 2a, literales: los CHECKS de distancia salen de ellas
ORIGINAL_AIRPORTS = """\
aeropuerto_id,nombre,ciudad,pais,latitud,longitud,es_ue,zona_horaria
MAD,Adolfo Suárez Madrid-Barajas,Madrid,España,40.4719,-3.5626,true,Europe/Madrid
BCN,Josep Tarradellas Barcelona-El Prat,Barcelona,España,41.2971,2.0785,true,Europe/Madrid
TFN,Tenerife Norte-Ciudad de La Laguna,San Cristóbal de La Laguna,España,28.4827,-16.3415,true,Atlantic/Canary
CDG,París-Charles de Gaulle,París,Francia,49.0097,2.5479,true,Europe/Paris
AMS,Ámsterdam-Schiphol,Ámsterdam,Países Bajos,52.3105,4.7683,true,Europe/Amsterdam
FCO,Roma-Fiumicino,Roma,Italia,41.8003,12.2389,true,Europe/Rome
LHR,Londres-Heathrow,Londres,Reino Unido,51.4700,-0.4543,false,Europe/London
JFK,John F. Kennedy,Nueva York,Estados Unidos,40.6413,-73.7781,false,America/New_York
"""


def test_database_seed_original_airports_untouched() -> None:
    text = (DATA_DIR / "aeropuertos.csv").read_text(encoding="utf-8")

    assert text.startswith(ORIGINAL_AIRPORTS)
    assert len(read_rows(DATA_DIR / "aeropuertos.csv")) > 8  # las nuevas, al final
