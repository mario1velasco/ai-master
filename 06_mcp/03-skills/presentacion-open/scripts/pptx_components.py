#!/usr/bin/env python3
"""Editable PowerPoint object builders using public python-pptx APIs."""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from pptx.chart.data import BubbleChartData, CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

EMU_PER_INCH = 914400.0
MAX_CONTAINER_CHARS = 180
DEFAULT_SLIDE_WIDTH_IN = 13.333333
DEFAULT_SLIDE_HEIGHT_IN = 7.5
DEFAULT_MARGIN_IN = 0.6
TEXT_FRAME_MARGIN_IN = 0.08
COLUMN_GAP_IN = 0.34
ITEM_GAP_IN = 0.13

DEFAULT_THEME: Dict[str, Any] = {
    "font_name": "Roboto",
    "title_color": "17324D",
    "body_color": "243B53",
    "accent_color": "C8102E",
    "background_color": "FFFFFF",
    "muted_color": "63788A",
    "title_pt": 32,
    "body_pt": 20,
    "cover_title_pt": 42,
    "safe_margin_inches": DEFAULT_MARGIN_IN,
    "chart_colors": ["C8102E", "17324D", "F2A900", "2F8F6B", "6B5B95"],
}

SHAPE_TYPES = {
    "rectangle": MSO_SHAPE.RECTANGLE,
    "rounded_rectangle": MSO_SHAPE.ROUNDED_RECTANGLE,
    "ellipse": MSO_SHAPE.OVAL,
    "diamond": MSO_SHAPE.DIAMOND,
    "chevron": MSO_SHAPE.CHEVRON,
    "right_arrow": MSO_SHAPE.RIGHT_ARROW,
    "left_arrow": MSO_SHAPE.LEFT_ARROW,
    "up_arrow": MSO_SHAPE.UP_ARROW,
    "down_arrow": MSO_SHAPE.DOWN_ARROW,
    "flow_process": MSO_SHAPE.FLOWCHART_PROCESS,
    "flow_decision": MSO_SHAPE.FLOWCHART_DECISION,
    "flow_document": MSO_SHAPE.FLOWCHART_DOCUMENT,
    "flow_start_end": MSO_SHAPE.FLOWCHART_TERMINATOR,
    "hexagon": MSO_SHAPE.HEXAGON,
}

CHART_TYPES = {
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "bar_stacked": XL_CHART_TYPE.BAR_STACKED,
    "bar_stacked_100": XL_CHART_TYPE.BAR_STACKED_100,
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "column_stacked": XL_CHART_TYPE.COLUMN_STACKED,
    "column_stacked_100": XL_CHART_TYPE.COLUMN_STACKED_100,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "line_plain": XL_CHART_TYPE.LINE,
    "area": XL_CHART_TYPE.AREA,
    "area_stacked": XL_CHART_TYPE.AREA_STACKED,
    "area_stacked_100": XL_CHART_TYPE.AREA_STACKED_100,
    "line_stacked": XL_CHART_TYPE.LINE_STACKED,
    "line_stacked_100": XL_CHART_TYPE.LINE_STACKED_100,
    "line_markers_stacked": XL_CHART_TYPE.LINE_MARKERS_STACKED,
    "line_markers_stacked_100": XL_CHART_TYPE.LINE_MARKERS_STACKED_100,
    "pie": XL_CHART_TYPE.PIE,
    "pie_exploded": XL_CHART_TYPE.PIE_EXPLODED,
    "doughnut": XL_CHART_TYPE.DOUGHNUT,
    "doughnut_exploded": XL_CHART_TYPE.DOUGHNUT_EXPLODED,
    "radar": XL_CHART_TYPE.RADAR,
    "radar_filled": XL_CHART_TYPE.RADAR_FILLED,
    "radar_markers": XL_CHART_TYPE.RADAR_MARKERS,
    "scatter": XL_CHART_TYPE.XY_SCATTER,
    "scatter_lines": XL_CHART_TYPE.XY_SCATTER_LINES,
    "scatter_lines_no_markers": XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS,
    "scatter_smooth": XL_CHART_TYPE.XY_SCATTER_SMOOTH,
    "scatter_smooth_no_markers": XL_CHART_TYPE.XY_SCATTER_SMOOTH_NO_MARKERS,
    "bubble": XL_CHART_TYPE.BUBBLE,
    "bubble_3d": XL_CHART_TYPE.BUBBLE_THREE_D_EFFECT,
}

ALIGNMENTS = {
    "left": PP_ALIGN.LEFT,
    "center": PP_ALIGN.CENTER,
    "right": PP_ALIGN.RIGHT,
    "justify": PP_ALIGN.JUSTIFY,
    "distributed": PP_ALIGN.DISTRIBUTE,
}
ANCHORS = {
    "top": MSO_ANCHOR.TOP,
    "middle": MSO_ANCHOR.MIDDLE,
    "bottom": MSO_ANCHOR.BOTTOM,
}


