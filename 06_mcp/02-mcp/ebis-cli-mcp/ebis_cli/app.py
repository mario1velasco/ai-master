from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, RichLog, Static

from .agent import Agent


class EbisCLI(App):
    TITLE = "EBIS CLI MCP — Agente con tools locales y MCP"
    CSS_PATH = "style.tcss"
    BINDINGS = [
        ("ctrl+l", "clear_log", "Limpiar"),
        ("f1", "help", "Ayuda"),
        ("f2", "tools", "Tools"),
    ]

    def __init__(self):
        super().__init__()
        self.agent = Agent()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Tip: escribe /help o /tools", id="tip", markup=False)
        yield RichLog(id="chat", wrap=True, markup=False, highlight=False)
        yield Input(placeholder="Escribe un objetivo para el agente o usa /help")
        yield Footer()

    async def on_mount(self) -> None:
        try:
            status = await self.agent.start_mcp()
            self.say("Sistema", status)
        except Exception as error:
            self.say("Error", f"No se pudo iniciar MCP; las tools locales siguen disponibles. {error}")
        self.say("Sistema", "Listo. Escribe un objetivo o usa /help.")

    async def on_unmount(self) -> None:
        await self.agent.close()

    def say(self, speaker: str, message: str) -> None:
        styles = {
            "Tú": ("OBJETIVO · TÚ", "cyan", "white"),
            "Respuesta": ("RESPUESTA FINAL", "green", "white"),
            "Tool": ("TOOL / ACCIÓN", "yellow", "yellow"),
            "Subagente tool": ("TOOL DE SUBAGENTE", "yellow", "yellow"),
            "Sistema": ("PASO DEL SISTEMA", "blue", "bright_blue"),
            "Paso": ("PROGRESO DEL AGENTE", "cyan", "white"),
            "Agente": ("AGENTE", "cyan", "white"),
            "Subagente": ("SUBAGENTE", "magenta", "white"),
            "Verificador": ("VERIFICADOR", "magenta", "white"),
            "Error": ("ERROR", "red", "bright_red"),
            "Ayuda": ("AYUDA", "blue", "white"),
            "Tools": ("HERRAMIENTAS", "yellow", "white"),
        }
        title, border, body = styles.get(speaker, (speaker.upper(), "white", "white"))
        panel = Panel(
            Text(message, style=body),
            title=Text(title, style=f"bold {border}"),
            title_align="left",
            border_style=border,
            padding=(0, 1),
            expand=True,
        )
        self.query_one("#chat", RichLog).write(panel)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        if text.startswith("/"):
            await self.command(text)
            return

        self.say("Tú", text)
        pending_agent_message = None

        def emit_agent_events(speaker: str, message: str) -> None:
            nonlocal pending_agent_message
            if speaker == "Agente":
                if pending_agent_message is not None:
                    self.say("Paso", pending_agent_message)
                pending_agent_message = message
                return

            if pending_agent_message is not None:
                self.say("Paso", pending_agent_message)
                pending_agent_message = None
            self.say(speaker, message)

        event.input.disabled = True
        try:
            await self.agent.run(text, emit_agent_events)
            if pending_agent_message is not None:
                self.say("Respuesta", pending_agent_message)
        except Exception as error:
            if pending_agent_message is not None:
                self.say("Paso", pending_agent_message)
            self.say("Error", str(error))
        finally:
            event.input.disabled = False
            event.input.focus()

    async def command(self, text: str) -> None:
        command = text.lower().split()[0]
        if command == "/help":
            self.action_help()
        elif command == "/tools":
            self.action_tools()
        elif command == "/clear":
            self.action_clear_log()
        elif command == "/exit":
            self.exit()
        else:
            self.say("Sistema", "Comandos: /help, /tools, /clear, /exit")

    def action_help(self) -> None:
        self.say("Ayuda", "Escribe un objetivo. /tools muestra capacidades; /clear limpia; /exit sale.")

    def action_tools(self) -> None:
        self.say("Tools", ", ".join(self.agent.available_tools()))

    def action_clear_log(self) -> None:
        self.query_one("#chat", RichLog).clear()


def main() -> None:
    EbisCLI().run()

if __name__ == "__main__":
    main()
