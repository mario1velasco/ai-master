#!/usr/bin/env python3
"""Crea (una vez) el entorno virtual compartido .venv en la raíz del repo, con las dependencias de todas las skills."""
from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".venv"
IMPORTS = "import faster_whisper, PIL, rapidocr, reportlab, pypdf, markdown_it, pptx, markitdown, docx, pypdfium2"


# Comprueba que las versiones instaladas son las fijadas en requirements.txt (un import que funciona no basta:
# p. ej. av 19 importa bien pero rompe faster-whisper 1.2.1).
CHECK_PINS = """
import re, sys
from importlib.metadata import version, PackageNotFoundError
bad = []
for line in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"\\s*([A-Za-z0-9_.-]+)(?:\\[[^\\]]*\\])?==([^\\s#]+)", line)
    if m:
        try:
            if version(m.group(1)) != m.group(2):
                bad.append("{} {} (fijado {})".format(m.group(1), version(m.group(1)), m.group(2)))
        except PackageNotFoundError:
            bad.append(m.group(1) + " (no instalado)")
print("\\n".join(bad))
"""


def wrong_versions(py: Path) -> list:
    res = subprocess.run([str(py), "-c", CHECK_PINS, str(ROOT / "requirements.txt")], capture_output=True, text=True)
    bad = [l for l in res.stdout.splitlines() if l.strip()]
    if bad:
        print("Versiones distintas de las fijadas en requirements.txt: " + "; ".join(bad))
    return bad


def main() -> None:
    problems = [b for b in ("ffmpeg", "ffprobe") if not shutil.which(b)]
    if problems:
        print("AVISO: falta {} en el PATH: no se podrán dividir/leer audios (instala ffmpeg).".format(", ".join(problems)))
    py = ENV / "bin" / "python"
    if not py.is_file():
        print("Creando {} …".format(ENV))
        venv.EnvBuilder(with_pip=True).create(ENV)
    if subprocess.run([str(py), "-c", IMPORTS], capture_output=True).returncode == 0 and not wrong_versions(py):
        print("OK: el entorno ya tiene todas las dependencias ({})".format(py))
    else:
        print("Instalando dependencias (faster-whisper y rapidocr pesan unos cientos de MB) …")
        subprocess.run([str(py), "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")], check=True)
        print("OK: entorno listo ({})".format(py))
    print("Los modelos (Whisper turbo ~1,6 GB, OCR) se descargan la primera vez que se usan.")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
