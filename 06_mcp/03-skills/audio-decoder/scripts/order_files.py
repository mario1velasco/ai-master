#!/usr/bin/env python3
"""Lista los audios de un directorio en el orden propuesto y avisa si el orden es dudoso.

Código de salida: 0 = orden claro, 3 = ambiguo (hay que preguntar al usuario), 1 = error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _ordering import find_audio, order_files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--json", action="store_true", help="salida JSON")
    args = parser.parse_args()
    if not args.directory.is_dir():
        sys.exit("error: {} no es un directorio".format(args.directory))
    files = find_audio(args.directory)
    if not files:
        sys.exit("error: no hay audios (.aac .m4a .mp3 .wav .flac .opus .ogg) en {}".format(args.directory))

    result = order_files(files)
    if args.json:
        print(json.dumps({"files": [f.name for f in result["files"]], "ambiguities": result["ambiguities"],
                          "warnings": result["warnings"]}, ensure_ascii=False, indent=2))
    else:
        for i, f in enumerate(result["files"], 1):
            print("{:>3}. {}".format(i, f.name))
        for w in result["warnings"]:
            print("AVISO:", w)
        for a in result["ambiguities"]:
            print("AMBIGUO:", a)
    sys.exit(3 if result["ambiguities"] else 0)


if __name__ == "__main__":
    main()
