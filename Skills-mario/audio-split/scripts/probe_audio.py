#!/usr/bin/env python3
"""Muestra duración, códec y nº de trozos previstos de un audio."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from _common import fmt_time, probe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--chunk-seconds", type=float, default=240.0)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit("error: no existe {}".format(args.input))

    info = probe(args.input)
    chunks = max(1, math.ceil(info["duration"] / args.chunk_seconds))
    print("Archivo:        {}".format(args.input))
    print("Duración:       {} ({:.1f} s)".format(fmt_time(info["duration"]), info["duration"]))
    print("Códec:          {}".format(info["codec"]))
    print("Bitrate:        {} kbit/s".format(info["bit_rate"] // 1000))
    print("Sample rate:    {} Hz, {} canal(es)".format(info["sample_rate"], info["channels"]))
    print("Trozos previstos (~{:g} s): {}".format(args.chunk_seconds, chunks))


if __name__ == "__main__":
    main()
