#!/usr/bin/env python3
"""Monta trabajo/fuente/: un fichero de texto por unidad, numerado en el orden final del documento.

Esa carpeta es la entrada de text-resume (collect_texts.py). Exige que cada unidad esté lista:
audios transcritos (process_audio.py), imágenes con trabajo/imagenes/transcripcion.md (join_parts.py).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_")[:40] or "fuente"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("work_dir", type=Path, help="carpeta trabajo/")
    ap.add_argument("--order", help="orden entre fuentes (por defecto, el de inventario.json)")
    args = ap.parse_args()

    inv = json.loads((args.work_dir / "inventario.json").read_text())
    units = {u["id"]: u for u in inv["units"]}
    tokens = [t.strip() for t in (args.order.split(",") if args.order else inv["sources_order"]) if t.strip()]
    kind_of = {"audio": "audio", "images": "images", "text": "text"}
    seq, seen = [], set()
    for t in tokens:
        ids = [u["id"] for u in inv["units"] if u["kind"] == kind_of[t]] if t in kind_of else [t]
        for i in ids:
            if i not in units:
                sys.exit("error: unidad desconocida «{}»".format(i))
            if i not in seen:
                seen.add(i)
                seq.append(i)
    rest = [u["id"] for u in inv["units"] if u["id"] not in seen]
    if rest:
        sys.exit("error: el orden no incluye estas unidades (se perdería su contenido): " + ", ".join(rest))

    out = args.work_dir / "fuente"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    problems = []
    for n, uid in enumerate(seq, 1):
        u = units[uid]
        if u["kind"] == "audio":
            src = args.work_dir / "audio" / "{}_{}".format(uid, Path(u["path"]).stem) / "transcripcion" / "transcripcion_completa.txt"
            name = "{:02d}_audio_{}.txt".format(n, slug(Path(u["path"]).stem))
        elif u["kind"] == "images":
            src = args.work_dir / "imagenes" / "transcripcion.md"
            name = "{:02d}_imagenes.md".format(n)
        else:
            src = Path(u["path"])
            name = "{:02d}_texto_{}{}".format(n, slug(src.stem), src.suffix.lower())
        if not src.is_file() or not src.read_text(encoding="utf-8", errors="replace").strip():
            problems.append("{}: falta o está vacío {}".format(uid, src))
            continue
        shutil.copyfile(src, out / name)
        print("{:>2}. {}  ←  {}".format(n, name, src))
    if problems:
        print("FALLO:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    (args.work_dir / "orden_final.txt").write_text("\n".join(sorted(p.name for p in out.iterdir())) + "\n")
    print("\nFuente lista en {} ({} fichero(s)).".format(out, len(seq)))
    print("Siguiente (text-resume), pasando el orden ya confirmado; sin --files-from su heurística puede marcar como ambiguos"
          " nombres con números del original:\n  python3 {}/collect_texts.py {} --output-dir {} --files-from {}".format(
              "../text-resume/scripts", out, args.work_dir / "resumen", args.work_dir / "orden_final.txt"))


if __name__ == "__main__":
    main()
