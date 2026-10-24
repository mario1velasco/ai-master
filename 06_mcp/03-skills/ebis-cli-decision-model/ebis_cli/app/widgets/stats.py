"""Presentación por secciones de las estadísticas del workspace."""

from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static


def _section_color(title: str) -> str:
    heading = title.upper()
    if heading.startswith("JEV"):
        return "magenta"
    if heading.startswith("OPENAI") or heading.startswith("MODELO") or heading.startswith("NIVEL"):
        return "cyan"
    if heading.startswith("AHORRO"):
        return "green"
    if heading.startswith("DECISION") or heading.startswith("MODO"):
        return "yellow"
    if heading.startswith("NOTAS"):
        return "bright_black"
    return "bright_blue"


def make_stats_message(message: str) -> Static:
    """Convierte los bloques del informe en paneles independientes y legibles."""
    panels = []
    for section in message.strip().split("\n\n"):
        title, separator, body = section.partition("\n")
        color = _section_color(title)
        panels.append(
            Panel(
                Text(body if separator else title, style="white"),
                title=Text(title, style=f"bold {color}"),
                border_style=color,
                padding=(0, 1),
                expand=True,
            )
        )
    return Static(Group(*panels), markup=False, classes="chat-message stats-message")
