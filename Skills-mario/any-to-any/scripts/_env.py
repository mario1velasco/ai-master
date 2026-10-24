"""Rutas de la skill, de las skills hermanas y del intérprete (venv compartido)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SKILLS = SKILL.parent
VENV = SKILLS / ".venv"  # entorno único compartido por todas las skills (ver scripts/setup_env.py en la raíz)
AUDIO_SPLIT = SKILLS / "audio-split" / "scripts"
AUDIO_DECODER = SKILLS / "audio-decoder" / "scripts"
IMG_TO_TEXT = SKILLS / "img-to-text" / "scripts"
SCRIPTS = SKILL / "scripts"


def venv_python() -> str:
    for rel in ("bin/python", "Scripts/python.exe"):
        p = VENV / rel
        if p.is_file():
            return str(p)
    sys.exit("error: falta el entorno virtual. Ejecuta desde la raíz del repo: python3 scripts/setup_env.py")


def load_module(name: str, path: Path):
    """Carga un módulo por ruta con nombre único (las skills hermanas tienen todas un _ordering.py/_common.py)."""
    if not path.is_file():
        sys.exit("error: no existe {} (¿falta la skill hermana?)".format(path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))  # por si el módulo importa a otro de su carpeta
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod
