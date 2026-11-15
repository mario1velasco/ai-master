"""El esquema guardado por huella: cuándo se regenera y qué pasa si el archivo falla (ticket TRAVEL-009).

Cada test copia `fixtures/` a una carpeta temporal y usa una caché vacía (carpeta y memoria), sin Ollama.
"""

import shutil
from pathlib import Path

import pytest

from database.seed import FIXTURES_DIR
from database.semantic_layer import cached_schema, open_db

NEW_CLIENT = "C-008,Rosa,Vega Ortiz,rosa.vega@example.com,España,2025-05-05,basico\n"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Una copia de las filas a mano: una carpeta de datos que la caché no ha visto nunca."""
    return Path(shutil.copytree(FIXTURES_DIR, tmp_path / "data"))


@pytest.fixture
def schema_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """La caché del esquema vacía y solo para este test: su carpeta y su memoria (las dos capas)."""
    path = tmp_path / "cache"
    monkeypatch.setattr("database.semantic_layer.SCHEMA_CACHE_DIR", path)
    monkeypatch.setattr("database.semantic_layer._SCHEMA_MEMORY_CACHE", {})
    return path


def test_changed_csv_regenerates_schema(data_dir: Path, schema_cache: Path) -> None:
    before = cached_schema(open_db(data_dir))
    with (data_dir / "clientes.csv").open("a", encoding="utf-8") as csv:
        csv.write(NEW_CLIENT)

    after = cached_schema(open_db(data_dir))

    assert len(list(schema_cache.iterdir())) == 2
    assert "Tabla v_resumen_clientes (7 filas)" in before  # los 7 clientes de fixtures/clientes.csv
    assert "Tabla v_resumen_clientes (8 filas)" in after
