"""Utilidades de texto comunes: normalización y palabras visibles de un Markdown."""
from __future__ import annotations

import re
import sys
import unicodedata
from typing import List

try:
    from markdown_it import MarkdownIt
except ImportError:
    sys.exit("error: falta markdown-it-py. Instálalo en el venv compartido: python3 scripts/setup_env.py (desde la raíz del repo) y usa .venv/bin/python")

# Marcadores de la transcripción: [ilegible] / [ilegible: motivo] no aportan palabras; [dudoso: texto] aporta «texto»
ILLEGIBLE = re.compile(r"\[ilegible(?::[^\]]*)?\]", re.IGNORECASE)  # también «[ilegible: motivo]» (anotación, no texto de la imagen)
DOUBTFUL = re.compile(r"\[dudoso:\s*([^\]]*)\]", re.IGNORECASE)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(s).lower()).strip()


def words_of(s: str) -> List[str]:
    return re.findall(r"\w+", norm(s))


def clean_markers(text: str) -> str:
    return DOUBTFUL.sub(lambda m: m.group(1), ILLEGIBLE.sub(" ", text))


def visible_text(md_text: str) -> str:
    """Texto visible (títulos, párrafos, listas, tablas, código); sin comentarios HTML ni sintaxis Markdown."""
    parts: List[str] = []
    for t in MarkdownIt("commonmark").enable("table").parse(md_text):
        if t.type == "inline":
            for c in t.children or []:
                if c.type in ("text", "code_inline", "image"):
                    parts.append(c.content)
                elif c.type in ("softbreak", "hardbreak"):
                    parts.append("\n")
            parts.append("\n")
        elif t.type in ("fence", "code_block"):
            parts.append(t.content + "\n")
    return clean_markers("".join(parts))
