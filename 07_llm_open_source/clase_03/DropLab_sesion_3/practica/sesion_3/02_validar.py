"""Práctica 1 (b) · El esquema y la validación, sin ningún modelo (instantáneo).

Tres ideas, con ejemplos preparados:
    1. El ESQUEMA: Pydantic define los campos y sus tipos; de ahí sale el JSON Schema que recibe el VLM.
    2. La VALIDACIÓN: Pydantic rechaza lo que no tiene la forma pedida (un importe «doscientos», una fecha imposible).
    3. JSON VÁLIDO ≠ CONTENIDO CORRECTO: una extracción inventada pasa la validación si tiene la forma correcta.
       Por eso, después, el código compara con los registros.

Uso:
    python practica/sesion_3/02_validar.py              # los tres ejemplos
    python practica/sesion_3/02_validar.py --esquema    # el JSON Schema completo del ticket
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.syntax import Syntax  # noqa: E402

from asistente import vision  # noqa: E402

c = Console()

EJEMPLOS = [
    ("A · Lo que leyó el VLM del ticket de abril (real, guardado)", "bien", {
        "pedido_id": "B-MAD-MAL-ORD-0005", "fecha": "2026-04-04", "tienda_codigo": "MAD-MAL",
        "lineas": [{"producto": "NIGHT SHIFT", "sku": "NIGHT_SHIFT_LILA_41", "linea_id": "B-MAD-MAL-0732", "cantidad": 1,
                    "precio_unitario": 130.0, "descuento": 12.73, "importe": 117.27},
                   {"producto": "CLOUD STEP", "sku": "CLOUD_STEP_AZUL_40", "linea_id": "B-MAD-MAL-0733", "cantidad": 1,
                    "precio_unitario": 105.0, "descuento": 10.28, "importe": 94.72}],
        "total_impreso": 231.99, "texto_campana": None, "campos_ilegibles": [], "legibilidad_declarada": "buena"}),
    ("B · Mal formado (como sin esquema): importe en letra, fecha imposible, legibilidad inventada", "mal", {
        "pedido_id": "B-MAD-MAL-ORD-0005", "fecha": "2026-04-31", "tienda_codigo": "MAD-MAL",
        "lineas": [{"producto": "NIGHT SHIFT", "cantidad": "una", "importe": "ciento diecisiete"}],
        "total_impreso": "231,99 €", "legibilidad_declarada": "95 %"}),
    ("C · Bien formado… e INVENTADO (lo que leyó el VLM del ticket muy borroso, real)", "trampa", {
        "pedido_id": "8-MAD-MAL-000-0005", "fecha": "2020-04-04", "tienda_codigo": "MAD-MAL",
        "lineas": [{"producto": "NIGHT SHIFT", "sku": "NIGHT_SHIFT_LILA_41", "linea_id": "8-MAD-MAL-0732", "cantidad": 1,
                    "precio_unitario": 138.88, "descuento": 12.75, "importe": 126.13},
                   {"producto": "CLOUD STEP", "sku": "CLOUD_STEP_AZUL_41", "linea_id": "8-MAD-MAL-0732", "cantidad": 1,
                    "precio_unitario": 105.98, "descuento": 18.28, "importe": 87.7}],
        "total_impreso": 231.99, "texto_campana": None, "campos_ilegibles": [], "legibilidad_declarada": "buena"}),
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Esquema y validación con Pydantic, sin modelo.")
    ap.add_argument("--esquema", action="store_true")
    a = ap.parse_args()
    esquema = vision.Ticket.model_json_schema()
    if a.esquema:
        c.print(Syntax(json.dumps(esquema, ensure_ascii=False, indent=2), "json"))
        return
    c.rule("[bold]1 · El esquema: lo escribimos en Python (Pydantic) y de ahí sale el JSON Schema")
    c.print(Syntax('''class LineaTicket(BaseModel):
    sku: str | None              # None = no se lee
    cantidad: int | None
    importe: float | None

class Ticket(BaseModel):
    pedido_id: str | None
    fecha: date | None           # AAAA-MM-DD; una fecha imposible no pasa
    lineas: list[LineaTicket]
    total_impreso: float | None  # el impreso, aunque no cuadre
    campos_ilegibles: list[str]
    legibilidad_declarada: Literal["buena", "regular", "mala"]   # opinión, no probabilidad''', "python"))
    c.print(f"[dim]El JSON Schema resultante tiene {len(json.dumps(esquema))} caracteres; Ollama lo usa en «format» "
            "para que el modelo solo pueda escribir JSON con esa forma (--esquema para verlo).[/]\n")
    c.rule("[bold]2 y 3 · Validar tres extracciones")
    for titulo, clase, ejemplo in EJEMPLOS:
        datos_, errores = vision.validar("ticket", json.dumps(ejemplo, ensure_ascii=False))
        if errores:
            cuerpo = "\n".join(f"[red]✗ {e['campo']}: {e['error']}[/]" for e in errores)
            c.print(Panel(cuerpo, title=f"{titulo}  →  [red]NO PASA[/]", border_style="red", title_align="left"))
            continue
        coh = vision.coherencia_ticket(datos_)
        malas = [x for x in coh if x["resultado"] != "coincide"]
        cuerpo = "[green]✓ Pydantic: JSON válido, campos y tipos correctos.[/]\n"
        if malas:
            cuerpo += "[bold]Pero el código encuentra:[/]\n" + "\n".join(
                f"[yellow]• {x['campo']}: {x['en_imagen']} → {x['nota'] or x['resultado']}[/]" for x in malas)
        else:
            cuerpo += "[dim]Y es coherente consigo mismo (las líneas suman lo que suman).[/]"
        col = "green" if clase == "bien" else "magenta"
        c.print(Panel(cuerpo, title=f"{titulo}  →  [{col}]PASA LA VALIDACIÓN[/]", border_style=col, title_align="left"))
    c.print("\n[bold]Para llevar:[/] la validación garantiza la [bold]forma[/]; el [bold]contenido[/] se comprueba "
            "después, con el propio documento y con los registros (01_ver_imagen.py).")


if __name__ == "__main__":
    main()
