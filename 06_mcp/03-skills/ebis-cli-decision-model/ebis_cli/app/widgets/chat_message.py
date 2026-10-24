"""Tarjetas compactas y plegables para la transcripción del agente."""

from rich.panel import Panel
from rich.text import Text
from textual.widgets import Collapsible, Static

from .stats import make_stats_message


STYLES = {
    "Tú": ("OBJETIVO · TÚ", "cyan", "white"),
    "Respuesta": ("RESPUESTA FINAL", "green", "white"),
    "Tool": ("TOOL / RESULTADO", "yellow", "white"),
    "Tool en curso": ("TOOL EN CURSO", "yellow", "bright_yellow"),
    "Decision Model": ("JEV · CHOICE", "magenta", "bright_magenta"),
    "Routing": ("JEV · ROUTING", "blue", "bright_blue"),
    "Sistema": ("SISTEMA", "blue", "white"),
    "Paso": ("PROGRESO", "cyan", "white"),
    "Contexto": ("CONTEXTO", "bright_blue", "white"),
    "Subagente": ("SUBAGENTE", "magenta", "bright_magenta"),
    "Verificador": ("VERIFICADOR", "magenta", "white"),
    "Error": ("ERROR", "red", "bright_red"),
    "Ayuda": ("AYUDA", "blue", "white"),
    "Tools": ("HERRAMIENTAS", "yellow", "white"),
    "Streaming": ("AGENTE · RESPONDIENDO", "green", "white"),
}


def make_chat_message(speaker: str, message: str, collapsed: bool = False):
    if speaker == "Estadísticas":
        return make_stats_message(message)
    label, border, body = STYLES.get(speaker, (speaker.upper(), "white", "white"))
    if collapsed or len(message) > 500 or speaker.startswith("Subagente sa-"):
        title_detail = " ".join(message.split())[:88]
        title = f"{label} · {title_detail}" if title_detail else label
        return Collapsible(
            Static(Text(message, style=body), markup=False),
            title=title,
            collapsed=True,
            classes="chat-details",
        )
    panel = Panel(
        Text(message, style=body),
        title=Text(label, style=f"bold {border}"),
        title_align="left",
        border_style=border,
        padding=(0, 1),
        expand=True,
    )
    return Static(panel, markup=False, classes="chat-message")


class StreamedAnswer(Static):
    """Una sola tarjeta que se actualiza con los deltas de texto del modelo."""

    def __init__(self) -> None:
        self._streamed_text = ""
        self.label = "AGENTE · RESPONDIENDO"
        super().__init__("", markup=False, classes="chat-message")
        self.update(self._render_panel())

    def append_text(self, delta: str) -> None:
        self._streamed_text += delta
        self.update(self._render_panel())

    def finish(self, answer: str) -> None:
        self._streamed_text = answer
        self.label = "RESPUESTA FINAL"
        self.update(self._render_panel())

    def _render_panel(self) -> Panel:
        return Panel(
            Text(self._streamed_text or "…", style="white"),
            title=Text(self.label, style="bold green"),
            title_align="left",
            border_style="green",
            padding=(0, 1),
            expand=True,
        )
