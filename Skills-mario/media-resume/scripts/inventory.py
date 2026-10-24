#!/usr/bin/env python3
"""Inventario de las entradas (audios, imágenes, textos), orden de cada tipo y plan de trabajo.

Crea <output-dir>/trabajo/inventario.json. Código de salida: 0 = todo claro, 3 = hay que PREGUNTAR al usuario
(orden dudoso dentro de un tipo, o entradas de varios tipos sin --sources-order), 1 = error.

Unidades de fuente: cada audio es una unidad (a01, a02…), todas las imágenes forman una (img) y cada texto
es otra (t01…). El orden final del documento se fija con --sources-order, p. ej. «audio,images» o «a01,img,a02».
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from _env import AUDIO_DECODER, AUDIO_SPLIT, IMG_TO_TEXT, TEXT_RESUME, load_module

LONG_AUDIO_MIN = 8.0      # por encima se divide en trozos de ~4 min
CPU_TURBO_FACTOR = 0.35   # minutos de proceso por minuto de audio (turbo, CPU, medido: 75 min -> 25 min)


def read_names(path: Path) -> List[str]:
    return [l.strip() for l in path.read_text().splitlines() if l.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inputs", nargs="+", type=Path, help="ficheros y/o directorios con audios, imágenes o textos")
    ap.add_argument("--output-dir", type=Path, required=True, help="carpeta de salida; el trabajo va en <output-dir>/trabajo")
    ap.add_argument("--audio-order", type=Path, help="fichero con los nombres de los audios, uno por línea, en el orden confirmado")
    ap.add_argument("--images-order", type=Path, help="idem para las imágenes")
    ap.add_argument("--text-order", type=Path, help="idem para los textos")
    ap.add_argument("--sources-order", help="orden entre fuentes: grupos (audio,images,text) y/o unidades (a01,img,t01) separados por comas")
    ap.add_argument("--accept-order", action="store_true", help="aceptar un orden ambiguo (solo si el usuario lo confirmó)")
    args = ap.parse_args()

    a_mod = load_module("order_audio", AUDIO_DECODER / "_ordering.py")
    i_mod = load_module("order_images", IMG_TO_TEXT / "_ordering.py")
    t_mod = load_module("order_texts", TEXT_RESUME / "_ordering.py")
    common = load_module("split_common", AUDIO_SPLIT / "_common.py")

    exts = {"audio": a_mod.AUDIO_EXTS, "images": i_mod.IMAGE_EXTS, "text": t_mod.TEXT_EXTS}
    found: Dict[str, List[Path]] = {"audio": [], "images": [], "text": []}
    unknown: List[Path] = []
    for p in args.inputs:
        if not p.exists():
            sys.exit("error: no existe {}".format(p))
        for f in (sorted(x for x in p.iterdir() if x.is_file()) if p.is_dir() else [p]):
            kind = next((k for k, e in exts.items() if f.suffix.lower() in e), None)
            (found[kind] if kind else unknown).append(f.resolve())
    if not any(found.values()):
        sys.exit("error: no hay audios, imágenes ni textos en las entradas")
    names = [f.name for fs in found.values() for f in fs]
    dups = sorted({n for n in names if names.count(n) > 1})
    if dups:
        sys.exit("error: nombres repetidos en carpetas distintas (renómbralos): " + ", ".join(dups))

    questions: List[str] = []
    ordered: Dict[str, List[Path]] = {}
    order_files = {"audio": args.audio_order, "images": args.images_order, "text": args.text_order}
    mods = {"audio": a_mod, "images": i_mod, "text": t_mod}
    labels = {"audio": "los audios", "images": "las imágenes", "text": "los textos"}
    for kind, files in found.items():
        if not files:
            continue
        if order_files[kind]:
            by_name = {f.name: f for f in files}
            wanted = read_names(order_files[kind])
            missing = [n for n in wanted if n not in by_name] + [n for n in by_name if n not in wanted]
            if missing:
                sys.exit("error: el orden confirmado de {} no coincide con los ficheros: {}".format(labels[kind], ", ".join(missing)))
            ordered[kind] = [by_name[n] for n in wanted]
            continue
        res = mods[kind].order_files(files)
        ordered[kind] = res["files"]
        for w in res["warnings"]:
            print("AVISO ({}): {}".format(labels[kind].split()[-1], w))
        if res["ambiguities"] and not args.accept_order:
            questions.append("Orden de {} dudoso ({}). Propuesto: {}".format(
                labels[kind], "; ".join(res["ambiguities"]), ", ".join(f.name for f in res["files"])))

    units: List[dict] = []
    for n, f in enumerate(ordered.get("audio", []), 1):
        info = common.probe(f)
        minutes = info["duration"] / 60
        units.append({"id": "a{:02d}".format(n), "kind": "audio", "path": str(f), "minutes": round(minutes, 1),
                      "split": minutes > LONG_AUDIO_MIN, "codec": info["codec"]})
    if ordered.get("images"):
        units.append({"id": "img", "kind": "images", "files": [str(f) for f in ordered["images"]]})
    for n, f in enumerate(ordered.get("text", []), 1):
        units.append({"id": "t{:02d}".format(n), "kind": "text", "path": str(f)})

    kinds = [k for k in ("audio", "images", "text") if ordered.get(k)]
    if args.sources_order:
        sources_order = [s.strip() for s in args.sources_order.split(",") if s.strip()]
        valid = set(kinds) | {u["id"] for u in units}
        bad = [s for s in sources_order if s not in valid]
        if bad:
            sys.exit("error: --sources-order contiene valores desconocidos: {} (válidos: {})".format(", ".join(bad), ", ".join(sorted(valid))))
    else:
        sources_order = kinds
        if len(kinds) > 1:
            questions.append("Hay {} a la vez: ¿en qué orden va su contenido en el documento final? (p. ej. «audio,images», «images,audio» "
                             "o intercalado «a01,img,a02»). Propuesto por defecto: {}".format(" y ".join(labels[k].split()[-1] for k in kinds), ",".join(kinds)))

    work = args.output_dir / "trabajo"
    work.mkdir(parents=True, exist_ok=True)
    inv = {"output_dir": str(args.output_dir.resolve()), "units": units, "sources_order": sources_order,
           "ignored": [str(u) for u in unknown]}
    (work / "inventario.json").write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n")

    print("Inventario → {}".format(work / "inventario.json"))
    for u in units:
        if u["kind"] == "audio":
            print("  {}  audio   {}  ({:.1f} min{}, {})".format(u["id"], Path(u["path"]).name, u["minutes"],
                                                                 ", se dividirá en trozos de ~4 min" if u["split"] else "", u["codec"]))
        elif u["kind"] == "images":
            print("  img  imágenes ({}): {}".format(len(u["files"]), ", ".join(Path(f).name for f in u["files"])))
        else:
            print("  {}  texto   {}".format(u["id"], Path(u["path"]).name))
    minutes = sum(u["minutes"] for u in units if u["kind"] == "audio")
    if minutes:
        print("Audio total: {:.0f} min → transcripción estimada ≈ {:.0f} min en CPU con el modelo turbo (≈ 3× tiempo real).".format(
            minutes, minutes * CPU_TURBO_FACTOR))
    if unknown:
        print("AVISO: se ignoran (formato no soportado): " + ", ".join(u.name for u in unknown))
    print("Orden de fuentes: " + ",".join(sources_order))
    if questions:
        print("\nPREGUNTAR AL USUARIO antes de seguir:")
        for q in questions:
            print(" -", q)
        print("(Reejecuta con --audio-order/--images-order/--text-order FICHERO y/o --sources-order cuando responda.)")
        sys.exit(3)


if __name__ == "__main__":
    main()
