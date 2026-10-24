#!/usr/bin/env python3
"""Prepara las imágenes para leerlas: orden, orientación, legibilidad y troceado de imágenes altas.

Entrada: una o varias imágenes y/o un directorio. Con varias rutas explícitas se respeta el orden dado;
con un directorio se ordena por número (orden natural) y, si es dudoso, se detiene (exit 3) para preguntar.
Salida: <output-dir>/tiles/*.png (lo que hay que mirar, a resolución nativa) y <output-dir>/lectura.json.

Por qué trocear: las herramientas de visión reducen las imágenes grandes (~1500 px de lado largo);
en una captura alta el texto pequeño queda ilegible. Los trozos conservan la resolución y se solapan un
poco, cortando donde hay un hueco en blanco para no partir líneas de texto.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from _ordering import IMAGE_EXTS, find_images, order_files

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("error: falta Pillow. Instálalo en un venv: python3 -m pip install -r requirements.txt")


def load_rgb(path: Path) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)  # respeta la rotación guardada por el móvil/escáner
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))  # transparencia -> fondo blanco
        img = Image.alpha_composite(bg, img)
    return img.convert("RGB")


def ink_per_row(img: Image.Image) -> List[float]:
    """Fracción de 'tinta' (0-255) de cada fila: píxeles que contrastan con el fondo (detecta fondo oscuro)."""
    g = ImageOps.grayscale(img)
    col = g.resize((1, g.height), Image.BOX)
    means = list(getattr(col, "get_flattened_data", col.getdata)())
    if sorted(means)[len(means) // 2] < 128:  # fondo oscuro (modo noche): la tinta es lo claro
        g = ImageOps.invert(g)
    ink = g.point(lambda v: 255 if v < 170 else 0).resize((1, g.height), Image.BOX)
    return list(getattr(ink, "get_flattened_data", ink.getdata)())


_ENGINE = None


def ocr_score(img: Image.Image) -> float:
    """Texto legible que encuentra el OCR (nº de caracteres ponderado por confianza)."""
    global _ENGINE
    import logging
    import numpy as np
    from rapidocr import RapidOCR
    if _ENGINE is None:
        logging.getLogger("RapidOCR").setLevel(logging.ERROR)
        _ENGINE = RapidOCR(params={"Global.log_level": "error"})
    res = _ENGINE(np.array(img))
    return sum(len(t) * float(s) for t, s in zip(res.txts or [], res.scores or []) if float(s) > 0.6)


def auto_rotation(img: Image.Image) -> int:
    """Grados (0/90/180/270, sentido antihorario de PIL) que hay que girar la imagen para que el texto quede horizontal."""
    small = img.copy()
    small.thumbnail((1000, 1000))
    scores = {a: ocr_score(small.rotate(a, expand=True)) for a in (0, 90, 270, 180)}
    best = max(scores, key=scores.get)
    # solo se gira si la mejora es clara (evita girar imágenes con poco texto por ruido del OCR)
    return best if scores[best] > scores[0] * 1.5 + 10 else 0


def cut_points(img: Image.Image, tile_h: int, overlap: int, window: int = 140) -> List[int]:
    """Filas de corte: cerca de cada múltiplo de tile_h, la fila sin tinta más próxima (no parte líneas de texto)."""
    h = img.height
    if h <= tile_h * 1.15:
        return []
    ink = ink_per_row(img)
    quiet_limit = 255 * 1.5 / img.width  # ≤ ~1-2 píxeles oscuros en la fila
    cuts, target = [], tile_h
    while target < h - overlap * 2:
        lo, hi = max(target - window, cuts[-1] + overlap * 2 if cuts else 1), min(target + window, h - 1)
        quiet = [y for y in range(lo, hi) if ink[y] <= quiet_limit]
        best = min(quiet, key=lambda y: abs(y - target)) if quiet else min(range(lo, hi), key=lambda y: (ink[y], abs(y - target)))
        cuts.append(best)
        target = best + tile_h - overlap
    return cuts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inputs", nargs="+", type=Path, help="imágenes y/o un directorio")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--files-from", type=Path, help="fichero con un nombre por línea (orden confirmado) para el directorio dado")
    ap.add_argument("--accept-order", action="store_true", help="aceptar un orden ambiguo (solo si el usuario lo confirmó)")
    ap.add_argument("--tile-height", type=int, default=1400, help="alto máximo de cada trozo (px)")
    ap.add_argument("--overlap", type=int, default=120, help="solape entre trozos (px)")
    ap.add_argument("--max-width", type=int, default=1500, help="ancho máximo; si es mayor se reduce")
    ap.add_argument("--min-width", type=int, default=900, help="ancho mínimo; si es menor se amplía (hasta x3)")
    ap.add_argument("--rotate", default="auto", choices=["auto", "0", "90", "180", "270"],
                    help="giro antihorario a aplicar (por defecto auto: el OCR elige la orientación con más texto legible)")
    ap.add_argument("--enhance", action="store_true", help="autocontraste (texto desvaído o fondos grises)")
    args = ap.parse_args()

    for p in args.inputs:
        if not p.exists():
            sys.exit("error: no existe {}".format(p))

    ordered_note = ""
    if len(args.inputs) == 1 and args.inputs[0].is_dir():
        d = args.inputs[0]
        if args.files_from:
            names = [l.strip() for l in args.files_from.read_text().splitlines() if l.strip()]
            files = [d / n for n in names]
            missing = [str(f) for f in files if not f.is_file()]
            if missing:
                sys.exit("error: no existen: " + ", ".join(missing))
        else:
            found = find_images(d)
            if not found:
                sys.exit("error: no hay imágenes en {}".format(d))
            result = order_files(found)
            if result["ambiguities"] and not args.accept_order:
                print("El orden es ambiguo; pregunta al usuario y usa --files-from (o --accept-order):", file=sys.stderr)
                for a in result["ambiguities"]:
                    print(" -", a, file=sys.stderr)
                print("Orden propuesto: " + ", ".join(f.name for f in result["files"]), file=sys.stderr)
                sys.exit(3)
            for w in result["warnings"]:
                print("AVISO:", w)
            files = result["files"]
    else:
        files = [f for p in args.inputs for f in (find_images(p) if p.is_dir() else [p])]
        ordered_note = "Orden: el de las rutas indicadas."
    bad = [f for f in files if f.suffix.lower() not in IMAGE_EXTS]
    if bad:
        sys.exit("error: formato no soportado: " + ", ".join(str(b) for b in bad))

    tiles_dir = args.output_dir / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    for old in tiles_dir.glob("*.png"):
        old.unlink()

    plan = []
    for i, f in enumerate(files, 1):
        img = load_rgb(f)
        angle = 0
        if args.rotate == "auto":
            try:
                angle = auto_rotation(img)
            except ImportError:
                print("AVISO: sin rapidocr no se detecta la orientación; usa --rotate si hay imágenes giradas")
        else:
            angle = int(args.rotate)
        if angle:
            img = img.rotate(angle, expand=True)
            print("  {}: girada {}° (el texto estaba rotado)".format(f.name, angle))
        orig_size = img.size
        scale = 1.0
        if img.width > args.max_width:
            scale = args.max_width / img.width
        elif img.width < args.min_width:
            scale = min(args.min_width / img.width, 3.0)
        if scale != 1.0:
            img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        if args.enhance:
            img = ImageOps.autocontrast(img, cutoff=1)
        cuts = cut_points(img, args.tile_height, args.overlap)
        starts = [0] + [max(c - args.overlap, 0) for c in cuts]
        ends = cuts + [img.height]
        tiles = []
        for k, (y0, y1) in enumerate(zip(starts, ends), 1):
            name = "{:02d}_{}_t{:02d}.png".format(i, f.stem, k)
            img.crop((0, y0, img.width, y1)).save(tiles_dir / name)
            tiles.append({"file": "tiles/" + name, "y0": y0, "y1": y1})
        entry = {"order": i, "image": f.name, "path": str(f.resolve()), "original_size": list(orig_size), "rotation": angle,
                 "scale": round(scale, 3), "tiles": tiles}
        plan.append(entry)

    (args.output_dir / "lectura.json").write_text(json.dumps(
        {"output_dir": str(args.output_dir.resolve()), "overlap": args.overlap, "images": plan}, ensure_ascii=False, indent=2) + "\n")

    print("Imágenes ({}):".format(len(plan)), ordered_note)
    for e in plan:
        extra = "" if e["scale"] == 1.0 else ", escala x{:g}".format(e["scale"])
        print("  {:>2}. {}  {}x{}{}  → {} trozo(s)".format(e["order"], e["image"], *e["original_size"], extra, len(e["tiles"])))
        for t in e["tiles"]:
            print("        {}  (filas {}–{})".format(args.output_dir / t["file"], t["y0"], t["y1"]))
        if len(e["tiles"]) > 1:
            print("        OJO: los trozos se solapan {} px; el texto del solape aparece en los dos: transcríbelo una sola vez.".format(args.overlap))
    print("\nMira con la herramienta Read CADA trozo, en orden, y transcribe a partes/NN_<nombre>.md")


if __name__ == "__main__":
    main()
