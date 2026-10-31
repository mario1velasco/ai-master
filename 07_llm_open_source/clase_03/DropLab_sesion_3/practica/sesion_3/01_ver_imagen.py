"""Práctica 1 · Leer una imagen con un VLM: de la pregunta libre al dato comprobado.

Seis pasos, uno detrás de otro, para ver qué hace el modelo y qué hace el código:

    1. pregunta libre    el VLM describe la imagen en prosa                         ← modelo
    2. extracción        el mismo VLM, con un esquema JSON (campos y tipos fijos)    ← modelo
    3. validación        Pydantic: ¿es JSON?, ¿están los campos?, ¿tienen su tipo?   ← código
    4. consulta          el pedido (o el stock) en los registros, con SQL de parámetros  ← código
    5. comparación       campo a campo, y el documento consigo mismo              ← código
    6. veredicto         coincide · discrepancia · lectura dudosa · no verificable  ← código

Uso:
    python practica/sesion_3/01_ver_imagen.py                                   # el ticket de marzo (coincide)
    python practica/sesion_3/01_ver_imagen.py ticket_abril.png                  # el de abril (no cuadra)
    python practica/sesion_3/01_ver_imagen.py recuento_stock_0604.png
    python practica/sesion_3/01_ver_imagen.py albaran_0604.png
    python practica/sesion_3/01_ver_imagen.py ticket_abril_muy_borroso.png      # sintética: lectura dudosa
    python practica/sesion_3/01_ver_imagen.py ticket_abril.png --modelo qwen3-vl:4b-instruct
    python practica/sesion_3/01_ver_imagen.py ticket_abril.png --sin-libre      # sin el paso 1 (más rápido)
    python practica/sesion_3/01_ver_imagen.py ticket_abril.png --guardada       # salida guardada (sin modelo)

Las imágenes se buscan en data/imagenes/ y en practica/sesion_3/imagenes_sinteticas/.
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
from rich.table import Table  # noqa: E402

from asistente import config, vision  # noqa: E402
from asistente.ollama import ErrorComponente  # noqa: E402

c = Console()
COLOR = {"coincide": "green", "no_coincide": "bold red", "sin_dato": "yellow", "aviso": "yellow"}
VEREDICTO = {"coincide": "green", "discrepancia": "red", "lectura_dudosa": "magenta", "coincide_en_parte": "yellow",
             "no_verificable": "yellow", "revisar": "yellow"}


def buscar_imagen(nombre: str) -> Path:
    for base in (Path.cwd(), config.IMAGENES, config.SINTETICAS):
        p = base / nombre
        if p.exists():
            return p
    disponibles = sorted(x.name for d in (config.IMAGENES, config.SINTETICAS) for x in d.glob("*.png"))
    raise SystemExit(f"No encuentro {nombre}. Disponibles: {', '.join(disponibles)}")


def tipo_por_nombre(nombre: str) -> str:
    return "recuento" if "recuento" in nombre else "albaran" if "albaran" in nombre else "ticket"


def tiempos(t: dict) -> str:
    return (f"{t['segundos']} s · carga {t['carga']} s · imagen y prompt {t['entrada']} s ({t['tokens_entrada']} tokens) · "
            f"escribir {t['salida']} s ({t['tokens_salida']} tokens, {t['tokens_por_segundo']} tok/s)")


def mostrar(nombre: str, libre: dict | None, ex: dict, comp: dict | None) -> None:
    sint = " · IMAGEN SINTÉTICA (derivada de ticket_abril.png)" if "borroso" in nombre else ""
    c.rule(f"[bold]{nombre}{sint} · {ex['modelo']} · {ex['imagen']['px_original']} → {ex['imagen']['px']} px")
    if libre:
        c.print(Panel(libre["respuesta"], title="[bold]1 · Pregunta libre[/] — el VLM describe (útil para leer; el código no "
                      "puede usarlo)", subtitle=f"[dim]{tiempos(libre['tiempos'])}[/]", border_style="cyan", title_align="left"))
    c.print(Panel(Syntax(json.dumps(json.loads(ex["json_crudo"]), ensure_ascii=False, indent=2) if ex["valido"] else
                         ex["json_crudo"], "json", word_wrap=True),
                  title="[bold]2 · Extracción con esquema[/] — lo que escribió el modelo, tal cual",
                  subtitle=f"[dim]{tiempos(ex['tiempos'])}[/]", border_style="blue", title_align="left"))
    if ex["valido"]:
        leg = ex["datos"].get("legibilidad_declarada")
        c.print(f"[bold]3 · Validación (Pydantic)[/]  [green]✓ JSON válido: campos y tipos correctos.[/]  "
                f"[dim]Legibilidad que declara el modelo: «{leg}» (una opinión, no una probabilidad). "
                f"Ilegibles: {ex['datos'].get('campos_ilegibles') or 'ninguno'}[/]")
    else:
        c.print("[bold]3 · Validación (Pydantic)[/]  [red]✗ no pasa:[/]")
        for e in ex["errores_validacion"]:
            c.print(f"   [red]· {e['campo']}: {e['error']}[/]")
        return
    if comp is None:
        return
    for q in comp["consultas"]:
        c.print(Panel(f"[cyan]{q['sql']}[/]\n[dim]parámetros: {q['parametros']} · {len(q['filas'])} fila(s)[/]",
                      title=f"[bold]4 · Consulta[/] — {q['titulo']} (SQL nuestro, solo lectura, con parámetros)",
                      border_style="dim", title_align="left"))
    t = Table(title="5 · Comparación (la hace el código)", title_justify="left", header_style="bold")
    for col in ("tipo", "campo", "en la imagen", "en el registro / cálculo", "resultado"):
        t.add_column(col)
    for x in comp["comprobaciones"]:
        t.add_row(x.get("clase", ""), x["campo"], str(x["en_imagen"] if x["en_imagen"] is not None else "—"),
                  str(x["en_registro"] if x["en_registro"] is not None else "—"),
                  f"[{COLOR.get(x['resultado'], 'white')}]{x['resultado']}[/]")
    c.print(t)
    col = VEREDICTO.get(comp["veredicto"], "white")
    c.print(Panel("\n".join(f"• {e}" for e in comp["explicacion"]), title=f"[bold]6 · Veredicto: [{col}]"
                  f"{comp['veredicto'].upper()}[/][/]  [dim](lo escribe el código, no el modelo)[/]",
                  border_style=col, title_align="left"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Leer una imagen con un VLM y comprobarla con los registros.")
    ap.add_argument("imagen", nargs="?", default="ticket_marzo.png")
    ap.add_argument("--tipo", choices=vision.TIPOS, help="Por defecto, por el nombre del archivo.")
    ap.add_argument("--modelo", default=config.MODELO_VISION)
    ap.add_argument("--sin-libre", action="store_true", help="Saltar el paso 1.")
    ap.add_argument("--sin-esquema", action="store_true", help="Extraer SIN «format»: ¿qué pasa sin esquema?")
    ap.add_argument("--guardada", action="store_true", help="Mostrar la salida guardada (sin llamar al modelo).")
    a = ap.parse_args()
    ruta = buscar_imagen(a.imagen)
    tipo = a.tipo or tipo_por_nombre(ruta.name)
    guardada = config.GUARDADAS / "vision" / f"{ruta.stem}.json"
    if a.guardada:
        if not guardada.exists():
            raise SystemExit(f"No hay salida guardada para {ruta.name} (python practica/sesion_3/guardar_salidas.py)")
        g = json.loads(guardada.read_text(encoding="utf-8"))
        c.print(f"[bold yellow]SALIDA GUARDADA[/] [dim]({g['fecha']}, {g['extraccion']['modelo']}): no se ha llamado a "
                "ningún modelo[/]")
        mostrar(ruta.name, g.get("libre"), g["extraccion"], g["comprobacion"])
        return
    try:
        img = vision.preparar_imagen(ruta.read_bytes())
        libre = None if a.sin_libre else vision.pregunta_libre(img, modelo=a.modelo)
        ex = vision.extraer(img, tipo, a.modelo, con_esquema=not a.sin_esquema)
        comp = vision.COMPROBAR[tipo](ex["datos"]) if ex["valido"] else None
    except ErrorComponente as e:
        c.print(f"[red]✗ {e.codigo} ({e.componente}): {e.mensaje}[/]")
        c.print(f"[dim]Plan B: python practica/sesion_3/01_ver_imagen.py {ruta.name} --guardada[/]")
        raise SystemExit(1)
    mostrar(ruta.name, libre, ex, comp)


if __name__ == "__main__":
    main()
