"""Las cifras: consultas de SOLO LECTURA sobre la capa semántica de la sesión 2.

Dos formas, como en las sesiones 1 y 2:

1. Consultas fijas con parámetros (función fija): el SQL lo escribimos nosotros y solo cambia el valor
   de un parámetro, que antes se valida (un pedido con su formato, una tienda de la lista…).
   Es lo que usa el flujo para comprobar un ticket o dar las cifras clave de una tienda.

       pedido(pedido_id)                    las líneas y los abonos de un pedido
       resumen_tienda(local_id)             ventas, abonos, netas, pedidos, unidades y pedidos de 4+ por periodo
       disponibilidad_en(local_id, instante, skus)   el stock registrado en un momento
       roturas_dia(local_id, fecha)         los intervalos sin stock de un día

2. SQL escrito por el modelo (01_preguntar_datos.py de la sesión 2), para las preguntas que no caben
   en una consulta fija: solo SELECT, una sentencia, sin acceso a archivos, 50 filas y verificador de cifras.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import date, datetime

from . import config
from .ollama import ErrorComponente
from .sesion2 import capa, preguntar_datos

TIENDAS = {"MAD-MAL": "Malasaña", "MAD-GOY": "Goya", "BCN-EIX": "Eixample"}
PEDIDO_RE = re.compile(r"^(?:[AB]-(?:MAD-MAL|MAD-GOY|BCN-EIX)-ORD-\d{4}|HIST-ORDER-\d{3})$")
SKU_RE = re.compile(r"^[A-Z]+(?:_[A-Z]+)*_\d{2}$|^[A-Z]+(?:_[A-Z]+)*_(?:S|M|L|XL)$")

_con = None
_lock = threading.Lock()


def conexion():
    """Una base DuckDB en memoria con las vistas de la sesión 2 (los CSV, ocultos). Se crea una vez."""
    global _con
    with _lock:
        if _con is None:
            _con = capa.abrir()
    return _con


def _ejecutar(herramienta: str, titulo: str, sql: str, parametros: list) -> dict:
    """Ejecuta una consulta NUESTRA con sus parámetros. Devuelve también el SQL: se enseña siempre."""
    try:
        cur = conexion().cursor()              # un cursor por llamada: seguro con varias peticiones a la vez
        df = cur.execute(sql, parametros).fetchdf()
    except Exception as exc:                   # noqa: BLE001 - se informa del error con su nombre
        raise ErrorComponente("SQL_ERROR", "duckdb", f"{herramienta}: {exc}")
    for col in df.select_dtypes("float").columns:
        df[col] = df[col].round(2)
    filas = json.loads(df.to_json(orient="records", force_ascii=False, date_format="iso"))
    return {"herramienta": herramienta, "titulo": titulo, "sql": " ".join(sql.split()), "parametros": parametros,
            "filas": filas}


def tienda_valida(local_id: str) -> str:
    if local_id not in TIENDAS:
        raise ErrorComponente("PARAMETRO_NO_VALIDO", "datos", f"Tienda desconocida: {local_id!r}. Válidas: {', '.join(TIENDAS)}")
    return local_id


# ---------------------------------------------------------------------------
# 1. Consultas fijas con parámetros
# ---------------------------------------------------------------------------


def pedido(pedido_id: str) -> dict:
    """Las líneas de un pedido (tal como las registró caja) y los abonos posteriores de esas líneas."""
    pedido_id = (pedido_id or "").strip().upper()
    if not PEDIDO_RE.fullmatch(pedido_id):
        raise ErrorComponente("PARAMETRO_NO_VALIDO", "datos", f"Formato de pedido no válido: {pedido_id!r}")
    lineas = _ejecutar("pedido", f"Líneas del pedido {pedido_id} en caja", """
        SELECT linea_id, strftime(fecha_venta, '%Y-%m-%d') AS fecha_venta, periodo, local_id, tienda, sku, cantidad, precio_unitario,
               descuento_linea, importe_antes_reembolsos AS importe
        FROM ventas_lineas WHERE pedido_id = ? ORDER BY linea_id""", [pedido_id])
    abonos = _ejecutar("abonos_pedido", f"Abonos de las líneas del pedido {pedido_id}", """
        SELECT reembolso_id, linea_id, strftime(fecha_reconocimiento, '%Y-%m-%d') AS fecha_reconocimiento, periodo, unidades_devueltas, importe_abonado, motivo
        FROM abonos WHERE pedido_id = ? ORDER BY fecha_reconocimiento, linea_id""", [pedido_id])
    total = round(sum(f["importe"] for f in lineas["filas"]), 2)
    return {**lineas, "total": total, "abonos": abonos}


def resumen_tienda(local_id: str = "MAD-MAL") -> dict:
    """Las cifras clave de una tienda en los periodos A y B (las mismas del script 03 de la sesión 1)."""
    tienda_valida(local_id)
    return _ejecutar("resumen_tienda", f"Cifras clave de {TIENDAS[local_id]} por periodo", """
        WITH r AS (
            SELECT periodo, SUM(ventas_antes_reembolsos) AS ventas_antes_reembolsos,
                   SUM(abonos_reconocidos) AS abonos, SUM(ventas_netas) AS ventas_netas,
                   CAST(SUM(pedidos) AS INTEGER) AS pedidos, CAST(SUM(unidades) AS INTEGER) AS unidades
            FROM resumen_diario WHERE local_id = ? AND periodo IS NOT NULL GROUP BY periodo),
        p AS (
            SELECT periodo, COUNT(*) FILTER (WHERE unidades >= 4) AS pedidos_4_o_mas_unidades
            FROM pedidos WHERE local_id = ? AND periodo IS NOT NULL GROUP BY periodo)
        , t AS (
            SELECT r.periodo, r.ventas_antes_reembolsos, r.abonos, r.ventas_netas, r.pedidos, r.unidades,
                   ROUND(r.unidades / r.pedidos, 2) AS unidades_por_pedido, p.pedidos_4_o_mas_unidades
            FROM r JOIN p USING (periodo))
        SELECT * FROM t
        UNION ALL      -- la diferencia la calcula el SQL, no el modelo
        SELECT 'B - A', b.ventas_antes_reembolsos - a.ventas_antes_reembolsos, b.abonos - a.abonos,
               b.ventas_netas - a.ventas_netas, b.pedidos - a.pedidos, b.unidades - a.unidades,
               ROUND(b.unidades_por_pedido - a.unidades_por_pedido, 2),
               b.pedidos_4_o_mas_unidades - a.pedidos_4_o_mas_unidades
        FROM t a, t b WHERE a.periodo = 'A' AND b.periodo = 'B'
        ORDER BY 1""", [local_id, local_id])


def disponibilidad_en(local_id: str, instante: str, skus: list[str] | None = None) -> dict:
    """El stock registrado en un instante (hora local de Madrid). Un intervalo incluye su inicio y excluye su fin."""
    tienda_valida(local_id)
    try:
        momento = datetime.fromisoformat(instante)
    except ValueError:
        raise ErrorComponente("PARAMETRO_NO_VALIDO", "datos", f"Instante no válido: {instante!r} (AAAA-MM-DD HH:MM)")
    skus = [s for s in (skus or []) if s]
    if any(not SKU_RE.fullmatch(s) for s in skus):
        raise ErrorComponente("PARAMETRO_NO_VALIDO", "datos", f"SKU con formato no válido en {skus}")
    filtro = f" AND sku IN ({', '.join('?' for _ in skus)})" if skus else ""
    return _ejecutar("disponibilidad_en", f"Stock registrado en {TIENDAS[local_id]} el {momento:%d/%m/%Y %H:%M}", f"""
        SELECT sku, strftime(timezone('Europe/Madrid', inicio), '%Y-%m-%d %H:%M') AS desde,
               strftime(timezone('Europe/Madrid', fin), '%Y-%m-%d %H:%M') AS hasta, unidades_disponibles
        FROM disponibilidad
        WHERE local_id = ? AND inicio <= timezone('Europe/Madrid', CAST(? AS TIMESTAMP))
          AND timezone('Europe/Madrid', CAST(? AS TIMESTAMP)) < fin{filtro}
        ORDER BY sku""", [local_id, momento.isoformat(" "), momento.isoformat(" "), *skus])


def roturas_dia(local_id: str, dia: str) -> dict:
    """Los intervalos con 0 unidades de un día (Street One es lo único que se observa)."""
    tienda_valida(local_id)
    try:
        d = date.fromisoformat(dia)
    except ValueError:
        raise ErrorComponente("PARAMETRO_NO_VALIDO", "datos", f"Fecha no válida: {dia!r} (AAAA-MM-DD)")
    return _ejecutar("roturas_dia", f"Intervalos sin stock en {TIENDAS[local_id]} el {d:%d/%m/%Y}", """
        SELECT sku, strftime(timezone('Europe/Madrid', inicio), '%H:%M') AS desde,
               strftime(timezone('Europe/Madrid', fin), '%H:%M') AS hasta, horas
        FROM disponibilidad WHERE local_id = ? AND unidades_disponibles = 0
          AND CAST(timezone('Europe/Madrid', inicio) AS DATE) = ? ORDER BY sku, inicio""", [local_id, d.isoformat()])


# ---------------------------------------------------------------------------
# 2. SQL escrito por el modelo (sesión 2), con barreras y verificador
# ---------------------------------------------------------------------------


def preguntar(pregunta: str, modelo: str | None = None) -> dict:
    """La pregunta en lenguaje natural → el modelo escribe SQL sobre las vistas → el código lo ejecuta y revisa."""
    con = conexion()
    sistema = capa.construir_system_prompt(con)
    r = preguntar_datos.conversar(modelo or config.MODELO_TEXTO, sistema, pregunta, con.cursor())
    if r.get("error"):
        raise ErrorComponente("OLLAMA_NO_DISPONIBLE", "ollama", r["error"])
    return {"herramienta": "sql_del_modelo", "titulo": "SQL escrito por el modelo (capa semántica)",
            "respuesta": r["respuesta"], "consultas": [{"sql": " ".join((p["sql"] or "").split()), "ok": p["ok"],
                                                         "resultado": p["resultado"]} for p in r["traza"]],
            "aviso": r.get("aviso"), "segundos": r["segundos"]}
