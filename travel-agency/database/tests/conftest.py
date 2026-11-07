from collections.abc import Generator

import duckdb
import pytest

from database.seed import FIXTURES_DIR
from database.semantic_layer import open_db, schema


@pytest.fixture(scope="session")
def con() -> Generator[duckdb.DuckDBPyConnection]:
    """Una sola base en memoria para todos los tests, sobre las filas a mano (`fixtures/`): ahí cuadran los CHECKS."""
    connection = open_db(FIXTURES_DIR)
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def schema_text(con: duckdb.DuckDBPyConnection) -> str:
    """El esquema generado, calculado una sola vez: hace ~200 consultas sobre vistas anidadas (~4 s)."""
    return schema(con)
