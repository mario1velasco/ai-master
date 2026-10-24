#!/usr/bin/env python3
"""Divide un audio largo en trozos de ~N segundos, cortando preferentemente en silencios."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from _common import fmt_time, probe, require_binary

# Formato de salida -> (extensión, códec de recodificación)
FORMATS = {
    "m4a": ("m4a", ["-c:a", "aac", "-b:a", "128k"]),
    "aac": ("aac", ["-c:a", "aac", "-b:a", "128k"]),
    "mp3": ("mp3", ["-c:a", "libmp3lame", "-b:a", "128k"]),
    "wav": ("wav", ["-c:a", "pcm_s16le"]),
    "flac": ("flac", ["-c:a", "flac"]),
    "opus": ("opus", ["-c:a", "libopus", "-b:a", "64k"]),
}
MIN_TAIL_SECONDS = 30.0


def detect_silences(path: Path, noise_db: float, min_silence: float) -> List[Tuple[float, float]]:
    """Un solo paso de ffmpeg silencedetect; devuelve [(inicio, fin)] en segundos."""
    ffmpeg = require_binary("ffmpeg")
    result = subprocess.run(
        [ffmpeg, "-nostats", "-i", str(path), "-vn", "-af",
         "silencedetect=noise={}dB:d={}".format(noise_db, min_silence), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit("error: ffmpeg falló en silencedetect:\n" + result.stderr[-500:])
    starts = [float(m) for m in re.findall(r"silence_start: (-?[\d.]+)", result.stderr)]
    ends = [float(m) for m in re.findall(r"silence_end: (-?[\d.]+)", result.stderr)]
    return list(zip(starts, ends))  # un silencio final sin cierre queda descartado: no hay nada que cortar


def plan_cuts(duration: float, chunk: float, window: float,
              silences: List[Tuple[float, float]]) -> List[Tuple[float, str]]:
    """Puntos de corte [(segundo, 'silence'|'hard')]; excluye 0 y la duración total."""
    cuts: List[Tuple[float, str]] = []
    target = chunk
    last = 0.0
    while target < duration:
        best: Optional[float] = None
        for start, end in silences:
            mid = (max(start, 0.0) + end) / 2
            if abs(mid - target) <= window and mid > last + 1.0 and (
                    best is None or abs(mid - target) < abs(best - target)):
                best = mid
        cut, kind = (best, "silence") if best is not None else (target, "hard")
        cuts.append((cut, kind))
        last = cut
        target = cut + chunk  # el siguiente objetivo se mide desde el corte real: evita trozos cortos acumulados
    # Un resto final demasiado corto se fusiona con el trozo anterior
    if cuts and duration - cuts[-1][0] < MIN_TAIL_SECONDS:
        cuts.pop()
    return cuts


def cut_chunk(src: Path, dst: Path, start: float, end: float, copy: bool, codec_args: List[str],
              exact_seek: bool = False) -> None:
    ffmpeg = require_binary("ffmpeg")
    times = ["-ss", "{:.3f}".format(start), "-to", "{:.3f}".format(end)]
    # AAC crudo (ADTS): el seek de entrada se estima por bitrate y se desvía segundos;
    # el seek de salida cuenta frames (más lento, pero exacto).
    cmd = [ffmpeg, "-y", "-v", "error"]
    cmd += ["-i", str(src)] + times if exact_seek else times + ["-i", str(src)]
    cmd += ["-vn", "-map_metadata", "-1"]
    cmd += ["-c", "copy"] if copy else codec_args
    cmd.append(str(dst))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit("error: ffmpeg falló cortando {}:\n{}".format(dst.name, result.stderr[-500:]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--chunk-seconds", type=float, default=240.0, help="duración objetivo (por defecto 240 = 4 min)")
    p.add_argument("--window", type=float, default=20.0, help="± segundos en los que se busca un silencio")
    p.add_argument("--silence-db", type=float, default=-35.0, help="umbral de silencio en dB; súbelo (-30) con ruido de fondo")
    p.add_argument("--min-silence", type=float, default=0.4, help="duración mínima de un silencio (s)")
    p.add_argument("--hard-cuts", action="store_true", help="cortar exactamente cada N segundos, sin buscar silencios")
    p.add_argument("--reencode", action="store_true", help="recodificar en vez de copiar el stream")
    p.add_argument("--format", choices=sorted(FORMATS), help="formato de salida (implica recodificar si difiere del de entrada)")
    p.add_argument("--force", action="store_true", help="permitir escribir en un directorio con trozos previos")
    args = p.parse_args()

    if not args.input.is_file():
        sys.exit("error: no existe {}".format(args.input))
    if args.chunk_seconds <= 2 * MIN_TAIL_SECONDS:
        sys.exit("error: --chunk-seconds debe ser mayor que {:g}".format(2 * MIN_TAIL_SECONDS))

    stem = args.input.stem
    in_ext = args.input.suffix.lstrip(".").lower()
    out_fmt = args.format or (in_ext if in_ext in FORMATS else "m4a")
    ext, codec_args = FORMATS[out_fmt]
    copy = not args.reencode and ext == in_ext  # -c copy solo si el contenedor no cambia

    args.output_dir.mkdir(parents=True, exist_ok=True)
    existing = list(args.output_dir.glob("{}_chunk_*".format(stem)))
    if existing and not args.force:
        sys.exit("error: {} ya contiene {} trozo(s) de {}; usa --force o cambia --output-dir".format(
            args.output_dir, len(existing), stem))
    for old in existing:
        old.unlink()

    info = probe(args.input)
    duration = info["duration"]
    silences = [] if args.hard_cuts else detect_silences(args.input, args.silence_db, args.min_silence)
    cuts = plan_cuts(duration, args.chunk_seconds, args.window, silences)

    bounds = [0.0] + [c for c, _ in cuts] + [duration]
    kinds = ["start"] + [k for _, k in cuts]  # tipo del corte que abre cada trozo
    width = max(3, len(str(len(bounds) - 1)))
    manifest = {
        "source": str(args.input.resolve()),
        "duration": round(duration, 3),
        "target_chunk_seconds": args.chunk_seconds,
        "mode": "copy" if copy else "reencode",
        "chunks": [],
    }
    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        name = "{}_chunk_{:0{w}d}.{}".format(stem, i + 1, ext, w=width)
        cut_chunk(args.input, args.output_dir / name, start, end, copy, codec_args, info["raw_adts"])
        manifest["chunks"].append({
            "file": name, "start": round(start, 3), "end": round(end, 3),
            "duration": round(end - start, 3), "cut": kinds[i],
        })
        print("{}  {} → {}  ({:.0f} s, {})".format(name, fmt_time(start), fmt_time(end), end - start, kinds[i]))

    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    hard = sum(1 for c in manifest["chunks"][1:] if c["cut"] == "hard")
    print("\n{} trozos en {} (modo {}; {} corte(s) duro(s))".format(
        len(manifest["chunks"]), args.output_dir, manifest["mode"], hard))


if __name__ == "__main__":
    main()
