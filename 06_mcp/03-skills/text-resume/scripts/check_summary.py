#!/usr/bin/env python3
"""QA de un .md de descripción/resumen: fidelidad respecto al texto fuente y, opcionalmente, igualdad con su PDF.

Heurísticas (señalan, no demuestran): cada AVISO hay que comprobarlo a mano contra el texto fuente.
 - INVENTADO?: cifras, nombres propios o citas literales del .md que no aparecen en la fuente.
 - OMITIDO?: cifras y nombres frecuentes de la fuente que no aparecen en el .md, y zonas de la fuente poco cubiertas.
Errores (exit 1): .md vacío o sin título, marcadores de relleno (TODO/TBD/XXX en mayúsculas, lorem ipsum, [...]), o PDF cuyo texto no coincide con el .md.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path
from typing import List, Set

from _md import inline_text, norm, parser, plain_tokens
from _ordering import find_texts, order_files

# TODO/TBD/XXX solo en mayúsculas: «todo» es una palabra corriente en español y no debe saltar
PLACEHOLDERS = re.compile(r"\b(?:TODO|TBD|XXX)\b|(?i:lorem ipsum)|\[\.\.\.\]|\[completar\]")
NUMBER = re.compile(r"\d+(?:[.,:]\d+)*")  # 180.000, 3,5 y horas 11:15 cuentan como una cifra
CAPITAL = re.compile(r"(?<![\w])([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]{2,})")
QUOTE = re.compile(r"[“\"«]([^”\"»]{12,}?)[”\"»]")
STOP_LONG = set()  # palabras largas muy comunes se filtran por frecuencia, no por lista
FOOTER = re.compile(r"^pág\. \d+$")


def read_source(path: Path) -> str:
    if path.is_file():
        files = [path]
    else:
        files = order_files(find_texts(path))["files"]
    chunks = []
    for f in files:
        raw = f.read_bytes()
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                chunks.append(raw.decode(enc))
                break
            except UnicodeDecodeError:
                continue
    return "\n".join(chunks)


def md_facts_text(md_text: str) -> dict:
    """Texto visible del .md separado en cuerpo (se comprueba) y títulos (se ignoran para cifras/nombres).
    El código en línea (`parte_1`, rutas…) no es contenido del texto fuente y se excluye."""
    body, heads = [], []
    toks = parser().parse(md_text)
    for i, t in enumerate(toks):
        if t.type == "inline":
            text = "".join(c.content if c.type == "text" else " " for c in (t.children or []) if c.type != "code_inline")
            (heads if toks[i - 1].type == "heading_open" else body).append(text)
    return {"body": "\n".join(body), "heads": heads}


def numbers_of(text: str) -> Counter:
    return Counter(re.sub(r"[.,:]", "", n) for n in NUMBER.findall(text))


def proper_nouns(text: str) -> Counter:
    """Palabras con inicial mayúscula que no abren frase (reduce falsos positivos de inicio de oración)."""
    found: Counter = Counter()
    for line in text.splitlines():
        for m in CAPITAL.finditer(line):
            before = line[:m.start()].rstrip()
            if not before or before[-1] in ".?!¿¡:;|-•*>\"“”»«()":
                continue
            found[norm(m.group(1))] += 1
    return found


def check_pdf(md_text: str, pdf: Path) -> List[str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("error: falta pypdf. Instálalo en un venv: python3 -m pip install -r requirements.txt")
    lines = []
    for page in PdfReader(str(pdf)).pages:
        lines.extend(l for l in (page.extract_text() or "").splitlines() if not FOOTER.match(l.strip()))
    got = re.findall(r"\w+", "\n".join(lines))
    want = plain_tokens(md_text)
    if got == want:
        return []
    sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
    issues = []
    for tag, a1, a2, b1, b2 in sm.get_opcodes():
        if tag != "equal":
            issues.append("{}: .md «{}» ↔ PDF «{}» (palabra nº {})".format(
                tag, " ".join(want[a1:a2][:12]), " ".join(got[b1:b2][:12]), a1))
        if len(issues) >= 8:
            break
    return ["el PDF no coincide con el .md ({} vs {} palabras):".format(len(want), len(got))] + issues


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("--source", type=Path, help="texto fuente (fichero o directorio) contra el que comprobar fidelidad")
    ap.add_argument("--pdf", type=Path, help="PDF generado a partir del .md; se comprueba que dice lo mismo")
    ap.add_argument("--min-ratio", type=float, default=0.05, help="aviso si resumen/fuente es menor (por defecto 5 %%)")
    args = ap.parse_args()

    if not args.markdown.is_file():
        sys.exit("error: no existe {}".format(args.markdown))
    md = args.markdown.read_text(encoding="utf-8")
    errors: List[str] = []
    warnings: List[str] = []

    toks = parser().parse(md)
    if not md.strip():
        errors.append("el .md está vacío")
    if not any(t.type == "heading_open" and t.tag == "h1" for t in toks):
        errors.append("falta un título de nivel 1 (# …)")
    for m in PLACEHOLDERS.finditer(md):
        errors.append("marcador de relleno en el texto: «{}»".format(m.group(0)))

    md_words = len(re.findall(r"\w+", md))
    info = ["{} palabras en el .md".format(md_words)]

    if args.source:
        if not args.source.exists():
            sys.exit("error: no existe {}".format(args.source))
        src = read_source(args.source)
        src_norm = norm(src)
        src_words = len(re.findall(r"\w+", src))
        ratio = md_words / max(src_words, 1)
        info.append("fuente: {} palabras; el .md es el {:.1f} % de la fuente".format(src_words, ratio * 100))
        if src_words > 2000 and ratio < args.min_ratio:
            warnings.append("OMITIDO?: el .md es solo el {:.1f} % de la fuente; se prefiere extenso a perder contenido".format(ratio * 100))

        facts = md_facts_text(md)
        body = facts["body"]
        # 1) Invención: lo que dice el .md y no está en la fuente
        src_nums = numbers_of(src)
        bad_nums = sorted(n for n in numbers_of(body) if n not in src_nums)
        if bad_nums:
            warnings.append("INVENTADO?: cifras que no aparecen en la fuente: " + ", ".join(bad_nums[:30]))
        src_nouns = set(proper_nouns(src)) | set(re.findall(r"\w+", src_norm))
        bad_nouns = sorted({w for w in proper_nouns(body) if w not in src_nouns})
        if bad_nouns:
            warnings.append("INVENTADO?: nombres propios que no aparecen en la fuente: " + ", ".join(bad_nouns[:30]))
        bad_quotes = [q for q in QUOTE.findall(body) if norm(q) not in src_norm]
        for q in bad_quotes[:10]:
            warnings.append("INVENTADO?: cita que no es literal de la fuente: «{}»".format(q[:100]))
        # 2) Omisión: lo importante de la fuente que el .md no menciona
        md_nums = numbers_of(md)
        missing_nums = [n for n, c in numbers_of(src).most_common() if n not in md_nums and (len(n) >= 2)]
        if missing_nums:
            warnings.append("OMITIDO?: cifras de la fuente ausentes del .md: " + ", ".join(missing_nums[:40])
                            + (" … (+{})".format(len(missing_nums) - 40) if len(missing_nums) > 40 else ""))
        md_norm_words = set(re.findall(r"\w+", norm(md)))
        lower_in_src = {norm(w) for w in re.findall(r"\b[a-záéíóúñü]{3,}\b", src)}  # «Entonces»/«pues» no son nombres propios
        missing_nouns = [w for w, c in proper_nouns(src).most_common()
                         if c >= 3 and w not in md_norm_words and w not in lower_in_src]
        if missing_nouns:
            warnings.append("OMITIDO?: nombres frecuentes (≥3 veces) de la fuente ausentes del .md: " + ", ".join(missing_nouns[:30]))
        # 3) Cobertura por zonas: 10 tramos consecutivos de la fuente
        src_tokens = re.findall(r"\w+", src_norm)
        if len(src_tokens) >= 1000:
            step = len(src_tokens) // 10
            counts = Counter(src_tokens)
            weak = []
            for k in range(10):
                part = {w for w in src_tokens[k * step:(k + 1) * step if k < 9 else None] if len(w) >= 6 and counts[w] <= 5}
                if part:
                    cover = len(part & md_norm_words) / len(part)
                    if cover < 0.2:
                        weak.append("{}/10 ({:.0f} %)".format(k + 1, cover * 100))
            if weak:
                warnings.append("OMITIDO?: zonas de la fuente poco cubiertas (décimas partes): " + ", ".join(weak))

    if args.pdf:
        if not args.pdf.is_file():
            errors.append("no existe el PDF {}".format(args.pdf))
        else:
            errors.extend(check_pdf(md, args.pdf))
            if not errors:
                info.append("el PDF coincide palabra por palabra con el .md")

    print("; ".join(info))
    for w in warnings:
        print("AVISO:", w)
    if errors:
        print("FALLO:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("OK" + (" (con {} aviso(s) a revisar contra la fuente)".format(len(warnings)) if warnings else ""))


if __name__ == "__main__":
    main()
