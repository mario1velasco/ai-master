"""Ollama falso para los tests: responde como /api/chat y guarda cada petición."""

import copy
from dataclasses import dataclass, field
from typing import Any


def sql_answer(*queries: str) -> dict[str, Any]:
    """Respuesta en la que el modelo pide la tool de SQL, una vez por consulta."""
    calls = [{"function": {"name": "run_sql", "arguments": {"query": q}}} for q in queries]
    return {"role": "assistant", "content": "", "tool_calls": calls}


def text_answer(text: str) -> dict[str, Any]:
    """Respuesta en la que el modelo escribe texto y no pide ninguna tool."""
    return {"role": "assistant", "content": text}


@dataclass(slots=True)
class FakeResponse:
    status_code: int
    body: dict[str, Any]
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.body


@dataclass(slots=True)
class FakeOllama:
    """Devuelve en orden los mensajes de `answers`, con la forma de /api/chat, y guarda lo que se le envía.

    Una respuesta que ya es un `FakeResponse` (p. ej. un 404) se devuelve tal cual.
    """

    answers: list[dict[str, Any] | FakeResponse] = field(default_factory=list)
    requests: list[dict[str, Any]] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)

    def post(self, url: str, json: dict[str, Any], timeout: float) -> FakeResponse:
        self.urls.append(url)
        # Copia: el requests.post real serializa la petición en el momento; el bucle sigue añadiendo mensajes
        self.requests.append(copy.deepcopy(json))
        message = self.answers[len(self.requests) - 1]
        if isinstance(message, FakeResponse):
            return message
        return FakeResponse(
            status_code=200,
            body={
                "model": json["model"],
                "created_at": "2026-11-08T10:00:00Z",
                "message": message,
                "done": True,
                "done_reason": "stop",
                "total_duration": 2_500_000_000,
                "load_duration": 100_000_000,
                "prompt_eval_count": 2400,
                "prompt_eval_duration": 1_200_000_000,
                "eval_count": 40,
                "eval_duration": 1_000_000_000,
            },
        )
