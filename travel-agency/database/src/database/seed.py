"""Generador de datos sintéticos con semilla fija (fase 2b, ticket TRAVEL-001).

Lee los 8 CSV escritos a mano (`fixtures/`), los copia tal cual y añade filas generadas en `data/`, la fuente de
verdad que abre la app. Se ejecuta una vez y se sube a git; solo se regenera si cambian `fixtures/` o el generador.
Sin referencia en el repo: en clase los datos ya venían hechos. Sin Faker (decisión de Mario): listas escritas a mano
y `random` con semilla.
"""

import argparse
import csv
import math
import random
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from database.semantic_layer import DATA_DIR

# Las filas escritas a mano (casos ancla con las trampas): el origen del generador y los datos de los tests.
# La app no las usa: abre data/, que las lleva dentro junto con las generadas.
FIXTURES_DIR = DATA_DIR.parent / "fixtures"

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

N_CUSTOMERS = 1_000
N_FLIGHTS = 2_000
N_BOOKINGS = 3_000
BOOKING_ID_START = 2000  # R-2000…: lejos de las filas a mano (R-1042 a R-1048)

# Vuelos entre estas fechas (supuesto del ticket), con salida de 06:00 a 22:55:
# así no hay horas que no existen al cambiar la hora
FIRST_DAY = date(2025, 1, 1)
LAST_DAY = date(2027, 3, 31)
CUTOFF = date(2026, 11, 1)  # «hoy» del conjunto: lo que sale desde ese día está programado
CRUISE_KMH = 800
TAXI_MIN = 30

# Vuelos ya volados: el resto llega en hora (hasta 15 min tarde)
FLIGHT_CANCELLED_SHARE = 0.05
FLIGHT_DELAYED_SHARE = 0.20

# Incidencias (Reglamento 261/2004 simplificado: ver supuestos del ticket)
CLAIM_SHARE = 0.60  # parte de las reservas en un vuelo retrasado o cancelado que reclaman
BAGGAGE_SHARE = 0.02  # parte de las reservas en un vuelo que salió con incidencia de equipaje
RESOLVED_SHARE = 0.80  # las que tienen derecho a compensación: el resto sigue abierta
MIN_DELAY_261 = 180

# Listas escritas a mano (sin Faker): nombres y apellidos frecuentes en España
FIRST_NAMES = [
    "Ana", "María", "Lucía", "Carmen", "Laura", "Marta", "Elena", "Paula", "Sara", "Clara",
    "Javier", "Marc", "Pedro", "David", "Carlos", "Pablo", "Sergio", "Jorge", "Hugo", "Álvaro",
]  # fmt: skip
SURNAMES = [
    "López", "García", "Martín", "Ruiz", "Fernández", "Soto", "Pérez", "Puig", "Serra", "Gómez",
    "Vidal", "Sánchez", "Romero", "Navarro", "Torres", "Díaz", "Moreno", "Muñoz", "Alonso", "Gil",
]  # fmt: skip
COUNTRIES = ["España", "España", "España", "Francia", "Portugal", "Italia", "Alemania"]
LOYALTY_LEVELS = ["basico", "basico", "basico", "plata", "plata", "oro"]
CANCELLED_SHARE = 0.10  # parte de las reservas que se cancelan
PARTIAL_REFUND_SHARE = 0.05  # parte de las no canceladas con un reembolso parcial (del 10 al 50 %)
STOPOVER_SHARE = 0.10  # reservas de ida con escala; otro RETURN_SHARE de ida y vuelta, el resto solo ida
RETURN_SHARE = 0.20
BOOKING_TYPES = ["solo_vuelo", "paquete"]
CABIN_CLASSES = ["turista", "turista", "turista", "business"]
PAYMENT_METHODS = ["tarjeta", "tarjeta", "bizum", "paypal", "transferencia"]

type Row = dict[str, str]


