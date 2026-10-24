#!/usr/bin/env python3
"""Audios → texto → bruto.md: divide los largos (audio-split), transcribe (audio-decoder), verifica y escribe el texto
literal como Markdown escapado en trabajo/unidades/<id>_<nombre>/bruto.md. Reanudable.

Si más de 1/3 de los cortes salen duros (sin silencio), repite la división con -30 dB / 0,3 s.
Es lento (≈ 1/3 de la duración del audio en CPU con turbo): lánzalo en segundo plano y mira el log.
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
from _md import content_words, escape_text, text_words
from convert_docs import unit_dir


def run(cmd: List[str]) -> int:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


def split(py: str, src: Path, trozos: Path, extra: List[str]) -> dict:
    cmd = [py, str(AUDIO_SPLIT / "split_audio.py"), str(src), "--output-dir", str(trozos), "--force"] + extra
    if run(cmd) != 0:
        sys.exit("error: falló la división de {}".format(src))
    return json.loads((trozos / "manifest.json").read_text())


def hard_ratio(manifest: dict) -> float:
    cuts = manifest["chunks"][1:]
    return sum(1 for c in cuts if c["cut"] == "hard") / len(cuts) if cuts else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("work_dir", type=Path, help="carpeta trabajo/ creada por inventory.py")
    ap.add_argument("--unit", action="append", help="solo esta unidad (u01…); repetible. Por defecto, todas las de audio")
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
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    for u in units:
        src = Path(u["path"])
        udir = unit_dir(args.work_dir, u)
        trozos, trans = udir / "trozos", udir / "transcripcion"
        print("\n=== {} · {} ({:.1f} min) ===".format(u["id"], src.name, u["minutes"]), flush=True)
        full = trans / "transcripcion_completa.txt"
        if full.is_file() and (udir / "bruto.md").is_file() and not args.force:
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
        text = full.read_text(encoding="utf-8")
        md = escape_text(text)
        if text_words(text) != content_words(md):
            sys.exit("error interno: el escape de la transcripción cambia palabras ({})".format(full))
        (udir / "bruto.md").write_text(md, encoding="utf-8")
        st_path = udir / "estado.json"
        st = json.loads(st_path.read_text()) if st_path.is_file() else {"id": u["id"], "name": u["name"], "kind": "audio",
                                                                         "dir": str(udir), "warnings": [], "needs": []}
        st["bruto"] = str(udir / "bruto.md")
        st["needs"] = [n for n in st.get("needs", []) if not n.startswith("audio:")]
        st["warnings"].append("transcripción automática (Whisper): puede haber errores en nombres propios y jerga; no se corrigen")
        st_path.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n")
        print("bruto.md: {} palabras → {}".format(len(content_words(md)), udir / "bruto.md"))
    print("\nAudio listo: {} unidad(es).".format(len(units)))


if __name__ == "__main__":
    main()
