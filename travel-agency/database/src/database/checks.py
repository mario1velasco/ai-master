"""Comprobación: las vistas de la capa semántica dan las cifras calculadas a mano sobre los CSV de `fixtures/`.

Como `COMPROBACIONES` de `07_llm_open_source/.../sesion_2/02_capa_semantica.py`. Se ejecuta con
`uv run python -m database.semantic_layer --check --data database/fixtures` y es la base de los tests de integridad.
"""

import duckdb
from rich.console import Console
from rich.table import Table

console = Console()

type Row = tuple[object, ...]

CHECKS: list[tuple[str, str, list[Row]]] = [
    (
        "Reservas y vuelos reservados (una reserva NO es un vuelo)",
        "SELECT COUNT(*), SUM(tramos) FROM v_reservas_cliente",
        [(7, 12)],
    ),
    (
        "Facturación: cobrado, reembolsado y neto",
        "SELECT SUM(importe_cobrado), SUM(importe_reembolsado), SUM(importe_neto) FROM v_reservas_cliente",
        [(2319.0, 470.0, 1849.0)],
    ),
    (
        "R-1042: cobrado y neto (un paquete con reembolso parcial)",
        "SELECT importe_cobrado, importe_neto FROM v_reservas_cliente WHERE reserva_id = 'R-1042'",
        [(1250.0, 1100.0)],
    ),
    (
        "IB3166: retraso al salir y al llegar, duración y distancia (Madrid → Nueva York)",
        "SELECT retraso_salida_min, retraso_llegada_min, duracion_prevista_min, distancia_km "
        "FROM v_vuelos_detalle WHERE codigo_vuelo = 'IB3166'",
        [(297, 312, 510, 5762.0)],
    ),
    (
        "IB3166: hora local de llegada prevista en Nueva York",
        "SELECT strftime(llegada_prevista_local, '%Y-%m-%d %H:%M') FROM v_vuelos_detalle WHERE codigo_vuelo = 'IB3166'",
        [("2026-07-01 12:35",)],
    ),
    (
        "VY1234: sale con 3 h 20 min de retraso pero llega con menos de 3 h",
        "SELECT retraso_salida_min, retraso_llegada_min, duracion_prevista_min FROM v_vuelos_detalle "
        "WHERE codigo_vuelo = 'VY1234'",
        [(200, 175, 160)],
    ),
    (
        "FR7312: retraso que cruza la medianoche",
        "SELECT retraso_llegada_min FROM v_vuelos_detalle WHERE codigo_vuelo = 'FR7312'",
        [(165,)],
    ),
    (
        "Vuelo programado y vuelo cancelado: retraso NULL, no 0",
        "SELECT codigo_vuelo, retraso_llegada_min, estado FROM v_vuelos_detalle "
        "WHERE codigo_vuelo IN ('IB0731', 'AF1001') ORDER BY 1",
        [("AF1001", None, "cancelado"), ("IB0731", None, "programado")],
    ),
    (
        "v_tramos: una fila por vuelo de cada reserva (las 12 de R-1042 a R-1048 en reservas_tramos)",
        "SELECT COUNT(*) FROM v_tramos WHERE reserva_id BETWEEN 'R-1042' AND 'R-1048'",
        [(12,)],
    ),
    (
        "v_tramos: R-1042 ida con su vuelo, clase, asiento y maleta",
        "SELECT codigo_vuelo, clase, asiento, equipaje_facturado FROM v_tramos "
        "WHERE reserva_id = 'R-1042' AND trayecto = 'ida'",
        [("IB3166", "turista", "23A", True)],
    ),
    (
        "v_tramos: R-1044 con escala, cada vuelo con su aerolínea, y R-1047 aún sin asiento",
        "SELECT reserva_id, orden, aerolinea, asiento FROM v_tramos WHERE reserva_id IN ('R-1044', 'R-1047') "
        "ORDER BY reserva_id, orden",
        [("R-1044", 1, "KLM", "8C"), ("R-1044", 2, "Vueling", "17D"), ("R-1047", 1, "Iberia", None)],
    ),
    (
        "R-1044 con escala: distancia del viaje (no la suma) y retraso en destino final",
        "SELECT origen, destino_final, escalas, distancia_km, retraso_llegada_destino_min FROM v_itinerarios "
        "WHERE reserva_id = 'R-1044'",
        [("AMS", "MAD", 1, 1461.0, 190)],
    ),
    (
        "Ida y vuelta: dos trayectos, cada uno con su destino",
        "SELECT trayecto, origen, destino_final FROM v_itinerarios WHERE reserva_id = 'R-1043' ORDER BY 1",
        [("ida", "MAD", "TFN"), ("vuelta", "TFN", "MAD")],
    ),
    (
        "Incidencia de R-1044: usa la distancia y el retraso del viaje, no del vuelo BCN → MAD",
        "SELECT codigo_vuelo, distancia_itinerario_km, retraso_llegada_destino_min FROM v_incidencias "
        "WHERE incidencia_id = 'I-03'",
        [("VY1002", 1461.0, 190)],
    ),
    (
        "Dos clientes llamados Ana López, distintos por cliente_id",
        "SELECT cliente_id, reservas, gasto_neto FROM v_resumen_clientes WHERE cliente LIKE 'Ana López%' ORDER BY 1",
        [("C-001", 2, 1195.0), ("C-004", 1, 230.0)],
    ),
    (
        "Cliente sin reservas: aparece con 0",
        "SELECT reservas, gasto_neto, incidencias FROM v_resumen_clientes WHERE cliente_id = 'C-007'",
        [(0, 0.0, 0)],
    ),
]


def rounded_rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[Row]:
    """Resultado de `sql` con los decimales redondeados a 2, para compararlo con lo esperado."""
    return [tuple(round(v, 2) if isinstance(v, float) else v for v in row) for row in con.execute(sql).fetchall()]


def run_checks(con: duckdb.DuckDBPyConnection) -> bool:
    table = Table(title="Las vistas frente a las cifras calculadas a mano sobre los CSV")
    for col in ("Comprobación", "Resultado de la vista", "Esperado", ""):
        table.add_column(col)
    all_ok = True
    for name, sql, expected in CHECKS:
        rows = rounded_rows(con, sql)
        ok = rows == expected
        all_ok &= ok
        table.add_row(name, str(rows), str(expected), "[green]✓[/]" if ok else "[red]✗[/]")
    console.print(table)
    return all_ok
