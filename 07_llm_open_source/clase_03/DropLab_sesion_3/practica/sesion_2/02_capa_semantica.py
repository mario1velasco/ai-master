"""Capa semántica de DropLab: el conocimiento del negocio, escrito una vez en código.

En la sesión 1 el modelo escribía SQL sobre las tablas crudas (los CSV) y caía en
las trampas del caso: periodo A = «marzo», el JOIN con calendario, abonos sin
tienda... Las reglas estaban en el prompt y el modelo podía ignorarlas.

Aquí el programa le presenta al modelo unas vistas (tablas virtuales) que ya llevan
dentro esas reglas. Los CSV se cargan en el esquema `crudo`; no forman parte del
esquema que se le presenta en el prompt:

  resumen_diario   por tienda y día: pedidos, unidades, ventas, abonos y VENTAS NETAS ya calculadas
  pedidos          una fila por compra (cesta, pedidos de 4+ unidades, ticket)
  ventas_lineas    cada línea con su periodo, tienda y producto ya pegados
  abonos           cada abono con su periodo (por fecha de reconocimiento) y la tienda heredada
  movimientos      ventas y abonos juntos, por producto (netos por modelo, categoría...)
  disponibilidad   stock con producto y horas (solo 8 SKU de Street One)
  tiendas, catalogo

Cada vista y cada columna lleva un comentario que el esquema automático incluye
(«NO descuenta abonos», «un pedido NO es un cliente»...). Las vistas se han
comprobado contra practica/sesion_1/03_metricas_basicas.py (--comprobar). La barrera
SQL limita las consultas, pero no es una política de permisos por esquema: el modelo
recibe el esquema de las vistas; no se debe describir `crudo` como inaccesible.

Uso:
  python practica/sesion_2/02_capa_semantica.py                 # lo que ve el modelo (y lo que no)
  python practica/sesion_2/02_capa_semantica.py --comprobar     # las vistas dan las cifras del 03
  python practica/sesion_2/02_capa_semantica.py --sql "SELECT periodo, SUM(ventas_netas) FROM resumen_diario WHERE tienda = 'Malasaña' GROUP BY periodo"

Origen: experimentos/text2sql/ (versión 3, la elegida). Explicación: docs/sesion_2/00.
"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module
from pathlib import Path

import duckdb
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sesion_1"))
metricas = import_module("03_metricas_basicas")          # solo para saber dónde están los CSV
sql08 = import_module("08_herramienta_sql")              # las mismas barreras de seguridad que en la sesión 1

console = Console()

# ---------------------------------------------------------------------------
# Las vistas: aquí vive el conocimiento del negocio
# ---------------------------------------------------------------------------

VISTAS = """
CREATE VIEW tiendas AS SELECT local_id, nombre AS tienda, ciudad FROM crudo.locales;

CREATE VIEW catalogo AS
SELECT sku, modelo, color, categoria, CAST(talla AS VARCHAR) AS talla, precio_lista FROM crudo.referencias;

-- Periodo de cada venta, por fecha_venta. Tienda y producto ya pegados.
CREATE VIEW ventas_lineas AS
SELECT v.linea_id, v.pedido_id, v.fecha_venta,
       CASE WHEN v.fecha_venta BETWEEN DATE '2026-03-02' AND DATE '2026-03-29' THEN 'A'
            WHEN v.fecha_venta BETWEEN DATE '2026-03-30' AND DATE '2026-04-26' THEN 'B' END AS periodo,
       v.local_id, l.nombre AS tienda, v.sku, r.modelo, r.color, CAST(r.talla AS VARCHAR) AS talla, r.categoria,
       v.cantidad, v.precio_unitario, v.descuento_linea, v.importe_linea AS importe_antes_reembolsos
FROM crudo.ventas v JOIN crudo.locales l USING (local_id) LEFT JOIN crudo.referencias r USING (sku);

-- Una fila por compra.
CREATE VIEW pedidos AS
SELECT pedido_id, MIN(fecha_venta) AS fecha_venta, MIN(periodo) AS periodo, MIN(local_id) AS local_id,
       MIN(tienda) AS tienda, COUNT(*) AS lineas, SUM(cantidad) AS unidades,
       ROUND(SUM(importe_antes_reembolsos), 2) AS importe_antes_reembolsos
FROM ventas_lineas GROUP BY pedido_id;

