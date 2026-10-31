from collections.abc import Generator

import duckdb
import pytest

from database.semantic_layer import open_db, schema


@pytest.fixture(scope="session")
def con() -> Generator[duckdb.DuckDBPyConnection]:
    """Una sola base en memoria para todos los tests: se construye en milisegundos y nadie la modifica."""
    connection = open_db()
    yield connection
    connection.close()


@pytest.fixture(scope="session")
def schema_text(con: duckdb.DuckDBPyConnection) -> str:
    """El esquema generado, calculado una sola vez: hace ~200 consultas sobre vistas anidadas (~4 s)."""
    return schema(con)
