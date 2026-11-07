from collections.abc import Generator

import duckdb
import pytest

from database.semantic_layer import open_db


@pytest.fixture(scope="session")
def con() -> Generator[duckdb.DuckDBPyConnection]:
    """La capa semántica en memoria, una vez para todos los tests: el validador no deja modificarla."""
    connection = open_db()
    yield connection
    connection.close()
