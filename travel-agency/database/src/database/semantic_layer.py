"""Capa semántica de Viajes Nimbo: el conocimiento del negocio, escrito una vez en código.

Copia el patrón de `07_llm_open_source/.../sesion_2/02_capa_semantica.py`. Los CSV se cargan en el esquema
`crudo`; el modelo solo ve unas vistas que ya llevan dentro las reglas difíciles:

  v_reservas_cliente   una fila por reserva: cliente, tramos e importes (cobrado, reembolsado y NETO)
  v_vuelos_detalle     una fila por vuelo: horas locales, retrasos en minutos y distancia ya calculados
  v_itinerarios        una fila por reserva y trayecto: origen inicial → destino final, retraso en destino final
  v_incidencias        una fila por incidencia, con el retraso y la distancia del viaje completo
  v_resumen_clientes   una fila por cliente: reservas, canceladas, gasto neto e incidencias

Cada vista y cada columna delicada lleva un comentario que el esquema automático incluye. Las vistas se comprueban
con `CHECKS` (cifras calculadas a mano). Igual que en clase, `crudo` no se describe al modelo, pero no está
prohibido: la lista blanca de vistas es cosa del validador de text2sql (fase 5).

Uso (desde travel-agency/):
  uv run python -m database.semantic_layer           # lo que ve el modelo (y lo que no)
  uv run python -m database.semantic_layer --check   # las vistas dan las cifras calculadas a mano
"""

import argparse
from pathlib import Path

import duckdb
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

console = Console()

# ---------------------------------------------------------------------------
# Las vistas: aquí vive el conocimiento del negocio
# ---------------------------------------------------------------------------