-- Periodo de cada abono, por fecha_reconocimiento (NO por la fecha de la venta). Tienda heredada de la venta.
CREATE VIEW abonos AS
SELECT a.reembolso_id, a.linea_id, v.pedido_id, a.fecha_reconocimiento,
       CASE WHEN a.fecha_reconocimiento BETWEEN DATE '2026-03-02' AND DATE '2026-03-29' THEN 'A'
            WHEN a.fecha_reconocimiento BETWEEN DATE '2026-03-30' AND DATE '2026-04-26' THEN 'B' END AS periodo,
       v.local_id, v.tienda, v.sku, v.modelo, v.categoria, v.fecha_venta AS fecha_venta_original,
       a.unidades AS unidades_devueltas, a.importe_reembolso AS importe_abonado, a.motivo
FROM crudo.reembolsos a JOIN ventas_lineas v USING (linea_id);

-- Ventas y abonos juntos, cada uno en su fecha: SUM(importe_neto) = ventas netas.
CREATE VIEW movimientos AS
SELECT 'venta' AS tipo, fecha_venta AS fecha, periodo, local_id, tienda, pedido_id, linea_id, sku, modelo, color,
       talla, categoria, importe_antes_reembolsos AS importe_venta, 0.0 AS importe_abonado,
       importe_antes_reembolsos AS importe_neto FROM ventas_lineas
UNION ALL
SELECT 'abono', a.fecha_reconocimiento, a.periodo, a.local_id, a.tienda, a.pedido_id, a.linea_id, a.sku, a.modelo,
       v.color, v.talla, a.categoria, 0.0, a.importe_abonado, -a.importe_abonado
FROM abonos a JOIN ventas_lineas v USING (linea_id);

-- Las métricas oficiales, por tienda y día. Se agrega ANTES de unir: sin trampa del JOIN.
CREATE VIEW resumen_diario AS
WITH dias AS (SELECT fecha, local_id FROM crudo.calendario),
v AS (SELECT fecha_venta AS fecha, local_id, COUNT(DISTINCT pedido_id) AS pedidos, COUNT(*) AS lineas,
             SUM(cantidad) AS unidades, SUM(importe_antes_reembolsos) AS ventas
      FROM ventas_lineas GROUP BY 1, 2),
a AS (SELECT fecha_reconocimiento AS fecha, local_id, COUNT(*) AS n_abonos, SUM(importe_abonado) AS abonado
      FROM abonos GROUP BY 1, 2)
SELECT d.fecha,
       CASE WHEN d.fecha BETWEEN DATE '2026-03-02' AND DATE '2026-03-29' THEN 'A'
            WHEN d.fecha BETWEEN DATE '2026-03-30' AND DATE '2026-04-26' THEN 'B' END AS periodo,
       d.local_id, l.nombre AS tienda,
       COALESCE(v.pedidos, 0) AS pedidos, COALESCE(v.lineas, 0) AS lineas, COALESCE(v.unidades, 0) AS unidades,
       ROUND(COALESCE(v.ventas, 0), 2) AS ventas_antes_reembolsos,
       COALESCE(a.n_abonos, 0) AS n_abonos, ROUND(COALESCE(a.abonado, 0), 2) AS abonos_reconocidos,
       ROUND(COALESCE(v.ventas, 0) - COALESCE(a.abonado, 0), 2) AS ventas_netas
FROM dias d JOIN crudo.locales l USING (local_id)
LEFT JOIN v USING (fecha, local_id) LEFT JOIN a USING (fecha, local_id);

CREATE VIEW disponibilidad AS
SELECT d.local_id, l.nombre AS tienda, d.sku, r.modelo, r.color, CAST(r.talla AS VARCHAR) AS talla,
       d.inicio, d.fin, date_diff('minute', d.inicio, d.fin) / 60.0 AS horas, d.unidades_disponibles
