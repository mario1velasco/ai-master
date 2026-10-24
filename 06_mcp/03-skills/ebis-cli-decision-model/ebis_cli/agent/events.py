"""Eventos tipados entre el runtime y la interfaz Textual."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentEvent:
    speaker: str
    message: str
    progress: float | None = None
    details: dict[str, Any] = field(default_factory=dict)
    collapsed: bool = False
