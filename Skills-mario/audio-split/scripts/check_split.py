#!/usr/bin/env python3
"""QA de una división: compara los trozos reales con manifest.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import probe

CHUNK_TOLERANCE = 1.0  # s por trozo
TOTAL_TOLERANCE = 0.5  # s en la suma, por trozo (cada corte puede desviarse ~ un frame)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--max-chunk-seconds", type=float, default=None,
                        help="falla si algún trozo supera esta duración (p. ej. 300)")
    args = parser.parse_args()

    manifest_path = args.output_dir / "manifest.json"
    if not manifest_path.is_file():
        sys.exit("error: no existe {}".format(manifest_path))
    manifest = json.loads(manifest_path.read_text())
    chunks = manifest["chunks"]

    issues = []
    total = 0.0
    for c in chunks:
        path = args.output_dir / c["file"]
        if not path.is_file() or path.stat().st_size == 0:
            issues.append("{}: falta o está vacío".format(c["file"]))
            continue
        real = probe(path)["duration"]
        total += real
        if abs(real - c["duration"]) > CHUNK_TOLERANCE:
            issues.append("{}: dura {:.1f} s y el manifest dice {:.1f} s".format(c["file"], real, c["duration"]))
        if args.max_chunk_seconds and real > args.max_chunk_seconds:
            issues.append("{}: dura {:.1f} s (> {:g})".format(c["file"], real, args.max_chunk_seconds))

    allowed = TOTAL_TOLERANCE * len(chunks)
    if abs(total - manifest["duration"]) > allowed:
        issues.append("suma de trozos {:.1f} s vs original {:.1f} s (tolerancia {:.1f} s)".format(
            total, manifest["duration"], allowed))

    if issues:
        print("FALLO:")
        for issue in issues:
            print(" -", issue)
        sys.exit(1)
    print("OK: {} trozos, suma {:.1f} s vs original {:.1f} s".format(len(chunks), total, manifest["duration"]))


if __name__ == "__main__":
    main()
