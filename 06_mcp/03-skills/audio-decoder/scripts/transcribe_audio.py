#!/usr/bin/env python3
"""Transcribe en local (faster-whisper) todos los audios de un directorio, en orden, a un único .txt."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Optional

from _ordering import find_audio, order_files

PARAGRAPH_GAP = 2.0  # s de pausa a partir de los cuales se abre un párrafo nuevo


def load_model(name: str, device: str, compute_type: str, model_dir: Optional[str]):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("error: falta faster-whisper. Instálalo en un venv: python3 -m pip install -r requirements.txt")
    attempts = [("cuda", "float16"), ("cpu", "int8")] if device == "auto" else [(device, compute_type or ("float16" if device == "cuda" else "int8"))]
    for dev, ctype in attempts:
        try:
            model = WhisperModel(name, device=dev, compute_type=compute_type or ctype, download_root=model_dir)
            if dev == "cuda":  # los errores de librerías CUDA faltantes saltan al transcribir, no al cargar
                list(model.transcribe(__import__("numpy").zeros(16000, dtype="float32"))[0])
            return model, dev
        except Exception as exc:  # noqa: BLE001 - cualquier fallo de GPU cae a CPU en modo auto
            if device != "auto" or dev == "cpu":
                raise
            print("aviso: GPU no utilizable ({}); uso CPU".format(str(exc).splitlines()[0][:100]), file=sys.stderr)
    raise RuntimeError("sin dispositivo disponible")


def collapse_repeats(text: str, max_repeats: int = 3) -> str:
    """Whisper a veces entra en bucle ('no, no, no, …'): deja como mucho `max_repeats` repeticiones seguidas."""
    pattern = re.compile(r"((?:\b[\wáéíóúüñÁÉÍÓÚÜÑ']+\b[,.¿?¡!]*\s+){1,4}?)\1{%d,}" % max_repeats, re.IGNORECASE)
    return pattern.sub(lambda m: m.group(1) * max_repeats, text + " ").strip()


MAX_WORDS_PER_SECOND = 10.0  # habla muy rápida ≈ 6-7 (los timestamps de Whisper son imprecisos: 6 descarta habla real); >10 es un eco/bucle


def clean_segments(segments):
    """Descarta segmentos con velocidad de habla imposible (p. ej. 4 palabras en 0,1 s): bucles de Whisper entre segmentos."""
    kept = []
    for s in segments:
        words = len(s["text"].split())
        if words >= 3 and words / max(s["end"] - s["start"], 0.01) > MAX_WORDS_PER_SECOND:
            continue
        kept.append(s)
    return kept


def fmt_ts(seconds: float) -> str:
    s = int(seconds)
    return "{:02d}:{:02d}:{:02d}".format(s // 3600, (s % 3600) // 60, s % 60)


def format_text(segments, offset: float, timestamps: bool) -> str:
    if timestamps:
        return "\n".join("[{}] {}".format(fmt_ts(offset + s["start"]), s["text"]) for s in segments)
    paragraphs: List[str] = []
    current: List[str] = []
    prev_end = None
    for s in segments:
        if prev_end is not None and s["start"] - prev_end >= PARAGRAPH_GAP and current:
            paragraphs.append(" ".join(current))
            current = []
        current.append(s["text"])
        prev_end = s["end"]
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path, help="directorio con los audios")
    p.add_argument("--output-dir", type=Path, help="por defecto <directorio>/transcripcion")
    p.add_argument("--files-from", type=Path, help="fichero de texto con un nombre de audio por línea, en el orden confirmado")
    p.add_argument("--accept-order", action="store_true", help="aceptar un orden marcado como ambiguo (solo si el usuario lo confirmó)")
    p.add_argument("--model", default="turbo", help="tiny|base|small|medium|large-v3|turbo o ruta local (por defecto turbo)")
    p.add_argument("--language", default=None, help="código (es, en…); por defecto se detecta en el primer audio y se reutiliza")
    p.add_argument("--task", choices=["transcribe", "translate"], default="transcribe", help="translate = traducir al inglés")
    p.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    p.add_argument("--compute-type", default=None, help="int8, float16… (por defecto según dispositivo)")
    p.add_argument("--beam-size", type=int, default=5)
    p.add_argument("--no-vad", action="store_true", help="desactivar el filtro de voz (Silero VAD integrado)")
    p.add_argument("--timestamps", action="store_true", help="una línea por segmento con [hh:mm:ss] acumulado entre archivos")
    p.add_argument("--file-headers", action="store_true", help="añadir '=== nombre ===' antes de cada archivo")
    p.add_argument("--model-dir", default=None, help="carpeta donde guardar/leer los modelos descargados")
    p.add_argument("--force", action="store_true", help="retranscribir aunque ya exista la parte")
    args = p.parse_args()

    if not args.directory.is_dir():
        sys.exit("error: {} no es un directorio".format(args.directory))

    if args.files_from:
        names = [l.strip() for l in args.files_from.read_text().splitlines() if l.strip()]
        files = [args.directory / n for n in names]
        missing = [str(f) for f in files if not f.is_file()]
        if missing:
            sys.exit("error: no existen: " + ", ".join(missing))
    else:
        found = find_audio(args.directory)
        if not found:
            sys.exit("error: no hay audios en {}".format(args.directory))
        result = order_files(found)
        if result["ambiguities"] and not args.accept_order:
            print("El orden es ambiguo; pregunta al usuario y usa --files-from (o --accept-order):", file=sys.stderr)
            for a in result["ambiguities"]:
                print(" -", a, file=sys.stderr)
            sys.exit(3)
        for w in result["warnings"]:
            print("AVISO:", w, file=sys.stderr)
        files = result["files"]

    out_dir = args.output_dir or args.directory / "transcripcion"
    parts_dir = out_dir / "partes"
    parts_dir.mkdir(parents=True, exist_ok=True)

    model, device = load_model(args.model, args.device, args.compute_type, args.model_dir)
    print("Modelo {} en {} · {} archivo(s)".format(args.model, device, len(files)), file=sys.stderr)

    language = args.language
    offset = 0.0
    manifest = {"directory": str(args.directory.resolve()), "model": args.model, "device": device,
                "task": args.task, "language": None, "files": []}
    texts: List[str] = []
    t_total = time.time()
    for i, f in enumerate(files, 1):
        part = parts_dir / "{:03d}_{}.json".format(i, f.stem)
        if part.exists() and not args.force:
            data = json.loads(part.read_text())
            language = language or data["language"]  # sin esto, si todo viene de caché el idioma queda en None
            print("[{}/{}] {} (reutilizado)".format(i, len(files), f.name), file=sys.stderr)
        else:
            t0 = time.time()
            segs, info = model.transcribe(str(f), language=language, task=args.task, beam_size=args.beam_size,
                                          vad_filter=not args.no_vad,
                                          condition_on_previous_text=False)  # evita arrastrar bucles de repetición
            language = language or info.language  # el primer archivo fija el idioma de los demás
            segments = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": collapse_repeats(s.text.strip())}
                        for s in segs if s.text.strip()]
            data = {"file": f.name, "duration": round(info.duration, 2), "language": info.language, "segments": segments}
            part.write_text(json.dumps(data, ensure_ascii=False, indent=1))
            print("[{}/{}] {} · {:.0f} s de audio en {:.0f} s".format(i, len(files), f.name, info.duration, time.time() - t0), file=sys.stderr)
        text = format_text(clean_segments(data["segments"]), offset, args.timestamps)  # al formatear: corrige también partes en caché
        (parts_dir / "{:03d}_{}.txt".format(i, f.stem)).write_text(text + "\n")
        texts.append(("=== {} ===\n".format(f.name) if args.file_headers else "") + text)
        manifest["files"].append({"order": i, "file": f.name, "duration": data["duration"], "offset": round(offset, 2),
                                  "language": data["language"], "words": len(text.split())})
        offset += data["duration"]
    manifest["language"] = language
    manifest["total_duration"] = round(offset, 2)
    manifest["elapsed_seconds"] = round(time.time() - t_total, 1)

    sep = "\n\n" if not args.timestamps else "\n"
    full = out_dir / "transcripcion_completa.txt"
    full.write_text(sep.join(t for t in texts if t) + "\n")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("\nListo: {} ({} palabras, idioma {}, {:.0f} s)".format(
        full, sum(f["words"] for f in manifest["files"]), language, manifest["elapsed_seconds"]))


if __name__ == "__main__":
    main()
