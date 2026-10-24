"""Choice de Jev para elegir la próxima acción discreta del agente."""

from dataclasses import dataclass
from typing import Any

from ..settings import DECISION_MODEL_ENABLED_DEFAULT
from .typesafe import TypeSafeUsage, choose, typesafe_is_configured


BUILD_CONTEXT = "build_context"
FINAL_ANSWER = "final_answer"
AUTO_TOOLS = "automatic_tool_selection"


@dataclass(frozen=True)
class ActionChoice:
    action: str
    tool_name: str | None = None
    reason: str = ""
    used_typesafe: bool = False
    jev_usage: TypeSafeUsage | None = None
    failed: bool = False


class ActionChooser:
    """Elige entre construir contexto, contestar o habilitar una tool concreta."""

    def __init__(self, *, enabled: bool = DECISION_MODEL_ENABLED_DEFAULT) -> None:
        self.enabled = enabled

    async def choose_next(
        self,
        *,
        goal: str,
        history: list[Any],
        tools: list[dict[str, Any]],
        step: int,
        allow_context: bool,
    ) -> ActionChoice:
        if not self.enabled:
            return ActionChoice(
                AUTO_TOOLS,
                reason="Decision Model desactivado; se habilita la seleccion automatica de tools.",
            )
        if not typesafe_is_configured():
            return ActionChoice(
                AUTO_TOOLS,
                reason="TYPESAFE_API_KEY no está configurada; se activa function calling automático.",
                failed=True,
            )

        criteria: dict[str, str] = {
            FINAL_ANSWER: "Ya hay información suficiente para responder al usuario sin otra tool.",
        }
        if allow_context:
            criteria[BUILD_CONTEXT] = (
                "El agente necesita crear contexto breve, separar hechos de dudas o formular "
                "una auto-pregunta antes de actuar."
            )

        tool_names: dict[str, str] = {}
        for tool in tools:
            name = tool["name"]
            choice_key = f"tool__{name}"
            tool_names[choice_key] = name
            description = tool.get("description") or "Sin descripción disponible."
            parameters = tool.get("parameters", {})
            properties = parameters.get("properties", {}) if isinstance(parameters, dict) else None
            required = parameters.get("required", []) if isinstance(parameters, dict) else None
            if (
                isinstance(properties, dict)
                and not properties
                and isinstance(required, list)
                and not required
            ):
                description += " No requiere argumentos; Jev puede ejecutarla directamente sin una llamada OpenAI."
            criteria[choice_key] = f"Invoca la tool {name}: {description[:300]}"

        state = {
            "goal": goal,
            "step": step,
            "recent_history": self._history_excerpt(history),
            "available_actions": [
                {"choice": key, "meaning": value} for key, value in criteria.items()
            ],
            "instruction": (
                "Elige una sola acción para la siguiente iteración. La acción determina "
                "el contenido y las tools que recibirá el siguiente prompt del LLM."
            ),
        }
        instructions = (
            "Si una tool sin argumentos requeridos resuelve el objetivo inmediato, "
            "priorizala para ejecutarla sin otra request OpenAI. "
            "Selecciona la mejor acción inmediata para avanzar el objetivo, no una "
            "estrategia para toda la conversación. Elige una tool solo si su descripción "
            "indica claramente que hace falta ahora. Elige build_context para convertir "
            "resultados dispersos en hechos y preguntas antes de la siguiente llamada al "
            "LLM. Elige final_answer solo cuando ya puedas responder con evidencia. "
            "No elijas una tool solo porque está disponible."
        )
        try:
            result = await choose(state, instructions, criteria)
        except Exception as error:
            return ActionChoice(
                AUTO_TOOLS,
                reason=f"Jev Choice no respondió; fallback automático: {error}",
                failed=True,
            )

        selected = result.choice
        if selected == FINAL_ANSWER:
            return ActionChoice(
                FINAL_ANSWER, reason=selected, used_typesafe=True, jev_usage=result.usage
            )
        if selected == BUILD_CONTEXT and allow_context:
            return ActionChoice(
                BUILD_CONTEXT, reason=selected, used_typesafe=True, jev_usage=result.usage
            )
        if selected in tool_names:
            return ActionChoice(
                "tool",
                tool_name=tool_names[selected],
                reason=selected,
                used_typesafe=True,
                jev_usage=result.usage,
            )
        return ActionChoice(
            AUTO_TOOLS,
            reason=f"Jev devolvió una opción desconocida ({selected}); fallback automático.",
            jev_usage=result.usage,
            failed=True,
        )

    @staticmethod
    def _history_excerpt(history: list[Any], limit: int = 6_000) -> str:
        parts: list[str] = []
        for item in history[-12:]:
            if isinstance(item, dict):
                role = item.get("role") or item.get("type", "item")
                content = item.get("content") or item.get("output") or ""
                if item.get("type") == "function_call":
                    content = f"{item.get('name', '')} {item.get('arguments', '')}"
            else:
                role = getattr(item, "role", getattr(item, "type", "item"))
                content = getattr(item, "content", "")
                if getattr(item, "type", None) == "function_call":
                    content = f"{getattr(item, 'name', '')} {getattr(item, 'arguments', '')}"
            if isinstance(content, list):
                content = " ".join(
                    str(block.get("text", "")) if isinstance(block, dict) else str(getattr(block, "text", ""))
                    for block in content
                )
            parts.append(f"{role}: {str(content)}")
        text = "\n".join(parts)
        return text[-limit:]
