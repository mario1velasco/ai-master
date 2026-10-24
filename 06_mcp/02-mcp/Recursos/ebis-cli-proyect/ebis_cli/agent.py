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
        # TODO 1: inicializa MCPManager y guárdalo en self.mcp.

    async def start_mcp(self):
        # TODO 2: inicia el gestor MCP y devuelve su mensaje de estado.
        raise NotImplementedError

    async def close(self):
        await self.mcp.close()

    def available_tools(self):
        return [tool["name"] for tool in self.available_tool_schemas()]

    def available_tool_schemas(self):
        # TODO 3: concatena TOOLS con las tools MCP descubiertas.
        return TOOLS + self.mcp.TODO_TOOLS_FOR_MODEL

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
                # TODO 4: pasa al modelo los esquemas locales y los esquemas MCP.
                tools=self.TODO_AVAILABLE_TOOL_SCHEMAS(),
            )
            run_history.extend(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                self.history.extend(run_history[history_start:])
                self.run_count += 1
                emit("Agente", response.output_text or "Tarea terminada.")
                return
            for call in calls:
                try:
                    arguments = json.loads(call.arguments)
                    if not isinstance(arguments, dict):
                        raise ValueError("Los argumentos de la tool deben ser un objeto JSON.")

                    # TODO 5: comprueba si call.name está en el mapa de nombres MCP.
                    if call.name in self.mcp.TODO_NAME_MAP:
                        result = await self.mcp.call_tool(call.name, arguments)
                    else:
                        result = dispatch_tool(call.name, arguments)
                    if not isinstance(result, str):
                        result = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as error:
                    result = f"Error de herramienta {call.name}: {error}"

                speaker = "Error" if result.startswith("Error de herramienta") else "Tool"
                emit(speaker, f"{call.name} -> {result}")
                run_history.append({"type": "function_call_output", "call_id": call.call_id, "output": result})

        self.history.extend(run_history[history_start:])
        self.run_count += 1
        emit("Sistema", "Límite alcanzado.")
