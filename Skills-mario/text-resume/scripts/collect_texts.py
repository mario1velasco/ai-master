#!/usr/bin/env python3
"""Prepara la lectura: ordena los textos, crea una copia de trabajo y propone un plan de lectura por trozos.

Entrada: un fichero de texto o un directorio con ficheros .txt/.md ordenados.
Salida: <output-dir>/texto_trabajo.txt (todos los textos, en orden, con cabecera por fichero y líneas
cortas para que la herramienta Read no las trunque) y el plan de lectura en pantalla y en lectura.json.

Código de salida: 0 = ok, 3 = orden ambiguo (hay que preguntar al usuario), 1 = error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from pathlib import Path
from typing import List

from _ordering import find_texts, order_files

MAX_LINE_CHARS = 1200  # Read trunca líneas largas (~2000); la copia de trabajo parte las que superen esto


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def wrap_long_lines(text: str) -> List[str]:
    lines: List[str] = []
    for line in text.splitlines():
        if len(line) <= MAX_LINE_CHARS:
            lines.append(line)
        else:  # solo cambia dónde cae el salto de línea, no el contenido
            lines.extend(textwrap.wrap(line, MAX_LINE_CHARS, break_long_words=True, break_on_hyphens=False))
    return lines


def words(s: str) -> int:
    return len(re.findall(r"\w+", s))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path, help="fichero de texto o directorio con textos")
    p.add_argument("--output-dir", type=Path, required=True, help="carpeta de trabajo/salida (se crea)")
    p.add_argument("--files-from", type=Path, help="fichero con un nombre por línea, en el orden confirmado por el usuario")
    p.add_argument("--accept-order", action="store_true", help="aceptar un orden ambiguo (solo si el usuario lo confirmó)")
    p.add_argument("--chunk-words", type=int, default=2500, help="palabras por trozo de lectura (por defecto 2500)")
    args = p.parse_args()

    if not args.input.exists():
        sys.exit("error: no existe {}".format(args.input))
    if args.input.is_file():
        files = [args.input]
    elif args.files_from:
        names = [l.strip() for l in args.files_from.read_text().splitlines() if l.strip()]
        files = [args.input / n for n in names]
        missing = [str(f) for f in files if not f.is_file()]
        if missing:
            sys.exit("error: no existen: " + ", ".join(missing))
    else:
        found = find_texts(args.input)
        if not found:
            sys.exit("error: no hay ficheros .txt/.md en {}".format(args.input))
        result = order_files(found)
        if result["ambiguities"] and not args.accept_order:
            print("El orden es ambiguo; pregunta al usuario y usa --files-from (o --accept-order):", file=sys.stderr)
            for a in result["ambiguities"]:
                print(" -", a, file=sys.stderr)
            print("Orden alfabético/natural propuesto: " + ", ".join(f.name for f in result["files"]), file=sys.stderr)
            sys.exit(3)
        for w in result["warnings"]:
            print("AVISO:", w)
        files = result["files"]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    work: List[str] = []
    stats = []
    for i, f in enumerate(files, 1):
        text = read_text(f)
        if not text.strip():
            print("AVISO: {} está vacío".format(f.name))
        if len(files) > 1:
            work.append("=== [{}/{}] {} ===".format(i, len(files), f.name))
        start = len(work) + 1
        work.extend(wrap_long_lines(text))
        stats.append({"order": i, "file": f.name, "words": words(text), "chars": len(text),
                      "first_line": start, "last_line": len(work)})
        if len(files) > 1:
            work.append("")
    work_path = args.output_dir / "texto_trabajo.txt"
    work_path.write_text("\n".join(work) + "\n")

    # Plan de lectura: trozos consecutivos de ~chunk_words palabras, cortando entre líneas
    plan, start, acc = [], 1, 0
    for n, line in enumerate(work, 1):
        acc += words(line)
        if acc >= args.chunk_words:
            plan.append({"chunk": len(plan) + 1, "from_line": start, "to_line": n, "words": acc})
            start, acc = n + 1, 0
    if start <= len(work):
        plan.append({"chunk": len(plan) + 1, "from_line": start, "to_line": len(work), "words": acc})

    total = sum(s["words"] for s in stats)
    (args.output_dir / "lectura.json").write_text(json.dumps(
        {"input": str(args.input.resolve()), "work_file": str(work_path.resolve()), "files": stats,
         "total_words": total, "plan": plan}, ensure_ascii=False, indent=2) + "\n")

    print("Orden ({} fichero(s)):".format(len(files)))
    for s in stats:
        print("  {:>3}. {}  ({} palabras)".format(s["order"], s["file"], s["words"]))
    print("\nTotal: {} palabras (~{} tokens)".format(total, int(total * 1.5)))
    print("Copia de trabajo: {}  ({} líneas)".format(work_path, len(work)))
    print("\nPlan de lectura (lee TODOS los trozos, en orden, con Read offset/limit):")
    for c in plan:
        print("  trozo {:>2}: offset={} limit={}  ({} palabras)".format(
            c["chunk"], c["from_line"], c["to_line"] - c["from_line"] + 1, c["words"]))


if __name__ == "__main__":
    main()
