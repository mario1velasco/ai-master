from collections.abc import Generator

import duckdb
import pytest

from database.seed import FIXTURES_DIR
from database.semantic_layer import open_db


@pytest.fixture(scope="session")
def con() -> Generator[duckdb.DuckDBPyConnection]:
    """La capa semántica sobre las filas a mano (`fixtures/`), una vez para todos los tests: cifras conocidas."""
    connection = open_db(FIXTURES_DIR)
    yield connection
    connection.close()
