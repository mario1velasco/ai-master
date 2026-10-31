"""El examen: preguntas con su respuesta calculada a mano, y una nota.

Para elegir un modelo o una forma de darle los datos no basta con «parece que
responde bien». Hace falta un examen:

  1. Preguntas variadas, escritas por nosotros.
  2. La respuesta correcta de cada una, calculada A MANO con SQL revisado y
     contrastada con el script 03 (experimentos/text2sql/verdad*.py).
  3. El modelo responde con su herramienta, como lo haría en producción.
  4. El código puntúa: ¿la respuesta contiene todas las cifras correctas?
     En las preguntas imposibles, ¿dice que el dato no existe?

Tres exámenes, para no hacernos trampas:
  bateria      13 preguntas: con ellas se diseñó la capa semántica
  validacion   10 preguntas nuevas: comprobar que no la ajustamos a la batería
  final        10 preguntas nuevas, escritas antes de la versión definitiva

Modos (lo que ve el modelo):
  clase   tablas crudas + reglas de cálculo en el prompt (el 08 de la sesión 1)
  capa    vistas de la capa semántica + verificador (04 y 05 de esta sesión)

Uso:
  python practica/sesion_2/04_examen.py --ver                  # preguntas y respuestas, sin modelo
  python practica/sesion_2/04_examen.py --modo clase --rapido  # 5 preguntas (~2 min)
  python practica/sesion_2/04_examen.py --modo capa --rapido
  python practica/sesion_2/04_examen.py --modo capa --examen final
  python practica/sesion_2/04_examen.py --modo clase --modelo qwen3:4b-instruct --preguntas P01 P07
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

from rich.console import Console
from rich.table import Table

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
asistente = import_module("01_preguntar_datos")

EXAMENES = {"bateria": "bateria.json", "validacion": "validacion.json", "final": "prueba_final.json"}
RAPIDO = ["P01", "P06", "P08", "P11", "P13"]     # neto, un día, producto, cesta e imposible
NEGACIONES = ["no hay", "no se puede", "no es posible", "no dispon", "no existe", "no contiene", "no permite",
              "no tenemos", "no incluye", "no se dispone", "no está disponible", "no registra", "no identifica",
              "no se registra", "no aparece", "imposible"]

console = Console()


def cargar(examen: str) -> list[dict]:
    return json.loads((AQUI / "examen" / EXAMENES[examen]).read_text(encoding="utf-8"))


def corregir(p: dict, respuesta: str | None) -> tuple[bool, list[str]]:
    """¿Contiene la respuesta todas las cifras (±0,01) y nombres esperados? En las imposibles, ¿lo niega?"""
    texto = asistente.normalizar(respuesta or "")
    if p.get("debe_negar"):
        ok = any(n in texto.lower() for n in NEGACIONES)
        return ok, [] if ok else ["no dice que el dato no existe"]
    nums = asistente.numeros(texto)
    faltan = [f"{k}={v:g}" for k, v in p["esperado"].items()
              if isinstance(v, (int, float)) and not any(abs(n - abs(v)) <= 0.011 for n in nums)]
    for k, opciones in p.get("texto_esperado", {}).items():
        if not any(o.lower() in texto.lower() for o in opciones):
            faltan.append(f"{k}={opciones[0]}")
    return not faltan, faltan


def esperado_legible(p: dict) -> str:
    if p.get("debe_negar"):
        return "decir que el dato no existe"
    def num(v):
        if isinstance(v, float):
            return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").removesuffix(",00")
        return str(v)
    partes = [f"{k} {num(v)}" for k, v in p["esperado"].items() if not isinstance(v, str)]
    partes += [f"{k} {v[0]}" for k, v in p.get("texto_esperado", {}).items()]
    return " · ".join(partes)


def ver(preguntas: list[dict], examen: str) -> None:
    t = Table(title=f"Examen «{examen}»: {len(preguntas)} preguntas con su respuesta calculada a mano", show_lines=True)
    t.add_column("Id", style="bold")
    t.add_column("Qué pone a prueba", style="dim")
    t.add_column("Pregunta")
    t.add_column("Respuesta correcta", style="green")
    for p in preguntas:
        t.add_row(p["id"], p["tipo"], p["pregunta"], esperado_legible(p))
    console.print(t)


def main() -> None:
    ap = argparse.ArgumentParser(description="Examen con respuestas calculadas a mano.")
    ap.add_argument("--examen", choices=list(EXAMENES), default="bateria")
    ap.add_argument("--modo", choices=["clase", "capa"], default="capa")
    ap.add_argument("--modelo", default=asistente.MODELO)
    ap.add_argument("--rapido", action="store_true", help=f"Solo {', '.join(RAPIDO)} (batería).")
    ap.add_argument("--preguntas", nargs="*")
    ap.add_argument("--ver", action="store_true", help="Enseñar preguntas y respuestas, sin llamar al modelo.")
    a = ap.parse_args()

    preguntas = cargar(a.examen)
    ids = a.preguntas or (RAPIDO if a.rapido else None)
    if ids:
        preguntas = [p for p in preguntas if p["id"] in ids]
    if a.ver:
        ver(preguntas, a.examen)
        return

    con, sistema = asistente.preparar(a.modo)
    verificar = a.modo == "capa"
    console.rule(f"[bold cyan]EXAMEN «{a.examen}» · {a.modelo} · modo {a.modo}"
                 + (" + verificador" if verificar else ""))
    aciertos, tiempo = 0, 0.0
    for p in preguntas:
        r = asistente.conversar(a.modelo, sistema, p["pregunta"], con, verificar=verificar,
                                max_rondas=6 if a.modo == "capa" else 4)
        ok, faltan = corregir(p, r["respuesta"])
        aciertos += ok
        tiempo += r["segundos"] - r["segundos_carga"]
        marca = "[green]✓[/]" if ok else "[red]✗[/]"
        console.print(f"{marca} [bold]{p['id']}[/] {p['pregunta']}")
        for paso in r["traza"]:
            console.print(f"     [blue]SQL[/] {' '.join(paso['sql'].split())[:150]}", highlight=False)
        console.print(f"     [dim]respuesta:[/] {(r['respuesta'] or '').strip()[:220]}", highlight=False)
        if not ok:
            console.print(f"     [red]esperado: {esperado_legible(p)} · falta: {', '.join(faltan)}[/]", highlight=False)
        console.print(f"     [dim]{len(r['traza'])} SQL · {r['segundos']} s[/]")
    n = len(preguntas)
    console.rule(f"[bold]NOTA: {aciertos} de {n} ({aciertos / n:.0%}) · {tiempo / n:.0f} s por pregunta")


if __name__ == "__main__":
    main()
