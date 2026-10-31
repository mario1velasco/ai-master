"""RAG · paso 4: preguntar a los documentos y obtener una respuesta con fuentes.

  1. Buscar (12_buscar.py): los k fragmentos más relevantes, en modo híbrido.
  2. Dárselos al modelo numerados [F1], [F2]…, cada uno con su documento, página o
     sección, fecha y ESTADO (aprobado, vigente, sustituido, transcripción automática…).
  3. El modelo responde SOLO con esos fragmentos y cita [F#] detrás de cada afirmación.
  4. El código construye la lista de fuentes (no el modelo) y VERIFICA la respuesta:
       - que las citas existen;
       - que cada frase lleva su cita;
       - que cada cifra o fecha de la respuesta aparece en el fragmento que cita;
       - que no se apoya en un borrador sustituido como si fuera lo vigente.

Uso:
  python practica/sesion_2/13_preguntar_documentos.py "¿Hasta qué día estuvo vigente el Pack 4?"
  python practica/sesion_2/13_preguntar_documentos.py "¿Qué pasó el 6 de abril con Street One?" -k 6
  python practica/sesion_2/13_preguntar_documentos.py "…" --llm qwen3:4b-instruct
  python practica/sesion_2/13_preguntar_documentos.py "…" --sin-reglas       # sin las reglas de versiones y fechas
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from importlib import import_module
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
indice = import_module("11_indice")
buscar = import_module("12_buscar")

OLLAMA = "http://localhost:11434/api/chat"
LLM = "qwen3:30b-a3b-instruct-2507-q4_K_M"
K = 5

REGLAS = """Eres el analista de DropLab. Respondes preguntas usando SOLO los fragmentos que se te dan.

Reglas:
- Cada afirmación lleva detrás la cita del fragmento del que sale, por ejemplo [F2]. Sin cita, no se afirma.
- Si los fragmentos no contienen la respuesta, di «No consta en los documentos» y qué información faltaría.
- Si dos fragmentos se contradicen, manda el de estado aprobado o vigente. Un borrador o documento SUSTITUIDO
  solo se menciona como antecedente, diciendo que fue sustituido.
- Respeta el significado de cada fecha: recepción de un aviso, inicio programado, fin previsto y fecha
  efectiva son cosas distintas. Lo previsto no prueba que ocurriera: si la pregunta da por hecho algo que
  los fragmentos no confirman, dilo.
- No afirmes lo que un fragmento no dice, tampoco en negativo («no menciona…»).
- La llamada es una transcripción automática: puede tener errores. Úsala como testimonio, no como dato oficial,
  y preferentemente junto a un documento.
