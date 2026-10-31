"""Guarda salidas REALES de cada demostración: el plan B si en clase falla un modelo, la red o el tiempo.

    python practica/sesion_3/guardar_salidas.py               # todo (~30 min en el Jetson; antes de clase)
    python practica/sesion_3/guardar_salidas.py --solo vision
    python practica/sesion_3/guardar_salidas.py --solo flujo

Salida: practica/sesion_3/salidas_guardadas/
    vision/<imagen>.json   pregunta libre + extracción + comprobación (01_ver_imagen.py --guardada)
    flujo/<caso>.json      el flujo completo de cada caso de 05_flujo.py (05_flujo.py --caso X --guardada)

Cada archivo lleva la fecha, los modelos y «origen: guardada»: en clase se enseñan como lo que son.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from importlib import import_module
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from asistente import config, flujo, vision  # noqa: E402

IMAGENES = [config.IMAGENES / n for n in ("ticket_marzo.png", "ticket_abril.png", "recuento_stock_0604.png", "albaran_0604.png")] + \
           [config.SINTETICAS / n for n in ("ticket_abril_borroso.png", "ticket_abril_muy_borroso.png")]


def ahora() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def guardar_vision() -> None:
    destino = config.GUARDADAS / "vision"
    destino.mkdir(parents=True, exist_ok=True)
    for ruta in IMAGENES:
        tipo = "recuento" if "recuento" in ruta.name else "albaran" if "albaran" in ruta.name else "ticket"
        img = vision.preparar_imagen(ruta.read_bytes())
        libre = vision.pregunta_libre(img)
        ex = vision.extraer(img, tipo)                       # sin caché: lectura real
        comp = vision.COMPROBAR[tipo](ex["datos"]) if ex["valido"] else None
        (destino / f"{ruta.stem}.json").write_text(json.dumps(
            {"fecha": ahora(), "origen": "guardada", "imagen": ruta.name, "sintetica": "sinteticas" in str(ruta),
             "libre": libre, "extraccion": ex, "comprobacion": comp}, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        print(f"vision/{ruta.stem}.json · {ex['tiempos']['segundos']} s · {comp and comp['veredicto']}", flush=True)


def guardar_flujo(solo_casos: list[str] | None = None) -> None:
    casos = import_module("05_flujo").CASOS
    if solo_casos:
        casos = {k: v for k, v in casos.items() if k in solo_casos}
    destino = config.GUARDADAS / "flujo"
    destino.mkdir(parents=True, exist_ok=True)
    for caso, (pregunta, imagen) in casos.items():
        img = (config.IMAGENES / imagen).read_bytes() if imagen else None
        r = flujo.ejecutar(pregunta, img)
        r.update({"fecha": ahora(), "origen": "guardada", "caso": caso, "pregunta": pregunta, "imagen": imagen})
        (destino / f"{caso}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        print(f"flujo/{caso}.json · {r['segundos']} s · verificación {r['verificacion'] or 'limpia'}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Guardar salidas reales (plan B).")
    ap.add_argument("--solo", choices=["vision", "flujo"])
    ap.add_argument("--caso", action="append", help="Con --solo flujo: solo estos casos (se puede repetir).")
    a = ap.parse_args()
    if a.solo in (None, "vision"):
        guardar_vision()
    if a.solo in (None, "flujo"):
        guardar_flujo(a.caso)


if __name__ == "__main__":
    main()
