#!/usr/bin/env python3
"""Comprueba que un .pdf o .docx generado con md_to_pdf.py / md_to_docx.py dice exactamente lo mismo que su .md.

PDF: texto extraído con pypdf (sin el pie «pág. N»), frente a las palabras visibles del .md con los números de las
listas numeradas (el PDF los imprime como texto). DOCX: párrafos y tablas en el orden del cuerpo (python-docx),
frente a las palabras visibles sin esos números (en Word son numeración automática).
Mismas palabras en el mismo orden → OK. Mismas palabras en otro orden (celdas largas de tablas que el extractor de
PDF intercala) → OK con AVISO. Cualquier palabra de más o de menos → FALLO (exit 1).
También se comparan los signos (€ % « » -- …): deben ser los mismos; en el PDF se descuentan las viñetas y el punto
que dibuja tras cada número de lista.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path
from typing import List

from _md import WORD, nfc, ordered_items, plain_tokens, signs, visible_blocks

FOOTER = re.compile(r"^pág\. \d+$")


def pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("error: falta pypdf. Ejecuta desde la raíz del repo: python3 scripts/setup_env.py")
    lines = []
    for page in PdfReader(str(path)).pages:
        lines.extend(l for l in (page.extract_text() or "").splitlines() if not FOOTER.match(l.strip()))
    return "\n".join(lines)


def docx_text(path: Path) -> str:
    try:
        import docx
    except ImportError:
        sys.exit("error: falta python-docx. Ejecuta desde la raíz del repo: python3 scripts/setup_env.py")
    out: List[str] = []

    def walk(container):
        for block in container.iter_inner_content():
            if hasattr(block, "rows"):
                for row in block.rows:
                    seen = set()
                    for cell in row.cells:
                        if id(cell._tc) in seen:  # celdas combinadas se repiten
                            continue
                        seen.add(id(cell._tc))
                        walk(cell)
            else:
                out.append(block.text)
    walk(docx.Document(str(path)))
    return "\n".join(out)


def compare(want: List[str], got: List[str], label: str) -> tuple:
    if got == want:
        return [], []
    if Counter(got) == Counter(want):
        return [], ["{}: mismas palabras en otro orden (normal en tablas con celdas de varias líneas); revisa a ojo".format(label)]
    sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
    issues = ["{} no coincide con el .md ({} vs {} palabras):".format(label, len(got), len(want))]
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag != "equal":
            issues.append("  {}: .md «{}» ↔ {} «{}» (palabra nº {})".format(
                tag, " ".join(want[a1:a2][:12]), label, " ".join(got[b1:b2][:12]), a1))
        if len(issues) >= 9:
            break
    return issues, []


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("outputs", nargs="+", type=Path, help="ficheros .pdf y/o .docx generados a partir del .md")
    args = ap.parse_args()
    if not args.markdown.is_file():
        sys.exit("error: no existe {}".format(args.markdown))
    md = args.markdown.read_text(encoding="utf-8")
    errors: List[str] = []
    warnings: List[str] = []
    for out in args.outputs:
        if not out.is_file():
            errors.append("no existe {}".format(out))
            continue
        if out.stat().st_mtime < args.markdown.stat().st_mtime:
            errors.append("{} es más antiguo que {}: regenéralo".format(out.name, args.markdown.name))
        ext = out.suffix.lower()
        want_signs = signs("\n".join(visible_blocks(md, list_numbers=False)))
        if ext == ".pdf":
            text = pdf_text(out)
            e, w = compare(plain_tokens(md, list_numbers=True), WORD.findall(nfc(text)), out.name)
            want_signs["."] += ordered_items(md)  # «1.» de las listas numeradas
        elif ext == ".docx":
            text = docx_text(out)
            e, w = compare(plain_tokens(md, list_numbers=False), WORD.findall(nfc(text)), out.name)
        else:
            sys.exit("error: formato no soportado: {}".format(out))
        got_signs = signs(text)
        if got_signs != want_signs:
            plus, minus = got_signs - want_signs, want_signs - got_signs
            e.append("{}: signos distintos del .md (de más: {}; de menos: {})".format(
                out.name, " ".join("{}×{}".format(k, v) for k, v in plus.items()) or "—",
                " ".join("{}×{}".format(k, v) for k, v in minus.items()) or "—"))
        errors.extend(e)
        warnings.extend(w)
        if not e:
            print("{}: coincide con {} ({} palabras)".format(out.name, args.markdown.name, len(plain_tokens(md))))
    for w in warnings:
        print("AVISO:", w)
    if errors:
        print("FALLO:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
