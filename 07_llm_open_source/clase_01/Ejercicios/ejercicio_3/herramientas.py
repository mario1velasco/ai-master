"""DropLab · Sesión 1 · Ejercicio 3 · Tu propia herramienta para el modelo.

Este archivo ya trae casi todo hecho. Tú completas dos cosas (busca «TODO»):

  TODO 1 · la función cesta(): cómo son las compras de una tienda entre dos fechas.
  TODO 2 · su descripción en TOOLS, para que el modelo sepa que existe y cuándo usarla.

Órdenes (desde la carpeta de este archivo):

  python herramientas.py probar                                    # ¿están bien tus funciones? (sin modelo)
  python herramientas.py calcular cesta MAD-MAL 2026-03-02 2026-03-29   # ejecutas tú una herramienta
  python herramientas.py preguntar "¿Cuántos pedidos hizo Goya en el periodo B?"
  python herramientas.py bateria                                   # las 6 preguntas del ejercicio
  python herramientas.py bateria --descripciones-pobres            # experimento 1
  python herramientas.py bateria --sin-contexto                    # experimento 2
  python herramientas.py bateria --modelo llama3.2:3b              # experimento 3

Solo necesita Python 3.9+ (sin librerías) y, para preguntar al modelo, Ollama.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen3:4b-instruct"
TIENDAS = {"MAD-MAL": "Malasaña", "MAD-GOY": "Goya", "BCN-EIX": "Eixample"}


# ===========================================================================
# 1. Datos (ya hecho: no hace falta tocarlo)
# ===========================================================================


def buscar_datos() -> Path:
    """Busca la carpeta con los CSV: DropLab/datos junto a este archivo o más arriba."""
    candidatos = []
    if os.environ.get("DROPLAB_DATOS"):
        candidatos.append(Path(os.environ["DROPLAB_DATOS"]))
    for base in [Path.cwd(), *Path(__file__).resolve().parents]:
        candidatos += [base / "DropLab" / "datos", base / "data" / "datos"]
    for c in candidatos:
        if (c / "ventas.csv").exists():
            return c
    sys.exit("No encuentro DropLab/datos/ventas.csv. Pon la carpeta del ejercicio junto a DropLab/ "
             "o define DROPLAB_DATOS con la ruta de los CSV.")


_TABLAS: dict[str, list[dict]] = {}


def tabla(nombre: str) -> list[dict]:
    """Lee un CSV una sola vez y lo guarda en memoria como lista de diccionarios."""
    if nombre not in _TABLAS:
        with (buscar_datos() / f"{nombre}.csv").open(encoding="utf-8", newline="") as f:
            _TABLAS[nombre] = list(csv.DictReader(f))
    return _TABLAS[nombre]


def validar(local_id: str, desde: str, hasta: str) -> str | None:
    """Devuelve un mensaje de error si los argumentos no son válidos (o None si lo son)."""
    if local_id not in TIENDAS:
        return f"local_id desconocido: {local_id}. Válidos: {', '.join(TIENDAS)}"
    try:
        d, h = date.fromisoformat(desde), date.fromisoformat(hasta)
    except (TypeError, ValueError):
        return "Fechas no válidas. Usa el formato YYYY-MM-DD."
    if d > h:
        return "'desde' es posterior a 'hasta'."
    return None


def euros(valor: Decimal) -> float:
    return float(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# ===========================================================================
# 2. Herramientas: funciones normales de Python
# ===========================================================================


def ventas_netas(local_id: str, desde: str, hasta: str) -> dict:
    """Ventas antes de reembolsos, reembolsos reconocidos y ventas netas de una tienda.

    - Una venta cuenta si su fecha_venta está entre desde y hasta (incluidas).
    - Un reembolso cuenta si su fecha_reconocimiento está en ese rango. La tienda del
      reembolso se obtiene de su venta original (linea_id), porque reembolsos.csv no
      tiene local_id.
    """
    error = validar(local_id, desde, hasta)
    if error:
        return {"error": error}
    ventas = tabla("ventas")
    bruto = sum((Decimal(v["importe_linea"]) for v in ventas
                 if v["local_id"] == local_id and desde <= v["fecha_venta"] <= hasta), Decimal(0))
    tienda_de_linea = {v["linea_id"]: v["local_id"] for v in ventas}
    abonos = sum((Decimal(r["importe_reembolso"]) for r in tabla("reembolsos")
                  if tienda_de_linea.get(r["linea_id"]) == local_id
                  and desde <= r["fecha_reconocimiento"] <= hasta), Decimal(0))
    return {
        "local_id": local_id,
        "desde": desde,
        "hasta": hasta,
        "ventas_antes_reembolsos_eur": euros(bruto),
        "reembolsos_reconocidos_eur": euros(abonos),
        "ventas_netas_eur": euros(bruto - abonos),
    }


def cesta(local_id: str, desde: str, hasta: str) -> dict:
    """Cómo son las compras de una tienda entre dos fechas (incluidas).

    Devuelve: pedidos, lineas, unidades, unidades_por_pedido, ticket_medio_eur y
    pedidos_4_o_mas_unidades.
    """
    error = validar(local_id, desde, hasta)
    if error:
        return {"error": error}
    filas = [v for v in tabla("ventas")
            if v["local_id"] == local_id and desde <= v["fecha_venta"] <= hasta]
    unidades_de_pedido = defaultdict(int)          # {pedido_id: unidades de ese pedido}
    for v in filas:
        unidades_de_pedido[v["pedido_id"]] += int(v["cantidad"])
    pedidos = len(unidades_de_pedido)
    unidades = sum(unidades_de_pedido.values())
    importe = sum((Decimal(v["importe_linea"]) for v in filas), Decimal(0))
    return {
        "local_id": local_id,
        "desde": desde,
        "hasta": hasta,
        "pedidos": pedidos,
        "lineas": len(filas),
        "unidades": unidades,
        "unidades_por_pedido": round(unidades / pedidos, 2) if pedidos else 0,
        "ticket_medio_eur": euros(importe / pedidos) if pedidos else 0,
        "pedidos_4_o_mas_unidades": sum(1 for u in unidades_de_pedido.values() if u >= 4),
    }



# ===========================================================================
# 3. Descripción de las herramientas para el modelo
# ===========================================================================

PARAMETROS = {
    "type": "object",
    "properties": {
        "local_id": {"type": "string", "enum": list(TIENDAS),
                    "description": "MAD-MAL = Malasaña, MAD-GOY = Goya, BCN-EIX = Eixample"},
        "desde": {"type": "string", "description": "Primer día incluido, formato YYYY-MM-DD"},
        "hasta": {"type": "string", "description": "Último día incluido, formato YYYY-MM-DD"},
    },
    "required": ["local_id", "desde", "hasta"],
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ventas_netas",
            "description": ("Ventas antes de reembolsos, reembolsos reconocidos y ventas netas (en euros) de UNA "
                            "tienda entre dos fechas incluidas. Para comparar periodos, llámala una vez por periodo."),
            "parameters": PARAMETROS,
        },
    },
        {
        "type": "function",
        "function": {
            "name": "cesta",
            "description": ("Cómo compran los clientes de UNA tienda entre dos fechas incluidas: número de pedidos, "
                            "líneas, unidades, unidades por pedido, ticket medio en euros (importe antes de "
                            "reembolsos / pedidos) y número de pedidos de 4 o más unidades. Úsala para preguntas "
                            "sobre pedidos, unidades, tamaño de la cesta o ticket medio; para ventas netas o "
                            "reembolsos usa ventas_netas. Para comparar periodos, llámala una vez por periodo."),
            "parameters": PARAMETROS,
        },
    },

]

EJECUTORES = {"ventas_netas": ventas_netas, "cesta": cesta}


# ===========================================================================
# 4. Comprobación de las funciones (sin modelo; no hace falta tocarlo)
# ===========================================================================

PRUEBAS = [
    ("ventas_netas · Eixample · periodo A", ventas_netas, ("BCN-EIX", "2026-03-02", "2026-03-29"),
     {"ventas_antes_reembolsos_eur": 25000.0, "reembolsos_reconocidos_eur": 1000.0, "ventas_netas_eur": 24000.0}),
    ("ventas_netas · Goya · 9 a 15 de marzo", ventas_netas, ("MAD-GOY", "2026-03-09", "2026-03-15"),
     {"ventas_antes_reembolsos_eur": 7610.33, "reembolsos_reconocidos_eur": 341.38, "ventas_netas_eur": 7268.95}),
    ("cesta · Goya · periodo A", cesta, ("MAD-GOY", "2026-03-02", "2026-03-29"),
     {"pedidos": 120, "lineas": 240, "unidades": 390, "unidades_por_pedido": 3.25, "ticket_medio_eur": 275.0,
      "pedidos_4_o_mas_unidades": 44}),
    ("cesta · Eixample · periodo B", cesta, ("BCN-EIX", "2026-03-30", "2026-04-26"),
     {"pedidos": 120, "lineas": 240, "unidades": 295, "unidades_por_pedido": 2.46, "ticket_medio_eur": 216.67,
      "pedidos_4_o_mas_unidades": 5}),
    ("cesta · Goya · 9 a 15 de marzo", cesta, ("MAD-GOY", "2026-03-09", "2026-03-15"),
     {"pedidos": 29, "lineas": 58, "unidades": 94, "unidades_por_pedido": 3.24, "ticket_medio_eur": 262.43,
      "pedidos_4_o_mas_unidades": 11}),
    ("cesta · tienda que no existe", cesta, ("MAD-XXX", "2026-03-02", "2026-03-29"), {"error": None}),
]


def probar() -> None:
    print("Comprobando las herramientas con casos de resultado conocido (no usa el modelo)\n")
    total = ok_total = 0
    for nombre, funcion, args, esperado in PRUEBAS:
        total += 1
        try:
            obtenido = funcion(*args)
        except NotImplementedError:
            print(f"  [PENDIENTE] {nombre}: la función todavía no está hecha")
            continue
        fallos = []
        for clave, valor in esperado.items():
            if clave == "error":
                if "error" not in obtenido:
                    fallos.append("debería devolver una clave 'error'")
            elif obtenido.get(clave) != valor:
                fallos.append(f"{clave}: esperado {valor}, obtenido {obtenido.get(clave)}")
        if fallos:
            print(f"  [FALLO] {nombre}\n          " + "\n          ".join(fallos))
        else:
            ok_total += 1
            print(f"  [OK]    {nombre}")
    print(f"\n{ok_total} de {total} pruebas superadas.")


# ===========================================================================
# 5. El modelo elige las herramientas: bucle de tool calling (no hace falta tocarlo)
# ===========================================================================

CONTEXTO = ("Periodo A: del 2026-03-02 al 2026-03-29. Periodo B: del 2026-03-30 al 2026-04-26.\n"
            "Tiendas: MAD-MAL (Malasaña), MAD-GOY (Goya), BCN-EIX (Eixample).")

INSTRUCCIONES = """Eres el analista de datos de DropLab.
{contexto}
Para cualquier cifra usa las herramientas disponibles; no calcules ni inventes cifras.
Si comparas periodos, pide cada periodo por separado.
Si ninguna herramienta puede responder a la pregunta, dilo claramente y no estimes.
Responde en español, en un máximo de 5 frases, citando las cifras que devuelven las herramientas."""

BATERIA = [
    "¿Cuáles fueron las ventas netas de Eixample en el periodo A y en el periodo B?",
    "¿Cuántos pedidos hizo Goya en el periodo B y cuántas unidades llevaba de media cada pedido?",
    "¿Qué ha cambiado en las compras de Malasaña entre el periodo A y el periodo B?",
    "¿Cuántos pedidos de 4 o más unidades hubo en Malasaña en el periodo A y en el periodo B?",
    "¿Cuánto vendió Malasaña, en ventas netas, entre el 6 y el 12 de abril de 2026?",
    "¿Cuántas personas visitaron la tienda de Malasaña en abril?",
]


def herramientas_pobres(tools: list[dict]) -> list[dict]:
    """Experimento: las mismas herramientas con descripciones casi vacías."""
    pobres = copy.deepcopy(tools)
    for t in pobres:
        t["function"]["description"] = "Herramienta de datos."
        for p in t["function"]["parameters"]["properties"].values():
            p.pop("description", None)
            p.pop("enum", None)
    return pobres


def llamar_ollama(payload: dict) -> dict:
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        sys.exit(f"Ollama devolvió {exc.code}. ¿Has descargado el modelo? Prueba: ollama pull {payload['model']}")
    except urllib.error.URLError:
        sys.exit("No puedo conectar con Ollama en localhost:11434. ¿Está abierto? Prueba: ollama list")


def ejecutar(nombre: str, argumentos) -> dict:
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos)
        except json.JSONDecodeError:
            return {"error": "Los argumentos no son un JSON válido."}
    if nombre not in EJECUTORES:
        return {"error": f"No existe la herramienta {nombre}."}
    try:
        return EJECUTORES[nombre](**argumentos)
    except NotImplementedError:
        return {"error": f"La herramienta {nombre} todavía no está implementada."}
    except TypeError as exc:
        return {"error": f"Argumentos incorrectos: {exc}"}


def preguntar(pregunta: str, modelo: str, sin_contexto: bool, pobres: bool, mostrar: bool = True,
              max_rondas: int = 5) -> dict:
    sistema = INSTRUCCIONES.format(contexto="" if sin_contexto else CONTEXTO)
    tools = herramientas_pobres(TOOLS) if pobres else TOOLS
    messages = [{"role": "system", "content": sistema}, {"role": "user", "content": pregunta}]
    traza, inicio, respuesta = [], time.time(), ""
    if mostrar:
        print(f"\nPREGUNTA: {pregunta}")
    for ronda in range(max_rondas + 1):
        payload = {"model": modelo, "messages": messages, "stream": False, "think": False,
                   "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 600}}
        if ronda < max_rondas:
            payload["tools"] = tools
        mensaje = llamar_ollama(payload)["message"]
        llamadas = mensaje.get("tool_calls") or []
        if not llamadas:
            respuesta = (mensaje.get("content") or "").strip()
            break
        messages.append({"role": "assistant", "content": mensaje.get("content", ""), "tool_calls": llamadas})
        for ll in llamadas:
            nombre, args = ll["function"]["name"], ll["function"].get("arguments") or {}
            resultado = ejecutar(nombre, args)
            traza.append({"herramienta": nombre, "argumentos": args, "resultado": resultado})
            messages.append({"role": "tool", "content": json.dumps(resultado, ensure_ascii=False),
                             "tool_name": nombre})
            if mostrar:
                print(f"  → el modelo pide  {nombre}({json.dumps(args, ensure_ascii=False)})")
                print(f"    tu código da    {json.dumps(resultado, ensure_ascii=False)}")
    segundos = round(time.time() - inicio, 1)
    if mostrar:
        if not traza:
            print("  (el modelo no ha usado ninguna herramienta)")
        print(f"RESPUESTA ({segundos} s): {respuesta}\n")
    return {"pregunta": pregunta, "llamadas": traza, "respuesta": respuesta, "segundos": segundos}


def bateria(modelo: str, sin_contexto: bool, pobres: bool, solo: list[int] | None) -> None:
    etiqueta = "base" + ("_sin_contexto" if sin_contexto else "") + ("_descripciones_pobres" if pobres else "")
    if modelo != MODELO:
        etiqueta += "_" + modelo.replace(":", "-").replace("/", "-")
    print(f"Batería · modelo {modelo} · experimento: {etiqueta}")
    resultados = []
    for i, q in enumerate(BATERIA, 1):
        if solo and i not in solo:
            continue
        print(f"\n===== Pregunta {i} =====")
        resultados.append({"id": i, **preguntar(q, modelo, sin_contexto, pobres)})
    salida = Path(__file__).with_name(f"resultados_{etiqueta}.json")
    salida.write_text(json.dumps({"modelo": modelo, "experimento": etiqueta, "resultados": resultados},
                                 ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nRESUMEN")
    for r in resultados:
        usadas = ", ".join(f"{c['herramienta']}({c['argumentos'].get('desde', '?')}…{c['argumentos'].get('hasta', '?')})"
                           if isinstance(c["argumentos"], dict) else c["herramienta"] for c in r["llamadas"]) or "ninguna"
        print(f"  P{r['id']} · {r['segundos']:>5} s · herramientas: {usadas}")
    print(f"\nGuardado en {salida.name}. Ahora revisa cada respuesta y rellena la entrega.")


def main() -> None:
    p = argparse.ArgumentParser(description="DropLab · Ejercicio 3: tu propia herramienta para el modelo.")
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("probar", help="Comprueba tus funciones con resultados conocidos (sin modelo).")
    c = sub.add_parser("calcular", help="Ejecuta tú una herramienta: calcular cesta MAD-MAL 2026-03-02 2026-03-29")
    c.add_argument("herramienta", choices=list(EJECUTORES))
    c.add_argument("local_id")
    c.add_argument("desde")
    c.add_argument("hasta")
    for nombre in ("preguntar", "bateria"):
        s = sub.add_parser(nombre)
        if nombre == "preguntar":
            s.add_argument("pregunta")
        else:
            s.add_argument("--solo", default="", help="Preguntas a ejecutar, por ejemplo 3,4,5")
        s.add_argument("--modelo", default=MODELO)
        s.add_argument("--sin-contexto", action="store_true", help="Experimento: no decir qué fechas son A y B.")
        s.add_argument("--descripciones-pobres", action="store_true",
                       help="Experimento: herramientas con descripciones casi vacías.")
    a = p.parse_args()
    if a.orden == "probar":
        probar()
    elif a.orden == "calcular":
        print(json.dumps(ejecutar(a.herramienta, {"local_id": a.local_id, "desde": a.desde, "hasta": a.hasta}),
                         ensure_ascii=False, indent=2))
    elif a.orden == "preguntar":
        preguntar(a.pregunta, a.modelo, a.sin_contexto, a.descripciones_pobres)
    else:
        solo = [int(x) for x in a.solo.split(",") if x.strip()] or None
        bateria(a.modelo, a.sin_contexto, a.descripciones_pobres, solo)


if __name__ == "__main__":
    main()
