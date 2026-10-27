#!/usr/bin/env python3
"""Verifica un vídeo descargado: existe, coincide con manifest.json y ffprobe lo lee entero (duración y pistas)."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def probe(path: Path) -> dict:
    res = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"FALLO: ffprobe no puede leer {path}: {res.stderr.strip()[:300]}")
    return json.loads(res.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="el vídeo, o la carpeta con el vídeo y manifest.json")
    parser.add_argument("--min-seconds", type=float, default=60, help="duración mínima esperada")
    args = parser.parse_args()
    if not shutil.which("ffprobe"):
        raise SystemExit("error: falta ffprobe (sudo apt install ffmpeg)")

    manifest = None
    if args.target.is_dir():  # salida de download_video.py
        manifest = json.loads((args.target / "manifest.json").read_text())
        video = args.target / manifest["file"]
    else:  # salida de yt-dlp
        video = args.target
    problems: list[str] = []
    if not video.is_file():
        raise SystemExit(f"FALLO: no existe {video}")
    if video.with_suffix(video.suffix + ".part").exists():
        problems.append("queda un .part: la descarga no terminó")
    size = video.stat().st_size
    if manifest and size != manifest["bytes"]:
        problems.append(f"tamaño {size} ≠ manifest {manifest['bytes']}")

    info = probe(video)
    duration = float(info["format"].get("duration", 0))
    kinds = [s["codec_type"] for s in info["streams"]]
    if duration < args.min_seconds:
        problems.append(f"dura solo {duration:.0f} s (¿es una página de error o un trozo?)")
    if "audio" not in kinds:
        problems.append("no tiene pista de audio")

    h, rem = divmod(int(duration), 3600)
    print(f"Vídeo:     {video}")
    print(f"Tamaño:    {size / 1e6:,.1f} MB")
    print(f"Duración:  {h}:{rem // 60:02d}:{rem % 60:02d}")
    print(f"Pistas:    {', '.join(f'{s['codec_type']} ({s['codec_name']})' for s in info['streams'])}")
    for p in problems:
        print(f"FALLO: {p}")
    if problems:
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
