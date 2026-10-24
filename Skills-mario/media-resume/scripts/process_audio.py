#!/usr/bin/env python3
"""Audios → texto: divide los largos (audio-split), transcribe (audio-decoder) y verifica. Reanudable.

Para cada unidad de audio del inventario crea trabajo/audio/<id>_<nombre>/{trozos,transcripcion}.
Si más de 1/3 de los cortes salen duros (sin silencio), repite la división con -30 dB / 0,3 s.
Es lento (≈ 3× tiempo real en CPU con turbo): lánzalo en segundo plano y mira el log.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from _env import AUDIO_DECODER, AUDIO_SPLIT, venv_python


def run(cmd: List[str]) -> int:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


def split(py: str, src: Path, trozos: Path, extra: List[str]) -> dict:
    cmd = [py, str(AUDIO_SPLIT / "split_audio.py"), str(src), "--output-dir", str(trozos), "--force"] + extra
    if run(cmd) != 0:
        sys.exit("error: falló la división de {}".format(src))
    return json.loads((trozos / "manifest.json").read_text())


def hard_ratio(manifest: dict) -> float:
    cuts = [c for c in manifest["chunks"][1:]]
    return sum(1 for c in cuts if c["cut"] == "hard") / len(cuts) if cuts else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("work_dir", type=Path, help="carpeta trabajo/ creada por inventory.py")
    ap.add_argument("--unit", action="append", help="solo esta unidad (a01…); repetible. Por defecto, todas las de audio")
    ap.add_argument("--model", default="turbo")
    ap.add_argument("--language", default=None)
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--chunk-seconds", type=float, default=240.0)
    ap.add_argument("--force", action="store_true", help="volver a dividir y retranscribir")
    args = ap.parse_args()

    inv = json.loads((args.work_dir / "inventario.json").read_text())
    units = [u for u in inv["units"] if u["kind"] == "audio" and (not args.unit or u["id"] in args.unit)]
    if not units:
        sys.exit("error: no hay unidades de audio que procesar")
    py = venv_python()
    env_note = os.environ.get("PYTHONDONTWRITEBYTECODE")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    for u in units:
        src = Path(u["path"])
        udir = args.work_dir / "audio" / "{}_{}".format(u["id"], src.stem)
        trozos, trans = udir / "trozos", udir / "transcripcion"
        print("\n=== {} · {} ({:.1f} min) ===".format(u["id"], src.name, u["minutes"]), flush=True)
        if (trans / "transcripcion_completa.txt").is_file() and not args.force:
            print("ya transcrito, se reutiliza (usa --force para rehacer)")
            continue
        trozos.mkdir(parents=True, exist_ok=True)
        if u["split"]:
            manifest_path = trozos / "manifest.json"
            if manifest_path.is_file() and not args.force:
                print("trozos ya generados, se reutilizan")
            else:
                for old in trozos.glob("*"):
                    if old.is_file() or old.is_symlink():
                        old.unlink()
                m = split(py, src, trozos, ["--chunk-seconds", str(args.chunk_seconds)])
                if hard_ratio(m) > 1 / 3:
                    print("{:.0%} de cortes duros: se repite con --silence-db -30 --min-silence 0.3".format(hard_ratio(m)), flush=True)
                    m = split(py, src, trozos, ["--chunk-seconds", str(args.chunk_seconds), "--silence-db", "-30", "--min-silence", "0.3"])
                    if hard_ratio(m) > 1 / 3:
                        print("AVISO: siguen más de 1/3 de cortes duros; puede partirse alguna palabra (ver audio-split/references/workflow.md)")
        else:
            link = trozos / src.name
            if not link.exists():
                link.symlink_to(src)
        cmd = [py, str(AUDIO_DECODER / "transcribe_audio.py"), str(trozos), "--output-dir", str(trans), "--model", args.model,
               "--device", args.device]
        if args.language:
            cmd += ["--language", args.language]
        if args.force:
            cmd.append("--force")
        if run(cmd) != 0:
            sys.exit("error: falló la transcripción de {}".format(src))
        if run([py, str(AUDIO_DECODER / "check_transcript.py"), str(trans)]) != 0:
            sys.exit("error: la verificación de la transcripción de {} falló".format(src))
        (udir / "listo.json").write_text(json.dumps({"unit": u["id"], "transcripcion": str(trans / "transcripcion_completa.txt")}) + "\n")
    print("\nAudio listo: {} unidad(es).".format(len(units)))
    if env_note is None:
        os.environ.pop("PYTHONDONTWRITEBYTECODE", None)


if __name__ == "__main__":
    main()
