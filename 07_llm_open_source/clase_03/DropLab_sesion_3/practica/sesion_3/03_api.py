"""Práctica 3 · Arrancar la API del Asistente DropLab (FastAPI + uvicorn).

    python practica/sesion_3/03_api.py              # http://127.0.0.1:8000  (Ctrl+C para pararla)
    python practica/sesion_3/03_api.py --puerto 8010

Al arrancar:
    http://127.0.0.1:8000/docs     el contrato (OpenAPI), con un botón «Try it out» en cada operación
    http://127.0.0.1:8000/salud    ¿están Ollama, el índice y los datos?

Escucha en 0.0.0.0 para que Open WebUI (en Docker, red del host) y otros equipos del aula puedan llamarla.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))


def main() -> None:
    ap = argparse.ArgumentParser(description="Arrancar la API del Asistente DropLab.")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()
    import socket
    import uvicorn
    from asistente import config
    with socket.socket() as sk:                     # ¿ya hay algo escuchando en ese puerto? (otra API, normalmente)
        if sk.connect_ex(("127.0.0.1", a.puerto)) == 0:
            raise SystemExit(f"El puerto {a.puerto} ya está ocupado: seguramente la API ya está en marcha "
                             f"(http://127.0.0.1:{a.puerto}/docs). Para otra: --puerto {a.puerto + 1}")
    print(f"Asistente DropLab · texto {config.MODELO_TEXTO} · visión {config.MODELO_VISION} · Ollama {config.OLLAMA_URL}")
    print(f"Contrato: http://127.0.0.1:{a.puerto}/docs   ·   Salud: http://127.0.0.1:{a.puerto}/salud")
    os.chdir(AQUI)
    uvicorn.run("asistente.api:app", host=a.host, port=a.puerto, log_level="info")


if __name__ == "__main__":
    main()
