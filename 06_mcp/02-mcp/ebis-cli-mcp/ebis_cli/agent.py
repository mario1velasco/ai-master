import json
import os
from openai import AsyncOpenAI

from .context import load_environment, load_instructions
from .mcp import MCPManager
from .tools import TOOLS, dispatch_tool


MAX_STEPS = 6
MAX_CONTEXT_ITEMS = 20
# Umbral de ejemplo; en un harness real dependería de la ventana de contexto.
CONTEXT_BUILD_AFTER_RUNS = 3
DEFAULT_INSTRUCTIONS = "Eres EBIS-CLI, un agente en español. Recuerda el contexto de esta sesión. Trabaja en la carpeta de trabajo actual."


class Agent:
    def __init__(self):
        load_environment()
        self.client = AsyncOpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-6-astra")
        self.history = []
        self.run_count = 0
        self.instructions = load_instructions(DEFAULT_INSTRUCTIONS)
        self.mcp = MCPManager()

    async def start_mcp(self):
        return await self.mcp.start()

    async def close(self):
        await self.mcp.close()

    def available_tools(self):
        return [tool["name"] for tool in self.available_tool_schemas()]

    def available_tool_schemas(self):
        return TOOLS + self.mcp.tools_for_model

    async def compact_history(self):
        if len(self.history) < MAX_CONTEXT_ITEMS:
            return
        response = await self.client.responses.create(
            model=self.model,
            instructions="Resume en español los objetivos, decisiones y resultados de esta conversación. Conserva los datos que ayudarían a continuar.",
            input=self.history,
        )
        self.history = [{"role": "assistant", "content": "Resumen de la sesión: " + response.output_text}]

    async def build_context(self, goal):
        if not self.history:
            return "No hay contexto previo relevante."

        response = await self.client.responses.create(
            model=self.model,
            instructions=(
                "Prepara el contexto para el objetivo actual. Del historial, conserva solo "
                "hechos, decisiones y resultados anteriores que ayuden a cumplirlo. "
                "No resuelvas el objetivo ni inventes información. Si nada es relevante, "
                "responde: No hay contexto previo relevante."
            ),
            input=self.history + [{"role": "user", "content": f"Objetivo actual: {goal}"}],
        )
        return response.output_text or "No hay contexto previo relevante."

    async def run(self, goal, emit):
        await self.compact_history()
        if self.run_count < CONTEXT_BUILD_AFTER_RUNS:
            run_history = list(self.history)
            history_start = len(run_history)
            run_history.append({"role": "user", "content": goal})
            emit("Sistema", f"Historial completo disponible; build_context se activa tras {CONTEXT_BUILD_AFTER_RUNS} runs.")
        else:
            context = await self.build_context(goal)
            run_history = [
                {
                    "role": "user",
                    "content": f"Contexto relevante de la sesión:\n{context}\n\nObjetivo actual:\n{goal}",
                }
            ]
            history_start = 0
            emit("Sistema", f"Contexto relevante para este objetivo: {context}")

        emit("Agente", "Instrucciones disponibles; historial de sesión preparado.")

        for step in range(1, MAX_STEPS + 1):
            emit("Sistema", f"Paso {step}/{MAX_STEPS}")
            response = await self.client.responses.create(
                model=self.model,
                instructions=self.instructions,
                input=run_history,
                tools=self.available_tool_schemas(),
            )
            run_history.extend(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                self.history.extend(run_history[history_start:])
                self.run_count += 1
                emit("Agente", response.output_text or "Tarea terminada.")
                return
            for call in calls:
                arguments = json.loads(call.arguments)
                if call.name in self.mcp.model_tool_name_to_mcp_name:
                    result = await self.mcp.call_tool(call.name, arguments)
                else:
                    result = dispatch_tool(call.name, arguments)
                emit("Tool", f"{call.name} -> {result}")
                run_history.append({"type": "function_call_output", "call_id": call.call_id, "output": result})

        self.history.extend(run_history[history_start:])
        self.run_count += 1
        emit("Sistema", "Límite alcanzado.")
