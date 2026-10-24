#!/usr/bin/env python3
"""Verificación final y entrega: comprueba .md ↔ fuente ↔ PDF y deja los entregables en la carpeta de salida.

Entregables: resumen.md, resumen.pdf (idéntico al .md), descripcion.md y transcripciones/ (la fuente en orden).
Falla (exit 1) si falta algo o el PDF no coincide con el .md.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from _env import TEXT_RESUME, venv_python


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("work_dir", type=Path, help="carpeta trabajo/")
    ap.add_argument("--summary-dir", type=Path, help="carpeta con resumen.md/descripcion.md/resumen.pdf (por defecto trabajo/resumen)")
    args = ap.parse_args()

    out = args.work_dir.parent
    sdir = args.summary_dir or args.work_dir / "resumen"
    fuente = args.work_dir / "fuente"
    missing = [str(p) for p in (sdir / "resumen.md", sdir / "descripcion.md", sdir / "resumen.pdf", fuente) if not p.exists()]
    if missing:
        sys.exit("error: falta: " + ", ".join(missing))
    if (sdir / "resumen.md").stat().st_mtime > (sdir / "resumen.pdf").stat().st_mtime:
        sys.exit("error: resumen.md es más reciente que resumen.pdf: regenera el PDF (md_to_pdf.py)")

    py = venv_python()
    ok = True
    for md in ("resumen.md", "descripcion.md"):
        cmd = [py, str(TEXT_RESUME / "check_summary.py"), str(sdir / md), "--source", str(fuente)]
        if md == "resumen.md":
            cmd += ["--pdf", str(sdir / "resumen.pdf")]
        print("\n=== {} ===".format(md), flush=True)
        ok &= subprocess.run(cmd).returncode == 0
    if not ok:
        sys.exit("FALLO en la verificación (ver arriba)")

    for name in ("resumen.md", "resumen.pdf", "descripcion.md"):
        shutil.copyfile(sdir / name, out / name)
    tr = out / "transcripciones"
    if tr.exists():
        shutil.rmtree(tr)
    shutil.copytree(fuente, tr)
    print("\nEntregables en {}:".format(out))
    for p in sorted(out.iterdir()):
        if p.name != "trabajo":
            print("  -", p.name + ("/" if p.is_dir() else ""))
    print("Recuerda revisar a mano los AVISO de OMITIDO?/INVENTADO? contra la fuente: son heurísticas.")


if __name__ == "__main__":
    main()
