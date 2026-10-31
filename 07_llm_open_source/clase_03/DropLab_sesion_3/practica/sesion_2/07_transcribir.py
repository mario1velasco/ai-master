"""Transcribir la llamada con Whisper, en local y en la GPU del Jetson.

Por defecto transcribe CADA CANAL POR SEPARADO (Central y Tienda) y une los
fragmentos por su hora de inicio: así sabemos quién dice cada cosa sin ningún
modelo de «diarización». También puede transcribir la mezcla mono, para comparar.

Para cada palabra Whisper da una probabilidad: las dudosas se marcan en color.

Con --solo-voz, Whisper solo escucha los tramos con voz que detecta la energía
(06_ver_audio.py): no pierde tiempo en silencios ni se inventa frases en ellos.

Uso:
  python practica/sesion_2/07_transcribir.py                         # turbo, por canales
  python practica/sesion_2/07_transcribir.py --modelo small
  python practica/sesion_2/07_transcribir.py --modo mono              # la mezcla: sin saber quién habla
  python practica/sesion_2/07_transcribir.py --modelo large-v3 --solo-voz
  python practica/sesion_2/07_transcribir.py --modelo small --modo mono --pista   # con el vocabulario del negocio

Salida: practica/sesion_2/transcripciones/<modelo>_<modo>.json (segmentos, palabras y probabilidades).

Requisitos (ver docs/sesion_2/02): PyTorch para Jetson (CUDA) y openai-whisper.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from importlib import import_module
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
AUDIO = ROOT / "data" / "audio"
SALIDA = AQUI / "transcripciones"
sys.path.insert(0, str(AQUI))
ver = import_module("06_ver_audio")

CANALES = {"central": "Central · Álex", "tienda": "Tienda · Dani"}
COLOR = {"central": "cyan", "tienda": "yellow", "mezcla": "white"}
DUDOSA = 0.70            # por debajo de esta probabilidad, la palabra se marca
# Pista de contexto (initial_prompt): el vocabulario del negocio que Whisper no puede adivinar.
PISTA = ("Llamada de DropLab entre Álex, de Operaciones, y Dani, de la tienda de Malasaña. "
         "Pack 4, tote bag, Street One.")


def cargar_whisper(modelo: str):
    try:
        import torch
        import whisper
    except ImportError:
        raise SystemExit("Falta openai-whisper o PyTorch. Instalación paso a paso: docs/sesion_2/02_audio_whisper.md")
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    t0 = time.time()
    m = whisper.load_model(modelo, device=dispositivo)
    return m, dispositivo, time.time() - t0


def leer_mono(ruta: Path) -> np.ndarray:
    audio, _, _ = ver.leer_wav(ruta)
    return audio.mean(axis=0)


def transcribir(m, audio: np.ndarray, quien: str, dispositivo: str, solo_voz: bool, pista: bool = False) -> list[dict]:
    """Devuelve los segmentos de un audio con su interlocutor, tiempos, texto y palabras."""
    opciones = dict(language="es", word_timestamps=True, condition_on_previous_text=False,
                    fp16=(dispositivo == "cuda"), initial_prompt=PISTA if pista else None)
    if solo_voz:
        # Whisper solo decodifica estos intervalos: [inicio1, fin1, inicio2, fin2, …], con 0,2 s de margen
        clip = []
        for _, inicio, fin in ver.detectar_turnos(audio[None, :]):
            clip += [round(max(0.0, inicio - 0.2), 2), round(fin + 0.2, 2)]
        opciones["clip_timestamps"] = clip
    r = m.transcribe(audio.astype(np.float32), **opciones)
    segmentos = []
    for s in r["segments"]:
        palabras = [{"palabra": w["word"].strip(), "inicio": round(w["start"], 2), "fin": round(w["end"], 2),
                     "p": round(float(w["probability"]), 3)} for w in s.get("words", [])]
        segmentos.append({"quien": quien, "inicio": round(s["start"], 2), "fin": round(s["end"], 2),
                          "texto": s["text"].strip(), "palabras": palabras,
                          "prob_silencio": round(float(s.get("no_speech_prob", 0)), 3)})
    return segmentos


def imprimir(segmentos: list[dict]) -> None:
    from rich.console import Console
    from rich.text import Text
    c = Console()
    for s in segmentos:
        linea = Text(f"[{s['inicio']:6.1f}–{s['fin']:6.1f}] ", style="dim")
        linea.append(f"{CANALES.get(s['quien'], 'Mezcla'):15} ", style=f"bold {COLOR[s['quien']]}")
        for w in s["palabras"] or [{"palabra": s["texto"], "p": 1.0}]:
            estilo = "bold white on red" if w["p"] < 0.5 else ("black on yellow" if w["p"] < DUDOSA else "")
            linea.append(w["palabra"], style=estilo)
            linea.append(" ")
        c.print(linea)
    dudosas = [(w["palabra"], w["p"]) for s in segmentos for w in s["palabras"] if w["p"] < DUDOSA]
    c.print(f"\n[dim]Palabras dudosas (p < {DUDOSA}): {len(dudosas)} de "
            f"{sum(len(s['palabras']) for s in segmentos)}[/dim]  "
            + ", ".join(f"{p} ({v:.2f})" for p, v in dudosas))


def main() -> None:
    ap = argparse.ArgumentParser(description="Transcribir la llamada con Whisper (local, GPU).")
    ap.add_argument("--modelo", default="turbo", help="tiny · base · small · medium · turbo · large-v3")
    ap.add_argument("--modo", choices=["canales", "mono"], default="canales")
    ap.add_argument("--solo-voz", action="store_true", help="Transcribir solo los tramos con voz (energía).")
    ap.add_argument("--pista", action="store_true", help="Dar a Whisper el vocabulario del negocio (initial_prompt).")
    a = ap.parse_args()
    warnings.filterwarnings("ignore")

    m, dispositivo, carga = cargar_whisper(a.modelo)
    print(f"Modelo {a.modelo} en {dispositivo.upper()} · carga {carga:.1f} s")
    t0 = time.time()
    if a.modo == "canales":
        segmentos = []
        for quien in CANALES:
            segmentos += transcribir(m, leer_mono(AUDIO / f"llamada_0704_{quien}.wav"), quien, dispositivo, a.solo_voz,
                                     a.pista)
        segmentos.sort(key=lambda s: s["inicio"])          # se intercalan los dos canales por tiempo
    else:
        segmentos = transcribir(m, leer_mono(AUDIO / "llamada_0704_escucha_mono.wav"), "mezcla", dispositivo,
                                a.solo_voz, a.pista)
    segundos = time.time() - t0
    duracion = 113.3
    print(f"Transcripción: {segundos:.1f} s para {duracion:.0f} s de audio "
          f"({duracion / segundos:.1f} veces más rápido que en tiempo real)\n")
    imprimir(segmentos)

    SALIDA.mkdir(exist_ok=True)
    nombre = f"{a.modelo}_{a.modo}{'_solo-voz' if a.solo_voz else ''}{'_pista' if a.pista else ''}"
    destino = SALIDA / f"{nombre}.json"
    destino.write_text(json.dumps({"modelo": a.modelo, "modo": a.modo, "solo_voz": a.solo_voz, "pista": a.pista,
                                   "dispositivo": dispositivo, "segundos_carga": round(carga, 1),
                                   "segundos_transcripcion": round(segundos, 1), "segmentos": segmentos},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {destino.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