VIEWS = """
-- Distancia ortodrómica (haversine) en km, como la mide el Reglamento 261/2004.
CREATE MACRO crudo.distancia_km(lat1, lon1, lat2, lon2) AS
ROUND(2 * 6371 * asin(sqrt(pow(sin(radians(lat2 - lat1) / 2), 2)
      + cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(radians(lon2 - lon1) / 2), 2))), 0);

-- Una fila por reserva. Pagos y tramos se agregan ANTES de unir: sin la trampa del JOIN que duplica.
CREATE VIEW v_reservas_cliente AS
WITH p AS (SELECT reserva_id, SUM(importe) FILTER (WHERE tipo = 'cargo') AS cobrado,
                  -SUM(importe) FILTER (WHERE tipo = 'reembolso') AS reembolsado, SUM(importe) AS neto
           FROM crudo.pagos GROUP BY reserva_id),
t AS (SELECT reserva_id, COUNT(*) AS tramos FROM crudo.reservas_tramos GROUP BY reserva_id)
SELECT r.reserva_id, r.cliente_id, c.nombre || ' ' || c.apellidos AS cliente, r.fecha_reserva, r.estado, r.tipo,
       COALESCE(t.tramos, 0) AS tramos,
       ROUND(COALESCE(p.cobrado, 0), 2) AS importe_cobrado,
       ROUND(COALESCE(p.reembolsado, 0), 2) AS importe_reembolsado,
       ROUND(COALESCE(p.neto, 0), 2) AS importe_neto, r.moneda
FROM crudo.reservas r JOIN crudo.clientes c USING (cliente_id)
LEFT JOIN p USING (reserva_id) LEFT JOIN t USING (reserva_id);

-- Una fila por vuelo. Horas en la zona de SU aeropuerto, minutos calculados sobre el instante real (UTC).
-- (Sin punto y coma en los comentarios: VIEWS se parte por ese carácter, como en clase.)
CREATE VIEW v_vuelos_detalle AS
SELECT v.vuelo_id, v.codigo_vuelo, v.aerolinea_id, al.nombre AS aerolinea,
       v.origen, o.ciudad AS ciudad_origen, v.destino, d.ciudad AS ciudad_destino,
       timezone(o.zona_horaria, v.salida_prevista) AS salida_prevista_local,
       timezone(o.zona_horaria, v.salida_real) AS salida_real_local,
       timezone(d.zona_horaria, v.llegada_prevista) AS llegada_prevista_local,
       timezone(d.zona_horaria, v.llegada_real) AS llegada_real_local,
       CAST((epoch(v.llegada_prevista) - epoch(v.salida_prevista)) / 60 AS INTEGER) AS duracion_prevista_min,
       CAST((epoch(v.salida_real) - epoch(v.salida_prevista)) / 60 AS INTEGER) AS retraso_salida_min,
       CAST((epoch(v.llegada_real) - epoch(v.llegada_prevista)) / 60 AS INTEGER) AS retraso_llegada_min,
       crudo.distancia_km(o.latitud, o.longitud, d.latitud, d.longitud) AS distancia_km,
       o.es_ue AS sale_de_ue, d.es_ue AS llega_a_ue, v.estado
FROM crudo.vuelos v JOIN crudo.aerolineas al USING (aerolinea_id)
JOIN crudo.aeropuertos o ON o.aeropuerto_id = v.origen
JOIN crudo.aeropuertos d ON d.aeropuerto_id = v.destino;

-- Una fila por reserva y trayecto (ida / vuelta). Lo que cuenta es el viaje: primer origen y último destino.
CREATE VIEW v_itinerarios AS
WITH tramos AS (SELECT rt.reserva_id, rt.trayecto, rt.orden, v.*
                FROM crudo.reservas_tramos rt JOIN v_vuelos_detalle v USING (vuelo_id)),
lim AS (SELECT reserva_id, trayecto, MIN(orden) AS primero, MAX(orden) AS ultimo, COUNT(*) AS vuelos,
               string_agg(codigo_vuelo, ' + ' ORDER BY orden) AS codigos_vuelo,
               COUNT(*) FILTER (WHERE estado = 'cancelado') AS vuelos_cancelados
        FROM tramos GROUP BY reserva_id, trayecto)
SELECT l.reserva_id, r.cliente_id, l.trayecto, l.codigos_vuelo, l.vuelos, l.vuelos - 1 AS escalas,
       p.origen, p.ciudad_origen, u.destino AS destino_final, u.ciudad_destino AS ciudad_destino_final,
       p.salida_prevista_local, u.llegada_prevista_local, u.llegada_real_local,
       u.retraso_llegada_min AS retraso_llegada_destino_min,
       crudo.distancia_km(ao.latitud, ao.longitud, ad.latitud, ad.longitud) AS distancia_km,
       l.vuelos_cancelados
FROM lim l JOIN crudo.reservas r USING (reserva_id)
JOIN tramos p ON p.reserva_id = l.reserva_id AND p.trayecto = l.trayecto AND p.orden = l.primero
JOIN tramos u ON u.reserva_id = l.reserva_id AND u.trayecto = l.trayecto AND u.orden = l.ultimo
JOIN crudo.aeropuertos ao ON ao.aeropuerto_id = p.origen
JOIN crudo.aeropuertos ad ON ad.aeropuerto_id = u.destino;

-- Una fila por incidencia. Retraso y distancia del VIAJE (itinerario), no del vuelo suelto.
CREATE VIEW v_incidencias AS
SELECT i.incidencia_id, i.tipo, i.fecha, i.estado, i.compensacion, i.reserva_id, it.cliente_id,
       c.nombre || ' ' || c.apellidos AS cliente, i.vuelo_id, v.codigo_vuelo, v.estado AS estado_vuelo,
       it.trayecto, it.origen, it.destino_final, it.escalas, it.retraso_llegada_destino_min,
       it.distancia_km AS distancia_itinerario_km
FROM crudo.incidencias i
JOIN crudo.reservas_tramos rt ON rt.reserva_id = i.reserva_id AND rt.vuelo_id = i.vuelo_id
JOIN v_itinerarios it ON it.reserva_id = i.reserva_id AND it.trayecto = rt.trayecto
JOIN v_vuelos_detalle v ON v.vuelo_id = i.vuelo_id
JOIN crudo.clientes c ON c.cliente_id = it.cliente_id;

-- Una fila por cliente, también los que no tienen reservas. Se agrega ANTES de unir.
CREATE VIEW v_resumen_clientes AS
WITH r AS (SELECT cliente_id, COUNT(*) AS reservas, COUNT(*) FILTER (WHERE estado = 'cancelada') AS canceladas,
                  SUM(importe_neto) AS gasto_neto
           FROM v_reservas_cliente GROUP BY cliente_id),
i AS (SELECT cliente_id, COUNT(*) AS incidencias FROM v_incidencias GROUP BY cliente_id)
SELECT c.cliente_id, c.nombre || ' ' || c.apellidos AS cliente, c.pais, c.nivel_fidelidad, c.fecha_alta,
       COALESCE(r.reservas, 0) AS reservas, COALESCE(r.canceladas, 0) AS reservas_canceladas,
       ROUND(COALESCE(r.gasto_neto, 0), 2) AS gasto_neto, COALESCE(i.incidencias, 0) AS incidencias
FROM crudo.clientes c LEFT JOIN r USING (cliente_id) LEFT JOIN i USING (cliente_id);
"""

