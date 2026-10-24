#!/usr/bin/env python3
"""Inventario de las entradas: tipo de cada fichero, orden, formatos de salida y plan → <output-dir>/trabajo/inventario.json.

Código de salida: 0 = todo claro, 3 = hay que PREGUNTAR al usuario (formatos de salida sin elegir, modo
separado/combinado sin elegir, u orden dudoso), 1 = error.

Cada fichero es una unidad (u01, u02…). Tipos:
  doc    documentos que lee markitdown (pdf, docx, pptx, html, epub, ipynb, json, xml…)
  sheet  hojas de cálculo y CSV (conversor propio: markitdown cambia valores, p. ej. 10 → 10.0 y vacío → NaN)
  office formatos que primero se pasan a docx/pptx/xlsx con LibreOffice (doc, odt, rtf, ppt, odp, ods)
  text   .txt / .md
  image  imágenes (las transcribe img-to-text)
  audio  audios (audio-split + audio-decoder)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List

from _env import AUDIO_DECODER, AUDIO_SPLIT, IMG_TO_TEXT, load_module

DOC_EXTS = {".pdf", ".docx", ".pptx", ".html", ".htm", ".xhtml", ".epub", ".ipynb", ".json", ".jsonl", ".xml", ".rss", ".atom"}
SHEET_EXTS = {".xlsx", ".xlsm", ".xls", ".csv", ".tsv"}
OFFICE_EXTS = {".doc": "docx", ".odt": "docx", ".rtf": "docx", ".wpd": "docx",
               ".ppt": "pptx", ".odp": "pptx", ".pps": "pptx", ".ppsx": "pptx",
               ".ods": "xlsx"}
TEXT_EXTS = {".txt", ".md", ".markdown", ".text", ".log"}
FORMATS = ("md", "pdf", "docx")
LONG_AUDIO_MIN = 8.0      # por encima se divide en trozos de ~4 min
CPU_TURBO_FACTOR = 0.35   # minutos de proceso por minuto de audio (turbo, CPU; medido en media-resume)
MIN_PAGE_CHARS = 25       # una página de PDF con menos caracteres de texto se considera sin capa de texto


def read_names(path: Path) -> List[str]:
    return [l.strip() for l in path.read_text().splitlines() if l.strip()]


def pdf_pages(path: Path) -> dict:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("error: falta pypdf. Ejecuta desde la raíz del repo: python3 scripts/setup_env.py")
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return {"error": "PDF cifrado con contraseña"}
        texts = [(p.extract_text() or "") for p in reader.pages]
    except Exception as e:  # PDF dañado: lo dirá también markitdown, pero mejor saberlo ya
        return {"error": "no se pudo leer el PDF ({})".format(e)}
    empty = [i + 1 for i, t in enumerate(texts) if len(t.strip()) < MIN_PAGE_CHARS]
    return {"pages": len(texts), "textless_pages": empty, "scanned": bool(texts) and len(empty) * 2 >= len(texts)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", type=Path, help="ficheros y/o directorios")
    ap.add_argument("--output-dir", type=Path, required=True, help="carpeta de salida (nueva); el trabajo va en <output-dir>/trabajo")
    ap.add_argument("--formats", help="formatos de salida elegidos POR EL USUARIO, separados por comas: md,pdf,docx")
    ap.add_argument("--mode", choices=["separado", "combinado"], help="con varias entradas: un documento por entrada o uno combinado")
    ap.add_argument("--order", type=Path, help="fichero con los nombres de las entradas, uno por línea, en el orden confirmado")
    ap.add_argument("--accept-order", action="store_true", help="aceptar un orden dudoso (solo si el usuario lo confirmó)")
    args = ap.parse_args()

    i_mod = load_module("order_images", IMG_TO_TEXT / "_ordering.py")
    a_mod = load_module("order_audio", AUDIO_DECODER / "_ordering.py")
    kinds = [("doc", DOC_EXTS), ("sheet", SHEET_EXTS), ("office", set(OFFICE_EXTS)), ("text", TEXT_EXTS),
             ("image", i_mod.IMAGE_EXTS), ("audio", a_mod.AUDIO_EXTS)]

    files: List[Path] = []
    unknown: List[Path] = []
    from_dirs = False
    for p in args.inputs:
        if not p.exists():
            sys.exit("error: no existe {}".format(p))
        if p.is_dir():
            from_dirs = True
            cand = sorted(x for x in p.iterdir() if x.is_file() and not x.name.startswith("."))
        else:
            cand = [p]
        for f in cand:
            (files if any(f.suffix.lower() in e for _, e in kinds) else unknown).append(f.resolve())
    if not files:
        sys.exit("error: ninguna entrada tiene un formato soportado (ver references/formatos_entrada.md)")
    names = [f.name for f in files]
    dups = sorted({n for n in names if names.count(n) > 1})
    if dups:
        sys.exit("error: nombres repetidos en carpetas distintas (renómbralos): " + ", ".join(dups))

    out_dir = args.output_dir.resolve()
    for f in files:
        if out_dir == f.parent or out_dir in f.parents:
            sys.exit("error: la carpeta de salida no puede contener las entradas ({}): usa una carpeta nueva".format(f.name))

    questions: List[str] = []
    # Formatos de salida: los elige el usuario, nunca el script
    formats: List[str] = []
    if args.formats:
        formats = [f.strip().lower().lstrip(".") for f in args.formats.split(",") if f.strip()]
        bad = [f for f in formats if f not in FORMATS]
        if bad or not formats:
            sys.exit("error: --formats admite solo {} (recibido: {})".format(", ".join(FORMATS), args.formats))
        formats = [f for f in FORMATS if f in formats]
    else:
        questions.append("¿En qué formato(s) quiere el resultado? md, pdf y/o docx (se pueden elegir varios).")
    mode = args.mode or "separado"
    if len(files) > 1 and not args.mode:
        questions.append("Hay {} entradas: ¿un documento por entrada (separado) o uno solo con todo en orden (combinado)?".format(len(files)))

    # Orden
    if args.order:
        by_name = {f.name: f for f in files}
        wanted = read_names(args.order)
        missing = [n for n in wanted if n not in by_name] + [n for n in by_name if n not in wanted]
        if missing:
            sys.exit("error: el orden confirmado no coincide con las entradas: {}".format(", ".join(missing)))
        files = [by_name[n] for n in wanted]
    elif from_dirs and len(files) > 1:
        res = i_mod.order_files(files)  # orden natural genérico (pag_2 antes que pag_10)
        files = res["files"]
        for w in res["warnings"]:
            print("AVISO (orden):", w)
        if res["ambiguities"] and not args.accept_order:
            q = "Orden de las entradas dudoso ({}). Propuesto: {}".format("; ".join(res["ambiguities"]), ", ".join(f.name for f in files))
            if mode == "combinado" or not args.mode:
                questions.append(q)
            else:
                print("AVISO (orden): {} — en modo separado no afecta al contenido".format(q))

    units: List[dict] = []
    problems: List[str] = []
    for n, f in enumerate(files, 1):
        kind = next(k for k, e in kinds if f.suffix.lower() in e)
        u: Dict = {"id": "u{:02d}".format(n), "kind": kind, "path": str(f), "name": f.name}
        if kind == "office":
            u["convert_to"] = OFFICE_EXTS[f.suffix.lower()]
            if not (shutil.which("soffice") or shutil.which("libreoffice")):
                problems.append("{}: {} necesita LibreOffice (soffice) para convertirse; instálalo o expórtalo a {} a mano".format(
                    u["id"], f.name, u["convert_to"]))
        elif kind == "doc" and f.suffix.lower() == ".pdf":
            info = pdf_pages(f)
            if "error" in info:
                problems.append("{}: {}: {}".format(u["id"], f.name, info["error"]))
            u.update(info)
        elif kind == "audio":
            common = load_module("split_common", AUDIO_SPLIT / "_common.py")
            info = common.probe(f)
            u["minutes"] = round(info["duration"] / 60, 1)
            u["split"] = u["minutes"] > LONG_AUDIO_MIN
        units.append(u)
    if problems:
        print("FALLO:")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    work = out_dir / "trabajo"
    work.mkdir(parents=True, exist_ok=True)
    inv = {"output_dir": str(out_dir), "formats": formats, "mode": mode if len(files) > 1 else "separado",
           "units": units, "ignored": [str(u) for u in unknown]}
    (work / "inventario.json").write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n")

    print("Inventario → {}".format(work / "inventario.json"))
    labels = {"doc": "documento", "sheet": "hoja/CSV", "office": "office", "text": "texto", "image": "imagen", "audio": "audio"}
    for u in units:
        extra = ""
        if u["kind"] == "office":
            extra = " (se convertirá a {} con LibreOffice)".format(u["convert_to"])
        elif u.get("pages") is not None:
            if u["scanned"]:
                extra = " ({} pág., ESCANEADO → se transcribe como imágenes)".format(u["pages"])
            elif u["textless_pages"]:
                extra = " ({} pág., SIN TEXTO en pág. {})".format(u["pages"], u["textless_pages"][:15])
            else:
                extra = " ({} pág.)".format(u["pages"])
        elif u["kind"] == "audio":
            extra = " ({:.1f} min{})".format(u["minutes"], ", se dividirá en trozos" if u["split"] else "")
        print("  {}  {:<10} {}{}".format(u["id"], labels[u["kind"]], u["name"], extra))
    minutes = sum(u.get("minutes", 0) for u in units)
    if minutes:
        print("Audio total: {:.0f} min → transcripción estimada ≈ {:.0f} min en CPU con el modelo turbo.".format(minutes, minutes * CPU_TURBO_FACTOR))
    if any(u["kind"] == "image" or u.get("scanned") for u in units):
        print("Hay imágenes o PDF escaneados: se transcriben con el flujo de img-to-text (lectura con visión + OCR de control).")
    if unknown:
        print("AVISO: se ignoran (formato no soportado): " + ", ".join(u.name for u in unknown))
    print("Formatos de salida: {} · modo: {}".format(",".join(formats) or "(sin elegir)", inv["mode"]))
    if questions:
        print("\nPREGUNTAR AL USUARIO antes de seguir:")
        for q in questions:
            print(" -", q)
        print("(Reejecuta con --formats md,pdf,docx, --mode separado|combinado y/o --order FICHERO cuando responda.)")
        sys.exit(3)


if __name__ == "__main__":
    main()
