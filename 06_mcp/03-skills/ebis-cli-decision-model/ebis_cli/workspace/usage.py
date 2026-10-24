"""Acumula tokens OpenAI y estima su coste con las tarifas de routing-llm.json."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..settings import (
    JEV_INPUT_USD_PER_MILLION,
    JEV_OUTPUT_USD_PER_MILLION,
    USAGE_FILE,
)


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _has_field(value: Any, name: str) -> bool:
    if isinstance(value, dict):
        return name in value and value[name] is not None
    return value is not None and getattr(value, name, None) is not None


def _number(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _empty_bucket() -> dict[str, Any]:
    return {
        "openai_calls": 0,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "reasoning_usage_calls": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _empty_jev_bucket() -> dict[str, Any]:
    return {
        "calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "unreported_usage_calls": 0,
        "calls_by_purpose": {"choice": 0, "routing": 0, "other": 0},
    }


def _new_stats() -> dict[str, Any]:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "schema_version": 1,
        "created_at": now,
        "updated_at": now,
        "openai": _empty_bucket(),
        "by_mode": {"decision_on": _empty_bucket(), "decision_off": _empty_bucket()},
        "jev": _empty_jev_bucket(),
        "jev_by_mode": {
            "decision_on": _empty_jev_bucket(),
            "decision_off": _empty_jev_bucket(),
        },
        "by_model": {},
        "by_tier": {},
        "decision": {
            "choice_steps": 0,
            "typesafe_choices": 0,
            "tool_selections": 0,
            "context_selections": 0,
            "final_selections": 0,
            "automatic_selections": 0,
            "tool_executions": 0,
            "tool_executions_after_choice": 0,
            "direct_tool_executions": 0,
            "successful_routes": 0,
            "cheaper_routes": 0,
            "estimated_routing_savings_usd": 0.0,
            "openai_calls_avoided": 0,
        },
        "unpriced_calls": 0,
    }


class UsageTracker:
    """Guarda estadísticas del workspace y compara el routing con su nivel caro."""

    def __init__(
        self,
        routing_config: dict[str, Any],
        path: Path = USAGE_FILE,
    ) -> None:
        self.path = path
        self.conversations_dir = path.parent / "conversations"
        self.models: dict[str, dict[str, Any]] = routing_config.get("models", {})
        baseline = routing_config.get("savings_baseline", "expensive_reasoning")
        self.baseline_tier = baseline if baseline in self.models else None
        self.conversation_id: str | None = None
        self.conversation_data: dict[str, Any] | None = None
        self.conversation_has_untracked_history = False
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = None
        return self._normalize(data)

    @staticmethod
    def _normalize(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            return _new_stats()
        defaults = _new_stats()
        for key, value in defaults.items():
            data.setdefault(key, value)
        for section in (
            "openai", "by_mode", "jev", "jev_by_mode", "by_model", "by_tier", "decision"
        ):
            if not isinstance(data.get(section), dict):
                data[section] = defaults[section]
        for key, value in defaults["openai"].items():
            data["openai"].setdefault(key, value)
        for mode, bucket in defaults["by_mode"].items():
            if not isinstance(data["by_mode"].get(mode), dict):
                data["by_mode"][mode] = bucket.copy()
            for key, value in bucket.items():
                data["by_mode"][mode].setdefault(key, value)
        for key, value in defaults["jev"].items():
            if key == "calls_by_purpose":
                if not isinstance(data["jev"].get(key), dict):
                    data["jev"][key] = value.copy()
                for purpose, count in value.items():
                    data["jev"][key].setdefault(purpose, count)
            else:
                data["jev"].setdefault(key, value)
        for mode, bucket in defaults["jev_by_mode"].items():
            if not isinstance(data["jev_by_mode"].get(mode), dict):
                data["jev_by_mode"][mode] = bucket.copy()
            for key, value in bucket.items():
                if key == "calls_by_purpose":
                    if not isinstance(data["jev_by_mode"][mode].get(key), dict):
                        data["jev_by_mode"][mode][key] = value.copy()
                    for purpose, count in value.items():
                        data["jev_by_mode"][mode][key].setdefault(purpose, count)
                else:
                    data["jev_by_mode"][mode].setdefault(key, value)
        for key, value in defaults["decision"].items():
            data["decision"].setdefault(key, value)
        for section in ("by_model", "by_tier"):
            for name, bucket in list(data[section].items()):
                if not isinstance(bucket, dict):
                    bucket = _empty_bucket()
                    data[section][name] = bucket
                for key, value in defaults["openai"].items():
                    bucket.setdefault(key, value)
        return data

    def set_conversation(self, conversation_id: str | None) -> None:
        """Selecciona dónde guardar y leer las métricas de la conversación activa."""
        if conversation_id is None:
            self.conversation_id = None
            self.conversation_data = None
            self.conversation_has_untracked_history = False
            return
        try:
            normalized_id = uuid.UUID(hex=conversation_id).hex
        except (ValueError, AttributeError):
            self.conversation_id = None
            self.conversation_data = None
            self.conversation_has_untracked_history = False
            return

        self.conversation_id = normalized_id
        path = self.conversations_dir / f"{normalized_id}.json"
        try:
            conversation = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            conversation = {}
        saved_stats = (
            conversation.get("usage_stats") if isinstance(conversation, dict) else None
        )
        self.conversation_data = self._normalize(saved_stats)
        events = conversation.get("events", []) if isinstance(conversation, dict) else []
        had_user_prompt = isinstance(events, list) and any(
            isinstance(event, dict) and event.get("speaker") == "Tú"
            for event in events
        )
        self.conversation_has_untracked_history = (
            isinstance(conversation, dict)
            and saved_stats is None
            and bool(had_user_prompt or conversation.get("agent_history"))
        )
        if self.conversation_has_untracked_history:
            self.conversation_data["historical_usage_unavailable"] = True

    def _scopes(self) -> tuple[dict[str, Any], ...]:
        if self.conversation_data is None:
            return (self.data,)
        return self.data, self.conversation_data

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        temporary = self.path.with_name(f"{self.path.stem}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary, self.path)

        if self.conversation_id is None or self.conversation_data is None:
            return
        conversation_path = self.conversations_dir / f"{self.conversation_id}.json"
        try:
            conversation = json.loads(conversation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(conversation, dict):
            return
        self.conversation_data["updated_at"] = self.data["updated_at"]
        conversation["usage_stats"] = self.conversation_data
        conversation["updated_at"] = self.data["updated_at"]
        temporary_conversation = conversation_path.with_name(
            f"{conversation_path.stem}.{uuid.uuid4().hex}.tmp"
        )
        temporary_conversation.write_text(
            json.dumps(conversation, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary_conversation, conversation_path)

    def record_choice(self, action: str, used_typesafe: bool) -> None:
        for data in self._scopes():
            decision = data["decision"]
            decision["choice_steps"] += 1
            if used_typesafe:
                decision["typesafe_choices"] += 1
            if action == "tool":
                decision["tool_selections"] += 1
            elif action == "build_context":
                decision["context_selections"] += 1
            elif action == "final_answer":
                decision["final_selections"] += 1
            else:
                decision["automatic_selections"] += 1
        self._save()

    def record_tool_execution(
        self, *, selected_by_choice: bool, direct: bool = False
    ) -> None:
        for data in self._scopes():
            decision = data["decision"]
            decision["tool_executions"] += 1
            if selected_by_choice:
                decision["tool_executions_after_choice"] += 1
            if direct:
                decision["direct_tool_executions"] += 1
                decision["openai_calls_avoided"] += 1
        self._save()

    def record_jev_usage(
        self,
        *,
        input_tokens: int | None,
        output_tokens: int | None,
        purpose: str,
        decision_enabled: bool,
    ) -> None:
        mode = "decision_on" if decision_enabled else "decision_off"
        purpose = purpose if purpose in {"choice", "routing"} else "other"
        input_count = _number(input_tokens)
        output_count = _number(output_tokens)
        input_cost = input_count * JEV_INPUT_USD_PER_MILLION / 1_000_000
        output_cost = output_count * JEV_OUTPUT_USD_PER_MILLION / 1_000_000

        for data in self._scopes():
            for bucket in (data["jev"], data["jev_by_mode"][mode]):
                bucket["calls"] += 1
                bucket["calls_by_purpose"][purpose] += 1
                bucket["input_tokens"] += input_count
                bucket["output_tokens"] += output_count
                bucket["total_tokens"] += input_count + output_count
                bucket["estimated_cost_usd"] += input_cost + output_cost
                if input_tokens is None:
                    bucket["unreported_usage_calls"] += 1
        self._save()

    @staticmethod
    def _usage_counts(usage: Any) -> dict[str, int]:
        input_details = _field(usage, "input_tokens_details", {}) or {}
        output_details = _field(usage, "output_tokens_details", None)
        input_tokens = _number(_field(usage, "input_tokens", 0))
        output_tokens = _number(_field(usage, "output_tokens", 0))
        reasoning_was_reported = _has_field(output_details, "reasoning_tokens")
        reasoning_tokens = min(
            output_tokens,
            _number(_field(output_details, "reasoning_tokens", 0)),
        )
        cached_tokens = min(
            input_tokens, _number(_field(input_details, "cached_tokens", 0))
        )
        cache_write_tokens = min(
            max(0, input_tokens - cached_tokens),
            _number(_field(input_details, "cache_write_tokens", 0)),
        )
        total_tokens = _number(
            _field(usage, "total_tokens", input_tokens + output_tokens)
        )
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens
        return {
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_tokens,
            "cache_write_tokens": cache_write_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "reasoning_usage_calls": int(reasoning_was_reported),
            "total_tokens": total_tokens,
        }

    def _cost(self, model: str, usage: dict[str, int]) -> float | None:
        entry = next(
            (item for item in self.models.values() if item.get("model") == model), None
        )
        pricing = entry.get("pricing") if isinstance(entry, dict) else None
        if not isinstance(pricing, dict):
            return None
        try:
            input_rate = float(pricing["input_per_million"])
            cached_rate = float(pricing.get("cached_input_per_million", input_rate))
            write_rate = float(pricing.get("cache_write_per_million", input_rate * 1.25))
            output_rate = float(pricing["output_per_million"])
        except (KeyError, TypeError, ValueError):
            return None
        ordinary_tokens = max(
            0,
            usage["input_tokens"]
            - usage["cached_input_tokens"]
            - usage["cache_write_tokens"],
        )
        input_cost = (
            ordinary_tokens * input_rate
            + usage["cached_input_tokens"] * cached_rate
            + usage["cache_write_tokens"] * write_rate
        ) / 1_000_000
        output_cost = usage["output_tokens"] * output_rate / 1_000_000
        return input_cost + output_cost

    def record_request(
        self,
        *,
        model: str,
        tier: str,
        usage: Any,
        route_used_typesafe: bool,
        decision_enabled: bool,
    ) -> None:
        counts = self._usage_counts(usage)
        cost = self._cost(model, counts) if usage is not None else None
        mode = "decision_on" if decision_enabled else "decision_off"
        baseline_model = (
            self.models[self.baseline_tier].get("model", "")
            if self.baseline_tier
            else ""
        )
        baseline_cost = self._cost(baseline_model, counts) if baseline_model else None
        for data in self._scopes():
            for bucket in (
                data["openai"],
                data["by_mode"].setdefault(mode, _empty_bucket()),
                data["by_model"].setdefault(model, _empty_bucket()),
                data["by_tier"].setdefault(tier, _empty_bucket()),
            ):
                bucket["openai_calls"] += 1
                for key, value in counts.items():
                    bucket[key] = bucket.get(key, 0) + value
                if cost is not None:
                    bucket["estimated_cost_usd"] += cost
            if cost is None:
                data["unpriced_calls"] += 1

            decision = data["decision"]
            if route_used_typesafe:
                decision["successful_routes"] += 1
                if (
                    cost is not None
                    and baseline_cost is not None
                    and baseline_cost > cost
                ):
                    decision["cheaper_routes"] += 1
                    decision["estimated_routing_savings_usd"] += baseline_cost - cost
        self._save()

    def report(
        self, *, decision_enabled: bool, scope: str = "workspace"
    ) -> str:
        if scope not in {"workspace", "conversation"}:
            raise ValueError("scope debe ser 'workspace' o 'conversation'.")
        if scope == "conversation":
            data = self.conversation_data or _new_stats()
        else:
            data = self.data
        overall = data["openai"]
        jev = data["jev"]
        decision = data["decision"]
        jev_cost = jev["estimated_cost_usd"]
        routing_savings = decision["estimated_routing_savings_usd"]
        net_savings = routing_savings - jev_cost

        sections = [
            f"{'RESUMEN DE LA CONVERSACIÓN ACTUAL' if scope == 'conversation' else 'RESUMEN DEL WORKSPACE'}\n"
            f"Decision Model ahora: {'ACTIVADO' if decision_enabled else 'DESACTIVADO'}\n"
            f"OpenAI: {overall['openai_calls']} llamadas · {overall['total_tokens']:,} tokens · "
            f"${overall['estimated_cost_usd']:.8f}\n"
            f"Jev: {jev['calls']} decisiones · {jev['total_tokens']:,} tokens · "
            f"${jev_cost:.8f}\n"
            f"Coste total estimado: ${overall['estimated_cost_usd'] + jev_cost:.8f}",
            "OPENAI · USO Y COSTE\n"
            f"Llamadas: {overall['openai_calls']}\n"
            f"Entrada: {overall['input_tokens']:,} tokens "
            f"({overall['cached_input_tokens']:,} cacheados; "
            f"{overall['cache_write_tokens']:,} escrituras de caché)\n"
            f"Salida: {overall['output_tokens']:,} tokens "
            f"(razonamiento: {overall['reasoning_tokens']:,}; "
            f"otros: {max(0, overall['output_tokens'] - overall['reasoning_tokens']):,})\n"
            f"Desglose de razonamiento recibido en "
            f"{overall['reasoning_usage_calls']}/{overall['openai_calls']} llamadas\n"
            f"Total: {overall['total_tokens']:,} tokens\n"
            f"Coste estimado: ${overall['estimated_cost_usd']:.8f}",
            "JEV / TYPESAFE · USO Y COSTE\n"
            f"Decisiones: {jev['calls']} · Choice {jev['calls_by_purpose']['choice']} · "
            f"Routing {jev['calls_by_purpose']['routing']}\n"
            f"Entrada: {jev['input_tokens']:,} tokens\n"
            f"Salida: {jev['output_tokens']:,} tokens\n"
            f"Total: {jev['total_tokens']:,} tokens\n"
            f"Coste estimado: ${jev_cost:.8f}\n"
            f"Tarifa aplicada: ${JEV_INPUT_USD_PER_MILLION:g}/millón de tokens de entrada; "
            f"salida ${JEV_OUTPUT_USD_PER_MILLION:g}/millón",
            "DECISION MODEL · ACTIVIDAD\n"
            f"Choice: {decision['choice_steps']} decisiones; "
            f"{decision['typesafe_choices']} resueltas por Jev\n"
            f"Tools: {decision['tool_selections']} preseleccionadas; "
            f"{decision['tool_executions_after_choice']} ejecutadas\n"
            f"Tools directas sin request OpenAI: {decision['direct_tool_executions']}\n"
            f"Requests OpenAI evitadas: {decision['openai_calls_avoided']}\n"
            f"Routing: {decision['successful_routes']} decisiones Jev; "
            f"{decision['cheaper_routes']} llamadas más baratas que "
                f"'{self.baseline_tier or 'expensive_reasoning'}'",
            "AHORRO ESTIMADO\n"
            f"Ahorro bruto por routing: ${routing_savings:.8f}\n"
            f"Coste estimado de Jev: -${jev_cost:.8f}\n"
            f"Ahorro neto aproximado: ${net_savings:.8f}",
        ]

        for model, bucket in sorted(data["by_model"].items()):
            sections.append(
                f"MODELO · {model}\n"
                f"Llamadas: {bucket['openai_calls']}\n"
                f"Entrada: {bucket['input_tokens']:,} · Salida: {bucket['output_tokens']:,} "
                f"(razonamiento: {bucket['reasoning_tokens']:,})\n"
                f"Coste estimado: ${bucket['estimated_cost_usd']:.8f}"
            )

        for tier, bucket in sorted(data["by_tier"].items()):
            entry = self.models.get(tier, {})
            model = entry.get("model", "modelo desconocido")
            effort = entry.get("reasoning_effort", "no registrado")
            sections.append(
                f"NIVEL · {tier}\n"
                f"Modelo: {model} · reasoning.effort={effort}\n"
                f"Llamadas: {bucket['openai_calls']} · Entrada: {bucket['input_tokens']:,} · "
                f"Salida: {bucket['output_tokens']:,} · "
                f"Razonamiento: {bucket['reasoning_tokens']:,}\n"
                f"Coste estimado: ${bucket['estimated_cost_usd']:.8f}"
            )

        for mode, label in (("decision_on", "ON"), ("decision_off", "OFF")):
            openai_mode = data["by_mode"].get(mode, _empty_bucket())
            jev_mode = data["jev_by_mode"].get(mode, _empty_jev_bucket())
            sections.append(
                f"MODO DECISION {label}\n"
                f"OpenAI: {openai_mode['openai_calls']} llamadas · "
                f"{openai_mode['total_tokens']:,} tokens · "
                f"${openai_mode['estimated_cost_usd']:.8f}\n"
                f"Entrada: {openai_mode['input_tokens']:,} · Salida: "
                f"{openai_mode['output_tokens']:,} · Razonamiento: "
                f"{openai_mode['reasoning_tokens']:,}\n"
                f"Jev: {jev_mode['calls']} decisiones · "
                f"{jev_mode['total_tokens']:,} tokens · "
                f"${jev_mode['estimated_cost_usd']:.8f}\n"
                f"Coste conjunto: ${openai_mode['estimated_cost_usd'] + jev_mode['estimated_cost_usd']:.8f}"
            )

        notes = [
            "Costes aproximados en USD: OpenAI según routing-llm.json y Jev según settings.py.",
            "El ahorro bruto compara los mismos tokens con el tier de referencia.",
            "El ahorro neto resta el coste medido de Jev. Las tools directas indican requests evitadas, sin estimar tokens hipotéticos.",
            "No se incluyen costes de servicios MCP.",
        ]
        if data["unpriced_calls"]:
            notes.append(
                f"{data['unpriced_calls']} llamadas OpenAI no tienen tarifa configurada."
            )
        if jev["unreported_usage_calls"]:
            notes.append(
                f"No se recibió usage de Jev en {jev['unreported_usage_calls']} respuestas; "
                "esas llamadas se cuentan, pero no se pueden costear."
            )
        reasoning_unreported = max(
            0, overall["openai_calls"] - overall["reasoning_usage_calls"]
        )
        if reasoning_unreported:
            notes.append(
                f"El desglose de reasoning_tokens no está disponible en "
                f"{reasoning_unreported} llamadas; puede tratarse de registros anteriores "
                "a este campo o de respuestas que no incluyeron el desglose."
            )
        if scope == "conversation" and data.get("historical_usage_unavailable"):
            notes.append(
                "Esta conversación ya tenía actividad antes del registro individual; "
                "su uso anterior no se puede reconstruir."
            )
        sections.append("NOTAS\n" + "\n".join(f"• {note}" for note in notes))
        return "\n\n".join(sections)