# Comentarios de cada vista y columna: el esquema automático los enseña al modelo.
COMMENTS: dict[str, tuple[str, dict[str, str]]] = {
    "v_reservas_cliente": (
        "Una fila por reserva. Una reserva NO es un vuelo: puede tener varios tramos (ida, vuelta, escalas).",
        {
            "cliente_id": "identificador único del cliente; dos clientes pueden llamarse igual",
            "estado": "'completada' (ya viajó), 'confirmada' (viaje futuro) o 'cancelada'",
            "tramos": "vuelos que forman la reserva",
            "importe_cobrado": "EUR cobrados (suma de cargos); NO descuenta reembolsos",
            "importe_reembolsado": "EUR devueltos al cliente (positivo)",
            "importe_neto": "importe_cobrado − importe_reembolsado. SUM(importe_neto) = facturación neta",
        },
    ),
    "v_vuelos_detalle": (
        "Una fila por vuelo, con sus horas, retrasos y distancia ya calculados. Un vuelo puede estar en varias "
        "reservas.",
        {
            "salida_prevista_local": "hora local del aeropuerto de origen",
            "salida_real_local": "hora local del aeropuerto de origen; NULL si no ha salido",
            "llegada_prevista_local": "hora local del aeropuerto de destino",
            "llegada_real_local": "hora local del aeropuerto de destino; NULL si no ha llegado",
            "duracion_prevista_min": "minutos de vuelo previstos (ya descontadas las zonas horarias)",
            "retraso_salida_min": "minutos de retraso al despegar; NO es el retraso que cuenta para compensar",
            "retraso_llegada_min": "minutos de retraso al llegar a ESTE destino; negativo = llegó antes; "
            "NULL si no ha volado o se canceló (NO es 0)",
            "distancia_km": "km en línea recta entre origen y destino de este vuelo",
            "sale_de_ue": "true si el aeropuerto de origen está en la UE",
            "llega_a_ue": "true si el aeropuerto de destino está en la UE",
            "estado": "'en_hora', 'retrasado', 'cancelado' o 'programado' (aún no ha volado)",
        },
    ),
    "v_itinerarios": (
        "Una fila por reserva y trayecto (ida o vuelta): el viaje del origen inicial al destino final, con "
        "escalas. Para compensaciones del Reglamento 261/2004, usa esta vista y no la del vuelo suelto.",
        {
            "trayecto": "'ida' o 'vuelta'",
            "codigos_vuelo": "vuelos del trayecto en orden, p. ej. 'KL1701 + VY1002'",
            "escalas": "vuelos − 1",
            "destino_final": "aeropuerto donde termina el trayecto",
            "retraso_llegada_destino_min": "minutos de retraso al llegar al DESTINO FINAL: el que cuenta para "
            "el Reglamento 261/2004; NULL si no ha volado o se canceló",
            "distancia_km": "km en línea recta del origen inicial al destino final (la del Reglamento); "
            "NO es la suma de los vuelos",
            "vuelos_cancelados": "vuelos cancelados en el trayecto",
        },
    ),
    "v_incidencias": (
        "Una fila por incidencia (reclamación) de un cliente sobre un vuelo de su reserva.",
        {
            "tipo": "'retraso', 'cancelacion' o 'equipaje'",
            "estado": "'abierta', 'resuelta' o 'rechazada'",
            "compensacion": "EUR pagados al cliente por la incidencia; NULL si no se ha pagado nada; NO está en los "
            "pagos de la reserva",
            "estado_vuelo": "estado del vuelo de la incidencia",
            "retraso_llegada_destino_min": "retraso al llegar al destino final del trayecto (no del vuelo suelto)",
            "distancia_itinerario_km": "km del origen inicial al destino final del trayecto (la del Reglamento)",
        },
    ),
    "v_resumen_clientes": (
        "Una fila por cliente, también los que no tienen reservas. Para totales por cliente.",
        {
            "cliente_id": "identificador único; dos clientes pueden llamarse igual",
            "nivel_fidelidad": "'basico', 'plata' u 'oro'",
            "reservas": "reservas del cliente, canceladas incluidas",
            "gasto_neto": "SUM(importe_neto) de sus reservas: cobrado − reembolsado",
            "incidencias": "incidencias del cliente",
        },
    ),
}