- No calcules cifras nuevas ni afirmes causas que los fragmentos no digan.
- Responde en español, en un máximo de 5 frases."""

REGLAS_MINIMAS = """Eres el analista de DropLab. Responde a la pregunta con los fragmentos que se te dan y cita [F#].
Responde en español, en un máximo de 5 frases."""


def contexto(frags: list[dict]) -> str:
    partes = []
    for n, f in enumerate(frags, 1):
        cab = f"[F{n}] {f['cita']} · {f['titulo']} ({f['codigo']}) · estado: {f['estado']} · fecha: {f['fecha']}"
        if f.get("sustituido_por"):
            cab += f" · SUSTITUIDO por {f['sustituido_por']}: no describe lo que se aplicó"
        partes.append(cab + "\n" + f["texto"])
    return "\n\n".join(partes)


# ---------------------------------------------------------------------------
# Verificación (el código revisa al modelo)
# ---------------------------------------------------------------------------

def frases(texto: str) -> list[str]:
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ¿¡«])", texto) if f.strip()]


def verificar(respuesta: str, frags: list[dict], pregunta: str) -> tuple[list[dict], list[str]]:
    avisos, citados = [], []
    numeros_cita = [int(n) for n in re.findall(r"\[F(\d+)\]", respuesta)]
    for n in numeros_cita:
        if not 1 <= n <= len(frags):
            avisos.append(f"cita inexistente [F{n}]")
        elif frags[n - 1] not in citados:
            citados.append(frags[n - 1])
    for fr in frases(respuesta):
        cit = [int(n) for n in re.findall(r"\[F(\d+)\]", fr) if 1 <= int(n) <= len(frags)]
        normal = buscar.normalizar(fr)
        if not cit:
            if not any(x in normal for x in ("no consta", "no se dispone", "faltaria", "falta", "no hay")):
                avisos.append(f"frase sin cita: «{fr[:60]}…»")
            continue
        texto_citado = buscar.normalizar(" ".join(frags[i - 1]["texto"] + " " + frags[i - 1]["titulo"] for i in cit))
        sin_citas = re.sub(r"\[F\d+\]", " ", fr)            # los números de las citas no cuentan
        for num in re.findall(r"\d+(?:[.,:/]\d+)*", sin_citas):
            sueltos = re.findall(r"\d+", num)
            if not all(s in texto_citado or s in pregunta for s in sueltos):
                avisos.append(f"«{num}» no aparece en {', '.join(f'[F{i}]' for i in cit)}")
    if any(f.get("sustituido_por") for f in citados):
        normal = buscar.normalizar(respuesta)
        if not any(x in normal for x in ("borrador", "sustitu", "propuesta")):
            avisos.append("cita un documento sustituido sin decir que es un borrador")
    return citados, avisos


def preguntar(pregunta: str, b: "buscar.Buscador", llm: str = LLM, modo: str = "hibrida", k: int = K,
              reglas: bool = True) -> dict:
    t0 = time.time()
    frags = b.buscar(pregunta, modo, k)
    mensaje = f"Fragmentos:\n\n{contexto(frags)}\n\nPregunta: {pregunta}"
    payload = {"model": llm, "stream": False, "think": False,
               "options": {"num_ctx": 8192, "temperature": 0, "num_predict": 500},
               "messages": [{"role": "system", "content": REGLAS if reglas else REGLAS_MINIMAS},
                            {"role": "user", "content": mensaje}]}
    r = requests.post(OLLAMA, json=payload, timeout=600)
    r.raise_for_status()
    c = r.json()
    respuesta = c["message"]["content"].strip()
    citados, avisos = verificar(respuesta, frags, pregunta)
    return {"pregunta": pregunta, "respuesta": respuesta, "fragmentos": frags, "citados": citados, "avisos": avisos,
            "segundos": round(time.time() - t0, 1), "tokens_entrada": c.get("prompt_eval_count")}


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG · preguntar a los documentos, con fuentes y verificación.")
    ap.add_argument("pregunta")
    ap.add_argument("-k", type=int, default=K)
    ap.add_argument("--modo", choices=["semantica", "palabras", "hibrida"], default="hibrida")
    ap.add_argument("--llm", default=LLM)
    ap.add_argument("--modelo", default=indice.MODELO, help="Modelo de embeddings.")
    ap.add_argument("--sin-reglas", action="store_true", help="Sin las reglas de versiones, fechas y citas.")
    a = ap.parse_args()
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    cons = Console()
    b = buscar.Buscador(a.modelo)
    r = preguntar(a.pregunta, b, a.llm, a.modo, a.k, reglas=not a.sin_reglas)

    cons.rule(f"[bold cyan]1 · LO QUE ENCONTRÓ EL BUSCADOR ({a.modo}, k={a.k}, {a.modelo})")
    for n, f in enumerate(r["fragmentos"], 1):
        citado = f in r["citados"]
        color = "red" if f["estado"] == "sustituido" else ("green" if f["estado"] in ("aprobado", "vigente") else "white")
        marca = "[bold green]● citado[/]" if citado else "[dim]○ no citado[/]"
        extra = " · añadido por ser el documento vigente" if f.get("anadido") else ""
        cons.print(f"  [F{n}] {marca}  {f['cita']} · [{color}]{f['estado']}[/] · {f['fecha']}{extra}")
    cons.rule(f"[bold cyan]2 · LA RESPUESTA ({a.llm})")
    from rich.text import Text
    texto = Text()
    pos = 0
    for m in re.finditer(r"\[F(\d+)\]", r["respuesta"]):     # cada cita, del color del estado de su fuente
        texto.append(r["respuesta"][pos:m.start()])
        n = int(m.group(1))
        est = r["fragmentos"][n - 1]["estado"] if 0 < n <= len(r["fragmentos"]) else ""
        col = "red" if est == "sustituido" else ("green" if est in ("aprobado", "vigente") else
                                                 "magenta" if est.startswith("transcripción") else "cyan")
        texto.append(m.group(), f"bold {col}" if est else "bold white on red")
        pos = m.end()
    texto.append(r["respuesta"][pos:])
    cons.print(Panel(texto, border_style="green",
                     subtitle="[dim]color de cada cita = estado de su fuente: verde vigente · rojo sustituido · "
                              "morado llamada[/]"))
    cons.rule("[bold cyan]3 · LAS FUENTES (las pone el código, a partir de las citas)")
    t = Table(show_header=True)
    for col in ("Cita", "Documento", "Dónde", "Estado", "Fecha"):
        t.add_column(col)
    for f in r["citados"]:
        n = r["fragmentos"].index(f) + 1
        donde = f"pág. {f['pagina']}" if f["pagina"] else f["seccion"]
        t.add_row(f"[F{n}]", f["titulo"], donde, f["estado"], f["fecha"])
    cons.print(t)
    cons.rule("[bold cyan]4 · VERIFICACIÓN DEL CÓDIGO")
    if r["avisos"]:
        for x in r["avisos"]:
            cons.print(f"  [yellow]⚠ {x}[/]")
    else:
        cons.print("  [green]✓ Todas las frases citan un fragmento, las citas existen y cada cifra aparece en su fuente.[/]")
    cons.print(f"[dim]{r['segundos']} s · {r['tokens_entrada']} tokens de entrada[/dim]")


if __name__ == "__main__":
    main()
