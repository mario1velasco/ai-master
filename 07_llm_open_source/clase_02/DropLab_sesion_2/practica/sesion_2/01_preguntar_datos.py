"""Preguntar cualquier cosa sobre los datos, con garantías.

Es el SQL libre de la sesión 1 (practica/sesion_1/08_herramienta_sql.py), con los
tres cambios que salieron del experimento (docs/sesion_2/00):

  1. CAPA SEMÁNTICA: al modelo le presentamos vistas que ya llevan dentro el
     conocimiento del negocio (02_capa_semantica.py), no el esquema de los CSV crudos.
     Ya no tiene que saber qué
     fecha manda ni cómo se resta un abono: solo traducir la pregunta.
  2. UN MODELO CAPAZ Y RÁPIDO: qwen3:30b-a3b-instruct, un modelo «de expertos»
     (30.000 millones de parámetros, unos 3.000 millones activos por palabra).
  3. UN VERIFICADOR EN EL CÓDIGO: si la respuesta trae cifras que no salen de
     ningún resultado de SQL, se la devuelve al modelo para que la corrija.

Lo que no cambia: el modelo ESCRIBE el SQL; nuestro código lo EJECUTA con las
mismas barreras (solo SELECT, una sentencia, sin archivos, 50 filas).

Uso:
  python practica/sesion_2/01_preguntar_datos.py --modo clase     # tablas crudas, como el 08
  python practica/sesion_2/01_preguntar_datos.py                  # capa semántica
  python practica/sesion_2/01_preguntar_datos.py -q "¿Qué ventas se hicieron en las tres tiendas el 25 de abril?"
  python practica/sesion_2/01_preguntar_datos.py --modelo qwen3:4b-instruct
  python practica/sesion_2/01_preguntar_datos.py --sin-verificar
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from importlib import import_module
from pathlib import Path

import requests
from rich.console import Console
from rich.panel import Panel

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "sesion_1"))
capa = import_module("02_capa_semantica")
sql08 = import_module("08_herramienta_sql")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen3:30b-a3b-instruct-2507-q4_K_M"
NUM_CTX = 12288          # el esquema de las vistas y las rondas ocupan unos 3.300 tokens
PREGUNTA = "¿Cuáles fueron las ventas netas de Malasaña en el periodo A y en el periodo B?"
TOOLS = sql08.TOOLS      # la misma herramienta que en la sesión 1: ejecutar_sql(consulta)

console = Console()


# ---------------------------------------------------------------------------
# Lo que recibe el modelo, según el modo
# ---------------------------------------------------------------------------


def preparar(modo: str):
    """Devuelve (conexión, system prompt). capa = vistas · clase = tablas crudas + reglas (el 08)."""
    if modo == "capa":
        con = capa.abrir()
        return con, capa.construir_system_prompt(con)
    con = sql08.abrir_base()
    return con, sql08.construir_system_prompt(con, reglas=True)


# ---------------------------------------------------------------------------
# El verificador: ¿cada cifra de la respuesta sale de algún resultado?
# ---------------------------------------------------------------------------

_NUM = re.compile(r"-?\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:[.,]\d+)?")


def normalizar(texto: str) -> str:
    """Espacios y guiones Unicode (algunos modelos escriben 40 000 o MAD‑GOY) a los normales."""
    for raro, simple in {"\u202f": " ", "\xa0": " ", "\u2009": " ", "\u2011": "-", "\u2010": "-", "\u2013": "-",
                         "\u2212": "-", "*": ""}.items():
        texto = texto.replace(raro, simple)
    return texto


def numeros(texto: str) -> list[float]:
    """Todas las cifras de un texto, entiendan el formato español (40.000,00) o el inglés (40,000.00)."""
    vals = []
    for m in _NUM.finditer(normalizar(texto)):
        t = m.group(0).replace(" ", "")
        if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", t):
            t = t.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t):
            t = t.replace(",", "")
        else:
            t = t.replace(",", ".")
        try:
            vals.append(abs(float(t)))
        except ValueError:
            pass
    return vals


def cifras_sin_respaldo(respuesta: str, fuentes: list[str]) -> list[float]:
    """Cifras de la respuesta que no aparecen en ningún resultado de SQL (ni en la pregunta ni en los periodos)."""
    permitidos = [n for t in fuentes for n in numeros(t)]
    return sorted({n for n in numeros(respuesta) if not any(abs(n - p) <= 0.011 for p in permitidos)})


# ---------------------------------------------------------------------------
# El bucle de herramientas, con verificación
# ---------------------------------------------------------------------------


def conversar(modelo: str, sistema: str, pregunta: str, con, verificar: bool = True, max_rondas: int = 6,
              num_ctx: int = NUM_CTX) -> dict:
    """Como el bucle del 07 (el modelo pide, nuestro código ejecuta), más la revisión de cifras.

    Devuelve la respuesta final, la traza (SQL y resultados), la verificación y los tiempos.
    """
    messages = [{"role": "system", "content": sistema}, {"role": "user", "content": pregunta}]
    out = {"modelo": modelo, "respuesta": None, "traza": [], "verificacion": [], "aviso": None, "error": None,
           "rondas": 0, "segundos": 0.0, "segundos_carga": 0.0, "tokens_entrada": 0}
    fuentes = [pregunta, capa.PERIODOS]
    t0 = time.time()
    ronda, limite, revisado = 0, max_rondas, False
    while ronda <= limite:
        payload = {"model": modelo, "messages": messages, "stream": False, "think": False,
                   "options": {"num_ctx": num_ctx, "temperature": 0, "num_predict": 1024}}
        if ronda < limite:
            payload["tools"] = TOOLS              # en la última ronda le obligamos a responder
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=900)
            r.raise_for_status()
        except requests.exceptions.RequestException as exc:
            out["error"] = f"Error con Ollama: {exc}. ¿Está en marcha y descargado {modelo}?"
            break
        c = r.json()
        out["segundos_carga"] += c.get("load_duration", 0) / 1e9
        out["tokens_entrada"] = max(out["tokens_entrada"], c.get("prompt_eval_count", 0) or 0)
        m = c["message"]
        llamadas = m.get("tool_calls") or []
        ronda += 1
        out["rondas"] = ronda
        if not llamadas:
            texto = (m.get("content") or "").strip()
            out["respuesta"] = texto
            if verificar and out["traza"]:
                dudosas = cifras_sin_respaldo(texto, fuentes)
                out["verificacion"].append({"ronda": ronda, "respuesta": texto, "cifras_sin_respaldo": dudosas})
                if dudosas and revisado:          # segundo intento y siguen: no se esconde, se avisa
                    out["aviso"] = "Cifras sin respaldo en los resultados: " + ", ".join(f"{d:g}" for d in dudosas)
                if dudosas and not revisado:      # primer intento: se lo devolvemos al modelo
                    revisado = True
                    lista = ", ".join(f"{d:g}" for d in dudosas)
                    messages.append({"role": "assistant", "content": texto})
                    messages.append({"role": "user", "content": (
                        f"Revisión automática del código: estas cifras de tu respuesta no aparecen en los resultados "
                        f"de tus consultas: {lista}. Si son un cálculo (resta, porcentaje, cociente), hazlo dentro "
                        f"de una consulta SQL. Después reescribe la respuesta usando solo cifras que aparezcan tal "
                        f"cual en los resultados.")})
                    limite = ronda + 3
                    continue
            break
        messages.append({"role": "assistant", "content": m.get("content", ""), "tool_calls": llamadas})
        for ll in llamadas:
            args = ll["function"].get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            consulta = args.get("consulta") or args.get("query") or args.get("sql") or ""
            ok, res = sql08.ejecutar_sql_seguro(con, consulta)
            fuentes.append(res)
            out["traza"].append({"ronda": ronda, "sql": consulta, "ok": ok, "resultado": res})
            messages.append({"role": "tool", "content": res, "tool_name": "ejecutar_sql"})
    out["segundos"] = round(time.time() - t0, 1)
    out["segundos_carga"] = round(out["segundos_carga"], 1)
    return out


# ---------------------------------------------------------------------------
# Demo en terminal
# ---------------------------------------------------------------------------


def sql_legible(consulta: str) -> str:
    """Un salto de línea antes de cada cláusula, para leerlo en clase."""
    texto = " ".join((consulta or "").split())
    for clave in ("FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "JOIN", "UNION"):
        texto = re.sub(rf"\s+({clave})\b", r"\n\1", texto)
    return texto


def main() -> None:
    p = argparse.ArgumentParser(description="Preguntar cualquier cosa sobre los datos: capa semántica + verificador.")
    p.add_argument("--question", "-q", default=PREGUNTA)
    p.add_argument("--modelo", default=MODELO)
    p.add_argument("--modo", choices=["capa", "clase"], default="capa",
                   help="capa = vistas (por defecto) · clase = tablas crudas + reglas, como el 08 de la sesión 1")
    p.add_argument("--sin-verificar", action="store_true", help="Quitar la revisión de cifras del código.")
    a = p.parse_args()

    con, sistema = preparar(a.modo)
    if a.modo == "capa":
        resumen = ("Instrucciones (usa ejecutar_sql, haz las cuentas en SQL, si un dato no existe dilo)\n\n"
                    "[ESQUEMA DE LAS VISTAS, con sus comentarios: el que enseña 02_capa_semantica.py]\n\n"
                   + capa.PERIODOS + "\n\n[GUÍA: qué tabla para qué pregunta + lo que NO existe]")
        titulo = "1 · SYSTEM PROMPT (vistas preparadas, no CSV)"
    else:
        resumen = ("Instrucciones\n\n[ESQUEMA DE LAS 6 TABLAS CRUDAS]\n\n" + sql08.CONTEXTO_BASICO
                   + "\n\n" + sql08.REGLAS_CALCULO)
        titulo = "1 · SYSTEM PROMPT (tablas crudas + reglas: el 08 de la sesión 1)"
    console.rule(f"[bold cyan]LO QUE RECIBE EL MODELO ({a.modelo} · modo {a.modo})")
    console.print(Panel(resumen, title=titulo, border_style="white"))
    console.print(Panel(a.question, title="2 · MENSAJE (solo la pregunta: ninguna cifra)", border_style="white"))

    # En modo clase se reproduce el 08 tal cual: 4 rondas y sin verificador.
    verificar = a.modo == "capa" and not a.sin_verificar
    r = conversar(a.modelo, sistema, a.question, con, verificar=verificar, max_rondas=6 if a.modo == "capa" else 4)
    if r["error"]:
        console.print(f"[red]{r['error']}[/red]")
        return
    ronda = None
    for i, paso in enumerate(r["traza"], 1):
        if paso["ronda"] != ronda:
            ronda = paso["ronda"]
            console.rule(f"[bold cyan]RONDA {ronda} · el modelo escribe SQL; nuestro código lo ejecuta")
        console.print(Panel(sql_legible(paso["sql"]) or "(vacío)", title=f"SQL {i} escrito por el MODELO",
                            border_style="blue"))
        console.print(Panel(paso["resultado"], border_style="green" if paso["ok"] else "red",
                            title="Resultado (DuckDB)" if paso["ok"] else "FALLÓ: el error vuelve al modelo"))
    if not r["traza"]:
        console.print("[yellow]El modelo respondió sin consultar los datos.[/yellow]")

    if verificar and r["verificacion"]:
        console.rule("[bold cyan]REVISIÓN DEL CÓDIGO · ¿cada cifra sale de un resultado de SQL?")
        for v in r["verificacion"]:
            if v["cifras_sin_respaldo"]:
                console.print(Panel(v["respuesta"], title="Borrador con cifras SIN respaldo: "
                                    + ", ".join(f"{d:g}" for d in v["cifras_sin_respaldo"])
                                    + " → se lo devolvemos al modelo", border_style="yellow"))
            else:
                console.print("[green]✓ Todas las cifras de la respuesta salen de los resultados de SQL.[/green] "
                              "[dim](Que existan no garantiza que signifiquen lo que se pregunta: lee el SQL.)[/dim]")
    console.print(Panel(r["respuesta"] or "(sin respuesta)", title="Respuesta final del modelo", border_style="green"))
    if r["aviso"]:
        console.print(f"[bold red]AVISO: {r['aviso']}[/bold red]")
    console.print(f"[dim]{len(r['traza'])} consultas · {r['rondas']} rondas · {r['segundos']} s "
                  f"(carga del modelo {r['segundos_carga']} s) · {r['tokens_entrada']} tokens de entrada[/dim]")


if __name__ == "__main__":
    main()
