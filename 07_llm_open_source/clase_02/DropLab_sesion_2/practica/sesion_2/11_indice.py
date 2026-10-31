"""RAG · paso 2: el índice vectorial. Cada fragmento se convierte en un vector (embedding).

Un modelo de embeddings lee un texto y devuelve una lista de números (un vector) que
resume su significado: textos que dicen cosas parecidas dan vectores cercanos, aunque
usen palabras distintas. Lo calculamos con Ollama, en local, y lo guardamos en DuckDB
(el mismo motor del bloque I): una tabla con los fragmentos, sus metadatos y su vector.

Para un corpus pequeño (decenas o miles de fragmentos) no hace falta una base de datos
vectorial especial: DuckDB compara la pregunta con todos los vectores en milisegundos.

Cada modelo espera las preguntas y los documentos con un «prefijo» propio: está en PREFIJOS.

Uso:
  python practica/sesion_2/11_indice.py                         # bge-m3 (el elegido): crea el índice
  python practica/sesion_2/11_indice.py --modelo qwen3-embedding:0.6b
  python practica/sesion_2/11_indice.py --ver "tote bag"        # el vector de un texto, en números y en colores
  python practica/sesion_2/11_indice.py --comparar              # ¿qué textos quedan cerca? (ejemplo preparado)
  python practica/sesion_2/11_indice.py --comparar "tote bag" "bolsa de regalo" "avería del vehículo"

En la nube sería lo mismo con otras piezas: los vectores, con un modelo de embeddings de Azure
OpenAI; el índice, en Azure AI Search (campos filtrables para la ficha y un campo vectorial).

Salida: practica/sesion_2/rag/indice_<modelo>.duckdb
Requisito: ollama pull bge-m3 (y el corpus: 10_corpus.py).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb
import requests

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
RAG = AQUI / "rag"
CORPUS = RAG / "corpus.jsonl"
OLLAMA = "http://localhost:11434/api/embed"
MODELO = "bge-m3"

# Cómo espera cada modelo las consultas y los documentos (según su ficha).
PREFIJOS = {
    "nomic-embed-text": ("search_query: ", "search_document: "),
    "qwen3-embedding": ("Instruct: Dada una pregunta, recupera los fragmentos de documentos que la responden\nQuery: ", ""),
    "embeddinggemma": ("task: search result | query: ", "title: none | text: "),
    "bge-m3": ("", ""),
}


def prefijos(modelo: str) -> tuple[str, str]:
    return PREFIJOS.get(modelo.split(":")[0], ("", ""))


def embeber(textos: list[str], modelo: str, lote: int = 16, avance=None) -> list[list[float]]:
    """Vectores de una lista de textos (Ollama /api/embed, por lotes). avance(n): para la barra de progreso."""
    vectores = []
    for i in range(0, len(textos), lote):
        r = requests.post(OLLAMA, json={"model": modelo, "input": textos[i:i + lote], "truncate": True}, timeout=600)
        if r.status_code == 404:
            raise SystemExit(f"Ollama no tiene el modelo {modelo}: ollama pull {modelo}")
        r.raise_for_status()
        vectores += r.json()["embeddings"]
        if avance:
            avance(len(textos[i:i + lote]))
    return vectores


def ruta_indice(modelo: str) -> Path:
    return RAG / f"indice_{modelo.replace(':', '_').replace('/', '_')}.duckdb"


def cargar_corpus() -> list[dict]:
    if not CORPUS.exists():
        raise SystemExit("Falta el corpus: ejecuta antes python practica/sesion_2/10_corpus.py")
    return [json.loads(l) for l in CORPUS.open(encoding="utf-8")]


def crear(modelo: str, avance=None) -> dict:
    frags = cargar_corpus()
    _, pref_doc = prefijos(modelo)
    t0 = time.time()
    vectores = embeber([pref_doc + f["texto_indexado"] for f in frags], modelo, avance=avance)
    segundos = time.time() - t0
    ruta = ruta_indice(modelo)
    ruta.unlink(missing_ok=True)
    con = duckdb.connect(str(ruta))
    con.execute("""CREATE TABLE fragmentos (id INTEGER, fuente VARCHAR, tipo VARCHAR, titulo VARCHAR, codigo VARCHAR,
                   seccion VARCHAR, pagina INTEGER, fecha VARCHAR, estado VARCHAR, sustituido_por VARCHAR,
                   estado_documento VARCHAR, sustitucion_deducida_de VARCHAR, sustitucion_mencion VARCHAR,
                   responsable VARCHAR, cita VARCHAR, inicio DOUBLE, fin DOUBLE, texto VARCHAR, texto_indexado VARCHAR,
                   vector FLOAT[])""")
    con.executemany("INSERT INTO fragmentos VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        (f["id"], f["fuente"], f["tipo"], f["titulo"], f["codigo"], f["seccion"], f["pagina"], f["fecha"], f["estado"],
         f.get("sustituido_por"), f.get("estado_documento"), f.get("sustitucion_deducida_de"), f.get("sustitucion_mencion"),
         f["responsable"], f["cita"], f.get("inicio"), f.get("fin"), f["texto"], f["texto_indexado"], v)
        for f, v in zip(frags, vectores)])
    con.execute("CREATE TABLE info AS SELECT ? AS modelo, ? AS dimensiones, ? AS fragmentos, ? AS segundos",
                [modelo, len(vectores[0]), len(frags), round(segundos, 1)])
    con.close()
    return {"modelo": modelo, "dimensiones": len(vectores[0]), "fragmentos": len(frags), "segundos": round(segundos, 1),
            "ruta": ruta}


# ---------------------------------------------------------------------------
# Vistas: ver un vector y ver qué textos quedan cerca
# ---------------------------------------------------------------------------

EJEMPLO = ["avería del vehículo", "el camión se estropeó", "tote bag", "bolsa de regalo", "HIST-JOIN-001"]


def coseno(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    return num / ((sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5))


def tira(v: list[float], n: int = 64):
    """Los primeros n números del vector como una tira de colores: azul positivo, rojo negativo."""
    from rich.text import Text
    t = Text()
    escala = max(abs(x) for x in v[:n]) or 1
    for x in v[:n]:
        k = min(1.0, abs(x) / escala)
        r, g, b = (int(255 - 205 * k), int(255 - 150 * k), 255) if x >= 0 else (255, int(255 - 190 * k), int(255 - 190 * k))
        t.append("█", f"rgb({r},{g},{b})")
    return t


def barra(valor: float, ancho: int = 30) -> str:
    llenos = round(max(0.0, valor) * ancho)
    return "█" * llenos + "░" * (ancho - llenos)


def vista_vector(c, texto: str, modelo: str) -> None:
    from rich.text import Text
    v = embeber([prefijos(modelo)[0] + texto], modelo)[0]
    c.print(Text.assemble((f"«{texto}»", "bold"), f"  →  {modelo}  →  ", (f"{len(v)} números", "bold cyan")))
    c.print("  [" + ", ".join(f"{x:+.3f}" for x in v[:8]) + f", … y {len(v) - 8} más]")
    c.print(Text.assemble("  ", tira(v), ("  ← los 64 primeros: azul +, rojo −", "dim")))
    c.print("[dim]  Ningún número significa nada por sí solo: el significado está en el conjunto. "
            "Lo útil es comparar vectores (--comparar).[/dim]")


def vista_comparar(c, textos: list[str], modelo: str) -> None:
    from rich.table import Table
    from rich.text import Text
    pref_q = prefijos(modelo)[0]
    vs = embeber([pref_q + x for x in textos], modelo)
    c.rule(f"[bold]¿Qué textos quedan cerca? · {modelo} · {len(vs[0])} números por texto")
    ancho = max(len(x) for x in textos) + 4
    for x, v in zip(textos, vs):
        c.print(Text.assemble(f"  {('«' + x + '»'):<{ancho}}", tira(v, 48)))
    t = Table(box=None, padding=(0, 1), header_style="bold")
    t.add_column("similitud coseno", style="bold")
    for x in textos:
        t.add_column(x[:14], justify="center")
    for i, x in enumerate(textos):
        fila = []
        for j in range(len(textos)):
            s = coseno(vs[i], vs[j])
            estilo = "dim" if i == j else ("bold green" if s >= 0.6 else ("yellow" if s >= 0.45 else ""))
            fila.append(Text(f"{s:.2f}", estilo))
        t.add_row(x[:24], *fila)
    c.print()
    c.print(t)
    pares = sorted(((coseno(vs[i], vs[j]), i, j) for i in range(len(vs)) for j in range(i + 1, len(vs))), reverse=True)
    c.print("\n[bold]De más parecido a menos:[/bold]")
    for s, i, j in pares[:6]:
        color = "green" if s >= 0.6 else ("yellow" if s >= 0.45 else "white")
        c.print(Text.assemble(f"  {s:.2f} ", (barra(s), color), f"  «{textos[i]}» ↔ «{textos[j]}»"))
    c.print("\n[dim]  1 = mismo significado. Textos sin relación no dan 0: rondan 0,3–0,4 con bge-m3.\n"
            "  Fíjate en las parejas que se parecen SIN compartir palabras: eso es buscar por significado.[/dim]")


def vista_indice(c, r: dict) -> None:
    from rich.panel import Panel
    from rich.table import Table
    con = duckdb.connect(str(r["ruta"]), read_only=True)
    filas = con.execute("SELECT id, cita, estado, vector FROM fragmentos WHERE id IN (2, 36, 42) ORDER BY id").fetchall()
    con.close()
    total = f"{r['fragmentos'] * r['dimensiones']:,}".replace(",", ".")
    c.print(Panel(f"[bold]{r['fragmentos']}[/] fragmentos × [bold]{r['dimensiones']}[/] números = "
                  f"[bold]{total}[/] números · {r['segundos']} s con {r['modelo']}\n"
                  f"Guardado: [cyan]{r['ruta'].relative_to(ROOT)}[/] ({r['ruta'].stat().st_size / 1e6:.1f} MB): "
                  "un archivo, como el DuckDB del bloque I",
                  title="[bold]RAG · paso 2 · índice vectorial[/]", border_style="cyan", expand=False))
    t = Table(title="Así queda la tabla «fragmentos» (3 filas de ejemplo): la ficha en columnas y, al lado, el vector",
              header_style="bold", title_justify="left")
    for col in ("id", "cita", "estado", "… 11 columnas más de la ficha y el texto", f"vector FLOAT[{r['dimensiones']}]"):
        t.add_column(col)
    for i, cita, estado, v in filas:
        color = "red" if estado == "sustituido" else ("green" if estado in ("aprobado", "vigente") else "magenta")
        t.add_row(str(i), cita, f"[{color}]{estado}[/]", "[dim]título, código, fecha, página…[/]", tira(v, 24))
    c.print(t)
    c.print("[dim]En Azure AI Search sería un índice con los mismos campos (filtrables) y un campo vectorial.\n"
            "Siguiente: python practica/sesion_2/12_buscar.py \"¿Hasta qué día estuvo vigente el Pack 4?\"[/dim]")


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG · paso 2: crear el índice vectorial en DuckDB.")
    ap.add_argument("--modelo", default=MODELO)
    ap.add_argument("--ver", help="Enseñar el vector de un texto (sin crear el índice).")
    ap.add_argument("--comparar", nargs="*", help="Comparar textos: ¿cuáles quedan cerca? (sin textos: un ejemplo).")
    a = ap.parse_args()
    from rich.console import Console
    from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
    c = Console()
    if a.ver:
        vista_vector(c, a.ver, a.modelo)
        return
    if a.comparar is not None:
        vista_comparar(c, a.comparar if len(a.comparar) >= 2 else EJEMPLO, a.modelo)
        return
    n = len(cargar_corpus())
    with Progress(TextColumn("  convirtiendo fragmentos en vectores"), BarColumn(), TextColumn("{task.completed}/{task.total}"),
                  TimeElapsedColumn(), console=c) as prog:
        tarea = prog.add_task("", total=n)
        r = crear(a.modelo, avance=lambda k: prog.advance(tarea, k))
    vista_indice(c, r)


if __name__ == "__main__":
    main()
