"""Utilidades comunes de Markdown: texto plano esperado (para comparar con el PDF) y normalización."""
from __future__ import annotations

import re
import sys
import unicodedata
from typing import List

try:
    from markdown_it import MarkdownIt
except ImportError:
    sys.exit("error: falta markdown-it-py. Instálalo en un venv: python3 -m pip install -r requirements.txt")


def parser() -> MarkdownIt:
    return MarkdownIt("commonmark").enable("table")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s: str) -> str:
    """Minúsculas, sin acentos y con espacios colapsados: para buscar un texto del resumen en la fuente."""
    return re.sub(r"\s+", " ", strip_accents(s).lower()).strip()


def inline_text(token) -> str:
    out = []
    for c in token.children or []:
        if c.type in ("text", "code_inline"):
            out.append(c.content)
        elif c.type in ("softbreak", "hardbreak"):
            out.append(" ")
        elif c.type == "image":
            out.append(c.content)
    return "".join(out)


def plain_tokens(md_text: str) -> List[str]:
    """Palabras visibles del Markdown, en orden, incluyendo los números de las listas ordenadas."""
    tokens = parser().parse(md_text)
    words: List[str] = []
    stack: List[dict] = []  # contadores de listas ordenadas anidadas
    for t in tokens:
        if t.type == "ordered_list_open":
            stack.append({"n": int(t.attrGet("start") or 1), "ordered": True})
        elif t.type == "bullet_list_open":
            stack.append({"n": 0, "ordered": False})
        elif t.type in ("ordered_list_close", "bullet_list_close"):
            stack.pop()
        elif t.type == "list_item_open" and stack and stack[-1]["ordered"]:
            words.append(str(stack[-1]["n"]))
            stack[-1]["n"] += 1
        elif t.type == "inline":
            words.extend(re.findall(r"\w+", inline_text(t)))
        elif t.type in ("fence", "code_block"):
            words.extend(re.findall(r"\w+", t.content))
    return words