def fail(message: str) -> None:
    raise ValueError(message)
def finite_number(value: Any, location: str, minimum: Optional[float] = None) -> float:
    if isinstance(value, bool):
        fail("{} must be a number".format(location))
    try:
        number = float(value)
    except (TypeError, ValueError):
        fail("{} must be a number".format(location))
    if not math.isfinite(number):
        fail("{} must be finite".format(location))
    if minimum is not None and number < minimum:
        fail("{} must be at least {}".format(location, minimum))
    return number
def parse_color(value: Any, location: str) -> RGBColor:
    if not isinstance(value, str):
        fail("{} must be a six-digit RGB hex string".format(location))
    color = value.strip().lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", color):
        fail("{} must be a six-digit RGB hex string".format(location))
    return RGBColor(int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))
def plain_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(plain_text(part) for part in value)
    if isinstance(value, dict):
        if "paragraphs" in value:
            return "\n".join(plain_text(p) for p in value["paragraphs"])
        if "runs" in value:
            return "".join(plain_text(run) for run in value["runs"])
        if "text" in value:
            return plain_text(value["text"])
        return ""
    return str(value)
def enforce_container(value: Any, location: str, maximum: int = MAX_CONTAINER_CHARS) -> str:
    text = plain_text(value).strip()
    if not text:
        fail("{} cannot be empty".format(location))
    if len(text) > maximum:
        fail("{} has {} characters (maximum {})".format(location, len(text), maximum))
    return text
def split_long_text(text: str, location: str, limit: int = MAX_CONTAINER_CHARS - 2) -> List[str]:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return [normalized]
    sentences = re.split(r"(?<=[.!?])\s+", normalized)
    result: List[str] = []
    current = ""
    for sentence in sentences:
        words = sentence.split()
        segment = ""
        for word in words:
            if len(word) > limit:
                fail("{} contains an unbroken token longer than {} characters".format(location, limit))
            candidate = word if not segment else segment + " " + word
            if len(candidate) > limit:
                if current:
                    result.append(current)
                    current = ""
                if segment:
                    if current:
                        result.append(current)
                    current = segment
                segment = word
            else:
                segment = candidate
        if segment:
            candidate = segment if not current else current + " " + segment
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    result.append(current)
                current = segment
    if current:
        result.append(current)
    if not result:
        fail("Could not split {} into valid containers".format(location))
    return result
def line_count(text: str, width_in: float, font_pt: float, bullet: bool = False) -> int:
    inside_width = max(0.1, width_in - 2 * TEXT_FRAME_MARGIN_IN - (0.22 if bullet else 0.0))
    chars_per_line = max(6, int(inside_width * 72.0 / (font_pt * 0.52)))
    count = 0
    for line in text.splitlines() or [text]:
        count += max(1, math.ceil(len(line) / float(chars_per_line)))
    return count
def estimated_text_height(text: Any, width_in: float, font_pt: float, bullet: bool = False) -> float:
    return line_count(plain_text(text), width_in, font_pt, bullet) * font_pt * 1.24 / 72.0 + 0.12
def partition_by_height(items: Sequence[Any], count: int, width_in: float, font_pt: float, bullet: bool) -> List[List[Any]]:
    heights = [estimated_text_height(item, width_in, font_pt, bullet) + ITEM_GAP_IN for item in items]
    if not heights:
        return [[] for _ in range(count)]
    low, high = max(heights), sum(heights)
    while low < high - 1e-6:
        middle = (low + high) / 2.0
        groups_needed, current = 1, 0.0
        for height in heights:
            if current and current + height > middle:
                groups_needed += 1
                current = 0.0
            current += height
        if groups_needed <= count:
            high = middle
        else:
            low = middle + 1e-6
    groups: List[List[Any]] = []
    current_items: List[Any] = []
    current_height = 0.0
    for index, (item, item_height) in enumerate(zip(items, heights)):
        groups_left = count - len(groups)
        items_left = len(items) - index
        if current_items and current_height + item_height > high and items_left >= groups_left:
            groups.append(current_items)
            current_items, current_height = [], 0.0
        current_items.append(item)
        current_height += item_height
    if current_items:
        groups.append(current_items)
    while len(groups) < count:
        groups.append([])
    return groups
