import json
import os

from openai import AsyncOpenAI

from .context import load_environment, load_instructions
from .tools import TOOLS, dispatch_tool


MAX_STEPS = 6
MAX_HISTORY_WORDS = 300
DEFAULT_INSTRUCTIONS = (
    "Eres EBIS-CLI, un agente en español. Recuerda el contexto de esta sesión. "
    "Trabaja en la carpeta de trabajo actual."
)


class Agent:
    def __init__(self):
        load_environment()
        self.client = AsyncOpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-6-astra")
        self.history = []
        self.instructions = load_instructions(DEFAULT_INSTRUCTIONS)

    def available_tools(self):
        return [tool["name"] for tool in TOOLS]

    async def run(self, goal, emit):
        # TODO 2: Crea count_history_words y compact_history, invoca la compactación
        # antes de preparar run_history y cambia input=goal por input=run_history.

        run_history = list(self.history)
        history_start = len(run_history)
        run_history.append({"role": "user", "content": goal})
        emit("Agente", "Instrucciones disponibles; historial de sesión preparado.")

        for step in range(1, MAX_STEPS + 1):
            emit("Sistema", f"Paso {step}/{MAX_STEPS}")
            response = await self.client.responses.create(
                model=self.model,
                instructions=self.instructions,
                input=goal,
                tools=TOOLS,
            )
            run_history.extend(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                self.history.extend(run_history[history_start:])
                emit("Agente", response.output_text or "Tarea terminada.")
                return

            for call in calls:
                result = dispatch_tool(call.name, json.loads(call.arguments))
                emit("Tool", f"{call.name} -> {result}")
                run_history.append(
                    {"type": "function_call_output", "call_id": call.call_id, "output": result}
                )

        self.history.extend(run_history[history_start:])
        emit("Sistema", "Límite alcanzado.")
