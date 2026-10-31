"""Cálculo determinista de las métricas del caso: ventas, abonos, neto y cesta.

De dónde sale cada dato:
- ventas.csv:     importe_linea, fecha_venta, local_id, pedido_id, cantidad
- reembolsos.csv: importe_reembolso, fecha_reconocimiento, linea_id
                  (NO tiene local_id propio: se hereda desde la venta
                  original cruzando por linea_id)
- disponibilidad.csv + referencias.csv: intervalos sin stock y su producto

Reglas de negocio (data/documentos/diccionario_datos.md):
- Una venta se asigna a un periodo según fecha_venta.
- Un abono se asigna a un periodo según fecha_reconocimiento, NO según la
  fecha de la venta que abona.
- Los abonos se agregan por linea_id ANTES de cruzarlos con ventas, para no
  repetir el doble conteo de HIST-JOIN-001 (2 abonos sobre la misma línea).
- Pedidos = pedido_id distintos. Líneas = filas. Unidades = suma de cantidad.

Detalle técnico: los importes se suman en CÉNTIMOS (números enteros). Sumar
1.441 decimales en coma flotante acumula error (42000.00000000003, o el
50.999,99 € que llegó a escribir un modelo). En céntimos la suma es exacta.

Uso:
    python practica/sesion_1/03_metricas_basicas.py             # informe de la sesión 1
    python practica/sesion_1/03_metricas_basicas.py --reparto   # añade los pedidos según unidades (sesión 2)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def buscar_datos() -> Path:
    """Carpeta de los CSV: DROPLAB_DATOS, data/datos (aula) o DropLab/datos (zip de alumnos), aquí o más arriba."""
    if os.environ.get("DROPLAB_DATOS"):
        return Path(os.environ["DROPLAB_DATOS"])
    for base in [ROOT, *ROOT.parents, Path.cwd()]:
        for candidato in (base / "data" / "datos", base / "DropLab" / "datos"):
            if (candidato / "ventas.csv").exists():
                return candidato
    return ROOT / "data" / "datos"


DATA = buscar_datos()

PERIODO_A = (pd.Timestamp("2026-03-02"), pd.Timestamp("2026-03-29"))
PERIODO_B = (pd.Timestamp("2026-03-30"), pd.Timestamp("2026-04-26"))
NOMBRES = {"MAD-MAL": "Malasaña", "MAD-GOY": "Goya", "BCN-EIX": "Eixample"}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def a_centimos(serie: pd.Series) -> pd.Series:
    return (serie * 100).round().astype("int64")


def a_euros(centimos: int | float) -> float:
    return round(int(centimos) / 100, 2)


def eur(valor: float, signo: bool = False) -> str:
    """Formato español: 40.000,00 €."""
    texto = f"{valor:+,.2f}" if signo else f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def num(valor: float, decimales: int = 2) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def asignar_periodo(fecha: pd.Timestamp) -> str | None:
    if PERIODO_A[0] <= fecha <= PERIODO_A[1]:
        return "A"
    if PERIODO_B[0] <= fecha <= PERIODO_B[1]:
        return "B"
    return None


# ---------------------------------------------------------------------------
# Carga
# ---------------------------------------------------------------------------


def cargar_ventas() -> pd.DataFrame:
    ventas = pd.read_csv(DATA / "ventas.csv")
    ventas["fecha_venta"] = pd.to_datetime(ventas["fecha_venta"])
    ventas["periodo"] = ventas["fecha_venta"].apply(asignar_periodo)
    ventas["importe_cent"] = a_centimos(ventas["importe_linea"])
    return ventas


def cargar_reembolsos_con_local(ventas: pd.DataFrame) -> pd.DataFrame:
    reembolsos = pd.read_csv(DATA / "reembolsos.csv")
    reembolsos["fecha_reconocimiento"] = pd.to_datetime(reembolsos["fecha_reconocimiento"])
    reembolsos["periodo"] = reembolsos["fecha_reconocimiento"].apply(asignar_periodo)
    reembolsos["importe_cent"] = a_centimos(reembolsos["importe_reembolso"])

    # Paso clave: agregar por linea_id ANTES de cruzar con ventas.
    agregado = reembolsos.groupby(["linea_id", "periodo"], as_index=False)["importe_cent"].sum()

    local_por_linea = ventas[["linea_id", "local_id"]].drop_duplicates()
    con_local = agregado.merge(local_por_linea, on="linea_id", how="left")

    sin_local = con_local["local_id"].isna().sum()
    if sin_local:
        print(f"Aviso: {sin_local} abonos sin venta asociada encontrada.")

    con_local["importe_reembolso"] = con_local["importe_cent"] / 100
    return con_local


# ---------------------------------------------------------------------------
# Ventas, abonos y neto
# ---------------------------------------------------------------------------


def ventas_brutas_por_periodo(ventas: pd.DataFrame) -> pd.Series:
    return ventas.groupby("periodo")["importe_cent"].sum().apply(a_euros)


def ventas_brutas_por_periodo_y_tienda(ventas: pd.DataFrame) -> pd.DataFrame:
    tabla = ventas.groupby(["local_id", "periodo"])["importe_cent"].sum().unstack("periodo")
    return tabla.apply(lambda col: col.apply(a_euros))


def reembolsos_por_periodo(reembolsos_con_local: pd.DataFrame) -> pd.Series:
    return reembolsos_con_local.groupby("periodo")["importe_cent"].sum().apply(a_euros)


def reembolsos_por_periodo_y_tienda(reembolsos_con_local: pd.DataFrame) -> pd.DataFrame:
    tabla = reembolsos_con_local.groupby(["local_id", "periodo"])["importe_cent"].sum().unstack("periodo")
    return tabla.apply(lambda col: col.apply(a_euros))


def ventas_netas(brutas, reembolsos):
    """Funciona con Series (por periodo) y con DataFrames (por tienda y periodo)."""
    return brutas.subtract(reembolsos, fill_value=0.0).round(2)


def variacion(neta_a: float, neta_b: float) -> tuple[float, float]:
    absoluta = round(neta_b - neta_a, 2)
    porcentual = (absoluta / neta_a * 100) if neta_a else float("nan")
    return absoluta, porcentual


# ---------------------------------------------------------------------------
# Cesta: pedidos, líneas y unidades
# ---------------------------------------------------------------------------


def cesta_por_tienda(ventas: pd.DataFrame) -> pd.DataFrame:
    """Una fila por tienda y periodo con las métricas de cesta.

    pedidos   = pedido_id distintos         (compras)
    lineas    = filas                       (renglones)
    unidades  = suma de cantidad            (artículos o pares)
    ticket    = ventas antes de abonos / pedidos
    precio realizado = ventas antes de abonos / unidades
    """
    v = ventas[ventas["periodo"].notna()]
    g = v.groupby(["local_id", "periodo"])
    tabla = pd.DataFrame({
        "pedidos": g["pedido_id"].nunique(),
        "lineas": g.size(),
        "unidades": g["cantidad"].sum(),
        "bruto_cent": g["importe_cent"].sum(),
    })
    tabla["unidades_por_pedido"] = tabla["unidades"] / tabla["pedidos"]
    tabla["unidades_por_linea"] = tabla["unidades"] / tabla["lineas"]
    tabla["ticket_bruto"] = tabla["bruto_cent"] / tabla["pedidos"] / 100
    tabla["precio_realizado_unidad"] = tabla["bruto_cent"] / tabla["unidades"] / 100
    return tabla.drop(columns="bruto_cent")


def distribucion_cesta(ventas: pd.DataFrame, local_id: str) -> pd.DataFrame:
    """Cuántos pedidos tienen 1, 2, 3, 4… unidades en cada periodo."""
    v = ventas[(ventas["local_id"] == local_id) & ventas["periodo"].notna()]
    unidades = v.groupby(["periodo", "pedido_id"])["cantidad"].sum().reset_index()
    return unidades.groupby(["cantidad", "periodo"]).size().unstack("periodo", fill_value=0)


def resumen_tienda(local_id: str, ventas: pd.DataFrame | None = None,
                   reembolsos_local: pd.DataFrame | None = None) -> dict:
    """Todo lo que sabemos de una tienda en A y en B, listo para convertir a JSON."""
    ventas = cargar_ventas() if ventas is None else ventas
    reembolsos_local = cargar_reembolsos_con_local(ventas) if reembolsos_local is None else reembolsos_local
    brutas = ventas_brutas_por_periodo_y_tienda(ventas).loc[local_id]
    abonos = reembolsos_por_periodo_y_tienda(reembolsos_local).loc[local_id]
    cesta = cesta_por_tienda(ventas).loc[local_id]
    resumen = {"local_id": local_id, "tienda": NOMBRES.get(local_id, local_id)}
    for p in ("A", "B"):
        neto = round(brutas[p] - abonos[p], 2)
        c = cesta.loc[p]
        resumen[p] = {
            "ventas_antes_reembolsos": float(brutas[p]),
            "reembolsos_reconocidos": float(abonos[p]),
            "ventas_netas": float(neto),
            "proporcion_reembolsada_pct": round(abonos[p] / brutas[p] * 100, 2),
            "pedidos": int(c["pedidos"]),
            "lineas": int(c["lineas"]),
            "unidades": int(c["unidades"]),
            "unidades_por_pedido": round(float(c["unidades_por_pedido"]), 2),
            "ticket_bruto": round(float(c["ticket_bruto"]), 2),
        }
    absoluta, porcentual = variacion(resumen["A"]["ventas_netas"], resumen["B"]["ventas_netas"])
    resumen["variacion_neta"] = {"absoluta_eur": absoluta, "porcentual": round(porcentual, 2)}
    return resumen


# ---------------------------------------------------------------------------
# Disponibilidad
# ---------------------------------------------------------------------------


def cargar_disponibilidad() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga disponibilidad.csv y referencias.csv (para saber qué SKU es qué modelo/talla)."""
    disponibilidad = pd.read_csv(DATA / "disponibilidad.csv")
    referencias = pd.read_csv(DATA / "referencias.csv")
    return disponibilidad, referencias


