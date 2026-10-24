#!/usr/bin/env python3
"""Verifica que final.md dice lo mismo que bruto.md (la extracción automática) y que el Markdown está sano.

Compara las palabras visibles (sin sintaxis Markdown, comentarios ni URLs; uniendo «pala-\\nbra»):
  ERROR (exit 1)  palabras AÑADIDAS que no están en bruto.md (nunca se permiten) y enlaces con URL nueva.
  AVISO           palabras QUITADAS (solo se admiten artefactos como cabeceras/pies/números de página repetidos:
                  hay que justificarlas en la entrega) y contenido MOVIDO (mismo texto en otro orden).
Bloques de transcripción insertados a mano (texto de imágenes, páginas escaneadas) se marcan así y se comparan
con su fichero de origen en vez de con bruto.md:
  <!-- transcripcion: ruta/a/parte.md -->
  …texto transcrito…
  <!-- /transcripcion -->
Texto que markitdown perdió y está en el original se recupera copiándolo de segundo_lector.txt en un bloque
  <!-- original: segundo_lector.txt -->
  …texto copiado literal…
  <!-- /original -->
cuyas palabras deben estar todas en ese fichero.
Sanidad: vacío, bloques de código sin cerrar, tablas con nº de columnas distinto, imágenes en base64.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path
from typing import List

from _md import content_words, parser, signs, text_words, visible_blocks

ORIGINAL = re.compile(r"<!--\s*original:\s*(.+?)\s*-->(.*?)<!--\s*/original\s*-->", re.S)
REGION = re.compile(r"<!--\s*transcripcion:\s*(.+?)\s*-->(.*?)<!--\s*/transcripcion\s*-->", re.S)
LINK = re.compile(r"\]\(\s*<?([^)\s>]+)")


def snippet(words: List[str], a: int, b: int, ctx: int = 4) -> str:
    left = " ".join(words[max(0, a - ctx):a])
    mid = " ".join(words[a:b][:15]) + (" …" if b - a > 15 else "")
    right = " ".join(words[b:b + ctx])
    return "…{} [{}] {}…".format(left, mid, right)


def table_problems(md: str) -> List[str]:
    out, block, start = [], [], 0
    lines = md.split("\n") + [""]
    in_fence = False
    for n, line in enumerate(lines, 1):
        if re.match(r"\s*(```|~~~)", line):
            in_fence = not in_fence
        s = line.strip()
        if not in_fence and s.startswith("|"):
            if not block:
                start = n
            block.append(s)
            continue
        if len(block) >= 2 and re.fullmatch(r"\|(\s*:?-+:?\s*\|)+", block[1].replace(" ", "")):
            counts = [len(re.findall(r"(?<!\\)\|", r)) - 1 for r in block]
            if len(set(counts)) > 1:
                out.append("tabla en la línea {}: filas con distinto nº de columnas {}".format(start, sorted(set(counts))))
        block = []
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", type=Path, help="final.md")
    ap.add_argument("--reference", type=Path, help="bruto.md (extracción automática); sin él solo se revisa la sanidad")
    ap.add_argument("--max-show", type=int, default=12, help="diferencias que se muestran (por defecto 12)")
    args = ap.parse_args()

    if not args.markdown.is_file():
        sys.exit("error: no existe {}".format(args.markdown))
    md = args.markdown.read_text(encoding="utf-8")
    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []

    if not md.strip():
        errors.append("el .md está vacío")
    fences = [l for l in md.split("\n") if re.match(r"\s{0,3}(```|~~~)", l)]
    if len(fences) % 2:
        errors.append("hay un bloque de código sin cerrar (nº impar de ``` / ~~~)")
    errors.extend(table_problems(md))
    if re.search(r"\]\(data:[^)]{200,}", md):
        warnings.append("hay imágenes incrustadas en base64: el PDF/DOCX no las muestra y pesan mucho; pásalas a comentario")
    for t in parser().parse(md):
        if t.type == "html_block" and not re.fullmatch(r"\s*(<!--.*?-->\s*)+", t.content, re.S) and re.search(r">[^<]*\w", t.content):
            warnings.append("bloque HTML con texto (línea {}): el PDF/DOCX no lo muestra; pásalo a Markdown".format(t.map[0] + 1 if t.map else "?"))
    if md.count("<!--") != md.count("-->"):
        errors.append("hay comentarios HTML <!-- sin cerrar: ocultarían texto")

    # Bloques de transcripción: se comparan con su origen y se apartan de la comparación con bruto.md
    body = md
    for m in REGION.finditer(md):
        src = Path(m.group(1))
        if not src.is_absolute():
            src = (args.markdown.parent / src).resolve()
        if not src.is_file():
            errors.append("transcripción insertada con origen inexistente: {}".format(m.group(1)))
            continue
        want, got = content_words(src.read_text(encoding="utf-8")), content_words(m.group(2))
        if want != got:
            errors.append("la transcripción insertada no coincide con {} ({} vs {} palabras)".format(src.name, len(got), len(want)))
        else:
            info.append("transcripción insertada de {} coincide ({} palabras)".format(src.name, len(got)))
        body = body.replace(m.group(0), "\n")

    for m in ORIGINAL.finditer(body):
        src = Path(m.group(1))
        if not src.is_absolute():
            src = (args.markdown.parent / src).resolve()
        if not src.is_file():
            errors.append("bloque <!-- original: … --> con fichero inexistente: {}".format(m.group(1)))
            continue
        extra = Counter(content_words(m.group(2))) - Counter(text_words(src.read_text(encoding="utf-8")))
        if extra:
            errors.append("bloque recuperado de {} con palabras que no están en él: {}".format(src.name, ", ".join(extra)))
        else:
            info.append("texto recuperado de {} ({} palabras): menciónalo en la entrega".format(src.name, len(content_words(m.group(2)))))
        body = body.replace(m.group(0), "\n")

    words = content_words(body)
    info.insert(0, "{} palabras en {}".format(len(words), args.markdown.name))

    if args.reference:
        if not args.reference.is_file():
            sys.exit("error: no existe {}".format(args.reference))
        ref_md = args.reference.read_text(encoding="utf-8")
        ref = content_words(ref_md)
        info.append("{} palabras en {}".format(len(ref), args.reference.name))
        added = Counter(words) - Counter(ref)
        removed = Counter(ref) - Counter(words)
        sm = difflib.SequenceMatcher(None, ref, words, autojunk=False)
        shown_add, shown_del = 0, 0
        for tag, a1, a2, b1, b2 in sm.get_opcodes():
            if tag == "equal":
                continue
            new = [w for w in words[b1:b2] if added[w] > 0]
            gone = [w for w in ref[a1:a2] if removed[w] > 0]
            if new and shown_add < args.max_show:
                errors.append("AÑADIDO (no está en {}): {}".format(args.reference.name, snippet(words, b1, b2)))
                shown_add += 1
            if gone and shown_del < args.max_show:
                warnings.append("QUITADO (estaba en {}): {}".format(args.reference.name, snippet(ref, a1, a2)))
                shown_del += 1
        if sum(added.values()):
            errors.insert(0, "{} palabra(s) añadidas que no están en la extracción: {}".format(
                sum(added.values()), ", ".join(w for w, _ in added.most_common(30))))
        if sum(removed.values()):
            warnings.insert(0, "{} palabra(s) quitadas: {} — solo valen artefactos (cabeceras/pies/números de página repetidos); "
                               "justifícalas en la entrega".format(sum(removed.values()), ", ".join(w for w, _ in removed.most_common(30))))
        if not added and not removed and words != ref:
            moved = sum(1 for op in sm.get_opcodes() if op[0] != "equal")
            warnings.append("MOVIDO: mismas palabras en otro orden ({} tramo(s)); correcto si reordenaste columnas/tablas de un PDF "
                            "según la vista de página, si no, revísalo".format(moved))
        s_new, s_ref = signs("\n".join(visible_blocks(body, False))), signs("\n".join(visible_blocks(ref_md, False)))
        if s_new != s_ref:
            fmt = lambda c: " ".join("{}×{}".format(k, v) for k, v in c.most_common(15)) or "—"
            warnings.append("SIGNOS distintos de {} (de más: {}; de menos: {}): correcto si es sintaxis que pasó a formato "
                            "(p. ej. «1.» → lista), si no, revísalo".format(args.reference.name, fmt(s_new - s_ref), fmt(s_ref - s_new)))
        ref_links = Counter(LINK.findall(ref_md))
        new_links = [u for u in LINK.findall(body) if u not in ref_links]
        for u in new_links[:10]:
            errors.append("enlace con URL que no está en la extracción: {}".format(u))
        if not added and not removed and words == ref:
            info.append("mismas palabras y en el mismo orden que {}".format(args.reference.name))

    print("; ".join(info))
    for w in warnings:
        print("AVISO:", w)
    if errors:
        print("FALLO:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("OK" + (" (con {} aviso(s))".format(len(warnings)) if warnings else ""))


if __name__ == "__main__":
    main()
