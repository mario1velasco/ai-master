"""Práctica 3 · El flujo: una pregunta, varias fuentes, una respuesta con evidencias.

Ejecuta el grafo de LangGraph (asistente/flujo.py) y enseña cada paso según termina: qué nodo, qué
herramienta, qué fuentes y cuánto tarda. Al final, la respuesta, las evidencias numeradas por el código,
las comprobaciones y los límites.

Preguntas preparadas (--caso):
    documental   ¿Hasta qué día estuvo vigente el Pack 4 en Malasaña?
    numerica     ¿Cuánto cambiaron las ventas netas y los pedidos de 4 o más unidades en Malasaña?
    visual       ¿Qué demuestra este ticket? (+ ticket_abril.png)
    combinada    ¿Qué cambió en Malasaña, qué aportan los documentos y la llamada y qué demuestra este ticket? (+ ticket)
    insuficiente ¿Cuántas tote bags se entregaron en marzo y cuántas ventas se perdieron por las obras?
    causal       ¿La rotura de stock del 6 de abril es la causa de la caída de Malasaña?
  Junio (segundo encargo: solo documentos, leídos por PaddleOCR-VL con 08 y 09):
    junio_tabla      ¿Cuántos pares de NEGRO_41 aceptó Malasaña en junio? El borrador decía 72.   (versiones)
    junio_grafico    ¿Qué semana tuvo el peor % de líneas completas en Malasaña? ¿Fue por la caja húmeda?  (gráfico)
    junio_escaneado  ¿Cuántos pares del albarán A-0617-04 se aceptaron al final y qué pasó con el resto?  (escaneado)
    junio_trampa     ¿Faltan 18 pares? ¿Cuánto costó la incidencia descontando los 240 € del transportista?
  Extras (si sobra tiempo):
    extra_falla      ¿Cuántos pares de ARENA_41 aceptó Goya en junio y cuándo llegó la última entrega?  (falla: 40, ENT-06-012)
    extra_campana    ¿La campaña de junio aumentó las ventas de Street One?   (no hay campaña en junio: «no consta»)

Uso:
    python practica/sesion_3/05_flujo.py --caso documental
    python practica/sesion_3/05_flujo.py --caso combinada
    python practica/sesion_3/05_flujo.py "¿Qué pasó el 6 de abril?" --imagen albaran_0604.png
    python practica/sesion_3/05_flujo.py --caso numerica --reglas           # el plan, por palabras clave (sin modelo)
    python practica/sesion_3/05_flujo.py --caso documental --sin-framework  # el mismo proceso sin LangGraph
    python practica/sesion_3/05_flujo.py --dibujar                          # el grafo (Mermaid), sin ejecutar
    python practica/sesion_3/05_flujo.py --caso combinada --guardada        # salida guardada (sin modelos)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from asistente import config, flujo, flujo_simple  # noqa: E402
from asistente.ollama import ErrorComponente  # noqa: E402

c = Console()
CASOS = {
    "documental": ("¿Hasta qué día estuvo vigente el Pack 4 en Malasaña?", None),
    "numerica": ("¿Cuánto cambiaron las ventas netas y los pedidos de 4 o más unidades en Malasaña entre A y B?", None),
    "visual": ("¿Qué demuestra este ticket? Compáralo con caja.", "ticket_abril.png"),
    "combinada": ("¿Qué cambió en las ventas de Malasaña, qué aportan los documentos y la llamada, y qué demuestra "
                  "este ticket?", "ticket_abril.png"),
    "insuficiente": ("¿Cuántas tote bags se entregaron en marzo y cuántas ventas se perdieron por las obras?", None),
    "causal": ("¿La rotura de stock del 6 de abril es la causa de la caída de Malasaña?", None),
    # Junio (segundo encargo): solo documentos, leídos por PaddleOCR-VL (08 y 09)
    "junio_tabla": ("¿Cuántos pares de STREET_ONE_NEGRO_41 aceptó Malasaña en junio? El borrador decía 72.", None),
    "junio_grafico": ("¿Qué semana de junio tuvo el peor porcentaje de líneas completas en Malasaña? ¿Fue por la caja "
                      "húmeda del albarán A-0617-04?", None),
    "junio_escaneado": ("¿Cuántos pares del albarán A-0617-04 se aceptaron al final y qué pasó con el resto?", None),
    # Extras (si sobra tiempo): una que el asistente FALLA con la verificación limpia, y la errata de la «campaña»
    "extra_falla": ("¿Cuántos pares de STREET_ONE_ARENA_41 aceptó Goya en junio y cuándo llegó la última entrega?", None),
    "extra_campana": ("¿La campaña de junio aumentó las ventas de Street One?", None),
    "junio_trampa": ("Tras la reposición de junio, ¿faltan 18 pares en las tiendas? ¿Cuánto costó la incidencia "
                     "descontando los 240 euros del transportista?", None),
}
COLOR_NODO = {"planificar": "magenta", "leer_imagen": "cyan", "consultar_datos": "blue", "buscar_documentos": "green",
              "contrastar": "yellow", "redactar": "bold white", "verificar": "bold yellow"}


def ruta_imagen(nombre: str | None) -> Path | None:
    if not nombre:
        return None
    for base in (Path.cwd(), config.IMAGENES, config.SINTETICAS):
        if (base / nombre).exists():
            return base / nombre
    raise SystemExit(f"No encuentro la imagen {nombre}")


def al_avanzar(nodo: str, cambios: dict) -> None:
    for t in cambios.get("traza", []):
        c.print(f"  [{COLOR_NODO.get(nodo, 'white')}]▸ {nodo:<18}[/] [dim]{t['segundos']:>6.1f} s[/]  "
                f"[dim]{t['herramienta']}[/]  {t['detalle'][:150]}")
    for e in cambios.get("errores", []):
        c.print(f"  [red]  ✗ {e['codigo']} ({e['componente']}): {e['mensaje']}[/]")


def mostrar(r: dict) -> None:
    c.print(Panel(Markdown(r["respuesta"] or "_(sin respuesta)_"), title="[bold]Respuesta[/] (la redacta el modelo)",
                  border_style="green", title_align="left"))
    if r["verificacion"]:
        c.print(f"[yellow]⚠ Verificación del código: {'; '.join(r['verificacion'])}[/]")
    else:
        c.print("[green]✓ Verificación del código: citas existentes, cifras con respaldo, sin culpas ni causas "
                "afirmadas.[/]  [dim](no comprueba el significado: eso, una persona)[/]")
    t = Table(title="Evidencias (las numera el código) · ● citada  ○ consultada", title_justify="left", header_style="bold")
    for col in ("", "id", "qué es", "detalle"):
        t.add_column(col)
    for e in r["evidencias"]:
        if e["tipo"] == "datos":
            det = f"[cyan]{e['sql'][:110]}…[/] parámetros {e['parametros']}"
        elif e["tipo"] == "documento":
            det = f"{e['cita']} · {e['estado']} · {e['fecha']}" + (" · [red]SUSTITUIDO[/]" if e.get("sustituido_por") else "")
        else:
            det = f"{e['modelo']} · veredicto [bold]{e.get('veredicto')}[/]"
        t.add_row("●" if e.get("citada") else "[dim]○[/]", e["id"], e["tipo"], det)
    c.print(t)
    for x in r["comprobaciones"]:
        c.print(f"  [yellow]◆[/] [bold]{x['nombre']}[/] · {x['resultado']}: {x['detalle']}")
    for x in r["limitaciones"]:
        c.print(f"  [dim]◇ límite:[/] {x}")
    for e in r["errores"]:
        c.print(f"  [red]✗ {e['codigo']} ({e['componente']}): {e['mensaje']}[/]")
    seg = {}
    for t_ in r["traza"]:
        seg[t_["nodo"]] = seg.get(t_["nodo"], 0) + t_["segundos"]
    c.print(f"[dim]{r['segundos']} s en total · " + " · ".join(f"{k} {v:.0f} s" for k, v in seg.items())
            + f" · texto {r['configuracion']['modelo_texto']} · visión {r['configuracion']['modelo_vision']}[/]")


def main() -> None:
    ap = argparse.ArgumentParser(description="El flujo del Asistente DropLab, paso a paso.")
    ap.add_argument("pregunta", nargs="?")
    ap.add_argument("--caso", choices=list(CASOS))
    ap.add_argument("--imagen")
    ap.add_argument("--reglas", action="store_true", help="Plan por palabras clave en lugar del modelo.")
    ap.add_argument("--sin-framework", action="store_true", help="El mismo proceso con funciones de Python (sin LangGraph).")
    ap.add_argument("--modelo-texto", default=None)
    ap.add_argument("--modelo-vision", default=None)
    ap.add_argument("--dibujar", action="store_true")
    ap.add_argument("--guardada", action="store_true")
    ap.add_argument("--guardar", type=Path, help="Guardar el resultado completo en JSON.")
    a = ap.parse_args()
    if a.dibujar:
        c.print(Panel(flujo.mermaid(), title="El grafo (Mermaid: pégalo en mermaid.live)", border_style="cyan"))
        c.print("[dim]Flechas continuas: siempre. Discontinuas: las elige el enrutamiento (enrutar, tras_verificar).[/]")
        return
    pregunta, imagen = (CASOS[a.caso] if a.caso else (a.pregunta, None))
    imagen = a.imagen or imagen
    if not pregunta:
        ap.error("Escribe una pregunta o elige --caso.")
    if a.guardada:
        ruta = config.GUARDADAS / "flujo" / f"{a.caso or 'pregunta'}.json"
        if not ruta.exists():
            raise SystemExit(f"No hay salida guardada {ruta.name} (python practica/sesion_3/guardar_salidas.py)")
        r = json.loads(ruta.read_text(encoding="utf-8"))
        c.print(f"[bold yellow]SALIDA GUARDADA[/] [dim]({r.get('fecha', '?')}): no se ha llamado a ningún modelo[/]")
        c.rule(f"[bold]«{pregunta}»" + (f"  + {imagen}" if imagen else ""))
        for t_ in r["traza"]:
            al_avanzar(t_["nodo"], {"traza": [t_]})
        mostrar(r)
        return
    c.rule(f"[bold]«{pregunta}»" + (f"  + {imagen}" if imagen else "")
           + ("  · sin framework" if a.sin_framework else "  · LangGraph"))
    ruta = ruta_imagen(imagen)
    motor = flujo_simple if a.sin_framework else flujo
    try:
        r = motor.ejecutar(pregunta, ruta.read_bytes() if ruta else None, al_avanzar=al_avanzar,
                           modelo_texto=a.modelo_texto, modelo_vision=a.modelo_vision,
                           planificador="reglas" if a.reglas else "modelo")
    except ErrorComponente as e:
        c.print(f"[red]✗ {e.codigo} ({e.componente}): {e.mensaje}[/]")
        raise SystemExit(1)
    mostrar(r)
    if a.guardar:
        a.guardar.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