def _horas_union(intervalos: list[tuple[pd.Timestamp, pd.Timestamp]]) -> float:
    """Duración de la unión de intervalos: las horas de reloj afectadas."""
    total, fin_actual, inicio_actual = 0.0, None, None
    for ini, fin in sorted(intervalos):
        if fin_actual is None or ini > fin_actual:
            if fin_actual is not None:
                total += (fin_actual - inicio_actual).total_seconds()
            inicio_actual, fin_actual = ini, fin
        else:
            fin_actual = max(fin_actual, fin)
    if fin_actual is not None:
        total += (fin_actual - inicio_actual).total_seconds()
    return total / 3600


def resumen_cero_stock(disponibilidad: pd.DataFrame, referencias: pd.DataFrame,
                       local_id: str = "MAD-MAL") -> dict:
    """Resume los intervalos observados con 0 unidades disponibles en una tienda.

    horas_sku_totales: suma de duraciones por variante (4 SKU x 6 h x 2 días = 48).
    horas_reloj:       duración de la unión de intervalos (12 horas de reloj).
    """
    con_catalogo = disponibilidad.merge(referencias[["sku", "modelo", "talla", "color"]], on="sku", how="left")
    cero = con_catalogo[(con_catalogo["unidades_disponibles"] == 0)
                        & (con_catalogo["local_id"] == local_id)].copy()
    resumen = {
        "local_id": local_id,
        "sku_observados": int(disponibilidad["sku"].nunique()),
        "alcance": "solo Street One; el resto del catálogo no se observa",
        "n_intervalos_cero": 0,
        "sku_afectados": 0,
        "horas_sku_totales": 0.0,
        "horas_reloj": 0.0,
        "modelos_afectados": [],
        "tallas_afectadas": [],
        "colores_afectados": [],
        "fechas": [],
    }
    if cero.empty:
        return resumen
    cero["inicio_dt"] = pd.to_datetime(cero["inicio"])
    cero["fin_dt"] = pd.to_datetime(cero["fin"])
    cero["horas"] = (cero["fin_dt"] - cero["inicio_dt"]).dt.total_seconds() / 3600
    resumen.update({
        "n_intervalos_cero": int(len(cero)),
        "sku_afectados": int(cero["sku"].nunique()),
        "horas_sku_totales": float(cero["horas"].sum()),
        "horas_reloj": _horas_union(list(zip(cero["inicio_dt"], cero["fin_dt"]))),
        "modelos_afectados": sorted(cero["modelo"].dropna().unique().tolist()),
        "tallas_afectadas": sorted(cero["talla"].astype(str).unique().tolist()),
        "colores_afectados": sorted(cero["color"].dropna().unique().tolist()),
        "fechas": sorted(cero["inicio_dt"].dt.date.astype(str).unique().tolist()),
    })
    return resumen


