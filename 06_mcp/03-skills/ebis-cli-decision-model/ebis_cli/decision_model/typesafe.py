"""Adaptador pequeño entre el harness asíncrono y el SDK TypeSafe."""

import asyncio
import os
from dataclasses import dataclass
from typing import Any

from typesafe_sdk import Choice, TypeSafeClient


@dataclass(frozen=True)
class TypeSafeUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    model: str | None = None


@dataclass(frozen=True)
class TypeSafeDecision:
    choice: str
    usage: TypeSafeUsage


def typesafe_is_configured() -> bool:
    return bool(os.getenv("TYPESAFE_API_KEY", "").strip())


def _token_count(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _choose_sync(
    state: dict[str, Any], instructions: str, criteria: dict[str, str]
) -> TypeSafeDecision:
    with TypeSafeClient() as client:
        result = client.system_one(
            state=state,
            questions={
                "decision": Choice(instructions=instructions, criteria=criteria),
            },
        )
    usage = getattr(result, "usage", None)
    return TypeSafeDecision(
        choice=result.answers["decision"].choice,
        usage=TypeSafeUsage(
            input_tokens=_token_count(_field(usage, "input_tokens")),
            output_tokens=_token_count(_field(usage, "output_tokens")),
            model=getattr(result, "model", None),
        ),
    )


async def choose(
    state: dict[str, Any], instructions: str, criteria: dict[str, str]
) -> TypeSafeDecision:
    """Ejecuta una decisión Jev sin bloquear el event loop de Textual."""
    return await asyncio.to_thread(_choose_sync, state, instructions, criteria)
