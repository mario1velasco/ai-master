"""Práctica 2 (b) · El índice ampliado: los 51 fragmentos de la sesión 2 (mismos id) + las páginas de junio, con su ficha.

Del paso anterior (08_leer_documentos.py) salen las lecturas de PaddleOCR-VL guardadas. Aquí:
    1. se limpian (tablas HTML → filas «| a | b |», sin logotipo ni número de página; el pie se guarda: lleva el código),
    2. se une la fila de tabla partida entre la pág. 7 y la 8 (la cola «tarde. La firma…» vuelve a ENT-06-012),
    3. cada página recibe su FICHA con reglas de este formato: código + VERSIÓN, estado, fecha, título, responsable…
       La versión entra en la clave: «LOG-2026-06 v0.9» (el borrador del anexo) es otro documento que «… v1.1»,
       y la pág. 1 dice «sustituye a LOG-2026-06 v0.9» → el anexo queda SUSTITUIDO.
    4. y un campo nuevo, LECTURA: con qué se leyó, «sin revisar», y cuántas cifras se pudieron comprobar con la
       capa de texto del PDF (en el escaneado, ninguna; en el gráfico, sus 12 valores solo están en la imagen).

Uso:
    python practica/sesion_3/09_indice_junio.py                    # crea corpus e índice ampliados (~10 s)
    python practica/sesion_3/09_indice_junio.py --ver 57           # la ficha de un fragmento y de dónde sale cada campo
    python practica/sesion_3/09_indice_junio.py --buscar "¿Cuántos pares aceptó MAD-MAL de NEGRO_41 en junio?"
    python practica/sesion_3/09_indice_junio.py --sin-indice       # solo el corpus (sin embeddings)

Salida: practica/sesion_3/rag/corpus_ampliado.jsonl e indice_ampliado_bge-m3.duckdb
El asistente (API, flujo y Open WebUI) usa este índice si existe. El de la sesión 2 no se toca.
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
from rich.table import Table  # noqa: E402
from rich.text import Text  # noqa: E402

from asistente import config, lectura  # noqa: E402
from asistente.sesion2 import buscar, indice  # noqa: E402

c = Console()
COLOR = {"aprobado": "green", "sustituido": "red", "registro": "cyan", "abierta (pendiente)": "yellow"}


def construir() -> list[dict]:
    base = indice.cargar_corpus()                       # la sesión 2, tal cual: sus id no cambian
    siguiente = max(f["id"] for f in base) + 1
    junio = lectura.fichas([lectura.lectura_guardada(a) for a in lectura.ALIAS])
    for i, f in enumerate(junio):
        f["id"] = siguiente + i
        f["cita"] = f"{f['fuente']} · pág. {f['pagina']}"
        f["texto_indexado"] = lectura.texto_indexado(f)
    return base + junio


def tabla(frags: list[dict]) -> None:
    t = Table(title="Fragmentos nuevos (junio): una página = un fragmento", title_justify="left", header_style="bold")
    for col in ("id", "cita", "código", "estado", "fecha", "lectura"):
        t.add_column(col, overflow="fold")
    for f in frags:
        if not f.get("lectura"):
            continue
        rev = f["revision"]
        aviso = ("sin capa de texto" if not rev["comprobable"] else
                 f"{len(rev['solo_en_lectura'])} cifras solo en la imagen" if rev["solo_en_lectura"] else
                 f"{rev['en_capa']}/{rev['cifras']} cifras comprobadas")
        t.add_row(str(f["id"]), f["cita"].replace("_DropLab_", " "), f["codigo"],
                  Text(f["estado"] + (f" → {f['sustituido_por']}" if f.get("sustituido_por") else ""),
                       style=COLOR.get(f["estado"], "")), f["fecha"],
                  Text(aviso, style="green" if "comprobadas" in aviso else "yellow"))
    c.print(t)


def ver(frags: list[dict], i: int) -> None:
    f = next((x for x in frags if x["id"] == i), None)
    if f is None:
        raise SystemExit(f"No hay fragmento {i} (0–{len(frags) - 1}).")
    t = Table(title=f"Ficha del fragmento {i}", title_justify="left", header_style="bold", show_lines=False)
    for col in ("campo", "valor", "de dónde sale"):
        t.add_column(col, overflow="fold")
    origen = f.get("origen") or {}
    for campo in ("cita", "tipo", "titulo", "codigo", "seccion", "fecha", "estado", "sustituido_por", "responsable", "lectura"):
        t.add_row(campo, str(f.get(campo) or "—"), origen.get(campo, "regla de 10_corpus.py (sesión 2)" if not f.get("lectura") else ""))
    c.print(t)
    if f.get("sustitucion_mencion"):
        c.print(f"[red]SUSTITUIDO[/]: «{f['sustitucion_mencion']}» ({f['sustitucion_deducida_de']})")
    c.print(Panel(f["texto_indexado"], title="texto que se indexa (cabecera + texto)", title_align="left"))


def buscar_vista(pregunta: str, k: int) -> None:
    b = buscar.Buscador(ruta=config.INDICE_AMPLIADO)
    t = Table(title=f"Búsqueda híbrida en el índice ampliado: «{pregunta}»", title_justify="left", header_style="bold")
    for col in ("#", "id", "cita", "estado", "lectura"):
        t.add_column(col, overflow="fold")
    for n, f in enumerate(b.buscar(pregunta, "hibrida", k), 1):
        t.add_row(str(n) if not f["anadido"] else "+", str(f["id"]), f["cita"],
                  Text(f["estado"] + (f" → {f['sustituido_por']}" if f.get("sustituido_por") else ""),
                       style=COLOR.get(f["estado"], "")), (f.get("lectura") or "—")[:60])
    c.print(t)
    c.print("[dim]«+»: añadido por la regla de versiones (sale un sustituido → se añade el vigente).[/]")


def main() -> None:
    ap = argparse.ArgumentParser(description="Corpus e índice ampliados con los PDF de junio.")
    ap.add_argument("--ver", type=int, help="La ficha de un fragmento.")
    ap.add_argument("--buscar", help="Buscar en el índice ampliado.")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--sin-indice", action="store_true", help="Solo el corpus, sin calcular embeddings.")
    a = ap.parse_args()
    if a.buscar:
        if not config.INDICE_AMPLIADO.exists():
            raise SystemExit("Falta el índice ampliado: python practica/sesion_3/09_indice_junio.py")
        buscar_vista(a.buscar, a.k)
        return
    frags = construir()
    if a.ver is not None:
        ver(frags, a.ver)
        return
    config.RAG3.mkdir(parents=True, exist_ok=True)
    with config.CORPUS_AMPLIADO.open("w", encoding="utf-8") as fh:
        for f in frags:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
    tabla(frags)
    c.print(f"Corpus: {len(frags)} fragmentos ({sum(1 for f in frags if f.get('lectura'))} de junio) → "
            f"{config.CORPUS_AMPLIADO.relative_to(config.ROOT)}")
    if not a.sin_indice:
        r = indice.crear(indice.MODELO, frags=frags, ruta=config.INDICE_AMPLIADO)
        c.print(f"Índice: {r['fragmentos']} vectores de {r['dimensiones']} dimensiones ({r['modelo']}) en {r['segundos']} s "
                f"→ {config.INDICE_AMPLIADO.relative_to(config.ROOT)}")
        c.print("[dim]Si la API está en marcha, reiníciala para que cargue el índice nuevo.[/]")


if __name__ == "__main__":
    main()
