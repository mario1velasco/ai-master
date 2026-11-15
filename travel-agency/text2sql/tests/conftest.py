from collections.abc import Generator, Iterator
from pathlib import Path

import duckdb
import pytest
from fake_ollama import FakeOllama

from database.seed import FIXTURES_DIR
from database.semantic_layer import DATA_DIR, open_db
from telemetry import close_log_files, configure, get_config


@pytest.fixture(scope="session")
def con() -> Generator[duckdb.DuckDBPyConnection]:
    """La capa semántica sobre las filas a mano (`fixtures/`), una vez para todos los tests: cifras conocidas."""
    connection = open_db(FIXTURES_DIR)
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def data_con() -> Generator[duckdb.DuckDBPyConnection]:
    """La capa semántica sobre `data/`, los datos con los que se mide (TRAVEL-007), una vez para todos los tests."""
    connection = open_db(DATA_DIR)
    yield connection
    connection.close()


@pytest.fixture(scope="session", autouse=True)
def session_schema_cache(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Los esquemas guardados van a una carpeta temporal de la sesión: nunca al repo, y se generan una vez."""
    with pytest.MonkeyPatch.context() as mp:
        path = tmp_path_factory.mktemp("schema_cache")
        mp.setattr("database.schema.SCHEMA_CACHE_DIR", path)
        yield path


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
