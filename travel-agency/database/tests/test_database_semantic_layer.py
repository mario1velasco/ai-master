import duckdb
import pytest

from database.semantic_layer import CHECKS, COMMENTS, GUIDE, Row, rounded_rows, run_checks


@pytest.mark.parametrize(("name", "sql", "expected"), CHECKS, ids=[c[0] for c in CHECKS])
def test_database_check(con: duckdb.DuckDBPyConnection, name: str, sql: str, expected: list[Row]) -> None:
    assert rounded_rows(con, sql) == expected


def test_database_run_checks_all_ok(con: duckdb.DuckDBPyConnection) -> None:
    assert run_checks(con) is True


def test_database_schema_only_shows_views(schema_text: str) -> None:
    for view in COMMENTS:
        assert f"Tabla {view} (" in schema_text
    assert "crudo" not in schema_text
    assert "email" not in schema_text  # los datos de contacto no se enseñan al modelo


def test_database_schema_has_comments(schema_text: str) -> None:
    for desc, cols in COMMENTS.values():
        assert desc in schema_text
        for comment in cols.values():
            assert comment in schema_text


def test_database_no_file_access(con: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(duckdb.PermissionException):
        con.execute("SELECT * FROM read_csv_auto('/etc/passwd')")


def test_database_configuration_locked(con: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(duckdb.InvalidInputException):
        con.execute("SET enable_external_access = true")


def test_database_guide_lists_missing_data() -> None:
    assert "Datos que NO existen" in GUIDE
