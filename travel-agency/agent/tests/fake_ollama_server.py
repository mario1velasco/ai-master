"""Ollama falso para los tests del agente: responde como /api/chat y guarda cada petición.

Hablan con él dos clientes, cada uno con su guion de respuestas: el agente llega por `httpx` (`ChatOllama`) y
`text2sql` por `requests.post`. Así cada test dice qué responde «el modelo» en cada papel, sin tocar nada interno de
los paquetes.
"""

import copy
import json
from dataclasses import dataclass, field
from typing import Any

import httpx

AGENT_TOOL = "query_db"


def query_db_answer(*questions: str) -> dict[str, Any]:
    """Respuesta en la que el modelo del agente pide `query_db`, una vez por pregunta."""
    calls = [{"function": {"name": AGENT_TOOL, "arguments": {"question": q}}} for q in questions]
    return {"role": "assistant", "content": "", "tool_calls": calls}


def sql_answer(*queries: str) -> dict[str, Any]:
    """Respuesta en la que el modelo de `text2sql` pide `run_sql`, una vez por consulta."""
    calls = [{"function": {"name": "run_sql", "arguments": {"query": q}}} for q in queries]
    return {"role": "assistant", "content": "", "tool_calls": calls}


def text_answer(text: str) -> dict[str, Any]:
    """Respuesta en la que el modelo escribe texto y no pide ninguna tool."""
    return {"role": "assistant", "content": text}


def _body(model: str, message: dict[str, Any]) -> dict[str, Any]:
    """El JSON final de /api/chat, con los tiempos de Ollama (en ns)."""
    return {
        "model": model,
        "created_at": "2026-11-14T10:00:00Z",
        "message": message,
        "done": True,
        "done_reason": "stop",
        "total_duration": 2_500_000_000,
        "load_duration": 100_000_000,
        "prompt_eval_count": 1200,
        "prompt_eval_duration": 1_200_000_000,
        "eval_count": 40,
        "eval_duration": 1_000_000_000,
    }


@dataclass(slots=True)
class FakeResponse:
    """Lo que devuelve `requests.post` (solo lo que lee `text2sql`)."""

    status_code: int
    body: dict[str, Any]
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.body


@dataclass(slots=True)
class FakeOllamaServer:
    """Devuelve en orden las respuestas del guion de cada papel y guarda las peticiones que recibe."""

    agent_answers: list[dict[str, Any]] = field(default_factory=list)
    text2sql_answers: list[dict[str, Any]] = field(default_factory=list)
    agent_requests: list[dict[str, Any]] = field(default_factory=list)
    text2sql_requests: list[dict[str, Any]] = field(default_factory=list)
    agent_urls: list[str] = field(default_factory=list)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Sustituye a `httpx.HTTPTransport.handle_request`: el camino de `ChatOllama`."""
        payload = json.loads(request.content)
        self.agent_urls.append(str(request.url))
        self.agent_requests.append(payload)
        message = self.agent_answers[len(self.agent_requests) - 1]
        # ChatOllama pide streaming: una sola línea NDJSON con done = true es una respuesta completa
        line = json.dumps(_body(payload["model"], message)) + "\n"
        return httpx.Response(200, content=line.encode(), headers={"Content-Type": "application/x-ndjson"})

    def post(self, url: str, json: dict[str, Any], timeout: float) -> FakeResponse:
        """Sustituye a `requests.post`: el camino de `text2sql`."""
        # Copia: el requests.post real serializa la petición en el momento; el bucle sigue añadiendo mensajes
        self.text2sql_requests.append(copy.deepcopy(json))
        message = self.text2sql_answers[len(self.text2sql_requests) - 1]
        return FakeResponse(status_code=200, body=_body(json["model"], message))
