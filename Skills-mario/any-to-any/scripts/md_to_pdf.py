#!/usr/bin/env python3
"""Convierte un .md a PDF (A4) sin perder ni añadir contenido. Usa markdown-it-py + reportlab (sin dependencias del sistema).

Copia de text-resume/scripts/md_to_pdf.py (duplicada a propósito): si cambias una, cambia la otra.
--landscape genera A4 apaisado (tablas anchas).
Los comentarios HTML (<!-- … -->) no se imprimen.

Soporta: títulos #–####, párrafos, negrita/cursiva/código, enlaces, listas (anidadas y numeradas),
citas, bloques de código, tablas y separadores. No soporta imágenes ni HTML embebido.
Caracteres que la fuente principal no tiene (CJK, emojis…): se busca con fc-list una fuente TrueType de reserva
que los tenga; si no hay ninguna, falla con la lista de caracteres en vez de perderlos en silencio.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape

from _md import inline_text, parser

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (CondPageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle, XPreformatted)
except ImportError:
    sys.exit("error: falta reportlab. Instálalo en el venv compartido: python3 scripts/setup_env.py (desde la raíz del repo) y usa .venv/bin/python")

DEJAVU_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu", "/Library/Fonts", "C:/Windows/Fonts"]
INK = colors.HexColor("#1f2933")
ACCENT = colors.HexColor("#17324D")


def setup_fonts(md_text: str, font_path: Optional[Path]) -> dict:
    """Helvetica (incluye cursiva) si el texto cabe en cp1252; si no, DejaVu Sans (cobertura Unicode)."""
    try:
        md_text.encode("cp1252")
        needs_unicode = False
    except UnicodeEncodeError:
        needs_unicode = True
    if not needs_unicode and not font_path:
        return {"body": "Helvetica", "mono": "Courier"}
    regular = font_path
    bold = None
    if not regular:
        for d in DEJAVU_DIRS:
            if (Path(d) / "DejaVuSans.ttf").is_file():
                regular, bold = Path(d) / "DejaVuSans.ttf", Path(d) / "DejaVuSans-Bold.ttf"
                break
    if not regular:
        sys.exit("error: el texto usa caracteres fuera de cp1252 y no se encontró DejaVu Sans; pasa --font /ruta/fuente.ttf")
    pdfmetrics.registerFont(TTFont("Body", str(regular)))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(bold if bold and bold.is_file() else regular)))
    # Sin versión cursiva: se usa la normal (el contenido no cambia, solo el estilo)
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")
    COVER["Body"] = ttf_cover(pdfmetrics.getFont("Body"))
    return {"body": "Body", "mono": "Courier"}


# ---------------------------------------------------------------- cobertura de caracteres y fuentes de reserva
def cp1252_cover(ch: str) -> bool:
    try:
        ch.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False


def ttf_cover(font) -> Callable[[str], bool]:
    cmap = set(font.face.charToGlyph)
    return lambda ch: ord(ch) in cmap


COVER: Dict[str, Callable[[str], bool]] = {"Helvetica": cp1252_cover, "Courier": cp1252_cover}
FALLBACKS: List[Tuple[str, Callable[[str], bool]]] = []
MISSING: set = set()


def find_fallback(ch: str) -> Optional[str]:
    for name, cover in FALLBACKS:
        if cover(ch):
            return name
    try:
        res = subprocess.run(["fc-list", ":charset=%x" % ord(ch), "file"], capture_output=True, text=True, timeout=30)
        paths = sorted({l.split(":")[0].strip() for l in res.stdout.splitlines() if l.strip()})
    except (OSError, subprocess.SubprocessError):
        paths = []
    # reportlab solo lee TrueType (.ttf); las .otf/.ttc CFF fallan al cargar y se descartan
    for path in sorted(paths, key=lambda x: (not x.lower().endswith(".ttf"), "noto" not in x.lower(), x)):
        if not path.lower().endswith(".ttf"):
            continue
        name = "Fallback%d" % (len(FALLBACKS) + 1)
        try:
            font = TTFont(name, path)
        except Exception:
            continue
        cover = ttf_cover(font)
        if not cover(ch):
            continue
        pdfmetrics.registerFont(font)
        pdfmetrics.registerFontFamily(name, normal=name, bold=name, italic=name, boldItalic=name)
        FALLBACKS.append((name, cover))
        return name
    return None


def markup(text: str, font: str) -> str:
    """Escapa el texto para reportlab y envuelve en <font> de reserva los caracteres que `font` no tiene."""
    cover = COVER.get(font, cp1252_cover)
    out, seg, seg_font = [], [], None
    for ch in text:
        f = None
        if not (ch.isspace() or cover(ch)):
            f = "Body" if font != "Body" and "Body" in COVER and COVER["Body"](ch) else find_fallback(ch)
            if f is None:
                MISSING.add(ch)
        if f != seg_font and seg:
            chunk = escape("".join(seg))
            out.append('<font face="%s">%s</font>' % (seg_font, chunk) if seg_font else chunk)
            seg = []
        seg_font = f
        seg.append(ch)
    if seg:
        chunk = escape("".join(seg))
        out.append('<font face="%s">%s</font>' % (seg_font, chunk) if seg_font else chunk)
    return "".join(out)


def make_styles(fonts: dict) -> dict:
    body = ParagraphStyle("body", fontName=fonts["body"], fontSize=10.5, leading=15, textColor=INK, alignment=TA_LEFT, spaceAfter=6)
    bold_font = "Helvetica-Bold" if fonts["body"] == "Helvetica" else "Body-Bold"
    heads = {}
    for level, (size, before, after) in {1: (20, 0, 10), 2: (15, 14, 6), 3: (12.5, 10, 4), 4: (11, 8, 3)}.items():
        heads[level] = ParagraphStyle("h%d" % level, parent=body, fontName=bold_font, fontSize=size, leading=size * 1.25,
                                      textColor=ACCENT, spaceBefore=before, spaceAfter=after, keepWithNext=1)
    return {
        "body": body, "heads": heads,
        "code": ParagraphStyle("code", parent=body, fontName=fonts["mono"], fontSize=9, leading=12, backColor=colors.HexColor("#f2f4f7"),
                               borderPadding=6, spaceBefore=4, spaceAfter=10),
        "cell": ParagraphStyle("cell", parent=body, fontSize=9.5, leading=12.5, spaceAfter=0),
        "cell_head": ParagraphStyle("cell_head", parent=body, fontName=bold_font, fontSize=9.5, leading=12.5, spaceAfter=0),
        "quote": ParagraphStyle("quote", parent=body, textColor=colors.HexColor("#3e4c59"), spaceAfter=4),
    }


def inline_markup(token, mono: str, body: str) -> str:
    out: List[str] = []
    for c in token.children or []:
        t = c.type
        if t == "text":
            out.append(markup(c.content, body))
        elif t == "code_inline":
            out.append('<font face="%s">%s</font>' % (mono, markup(c.content, mono)))
        elif t == "html_inline" and c.content.lower().startswith("<br"):
            out.append("<br/>")
        elif t == "softbreak":
            out.append(" ")
        elif t == "hardbreak":
            out.append("<br/>")
        elif t == "strong_open":
            out.append("<b>")
        elif t == "strong_close":
            out.append("</b>")
        elif t == "em_open":
            out.append("<i>")
        elif t == "em_close":
            out.append("</i>")
        elif t == "link_open":
            out.append('<a href="%s" color="#1d4ed8">' % escape(c.attrGet("href") or "", {'"': "&quot;"}))
        elif t == "link_close":
            out.append("</a>")
        elif t == "image":
            out.append(markup(c.content, body))
    return "".join(out)


class Renderer:
    def __init__(self, styles: dict, mono: str, body: str, width: float):
        self.s, self.mono, self.body, self.width = styles, mono, body, width

    def blocks(self, tokens, i: int, until: Optional[str], style=None) -> tuple:
        flow: list = []
        style = style or self.s["body"]
        while i < len(tokens):
            t = tokens[i]
            if until and t.type == until:
                return flow, i + 1
            if t.type == "heading_open":
                level = min(int(t.tag[1]), 4)
                flow.append(CondPageBreak(3.5 * cm))  # keepWithNext no basta con listas: evita títulos huérfanos al pie
                flow.append(Paragraph(inline_markup(tokens[i + 1], self.mono, self.body), self.s["heads"][level]))
                i += 3
            elif t.type == "paragraph_open":
                flow.append(Paragraph(inline_markup(tokens[i + 1], self.mono, self.body), style))
                i += 3
            elif t.type in ("bullet_list_open", "ordered_list_open"):
                ordered = t.type == "ordered_list_open"
                start = int(t.attrGet("start") or 1)
                close = t.type.replace("open", "close")
                items, i = self.list_items(tokens, i + 1, close)
                kw = {"bulletType": "1", "start": start, "bulletFormat": "%s."} if ordered else {"bulletType": "bullet", "start": "•"}
                flow.append(ListFlowable(items, bulletFontName=style.fontName, bulletFontSize=style.fontSize,
                                         leftIndent=18, bulletColor=ACCENT, **kw))
                flow.append(Spacer(1, 4))
            elif t.type == "blockquote_open":
                inner, i = self.blocks(tokens, i + 1, "blockquote_close", self.s["quote"])
                q = Table([[inner]], colWidths=[self.width - 10])
                q.setStyle(TableStyle([("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                       ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                flow.extend([q, Spacer(1, 6)])
            elif t.type in ("fence", "code_block"):
                flow.append(XPreformatted(markup(t.content.rstrip("\n"), self.mono), self.s["code"]))
                i += 1
            elif t.type == "hr":
                flow.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#cbd2d9"), spaceBefore=6, spaceAfter=10))
                i += 1
            elif t.type == "table_open":
                tbl, i = self.table(tokens, i + 1)
                flow.extend([tbl, Spacer(1, 8)])
            else:
                i += 1
        return flow, i

    def list_items(self, tokens, i: int, close: str) -> tuple:
        items = []
        while tokens[i].type != close:
            inner, i = self.blocks(tokens, i + 1, "list_item_close")
            items.append(ListItem(inner))
        return items, i + 1

    def table(self, tokens, i: int) -> tuple:
        rows, row, head_rows = [], [], 0
        while tokens[i].type != "table_close":
            t = tokens[i]
            if t.type in ("th_open", "td_open"):
                st = self.s["cell_head"] if t.type == "th_open" else self.s["cell"]
                row.append(Paragraph(inline_markup(tokens[i + 1], self.mono, self.body), st))
                i += 2
            elif t.type == "tr_close":
                rows.append(row)
                row = []
            elif t.type == "thead_close":
                head_rows = len(rows)
            i += 1
        cols = max(len(r) for r in rows)
        for r in rows:
            r.extend([Paragraph("", self.s["cell"])] * (cols - len(r)))
        tbl = Table(rows, colWidths=[self.width / cols] * cols, repeatRows=head_rows)
        style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd2d9")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
        if head_rows:
            style.append(("BACKGROUND", (0, 0), (-1, head_rows - 1), colors.HexColor("#e4e7eb")))
        tbl.setStyle(TableStyle(style))
        return tbl, i + 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("--output", type=Path, help="por defecto, el mismo nombre con extensión .pdf")
    ap.add_argument("--font", type=Path, help="fuente .ttf (solo si el texto usa caracteres fuera de cp1252)")
    ap.add_argument("--landscape", action="store_true", help="A4 apaisado (tablas con muchas columnas)")
    args = ap.parse_args()
    if not args.markdown.is_file():
        sys.exit("error: no existe {}".format(args.markdown))
    out = args.output or args.markdown.with_suffix(".pdf")
    md_text = args.markdown.read_text(encoding="utf-8")

    tokens = parser().parse(md_text)
    title = next((inline_text(tokens[i + 1]) for i, t in enumerate(tokens) if t.type == "heading_open" and t.tag == "h1"), args.markdown.stem)
    fonts = setup_fonts(md_text, args.font)
    styles = make_styles(fonts)

    page = landscape(A4) if args.landscape else A4
    doc = SimpleDocTemplate(str(out), pagesize=page, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2.2 * cm,
                            title=title, author="")
    renderer = Renderer(styles, fonts["mono"], fonts["body"], doc.width)
    flow, _ = renderer.blocks(tokens, 0, None)
    if MISSING:
        sys.exit("error: ninguna fuente instalada tiene estos caracteres y se perderían en el PDF: {} "
                 "(instala una fuente que los tenga, p. ej. fonts-noto / fonts-droid-fallback, o pasa --font)".format(
                     " ".join(sorted(MISSING))))
    if not flow:
        sys.exit("error: el Markdown no produjo contenido")

    def footer(canvas, d):  # línea 'pág. N': check_summary la ignora al comparar con el .md
        canvas.saveState()
        canvas.setFont(fonts["body"], 8.5)
        canvas.setFillColor(colors.HexColor("#7b8794"))
        canvas.drawCentredString(page[0] / 2, 1.2 * cm, "pág. %d" % d.page)
        canvas.restoreState()

    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print("PDF creado: {} ({} KB)".format(out, out.stat().st_size // 1024))


if __name__ == "__main__":
    main()
