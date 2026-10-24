"""Punto de entrada del subagente aislado en un proceso hijo."""

import asyncio
import json
import sys
from typing import Any

from openai import AsyncOpenAI

from ..workspace.context import load_environment
from ..decision_model import LLMRouter
from ..prompts import build_worker_prompt
from ..settings import (
    DECISION_MODEL_ENABLED_DEFAULT,
    MAX_SUBAGENT_RESULT_CHARS,
    MAX_SUBAGENT_STEPS,
)
from ..tools import TOOLS, dispatch_local_tool


def _send(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()


def _event(speaker: str, message: str, **details: Any) -> None:
    _send({"type": "event", "speaker": speaker, "message": message, "details": details})


async def run_worker(request: dict[str, Any]) -> str:
    load_environment()
    task = str(request.get("task", "")).strip()
    agent_id = str(request.get("id", "worker"))
    if not task:
        return "La tarea delegada estaba vacía."

    client = AsyncOpenAI()
    enabled = request.get("decision_enabled", DECISION_MODEL_ENABLED_DEFAULT)
    router = LLMRouter(enabled=enabled if isinstance(enabled, bool) else True)
    history: list[Any] = [{"role": "user", "content": task}]
    instructions = build_worker_prompt(task)
    max_steps = min(MAX_SUBAGENT_STEPS, max(1, int(request.get("max_steps", MAX_SUBAGENT_STEPS))))
    try:
        for step in range(1, max_steps + 1):
            _event("Paso", f"{agent_id}: iteración {step}/{max_steps}.")
            route = await router.route(
                goal=task,
                action="resolver subtarea delegada",
                recent_context="\n".join(str(item)[:400] for item in history[-4:]),
            )
            if route.jev_usage is not None:
                _send(
                    {
                        "type": "jev_usage",
                        "purpose": "routing",
                        "input_tokens": route.jev_usage.input_tokens,
                        "output_tokens": route.jev_usage.output_tokens,
                        "decision_enabled": router.enabled,
                    }
                )
            if route.failed and router.enabled:
                router.enabled = False
                _send({"type": "decision_failure", "reason": route.reason})
            _event(
                "Routing",
                f"Modelo {route.model} ({route.tier}; reasoning.effort="
                f"{route.reasoning_effort}); {route.reason}",
            )
            response = await client.responses.create(
                model=route.model,
                reasoning={"effort": route.reasoning_effort},
                instructions=instructions,
                input=history,
                tools=TOOLS,
                tool_choice="auto",
            )
            usage = getattr(response, "usage", None)
            model_dump = getattr(usage, "model_dump", None)
            usage_data = (
                model_dump(mode="json", exclude_none=True)
                if callable(model_dump)
                else usage
            )
            _send(
                {
                    "type": "usage",
                    "payload": {
                        "model": route.model,
                        "tier": route.tier,
                        "reasoning_effort": route.reasoning_effort,
                        "usage": usage_data,
                        "route_used_typesafe": route.used_typesafe,
                        "decision_enabled": router.enabled,
                    },
                }
            )
            history.extend(response.output or [])
            calls = [item for item in (response.output or []) if getattr(item, "type", None) == "function_call"]
            if not calls:
                return response.output_text.strip() or "Subtarea terminada sin texto final."

            for call in calls:
                try:
                    arguments = json.loads(call.arguments)
                    if not isinstance(arguments, dict):
                        raise ValueError("Los argumentos deben ser un objeto JSON.")
                    _event("Tool", f"{call.name} iniciado.", tool=call.name)
                    result = await dispatch_local_tool(call.name, arguments)
                except Exception as error:
                    result = f"Error de tool {call.name}: {error}"
                history.append(
                    {"type": "function_call_output", "call_id": call.call_id, "output": result}
                )
                _event("Tool", f"{call.name} terminó: {result[:700]}", tool=call.name)
        return f"La subtarea alcanzó el límite de {max_steps} iteraciones."
    finally:
        await client.close()


async def _main() -> None:
    try:
        request = json.loads(sys.stdin.read() or "{}")
        if not isinstance(request, dict):
            raise ValueError("La petición del subagente debe ser un objeto JSON.")
        result = await run_worker(request)
        if len(result) > MAX_SUBAGENT_RESULT_CHARS:
            result = result[:MAX_SUBAGENT_RESULT_CHARS] + "\n…resultado truncado."
        _send({"type": "result", "result": result})
    except Exception as error:
        _event("Error", str(error))
        _send({"type": "result", "result": f"Error del subagente: {error}"})
        raise


if __name__ == "__main__":
    asyncio.run(_main())
