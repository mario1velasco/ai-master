"""Herramienta con función fija: el código está escrito y probado; el modelo
solo decide CUÁNDO llamarla y con QUÉ argumentos.

Paso intermedio entre el Nivel 1 (04: nosotros calculamos todo de antemano) y
el Nivel 2 (08: el modelo escribe el SQL que quiera):

  Paso 0. La función sin modelo: la llamamos nosotros a resumen_comercial() y
     vemos que es una función normal de Python que devuelve JSON.
  Después, con el modelo, la pantalla enseña:
     LO QUE RECIBE EL MODELO: system prompt, pregunta y la DESCRIPCIÓN de la
       herramienta (nunca su código).
     RONDA 1: el modelo responde con una petición (tool_call), no con texto.
       Nuestro código ejecuta la función y le devuelve el JSON.
     RONDA 2: el modelo recibe esos resultados y escribe la respuesta.

La función calcula sobre los CSV para cualquier tienda y rango de fechas; no
contiene respuestas del caso.

Uso:
  python practica/sesion_1/07_herramienta_funcion.py
  python practica/sesion_1/07_herramienta_funcion.py --modelo llama3.2:1b
  python practica/sesion_1/07_herramienta_funcion.py -q "¿Cómo le fue a Eixample en el periodo B?"
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

metricas = import_module("03_metricas_basicas")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen3:4b-instruct"
NUM_CTX = 8192
TIENDAS = ["MAD-MAL", "MAD-GOY", "BCN-EIX"]
PREGUNTA = "¿Cuánto han caído las ventas netas de Malasaña entre el periodo A y el B, y cuántos pedidos hubo en cada uno?"

console = Console()


# ---------------------------------------------------------------------------
# La función fija (código nuestro, probado)
# ---------------------------------------------------------------------------


def resumen_comercial(local_id: str, desde: str, hasta: str) -> tuple[bool, str]:
    """Ventas, abonos, neto y cesta de una tienda entre dos fechas (incluidas).

    - Ventas antes de reembolsos: suma de importe_linea por fecha_venta.
    - Reembolsos reconocidos: por fecha_reconocimiento; la tienda se hereda
      de la venta original (linea_id).
    Devuelve (éxito, JSON en texto).
    """
    if local_id not in TIENDAS:
        return False, json.dumps({"error": f"local_id desconocido: {local_id}. Válidos: {TIENDAS}"})
    try:
        d, h = pd.Timestamp(desde), pd.Timestamp(hasta)
    except (ValueError, TypeError):
        return False, json.dumps({"error": "Fechas no válidas. Formato: YYYY-MM-DD"})
    if d > h:
        return False, json.dumps({"error": "'desde' es posterior a 'hasta'"})

    ventas = metricas.cargar_ventas()
    v = ventas[(ventas["local_id"] == local_id) & ventas["fecha_venta"].between(d, h)]

    abonos = pd.read_csv(metricas.DATA / "reembolsos.csv")
    abonos["fecha_reconocimiento"] = pd.to_datetime(abonos["fecha_reconocimiento"])
    abonos = abonos[abonos["fecha_reconocimiento"].between(d, h)]
    abonos = abonos.merge(ventas[["linea_id", "local_id"]], on="linea_id", how="left")
    abonos = abonos[abonos["local_id"] == local_id]

    bruto = int(v["importe_cent"].sum())
    abonado = int(metricas.a_centimos(abonos["importe_reembolso"]).sum())
    pedidos = int(v["pedido_id"].nunique())
    unidades = int(v["cantidad"].sum())
    return True, json.dumps({
        "local_id": local_id,
        "desde": d.date().isoformat(),
        "hasta": h.date().isoformat(),
        "ventas_antes_reembolsos_eur": bruto / 100,
        "reembolsos_reconocidos_eur": abonado / 100,
        "ventas_netas_eur": (bruto - abonado) / 100,
        "pedidos": pedidos,
        "lineas": int(len(v)),
        "unidades": unidades,
        "unidades_por_pedido": round(unidades / pedidos, 2) if pedidos else None,
        "ticket_medio_eur": round(bruto / pedidos / 100, 2) if pedidos else None,
    }, ensure_ascii=False)


TOOLS = [{
    "type": "function",
    "function": {
        "name": "resumen_comercial",
        "description": ("Devuelve ventas antes de reembolsos, reembolsos reconocidos, ventas netas, pedidos, "
                        "unidades y ticket medio de UNA tienda entre dos fechas incluidas. Llámala una vez "
                        "por periodo si necesitas comparar periodos."),
        "parameters": {
            "type": "object",
            "properties": {
                "local_id": {"type": "string", "enum": TIENDAS,
                             "description": "MAD-MAL = Malasaña, MAD-GOY = Goya, BCN-EIX = Eixample"},
                "desde": {"type": "string", "description": "Fecha inicial, YYYY-MM-DD"},
                "hasta": {"type": "string", "description": "Fecha final incluida, YYYY-MM-DD"},
            },
            "required": ["local_id", "desde", "hasta"],
        },
    },
}]

SYSTEM_PROMPT = """Eres el analista de datos de DropLab.
Periodo A: 2026-03-02 a 2026-03-29. Periodo B: 2026-03-30 a 2026-04-26.
Tiendas: MAD-MAL (Malasaña), MAD-GOY (Goya), BCN-EIX (Eixample).
Para cualquier cifra, usa la herramienta resumen_comercial; no calcules ni
inventes cifras. Si comparas periodos, pide cada periodo por separado.
Responde en español, en un máximo de 5 frases, con las cifras que devuelve
la herramienta."""


# ---------------------------------------------------------------------------
# Bucle de herramientas (lo reutilizan 08 y 09)
# ---------------------------------------------------------------------------


def _parece_llamada_en_texto(texto: str) -> bool:
    t = texto.strip()
    return t.startswith("{") and ('"name"' in t or '"function"' in t or '"parameters"' in t)


def conversar_con_herramientas(modelo: str, messages: list[dict], tools: list[dict], ejecutores: dict,
                               max_rondas: int = 4, num_ctx: int = NUM_CTX, temperatura: float = 0.0,
                               timeout: int = 600) -> dict:   # 10 min: portátiles sin GPU
    """Bucle: el modelo pide herramientas, nosotros las ejecutamos, se repite
    hasta que responde en texto (o se agotan las rondas).

    ejecutores: {"nombre": función(**argumentos) -> (éxito, texto)}
    Devuelve la respuesta final y la traza de todas las llamadas.
    """
    salida = {"modelo": modelo, "respuesta": None, "traza": [], "rondas": 0, "error": None,
              "llamada_en_texto": False, "segundos": 0.0, "segundos_carga": 0.0}
    inicio = time.time()
    for ronda in range(max_rondas + 1):
        payload = {"model": modelo, "messages": messages, "think": False, "stream": False,
                   "options": {"num_ctx": num_ctx, "temperature": temperatura, "num_predict": 700}}
        if ronda < max_rondas:
            payload["tools"] = tools          # en la última ronda le obligamos a responder
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            r.raise_for_status()
        except requests.exceptions.RequestException as exc:
            salida["error"] = f"Error de conexión con Ollama: {exc}"
            break
        cuerpo = r.json()
        salida["segundos_carga"] += cuerpo.get("load_duration", 0) / 1e9
        mensaje = cuerpo["message"]
        llamadas = mensaje.get("tool_calls") or []
        salida["rondas"] = ronda + 1
        if not llamadas:
            texto = (mensaje.get("content") or "").strip()
            salida["respuesta"] = texto
            salida["llamada_en_texto"] = _parece_llamada_en_texto(texto)
            break
        messages.append({"role": "assistant", "content": mensaje.get("content", ""), "tool_calls": llamadas})
        for llamada in llamadas:
            nombre = llamada["function"]["name"]
            args = llamada["function"].get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            if nombre not in ejecutores:
                ok, resultado = False, json.dumps({"error": f"No existe la herramienta {nombre}"})
            else:
                try:
                    ok, resultado = ejecutores[nombre](**args)
                except TypeError as exc:
                    ok, resultado = False, json.dumps({"error": f"Argumentos incorrectos: {exc}"})
            salida["traza"].append({"herramienta": nombre, "argumentos": args, "ok": ok, "resultado": resultado,
                                    "ronda": ronda + 1})
            messages.append({"role": "tool", "content": resultado, "tool_name": nombre})
    salida["segundos"] = round(time.time() - inicio, 1)
    salida["segundos_carga"] = round(salida["segundos_carga"], 1)
    return salida


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def describir_herramientas(tools: list[dict]) -> str:
    """Las herramientas tal como las ve el modelo: nombre, descripción y parámetros (nunca el código)."""
    partes = []
    for t in tools:
        f = t["function"]
        props = f["parameters"]["properties"]
        firma = ", ".join(props)
        lineas = [f"{f['name']}({firma})", f"  Qué hace: {f['description']}"]
        for nombre, info in props.items():
            extra = f" · valores: {', '.join(info['enum'])}" if "enum" in info else ""
            lineas.append(f"  - {nombre}: {info.get('description', '')}{extra}")
        partes.append("\n".join(lineas))
    return "\n\n".join(partes) + "\n\n(Solo la descripción. El código de la función NO se envía al modelo.)"


def demo_explicita() -> None:
    console.rule("[bold cyan]PASO 0 · La función, sin modelo: la llamamos nosotros a mano")
    console.print("[dim]Es Python normal: recibe tienda y fechas, calcula sobre los CSV y devuelve un JSON.[/dim]\n")
    for periodo, (d, h) in {"A": ("2026-03-02", "2026-03-29"), "B": ("2026-03-30", "2026-04-26")}.items():
        _, res = resumen_comercial("MAD-MAL", d, h)
        console.print(Panel(json.dumps(json.loads(res), ensure_ascii=False, indent=2),
                            title=f'resumen_comercial("MAD-MAL", "{d}", "{h}")  ·  periodo {periodo}',
                            border_style="green"))


def demo_modelo(modelo: str, pregunta: str) -> dict:
    console.rule(f"[bold cyan]LO QUE RECIBE EL MODELO al empezar ({modelo})")
    console.print(Panel(SYSTEM_PROMPT, title="1 · SYSTEM PROMPT (instrucciones fijas)", border_style="white"))
    console.print(Panel(pregunta, title="2 · MENSAJE (solo la pregunta: ninguna cifra)", border_style="white"))
    console.print(Panel(describir_herramientas(TOOLS), title="3 · HERRAMIENTAS que puede pedir", border_style="white"))

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": pregunta}]
    res = conversar_con_herramientas(modelo, messages, TOOLS, {"resumen_comercial": resumen_comercial})
    if res["error"]:
        console.print(f"[red]{res['error']}[/red]")
        return res
    ronda_actual = None
    for paso in res["traza"]:
        if paso["ronda"] != ronda_actual:
            ronda_actual = paso["ronda"]
            console.rule(f"[bold cyan]RONDA {ronda_actual} · el modelo NO escribe texto: pide la herramienta")
        args = paso["argumentos"]
        llamada = f"{paso['herramienta']}(" + ", ".join(f'{k}="{v}"' for k, v in args.items()) + ")"
        console.print(Panel(json.dumps(args, ensure_ascii=False),
                            title=f"El MODELO pide: {llamada}", border_style="blue"))
        console.print(Panel(paso["resultado"], title="NUESTRO código la ejecuta y le DEVUELVE este JSON",
                            border_style="green" if paso["ok"] else "red"))
    if res["traza"]:
        console.rule(f"[bold cyan]RONDA {res['rondas']} · el modelo recibe todo lo anterior + los resultados "
                     "→ ahora sí escribe")
    if not res["traza"]:
        aviso = (" — escribió la llamada como TEXTO, en vez de usar tool_calls" if res["llamada_en_texto"]
                 else " — respondió sin pedir la herramienta")
        console.print(f"[yellow]El modelo no usó la herramienta{aviso}.[/yellow]")
    console.print(Panel(res["respuesta"] or "(sin respuesta)", title="Respuesta final del modelo",
                        border_style="green"))
    console.print(f"[dim]{res['rondas']} rondas · {res['segundos']} s (carga {res['segundos_carga']} s)[/dim]")
    return res


def main() -> None:
    p = argparse.ArgumentParser(description="Herramienta con función fija: resumen_comercial().")
    p.add_argument("--modelo", default=MODELO)
    p.add_argument("--question", "-q", default=PREGUNTA)
    p.add_argument("--solo-explicita", action="store_true", help="No llamar al modelo.")
    a = p.parse_args()
    demo_explicita()
    if not a.solo_explicita:
        demo_modelo(a.modelo, a.question)


if __name__ == "__main__":
    main()