# Guía de uso: qué vista para qué pregunta (no son reglas de cálculo: el cálculo ya está en las vistas).
GUIDE = """Qué vista usar:
- Una reserva concreta, sus importes (cobrado, reembolsado, neto) o las reservas de un cliente: v_reservas_cliente.
- Un vuelo concreto (horas, retraso al salir y al llegar, distancia, estado): v_vuelos_detalle.
- El viaje completo de una reserva (origen inicial → destino final, escalas, retraso en destino final,
  distancia del viaje): v_itinerarios.
- Incidencias y reclamaciones (retraso, cancelación, equipaje) y su compensación: v_incidencias.
- Totales por cliente (reservas, canceladas, gasto neto, incidencias): v_resumen_clientes.
- Cada vista ya trae cliente, vuelo y ciudades: casi nunca hace falta un JOIN.

Métricas:
- Facturación neta = SUM(importe_neto) en v_reservas_cliente · SUM(gasto_neto) en v_resumen_clientes.
  SUM(importe_cobrado) NO descuenta reembolsos.
- Reservas = COUNT(*) en v_reservas_cliente. Vuelos de las reservas = SUM(tramos). Una reserva NO es un vuelo.
- Retraso del Reglamento 261/2004 = retraso_llegada_destino_min (al llegar al destino final), NO retraso_salida_min.
- Distancia del Reglamento 261/2004 = distancia_km de v_itinerarios (origen inicial → destino final),
  NO la suma de los vuelos.

Cálculos:
- Sumas, diferencias, porcentajes y medias, DENTRO del SQL. Nunca de cabeza.
- Duraciones y retrasos: usa las columnas *_min, ya calculadas. Las columnas *_local están en la hora local de
  su aeropuerto: no las restes entre sí.
- Retraso NULL = el vuelo no ha volado (programado) o se canceló; NO es 0 minutos.
- Clientes con el mismo nombre: distingue siempre por cliente_id.

Datos que NO existen (si los piden, dilo y explica qué dato sí hay):
pasajeros de cada reserva (una reserva no dice cuántas personas viajan), precio de cada vuelo (el importe es de la
reserva entera), detalle de los paquetes (hotel, traslados), causa del retraso o de la cancelación (meteorología,
huelga…), datos de contacto de los clientes, puntos de fidelidad, tarifas y condiciones del billete."""


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------


