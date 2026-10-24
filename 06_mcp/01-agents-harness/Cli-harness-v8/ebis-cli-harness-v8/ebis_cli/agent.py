import json
import os
from openai import AsyncOpenAI

from .context import load_environment, load_instructions
from .tools import TOOLS, dispatch_tool

DELEGATE_TOOL = {
    "type": "function", "name": "delegate_task", "description": "Delega una parte del objetivo a un subagente con contexto propio.",
    "parameters": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"], "additionalProperties": False},
    "strict": True,
}


MAX_STEPS = 6
MAX_CONTEXT_ITEMS = 20
# Umbral de ejemplo; en un harness real dependería de la ventana de contexto.
CONTEXT_BUILD_AFTER_RUNS = 3
LEAD_PERMISSIONS = {"list_files", "read_file", "write_file", "save_memory", "read_memory", "verify_file", "delegate_task"}
WORKER_PERMISSIONS = {"list_files", "read_file", "write_file"}
DEFAULT_INSTRUCTIONS = "Eres EBIS-CLI, un agente en español. Recuerda la sesión, guarda datos útiles y verifica tu trabajo. Trabaja en la carpeta de trabajo actual."


class Agent:
    def __init__(self):
        load_environment()
        self.client = AsyncOpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-6-astra")
        self.history = []
        self.run_count = 0
        self.instructions = load_instructions(DEFAULT_INSTRUCTIONS)

    def available_tools(self):
        return sorted(LEAD_PERMISSIONS)

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

    def tools_for(self, role):
        allowed = LEAD_PERMISSIONS if role == "lead" else WORKER_PERMISSIONS
        definitions = TOOLS + [DELEGATE_TOOL]
        return [tool for tool in definitions if tool["name"] in allowed]

    def execute(self, role, name, arguments):
        allowed = LEAD_PERMISSIONS if role == "lead" else WORKER_PERMISSIONS
        if name not in allowed:
            return f"Permiso denegado: {role} no puede usar {name}"
        if name == "delegate_task":
            return "delegate_task debe ejecutarse de forma asíncrona"
        return dispatch_tool(name, arguments)

    async def act(self, emit, history):
        notes = []
        for step in range(1, MAX_STEPS + 1):
            emit("Sistema", f"Paso {step}/{MAX_STEPS}")
            response = await self.client.responses.create(
                model=self.model, instructions=self.instructions, input=history, tools=self.tools_for("lead")
            )
            history.extend(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                return response.output_text or "Tarea terminada.", "\n".join(notes)
            for call in calls:
                arguments = json.loads(call.arguments)
                if call.name == "delegate_task":
                    result = await self.run_subagent(arguments["task"], emit)
                else:
                    result = self.execute("lead", call.name, arguments)
                notes.append(f"{call.name}: {result}")
                emit("Tool", f"{call.name} -> {result}")
                history.append({"type": "function_call_output", "call_id": call.call_id, "output": result})
        return "El límite de pasos se alcanzó.", "\n".join(notes)

    async def review(self, goal, answer, notes):
        response = await self.client.responses.create(
            model=self.model,
            instructions="Eres un verificador independiente. Compara el objetivo con la respuesta y las pruebas. Responde con PASS si está completo; si no, empieza con FIX: y explica el cambio concreto.",
            input=f"Objetivo: {goal}\nRespuesta: {answer}\nAcciones y resultados: {notes}",
        )
        return response.output_text.strip()

    async def run_subagent(self, task, emit):
        emit("Subagente", f"Empiezo: {task}")
        messages = [{"role": "user", "content": task}]
        for _ in range(3):
            response = await self.client.responses.create(
                model=self.model, instructions=self.instructions + "\nAdemás, eres un subagente con permisos limitados. Resuelve solo la tarea delegada en la carpeta de trabajo actual.", input=messages, tools=self.tools_for("worker")
            )
            messages.extend(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                return response.output_text or "Subtarea terminada."
            for call in calls:
                result = self.execute("worker", call.name, json.loads(call.arguments))
                messages.append({"type": "function_call_output", "call_id": call.call_id, "output": result})
                emit("Subagente tool", f"{call.name} -> {result}")
        return "Subagente detenido al llegar a 3 pasos."

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
        emit("Agente", "El resultado pasará por una revisión independiente.")

        for review_number in range(2):
            answer, notes = await self.act(emit, run_history)
            verdict = await self.review(goal, answer, notes)
            emit("Verificador", verdict)
            if verdict.upper().startswith("PASS"):
                self.history.extend(run_history[history_start:])
                self.run_count += 1
                emit("Agente", answer)
                return
            if review_number == 0:
                run_history.append({"role": "user", "content": "Feedback del verificador: " + verdict + " Corrige el trabajo."})

        self.history.extend(run_history[history_start:])
        self.run_count += 1
        emit("Agente", "Terminé el ciclo de corrección. Revisa el feedback del verificador.")
