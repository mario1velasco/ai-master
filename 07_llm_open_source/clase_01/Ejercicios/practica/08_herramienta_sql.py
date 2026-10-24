"""Nivel 2 · SQL libre: el modelo ESCRIBE la consulta, nuestro código la EJECUTA.

Diferencia con 07 (función fija): allí el cálculo estaba escrito y probado de
antemano; aquí el modelo decide el cálculo entero. Responde a preguntas que
nadie había previsto, pero puede escribir un SQL que se ejecuta sin error y
calcula otra cosa (por ejemplo, contar dos veces una venta al unir tablas).

Qué hace nuestro código:
  1. Carga los 6 CSV en una base DuckDB en memoria (una tabla por archivo).
  2. Genera el ESQUEMA automáticamente: tablas, columnas, tipos y valores
     de ejemplo. Nadie lo escribe a mano.
  3. Añade el contexto (periodos, tiendas) y las REGLAS DE CÁLCULO
     (--sin-reglas quita solo las reglas de cálculo).
  4. Seguridad real, en el código y no solo en el prompt: una sola sentencia,
     solo SELECT, sin acceso a archivos externos y como mucho 50 filas.
  5. Si el SQL falla, el error vuelve al modelo para que lo corrija.

Uso:
  python practica/08_herramienta_sql.py
  python practica/08_herramienta_sql.py --sin-reglas
  python practica/08_herramienta_sql.py --modelo qwen3:8b -q "¿Qué tienda vendió más unidades en B?"
  python practica/08_herramienta_sql.py --solo-esquema
  python practica/08_herramienta_sql.py --sql "SELECT COUNT(*) FROM ventas"   # sin modelo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

metricas = import_module("03_metricas_basicas")
funcion = import_module("07_herramienta_funcion")

MODELO = "qwen3:4b-instruct"
MAX_FILAS = 50
PREGUNTA = "¿Cuáles fueron las ventas netas de Malasaña en el periodo A y en el periodo B?"

console = Console()

CONTEXTO_BASICO = """Contexto:
- Periodo A: fecha entre 2026-03-02 y 2026-03-29. Periodo B: entre 2026-03-30 y 2026-04-26.
- Tiendas: MAD-MAL = Malasaña, MAD-GOY = Goya, BCN-EIX = Eixample."""

REGLAS_CALCULO = """Reglas de cálculo (obligatorias):
- Ventas antes de reembolsos = SUM(ventas.importe_linea) filtrando por ventas.fecha_venta.
- Reembolsos reconocidos = SUM(reembolsos.importe_reembolso) filtrando por
  reembolsos.fecha_reconocimiento (NO por la fecha de la venta). reembolsos no tiene
  local_id: la tienda se obtiene uniendo reembolsos.linea_id con ventas.linea_id.
- Ventas netas = ventas antes de reembolsos - reembolsos reconocidos del mismo periodo.
  Calcula ventas y reembolsos en subconsultas separadas y resta al final: una línea
  puede tener varios reembolsos y un JOIN directo repetiría la venta.
