"""Loop principal: Jev decide una acción, el LLM la ejecuta y el harness registra."""

import asyncio
import json
import os
import signal
import sys
import uuid
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Awaitable, Callable

from openai import AsyncOpenAI

from ..workspace.context import CODE_DIR, WORK_DIR, load_environment
from ..decision_model import ActionChooser, LLMRouter
from .events import AgentEvent
from ..integrations.mcp import MCPManager
from ..prompts import action_prompt, build_context_prompt, build_main_prompt
from ..settings import (
    DECISION_MODEL_ENABLED_DEFAULT,
    MAX_AGENT_STEPS,
    MAX_CONTEXT_BUILDS,
    MAX_HISTORY_ITEMS,
    MAX_SUBAGENT_STEPS,
    MAX_TOOL_OUTPUT_CHARS,
)
from ..tools import TOOLS, dispatch_local_tool
from ..workspace.usage import UsageTracker


DELEGATE_TOOL = {
    "type": "function",
    "name": "delegate_task",
    "description": (
        "Lanza un subagente de programación en un proceso separado para una subtarea "
        "acotada. La interfaz mostrará su identificador y estado."
    ),
    "parameters": {
        "type": "object",
        "properties": {"task": {"type": "string", "description": "Subtarea concreta y verificable."}},
        "required": ["task"],
        "additionalProperties": False,
    },
    "strict": True,
}

Emit = Callable[[AgentEvent], Awaitable[None]]


