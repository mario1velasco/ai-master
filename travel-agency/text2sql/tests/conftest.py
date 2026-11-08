from collections.abc import Generator, Iterator
from pathlib import Path

import duckdb
import pytest
from fake_ollama import FakeOllama

from database.seed import FIXTURES_DIR
from database.semantic_layer import open_db
from telemetry import close_log_files, configure, get_config


@pytest.fixture(scope="session")
def con() -> Generator[duckdb.DuckDBPyConnection]:
    """La capa semántica sobre las filas a mano (`fixtures/`), una vez para todos los tests: cifras conocidas."""
    connection = open_db(FIXTURES_DIR)
    yield connection
    connection.close()


@pytest.fixture(autouse=True)
def log_dir(tmp_path: Path) -> Iterator[Path]:
    """Cada test escribe su telemetría en su carpeta temporal, en modo estricto (como en `telemetry/tests`)."""
    previous = get_config()
    configure(log_dir=tmp_path, environment="test", strict=True)
    yield tmp_path
    close_log_files()
    configure(log_dir=previous.log_dir, environment=previous.environment, strict=previous.strict)


@pytest.fixture
def fake_ollama(monkeypatch: pytest.MonkeyPatch) -> FakeOllama:
    """Sustituye el `requests.post` del cliente de Ollama y fija la configuración (nunca el .env real)."""
    fake = FakeOllama()
    monkeypatch.setattr("text2sql.ollama.requests.post", fake.post)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("TEXT2SQL_MODEL", "qwen3:4b-instruct")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "8192")
    monkeypatch.setenv("OLLAMA_KEEP_ALIVE", "30m")
    return fake