def _run_specs(paragraph_spec: Any) -> List[Mapping[str, Any]]:
    if isinstance(paragraph_spec, str):
        return [{"text": paragraph_spec}]
    if not isinstance(paragraph_spec, dict):
        fail("Each paragraph must be a string or object")
    runs = paragraph_spec.get("runs")
    if runs is None:
        return [{"text": paragraph_spec.get("text", "")}]
    if not isinstance(runs, list):
        fail("paragraph.runs must be a list")
    normalized: List[Mapping[str, Any]] = []
    for index, run in enumerate(runs):
        if isinstance(run, str):
            normalized.append({"text": run})
        elif isinstance(run, dict):
            normalized.append(run)
        else:
            fail("paragraph.runs[{}] must be a string or object".format(index))
    return normalized
def _paragraph_specs(content: Any) -> List[Any]:
    if isinstance(content, str):
        return [{"text": part} for part in content.split("\n")]
    if isinstance(content, dict):
        paragraphs = content.get("paragraphs")
        if paragraphs is not None:
            if not isinstance(paragraphs, list):
                fail("text.paragraphs must be a list")
            return paragraphs
        return [content]
    if isinstance(content, list):
        return content
    fail("Text content must be a string, list, or object")
    return []
def _apply_run_format(run: Any, spec: Mapping[str, Any], theme: Mapping[str, Any], use_theme: bool) -> None:
    font = run.font
    font_name = spec.get("font_name", theme.get("font_name") if use_theme else None)
    font_size = spec.get("font_size_pt", theme.get("body_pt") if use_theme else None)
    color_value = spec.get("color", theme.get("body_color") if use_theme else None)
    if font_name:
        font.name = str(font_name)
    if font_size is not None:
        font.size = Pt(finite_number(font_size, "font_size_pt", 1))
    if color_value:
        font.color.rgb = parse_color(color_value, "text color")
    for key in ("bold", "italic", "underline"):
        if key in spec:
            setattr(font, key, bool(spec[key]))
    hyperlink = spec.get("hyperlink")
    if hyperlink:
        if not isinstance(hyperlink, str):
            fail("run.hyperlink must be a URL string")
        run.hyperlink.address = hyperlink
def apply_text_frame(
    frame: Any,
    content: Any,
    theme: Mapping[str, Any],
    style: Optional[Mapping[str, Any]] = None,
    bullet: bool = False,
    use_theme: bool = True,
) -> None:
    style = style or {}
    rendered = plain_text(content)
    if len(rendered.strip()) > MAX_CONTAINER_CHARS:
        fail("Text container has {} characters (maximum {})".format(len(rendered.strip()), MAX_CONTAINER_CHARS))
    frame.clear()
    frame.word_wrap = bool(style.get("word_wrap", True))
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = ANCHORS.get(str(style.get("vertical_anchor", "top")).lower(), MSO_ANCHOR.TOP)
    margins = style.get("margins_in", {})
    if not isinstance(margins, dict):
        fail("margins_in must be an object")
    frame.margin_left = Inches(finite_number(margins.get("left", TEXT_FRAME_MARGIN_IN), "margins_in.left", 0))
    frame.margin_right = Inches(finite_number(margins.get("right", TEXT_FRAME_MARGIN_IN), "margins_in.right", 0))
    frame.margin_top = Inches(finite_number(margins.get("top", 0.04), "margins_in.top", 0))
    frame.margin_bottom = Inches(finite_number(margins.get("bottom", 0.04), "margins_in.bottom", 0))

    paragraphs = _paragraph_specs(content)
    for paragraph_index, paragraph_spec in enumerate(paragraphs):
        paragraph = frame.paragraphs[0] if paragraph_index == 0 else frame.add_paragraph()
        if isinstance(paragraph_spec, dict):
            alignment = paragraph_spec.get("alignment", style.get("alignment"))
            if alignment:
                if str(alignment).lower() not in ALIGNMENTS:
                    fail("Unsupported paragraph alignment: {}".format(alignment))
                paragraph.alignment = ALIGNMENTS[str(alignment).lower()]
            if "level" in paragraph_spec:
                paragraph.level = int(paragraph_spec["level"])
            paragraph.space_before = Pt(finite_number(paragraph_spec.get("space_before_pt", 0), "space_before_pt", 0))
            paragraph.space_after = Pt(finite_number(paragraph_spec.get("space_after_pt", 0), "space_after_pt", 0))
            if "line_spacing" in paragraph_spec:
                paragraph.line_spacing = finite_number(paragraph_spec["line_spacing"], "line_spacing", 0.1)
            paragraph_bullet = bool(paragraph_spec.get("bullet", bullet))
        else:
            paragraph_bullet = bullet
            alignment = style.get("alignment")
            if alignment:
                if str(alignment).lower() not in ALIGNMENTS:
                    fail("Unsupported paragraph alignment: {}".format(alignment))
                paragraph.alignment = ALIGNMENTS[str(alignment).lower()]
            paragraph.space_before = Pt(0)
            paragraph.space_after = Pt(0)

        runs = _run_specs(paragraph_spec)
        nonempty = any(str(run.get("text", "")) for run in runs)
        if paragraph_bullet and nonempty:
            bullet_run = paragraph.add_run()
            bullet_run.text = "• "
            _apply_run_format(bullet_run, {"font_size_pt": style.get("font_size_pt", theme.get("body_pt", 20))}, theme, use_theme)
        for run_spec in runs:
            run = paragraph.add_run()
            run.text = str(run_spec.get("text", ""))
            combined = dict(style)
            combined.update(run_spec)
            _apply_run_format(run, combined, theme, use_theme)