def open_db(data_dir: Path = DATA_DIR) -> duckdb.DuckDBPyConnection:
    """CSV en el esquema oculto «crudo», vistas en «main», sin acceso a archivos."""
    con = duckdb.connect()
    con.execute("CREATE SCHEMA crudo")
    for csv in sorted(data_dir.glob("*.csv")):
        con.execute(f"CREATE TABLE crudo.{csv.stem} AS SELECT * FROM read_csv_auto('{csv.as_posix()}')")
    for statement in VIEWS.strip().split(";"):
        if statement.strip():
            con.execute(statement)

    def quote(text: str) -> str:
        return "'" + text.replace("'", "''") + "'"

    for view, (desc, cols) in COMMENTS.items():
        con.execute(f"COMMENT ON VIEW {view} IS {quote(desc)}")
        for col, comment in cols.items():
            con.execute(f"COMMENT ON COLUMN {view}.{col} IS {quote(comment)}")
    con.execute("SET enable_external_access = false")
    con.execute("SET lock_configuration = true")
    return con


def _scalar(con: duckdb.DuckDBPyConnection, sql: str) -> object:
    """Primer valor de la primera fila (las consultas de `schema` siempre devuelven una)."""
    row = con.execute(sql).fetchone()
    return row[0] if row else None


def schema(con: duckdb.DuckDBPyConnection, max_values: int = 6) -> str:
    """Esquema automático de lo que está en «main» (las vistas), con sus comentarios. Nadie lo escribe a mano."""
    objects = [
        r[0]
        for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1"
        ).fetchall()
    ]
    view_comments = dict(con.execute("SELECT view_name, comment FROM duckdb_views() WHERE NOT internal").fetchall())
    column_comments = {
        (table, col): comment
        for table, col, comment in con.execute(
            "SELECT table_name, column_name, comment FROM duckdb_columns() WHERE comment IS NOT NULL"
        ).fetchall()
    }
    parts = []
    for name in objects:
        n = _scalar(con, f"SELECT COUNT(*) FROM {name}")
        header = f"Tabla {name} ({n} filas)" + (f": {view_comments[name]}" if view_comments.get(name) else "")
        lines = []
        for col, col_type, *_ in con.execute(f"DESCRIBE {name}").fetchall():
            distinct = _scalar(con, f'SELECT COUNT(DISTINCT "{col}") FROM {name}')
            if isinstance(distinct, int) and distinct <= max_values:
                values = [str(r[0]) for r in con.execute(f'SELECT DISTINCT "{col}" FROM {name} ORDER BY 1').fetchall()]
                extra = f" valores: {', '.join(values)}"
            else:
                example = _scalar(con, f'SELECT "{col}" FROM {name} WHERE "{col}" IS NOT NULL ORDER BY 1 LIMIT 1')
                extra = f" ej.: {example}"
            note = f" — {column_comments[(name, col)]}" if (name, col) in column_comments else ""
            lines.append(f"  - {col} ({col_type}){extra}{note}")
        parts.append(header + ":\n" + "\n".join(lines))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Comprobación: las vistas dan las cifras calculadas a mano sobre los CSV
# ---------------------------------------------------------------------------

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


def main() -> None:
    parser = argparse.ArgumentParser(description="La capa semántica: lo que ve el modelo en lugar de los CSV.")
    parser.add_argument("--check", action="store_true", help="Comprobar las vistas contra las cifras a mano.")
    args = parser.parse_args()
    con = open_db()
    if args.check:
        raise SystemExit(0 if run_checks(con) else 1)
    hidden = [
        r[0]
        for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'crudo' ORDER BY 1"
        ).fetchall()
    ]
    console.print(
        Panel(
            "\n".join(f"crudo.{t}" for t in hidden)
            + "\n\nLos CSV siguen ahí en `crudo`, pero no se incluyen en el esquema que presentamos al modelo.",
            title=f"LO QUE EL MODELO NO VE · los {len(hidden)} CSV crudos",
            border_style="red",
        )
    )
    console.print(
        Panel(
            schema(con),
            title="LO QUE EL MODELO SÍ VE · las vistas, con sus comentarios (esquema generado por el código)",
            border_style="green",
        )
    )
    console.print(Panel(GUIDE, title="Y una guía: qué vista para qué pregunta", border_style="white"))


if __name__ == "__main__":
    main()
