#!/usr/bin/env python3
"""Monta el Markdown final de cada entrada, lo verifica, genera los formatos pedidos (md/pdf/docx) y los entrega.

Por unidad toma final.md (o, si no existe, la referencia con AVISO «sin revisar»). Referencia = bruto.md
(documentos, hojas, textos, audios), img/transcripcion.md (PDF escaneado) o la parte de img-to-text
(trabajo/imagenes/partes/NN_<nombre>.md) en imágenes sueltas. Pasa check_markdown.py final ↔ referencia.

Modo separado: <salida>/<nombre>.<fmt> por entrada. Modo combinado: <salida>/<--name>.<fmt> con todas las
entradas en orden, separadas por <!-- fuente N: nombre --> y --- (sin títulos inventados).
Cada .pdf/.docx se comprueba con check_output.py contra su .md. Falla (exit 1) si algo no cuadra.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from _env import SCRIPTS, venv_python
from convert_docs import unit_dir

WIDE_TABLE_COLS = 7  # a partir de aquí el PDF se genera apaisado


def find_sources(work: Path, u: dict) -> Tuple[Optional[Path], Optional[Path], List[str]]:
    """Devuelve (final, referencia, problemas)."""
    udir = unit_dir(work, u)
    problems: List[str] = []
    if u["kind"] == "image":
        stem = Path(u["name"]).stem
        parts = sorted((work / "imagenes" / "partes").glob("[0-9][0-9]_{}.md".format(glob_escape(stem))))
        ref = parts[0] if parts else None
        if not ref:
            problems.append("falta la transcripción de la imagen (trabajo/imagenes/partes/NN_{}.md, flujo de img-to-text)".format(stem))
    elif u.get("scanned"):
        ref = udir / "img" / "transcripcion.md"
        if not ref.is_file():
            problems.append("falta {} (transcribe las páginas con img-to-text y join_parts.py)".format(ref))
            ref = None
    else:
        ref = udir / "bruto.md"
        if not ref.is_file():
            problems.append("falta {} ({})".format(ref, "process_audio.py" if u["kind"] == "audio" else "convert_docs.py"))
            ref = None
    final = udir / "final.md"
    return (final if final.is_file() else ref), ref, problems


def glob_escape(s: str) -> str:
    return re.sub(r"([\[\]*?])", r"[\1]", s)


def max_table_cols(md: str) -> int:
    return max((len(re.findall(r"(?<!\\)\|", l)) - 1 for l in md.split("\n") if l.strip().startswith("|")), default=0)


def run(cmd: List[str]) -> int:
    return subprocess.run(cmd).returncode


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work_dir", type=Path, help="carpeta trabajo/")
    ap.add_argument("--name", default="documento", help="nombre del documento combinado (sin extensión)")
    ap.add_argument("--landscape", choices=["auto", "si", "no"], default="auto", help="PDF apaisado (auto: tablas de ≥7 columnas)")
    args = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)  # que los mensajes salgan en orden con los de los subprocesos

    work = args.work_dir.resolve()
    inv = json.loads((work / "inventario.json").read_text())
    formats, mode = inv["formats"], inv["mode"]
    if not formats:
        sys.exit("error: no hay formatos de salida: pregunta al usuario y reejecuta inventory.py con --formats")
    out_dir = Path(inv["output_dir"])
    py = venv_python()

    pieces: List[Tuple[dict, Path]] = []
    problems: List[str] = []
    pending: List[str] = []
    for u in inv["units"]:
        final, ref, probs = find_sources(work, u)
        problems.extend("{} ({}): {}".format(u["id"], u["name"], p) for p in probs)
        if not final:
            continue
        print("\n=== {} · {} ===".format(u["id"], u["name"]))
        if final == ref:
            print("AVISO: no hay final.md: se entrega la extracción sin revisar el formato ({})".format(ref.name))
            code = run([py, str(SCRIPTS / "check_markdown.py"), str(final)])
        else:
            code = run([py, str(SCRIPTS / "check_markdown.py"), str(final), "--reference", str(ref)])
        if code != 0:
            problems.append("{} ({}): check_markdown.py falló (ver arriba)".format(u["id"], u["name"]))
        st_path = unit_dir(work, u) / "estado.json"
        if st_path.is_file():
            st = json.loads(st_path.read_text())
            text = final.read_text(encoding="utf-8")
            for n in st.get("needs", []):
                if "SIN TEXTO" in n and "<!-- transcripcion:" not in text:
                    problems.append("{} ({}): {} — y final.md no tiene ningún bloque <!-- transcripcion: … -->".format(u["id"], u["name"], n))
                elif "incrustada" in n and "<!-- transcripcion:" not in text:
                    pending.append("{} ({}): {}".format(u["id"], u["name"], n))
        pieces.append((u, final))
    if problems:
        print("\nFALLO: no se puede entregar todavía:")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    # Markdown de salida (siempre se genera en trabajo/salida; se entrega si se pidió «md»)
    stage = work / "salida"
    stage.mkdir(exist_ok=True)
    docs: List[Path] = []
    if mode == "combinado":
        chunks = ["<!-- fuente {}: {} -->\n\n{}".format(n, u["name"], f.read_text(encoding="utf-8").strip())
                  for n, (u, f) in enumerate(pieces, 1)]
        target = stage / (args.name + ".md")
        target.write_text("\n\n---\n\n".join(chunks) + "\n", encoding="utf-8")
        docs.append(target)
    else:
        stems = [Path(u["name"]).stem for u, _ in pieces]
        for u, f in pieces:
            stem = Path(u["name"]).stem
            name = stem if stems.count(stem) == 1 else "{}_{}".format(stem, Path(u["name"]).suffix.lstrip(".").lower())
            target = stage / (name + ".md")
            target.write_text(f.read_text(encoding="utf-8").strip() + "\n", encoding="utf-8")
            docs.append(target)

    ok = True
    delivered: List[Path] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for md in docs:
        outputs = []
        if "pdf" in formats:
            pdf = md.with_suffix(".pdf")
            cmd = [py, str(SCRIPTS / "md_to_pdf.py"), str(md), "--output", str(pdf)]
            text = md.read_text(encoding="utf-8")
            if args.landscape == "si" or (args.landscape == "auto" and max_table_cols(text) >= WIDE_TABLE_COLS):
                cmd.append("--landscape")
            ok &= run(cmd) == 0
            outputs.append(pdf)
        if "docx" in formats:
            dx = md.with_suffix(".docx")
            ok &= run([py, str(SCRIPTS / "md_to_docx.py"), str(md), "--output", str(dx)]) == 0
            outputs.append(dx)
        if outputs and ok:
            ok &= run([py, str(SCRIPTS / "check_output.py"), str(md)] + [str(o) for o in outputs]) == 0
        if "md" in formats:
            outputs.insert(0, md)
        for o in outputs:
            dest = out_dir / o.name
            if dest.exists() and dest.resolve() in {Path(u["path"]).resolve() for u in inv["units"]}:
                sys.exit("error: {} es una de las entradas: no se sobrescribe".format(dest))
            if o.is_file():
                dest.write_bytes(o.read_bytes())
                delivered.append(dest)
    if not ok:
        sys.exit("FALLO en la generación o verificación de los formatos de salida (ver arriba)")

    print("\nEntregado en {}:".format(out_dir))
    for d in delivered:
        print("  -", d.name)
    for p in pending:
        print("PENDIENTE (decisión del usuario):", p)
    print("Revisa a ojo: el PDF (pdftoppm -r 70 -png) y el DOCX; y menciona en la entrega los AVISOS de arriba.")


if __name__ == "__main__":
    main()