def add_textbox(
    slide: Any,
    content: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    theme: Mapping[str, Any],
    style: Optional[Mapping[str, Any]] = None,
    name: Optional[str] = None,
    bullet: bool = False,
    use_theme: bool = True,
) -> Any:
    for location, value in (("x", x), ("y", y), ("width", width), ("height", height)):
        finite_number(value, location)
    if width <= 0 or height <= 0:
        fail("Text box width and height must be positive")
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(width), Inches(height))
    if name:
        shape.name = str(name)
    apply_text_frame(shape.text_frame, content, theme, style, bullet, use_theme)
    return shape
def _resolve_image_path(value: Any, deck_dir: Path) -> Path:
    raw = value.get("path") if isinstance(value, dict) else value
    if not isinstance(raw, (str, Path)) or not str(raw).strip():
        fail("Image requires a non-empty path")
    path = Path(raw)
    if not path.is_absolute():
        path = (deck_dir / path).resolve()
    if not path.is_file():
        fail("Image file not found: {}".format(path))
    return path
def add_image(slide: Any, element: Mapping[str, Any], deck_dir: Path, name: Optional[str] = None) -> Any:
    x = finite_number(element.get("x"), "image.x")
    y = finite_number(element.get("y"), "image.y")
    width = finite_number(element.get("width"), "image.width", 0.01)
    height = finite_number(element.get("height"), "image.height", 0.01)
    image = slide.shapes.add_picture(str(_resolve_image_path(element.get("path", element), deck_dir)), Inches(x), Inches(y))
    original_width = float(image.width)
    original_height = float(image.height)
    mode = str(element.get("fit", "contain")).lower()
    if mode == "contain":
        scale = min(width * EMU_PER_INCH / original_width, height * EMU_PER_INCH / original_height)
        image.width = int(original_width * scale)
        image.height = int(original_height * scale)
        image.left = Inches(x + (width - image.width / EMU_PER_INCH) / 2)
        image.top = Inches(y + (height - image.height / EMU_PER_INCH) / 2)
    elif mode == "cover":
        source_ratio = original_width / original_height
        frame_ratio = width / height
        if source_ratio > frame_ratio:
            visible = frame_ratio / source_ratio
            crop = (1.0 - visible) / 2.0
            image.crop_left = crop
            image.crop_right = crop
        elif source_ratio < frame_ratio:
            visible = source_ratio / frame_ratio
            crop = (1.0 - visible) / 2.0
            image.crop_top = crop
            image.crop_bottom = crop
        image.left, image.top = Inches(x), Inches(y)
        image.width, image.height = Inches(width), Inches(height)
    elif mode == "stretch":
        image.left, image.top = Inches(x), Inches(y)
        image.width, image.height = Inches(width), Inches(height)
    else:
        fail("image.fit must be contain, cover, or stretch")
    if name:
        image.name = str(name)
    return image
def _cell_text(cell: Any, content: Any, theme: Mapping[str, Any], style: Mapping[str, Any], use_theme: bool = True) -> None:
    apply_text_frame(cell.text_frame, content, theme, style, use_theme=use_theme)
