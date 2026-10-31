"""Práctica 3 · Hablar con la API: peticiones y respuestas, como lo haría cualquier programa.

Cada operación enseña la PETICIÓN (método, dirección y cuerpo) y la RESPUESTA (código HTTP y JSON).

    python practica/sesion_3/04_cliente_api.py salud
    python practica/sesion_3/04_cliente_api.py buscar "¿Hasta qué día estuvo vigente el Pack 4?"
    python practica/sesion_3/04_cliente_api.py consulta                       # resumen de Malasaña (sin modelo)
    python practica/sesion_3/04_cliente_api.py consulta --pedido "1; DROP TABLE ventas"   # parámetro rechazado
    python practica/sesion_3/04_cliente_api.py ticket ticket_marzo.png         # imagen → comprobación (VLM)
    python practica/sesion_3/04_cliente_api.py analizar "¿Cuánto cayó el neto de Goya?"
    python practica/sesion_3/04_cliente_api.py salud --api http://127.0.0.1:8999   # API caída: ¿qué error da?

Lo mismo se puede hacer con curl o desde /docs. La API no sabe ni le importa quién la llama: Open WebUI, este
script o un Excel con Power Query.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.syntax import Syntax  # noqa: E402

from asistente import config  # noqa: E402

c = Console()


def recortar(x, n=400):
    if isinstance(x, str) and len(x) > n:
        return x[:120] + f"… ({len(x)} caracteres)"
    if isinstance(x, dict):
        return {k: recortar(v, n) for k, v in x.items()}
    if isinstance(x, list):
        return [recortar(v, n) for v in x[:12]] + ([f"… y {len(x) - 12} más"] if len(x) > 12 else [])
    return x


def llamar(metodo: str, api: str, ruta: str, cuerpo: dict | None = None, archivos: dict | None = None,
           formulario: dict | None = None, ver: int = 60) -> dict | None:
    c.print(Panel(Syntax(f"{metodo} {api}{ruta}\n" + (json.dumps(recortar(cuerpo), ensure_ascii=False, indent=2)
                                                      if cuerpo else "")
                         + (f"\n(multipart) imagen={archivos['imagen'][0]}, {formulario}" if archivos else ""),
                         "http", word_wrap=True), title="[bold]PETICIÓN[/]", border_style="cyan", title_align="left"))
    t0 = time.time()
    try:
        r = requests.request(metodo, api + ruta, json=cuerpo, files=archivos, data=formulario, timeout=900)
    except requests.exceptions.ConnectionError:
        c.print(Panel(f"[red]No hay nadie escuchando en {api}.[/]\nEl cliente no recibe ningún JSON: el error lo pone "
                      "quien llama (en Open WebUI, la Pipe lo enseña como API_NO_DISPONIBLE).",
                      title="[bold red]SIN RESPUESTA[/]", border_style="red", title_align="left"))
        return None
    seg = time.time() - t0
    try:
        j = r.json()
    except ValueError:
        j = {"texto": r.text[:500]}
    col = "green" if r.status_code < 300 else "yellow" if r.status_code < 500 else "red"
    texto = json.dumps(recortar(j), ensure_ascii=False, indent=2)
    lineas = texto.splitlines()
    if len(lineas) > ver:
        texto = "\n".join(lineas[:ver]) + f"\n… ({len(lineas) - ver} líneas más)"
    c.print(Panel(Syntax(texto, "json", word_wrap=True), title=f"[bold]RESPUESTA[/] · HTTP [{col}]{r.status_code}[/] · "
                  f"{seg:.1f} s", border_style=col, title_align="left"))
    return j


def main() -> None:
    ap = argparse.ArgumentParser(description="Cliente de la API del Asistente DropLab.")
    ap.add_argument("operacion", choices=["salud", "buscar", "consulta", "ticket", "analizar"])
    ap.add_argument("texto", nargs="?")
    ap.add_argument("--api", default=config.API_URL)
    ap.add_argument("--pedido")
    ap.add_argument("--tienda", default="MAD-MAL")
    ap.add_argument("--imagen")
    a = ap.parse_args()
    if a.operacion == "salud":
        llamar("GET", a.api, "/salud")
    elif a.operacion == "buscar":
        llamar("POST", a.api, "/documentos/buscar", {"pregunta": a.texto or "¿Hasta qué día estuvo vigente el Pack 4?",
                                                     "k": 3})
    elif a.operacion == "consulta":
        cuerpo = ({"consulta": "pedido", "pedido_id": a.pedido} if a.pedido
                  else {"consulta": "resumen_tienda", "local_id": a.tienda})
        llamar("POST", a.api, "/datos/consulta", cuerpo)
    elif a.operacion == "ticket":
        nombre = a.texto or "ticket_marzo.png"
        ruta = next((b / nombre for b in (Path.cwd(), config.IMAGENES, config.SINTETICAS) if (b / nombre).exists()), None)
        if not ruta:
            raise SystemExit(f"No encuentro {nombre}")
        tipo = "recuento" if "recuento" in nombre else "albaran" if "albaran" in nombre else "ticket"
        llamar("POST", a.api, "/tickets/comprobar", archivos={"imagen": (ruta.name, ruta.read_bytes(), "image/png")},
               formulario={"tipo": tipo}, ver=90)
    else:
        cuerpo = {"pregunta": a.texto or "¿Cuánto cayó el neto de Goya entre A y B?"}
        if a.imagen:
            ruta = next(b / a.imagen for b in (Path.cwd(), config.IMAGENES, config.SINTETICAS) if (b / a.imagen).exists())
            cuerpo["imagen_base64"] = base64.b64encode(ruta.read_bytes()).decode()
        llamar("POST", a.api, "/analizar", cuerpo, ver=80)


if __name__ == "__main__":
    main()
