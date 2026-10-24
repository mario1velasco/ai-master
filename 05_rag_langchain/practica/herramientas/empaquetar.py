"""Paso 11 · Crea el ZIP de entrega con SOLO los archivos exigidos.

Uso:  python -m herramientas.empaquetar Apellidos_Nombre     (desde practica/)
Genera  practica/Apellidos_Nombre_RAG_Tenerife.zip  (ignorado por git).
Nunca incluye .env, .venv, data/, cachés ni la carpeta docs/tests.
"""
import re
import sys
import zipfile
from pathlib import Path

OBLIGATORIOS = ("rag_tenerife.ipynb", "resultados.json", "revision.csv", "README.md",
                "requirements.txt", "preguntas.csv", "utilidades.py")
PROHIBIDOS = (".env", ".venv", "data", "__pycache__", ".ipynb_checkpoints")
PATRON_CLAVE = re.compile(r"sk-[A-Za-z0-9_\-]{20,}")


def comprobar(carpeta):
    carpeta = Path(carpeta)
    problemas = [f"Falta {n}" for n in OBLIGATORIOS if not (carpeta / n).is_file()]
    for n in OBLIGATORIOS:
        f = carpeta / n
        if f.is_file() and f.suffix in (".ipynb", ".json", ".md", ".txt", ".py", ".csv"):
            if PATRON_CLAVE.search(f.read_text(encoding="utf-8", errors="ignore")):
                problemas.append(f"{n} parece contener una clave de API (sk-…).")
    return problemas


def crear_zip(carpeta, destino):
    carpeta, destino = Path(carpeta), Path(destino)
    problemas = comprobar(carpeta)
    if problemas:
        raise ValueError("; ".join(problemas))
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for n in OBLIGATORIOS:
            z.write(carpeta / n, n)
    return destino


if __name__ == "__main__":
    nombre = sys.argv[1] if len(sys.argv) > 1 else "Apellidos_Nombre"
    aqui = Path(__file__).resolve().parents[1]
    print(crear_zip(aqui / "Recursos ", aqui / f"{nombre}_RAG_Tenerife.zip"))
