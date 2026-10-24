"""Auditoría rápida de integridad y relaciones en data/.

Objetivo: cerrar la fase de "conocer los datos" con un único script, sin
calcular todavía ninguna métrica de negocio (eso es la siguiente etapa).

Preguntas que responde:
1. ¿Las claves principales son únicas?
2. ¿Todas las referencias entre tablas apuntan a algo que existe?
   (reembolsos -> ventas, ventas -> referencias, ventas/calendario/
   disponibilidad -> locales)
3. ¿El calendario cubre todos los días esperados para los tres locales?
4. ¿Qué pasa si unimos ventas y reembolsos directamente por linea_id?
   (demostración de la trampa de doble conteo)

Periodos de negocio (dados por el brief, no inventados por este script):
  A: 2026-03-02 a 2026-03-29
  B: 2026-03-30 a 2026-04-26
"""

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

PERIODO_A = ("2026-03-02", "2026-03-29")
PERIODO_B = ("2026-03-30", "2026-04-26")


def cargar() -> dict[str, pd.DataFrame]:
    nombres = [
        "ventas",
        "reembolsos",
        "referencias",
        "locales",
        "calendario",
        "disponibilidad",
    ]
    return {nombre: pd.read_csv(DATA / f"{nombre}.csv") for nombre in nombres}


def check(descripcion: str, ok: bool, detalle: str = "") -> None:
    estado = "OK" if ok else "FALLO"
    linea = f"[{estado}] {descripcion}"
    if detalle:
        linea += f" — {detalle}"
    print(linea)


def auditar_claves(t: dict[str, pd.DataFrame]) -> None:
    print("\n== 1. Claves únicas ==")
    check(
        "ventas.linea_id es única",
        t["ventas"]["linea_id"].is_unique,
    )
    check(
        "reembolsos.reembolso_id es única",
        t["reembolsos"]["reembolso_id"].is_unique,
    )
    check(
        "referencias.sku es única",
        t["referencias"]["sku"].is_unique,
    )
    check(
        "locales.local_id es única",
        t["locales"]["local_id"].is_unique,
    )


def auditar_referencias(t: dict[str, pd.DataFrame]) -> None:
    print("\n== 2. Integridad referencial ==")

    huerfanos_reembolsos = set(t["reembolsos"]["linea_id"]) - set(t["ventas"]["linea_id"])
    check(
        "Todo reembolso apunta a una venta existente",
        len(huerfanos_reembolsos) == 0,
        f"huérfanos: {sorted(huerfanos_reembolsos)}" if huerfanos_reembolsos else "",
    )

    sku_sin_catalogo = set(t["ventas"]["sku"]) - set(t["referencias"]["sku"])
    check(
        "Todo sku vendido existe en referencias",
        len(sku_sin_catalogo) == 0,
        f"sin catálogo: {sorted(sku_sin_catalogo)}" if sku_sin_catalogo else "",
    )

    locales_validos = set(t["locales"]["local_id"])
    for nombre in ["ventas", "calendario", "disponibilidad"]:
        locales_tabla = set(t[nombre]["local_id"])
        desconocidos = locales_tabla - locales_validos
        check(
            f"{nombre}.local_id solo usa locales conocidos",
            len(desconocidos) == 0,
            f"desconocidos: {sorted(desconocidos)}" if desconocidos else "",
        )


def auditar_cobertura_calendario(t: dict[str, pd.DataFrame]) -> None:
    print("\n== 3. Cobertura del calendario ==")

    calendario = t["calendario"].copy()
    calendario["fecha"] = pd.to_datetime(calendario["fecha"])

    rango_completo = pd.date_range(PERIODO_A[0], PERIODO_B[1], freq="D")
    locales = sorted(t["locales"]["local_id"])

    for local in locales:
        fechas_local = set(
            calendario.loc[calendario["local_id"] == local, "fecha"]
        )
        faltantes = [f for f in rango_completo if f not in fechas_local]
        check(
            f"{local} tiene un registro de calendario por cada día (A+B)",
            len(faltantes) == 0,
            f"faltan {len(faltantes)} días" if faltantes else "",
        )

    incompletos = calendario.loc[~calendario["cobertura_completa"]]
    check(
        "Todos los días tienen cobertura_completa = True",
        incompletos.empty,
        f"{len(incompletos)} días con cobertura incompleta" if not incompletos.empty else "",
    )


def demostrar_trampa_join(t: dict[str, pd.DataFrame]) -> None:
    print("\n== 4. Trampa del doble conteo (ventas + reembolsos) ==")

    venta = t["ventas"].loc[t["ventas"]["linea_id"] == "HIST-JOIN-001"]
    reembolsos_linea = t["reembolsos"].loc[
        t["reembolsos"]["linea_id"] == "HIST-JOIN-001"
    ]

    importe_venta = venta["importe_linea"].sum()
    importe_reembolsos = reembolsos_linea["importe_reembolso"].sum()

    print(f"Venta original (HIST-JOIN-001): {importe_venta:.2f} €")
    print(f"Número de reembolsos asociados: {len(reembolsos_linea)}")
    print(f"Importe reembolsado total:      {importe_reembolsos:.2f} €")

    join_directo = venta.merge(reembolsos_linea, on="linea_id", how="left")
    suma_incorrecta = join_directo["importe_linea"].sum()

    print(
        f"\nSi hacemos un JOIN directo ventas-reembolsos por linea_id, "
        f"la venta aparece {len(join_directo)} veces."
    )
    print(
        f"Sumar 'importe_linea' tras ese JOIN da {suma_incorrecta:.2f} € "
        f"en vez de {importe_venta:.2f} € — doble conteo."
    )
    print(
        "Solución correcta: agregar reembolsos por linea_id ANTES de unir, "
        "o calcular venta y reembolsos por separado y restar al final."
    )


def main() -> None:
    tablas = cargar()
    auditar_claves(tablas)
    auditar_referencias(tablas)
    auditar_cobertura_calendario(tablas)
    demostrar_trampa_join(tablas)
    print("\nAuditoría completada.")


if __name__ == "__main__":
    main()