# ---------------------------------------------------------------------------
# Informe
# ---------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description="Métricas básicas de DropLab, calculadas con código.")
    p.add_argument("--reparto", action="store_true",
                   help="Mostrar cuántos pedidos de Malasaña tienen 2, 3 o 4 unidades (se usa en la sesión 2).")
    args = p.parse_args()

    ventas = cargar_ventas()
    reembolsos_local = cargar_reembolsos_con_local(ventas)

    brutas = ventas_brutas_por_periodo(ventas)
    abonos = reembolsos_por_periodo(reembolsos_local)
    netas = ventas_netas(brutas, abonos)
    absoluta, porcentual = variacion(netas["A"], netas["B"])

    print("== DropLab · total de la empresa ==")
    print(f"{'':28}{'Periodo A':>16}{'Periodo B':>16}")
    for nombre, serie in [("Ventas antes de reembolsos", brutas), ("Reembolsos reconocidos", abonos),
                          ("Ventas netas", netas)]:
        print(f"{nombre:28}{eur(serie['A']):>16}{eur(serie['B']):>16}")
    print(f"Variación neta A -> B: {eur(absoluta, signo=True)} ({num(porcentual, 3)} %)")

    print("\n== Ventas netas por tienda ==")
    brutas_t = ventas_brutas_por_periodo_y_tienda(ventas)
    abonos_t = reembolsos_por_periodo_y_tienda(reembolsos_local)
    netas_t = ventas_netas(brutas_t, abonos_t)
    for local in netas_t.index:
        a, b = netas_t.loc[local, "A"], netas_t.loc[local, "B"]
        print(f"{NOMBRES[local]:10} {local}: bruto {eur(brutas_t.loc[local, 'A'])} -> {eur(brutas_t.loc[local, 'B'])}"
              f" | abonos {eur(abonos_t.loc[local, 'A'])} -> {eur(abonos_t.loc[local, 'B'])}"
              f" | neto {eur(a)} -> {eur(b)} ({eur(b - a, signo=True)}, {num((b - a) / a * 100, 1)} %)")

    print("\n== Cesta por tienda (pedidos, líneas, unidades) ==")
    cesta = cesta_por_tienda(ventas)
    print(f"{'Tienda':10}{'P':>3}{'Pedidos':>9}{'Líneas':>8}{'Unidades':>10}{'Uds/pedido':>12}{'Ticket':>13}")
    for (local, p), fila in cesta.iterrows():
        print(f"{NOMBRES[local]:10}{p:>3}{int(fila['pedidos']):>9}{int(fila['lineas']):>8}{int(fila['unidades']):>10}"
              f"{num(fila['unidades_por_pedido']):>12}{eur(fila['ticket_bruto']):>13}")

    mal = resumen_tienda("MAD-MAL", ventas, reembolsos_local)
    print("\n== Malasaña en detalle ==")
    for p in ("A", "B"):
        r = mal[p]
        print(f"Periodo {p}: neto {eur(r['ventas_netas'])} | abonos {eur(r['reembolsos_reconocidos'])} "
              f"({num(r['proporcion_reembolsada_pct'])} % de las ventas) | {r['pedidos']} pedidos | "
              f"{num(r['unidades_por_pedido'])} uds/pedido | ticket {eur(r['ticket_bruto'])}")
    if args.reparto:
        print("Pedidos según unidades (A / B):")
        dist = distribucion_cesta(ventas, "MAD-MAL")
        for uds, fila in dist.iterrows():
            print(f"  {uds} unidades: {fila.get('A', 0):>4} / {fila.get('B', 0):<4}")

    disponibilidad, referencias = cargar_disponibilidad()
    stock = resumen_cero_stock(disponibilidad, referencias, "MAD-MAL")
    print("\n== Disponibilidad en Malasaña ==")
    print(f"{stock['n_intervalos_cero']} intervalos sin stock · {num(stock['horas_sku_totales'], 0)} horas-SKU · "
          f"{num(stock['horas_reloj'], 0)} horas de reloj · {', '.join(stock['modelos_afectados'])} "
          f"tallas {', '.join(stock['tallas_afectadas'])} · días {', '.join(stock['fechas'])}")
    print(f"Alcance: {stock['sku_observados']} SKU observados ({stock['alcance']}).")


if __name__ == "__main__":
    main()