def add_table(slide: Any, element: Mapping[str, Any], theme: Mapping[str, Any], name: Optional[str] = None) -> Any:
    x = finite_number(element.get("x"), "table.x")
    y = finite_number(element.get("y"), "table.y")
    width = finite_number(element.get("width"), "table.width", 0.1)
    height = finite_number(element.get("height"), "table.height", 0.1)
    headers = element.get("headers")
    rows = element.get("rows")
    if not isinstance(rows, list):
        fail("table.rows must be a list")
    if headers is not None and (not isinstance(headers, list) or not headers):
        fail("table.headers must be a non-empty list when supplied")
    col_count = len(headers) if headers is not None else (len(rows[0]) if rows else 0)
    if col_count < 1:
        fail("A table must have at least one column")
    if len(rows) > 100 or col_count > 30:
        fail("Table exceeds the supported 100-row/30-column authoring guard")
    table_rows: List[List[Any]] = []
    if headers is not None:
        table_rows.append(headers)
    table_rows.extend(rows)
    if not table_rows:
        fail("A table must contain headers or data rows")
    normalized_rows: List[List[str]] = []
    for row_index, row in enumerate(table_rows):
        if not isinstance(row, list) or len(row) != col_count:
            fail("table row {} must contain {} cells".format(row_index, col_count))
        normalized_rows.append([enforce_container(cell, "table cell {},{}".format(row_index, col_index)) for col_index, cell in enumerate(row)])
    table_rows = normalized_rows

    table_shape = slide.shapes.add_table(len(table_rows), col_count, Inches(x), Inches(y), Inches(width), Inches(height))
    if name:
        table_shape.name = str(name)
    table = table_shape.table
    widths_in = element.get("column_widths_in")
    weights = element.get("column_weights")
    if widths_in is not None:
        if not isinstance(widths_in, list) or len(widths_in) != col_count:
            fail("table.column_widths_in must match the number of columns")
        parsed_widths = [finite_number(v, "column width", 0.01) for v in widths_in]
        if abs(sum(parsed_widths) - width) > 0.02:
            fail("table.column_widths_in must sum to table.width within 0.02 inches")
    else:
        if weights is None:
            weights = [1.0] * col_count
        if not isinstance(weights, list) or len(weights) != col_count:
            fail("table.column_weights must match the number of columns")
        parsed_weights = [finite_number(v, "column weight", 0.01) for v in weights]
        total = sum(parsed_weights)
        parsed_widths = [width * value / total for value in parsed_weights]
    for index, column_width in enumerate(parsed_widths):
        table.columns[index].width = Inches(column_width)

    row_heights = element.get("row_heights_in")
    if row_heights is not None:
        if not isinstance(row_heights, list) or len(row_heights) != len(table_rows):
            fail("table.row_heights_in must match the number of rows")
        parsed_heights = [finite_number(v, "row height", 0.01) for v in row_heights]
        if abs(sum(parsed_heights) - height) > 0.02:
            fail("table.row_heights_in must sum to table.height within 0.02 inches")
    else:
        parsed_heights = [height / len(table_rows)] * len(table_rows)
    for index, row_height in enumerate(parsed_heights):
        table.rows[index].height = Inches(row_height)

    header_rows = int(element.get("header_rows", 1 if headers is not None else 0))
    if header_rows < 0 or header_rows > len(table_rows):
        fail("table.header_rows is outside the table")
    font_pt = finite_number(element.get("font_size_pt", theme.get("body_pt", 20)), "table.font_size_pt", 1)
    header_fill = parse_color(element.get("header_fill", theme.get("accent_color", "C8102E")), "table.header_fill")
    header_color_value = str(element.get("header_color", "FFFFFF"))
    body_color_value = str(element.get("body_color", theme.get("body_color", "243B53")))
    parse_color(header_color_value, "table.header_color")
    parse_color(body_color_value, "table.body_color")
    stripe_color_value = element.get("stripe_fill")
    stripe_color = parse_color(stripe_color_value, "table.stripe_fill") if stripe_color_value else None
    margins = element.get("cell_margins_in", {"left": 0.08, "right": 0.08, "top": 0.04, "bottom": 0.04})
    if not isinstance(margins, dict):
        fail("table.cell_margins_in must be an object")
    for row_index, row in enumerate(table_rows):
        for col_index, value in enumerate(row):
            cell = table.cell(row_index, col_index)
            cell.margin_left = Inches(finite_number(margins.get("left", 0.08), "cell margin", 0))
            cell.margin_right = Inches(finite_number(margins.get("right", 0.08), "cell margin", 0))
            cell.margin_top = Inches(finite_number(margins.get("top", 0.04), "cell margin", 0))
            cell.margin_bottom = Inches(finite_number(margins.get("bottom", 0.04), "cell margin", 0))
            cell.vertical_anchor = ANCHORS.get(str(element.get("vertical_anchor", "middle")).lower(), MSO_ANCHOR.MIDDLE)
            is_header = row_index < header_rows
            if is_header:
                cell.fill.solid()
                cell.fill.fore_color.rgb = header_fill
                cell_color = header_color_value
            else:
                if stripe_color is not None and (row_index - header_rows) % 2 == 1:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = stripe_color
                cell_color = body_color_value
            style = {
                "font_name": element.get("font_name", theme.get("font_name")),
                "font_size_pt": element.get("font_size_pt", theme.get("body_pt", 20)),
                "color": cell_color,
                "bold": bool(is_header),
                "alignment": element.get("alignment", "left"),
                "margins_in": margins,
            }
            _cell_text(cell, value, theme, style)
    merges = element.get("merges", [])
    if not isinstance(merges, list):
        fail("table.merges must be a list")
    for merge in merges:
        if not isinstance(merge, list) or len(merge) != 4:
            fail("each table merge must be [row1, col1, row2, col2] using zero-based indices")
        r1, c1, r2, c2 = [int(v) for v in merge]
        if min(r1, c1, r2, c2) < 0 or r2 >= len(table_rows) or c2 >= col_count or r2 < r1 or c2 < c1:
            fail("table merge range is outside the table")
        table.cell(r1, c1).merge(table.cell(r2, c2))
    return table_shape
