"""Lo que el agente envía a Ollama y cómo responde cuando Ollama falla (ticket TRAVEL-006).

El Ollama falso (`ollama`) guarda cada petición del agente; los de Ollama caído usan `httpx` de verdad contra un
puerto donde no escucha nadie.
"""

from datetime import UTC, datetime

import duckdb
import pytest
from fake_ollama_server import FakeOllamaServer, text_answer

from agent import respond
from contracts.metrics import BaseMetrics, Component, Status
from telemetry import events_path, read_events
from text2sql import ComponentError

QUESTION = "¿Cuántas reservas tiene C-001?"


def test_request_uses_config(
    con: duckdb.DuckDBPyConnection, ollama: FakeOllamaServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Valores distintos de los de por defecto: así se ve que salen del entorno y no del código
    monkeypatch.setenv("AGENT_MODEL", "qwen3:1.7b")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "4096")
    monkeypatch.setenv("OLLAMA_KEEP_ALIVE", "10m")
    ollama.agent_answers = [text_answer("No tengo ese dato.")]

    respond(QUESTION, con=con)

    assert ollama.agent_urls == ["http://localhost:11434/api/chat"]
    [request] = ollama.agent_requests
    assert request["model"] == "qwen3:1.7b"
    assert request["options"]["num_ctx"] == 4096
    assert request["options"]["temperature"] == 0
    assert request["keep_alive"] == "10m"
    assert request["think"] is False  # sin modo razonamiento


def agent_events() -> list[BaseMetrics]:
    """Las métricas de los eventos que ha escrito el agente hoy (el log va a la carpeta temporal del test)."""
    return [event.metrics for event in read_events(events_path(Component.agent, datetime.now(UTC).date()))]


def test_ollama_down_raises_coded_error(con: duckdb.DuckDBPyConnection, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")  # Ollama de verdad (httpx real), nadie escucha

    with pytest.raises(ComponentError) as error:
        respond(QUESTION, con=con)

    assert error.value.code == "ollama_unavailable"
    assert "No hay respuesta de Ollama en http://127.0.0.1:1" in error.value.message
    assert [m.status for m in agent_events()] == [Status.error]