def _read(path: Path) -> tuple[list[str], list[Row]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, header: list[str], rows: list[Row]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _ascii(text: str) -> str:
    """«López» → «lopez», para los emails."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def _customers(rng: random.Random, start: int) -> list[Row]:
    rows = []
    for n in range(start, start + N_CUSTOMERS):
        first, last1, last2 = rng.choice(FIRST_NAMES), rng.choice(SURNAMES), rng.choice(SURNAMES)
        rows.append(
            {
                "cliente_id": f"C-{n:04d}",
                "nombre": first,
                "apellidos": f"{last1} {last2}",
                "email": f"{_ascii(first)}.{_ascii(last1)}.{n}@example.com",
                "pais": rng.choice(COUNTRIES),
                "fecha_alta": f"{rng.randint(2020, 2025)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
                "nivel_fidelidad": rng.choice(LOYALTY_LEVELS),
            }
        )
    return rows


def _flight_code(rng: random.Random, airline: str, used: set[str]) -> str:
    """Un código de vuelo que no se ha usado todavía (ni en las filas a mano ni en las generadas)."""
    while (code := f"{airline}{rng.randint(1000, 9999)}") in used:
        pass
    used.add(code)
    return code


def _distance_km(a: Row, b: Row) -> float:
    """Distancia ortodrómica (haversine), la misma fórmula que `VIEWS` en semantic_layer.py."""
    lat1, lon1, lat2, lon2 = (float(a["latitud"]), float(a["longitud"]), float(b["latitud"]), float(b["longitud"]))
    h = (
        math.sin(math.radians(lat2 - lat1) / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return round(2 * 6371 * math.asin(math.sqrt(h)), 0)


def _duration(origin: Row, destination: Row) -> timedelta:
    """Tiempo de vuelo aproximado: distancia a velocidad de crucero + rodaje, en múltiplos de 5 min."""
    minutes = _distance_km(origin, destination) / CRUISE_KMH * 60 + TAXI_MIN
    return timedelta(minutes=round(minutes / 5) * 5)


def _before_cutoff(day: date) -> date:
    """`day`, o el último día antes del corte si cae en él o después: nada se registra «en el futuro»."""
    return min(day, CUTOFF - timedelta(days=1))


def _local_day(row: Row, column: str) -> date:
    """La fecha local de una hora del CSV («2026-07-01T10:05:00+02:00» → 2026-07-01)."""
    return datetime.fromisoformat(row[column]).date()


def _iso(moment: datetime, airport: Row) -> str:
    """El instante en la hora local del aeropuerto, con su desfase: «2026-07-01T10:05:00+02:00»."""
    return moment.astimezone(ZoneInfo(airport["zona_horaria"])).isoformat(timespec="seconds")


@dataclass(slots=True)
class _Fleet:
    """Crea vuelos con id y código únicos y los va guardando: los de base y los que piden las reservas."""

    rng: random.Random
    airlines: list[str]
    used_codes: set[str]  # empieza con los de las filas a mano: IB3166, VY1234…
    next_id: int
    flights: list[Row] = field(default_factory=list)

    def add(self, origin: Row, destination: Row, departure: datetime) -> Row:
        """Un vuelo que sale en el instante `departure`; su estado depende de si ya ha volado (fecha de corte)."""
        rng = self.rng
        airline = rng.choice(self.airlines)
        arrival = departure + _duration(origin, destination)  # en UTC: un cambio de hora no altera la duración
        actual_departure = actual_arrival = ""
        roll = rng.random()
        if departure.astimezone(ZoneInfo(origin["zona_horaria"])).date() >= CUTOFF:  # por volar: sin horas reales
            state = "programado"
        elif roll < FLIGHT_CANCELLED_SHARE:
            state = "cancelado"
        else:
            # Retraso a la llegada (lo que mide el Reglamento 261); la salida se mueve parecido
            delayed = roll < FLIGHT_CANCELLED_SHARE + FLIGHT_DELAYED_SHARE
            delay = rng.randint(16, 400) if delayed else rng.randint(-10, 15)
            actual_departure = _iso(departure + timedelta(minutes=delay + rng.randint(-10, 20)), origin)
            actual_arrival = _iso(arrival + timedelta(minutes=delay), destination)
            state = "retrasado" if delayed else "en_hora"
        flight = {
            "vuelo_id": f"V-{self.next_id:04d}",
            "codigo_vuelo": _flight_code(rng, airline, self.used_codes),
            "aerolinea_id": airline,
            "origen": origin["aeropuerto_id"],
            "destino": destination["aeropuerto_id"],
            "salida_prevista": _iso(departure, origin),
            "llegada_prevista": _iso(arrival, destination),
            "salida_real": actual_departure,
            "llegada_real": actual_arrival,
            "estado": state,
        }
        self.next_id += 1
        self.flights.append(flight)
        return flight


def _random_departure(rng: random.Random, origin: Row) -> datetime:
    """Un día al azar entre FIRST_DAY y LAST_DAY, de 06:00 a 22:55 en la hora local del origen (en UTC)."""
    day = FIRST_DAY + timedelta(days=rng.randint(0, (LAST_DAY - FIRST_DAY).days))
    local = datetime(
        day.year, day.month, day.day, rng.randint(6, 22), rng.randrange(0, 60, 5),
        tzinfo=ZoneInfo(origin["zona_horaria"]),
    )  # fmt: skip
    return local.astimezone(UTC)


def _base_flights(rng: random.Random, fleet: _Fleet, airports: list[Row]) -> list[Row]:
    for _ in range(N_FLIGHTS):
        origin, destination = rng.sample(airports, 2)
        fleet.add(origin, destination, _random_departure(rng, origin))
    return list(fleet.flights)


type Itinerary = list[tuple[str, Row]]  # (trayecto, vuelo) por orden


def _itinerary(rng: random.Random, first: Row, fleet: _Fleet, airports: dict[str, Row]) -> Itinerary:
    """Solo ida, ida con escala (otro vuelo desde la escala) o ida y vuelta (vuelo de regreso días después)."""
    legs = [("ida", first)]
    landed = datetime.fromisoformat(first["llegada_prevista"])
    roll = rng.random()
    if roll < STOPOVER_SHARE:
        hub = airports[first["destino"]]
        final = rng.choice(
            [a for a in airports.values() if a["aeropuerto_id"] not in (first["origen"], first["destino"])]
        )
        departure = landed + timedelta(minutes=rng.randint(60, 240))
        legs.append(("ida", fleet.add(hub, final, departure.astimezone(UTC))))
    elif roll < STOPOVER_SHARE + RETURN_SHARE:
        departure = landed + timedelta(days=rng.randint(2, 14))
        if departure.date() <= LAST_DAY:  # sin vuelos fuera del periodo del conjunto
            back = fleet.add(airports[first["destino"]], airports[first["origen"]], departure.astimezone(UTC))
            legs.append(("vuelta", back))
    return legs


def _bookings(
    rng: random.Random, customers: list[Row], flights: list[Row], fleet: _Fleet, airports: dict[str, Row]
) -> list[tuple[Row, Itinerary]]:
    """Cada reserva con su itinerario: se reserva de 1 a 120 días antes de salir, por un cliente ya dado de alta."""
    trips = []
    for n in range(BOOKING_ID_START, BOOKING_ID_START + N_BOOKINGS):
        first = rng.choice(flights)
        legs = _itinerary(rng, first, fleet, airports)
        booked = _local_day(first, "salida_prevista") - timedelta(days=rng.randint(1, 120))
        if booked >= CUTOFF:  # nadie reserva «en el futuro»; el vuelo sale después del corte: sigue siendo antes
            booked = CUTOFF - timedelta(days=rng.randint(1, 60))
        customer = rng.choice(customers)
        while date.fromisoformat(customer["fecha_alta"]) > booked:
            customer = rng.choice(customers)
        # Cancelada (siempre si se canceló algún vuelo) o, si no, completada cuando el último tramo ya ha salido y
        # confirmada cuando está por volar
        if rng.random() < CANCELLED_SHARE or any(flight["estado"] == "cancelado" for _, flight in legs):
            state = "cancelada"
        else:
            state = "completada" if _local_day(legs[-1][1], "salida_prevista") < CUTOFF else "confirmada"
        booking = {
            "reserva_id": f"R-{n}",
            "cliente_id": customer["cliente_id"],
            "fecha_reserva": booked.isoformat(),
            "estado": state,
            "tipo": rng.choice(BOOKING_TYPES),
            "importe_total": f"{rng.randint(40, 900)}.00",
            "moneda": "EUR",
        }
        trips.append((booking, legs))
    return trips


def _legs(rng: random.Random, trips: list[tuple[Row, Itinerary]]) -> list[Row]:
    """Los tramos de cada reserva, numerados por orden (la vuelta sigue a la ida, como en R-1042)."""
    return [
        {
            "reserva_id": booking["reserva_id"],
            "orden": str(order),
            "trayecto": direction,
            "vuelo_id": flight["vuelo_id"],
            "clase": rng.choice(CABIN_CLASSES),
            "asiento": f"{rng.randint(1, 32)}{rng.choice('ABCDEF')}",
            "equipaje_facturado": str(rng.randint(0, 1)),
        }
        for booking, legs in trips
        for order, (direction, flight) in enumerate(legs, 1)
    ]


def _payments(rng: random.Random, bookings: list[Row], start: int) -> list[Row]:
    """Un cargo por reserva, por su importe total; si se canceló, además un reembolso total (importe negativo)."""
    rows = []
    for booking in bookings:
        method = rng.choice(PAYMENT_METHODS)
        booked = date.fromisoformat(booking["fecha_reserva"])
        payments = [(booked, booking["importe_total"], "cargo")]
        if booking["estado"] == "cancelada":
            refunded = _before_cutoff(booked + timedelta(days=rng.randint(0, 30)))
            payments.append((refunded, f"-{booking['importe_total']}", "reembolso"))
        elif rng.random() < PARTIAL_REFUND_SHARE:  # p. ej. un servicio del paquete que no se prestó (como R-1042)
            refunded = _before_cutoff(booked + timedelta(days=rng.randint(1, 60)))
            amount = round(float(booking["importe_total"]) * rng.uniform(0.10, 0.50))
            payments.append((refunded, f"-{amount}.00", "reembolso"))
        for day, amount, kind in payments:
            rows.append(
                {
                    "pago_id": f"P-{start + len(rows):04d}",
                    "reserva_id": booking["reserva_id"],
                    "fecha": day.isoformat(),
                    "importe": amount,
                    "tipo": kind,
                    "metodo": method,
                }
            )
    return rows


def _compensation(distance_km: float, within_eu: bool) -> int:
    """Cuantía del Reglamento 261/2004 (art. 7) según la distancia del viaje."""
    if distance_km <= 1500:
        return 250
    if within_eu or distance_km <= 3500:
        return 400
    return 600


def _arrival_delay_min(flight: Row) -> int:
    late = datetime.fromisoformat(flight["llegada_real"]) - datetime.fromisoformat(flight["llegada_prevista"])
    return late // timedelta(minutes=1)


def _incidents(
    rng: random.Random, trips: list[tuple[Row, Itinerary]], airports: dict[str, Row], start: int
) -> list[Row]:
    """Reclamaciones por trayecto: vuelo cancelado, llegada con retraso al destino final, o equipaje."""
    rows = []
    for booking, legs in trips:
        for direction in ("ida", "vuelta"):
            trip = [flight for d, flight in legs if d == direction]
            if not trip:
                continue
            cancelled = next((flight for flight in trip if flight["estado"] == "cancelado"), None)
            last = trip[-1]  # el Reglamento mide el retraso en el destino final
            if cancelled and rng.random() < CLAIM_SHARE:
                kind, flight = "cancelacion", cancelled
            elif not cancelled and last["estado"] == "retrasado" and rng.random() < CLAIM_SHARE:
                kind, flight = "retraso", last
            elif not cancelled and last["estado"] in ("en_hora", "retrasado") and rng.random() < BAGGAGE_SHARE:
                kind, flight = "equipaje", last
            else:
                continue
            amount = ""
            if kind == "equipaje":
                state = rng.choice(["abierta", "resuelta"])
            elif kind == "retraso" and _arrival_delay_min(last) < MIN_DELAY_261:
                state = "rechazada"
            elif rng.random() < RESOLVED_SHARE:
                # Distancia del viaje: origen del primer tramo → destino final, no la suma de tramos
                origin, destination = airports[trip[0]["origen"]], airports[last["destino"]]
                within_eu = origin["es_ue"] == destination["es_ue"] == "true"
                amount = f"{_compensation(_distance_km(origin, destination), within_eu)}.00"
                state = "resuelta"
            else:
                state = "abierta"
            arrived = _local_day(flight, "llegada_prevista")
            rows.append(
                {
                    "incidencia_id": f"I-{start + len(rows):04d}",
                    "reserva_id": booking["reserva_id"],
                    "vuelo_id": flight["vuelo_id"],
                    "tipo": kind,
                    "fecha": _before_cutoff(arrived + timedelta(days=rng.randint(0, 10))).isoformat(),
                    "estado": state,
                    "compensacion": amount,
                }
            )
    return rows


def generate(source_dir: Path, out_dir: Path, seed: int = 42) -> dict[str, int]:
    """Escribe en `out_dir` los 8 CSV: las filas a mano de `source_dir` + las generadas. Devuelve filas por tabla."""
    rng = random.Random(seed)
    data = {table: _read(source_dir / f"{table}.csv") for table in TABLES}
    rows = {table: list(table_rows) for table, (_, table_rows) in data.items()}

    customers = _customers(rng, start=len(rows["clientes"]) + 1)
    rows["clientes"] += customers
    airlines = [r["aerolinea_id"] for r in rows["aerolineas"]]
    airports = rows["aeropuertos"]
    airports_by_id = {r["aeropuerto_id"]: r for r in airports}
    used_codes = {r["codigo_vuelo"] for r in rows["vuelos"]}  # IB3166, VY1234…: no se repiten
    fleet = _Fleet(rng, airlines, used_codes, next_id=len(rows["vuelos"]) + 1)
    flights = _base_flights(rng, fleet, airports)
    trips = _bookings(rng, customers, flights, fleet, airports_by_id)
    rows["vuelos"] += fleet.flights  # los de base y los de escala o vuelta que crearon las reservas
    bookings = [booking for booking, _ in trips]
    rows["reservas"] += bookings
    rows["reservas_tramos"] += _legs(rng, trips)
    rows["pagos"] += _payments(rng, bookings, start=len(rows["pagos"]) + 1)
    rows["incidencias"] += _incidents(rng, trips, airports_by_id, start=len(rows["incidencias"]) + 1)

    out_dir.mkdir(parents=True, exist_ok=True)
    for table, (header, _) in data.items():
        _write(out_dir / f"{table}.csv", header, rows[table])
    return {table: len(table_rows) for table, table_rows in rows.items()}


def _seed(text: str) -> int:
    """La semilla de `--seed`: un número entero, o un error de uso que lo explica."""
    try:
        return int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"la semilla debe ser un número entero (recibido: {text!r})") from None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Amplía los CSV a mano con filas generadas, con semilla fija.")
    parser.add_argument("--seed", type=_seed, default=42, help="Semilla de random (por defecto 42).")
    parser.add_argument("--source", type=Path, default=FIXTURES_DIR, help="Carpeta con los 8 CSV a mano.")
    parser.add_argument(
        "--out", type=Path, default=DATA_DIR, help="Carpeta donde se escriben los CSV (se sobrescriben)."
    )
    args = parser.parse_args(argv)
    try:
        # Lee los 8 CSV antes de escribir: si falta uno, no deja nada a medias
        generate(args.source, args.out, args.seed)
    except FileNotFoundError as exc:
        parser.error(f"falta {Path(str(exc.filename)).name} en {args.source}")


if __name__ == "__main__":
    main()
