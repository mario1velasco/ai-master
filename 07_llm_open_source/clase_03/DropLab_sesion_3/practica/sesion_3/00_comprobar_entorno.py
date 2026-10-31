"""Comprobación antes de clase: ¿está todo lo de la sesión 3? (no llama a ningún modelo de texto; ~10 s)

    python practica/sesion_3/00_comprobar_entorno.py
    python practica/sesion_3/00_comprobar_entorno.py --calentar     # además, carga los modelos en memoria (~1 min)

Comprueba: hardware y modo de energía, versiones de Python y librerías, Ollama y sus modelos, índice del RAG
(ampliado con junio), lecturas de los PDF de junio, el entorno de OCR (.venv-ocr, opcional), API (8000),
Open WebUI (3000) y la Pipe, salidas guardadas y resultados medidos.
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import requests  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from asistente import config, documentos  # noqa: E402
from asistente.ollama import chat, estado  # noqa: E402

c = Console()
VERSIONES_PROBADAS = {"fastapi": "0.143.0", "pydantic": "2.14.1", "langgraph": "1.2.14", "langchain-core": "1.6.9",
                      "uvicorn": "0.54.0", "duckdb": "1.5.6", "requests": "2.34.2", "pillow": "12.3.0", "rich": "13.9.4",
                      "python-multipart": "0.0.32", "websockets": "16.1.1"}


def fila(t, que, ok, detalle):
    t.add_row("[green]✓[/]" if ok is True else "[yellow]·[/]" if ok is None else "[red]✗[/]", que, detalle)
    return ok is not False


def main() -> None:
    ap = argparse.ArgumentParser(description="Comprobación de la sesión 3.")
    ap.add_argument("--calentar", action="store_true", help="Cargar en memoria los modelos de texto y visión.")
    a = ap.parse_args()
    t = Table(title="Sesión 3 · comprobación", header_style="bold", title_justify="left")
    for col in ("", "qué", "detalle"):
        t.add_column(col)
    todo = True
    modo = shutil.which("nvpmodel") and subprocess.run(["nvpmodel", "-q"], capture_output=True, text=True).stdout.split("\n")[0]
    todo &= fila(t, "Equipo", None, f"{platform.machine()} · {modo or 'sin nvpmodel (no es un Jetson)'}"
                 + (" · MAXN sería más rápido (sudo nvpmodel -m 0)" if modo and "MAXN" not in modo else ""))
    todo &= fila(t, "Python", sys.version_info[:2] >= (3, 10), platform.python_version())
    for paquete, probada in VERSIONES_PROBADAS.items():
        try:
            v = md.version(paquete)
            todo &= fila(t, paquete, True if v == probada else None, v + ("" if v == probada else f" (probada: {probada})"))
        except md.PackageNotFoundError:
            todo &= fila(t, paquete, False, "no instalado: pip install -r requirements_sesion_3.txt")
    o = estado()
    todo &= fila(t, "Ollama", o["ok"], o.get("url") + (" · cargados: " + (", ".join(m["modelo"] for m in o.get("cargados", [])) or "ninguno")
                                                        if o["ok"] else " · NO RESPONDE"))
    for m in (config.MODELO_TEXTO, config.MODELO_VISION, "bge-m3", "qwen3:4b-instruct", "qwen3-vl:4b-instruct"):
        ok = o["ok"] and any(i.split(":latest")[0] == m.split(":latest")[0] for i in o["instalados"])
        todo &= fila(t, f"modelo {m}", ok if m in (config.MODELO_TEXTO, config.MODELO_VISION, "bge-m3") else (ok or None),
                     "instalado" if ok else f"ollama pull {m}")
    d = documentos.estado()
    todo &= fila(t, "Índice RAG" + (" (ampliado con junio)" if d.get("ampliado") else " (sesión 2)"), d["ok"],
                 f"{d['indice']} · {d['fragmentos']} fragmentos"
                 + ("" if d.get("ampliado") else " · falta el ampliado: python practica/sesion_3/09_indice_junio.py"))
    lect = [config.GUARDADAS / "documentos" / f"{a}.json" for a in ("informe", "escaneado")]
    todo &= fila(t, "Lecturas de los PDF de junio", all(p.exists() for p in lect),
                 "informe.json y escaneado.json" if all(p.exists() for p in lect)
                 else ".venv-ocr/bin/python practica/sesion_3/08_leer_documentos.py --guardar")
    ocr = config.ROOT / ".venv-ocr"
    modelos_ocr = Path.home() / ".paddlex" / "official_models"
    faltan = [m for m in ("PP-OCRv6_medium_det_safetensors", "PP-OCRv6_medium_rec_safetensors", "PaddleOCR-VL-1.6",
                          "PP-DocLayoutV3_safetensors") if not (modelos_ocr / m).exists()]
    hay_ocr = bool(list(ocr.glob("lib/python3*/site-packages/paddleocr")))
    todo &= fila(t, "OCR en directo (.venv-ocr, opcional)", (hay_ocr and not faltan) or None,
                 "PaddleOCR + modelos en ~/.paddlex" if hay_ocr and not faltan else
                 ("faltan modelos: " + ", ".join(faltan) if hay_ocr else "sin .venv-ocr: ver requirements_ocr.txt")
                 + " · sin él, 08_leer_documentos.py --guardada")
    for nombre, url in (("API (03_api.py)", config.API_URL + "/salud"), ("Open WebUI", "http://127.0.0.1:3000/health")):
        try:
            r = requests.get(url, timeout=4)
            todo &= fila(t, nombre, r.status_code == 200, url)
        except requests.exceptions.RequestException:
            todo &= fila(t, nombre, False, f"{url} no responde")
    try:
        tok = requests.post("http://127.0.0.1:3000/api/v1/auths/signin", json={"email": "", "password": ""}, timeout=5).json()["token"]
        f = requests.get("http://127.0.0.1:3000/api/v1/functions/id/droplab_analista",
                         headers={"Authorization": f"Bearer {tok}"}, timeout=5)
        ok = f.status_code == 200 and f.json().get("is_active")
        todo &= fila(t, "Pipe «DropLab Analista»", bool(ok), "activa" if ok else "python practica/sesion_3/openwebui/instalar_pipe.py")
    except Exception:  # noqa: BLE001
        todo &= fila(t, "Pipe «DropLab Analista»", False, "no se pudo comprobar")
    g = list((config.GUARDADAS / "vision").glob("*.json")) + list((config.GUARDADAS / "flujo").glob("*.json"))
    todo &= fila(t, "Salidas guardadas (plan B)", len(g) >= 16, f"{len(g)} archivos (6 imágenes + 12 preguntas del flujo, 2 extras) · "
                 "python practica/sesion_3/guardar_salidas.py")
    res = list(config.RESULTADOS.glob("*.json"))
    todo &= fila(t, "Resultados medidos", len(res) >= 2, ", ".join(p.name for p in res) or "06_evaluar.py / 07_comparar.py")
    c.print(t)
    if a.calentar and o["ok"]:
        from asistente import vision
        for m, img in ((config.MODELO_TEXTO, None), (config.MODELO_VISION, config.IMAGENES / "ticket_marzo.png")):
            msg = {"role": "user", "content": "ok"}
            if img:
                msg["images"] = [vision.preparar_imagen(img.read_bytes()).b64]
            r = chat(m, [msg], num_predict=2, num_ctx=config.CTX_VISION if img else config.CTX_TEXTO)
            c.print(f"calentado {m}: {r.segundos:.0f} s (carga {r.segundos_carga:.0f} s)")
        c.print(json.dumps(estado()["cargados"], ensure_ascii=False))
    c.print("[bold green]Todo listo.[/]" if todo else "[bold red]Revisa las filas en rojo.[/]")


if __name__ == "__main__":
    main()