def _set_chart_text_font(frame: Any, theme: Mapping[str, Any], size_pt: float, color: str) -> None:
    for paragraph in frame.paragraphs:
        for run in paragraph.runs:
            run.font.name = str(theme.get("font_name", "Roboto"))
            run.font.size = Pt(size_pt)
            run.font.color.rgb = parse_color(color, "chart text color")
def add_chart(slide: Any, element: Mapping[str, Any], theme: Mapping[str, Any], name: Optional[str] = None) -> Any:
    chart_type_name = str(element.get("chart_type", element.get("type", "column"))).lower()
    if chart_type_name not in CHART_TYPES:
        fail("Unsupported chart type '{}'; choose from {}".format(chart_type_name, ", ".join(sorted(CHART_TYPES))))
    chart_type = CHART_TYPES[chart_type_name]
    x = finite_number(element.get("x"), "chart.x")
    y = finite_number(element.get("y"), "chart.y")
    width = finite_number(element.get("width"), "chart.width", 0.1)
    height = finite_number(element.get("height"), "chart.height", 0.1)

    if chart_type_name.startswith("scatter"):
        raw_series = element.get("series")
        if not isinstance(raw_series, list) or not raw_series:
            fail("scatter chart requires series")
        chart_data = XyChartData()
        for index, series in enumerate(raw_series):
            if not isinstance(series, dict):
                fail("chart.series[{}] must be an object".format(index))
            name_value = enforce_container(series.get("name"), "chart series name")
            xs = series.get("x_values")
            ys = series.get("values")
            if not isinstance(xs, list) or not isinstance(ys, list) or len(xs) != len(ys) or not xs:
                fail("scatter series must have equal non-empty x_values and values lists")
            xy = chart_data.add_series(name_value)
            for x_value, y_value in zip(xs, ys):
                xy.add_data_point(finite_number(x_value, "scatter x"), finite_number(y_value, "scatter y"))
    elif chart_type_name in ("bubble", "bubble_3d"):
        raw_series = element.get("series")
        if not isinstance(raw_series, list) or not raw_series:
            fail("bubble chart requires series")
        chart_data = BubbleChartData()
        for index, series in enumerate(raw_series):
            if not isinstance(series, dict):
                fail("chart.series[{}] must be an object".format(index))
            name_value = enforce_container(series.get("name"), "chart series name")
            xs, ys, sizes = series.get("x_values"), series.get("values"), series.get("bubble_sizes")
            if not all(isinstance(values, list) for values in (xs, ys, sizes)) or not xs or len(xs) != len(ys) or len(xs) != len(sizes):
                fail("bubble series requires equal non-empty x_values, values, and bubble_sizes lists")
            bubble_series = chart_data.add_series(name_value)
            for x_value, y_value, size in zip(xs, ys, sizes):
                size_value = finite_number(size, "bubble size", 0.000001)
                bubble_series.add_data_point(finite_number(x_value, "bubble x"), finite_number(y_value, "bubble y"), size_value)
    else:
        categories = element.get("categories")
        raw_series = element.get("series")
        if not isinstance(categories, list) or not categories:
            fail("category chart requires a non-empty categories list")
        if not isinstance(raw_series, list) or not raw_series:
            fail("chart requires a non-empty series list")
        categories = [enforce_container(item, "chart category") for item in categories]
        chart_data = CategoryChartData()
        chart_data.categories = categories
        for index, series in enumerate(raw_series):
            if not isinstance(series, dict):
                fail("chart.series[{}] must be an object".format(index))
            series_name = enforce_container(series.get("name"), "chart series name")
            values = series.get("values")
            if not isinstance(values, list) or len(values) != len(categories):
                fail("chart series '{}' must have one value per category".format(series_name))
            numeric_values = [finite_number(value, "chart value") for value in values]
            if chart_type_name in ("pie", "pie_exploded", "doughnut", "doughnut_exploded") and any(value < 0 for value in numeric_values):
                fail("pie and doughnut values must be non-negative")
            if chart_type_name in ("pie", "pie_exploded", "doughnut", "doughnut_exploded") and sum(numeric_values) <= 0:
                fail("pie and doughnut charts need at least one positive value")
            chart_data.add_series(series_name, numeric_values, number_format=series.get("number_format"))
        if chart_type_name in ("pie", "pie_exploded", "doughnut", "doughnut_exploded") and len(raw_series) != 1:
            fail("pie and doughnut charts accept exactly one series")

    chart_shape = slide.shapes.add_chart(chart_type, Inches(x), Inches(y), Inches(width), Inches(height), chart_data)
    if name:
        chart_shape.name = str(name)
    chart = chart_shape.chart
    chart.font.name = str(theme.get("font_name", "Roboto"))
    chart.font.size = Pt(finite_number(element.get("font_size_pt", 12), "chart.font_size_pt", 1))
    chart.font.color.rgb = parse_color(element.get("font_color", theme.get("body_color", "243B53")), "chart.font_color")
    if "style" in element:
        chart.chart_style = int(element["style"])
    title = element.get("title")
    if title:
        title = enforce_container(title, "chart.title")
        chart.has_title = True
        chart.chart_title.text_frame.text = title
        _set_chart_text_font(chart.chart_title.text_frame, theme, finite_number(element.get("title_pt", 14), "chart.title_pt", 1), theme.get("title_color", "17324D"))
    else:
        chart.has_title = False

    legend = element.get("legend", True)
    chart.has_legend = bool(legend)
    if chart.has_legend and isinstance(legend, dict):
        position = str(legend.get("position", "bottom")).upper()
        if position not in {"BOTTOM", "LEFT", "RIGHT", "TOP", "CORNER"}:
            fail("Unsupported chart legend position: {}".format(position))
        chart.legend.position = getattr(XL_LEGEND_POSITION, position)
        chart.legend.include_in_layout = bool(legend.get("include_in_layout", True))

    labels = element.get("data_labels", False)
    if labels and (chart_type_name.startswith("scatter") or chart_type_name in ("bubble", "bubble_3d")):
        fail("python-pptx does not expose editable data-label formatting for XY/bubble charts; omit data_labels or use a supported chart type")
    if labels:
        plot = chart.plots[0]
        plot.has_data_labels = True
        label_options = labels if isinstance(labels, dict) else {}
        data_labels = plot.data_labels
        for key in ("show_value", "show_category_name", "show_series_name", "show_percentage"):
            if key in label_options:
                setattr(data_labels, key, bool(label_options[key]))
        if "number_format" in label_options:
            data_labels.number_format = str(label_options["number_format"])
        if "position" in label_options:
            label_position = str(label_options["position"]).upper()
            if label_position not in {"CENTER", "INSIDE_END", "INSIDE_BASE", "OUTSIDE_END", "ABOVE", "BELOW", "LEFT", "RIGHT", "BEST_FIT"}:
                fail("Unsupported data label position: {}".format(label_position))
            data_labels.position = getattr(XL_LABEL_POSITION, label_position)
        if "font_size_pt" in label_options:
            data_labels.font.size = Pt(finite_number(label_options["font_size_pt"], "data_labels.font_size_pt", 1))
        if "font_name" in label_options:
            data_labels.font.name = str(label_options["font_name"])

    colors = element.get("colors", theme.get("chart_colors", []))
    if colors and chart_type_name in ("pie", "pie_exploded", "doughnut", "doughnut_exploded"):
        points = chart.series[0].points
        for index, point in enumerate(points):
            color = parse_color(colors[index % len(colors)], "chart color")
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = color
    elif colors:
        for index, series in enumerate(chart.series):
            color = parse_color(colors[index % len(colors)], "chart color")
            if chart_type_name.startswith(("line", "scatter")) or (chart_type_name.startswith("radar") and chart_type_name != "radar_filled"):
                series.format.line.color.rgb = color
            else:
                series.format.fill.solid()
                series.format.fill.fore_color.rgb = color

    axis_options = element.get("axes", {})
    if not isinstance(axis_options, dict):
        fail("chart.axes must be an object")
    xy_chart = chart_type_name.startswith("scatter") or chart_type_name in ("bubble", "bubble_3d")
    pie_chart = chart_type_name in ("pie", "pie_exploded", "doughnut", "doughnut_exploded")
    category_options = axis_options.get("x", {}) if xy_chart else axis_options.get("category", {})
    if not pie_chart:
        if isinstance(category_options, dict) and category_options:
            options = category_options
            axis = chart.category_axis
            if "visible" in options:
                axis.visible = bool(options["visible"])
            if "title" in options:
                axis.has_title = True
                axis.axis_title.text_frame.text = enforce_container(options["title"], "category axis title")
            if "major_gridlines" in options:
                axis.has_major_gridlines = bool(options["major_gridlines"])
            if "font_size_pt" in options:
                axis.tick_labels.font.size = Pt(finite_number(options["font_size_pt"], "category axis font_size_pt", 1))
    value_options = axis_options.get("y", {}) if xy_chart else axis_options.get("value", {})
    if not pie_chart and isinstance(value_options, dict) and value_options:
        options = value_options
        axis = chart.value_axis
        if "minimum" in options:
            axis.minimum_scale = finite_number(options["minimum"], "value axis minimum")
        if "maximum" in options:
            axis.maximum_scale = finite_number(options["maximum"], "value axis maximum")
        if "major_unit" in options:
            axis.major_unit = finite_number(options["major_unit"], "value axis major_unit", 0.000001)
        if "number_format" in options:
            axis.tick_labels.number_format = str(options["number_format"])
        if "major_gridlines" in options:
            axis.has_major_gridlines = bool(options["major_gridlines"])
        if "font_size_pt" in options:
            axis.tick_labels.font.size = Pt(finite_number(options["font_size_pt"], "value axis font_size_pt", 1))
    return chart_shape