class Agent:
    def __init__(self) -> None:
        load_environment()
        self.client = AsyncOpenAI()
        self.decision_enabled = DECISION_MODEL_ENABLED_DEFAULT
        self.chooser = ActionChooser(enabled=self.decision_enabled)
        self.router = LLMRouter(enabled=self.decision_enabled)
        self.stats = UsageTracker(self.router.config)
        self.instructions = build_main_prompt()
        self.mcp = MCPManager()
        self.history: list[Any] = []
        self.run_count = 0
        self.subagents: dict[str, dict[str, Any]] = {}
        self._subagent_processes: dict[str, asyncio.subprocess.Process] = {}
        self._next_subagent_number = 1

    async def start_mcp(self) -> str:
        return await self.mcp.start()

    async def close(self) -> None:
        processes = list(self._subagent_processes.values())
        self._subagent_processes.clear()
        await asyncio.gather(
            *(self._stop_subprocess(process) for process in processes),
            asyncio.wait_for(self.mcp.close(), timeout=5),
            asyncio.wait_for(self.client.close(), timeout=5),
            return_exceptions=True,
        )

    @staticmethod
    async def _stop_subprocess(process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None and os.name == "nt":
            return
        try:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        try:
            await asyncio.wait_for(process.wait(), timeout=1.5)
            return
        except asyncio.TimeoutError:
            pass
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass
        try:
            await asyncio.wait_for(process.wait(), timeout=2)
        except asyncio.TimeoutError:
            pass

    def available_tool_schemas(self, include_delegate: bool = True) -> list[dict[str, Any]]:
        schemas = [*TOOLS, *self.mcp.tools_for_model]
        if include_delegate:
            schemas.append(DELEGATE_TOOL)
        return schemas

    def available_tools(self) -> list[str]:
        return [tool["name"] for tool in self.available_tool_schemas()]

    def restore(self, history: list[Any], run_count: int = 0) -> None:
        self.history = history if isinstance(history, list) else []
        self.run_count = max(0, int(run_count))

    def set_decision_enabled(self, enabled: bool) -> None:
        self.decision_enabled = bool(enabled)
        self.chooser.enabled = self.decision_enabled
        self.router.enabled = self.decision_enabled

    async def _disable_decision_after_failure(self, reason: str, emit: Emit) -> None:
        if not self.decision_enabled:
            return
        self.set_decision_enabled(False)
        detail = " ".join(reason.split())[:320]
        await self._emit(
            emit,
            "Decision Model",
            f"Jev no está disponible; Decision Model desactivado automáticamente. {detail}",
            details={"decision_model": "disabled_after_failure"},
        )

    def subagent_summaries(self) -> list[dict[str, Any]]:
        return sorted(
            self.subagents.values(), key=lambda item: item["started_at"], reverse=True
        )

    def describe_subagents(self, agent_id: str | None = None) -> str:
        agents = self.subagent_summaries()
        if agent_id:
            target = next((item for item in agents if item["id"] == agent_id), None)
            if target is None:
                return f"No existe un subagente con id {agent_id}."
            return (
                f"{target['id']} · {target['status']} · PID {target.get('pid', '—')}\n"
                f"Tarea: {target['task']}\n"
                f"Inicio: {target['started_at']}\n"
                f"Último evento: {target.get('last_event', 'sin eventos')}\n"
                f"Resultado: {target.get('result', 'pendiente')}"
            )
        if not agents:
            return "No se han lanzado subagentes en esta sesión."
        rows = ["ID      ESTADO       PID      TAREA"]
        for item in agents:
            task = " ".join(item["task"].split())
            if len(task) > 72:
                task = task[:69] + "..."
            rows.append(
                f"{item['id']:<7} {item['status']:<12} "
                f"{str(item.get('pid', '—')):<8} {task}"
            )
        return "\n".join(rows)

    async def compact_history(self, goal: str, emit: Emit) -> None:
        if len(self.history) < MAX_HISTORY_ITEMS:
            return
        await self._emit(emit, "Sistema", "Compactando el historial anterior.", 1)
        decision_enabled = self.decision_enabled
        route = await self.router.route(
            goal=goal,
            action="compactar el historial conservando hechos reutilizables",
            recent_context=ActionChooser._history_excerpt(self.history),
        )
        if route.jev_usage is not None:
            self.stats.record_jev_usage(
                input_tokens=route.jev_usage.input_tokens,
                output_tokens=route.jev_usage.output_tokens,
                purpose="routing",
                decision_enabled=decision_enabled,
            )
        if route.failed:
            await self._disable_decision_after_failure(route.reason, emit)
        response = await self.client.responses.create(
            model=route.model,
            reasoning={"effort": route.reasoning_effort},
            instructions=(
                "Resume en español los objetivos, decisiones, datos y resultados que "
                "puedan ayudar en tareas futuras. Separa hechos de dudas y no inventes."
            ),
            input=self.history,
        )
        self.stats.record_request(
            model=route.model,
            tier=route.tier,
            usage=getattr(response, "usage", None),
            route_used_typesafe=route.used_typesafe,
            decision_enabled=decision_enabled,
        )
        summary = response.output_text.strip() or "No hay contexto previo relevante."
        self.history = [{"role": "assistant", "content": f"Resumen de la sesión: {summary}"}]
        await self._emit(
            emit,
            "Contexto",
            f"Historial compacto ({route.model}, {route.tier}; "
            f"reasoning.effort={route.reasoning_effort}): {summary}",
            2,
            collapsed=True,
        )

    async def run(self, goal: str, emit: Emit) -> None:
        self.instructions = build_main_prompt()
        await self.compact_history(goal, emit)
        self.history.append({"role": "user", "content": goal})
        context_builds = 0
        tools = self.available_tool_schemas()

        for step in range(1, MAX_AGENT_STEPS + 1):
            await self._emit(
                emit,
                "Paso",
                f"Iteración {step}/{MAX_AGENT_STEPS}: preparando decisión discreta.",
                self._progress(step, 0.05),
            )
            decision_was_enabled = self.decision_enabled
            choice = await self.chooser.choose_next(
                goal=goal,
                history=self.history,
                tools=tools,
                step=step,
                allow_context=context_builds < MAX_CONTEXT_BUILDS,
            )
            if choice.jev_usage is not None:
                self.stats.record_jev_usage(
                    input_tokens=choice.jev_usage.input_tokens,
                    output_tokens=choice.jev_usage.output_tokens,
                    purpose="choice",
                    decision_enabled=decision_was_enabled,
                )
            if decision_was_enabled:
                self.stats.record_choice(choice.action, choice.used_typesafe)
            if choice.failed:
                await self._disable_decision_after_failure(choice.reason, emit)
            await self._emit(
                emit,
                "Decision Model",
                f"Choice → {choice.tool_name or choice.action}. {choice.reason}",
                self._progress(step, 0.12),
                {"decision": choice.action, "tool": choice.tool_name, "jev": choice.used_typesafe},
                collapsed=True,
            )

            if choice.action == "build_context":
                context_builds += 1
                response = await self._request(
                    goal=goal,
                    action="build_context",
                    tools=[],
                    tool_choice="none",
                    instructions=f"{self.instructions}\n\n{build_context_prompt()}\n\n{action_prompt('build_context')}",
                    emit=emit,
                    step=step,
                )
                note = response.output_text.strip() or "No se generó contexto adicional."
                await self._emit(
                    emit,
                    "Contexto",
                    note,
                    self._progress(step, 0.82),
                    {"kind": "context_builder"},
                    collapsed=True,
                )
                continue

            if choice.action == "final_answer":
                response = await self._request(
                    goal=goal,
                    action="final_answer",
                    tools=[],
                    tool_choice="none",
                    instructions=f"{self.instructions}\n\n{action_prompt('final_answer')}",
                    emit=emit,
                    step=step,
                )
                answer = response.output_text.strip() or "Tarea terminada."
                self.run_count += 1
                await self._emit(emit, "Respuesta", answer, 100)
                return

            if choice.action == "automatic_tool_selection":
                response = await self._request(
                    goal=goal,
                    action="automatic_tool_selection",
                    tools=tools,
                    tool_choice="auto",
                    instructions=f"{self.instructions}\n\n{action_prompt('automatic_tool_selection')}",
                    emit=emit,
                    step=step,
                )
                calls = [item for item in (response.output or []) if getattr(item, "type", None) == "function_call"]
                if not calls:
                    self.run_count += 1
                    await self._emit(
                        emit, "Respuesta", response.output_text.strip() or "Tarea terminada.", 100
                    )
                    return
                for call in calls:
                    await self._execute_call(
                        call, emit, self._progress(step, 0.82), selected_by_choice=False
                    )
                continue

            selected_name = choice.tool_name
            schema = next((tool for tool in tools if tool["name"] == selected_name), None)
            if schema is None:
                await self._emit(
                    emit,
                    "Error",
                    f"La tool elegida ya no está disponible: {selected_name}",
                    self._progress(step, 0.9),
                )
                continue
            if self._can_execute_without_llm(schema):
                call_id = f"call_{uuid.uuid4().hex}"
                self.history.append(
                    {
                        "type": "function_call",
                        "call_id": call_id,
                        "name": selected_name,
                        "arguments": "{}",
                    }
                )
                await self._emit(
                    emit,
                    "Decision Model",
                    f"Jev ejecuta {selected_name} directamente; no requiere argumentos ni request OpenAI.",
                    self._progress(step, 0.82),
                    {"decision": "direct_tool", "tool": selected_name, "openai_call_avoided": True},
                    collapsed=True,
                )
                await self._execute_call(
                    SimpleNamespace(name=selected_name, arguments="{}", call_id=call_id),
                    emit,
                    self._progress(step, 0.84),
                    selected_by_choice=True,
                    direct=True,
                )
                continue
            response = await self._request(
                goal=goal,
                action="tool",
                tools=[schema],
                tool_choice={"type": "function", "name": selected_name},
                instructions=(
                    f"{self.instructions}\n\n"
                    f"{action_prompt('tool', selected_name)}"
                ),
                emit=emit,
                step=step,
            )
            calls = [item for item in (response.output or []) if getattr(item, "type", None) == "function_call"]
            if not calls:
                text = response.output_text.strip() or "El modelo no generó la llamada solicitada."
                await self._emit(
                    emit,
                    "Contexto",
                    f"La llamada a {selected_name} no se generó. Nota del modelo: {text}",
                    self._progress(step, 0.85),
                    collapsed=True,
                )
                continue
            for call in calls:
                await self._execute_call(
                    call, emit, self._progress(step, 0.82), selected_by_choice=True
                )

        self.run_count += 1
        await self._emit(
            emit,
            "Sistema",
            f"Se alcanzó el límite de {MAX_AGENT_STEPS} iteraciones. Revisa el contexto y vuelve a indicar cómo continuar.",
            100,
        )

    async def _request(
        self,
        *,
        goal: str,
        action: str,
        tools: list[dict[str, Any]],
        tool_choice: Any,
        instructions: str,
        emit: Emit,
        step: int,
    ) -> Any:
        decision_enabled = self.decision_enabled
        route = await self.router.route(
            goal=goal,
            action=action,
            recent_context=ActionChooser._history_excerpt(self.history),
        )
        if route.jev_usage is not None:
            self.stats.record_jev_usage(
                input_tokens=route.jev_usage.input_tokens,
                output_tokens=route.jev_usage.output_tokens,
                purpose="routing",
                decision_enabled=decision_enabled,
            )
        if route.failed:
            await self._disable_decision_after_failure(route.reason, emit)
        await self._emit(
            emit,
            "Routing",
            f"Routing → {route.model} ({route.tier}; reasoning.effort="
            f"{route.reasoning_effort}). {route.reason}",
            self._progress(step, 0.25),
            {
                "model": route.model,
                "tier": route.tier,
                "reasoning_effort": route.reasoning_effort,
                "jev": route.used_typesafe,
            },
            collapsed=True,
        )
        request = {
            "model": route.model,
            "reasoning": {"effort": route.reasoning_effort},
            "instructions": instructions,
            "input": self.history,
            "tools": tools,
            "tool_choice": tool_choice,
        }
        if action == "final_answer":
            stream = await self.client.responses.create(**request, stream=True)
            response = None
            try:
                async for event in stream:
                    if event.type == "response.output_text.delta":
                        await self._emit(emit, "Streaming", event.delta)
                    elif event.type == "response.completed":
                        response = event.response
            finally:
                await stream.close()
            if response is None:
                raise RuntimeError("El stream del modelo terminó sin response.completed.")
        else:
            response = await self.client.responses.create(**request)
        self.stats.record_request(
            model=route.model,
            tier=route.tier,
            usage=getattr(response, "usage", None),
            route_used_typesafe=route.used_typesafe,
            decision_enabled=decision_enabled,
        )
        self.history.extend(response.output or [])
        if action != "final_answer":
            await self._emit(
                emit,
                "Paso",
                f"Respuesta del modelo recibida ({route.model}).",
                self._progress(step, 0.62),
                {"model": route.model, "output_items": len(response.output or [])},
                collapsed=True,
            )
        return response

    @staticmethod
    def _can_execute_without_llm(schema: dict[str, Any]) -> bool:
        parameters = schema.get("parameters", {})
        if not isinstance(parameters, dict):
            return False
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])
        return (
            isinstance(properties, dict)
            and not properties
            and isinstance(required, list)
            and not required
        )

    async def _execute_call(
        self,
        call: Any,
        emit: Emit,
        progress: float,
        *,
        selected_by_choice: bool,
        direct: bool = False,
    ) -> None:
        self.stats.record_tool_execution(
            selected_by_choice=selected_by_choice, direct=direct
        )
        name = call.name
        try:
            arguments = json.loads(call.arguments)
            if not isinstance(arguments, dict):
                raise ValueError("Los argumentos de una tool deben formar un objeto JSON.")
        except (json.JSONDecodeError, ValueError) as error:
            result = f"Error de herramienta {name}: argumentos no válidos: {error}"
        else:
            await self._emit(
                emit,
                "Tool en curso",
                f"Ejecutando {name}…",
                progress,
                {"tool": name, "arguments": arguments},
                collapsed=True,
            )
            if name == "delegate_task":
                result = await self._launch_subagent(str(arguments.get("task", "")), emit)
            elif name in self.mcp.model_tool_name_to_server:
                result = await self.mcp.call_tool(name, arguments)
            else:
                result = await dispatch_local_tool(name, arguments)

        if len(result) > MAX_TOOL_OUTPUT_CHARS:
            result = result[:MAX_TOOL_OUTPUT_CHARS] + "\n…salida truncada por el arnés."
        self.history.append(
            {"type": "function_call_output", "call_id": call.call_id, "output": result}
        )
        await self._emit(
            emit,
            "Tool",
            f"{name} → {result}",
            progress,
            {"tool": name, "result_chars": len(result)},
            collapsed=True,
        )

    async def _launch_subagent(self, task: str, emit: Emit) -> str:
        if not task.strip():
            return "Error: la tarea delegada está vacía."
        agent_id = f"sa-{self._next_subagent_number:03d}"
        self._next_subagent_number += 1
        started_at = datetime.now().astimezone().isoformat(timespec="seconds")
        state = {
            "id": agent_id,
            "task": task,
            "status": "starting",
            "started_at": started_at,
            "last_event": "Proceso solicitado.",
            "result": "pendiente",
            "logs": [],
        }
        self.subagents[agent_id] = state
        await self._emit(
            emit,
            "Subagente",
            f"Preparando el subproceso {agent_id}. Usa /agents o /agents {agent_id} para consultarlo.\nTarea: {task}",
            details={"agent_id": agent_id, "status": "starting", "task": task},
        )

        child_environment = os.environ.copy()
        existing_pythonpath = child_environment.get("PYTHONPATH", "")
        child_environment["PYTHONPATH"] = (
            str(CODE_DIR) + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
        )
        request = json.dumps(
            {
                "id": agent_id,
                "task": task,
                "max_steps": MAX_SUBAGENT_STEPS,
                "decision_enabled": self.decision_enabled,
            },
            ensure_ascii=False,
        )
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "ebis_cli.agent.subagent",
                cwd=str(WORK_DIR),
                env=child_environment,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=128 * 1024,
                **({"start_new_session": True} if os.name != "nt" else {}),
            )
        except Exception as error:
            state["status"] = "failed"
            state["last_event"] = str(error)
            await self._emit(
                emit,
                "Error",
                f"No se pudo iniciar {agent_id} como subproceso: {error}",
                details={"agent_id": agent_id, "status": "failed"},
            )
            return f"No se pudo iniciar {agent_id}: {error}"

        state["status"] = "running"
        state["pid"] = process.pid
        state["last_event"] = "Proceso iniciado."
        self._subagent_processes[agent_id] = process
        await self._emit(
            emit,
            "Subagente",
            f"▶ {agent_id} iniciado como subproceso (PID {process.pid}). Usa /agents para consultarlo.",
            details={"agent_id": agent_id, "status": "running", "pid": process.pid},
        )
        if process.stdin is not None:
            process.stdin.write(request.encode("utf-8"))
            await process.stdin.drain()
            process.stdin.close()
        stderr_task = asyncio.create_task(process.stderr.read()) if process.stderr else None

        try:
            while process.stdout is not None:
                line = await process.stdout.readline()
                if not line:
                    break
                try:
                    child_event = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    state["last_event"] = line.decode("utf-8", errors="replace")[:500]
                    continue
                if child_event.get("type") == "usage":
                    usage_payload = child_event.get("payload")
                    if isinstance(usage_payload, dict):
                        self.stats.record_request(**usage_payload)
                elif child_event.get("type") == "jev_usage":
                    self.stats.record_jev_usage(
                        input_tokens=child_event.get("input_tokens"),
                        output_tokens=child_event.get("output_tokens"),
                        purpose=str(child_event.get("purpose", "routing")),
                        decision_enabled=bool(
                            child_event.get("decision_enabled", self.decision_enabled)
                        ),
                    )
                elif child_event.get("type") == "decision_failure":
                    reason = str(child_event.get("reason", "falló una decisión en el subagente."))
                    await self._disable_decision_after_failure(reason, emit)
                elif child_event.get("type") == "event":
                    speaker = str(child_event.get("speaker", "Subagente"))
                    message = str(child_event.get("message", ""))
                    state["last_event"] = message[:500]
                    state["logs"].append({"speaker": speaker, "message": message})
                    await self._emit(
                        emit,
                        f"Subagente {agent_id}",
                        f"{speaker}: {message}",
                        details={"agent_id": agent_id, "status": "running"},
                        collapsed=True,
                    )
                elif child_event.get("type") == "result":
                    state["result"] = str(child_event.get("result", ""))
        except asyncio.CancelledError:
            await self._stop_subprocess(process)
            raise
        finally:
            return_code = process.returncode
            if return_code is None:
                return_code = await process.wait()
            stderr = await stderr_task if stderr_task else b""
            self._subagent_processes.pop(agent_id, None)

        if return_code == 0:
            state["status"] = "completed"
            state["last_event"] = "Subtarea terminada."
        else:
            state["status"] = "failed"
            state["last_event"] = stderr.decode("utf-8", errors="replace")[-1_000:]
            state["result"] = state["last_event"] or f"Proceso terminado con código {return_code}."
        await self._emit(
            emit,
            "Subagente",
            f"■ {agent_id} {state['status']}: {state['result']}",
            details={"agent_id": agent_id, "status": state["status"]},
            collapsed=True,
        )
        return f"Subagente {agent_id} ({state['status']}): {state['result']}"

    async def _emit(
        self,
        emit: Emit,
        speaker: str,
        message: str,
        progress: float | None = None,
        details: dict[str, Any] | None = None,
        collapsed: bool = False,
    ) -> None:
        await emit(
            AgentEvent(
                speaker=speaker,
                message=message,
                progress=progress,
                details=details or {},
                collapsed=collapsed,
            )
        )

    @staticmethod
    def _progress(step: int, phase: float) -> float:
        return min(99.0, ((step - 1 + phase) / MAX_AGENT_STEPS) * 100)
