#!/usr/bin/env python3
"""Crea (una vez) el entorno virtual .venv de la skill con todas las dependencias y comprueba ffmpeg."""
from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from pathlib import Path

from _env import SKILL


def main() -> None:
    problems = [b for b in ("ffmpeg", "ffprobe") if not shutil.which(b)]
    if problems:
        print("AVISO: falta {} en el PATH: no se podrán dividir/leer audios (instala ffmpeg).".format(", ".join(problems)))
    env = SKILL / ".venv"
    py = env / "bin" / "python"
    if not py.is_file():
        print("Creando {} …".format(env))
        venv.EnvBuilder(with_pip=True).create(env)
    probe = subprocess.run([str(py), "-c", "import faster_whisper, PIL, rapidocr, reportlab, pypdf, markdown_it"], capture_output=True)
    if probe.returncode == 0:
        print("OK: el entorno ya tiene todas las dependencias ({})".format(py))
    else:
        print("Instalando dependencias (faster-whisper y rapidocr pesan unos cientos de MB) …")
        subprocess.run([str(py), "-m", "pip", "install", "-q", "-r", str(SKILL / "requirements.txt")], check=True)
        print("OK: entorno listo ({})".format(py))
    print("Los modelos (Whisper turbo ~1,6 GB, OCR) se descargan la primera vez que se usan.")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