- Pedidos = COUNT(DISTINCT pedido_id). Líneas = COUNT(*). Unidades = SUM(cantidad).
- disponibilidad solo observa 8 SKU de Street One: un SKU sin filas no significa stock cero."""


# ---------------------------------------------------------------------------
# Base de datos y esquema automático
# ---------------------------------------------------------------------------


def abrir_base() -> duckdb.DuckDBPyConnection:
    """DuckDB en memoria con una tabla por CSV y sin acceso a archivos externos."""
    con = duckdb.connect()
    for csv in sorted(metricas.DATA.glob("*.csv")):
        con.execute(f"CREATE TABLE {csv.stem} AS SELECT * FROM read_csv_auto('{csv.as_posix()}')")
    # A partir de aquí ninguna consulta puede leer ni escribir archivos.
    con.execute("SET enable_external_access = false")
    con.execute("SET lock_configuration = true")
    return con


def esquema_automatico(con: duckdb.DuckDBPyConnection, max_valores: int = 6) -> str:
    """Describe todas las tablas leyendo los propios datos: nadie lo escribe a mano."""
    partes = []
    for (tabla,) in con.execute("SELECT table_name FROM information_schema.tables ORDER BY 1").fetchall():
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        lineas = []
        for nombre, tipo, *_ in con.execute(f"DESCRIBE {tabla}").fetchall():
            distintos = con.execute(f'SELECT COUNT(DISTINCT "{nombre}") FROM {tabla}').fetchone()[0]
            if distintos <= max_valores:
                vals = [str(r[0]) for r in con.execute(f'SELECT DISTINCT "{nombre}" FROM {tabla} ORDER BY 1').fetchall()]
                extra = f" valores: {', '.join(vals)}"
            else:
                ej = con.execute(f'SELECT "{nombre}" FROM {tabla} LIMIT 1').fetchone()[0]
                extra = f" ej.: {ej}"
            lineas.append(f"  - {nombre} ({tipo}){extra}")
        partes.append(f"Tabla {tabla} ({n} filas):\n" + "\n".join(lineas))
    return "\n\n".join(partes)


def construir_system_prompt(con: duckdb.DuckDBPyConnection, reglas: bool = True) -> str:
    texto = ("Eres el analista de datos de DropLab. Tienes una base DuckDB de solo lectura.\n"
             "Para obtener cualquier cifra usa la herramienta ejecutar_sql con UNA consulta SELECT.\n"
             "No inventes tablas ni columnas. Si la consulta da error, corrígela.\n"
             "Responde en español, en un máximo de 5 frases, con las cifras del resultado.\n\n"
             + esquema_automatico(con) + "\n\n" + CONTEXTO_BASICO)
    if reglas:
        texto += "\n\n" + REGLAS_CALCULO
    return texto


# ---------------------------------------------------------------------------
# Ejecución segura
# ---------------------------------------------------------------------------


def ejecutar_sql_seguro(con: duckdb.DuckDBPyConnection, consulta: str) -> tuple[bool, str]:
    """Ejecuta el SQL del modelo con las barreras puestas en el código."""
    consulta = (consulta or "").strip().rstrip(";")
    if not consulta:
        return False, "ERROR: la consulta está vacía."
    try:
        sentencias = duckdb.extract_statements(consulta)
    except duckdb.Error as exc:
        return False, f"ERROR de sintaxis: {exc}"
    if len(sentencias) != 1:
        return False, "ERROR: envía exactamente una sentencia."
    if sentencias[0].type != duckdb.StatementType.SELECT:
        return False, f"ERROR: solo se permiten consultas SELECT (recibido: {sentencias[0].type.name})."
    try:
        df = con.execute(consulta).fetchdf()
    except duckdb.Error as exc:
        return False, f"ERROR al ejecutar: {exc}"
    recortado = len(df) > MAX_FILAS
    df = df.head(MAX_FILAS)
    for col in df.select_dtypes("float").columns:   # importes exactos a 2 decimales
        df[col] = df[col].round(2)
    texto = df.to_json(orient="records", force_ascii=False, date_format="iso")
    if recortado:
        texto += f"  (resultado recortado a {MAX_FILAS} filas)"
    return True, texto


TOOLS = [{
    "type": "function",
    "function": {
        "name": "ejecutar_sql",
        "description": "Ejecuta UNA consulta SELECT (dialecto DuckDB) sobre las tablas de DropLab y devuelve el resultado en JSON.",
        "parameters": {
            "type": "object",
            "properties": {"consulta": {"type": "string", "description": "Consulta SELECT en DuckDB."}},
            "required": ["consulta"],
        },
    },
}]


def ejecutar_prueba(modelo: str, pregunta: str, reglas: bool = True, max_rondas: int = 4) -> dict:
    """Lógica pura (sin imprimir): la reutiliza 09_comparativa_modelos.py."""
    con = abrir_base()
    messages = [{"role": "system", "content": construir_system_prompt(con, reglas)},
                {"role": "user", "content": pregunta}]
    res = funcion.conversar_con_herramientas(modelo, messages, TOOLS,
                                             {"ejecutar_sql": lambda consulta="", **_: ejecutar_sql_seguro(con, consulta)},
                                             max_rondas=max_rondas)
    res.update({"pregunta": pregunta, "reglas": reglas,
                "sql": [p["argumentos"].get("consulta") for p in res["traza"]],
                "sql_ok": [p["ok"] for p in res["traza"]]})
    return res


# ---------------------------------------------------------------------------
# Demo en terminal
# ---------------------------------------------------------------------------


def referencia_malasana() -> str:
    r = metricas.resumen_tienda("MAD-MAL")
    return (f"Malasaña · ventas netas A {metricas.eur(r['A']['ventas_netas'])} · B {metricas.eur(r['B']['ventas_netas'])}"
            f" · pedidos {r['A']['pedidos']} / {r['B']['pedidos']}")


def preguntar_con_herramienta(modelo: str, pregunta: str, reglas: bool = True) -> dict:
    console.rule(f"[bold cyan]LO QUE RECIBE EL MODELO al empezar ({modelo} · reglas de cálculo: "
                 f"{'sí' if reglas else 'NO'})")
    system_vista = ("Eres el analista de datos de DropLab. Tienes una base DuckDB de solo lectura.\n"
                    "Para obtener cualquier cifra usa la herramienta ejecutar_sql con UNA consulta SELECT.\n"
                    "No inventes tablas ni columnas. Si la consulta da error, corrígela.\n"
                    "Responde en español, en un máximo de 5 frases, con las cifras del resultado.\n\n"
                    "[ESQUEMA: las 6 tablas con sus columnas, el que enseña --solo-esquema]\n\n"
                    + CONTEXTO_BASICO + ("\n\n" + REGLAS_CALCULO if reglas else
                                         "\n\n(Sin reglas de cálculo: se han quitado con --sin-reglas.)"))
    console.print(Panel(system_vista, title="1 · SYSTEM PROMPT (instrucciones + esquema + periodos"
                        + (" + reglas de cálculo)" if reglas else ")"), border_style="white"))
    console.print(Panel(pregunta, title="2 · MENSAJE (solo la pregunta: ninguna cifra)", border_style="white"))
    console.print(Panel(funcion.describir_herramientas(TOOLS), title="3 · HERRAMIENTAS que puede pedir",
                        border_style="white"))
    r = ejecutar_prueba(modelo, pregunta, reglas)
    if r["error"]:
        console.print(f"[red]{r['error']}[/red]")
        return r
    ronda_actual = None
    for i, paso in enumerate(r["traza"], 1):
        if paso["ronda"] != ronda_actual:
            ronda_actual = paso["ronda"]
            console.rule(f"[bold cyan]RONDA {ronda_actual} · el modelo NO escribe texto: escribe una consulta SQL")
        console.print(Panel(paso["argumentos"].get("consulta") or json.dumps(paso["argumentos"], ensure_ascii=False),
                            title=f"SQL {i} escrito por el MODELO (texto)", border_style="blue"))
        console.print(Panel(paso["resultado"], border_style="green" if paso["ok"] else "red",
                            title="NUESTRO código lo ejecuta en DuckDB y le DEVUELVE este resultado" if paso["ok"]
                            else "FALLÓ: el error vuelve al modelo para que lo corrija"))
    if r["traza"]:
        console.rule(f"[bold cyan]RONDA {r['rondas']} · el modelo recibe todo lo anterior + los resultados "
                     "→ ahora sí escribe")
    if not r["traza"]:
        aviso = ("escribió la llamada como TEXTO en vez de usar tool_calls" if r["llamada_en_texto"]
                 else "respondió sin consultar los datos")
        console.print(f"[yellow]El modelo no usó la herramienta: {aviso}.[/yellow]")
    console.print(Panel(r["respuesta"] or "(sin respuesta)", title="Respuesta final del modelo", border_style="green"))
    console.print(Panel(referencia_malasana(), title="Para comparar: lo que calcula 03_metricas_basicas.py",
                        border_style="magenta"))
    console.print(f"[dim]{len(r['traza'])} consultas · {r['rondas']} rondas · {r['segundos']} s "
                  f"(carga {r['segundos_carga']} s)[/dim]\n")
    return r


def main() -> None:
    p = argparse.ArgumentParser(description="El modelo escribe SQL libre; DuckDB lo ejecuta con barreras.")
    p.add_argument("--modelo", default=MODELO)
    p.add_argument("--question", "-q", default=PREGUNTA)
    p.add_argument("--sin-reglas", action="store_true", help="Quitar las reglas de cálculo del prompt (se mantienen periodos y tiendas).")
    p.add_argument("--solo-esquema", action="store_true", help="Mostrar el esquema automático y salir.")
    p.add_argument("--sql", help="Ejecutar NOSOTROS una consulta (sin modelo), con las mismas barreras. "
                                 "Sirve para comprobar en clase el SQL que escribió el modelo.")
    a = p.parse_args()
    if a.sql:
        con = abrir_base()
        ok, msg = ejecutar_sql_seguro(con, a.sql)
        console.print(Panel(a.sql, title="SQL escrito por NOSOTROS (sin modelo)", border_style="blue"))
        console.print(Panel(msg, title="Resultado (DuckDB)" if ok else "ERROR", border_style="green" if ok else "red"))
        return
    if a.solo_esquema:
        con = abrir_base()
        console.print(Panel(esquema_automatico(con), title="Esquema generado automáticamente", border_style="blue"))
        for prueba in ["DELETE FROM ventas", "SELECT * FROM read_csv_auto('/etc/passwd')", "SELECT 1; SELECT 2"]:
            ok, msg = ejecutar_sql_seguro(con, prueba)
            console.print(f"[{'green' if ok else 'red'}]{prueba}[/] → {msg[:110]}")
        return
    preguntar_con_herramienta(a.modelo, a.question, reglas=not a.sin_reglas)


if __name__ == "__main__":
    main()
