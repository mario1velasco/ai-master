"""Selector modal de conversaciones guardadas."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class HistoryScreen(ModalScreen[str | None]):
    CSS = """
    HistoryScreen { align: center middle; background: $background 80%; }
    #history-dialog { width: 80%; height: 80%; max-width: 100; max-height: 85%; padding: 1 2; border: round $accent; background: $surface; }
    #history-title { height: 2; text-style: bold; color: $accent; }
    #history-list { height: 1fr; min-height: 3; }
    .history-entry { width: 1fr; margin: 0 0 1 0; }
    #history-cancel { width: 18; }
    """

    def __init__(self, conversations: list[dict[str, Any]]) -> None:
        super().__init__()
        self.conversations = conversations

    def compose(self) -> ComposeResult:
        with Vertical(id="history-dialog"):
            yield Static("Conversaciones guardadas  ·  Esc para cerrar", id="history-title")
            with VerticalScroll(id="history-list"):
                if not self.conversations:
                    yield Static("Todavía no hay conversaciones guardadas.")
                for item in self.conversations:
                    title = str(item.get("title", "Conversación"))
                    updated = str(item.get("updated_at", ""))[:16].replace("T", " ")
                    event_count = len(item.get("events", []))
                    label = f"{title}  ·  {updated}  ·  {event_count} eventos"
                    yield Button(label, id=f"history-{item['id']}", classes="history-entry")
            yield Button("Cerrar", id="history-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "history-cancel":
            self.dismiss(None)
        elif button_id.startswith("history-"):
            self.dismiss(button_id.removeprefix("history-"))