FROM crudo.disponibilidad d JOIN crudo.locales l USING (local_id) LEFT JOIN crudo.referencias r USING (sku);
"""

# Comentarios de cada vista y columna: el esquema automático los enseña al modelo.
COMENTARIOS = {
    "tiendas": ("Una fila por tienda.", {}),
    "catalogo": ("Una fila por producto (SKU = modelo + color + talla).", {
        "precio_lista": "precio de catálogo por unidad; no es el coste ni lo que pagó el cliente"}),
    "ventas_lineas": ("Una fila por línea de pedido (un pedido tiene varias líneas). Úsala para cualquier pregunta "
                      "por producto (modelo, categoría, talla, color).", {
        "periodo": "'A', 'B' o NULL según fecha_venta",
        "cantidad": "unidades de la línea",
        "importe_antes_reembolsos": "EUR de la línea, descuento ya restado; NO descuenta abonos"}),
    "pedidos": ("Una fila por pedido (compra completa). Para preguntas sobre la cesta. Un pedido NO es un cliente.", {
        "periodo": "'A', 'B' o NULL según fecha_venta",
        "lineas": "líneas del pedido", "unidades": "unidades totales del pedido",
        "importe_antes_reembolsos": "EUR del pedido; NO descuenta abonos"}),
    "abonos": ("Una fila por reembolso, con la tienda y el producto de la venta original.", {
        "periodo": "'A', 'B' o NULL según fecha_reconocimiento (NO según la fecha de la venta)",
        "importe_abonado": "EUR abonados (positivo)",
        "unidades_devueltas": "artículos devueltos físicamente; puede ser 0 (ajuste de dinero)"}),
    "movimientos": ("Ventas y abonos juntos, por producto, cada uno en su fecha y periodo. Para netas o abonos "
                    "por producto.", {
        "tipo": "'venta' o 'abono'",
        "fecha": "venta: fecha_venta; abono: fecha_reconocimiento",
        "importe_venta": "EUR vendidos (solo en filas de venta; 0 en abonos)",
        "importe_abonado": "EUR abonados (solo en filas de abono; 0 en ventas)",
        "importe_neto": "importe_venta − importe_abonado. SUM(importe_neto) = ventas netas"}),
    "resumen_diario": ("Métricas oficiales por tienda y día (2026-03-02 a 2026-04-26), SIN producto. No sirve si la "
                       "pregunta filtra por modelo, categoría, talla o color.", {
        "periodo": "'A' o 'B'",
        "pedidos": "pedidos de ese día", "unidades": "unidades vendidas ese día",
        "ventas_antes_reembolsos": "EUR vendidos ese día",
        "n_abonos": "abonos reconocidos ese día", "abonos_reconocidos": "EUR abonados ese día",
        "ventas_netas": "ventas_antes_reembolsos − abonos_reconocidos de ese día"}),
    "disponibilidad": ("Stock observado por intervalos. SOLO 8 SKU de Street One; un producto sin filas no se "
                       "observa (no es stock cero).", {
        "horas": "duración del intervalo en horas",
        "unidades_disponibles": "unidades disponibles durante el intervalo"}),
}

# Guía de uso: qué tabla para qué pregunta (no son reglas de cálculo: el cálculo ya está en las vistas).
GUIA = """Qué tabla usar:
- Totales por tienda, día o periodo, SIN filtro de producto (ventas, abonos, netas, pedidos, unidades): resumen_diario, sumando sus columnas.
- Cualquier filtro o agrupación por producto (modelo, categoría, talla, color, sku): ventas_lineas (unidades, ventas antes de reembolsos) o movimientos (si hacen falta abonos o ventas netas).
- Cómo son los pedidos (pedidos con X unidades, importe de cada pedido, ticket): pedidos.
- Reembolsos concretos (motivo, línea, unidades devueltas): abonos. Stock: disponibilidad.
- Cada tabla ya trae tienda, periodo y producto: casi nunca hace falta un JOIN.

Métricas:
- Ventas antes de reembolsos = SUM(ventas_antes_reembolsos) en resumen_diario · SUM(importe_antes_reembolsos) en ventas_lineas o pedidos · SUM(importe_venta) en movimientos.
- Abonos reconocidos = SUM(abonos_reconocidos) en resumen_diario · SUM(importe_abonado) en abonos o movimientos.
- Ventas netas = SUM(ventas_netas) en resumen_diario · SUM(importe_neto) en movimientos. importe_neto NUNCA son ventas antes de reembolsos.
- Pedidos = SUM(pedidos) en resumen_diario o COUNT(*) en pedidos. Unidades = SUM(unidades) o SUM(cantidad).

Cálculos:
- Porcentajes, ratios y variaciones, DENTRO del SQL: por ejemplo ROUND(100.0 * SUM(x) / SUM(y), 2). Nunca de cabeza.
- Ratios: divide totales (SUM / SUM), no hagas medias de medias.
- Periodos: usa la columna periodo ('A' o 'B'). Filtra por fecha solo si la pregunta da días concretos.

