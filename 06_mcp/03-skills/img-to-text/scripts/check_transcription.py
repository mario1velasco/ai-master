#!/usr/bin/env python3
"""Segundo lector independiente: compara la transcripción .md con el OCR local (RapidOCR) de las imágenes.

Heurística; cada aviso hay que contrastarlo mirando la imagen (zoom_image.py):
 - INVENTADO?/MAL LEÍDO?: palabras o cifras del .md que el OCR no ve en las imágenes.
 - OMITIDO?: palabras o cifras que el OCR ve en las imágenes y no están en el .md (con trozo y caja para hacer zoom).
Errores (exit 1): .md vacío, nº de comentarios `<!-- imagen N -->` distinto del nº de imágenes.
El OCR también se equivoca (letras parecidas, texto pequeño, manuscrito): un aviso no es una prueba.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from _text import DOUBTFUL, ILLEGIBLE, visible_text, words_of

MAX_SHOWN = 40


def within_one(a: str, b: str) -> bool:
    """Distancia de edición ≤ 1 (sustitución, inserción o borrado)."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = j = diff = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            diff += 1
            if diff > 1:
                return False
            if len(a) == len(b):
                i += 1
            j += 1
    return diff + (len(b) - j) + (len(a) - i) <= 1


def supported(word: str, vocab: set, by_len: Dict[int, List[str]]) -> bool:
    if word in vocab:
        return True
    if word.isdigit() or len(word) < 4:  # cifras y palabras cortas: solo coincidencia exacta
        return False
    return any(within_one(word, v) for n in (len(word) - 1, len(word), len(word) + 1) for v in by_len.get(n, ()))


def index(vocab: set) -> Dict[int, List[str]]:
    out: Dict[int, List[str]] = {}
    for w in vocab:
        out.setdefault(len(w), []).append(w)
    return out


def run_ocr(tiles: List[Path], cache: Path) -> List[dict]:
    if cache.is_file() and cache.stat().st_mtime >= max(t.stat().st_mtime for t in tiles):
        return json.loads(cache.read_text())
    try:
        from rapidocr import RapidOCR
    except ImportError:
        sys.exit("error: falta rapidocr. Instálalo en un venv: python3 -m pip install -r requirements.txt")
    logging.getLogger("RapidOCR").setLevel(logging.ERROR)
    engine = RapidOCR(params={"Global.log_level": "error"})  # sin los INFO de carga de modelos
    lines = []
    for t in tiles:
        res = engine(str(t))
        for text, score, box in zip(res.txts or [], res.scores or [], res.boxes if res.boxes is not None else []):
            xs, ys = [p[0] for p in box], [p[1] for p in box]
            lines.append({"tile": t.name, "text": text, "score": round(float(score), 3),
                          "box": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]})
    cache.write_text(json.dumps(lines, ensure_ascii=False))
    return lines


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("--work-dir", type=Path, required=True, help="carpeta con lectura.json y tiles/ (la de prepare_images.py)")
    args = ap.parse_args()

    if not args.markdown.is_file() or not args.markdown.read_text(encoding="utf-8").strip():
        sys.exit("error: el .md no existe o está vacío")
    md = args.markdown.read_text(encoding="utf-8")
    plan = json.loads((args.work_dir / "lectura.json").read_text())
    images = plan["images"]
    errors: List[str] = []
    warnings: List[str] = []

    markers = re.findall(r"<!--\s*imagen\s+(\d+)\s*:", md)
    if len(markers) != len(images):
        errors.append("hay {} comentarios <!-- imagen N --> y {} imágenes (usa join_parts.py)".format(len(markers), len(images)))

    tiles = [args.work_dir / t["file"] for e in images for t in e["tiles"]]
    ocr = run_ocr(tiles, args.work_dir / "ocr.json")
    ocr_text = "\n".join(l["text"] for l in ocr)
    ocr_words = words_of(ocr_text)
    md_words = words_of(visible_text(md))
    ocr_vocab, md_vocab = set(ocr_words), set(md_words)
    ocr_idx, md_idx = index(ocr_vocab), index(md_vocab)

    info = ["{} palabras en el .md; {} en el OCR ({:.0%})".format(len(md_words), len(ocr_words), len(md_words) / max(len(ocr_words), 1))]
    n_ill, n_dub = len(ILLEGIBLE.findall(md)), len(DOUBTFUL.findall(md))
    if n_ill or n_dub:
        warnings.append("REVISAR: {} marcador(es) [ilegible] y {} [dudoso: …]; vuelve a mirar cada uno con zoom_image.py".format(n_ill, n_dub))
    if ocr_words and not 0.85 <= len(md_words) / len(ocr_words) <= 1.15:
        warnings.append("la cantidad de palabras difiere más de un 15 % del OCR: puede faltar o sobrar texto")

    # 1) Palabras del .md que el OCR no ve (con su línea del .md)
    md_lines = [(n, words_of(visible_text(l))) for n, l in enumerate(md.splitlines(), 1)]
    seen, bad = set(), []
    for n, ws in md_lines:
        for w in ws:
            if w not in seen and not supported(w, ocr_vocab, ocr_idx):
                seen.add(w)
                bad.append("«{}» (línea {})".format(w, n))
    if bad:
        warnings.append("INVENTADO?/MAL LEÍDO?: palabras del .md que el OCR no ve en las imágenes: " + ", ".join(bad[:MAX_SHOWN])
                        + (" … (+{})".format(len(bad) - MAX_SHOWN) if len(bad) > MAX_SHOWN else ""))

    # 2) Texto que el OCR ve y el .md no tiene (con trozo y caja)
    seen, miss = set(), []
    for l in ocr:
        for w in words_of(l["text"]):
            if w not in seen and (len(w) >= 3 or w.isdigit()) and not supported(w, md_vocab, md_idx):
                seen.add(w)
                miss.append("«{}» ({}, caja {})".format(w, l["tile"], ",".join(map(str, l["box"]))))
    if miss:
        warnings.append("OMITIDO?: palabras que el OCR ve en las imágenes y faltan en el .md: " + "; ".join(miss[:MAX_SHOWN])
                        + (" … (+{})".format(len(miss) - MAX_SHOWN) if len(miss) > MAX_SHOWN else "")
                        + "\n         Para mirar una zona: zoom_image.py <trozo> --box x0,y0,x1,y1")

    print("; ".join(info))
    for w in warnings:
        print("AVISO:", w)
    if errors:
        print("FALLO:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("OK" + (" (con {} aviso(s) a contrastar con las imágenes)".format(len(warnings)) if warnings else ""))


if __name__ == "__main__":
    main()