def add_shape(slide: Any, element: Mapping[str, Any], theme: Mapping[str, Any], name: Optional[str] = None) -> Any:
    shape_name = str(element.get("shape_type", "rectangle")).lower()
    shape_enum = SHAPE_TYPES.get(shape_name)
    if shape_enum is None:
        enum_name = shape_name.upper()
        shape_enum = getattr(MSO_SHAPE, enum_name, None)
    if shape_enum is None:
        fail("Unsupported shape type '{}'; use an alias in the schema or an MSO_SHAPE enum name".format(shape_name))
    x = finite_number(element.get("x"), "shape.x")
    y = finite_number(element.get("y"), "shape.y")
    width = finite_number(element.get("width"), "shape.width", 0.01)
    height = finite_number(element.get("height"), "shape.height", 0.01)
    shape = slide.shapes.add_shape(shape_enum, Inches(x), Inches(y), Inches(width), Inches(height))
    if name:
        shape.name = str(name)
    fill = element.get("fill")
    if fill is None or str(fill).lower() == "none":
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = parse_color(fill, "shape.fill")
    line_color = element.get("line_color")
    if line_color is None or str(line_color).lower() == "none":
        shape.line.fill.background()
    else:
        shape.line.color.rgb = parse_color(line_color, "shape.line_color")
        shape.line.width = Pt(finite_number(element.get("line_width_pt", 1), "shape.line_width_pt", 0.1))
    if "text" in element:
        text_style = element.get("text_style", {})
        if not isinstance(text_style, dict):
            fail("shape.text_style must be an object")
        apply_text_frame(shape.text_frame, element["text"], theme, text_style, use_theme=True)
    return shape