Datos que NO existen (si los piden, dilo y explica qué dato sí hay):
clientes (no hay cliente_id: un pedido no es una persona), visitas o tráfico, hora de la venta, costes y margen,
campaña aplicada a cada pedido, regalos entregados, demanda no atendida."""

INSTRUCCIONES = """Eres el analista de datos de DropLab. Tienes una base DuckDB de solo lectura.
Para obtener cualquier cifra usa la herramienta ejecutar_sql con UNA consulta SELECT.
No inventes tablas ni columnas. Si la consulta da error, corrígela.
Haz TODAS las operaciones (sumas, restas, divisiones) dentro del SQL; no calcules de cabeza.
Si la pregunta compara periodos o tiendas, obtén cada valor y etiquétalo.
Si la pregunta pide un dato que no existe en las tablas, dilo claramente en lugar de aproximarlo.
Responde en español, en un máximo de 5 frases, con las cifras exactas del resultado
(dos decimales para importes) e indica a qué tienda y periodo corresponde cada una."""

PERIODOS = """Periodos (ambos días incluidos):
- Periodo A: del 2026-03-02 al 2026-03-29.
- Periodo B: del 2026-03-30 al 2026-04-26.
Tiendas: MAD-MAL = Malasaña, MAD-GOY = Goya, BCN-EIX = Eixample."""


# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------


def abrir() -> duckdb.DuckDBPyConnection:
    """CSV en el esquema oculto «crudo», vistas en «main», sin acceso a archivos."""
    con = duckdb.connect()
    con.execute("CREATE SCHEMA crudo")
    for csv in sorted(metricas.DATA.glob("*.csv")):
        con.execute(f"CREATE TABLE crudo.{csv.stem} AS SELECT * FROM read_csv_auto('{csv.as_posix()}')")
    for sentencia in VISTAS.strip().split(";"):
        if sentencia.strip():
            con.execute(sentencia)

    def lit(texto: str) -> str:
        return "'" + texto.replace("'", "''") + "'"
    for vista, (desc, cols) in COMENTARIOS.items():
        con.execute(f"COMMENT ON VIEW {vista} IS {lit(desc)}")
        for col, c in cols.items():
            con.execute(f"COMMENT ON COLUMN {vista}.{col} IS {lit(c)}")
    con.execute("SET enable_external_access = false")
    con.execute("SET lock_configuration = true")
    return con


def esquema(con: duckdb.DuckDBPyConnection, max_valores: int = 6) -> str:
    """Esquema automático de lo que está en «main» (las vistas), con sus comentarios. Nadie lo escribe a mano."""
    objetos = [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1").fetchall()]
    com_vista = dict(con.execute("SELECT view_name, comment FROM duckdb_views() WHERE NOT internal").fetchall())
    com_col = {(t, c): k for t, c, k in con.execute(
        "SELECT table_name, column_name, comment FROM duckdb_columns() WHERE comment IS NOT NULL").fetchall()}
    partes = []
    for nombre in objetos:
        n = con.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0]
        cab = f"Tabla {nombre} ({n} filas)" + (f": {com_vista[nombre]}" if com_vista.get(nombre) else "")
        lineas = []
        for col, tipo, *_ in con.execute(f"DESCRIBE {nombre}").fetchall():
            distintos = con.execute(f'SELECT COUNT(DISTINCT "{col}") FROM {nombre}').fetchone()[0]
            if distintos <= max_valores:
                vals = [str(r[0]) for r in con.execute(f'SELECT DISTINCT "{col}" FROM {nombre} ORDER BY 1').fetchall()]
                extra = f" valores: {', '.join(vals)}"
            else:
                ej = con.execute(f'SELECT "{col}" FROM {nombre} WHERE "{col}" IS NOT NULL ORDER BY 1 LIMIT 1').fetchone()[0]
                extra = f" ej.: {ej}"
            nota = f" — {com_col[(nombre, col)]}" if (nombre, col) in com_col else ""
            lineas.append(f"  - {col} ({tipo}){extra}{nota}")
        partes.append(cab + ":\n" + "\n".join(lineas))
    return "\n\n".join(partes)


def construir_system_prompt(con: duckdb.DuckDBPyConnection) -> str:
    return "\n\n".join([INSTRUCCIONES, esquema(con), PERIODOS, GUIA])


def ejecutar_sql(con: duckdb.DuckDBPyConnection, consulta: str) -> tuple[bool, str]:
    """Las barreras de la sesión 1 (solo SELECT, una sentencia, sin archivos, 50 filas)."""
    return sql08.ejecutar_sql_seguro(con, consulta)


# ---------------------------------------------------------------------------
# Comprobación: las vistas dan las mismas cifras que el script 03
# ---------------------------------------------------------------------------

COMPROBACIONES = [
    ("Neto de Malasaña, A y B",
     "SELECT periodo, SUM(ventas_netas) FROM resumen_diario WHERE local_id = 'MAD-MAL' GROUP BY 1 ORDER BY 1",
     [("A", 40000.0), ("B", 26000.0)]),
    ("Neto de la empresa, A y B",
     "SELECT periodo, ROUND(SUM(ventas_netas), 2) FROM resumen_diario GROUP BY 1 ORDER BY 1",
     [("A", 96000.0), ("B", 81000.0)]),
    ("Lo mismo, desde movimientos",
     "SELECT periodo, ROUND(SUM(importe_neto), 2) FROM movimientos WHERE periodo IS NOT NULL GROUP BY 1 ORDER BY 1",
     [("A", 96000.0), ("B", 81000.0)]),
    ("Cesta de Malasaña (pedidos, unidades)",
     "SELECT periodo, SUM(pedidos), SUM(unidades) FROM resumen_diario WHERE local_id = 'MAD-MAL' GROUP BY 1 ORDER BY 1",
     [("A", 120, 467), ("B", 120, 304)]),
    ("Pedidos de 4+ unidades en Malasaña",
     "SELECT periodo, COUNT(*) FROM pedidos WHERE local_id = 'MAD-MAL' AND unidades >= 4 AND periodo IS NOT NULL "
     "GROUP BY 1 ORDER BY 1",
     [("A", 108), ("B", 7)]),
    ("Abonos de HIST-JOIN-001 en A (venta de febrero)",
     "SELECT COUNT(*), SUM(importe_abonado) FROM abonos WHERE linea_id = 'HIST-JOIN-001' AND periodo = 'A'",
     [(2, 30.0)]),
    ("Stock: intervalos sin stock y SKU en Malasaña",
     "SELECT COUNT(*), COUNT(DISTINCT sku), SUM(horas) FROM disponibilidad WHERE local_id = 'MAD-MAL' "
     "AND unidades_disponibles = 0",
     [(8, 4, 48.0)]),
]


def comprobar(con) -> bool:
    t = Table(title="Las vistas frente a las cifras del 03 (calculadas a mano en la sesión 1)")
    for c in ("Comprobación", "Resultado de la vista", "Esperado", ""):
        t.add_column(c)
    todo_ok = True
    for nombre, sql, esperado in COMPROBACIONES:
        filas = [tuple(round(v, 2) if isinstance(v, float) else v for v in f) for f in con.execute(sql).fetchall()]
        ok = filas == esperado
        todo_ok &= ok
        t.add_row(nombre, str(filas), str(esperado), "[green]✓[/]" if ok else "[red]✗[/]")
    console.print(t)
    return todo_ok


def main() -> None:
    p = argparse.ArgumentParser(description="La capa semántica: lo que ve el modelo en lugar de los CSV.")
    p.add_argument("--comprobar", action="store_true", help="Comprobar las vistas contra las cifras del 03.")
    p.add_argument("--sql", help="Ejecutar NOSOTROS una consulta sobre las vistas (con las barreras).")
    p.add_argument("--prompt", action="store_true", help="Enseñar el system prompt completo que recibe el modelo.")
    a = p.parse_args()
    con = abrir()
    if a.comprobar:
        raise SystemExit(0 if comprobar(con) else 1)
    if a.sql:
        ok, res = ejecutar_sql(con, a.sql)
        console.print(Panel(a.sql, title="SQL escrito por NOSOTROS", border_style="blue"))
        console.print(Panel(res, title="Resultado (DuckDB, sobre las vistas)" if ok else "ERROR",
                            border_style="green" if ok else "red"))
        return
    if a.prompt:
        console.print(construir_system_prompt(con), markup=False)
        return
    ocultas = [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'crudo' ORDER BY 1").fetchall()]
    console.print(Panel("\n".join(f"crudo.{t}" for t in ocultas) +
                        "\n\nLos CSV siguen ahí en `crudo`, pero no se incluyen en el esquema que presentamos al modelo.",
                        title="LO QUE EL MODELO NO VE · los 6 CSV crudos", border_style="red"))
    console.print(Panel(esquema(con), title="LO QUE EL MODELO SÍ VE · las vistas, con sus comentarios "
                        "(esquema generado por el código)", border_style="green"))
    console.print(Panel(GUIA, title="Y una guía: qué tabla para qué pregunta", border_style="white"))


if __name__ == "__main__":
    main()
