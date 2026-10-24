#!/usr/bin/env python3
"""Une las transcripciones por imagen (partes/NN_<nombre>.md) en un único .md, en el orden de lectura.json.

Entre imágenes añade un separador `---` y un comentario HTML `<!-- imagen N: nombre -->` (no se ve ni añade palabras).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("work_dir", type=Path, help="carpeta de trabajo con lectura.json y partes/")
    ap.add_argument("--output", type=Path, help="por defecto <work_dir>/transcripcion.md")
    args = ap.parse_args()

    plan_path = args.work_dir / "lectura.json"
    if not plan_path.is_file():
        sys.exit("error: falta {} (ejecuta prepare_images.py)".format(plan_path))
    images = json.loads(plan_path.read_text())["images"]
    chunks, missing = [], []
    for e in images:
        part = args.work_dir / "partes" / "{:02d}_{}.md".format(e["order"], Path(e["image"]).stem)
        if not part.is_file() or not part.read_text().strip():
            missing.append(part.name)
            continue
        chunks.append("<!-- imagen {}: {} -->\n\n{}".format(e["order"], e["image"], part.read_text().strip()))
    if missing:
        sys.exit("error: faltan o están vacías estas partes en {}/partes: {}".format(args.work_dir, ", ".join(missing)))

    out = args.output or args.work_dir / "transcripcion.md"
    out.write_text("\n\n---\n\n".join(chunks) + "\n", encoding="utf-8")
    print("Creado {} ({} imagen/es)".format(out, len(chunks)))


if __name__ == "__main__":
    main()
