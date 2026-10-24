"""Aplicación Textual: conversación, actividad en vivo e historial persistente."""

import asyncio
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input, ProgressBar, Static

from ..agent import Agent
from ..workspace.conversations import ConversationStore
from ..agent.events import AgentEvent
from ..settings import MAX_AGENT_STEPS
from .screens.history import HistoryScreen
from .widgets.chat_message import StreamedAnswer, make_chat_message


class EbisCLI(App):
    TITLE = "EBIS CLI · Decision Model"
    CSS_PATH = str(Path(__file__).resolve().parents[1] / "style.tcss")
    BINDINGS = [
        ("ctrl+l", "clear_view", "Limpiar vista"),
        ("ctrl+n", "new_conversation", "Nueva conversación"),
        ("f3", "history", "Historial"),
        ("ctrl+a", "agents", "Subagentes"),
        ("f1", "help", "Ayuda"),
        ("f2", "tools", "Tools"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.agent = Agent()
        self.store = ConversationStore()
        self.current_conversation = self.store.latest() or self.store.create()
        self.agent.stats.set_conversation(self.current_conversation["id"])
        self.agent.restore(
            self.current_conversation.get("agent_history", []),
            self.current_conversation.get("run_count", 0),
        )
        self.busy = False
        self._progress_value = 0.0
        self._progress_target = 0.0
        self._streaming_widget: StreamedAnswer | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="workspace-status", markup=False)
        yield ProgressBar(total=100, show_eta=False, id="progress")
        yield VerticalScroll(id="chat")
        yield Input(placeholder="Escribe una tarea · /help muestra comandos", id="prompt")
        yield Footer()

    async def on_mount(self) -> None:
        self._update_workspace_status()
        self._progress_timer = self.set_interval(0.08, self._animate_progress)
        for event in self.current_conversation.get("events", []):
            await self._append_widget(
                make_chat_message(
                    str(event.get("speaker", "Sistema")),
                    str(event.get("message", "")),
                    bool(event.get("details", {}).get("collapsed", False)),
                )
            )

        if not self.current_conversation.get("events"):
            await self.emit_event(
                AgentEvent(
                    "Sistema",
                    "Listo. /help muestra comandos; F3 abre el historial.",
                )
            )
        try:
            status = await self.agent.start_mcp()
            await self.emit_event(AgentEvent("Sistema", status, details={"mcp": True}))
        except Exception as error:
            await self.emit_event(
                AgentEvent(
                    "Error",
                    f"No se pudo cargar la configuración MCP. Las tools locales siguen disponibles. {error}",
                )
            )

    async def on_shutdown(self) -> None:
        workers = self.workers.cancel_group(self, "agent-run")
        if workers:
            try:
                await asyncio.wait_for(
                    self.workers.wait_for_complete(workers), timeout=4
                )
            except Exception:
                pass
        try:
            await asyncio.wait_for(self.agent.close(), timeout=8)
        except asyncio.TimeoutError:
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        if text.startswith("/"):
            await self.command(text)
            return
        if self.busy:
            await self.emit_event(
                AgentEvent("Sistema", "El agente está ocupado. Puedes consultar /agents mientras termina.")
            )
            return

        await self.emit_event(AgentEvent("Tú", text))
        self.busy = True
        self._update_workspace_status("Procesando objetivo…")
        self.run_goal(text)

    @work(group="agent-run", exclusive=True)
    async def run_goal(self, goal: str) -> None:
        self.busy = True
        self._progress_value = 0
        self._progress_target = 0
        self.query_one("#progress", ProgressBar).update(progress=0)
        self.query_one("#prompt", Input).placeholder = "El agente trabaja · /agents consulta subprocesos"
        self._update_workspace_status("Procesando objetivo…")
        try:
            await self.agent.run(goal, self.emit_event)
        except Exception as error:
            await self.emit_event(AgentEvent("Error", str(error), progress=100))
        finally:
            self.busy = False
            self.store.save_agent_state(
                self.current_conversation["id"], self.agent.history, self.agent.run_count
            )
            self._progress_target = 100
            self.query_one("#prompt", Input).placeholder = "Escribe otra tarea · /help muestra comandos"
            self._update_workspace_status()

    async def emit_event(self, event: AgentEvent) -> None:
        if event.speaker == "Streaming":
            await self._append_stream_delta(event.message)
            return

        details = dict(event.details)
        details["collapsed"] = event.collapsed
        self.store.add_event(
            self.current_conversation["id"], event.speaker, event.message, details
        )
        self.store.save_agent_state(
            self.current_conversation["id"], self.agent.history, self.agent.run_count
        )
        if event.speaker == "Respuesta" and self._streaming_widget is not None:
            self._streaming_widget.finish(event.message)
            self._streaming_widget = None
            if event.progress is not None and event.progress >= 100:
                self._progress_value = 100
                self._progress_target = 100
                self.query_one("#progress", ProgressBar).update(progress=100)
            return
        await self._append_widget(
            make_chat_message(event.speaker, event.message, event.collapsed)
        )
        if event.progress is not None:
            self._progress_target = max(self._progress_target, min(100.0, event.progress))
            if event.progress >= 100:
                self._progress_value = 100
                self.query_one("#progress", ProgressBar).update(progress=100)
        if event.speaker.startswith("Subagente"):
            self._update_workspace_status(f"Actividad: {event.speaker}")
        elif event.speaker == "Decision Model":
            self._update_workspace_status()

    async def _append_stream_delta(self, delta: str) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        was_at_bottom = chat.scroll_y >= chat.max_scroll_y - 1
        if self._streaming_widget is None:
            self._streaming_widget = StreamedAnswer()
            await chat.mount(self._streaming_widget)
        self._streaming_widget.append_text(delta)
        if was_at_bottom:
            chat.scroll_end(animate=False)

    async def _append_widget(self, widget) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        was_at_bottom = chat.scroll_y >= chat.max_scroll_y - 1
        await chat.mount(widget)
        if was_at_bottom:
            chat.scroll_end(animate=False)

    def _animate_progress(self) -> None:
        if self._progress_value < self._progress_target:
            self._progress_value = min(self._progress_target, self._progress_value + 0.22)
            self.query_one("#progress", ProgressBar).update(progress=self._progress_value)

    async def command(self, text: str) -> None:
        parts = text.strip().split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1].strip() if len(parts) > 1 else ""
        if command == "/help":
            await self.action_help()
        elif command == "/tools":
            await self.action_tools()
        elif command == "/clear":
            await self.action_clear_view()
        elif command in {"/new", "/conversation"}:
            await self.action_new_conversation()
        elif command == "/history":
            self.action_history()
        elif command == "/agents":
            await self.action_agents(argument or None)
        elif command == "/decision":
            await self.action_decision(argument)
        elif command == "/stat":
            await self.action_conversation_stats()
        elif command == "/stats":
            await self.action_stats()
        elif command == "/exit":
            self.exit()
        else:
            await self.emit_event(
                AgentEvent(
                    "Sistema",
                    "Comandos: /help, /tools, /agents [id], /decision [on|off|toggle|status], "
                    "/stat, /stats, /history, /new, /clear, /exit",
                )
            )

    async def action_help(self) -> None:
        await self.emit_event(
            AgentEvent(
                "Ayuda",
                "Escribe una tarea para el agente. /agents [id] consulta subagentes; "
                "/decision [on|off|toggle] activa o desactiva Jev; /stat muestra uso y coste de esta conversación; "
                "/stats muestra el acumulado del workspace. "
                "/history abre conversaciones; /new crea otra. Ctrl+N nueva, F3 historial, "
                "Ctrl+A subagentes, Ctrl+L limpia la vista. F2 tools, F1 ayuda.",
            )
        )

    async def action_tools(self) -> None:
        await self.emit_event(
            AgentEvent("Tools", "\n".join(self.agent.available_tools()), collapsed=True)
        )

    async def action_agents(self, agent_id: str | None = None) -> None:
        await self.emit_event(AgentEvent("Subagente", self.agent.describe_subagents(agent_id)))

    async def action_decision(self, argument: str = "") -> None:
        requested = argument.strip().lower()
        if requested in {"", "toggle"}:
            enabled = not self.agent.decision_enabled
        elif requested in {"on", "activar", "activa"}:
            enabled = True
        elif requested in {"off", "desactivar", "desactiva"}:
            enabled = False
        elif requested == "status":
            state = "activado" if self.agent.decision_enabled else "desactivado"
            await self.emit_event(AgentEvent("Decision Model", f"Decision Model {state}."))
            return
        else:
            await self.emit_event(
                AgentEvent("Sistema", "Uso: /decision [on|off|toggle|status]. Sin argumento, cambia el estado.")
            )
            return

        self.agent.set_decision_enabled(enabled)
        state = "activado" if enabled else "desactivado"
        timing = (
            " Se aplica desde la siguiente decision; los subagentes ya iniciados conservan "
            "el estado heredado."
            if self.busy
            else ""
        )
        self._update_workspace_status()
        await self.emit_event(AgentEvent("Decision Model", f"Decision Model {state}.{timing}"))

    async def action_stats(self) -> None:
        await self.emit_event(
            AgentEvent(
                "Estadísticas",
                self.agent.stats.report(
                    decision_enabled=self.agent.decision_enabled, scope="workspace"
                ),
            )
        )

    async def action_conversation_stats(self) -> None:
        await self.emit_event(
            AgentEvent(
                "Estadísticas",
                self.agent.stats.report(
                    decision_enabled=self.agent.decision_enabled, scope="conversation"
                ),
            )
        )

    async def action_new_conversation(self) -> None:
        if self.busy:
            await self.emit_event(AgentEvent("Sistema", "Espera a que termine el agente antes de cambiar de conversación."))
            return
        self.current_conversation = self.store.create()
        self.agent.stats.set_conversation(self.current_conversation["id"])
        self._progress_value = 0
        self._progress_target = 0
        self.query_one("#progress", ProgressBar).update(progress=0)
        self.agent.restore([], 0)
        await self.action_clear_view()
        self._update_workspace_status()
        await self.emit_event(AgentEvent("Sistema", "Nueva conversación iniciada."))
        self.query_one("#prompt", Input).focus()

    @work(group="history-dialog", exclusive=True)
    async def action_history(self) -> None:
        if self.busy:
            await self.emit_event(AgentEvent("Sistema", "Consulta el progreso con /agents; el historial se puede abrir al terminar."))
            return
        selected_id = await self.push_screen_wait(HistoryScreen(self.store.list()))
        if selected_id:
            await self.open_conversation(selected_id)

    async def open_conversation(self, conversation_id: str) -> None:
        conversation = self.store.get(conversation_id)
        if conversation is None:
            await self.emit_event(AgentEvent("Error", "No se pudo abrir esa conversación."))
            return
        self.current_conversation = conversation
        self.agent.stats.set_conversation(conversation_id)
        self.agent.restore(
            conversation.get("agent_history", []), conversation.get("run_count", 0)
        )
        await self.action_clear_view()
        for event in conversation.get("events", []):
            await self._append_widget(
                make_chat_message(
                    str(event.get("speaker", "Sistema")),
                    str(event.get("message", "")),
                    bool(event.get("details", {}).get("collapsed", False)),
                )
            )
        self._update_workspace_status()
        self.query_one("#prompt", Input).focus()

    async def action_clear_view(self) -> None:
        await self.query_one("#chat", VerticalScroll).remove_children()
        self._streaming_widget = None

    def _update_workspace_status(self, activity: str = "") -> None:
        if not self.is_mounted:
            return
        title = self.current_conversation.get("title", "Conversación")
        short_id = self.current_conversation.get("id", "")[:8]
        agent_status = " · trabajando" if self.busy else " · listo"
        decision_status = " · decision ON" if self.agent.decision_enabled else " · decision OFF"
        suffix = f" · {activity}" if activity else ""
        self.query_one("#workspace-status", Static).update(
            f"{title}  [{short_id}]{agent_status}{decision_status}{suffix}  ·  {MAX_AGENT_STEPS} iteraciones máx."
        )


def main() -> None:
    EbisCLI().run()