def add_connector(slide: Any, element: Mapping[str, Any], name: Optional[str] = None) -> Any:
    start, end = element.get("start"), element.get("end")
    if not isinstance(start, dict) or not isinstance(end, dict):
        fail("connector requires start and end objects with x and y")
    x1 = finite_number(start.get("x"), "connector.start.x")
    y1 = finite_number(start.get("y"), "connector.start.y")
    x2 = finite_number(end.get("x"), "connector.end.x")
    y2 = finite_number(end.get("y"), "connector.end.y")
    connector_kind = str(element.get("connector_type", "straight")).lower()
    connector_map = {"straight": MSO_CONNECTOR.STRAIGHT, "elbow": MSO_CONNECTOR.ELBOW, "curve": MSO_CONNECTOR.CURVE}
    if connector_kind not in connector_map:
        fail("connector_type must be straight, elbow, or curve")
    shape = slide.shapes.add_connector(connector_map[connector_kind], Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    if name:
        shape.name = str(name)
    shape.line.color.rgb = parse_color(element.get("color", "63788A"), "connector.color")
    shape.line.width = Pt(finite_number(element.get("width_pt", 1.5), "connector.width_pt", 0.1))
    return shape
def add_element(slide: Any, element: Mapping[str, Any], deck_dir: Path, theme: Mapping[str, Any], index: int) -> Any:
    if not isinstance(element, dict):
        fail("elements[{}] must be an object".format(index))
    kind = str(element.get("type", "")).lower()
    name = element.get("name", "element-{}".format(index + 1))
    if kind == "textbox":
        return add_textbox(slide, element.get("text"), finite_number(element.get("x"), "textbox.x"), finite_number(element.get("y"), "textbox.y"), finite_number(element.get("width"), "textbox.width"), finite_number(element.get("height"), "textbox.height"), theme, element.get("style", {}), name, bool(element.get("bullet", False)))
    if kind == "image":
        image_spec = dict(element)
        image_spec["path"] = _resolve_image_path(element.get("path"), deck_dir)
        return add_image(slide, image_spec, deck_dir, str(name))
    if kind == "table":
        return add_table(slide, element, theme, str(name))
    if kind == "chart":
        return add_chart(slide, element, theme, str(name))
    if kind == "shape":
        return add_shape(slide, element, theme, str(name))
    if kind == "connector":
        return add_connector(slide, element, str(name))
    fail("Unsupported element type '{}'; use textbox, image, table, chart, shape, or connector".format(kind))
