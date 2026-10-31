"""RAG · paso 3: buscar. La pregunta entra; salen los fragmentos más relevantes, con su fuente.

Tres formas de buscar:
  semantica  por significado: la pregunta se convierte en vector y se compara con todos
             (similitud coseno, en DuckDB). Entiende sinónimos; puede fallar con códigos.
  palabras   por palabras clave (BM25, el clásico de los buscadores). Clava códigos y
             nombres («HIST-JOIN-001», «DL-0604-MAL»); no entiende sinónimos.
  hibrida    las dos a la vez, combinadas por su posición (Reciprocal Rank Fusion).

Y una regla de negocio, en el código: si sale un fragmento de un documento SUSTITUIDO
(el borrador del Pack 4), se avisa y se añade el documento que lo sustituye.

Uso:
  python practica/sesion_2/12_buscar.py "¿Hasta qué día duró el Pack 4?"
  python practica/sesion_2/12_buscar.py "¿Hasta qué día duró el Pack 4?" --explicar   # cómo se combinan las dos listas
  python practica/sesion_2/12_buscar.py "HIST-JOIN-001" --modo palabras
  python practica/sesion_2/12_buscar.py "¿Qué pasó el 6 de abril?" --modo semantica -k 8
  python practica/sesion_2/12_buscar.py "¿Hasta qué día duró el Pack 4?" --sin-vigentes  # sin la regla de versiones

Qué se ve: un ranking con barras (y, en la híbrida, el puesto en cada lista), el estado de cada
fragmento en color y, en el texto, en amarillo, las palabras de la pregunta que aparecen.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import unicodedata
from collections import Counter
from importlib import import_module
from pathlib import Path

import duckdb

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
indice = import_module("11_indice")

K = 5
STOP = set("""a al algo como con de del el en es esa ese esta este fue ha han hay la las le les lo los mas me mi muy
no o para pero por que qué se si sin sobre su sus te tu un una uno unos y ya cual cuál cuando cuándo cuanto cuánto
cuantos cuántos donde dónde quien quién""".split())


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def tokens(texto: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9_]+(?:-[a-z0-9_]+)*", normalizar(texto)) if w not in STOP]


class Buscador:
    """Carga el índice de un modelo y busca de las tres formas."""

    def __init__(self, modelo: str = indice.MODELO, ruta: Path | None = None):
        ruta = ruta or indice.ruta_indice(modelo)   # ruta: otro índice (la sesión 3 usa el ampliado con junio)
        if not ruta.exists():
            raise SystemExit(f"Falta el índice de {modelo}: python practica/sesion_2/11_indice.py --modelo {modelo}")
        self.modelo = modelo
        self.con = duckdb.connect(str(ruta), read_only=True)
        cols = [c[0] for c in self.con.execute("DESCRIBE fragmentos").fetchall() if c[0] != "vector"]
        self.frags = {r[0]: dict(zip(cols, r)) for r in self.con.execute(f"SELECT {', '.join(cols)} FROM fragmentos").fetchall()}
        # BM25: estadísticas de palabras de todo el corpus
        self.docs = {i: tokens(f["texto_indexado"]) for i, f in self.frags.items()}
        self.media = sum(len(d) for d in self.docs.values()) / len(self.docs)
        df = Counter(w for d in self.docs.values() for w in set(d))
        n = len(self.docs)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}
        self.tf = {i: Counter(d) for i, d in self.docs.items()}

    def semantica(self, pregunta: str, k: int = K) -> list[tuple[int, float]]:
        pref_q, _ = indice.prefijos(self.modelo)
        q = indice.embeber([pref_q + pregunta], self.modelo)[0]
        filas = self.con.execute(
            "SELECT id, list_cosine_similarity(vector, ?::FLOAT[]) AS s FROM fragmentos ORDER BY s DESC LIMIT ?",
            [q, k]).fetchall()
        return [(i, float(s)) for i, s in filas]

    def palabras(self, pregunta: str, k: int = K, k1: float = 1.5, b: float = 0.75) -> list[tuple[int, float]]:
        q = tokens(pregunta)
        puntos = {}
        for i, tf in self.tf.items():
            largo = len(self.docs[i])
            s = sum(self.idf.get(w, 0) * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * largo / self.media))
                    for w in q if w in tf)
            if s > 0:
                puntos[i] = s
        return sorted(puntos.items(), key=lambda x: -x[1])[:k]

    def hibrida(self, pregunta: str, k: int = K, rrf: int = 60) -> list[tuple[int, float]]:
        """Reciprocal Rank Fusion: suma 1/(60 + posición) de cada lista. No mezcla puntuaciones distintas."""
        puntos = Counter()
        for lista in (self.semantica(pregunta, 20), self.palabras(pregunta, 20)):
            for pos, (i, _) in enumerate(lista):
                puntos[i] += 1 / (rrf + pos + 1)
        return puntos.most_common(k)

    def buscar(self, pregunta: str, modo: str = "hibrida", k: int = K, vigentes: bool = True) -> list[dict]:
        """Fragmentos (dict) con su puntuación. Con vigentes=True, añade el documento que sustituye a un borrador."""
        res = getattr(self, modo)(pregunta, k)
        salida = [{**self.frags[i], "puntuacion": s, "anadido": False} for i, s in res]
        if vigentes:
            ids = {f["id"] for f in salida}
            for f in list(salida):
                if f.get("sustituido_por"):
                    nuevos = [x for x in self.frags.values() if x["codigo"] == f["sustituido_por"] and x["id"] not in ids]
                    for x in nuevos[:1]:
                        salida.append({**x, "puntuacion": None, "anadido": True})
                        ids.add(x["id"])
        return salida


# ---------------------------------------------------------------------------
# Vista
# ---------------------------------------------------------------------------


def resaltar(texto: str, palabras_q: set[str]):
    """El texto con las palabras de la pregunta en amarillo (lo que ve la búsqueda por palabras)."""
    from rich.text import Text
    t = Text()
    pos = 0
    for m in re.finditer(r"[\wÀ-ÿ]+(?:-[\wÀ-ÿ]+)*", texto):
        t.append(texto[pos:m.start()])
        t.append(m.group(), "bold black on yellow" if normalizar(m.group()) in palabras_q else "")
        pos = m.end()
    t.append(texto[pos:])
    return t


def extracto(texto: str, palabras_q: set[str], largo: int = 420) -> str:
    """Hasta `largo` caracteres; si la primera palabra buscada está más abajo, el trozo donde aparece."""
    if len(texto) <= largo:
        return texto
    inicio = 0
    for m in re.finditer(r"[\wÀ-ÿ]+(?:-[\wÀ-ÿ]+)*", texto):
        if normalizar(m.group()) in palabras_q:
            inicio = max(0, m.start() - 150) if m.start() > largo - 80 else 0
            break
    trozo = texto[inicio:inicio + largo]
    return ("… " if inicio else "") + trozo + (" …" if inicio + largo < len(texto) else "")


def color(estado: str) -> str:
    return "red" if estado == "sustituido" else ("green" if estado in ("aprobado", "vigente") else
                                                 "magenta" if estado.startswith("transcripción") else "cyan")


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG · paso 3: buscar fragmentos relevantes.")
    ap.add_argument("pregunta")
    ap.add_argument("--modo", choices=["semantica", "palabras", "hibrida"], default="hibrida")
    ap.add_argument("-k", type=int, default=K)
    ap.add_argument("--modelo", default=indice.MODELO)
    ap.add_argument("--sin-vigentes", action="store_true", help="No añadir el documento que sustituye a un borrador.")
    ap.add_argument("--explicar", action="store_true", help="Enseñar las dos listas y cómo se combinan (RRF).")
    ap.add_argument("--corto", action="store_true", help="Solo el ranking, sin el texto de cada fragmento.")
    a = ap.parse_args()
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    c = Console()
    b = Buscador(a.modelo)
    palabras_q = set(tokens(a.pregunta))
    res = b.buscar(a.pregunta, a.modo, a.k, not a.sin_vigentes)
    sem = [i for i, _ in b.semantica(a.pregunta, 20)]
    pal = [i for i, _ in b.palabras(a.pregunta, 20)]

    c.rule(f"[bold cyan]«{a.pregunta}»  ·  búsqueda {a.modo}  ·  {a.modelo}  ·  k = {a.k}")
    c.print(Text.assemble("  palabras que busca BM25: ", (" ".join(sorted(palabras_q)) or "—", "bold black on yellow"),
                          ("   (sin «de», «el», «qué»…: no distinguen)", "dim")))
    t = Table(box=None, padding=(0, 1), header_style="bold")
    for col, j in (("#", "right"), ("fragmento", "left"), ("estado", "left"), ("puntuación", "left"),
                   ("puesto por significado", "center"), ("puesto por palabras", "center")):
        t.add_column(col, justify=j, no_wrap=col in ("fragmento", "puntuación"))
    maxp = max((f["puntuacion"] for f in res if f["puntuacion"] is not None), default=1) or 1
    for n, f in enumerate(res, 1):
        if f["puntuacion"] is None:
            punt = Text("+ añadido: es el vigente", "bold green")
        else:
            valor = f["puntuacion"] / maxp
            punt = Text.assemble(("█" * round(valor * 16) + "░" * (16 - round(valor * 16)), color(f["estado"])),
                                 f" {f['puntuacion']:.3f}")
        ps = sem.index(f["id"]) + 1 if f["id"] in sem else None
        pp = pal.index(f["id"]) + 1 if f["id"] in pal else None
        est = Text(f["estado"][:24], f"bold {color(f['estado'])}")
        if f.get("sustituido_por"):
            est.append(f" → {f['sustituido_por']}", color(f["estado"]))
        t.add_row(str(n), f["cita"], est, punt, f"{ps}º" if ps else "—", f"{pp}º" if pp else "[dim]no sale[/]")
    c.print(t)
    if any(f.get("sustituido_por") for f in res):
        c.print("  [red]⚠ Ha salido un documento SUSTITUIDO.[/] La similitud no sabe qué documento manda; "
                "la ficha sí: " + ("[green]se añade el vigente.[/]" if not a.sin_vigentes else
                                  "[yellow]con --sin-vigentes no se añade nada.[/]"))
        relaciones = set()
        for f in res:
            if f.get("sustituido_por"):
                relacion = (f.get("codigo"), f.get("sustituido_por"), f.get("sustitucion_deducida_de"),
                            f.get("sustitucion_mencion"))
                if relacion not in relaciones:
                    relaciones.add(relacion)
                    c.print(f"  [dim]Regla literal: {relacion[3] or 'sustituye a …'} · "
                            f"detectado en {relacion[2] or 'sin localización'} → "
                            f"{relacion[0]} sustituido por {relacion[1]}[/]")
    if a.explicar:
        c.print("\n[bold]Cómo se combinan las dos listas (Reciprocal Rank Fusion)[/]  "
                "[dim]cada lista da 1/(60 + puesto); se suman. Cuenta el PUESTO, no la puntuación.[/]")
        e = Table(box=None, padding=(0, 1), header_style="bold")
        for col in ("fragmento", "por significado", "por palabras", "suma RRF"):
            e.add_column(col)
        ids = list(dict.fromkeys(sem[:6] + pal[:6]))
        filas = []
        for i in ids:
            ps = sem.index(i) + 1 if i in sem else None
            pp = pal.index(i) + 1 if i in pal else None
            rs = 1 / (60 + ps) if ps else 0.0
            rp = 1 / (60 + pp) if pp else 0.0
            filas.append((rs + rp, i, ps, pp, rs, rp))
        for total, i, ps, pp, rs, rp in sorted(filas, reverse=True):
            e.add_row(b.frags[i]["cita"], f"{ps}º → {rs:.4f}" if ps else "—", f"{pp}º → {rp:.4f}" if pp else "—",
                      Text(f"{total:.4f}", "bold"))
        c.print(e)
    if a.corto:
        return
    c.print()
    for n, f in enumerate(res, 1):
        texto = extracto(f["texto"], palabras_q)
        titulo = f"{n} · {f['cita']} · [{color(f['estado'])}]{f['estado']}[/] · {f['fecha']}"
        if f["anadido"]:
            titulo += " · [green]añadido: es el documento vigente[/]"
        c.print(Panel(resaltar(texto, palabras_q), title=titulo, title_align="left", border_style=color(f["estado"])))
    c.print("[dim]Siguiente: python practica/sesion_2/13_preguntar_documentos.py \"…\" — el modelo responde SOLO con "
            "estos fragmentos, citando.[/dim]")


if __name__ == "__main__":
    main()
