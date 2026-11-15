"""El esquema que recibe el modelo se guarda en un archivo con la huella de los datos (ticket TRAVEL-009).

Cada test copia `fixtures/` a una carpeta temporal y apunta la caché a otra: así ve una carpeta sin esquema guardado
y no escribe en el repo.
"""

import json
import re
import shutil
from pathlib import Path

import pytest
from fake_ollama import FakeOllama, sql_answer

from database.seed import FIXTURES_DIR
from database.semantic_layer import open_db, schema
from text2sql import ask

QUESTION = "¿Cuántas reservas tiene C-001?"
SQL = "SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Una copia de las filas a mano: una carpeta de datos que la caché no ha visto nunca."""
    return Path(shutil.copytree(FIXTURES_DIR, tmp_path / "data"))


@pytest.fixture
def cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """La carpeta de la caché del esquema, vacía y solo para este test."""
    path = tmp_path / "cache"
    monkeypatch.setattr("database.semantic_layer.CACHE_DIR", path)
    return path


def test_first_question_saves_schema_file(data_dir: Path, cache_dir: Path, fake_ollama: FakeOllama) -> None:
    con = open_db(data_dir)
    fake_ollama.answers = [sql_answer(SQL)]

    ask(QUESTION, con=con)

    expected = schema(con)
    [request] = fake_ollama.requests
    assert expected in request["messages"][0]["content"]
    [saved] = cache_dir.iterdir()
    assert re.fullmatch(r"schema_[0-9a-f]{16}\.json", saved.name)  # la huella va en el nombre, como en vision.py
    assert expected in json.loads(saved.read_text(encoding="utf-8")).values()
