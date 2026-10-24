"""Choice de Jev para enrutar cada llamada LLM a un modelo permitido."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..settings import DECISION_MODEL_ENABLED_DEFAULT, ROUTING_FILE
from .typesafe import TypeSafeUsage, choose, typesafe_is_configured


SUPPORTED_REASONING_EFFORTS = {
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
}
# Límites de compatibilidad comprobados para los modelos usados por el ejemplo.
MODEL_REASONING_EFFORTS = {
    "gpt-6-luna": {"none", "low", "medium", "high", "xhigh", "max"},
    "gpt-6-sol": {"none", "low", "medium", "high", "xhigh", "max"},
    "gpt-5.6-sol": {"none", "low", "medium", "high", "xhigh", "max"},
    "gpt-6-astra": {"low", "medium", "high", "xhigh", "max"},
    "gpt-6.1-sol": {"low", "medium", "high", "xhigh", "max"},
}


@dataclass(frozen=True)
class RouteChoice:
    model: str
    tier: str
    reasoning_effort: str = "medium"
    used_typesafe: bool = False
    reason: str = ""
    jev_usage: TypeSafeUsage | None = None
    failed: bool = False


class LLMRouter:
    """Carga la allowlist local y solicita a Jev un nivel para cada llamada."""

    def __init__(
        self,
        config_path: Path = ROUTING_FILE,
        *,
        enabled: bool = DECISION_MODEL_ENABLED_DEFAULT,
    ) -> None:
        self.config_path = config_path
        self.enabled = enabled
        self.config = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"No se pudo leer {self.config_path}: {error}") from error

        models = config.get("models") if isinstance(config, dict) else None
        if not isinstance(models, dict) or not models:
            raise ValueError("routing-llm.json necesita un objeto 'models' no vacío.")
        for tier, entry in models.items():
            if not isinstance(tier, str) or not isinstance(entry, dict):
                raise ValueError("Cada nivel de models debe ser un objeto con model y description.")
            if not isinstance(entry.get("model"), str) or not entry["model"].strip():
                raise ValueError(f"models.{tier}.model debe ser un nombre no vacío.")
            if not isinstance(entry.get("description"), str):
                raise ValueError(f"models.{tier}.description debe ser texto.")
            reasoning_effort = entry.get("reasoning_effort")
            if reasoning_effort not in SUPPORTED_REASONING_EFFORTS:
                allowed = ", ".join(sorted(SUPPORTED_REASONING_EFFORTS))
                raise ValueError(
                    f"models.{tier}.reasoning_effort debe ser uno de: {allowed}."
                )
            supported_efforts = MODEL_REASONING_EFFORTS.get(entry["model"])
            if supported_efforts is not None and reasoning_effort not in supported_efforts:
                allowed = ", ".join(sorted(supported_efforts))
                raise ValueError(
                    f"El modelo {entry['model']} no admite reasoning.effort="
                    f"{reasoning_effort}; valores documentados aquí: {allowed}."
                )
            pricing = entry.get("pricing")
            if pricing is not None:
                if not isinstance(pricing, dict):
                    raise ValueError(f"models.{tier}.pricing debe ser un objeto.")
                for key, value in pricing.items():
                    if not isinstance(value, (int, float)) or value < 0:
                        raise ValueError(f"models.{tier}.pricing.{key} debe ser un numero no negativo.")
        default_tier = config.get("default")
        if not isinstance(default_tier, str) or default_tier not in models:
            raise ValueError("'default' debe apuntar a una clave definida en 'models'.")
        baseline_tier = config.get("savings_baseline")
        if baseline_tier is not None and (
            not isinstance(baseline_tier, str) or baseline_tier not in models
        ):
            raise ValueError("'savings_baseline' debe apuntar a un nivel definido en 'models'.")
        return config

    async def route(self, *, goal: str, action: str, recent_context: str = "") -> RouteChoice:
        default_tier = self.config["default"]
        models = self.config["models"]
        default_entry = models[default_tier]
        if not self.enabled:
            return RouteChoice(
                model=default_entry["model"],
                tier=default_tier,
                reasoning_effort=default_entry["reasoning_effort"],
                reason="Decision Model desactivado; se usa el modelo predeterminado.",
            )
        if not typesafe_is_configured():
            return RouteChoice(
                model=default_entry["model"],
                tier=default_tier,
                reasoning_effort=default_entry["reasoning_effort"],
                reason="TYPESAFE_API_KEY no está configurada; se usa el modelo predeterminado.",
                failed=True,
            )

        criteria = {}
        for tier, entry in models.items():
            pricing = entry.get("pricing", {})
            rate_note = ""
            if isinstance(pricing, dict):
                rates = (
                    f"USD/MTok input ${pricing.get('input_per_million', '?')}, "
                    f"cached ${pricing.get('cached_input_per_million', '?')}, "
                    f"cache write ${pricing.get('cache_write_per_million', '?')}, "
                    f"output ${pricing.get('output_per_million', '?')}"
                )
                rate_note = f" ({rates})"
            criteria[tier] = (
                f"Modelo {entry['model']}; reasoning.effort="
                f"{entry['reasoning_effort']}{rate_note}. "
                f"Cuándo elegirlo: {entry['description']}"
            )
        state = {
            "goal": goal,
            "next_action": action,
            "recent_context": recent_context[-3_000:],
            "allowed_models": {
                tier: {
                    "model": entry["model"],
                    "reasoning_effort": entry["reasoning_effort"],
                }
                for tier, entry in models.items()
            },
        }
        instructions = (
            "Elige una sola combinación permitida de modelo y esfuerzo de razonamiento "
            "para esta llamada, no para toda la tarea. Minimiza coste y latencia sin "
            "sacrificar la probabilidad de completar bien la acción inmediata. "
            "Usa reasoning.effort=none para extracción literal, clasificación evidente, "
            "resumen directo o transformación determinista. Usa low cuando haya una "
            "inferencia corta, ambigüedad menor o una decisión sencilla. Usa medium "
            "para planificar varios pasos, seleccionar y combinar tools, depurar o "
            "comparar alternativas. Reserva el nivel expensive para problemas de alta "
            "complejidad, mucha incertidumbre o alto impacto que justifiquen su precio; "
            "elige reasoning.effort=high solo si medium probablemente sea insuficiente "
            "y la importancia de acertar justifique más coste y latencia. "
            "La longitud del prompt por sí sola no lo justifica. Lee cada descripción: "
            "effort=none significa que no se solicita razonamiento interno aunque el "
            "modelo sea capaz; low, medium y high sí permiten tokens de razonamiento. Devuelve "
            "solo una clave exacta de las opciones permitidas."
        )
        try:
            result = await choose(state, instructions, criteria)
        except Exception as error:
            return RouteChoice(
                model=default_entry["model"],
                tier=default_tier,
                reasoning_effort=default_entry["reasoning_effort"],
                reason=f"Jev Routing no respondió; modelo predeterminado: {error}",
                failed=True,
            )

        tier = result.choice
        if tier not in models:
            return RouteChoice(
                model=default_entry["model"],
                tier=default_tier,
                reasoning_effort=default_entry["reasoning_effort"],
                reason=f"Jev devolvió un nivel desconocido ({tier}); modelo predeterminado.",
                jev_usage=result.usage,
                failed=True,
            )
        return RouteChoice(
            model=models[tier]["model"],
            tier=tier,
            reasoning_effort=models[tier]["reasoning_effort"],
            used_typesafe=True,
            reason=f"{tier}; reasoning.effort={models[tier]['reasoning_effort']}",
            jev_usage=result.usage,
        )
