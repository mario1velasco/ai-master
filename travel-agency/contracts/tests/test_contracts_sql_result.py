import pytest
from pydantic import BaseModel

from contracts.sql import SqlQuery, SqlResult


@pytest.mark.parametrize("model", [SqlQuery, SqlResult])
def test_every_sql_result_field_has_description(model: type[BaseModel]) -> None:
    properties = model.model_json_schema()["properties"]
    missing = [name for name, prop in properties.items() if not prop.get("description")]
    assert missing == []
