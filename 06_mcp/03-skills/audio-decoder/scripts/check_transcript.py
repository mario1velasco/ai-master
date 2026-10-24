#!/usr/bin/env python3
"""QA de una transcripción: partes completas, orden correcto en el .txt final y densidad de texto plausible."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MIN_WORDS_PER_MIN = 20  # por debajo, probablemente hubo voz sin transcribir (o es música/silencio)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="carpeta 'transcripcion' generada por transcribe_audio.py")
    args = parser.parse_args()

    manifest_path = args.output_dir / "manifest.json"
    full_path = args.output_dir / "transcripcion_completa.txt"
    if not manifest_path.is_file() or not full_path.is_file():
        sys.exit("error: faltan manifest.json o transcripcion_completa.txt en {}".format(args.output_dir))
    manifest = json.loads(manifest_path.read_text())
    full = full_path.read_text()

    issues, warnings = [], []
    cursor = 0
    for f in manifest["files"]:
        part_txt = args.output_dir / "partes" / "{:03d}_{}.txt".format(f["order"], Path(f["file"]).stem)
        if not part_txt.is_file():
            issues.append("{}: falta la parte".format(f["file"]))
            continue
        text = part_txt.read_text().strip()
        if not text:
            warnings.append("{}: transcripción vacía".format(f["file"]))
            continue
        pos = full.find(text[:200], cursor)  # cada parte debe aparecer después de la anterior
        if pos < 0:
            issues.append("{}: no aparece (o aparece desordenada) en transcripcion_completa.txt".format(f["file"]))
        else:
            cursor = pos + 1
        minutes = f["duration"] / 60
        if minutes >= 1 and f["words"] / minutes < MIN_WORDS_PER_MIN:
            warnings.append("{}: solo {:.0f} palabras/min (¿voz sin detectar?)".format(f["file"], f["words"] / minutes))

    for w in warnings:
        print("AVISO:", w)
    if issues:
        print("FALLO:")
        for i in issues:
            print(" -", i)
        sys.exit(1)
    print("OK: {} archivos en orden, {} palabras, {:.0f} min de audio, idioma {}".format(
        len(manifest["files"]), sum(f["words"] for f in manifest["files"]), manifest["total_duration"] / 60, manifest["language"]))


if __name__ == "__main__":
    main()
