import json
import os

from openai import AsyncOpenAI

from .context import load_environment, load_instructions
from .tools import TOOLS, dispatch_tool


INSTRUCTIONS = "Eres EBIS-CLI, un agente en español. Resuelve el objetivo usando las tools locales cuando te ayuden. Trabaja en la carpeta de trabajo actual."


class Agent:
    def __init__(self):
        load_environment()
        self.client = AsyncOpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-6-astra")
        self.instructions = load_instructions(INSTRUCTIONS)

    def available_tools(self):
        return [tool["name"] for tool in TOOLS]

    async def run(self, goal, emit):
        emit("Agente", "Empiezo el trabajo.")
        input_items = [{"role": "user", "content": goal}]

        while True:
            response = await self.client.responses.create(
                model=self.model, instructions=self.instructions, input=input_items, tools=TOOLS
            )
            input_items.extend(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                emit("Agente", response.output_text or "Tarea terminada.")
                return

            for call in calls:
                arguments = json.loads(call.arguments)
                result = dispatch_tool(call.name, arguments)
                emit("Tool", f"{call.name} -> {result}")
                input_items.append({"type": "function_call_output", "call_id": call.call_id, "output": result})
