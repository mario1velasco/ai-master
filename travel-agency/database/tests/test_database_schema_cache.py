"""El esquema guardado por huella: cuándo se regenera y qué pasa si el archivo falla (ticket TRAVEL-009).

Cada test copia `fixtures/` a una carpeta temporal y usa una caché vacía (carpeta y memoria), sin Ollama.
"""

import json
import shutil
from pathlib import Path

import duckdb
import pytest

from database.schema import SCHEMA_SOURCE_FILES, cached_schema
from database.seed import FIXTURES_DIR
from database.semantic_layer import open_db

NEW_CLIENT = "C-008,Rosa,Vega Ortiz,rosa.vega@example.com,España,2025-05-05,basico\n"


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Una copia de las filas a mano: una carpeta de datos que la caché no ha visto nunca."""
    return Path(shutil.copytree(FIXTURES_DIR, tmp_path / "data"))


@pytest.fixture
def schema_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """La caché del esquema vacía y solo para este test: su carpeta y su memoria (las dos capas)."""
    path = tmp_path / "cache"
    monkeypatch.setattr("database.schema.SCHEMA_CACHE_DIR", path)
    monkeypatch.setattr("database.schema._SCHEMA_MEMORY_CACHE", {})
    return path


def test_changed_csv_regenerates_schema(data_dir: Path, schema_cache: Path) -> None:
    before = cached_schema(open_db(data_dir))
    with (data_dir / "clientes.csv").open("a", encoding="utf-8") as csv:
        csv.write(NEW_CLIENT)

    after = cached_schema(open_db(data_dir))

    assert len(list(schema_cache.iterdir())) == 2
    assert "Tabla v_resumen_clientes (7 filas)" in before  # los 7 clientes de fixtures/clientes.csv
    assert "Tabla v_resumen_clientes (8 filas)" in after


@pytest.mark.parametrize("change", ["semantic_layer.py", "schema.py", "duckdb"])
def test_other_code_or_duckdb_version_regenerates_schema(
    change: str, data_dir: Path, schema_cache: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sources = tuple(Path(shutil.copy(source, tmp_path / source.name)) for source in SCHEMA_SOURCE_FILES)
    monkeypatch.setattr("database.schema.SCHEMA_SOURCE_FILES", sources)
    cached_schema(open_db(data_dir))
    if change == "duckdb":
        monkeypatch.setattr(duckdb, "__version__", "0.0.0-otra")
    else:
        with (tmp_path / change).open("a", encoding="utf-8") as source:
            source.write("# otro cambio en el código que decide el esquema\n")

    cached_schema(open_db(data_dir))

    assert len(list(schema_cache.iterdir())) == 2


def test_two_data_dirs_do_not_overwrite(data_dir: Path, schema_cache: Path, tmp_path: Path) -> None:
    other_dir = Path(shutil.copytree(FIXTURES_DIR, tmp_path / "other"))
    with (other_dir / "clientes.csv").open("a", encoding="utf-8") as csv:
        csv.write(NEW_CLIENT)
    con, other_con = open_db(data_dir), open_db(other_dir)

    cached_schema(con)
    cached_schema(other_con)

    assert len(list(schema_cache.iterdir())) == 2
    assert "Tabla v_resumen_clientes (7 filas)" in cached_schema(con)  # los 7 clientes de fixtures/clientes.csv
    assert "Tabla v_resumen_clientes (8 filas)" in cached_schema(other_con)


def test_half_written_schema_is_never_used(data_dir: Path, schema_cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def write_half_and_stop(self: Path, data: str, *args: object, **kwargs: object) -> int:
        with self.open("w", encoding="utf-8") as file:
            file.write(data[: len(data) // 2])
        raise KeyboardInterrupt  # un Ctrl+C a mitad de escribir

    with monkeypatch.context() as cut:
        cut.setattr(Path, "write_text", write_half_and_stop)
        with pytest.raises(KeyboardInterrupt):
            cached_schema(open_db(data_dir))

    assert list(schema_cache.glob("schema_*.json")) == []  # nada a medias con nombre de esquema guardado
    monkeypatch.setattr("database.schema._SCHEMA_MEMORY_CACHE", {})  # la pregunta siguiente, en otro proceso
    text = cached_schema(open_db(data_dir))
    [saved] = schema_cache.glob("schema_*.json")
    assert json.loads(saved.read_text(encoding="utf-8"))["schema"] == text
