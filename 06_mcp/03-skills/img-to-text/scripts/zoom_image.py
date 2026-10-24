#!/usr/bin/env python3
"""Recorta y amplía una zona de una imagen para releer con calma una palabra dudosa (se mira con Read)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("error: falta Pillow. Instálalo en un venv: python3 -m pip install -r requirements.txt")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", type=Path, help="normalmente un trozo de <work>/tiles/")
    ap.add_argument("--box", required=True, help="x0,y0,x1,y1 en píxeles del trozo (check_transcription.py los indica)")
    ap.add_argument("--scale", type=float, default=3.0)
    ap.add_argument("--pad", type=int, default=25, help="margen extra alrededor de la caja (px)")
    ap.add_argument("--output", type=Path, help="por defecto <imagen>_zoom_<x0>_<y0>.png junto a la imagen (distinto por caja)")
    args = ap.parse_args()

    try:
        x0, y0, x1, y1 = (int(float(v)) for v in args.box.split(","))
    except ValueError:
        sys.exit("error: --box debe ser x0,y0,x1,y1")
    img = Image.open(args.image).convert("RGB")
    box = (max(x0 - args.pad, 0), max(y0 - args.pad, 0), min(x1 + args.pad, img.width), min(y1 + args.pad, img.height))
    crop = img.crop(box)
    crop = crop.resize((round(crop.width * args.scale), round(crop.height * args.scale)), Image.LANCZOS)
    crop = ImageOps.autocontrast(crop, cutoff=1)
    out = args.output or args.image.with_name("{}_zoom_{}_{}.png".format(args.image.stem, x0, y0))
    crop.save(out)
    print(out)


if __name__ == "__main__":
    main()
