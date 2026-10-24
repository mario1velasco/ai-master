"""Utilidades comunes de Markdown (copia ampliada de text-resume/scripts/_md.py; duplicada a propósito para que la skill sea autónoma).

- plain_tokens: palabras visibles del .md en orden (lo que debe aparecer en el PDF/DOCX).
- content_words: palabras para comparar contenido entre dos .md (une cortes con guion y palabras con guion).
- escape_text: convierte texto plano en Markdown que se ve igual, sin cambiar ninguna palabra.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter
from typing import List

try:
    from markdown_it import MarkdownIt
except ImportError:
    sys.exit("error: falta markdown-it-py. Instálalo en el venv compartido: python3 scripts/setup_env.py (desde la raíz del repo) y usa .venv/bin/python")

WORD = re.compile(r"\w+")
# [ilegible] / [ilegible: motivo] no aportan palabras; [dudoso: texto] aporta «texto» (marcadores de img-to-text)
ILLEGIBLE = re.compile(r"\[ilegible(?::[^\]]*)?\]", re.IGNORECASE)
DOUBTFUL = re.compile(r"\[dudoso:\s*([^\]]*)\]", re.IGNORECASE)


def parser() -> MarkdownIt:
    return MarkdownIt("commonmark").enable("table")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def inline_text(token) -> str:
    out = []
    for c in token.children or []:
        if c.type in ("text", "code_inline"):
            out.append(c.content)
        elif c.type in ("softbreak", "hardbreak"):
            out.append(" ")
        elif c.type == "image":
            out.append(c.content)
        elif c.type == "html_inline":
            out.append(" ")  # <br>, comentarios…: separan palabras pero no aportan texto
    return "".join(out)


def visible_blocks(md_text: str, list_numbers: bool = True) -> List[str]:
    """Texto visible del Markdown por bloques, en orden; con list_numbers incluye los números de las listas ordenadas."""
    blocks: List[str] = []
    stack: List[dict] = []  # contadores de listas ordenadas anidadas
    for t in parser().parse(md_text):
        if t.type == "ordered_list_open":
            stack.append({"n": int(t.attrGet("start") or 1), "ordered": True})
        elif t.type == "bullet_list_open":
            stack.append({"n": 0, "ordered": False})
        elif t.type in ("ordered_list_close", "bullet_list_close"):
            stack.pop()
        elif t.type == "list_item_open" and stack and stack[-1]["ordered"]:
            if list_numbers:
                blocks.append(str(stack[-1]["n"]))
            stack[-1]["n"] += 1
        elif t.type == "inline":
            blocks.append(inline_text(t))
        elif t.type in ("fence", "code_block"):
            blocks.append(t.content)
    return blocks


def plain_tokens(md_text: str, list_numbers: bool = True) -> List[str]:
    """Palabras visibles del Markdown, en orden (incluye por defecto los números de las listas ordenadas)."""
    return WORD.findall(nfc("\n".join(visible_blocks(md_text, list_numbers))))


# Glifos de viñeta: son marcas de lista (formato), no contenido; el PDF los dibuja y markitdown los deja en el texto
BULLETS = set("•◦▪▫‣⁃●○■□►▶➢➤✓✔·\x7f")


def signs(text: str) -> Counter:
    """Signos visibles (todo lo que no es letra, número ni espacio), sin glifos de viñeta."""
    return Counter(c for c in nfc(text) if not (c.isalnum() or c == "_" or c.isspace()) and c not in BULLETS)


def ordered_items(md_text: str) -> int:
    return sum(1 for t in parser().parse(md_text) if t.type == "list_item_open" and t.markup in (".", ")"))


def join_hyphens(text: str) -> str:
    """«pala-\\nbra» y «auto-escuela» → una sola palabra, para que unir cortes de línea no cuente como cambio."""
    text = re.sub(r"(\w)[-­][ \t]*\n[ \t]*(\w)", r"\1\2", text)
    return re.sub(r"(\w)[-‐‑](?=\w)", r"\1", text)


def content_words(md_text: str, list_numbers: bool = True) -> List[str]:
    """Palabras de contenido de un .md para compararlo con otro .md (sin marcadores [ilegible], con guiones unidos)."""
    md_text = DOUBTFUL.sub(lambda m: m.group(1), ILLEGIBLE.sub(" ", md_text))
    return WORD.findall(nfc(join_hyphens("\n".join(visible_blocks(md_text, list_numbers)))))


def text_words(text: str) -> List[str]:
    """Palabras de un texto plano (mismo criterio que content_words)."""
    return WORD.findall(nfc(join_hyphens(text)))


_SPECIAL = re.compile(r"([\\`*_\[\]<>#|~&!])")


def escape_line(line: str) -> str:
    """Escapa una línea de texto plano para que Markdown la muestre tal cual (mismas palabras y signos)."""
    out = _SPECIAL.sub(r"\\\1", line)
    stripped = out.lstrip(" ")
    indent = out[: len(out) - len(stripped)]
    if len(indent) >= 4:  # 4 espacios = bloque de código: se quita la sangría, no hay palabras que perder
        indent = ""
    m = re.match(r"(\d{1,9})([.)])(\s|$)", stripped)
    if m:  # «1. texto» no debe convertirse en lista numerada
        stripped = m.group(1) + "\\" + stripped[len(m.group(1)):]
    elif re.match(r"[-+=](\s|$)|[-=]+\s*$", stripped):  # viñetas y subrayados de título (--- / ===)
        stripped = "\\" + stripped
    return indent + stripped


def escape_text(text: str) -> str:
    """Texto plano → Markdown: un párrafo por bloque separado por líneas en blanco, conservando los saltos de línea
    (salto duro con dos espacios). No añade ni quita palabras."""
    text = nfc(text.replace("\r\n", "\n").replace("\r", "\n")).replace("\t", "    ")
    paras = [p for p in re.split(r"\n[ \t]*\n", text) if p.strip()]
    out = []
    for p in paras:
        lines = [escape_line(l.rstrip()) for l in p.split("\n") if l.strip()]
        out.append("  \n".join(lines))
    return "\n\n".join(out) + "\n"
