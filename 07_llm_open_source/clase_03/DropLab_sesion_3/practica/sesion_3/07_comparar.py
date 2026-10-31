"""Para casa (ampliación) · Elegir configuración: dos combinaciones de modelos, las mismas tareas.

    A · «Jetson»    texto qwen3:30b-a3b-instruct (MoE, 18 GB)   +  visión qwen3-vl:8b-instruct (6 GB)
    B · «Portátil»  texto qwen3:4b-instruct (2,5 GB)            +  visión qwen3-vl:4b-instruct (3,3 GB)

Para cada una se mide, con los modelos descargados de memoria al empezar:
    - CARGA:   lo que tarda la primera llamada en cargar cada modelo (se paga una vez);
    - MEMORIA: lo que ocupa en memoria con su contexto (ollama ps);
    - CALIDAD: las partes «lectura» y «respuesta» del examen (06_evaluar.py), ya con los modelos cargados;
    - TIEMPO:  segundos por imagen y por pregunta (sin la carga).

Uso:
    python practica/sesion_3/07_comparar.py                # tabla con los resultados guardados (instantáneo)
    python practica/sesion_3/07_comparar.py --medir        # medir las dos (~1 h en el Jetson; antes de clase)
    python practica/sesion_3/07_comparar.py --medir --solo B
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from importlib import import_module
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import requests  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from asistente import config  # noqa: E402
from asistente.ollama import chat  # noqa: E402

evaluar = import_module("06_evaluar")
c = Console()
CONFIGS = {
    "A": {"nombre": "Jetson", "texto": "qwen3:30b-a3b-instruct-2507-q4_K_M", "vision": "qwen3-vl:8b-instruct"},
    "B": {"nombre": "Portátil", "texto": "qwen3:4b-instruct", "vision": "qwen3-vl:4b-instruct"},
}
SALIDA = config.RESULTADOS / "comparacion.json"
LICENCIAS = {"qwen3:30b-a3b-instruct-2507-q4_K_M": "Apache 2.0 · pesos abiertos", "qwen3:4b-instruct": "Apache 2.0 · pesos abiertos",
             "qwen3-vl:8b-instruct": "Apache 2.0 · pesos abiertos", "qwen3-vl:4b-instruct": "Apache 2.0 · pesos abiertos"}


def descargar_todo() -> None:
    for m in requests.get(config.OLLAMA_URL + "/api/ps", timeout=10).json().get("models", []):
        if m["name"] != "bge-m3:latest":
            subprocess.run(["ollama", "stop", m["name"]], capture_output=True)
    time.sleep(3)


def memoria(modelo: str) -> float | None:
    for m in requests.get(config.OLLAMA_URL + "/api/ps", timeout=10).json().get("models", []):
        if m["name"] == modelo:
            return round(m.get("size", 0) / 1e9, 1)
    return None


def carga(modelo: str, imagen: bool) -> dict:
    """La primera llamada, con el modelo fuera de memoria: separa la carga del resto."""
    msg = {"role": "user", "content": "Responde solo: ok"}
    if imagen:
        from asistente import vision
        msg["images"] = [vision.preparar_imagen((config.IMAGENES / "ticket_marzo.png").read_bytes()).b64]
    r = chat(modelo, [msg], num_ctx=config.CTX_VISION if imagen else config.CTX_TEXTO, num_predict=5)
    return {"carga_s": round(r.segundos_carga, 1), "primera_llamada_s": round(r.segundos, 1), "memoria_gb": memoria(modelo)}


def medir(clave: str) -> dict:
    cfg = CONFIGS[clave]
    c.rule(f"[bold]{clave} · {cfg['nombre']}[/] · {cfg['texto']} + {cfg['vision']}")
    descargar_todo()
    res = {"config": cfg, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
           "carga": {"texto": carga(cfg["texto"], False), "vision": carga(cfg["vision"], True)}}
    c.print(f"  carga texto {res['carga']['texto']} · carga visión {res['carga']['vision']}")
    a = argparse.Namespace(texto=cfg["texto"], vision=cfg["vision"])
    for parte in ("lectura", "respuesta"):
        t0 = time.time()
        res[parte] = evaluar.FUNCIONES[parte](a)
        c.print(f"  {parte}: {sum(f['ok'] for f in res[parte])}/{len(res[parte])} en {time.time() - t0:.0f} s")
    res["memoria_final_gb"] = {"texto": memoria(cfg["texto"]), "vision": memoria(cfg["vision"])}
    # Las mismas filas, en el archivo de 06_evaluar.py de esta configuración
    archivo = config.RESULTADOS / f"evaluacion_{evaluar.nombre_config(cfg['texto'], cfg['vision'])}.json"
    previo = json.loads(archivo.read_text(encoding="utf-8"))["resultados"] if archivo.exists() else {}
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps({"fecha": res["fecha"], "texto": cfg["texto"], "vision": cfg["vision"],
                                   "resultados": {**previo, "lectura": res["lectura"], "respuesta": res["respuesta"]}},
                                  ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return res


def tabla(datos: dict) -> None:
    t = Table(title="Dos configuraciones locales, las mismas tareas", title_justify="left", header_style="bold")
    t.add_column("medida")
    for k, d in datos.items():
        t.add_column(f"{k} · {d['config']['nombre']}\n{d['config']['texto'].split('-instruct')[0]} + "
                     f"{d['config']['vision'].split('-instruct')[0]}")

    def fila(nombre, f):
        t.add_row(nombre, *[f(d) for d in datos.values()])

    fila("lectura: imágenes bien leídas (de 4 reales)", lambda d: f"{sum(x['ok'] for x in d['lectura'][:4])}/4")
    fila("lectura: campos correctos (reales)", lambda d: f"{sum(x.get('campos_bien', 0) for x in d['lectura'][:4])}/"
         f"{sum(x.get('campos', 0) for x in d['lectura'][:4])}")
    fila("lectura: detecta la imagen ilegible (L6)", lambda d: ("sí · " if d["lectura"][5]["ok"] else "no · ")
         + d["lectura"][5]["obtenido"].split(" · ")[1])
    fila("respuestas correctas (de 7)", lambda d: f"{sum(x['ok'] for x in d['respuesta'])}/7")
    fila("respuestas con verificación limpia", lambda d: f"{sum(x.get('verificacion_limpia', False) for x in d['respuesta'])}/7")
    fila("s por imagen (modelo cargado)", lambda d: f"{sum(x['segundos'] for x in d['lectura']) / len(d['lectura']):.0f}")
    fila("s por pregunta (modelo cargado)", lambda d: f"{sum(x['segundos'] for x in d['respuesta']) / len(d['respuesta']):.0f}")
    fila("carga del modelo de texto (una vez)", lambda d: f"{d['carga']['texto']['carga_s']} s")
    fila("carga del modelo de visión (una vez)", lambda d: f"{d['carga']['vision']['carga_s']} s")
    fila("memoria texto + visión (ollama ps)", lambda d: f"{d['carga']['texto']['memoria_gb']} + "
         f"{d['carga']['vision']['memoria_gb']} GB")
    fila("licencia", lambda d: LICENCIAS.get(d["config"]["texto"], "?"))
    c.print(t)
    for k, d in datos.items():
        fallos = [f"{x['id']}: {x['obtenido'][:100]}" for x in d["lectura"] + d["respuesta"] if not x["ok"]]
        if fallos:
            c.print(f"[bold]{k}[/] falla en: " + " · ".join(fallos))


def main() -> None:
    ap = argparse.ArgumentParser(description="Comparar dos configuraciones locales.")
    ap.add_argument("--medir", action="store_true")
    ap.add_argument("--solo", choices=list(CONFIGS))
    ap.add_argument("--recalificar", action="store_true",
                    help="Volver a poner nota a las respuestas guardadas con el examen actual (sin modelos).")
    a = ap.parse_args()
    datos = json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}
    if a.recalificar and datos:
        examen = {q["id"]: q for q in evaluar.EXAMEN["respuesta"]}
        for d in datos.values():
            for f in d["respuesta"]:
                ver = f.get("verificacion") or ([] if f.get("verificacion_limpia") else ["(aviso)"])
                f.update(evaluar.calificar(examen[f["id"]], f["respuesta"], ver, f.get("citas", 0)))
        SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        for k, d in datos.items():
            cfg = d["config"]
            archivo = config.RESULTADOS / f"evaluacion_{evaluar.nombre_config(cfg['texto'], cfg['vision'])}.json"
            if archivo.exists():
                e = json.loads(archivo.read_text(encoding="utf-8"))
                e["resultados"]["respuesta"] = d["respuesta"]
                archivo.write_text(json.dumps(e, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        c.print("[yellow]Recalificado con el examen actual (sin llamar a ningún modelo).[/]")
    if a.medir:
        for k in ([a.solo] if a.solo else CONFIGS):
            datos[k] = medir(k)
            config.RESULTADOS.mkdir(parents=True, exist_ok=True)
            SALIDA.write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not datos:
        raise SystemExit("No hay resultados: python practica/sesion_3/07_comparar.py --medir")
    c.print(f"[dim]{'MEDIDO AHORA' if a.medir else 'RESULTADOS GUARDADOS'} · "
            + " · ".join(f"{k}: {d['fecha']}" for k, d in datos.items()) + "[/]")
    tabla(datos)


if __name__ == "__main__":
    main()
