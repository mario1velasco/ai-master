"""El esquema que ve el modelo: `schema()` lo genera desde las vistas y `cached_schema()` lo guarda por huella.

`schema()` es `esquema()` de `07_llm_open_source/.../sesion_2/02_capa_semantica.py`: nadie lo escribe a mano. Tarda
~5 s, así que `cached_schema()` lo guarda en memoria y en un archivo con la huella de lo que lo decide en el nombre
(TRAVEL-009). Este módulo no sabe nada del negocio: eso vive en `semantic_layer.py`.
"""

import hashlib
import json
from pathlib import Path

import duckdb

SCHEMA_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache"  # esquemas guardados por huella (fuera de git)
# El código que decide el texto del esquema: las vistas y sus comentarios, y cómo se escribe (va en la huella)
SCHEMA_SOURCE_FILES = (Path(__file__).resolve().with_name("semantic_layer.py"), Path(__file__).resolve())
_FINGERPRINT_VARIABLE = "data_fingerprint"  # variable de DuckDB donde open_db() guarda la huella


# ---------------------------------------------------------------------------
# El esquema generado
# ---------------------------------------------------------------------------


def _scalar(con: duckdb.DuckDBPyConnection, sql: str) -> object:
    """Primer valor de la primera fila (las consultas de `schema` siempre devuelven una)."""
    row = con.execute(sql).fetchone()
    return row[0] if row else None


def schema(con: duckdb.DuckDBPyConnection, max_values: int = 6) -> str:
    """Esquema automático de lo que está en «main» (las vistas), con sus comentarios. Nadie lo escribe a mano."""
    objects = [
        r[0]
        for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1"
        ).fetchall()
    ]
    view_comments = dict(con.execute("SELECT view_name, comment FROM duckdb_views() WHERE NOT internal").fetchall())
    column_comments = {
        (table, col): comment
        for table, col, comment in con.execute(
            "SELECT table_name, column_name, comment FROM duckdb_columns() WHERE comment IS NOT NULL"
        ).fetchall()
    }
    parts = []
    for name in objects:
        n = _scalar(con, f"SELECT COUNT(*) FROM {name}")
        header = f"Tabla {name} ({n} filas)" + (f": {view_comments[name]}" if view_comments.get(name) else "")
        lines = []
        for col, col_type, *_ in con.execute(f"DESCRIBE {name}").fetchall():
            distinct = _scalar(con, f'SELECT COUNT(DISTINCT "{col}") FROM {name}')
            if isinstance(distinct, int) and distinct <= max_values:
                values = [str(r[0]) for r in con.execute(f'SELECT DISTINCT "{col}" FROM {name} ORDER BY 1').fetchall()]
                extra = f" valores: {', '.join(values)}"
            else:
                example = _scalar(con, f'SELECT "{col}" FROM {name} WHERE "{col}" IS NOT NULL ORDER BY 1 LIMIT 1')
                extra = f" ej.: {example}"
            note = f" — {column_comments[(name, col)]}" if (name, col) in column_comments else ""
            lines.append(f"  - {col} ({col_type}){extra}{note}")
        parts.append(header + ":\n" + "\n".join(lines))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# El esquema guardado por huella (TRAVEL-009)
# ---------------------------------------------------------------------------


def _file_digest(path: Path) -> str:
    """SHA-256 de un archivo, por bloques (`file_digest` de `05_rag_langchain/.../infrastructure/artifacts.py`)."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            digest.update(block)
    return digest.hexdigest()


def _fingerprint(value: object) -> str:
    """SHA-256 de un valor JSON (`fingerprint` de `05_rag_langchain/.../infrastructure/artifacts.py`)."""
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: object) -> None:
    """Escritura atómica: primero un `.tmp` y después `replace`, así nunca queda un archivo a medias con su nombre
    (`write_json` de `05_rag_langchain/.../infrastructure/artifacts.py`)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    clean = json.loads(json.dumps(value, default=str), parse_constant=lambda _: None)
    temporary.write_text(json.dumps(clean, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def _data_fingerprint(data_dir: Path) -> str:
    """Huella de lo que decide el esquema: los CSV, el código que lo genera y la versión de DuckDB.

    Sirve para saber si el esquema guardado sigue valiendo sin generarlo otra vez: va en el nombre del archivo
    (`schema_<huella>.json`). Si nada cambió, sale la misma huella y se lee el archivo; si cambia un solo byte de
    cualquiera de las tres cosas, sale otra, no hay archivo y el esquema se genera y se guarda de nuevo.
    """
    inputs = {
        "csv": {csv.name: _file_digest(csv) for csv in sorted(data_dir.glob("*.csv"))},
        "code": {source.name: _file_digest(source) for source in SCHEMA_SOURCE_FILES},
        "duckdb": duckdb.__version__,
    }
    return _fingerprint(inputs)


_SCHEMA_MEMORY_CACHE: dict[str, str] = {}  # huella → esquema; la clave es texto, nunca la conexión (no la retiene)


def cached_schema(con: duckdb.DuckDBPyConnection) -> str:
    """El esquema de `schema()`, guardado en memoria y en un archivo con la huella de los datos en el nombre.

    Como las dos capas de `extraer()` en `07_llm_open_source/.../sesion_3/asistente/vision.py`: primero la memoria
    (mismo proceso), después el disco (otros procesos) y, si no está, se genera. Desvío (TRAVEL-009): en clase el
    esquema se genera en cada pregunta, y aquí tarda ~5 s.
    """
    key = str(_scalar(con, f"SELECT getvariable('{_FINGERPRINT_VARIABLE}')"))
    disk = SCHEMA_CACHE_DIR / f"schema_{key[:16]}.json"
    if key in _SCHEMA_MEMORY_CACHE:
        return _SCHEMA_MEMORY_CACHE[key]
    if disk.exists():  # mismos datos (huella sha256): el esquema ya está guardado
        _SCHEMA_MEMORY_CACHE[key] = json.loads(disk.read_text(encoding="utf-8"))["schema"]
        return _SCHEMA_MEMORY_CACHE[key]
    text = schema(con)
    _SCHEMA_MEMORY_CACHE[key] = text
    _write_json(disk, {"fingerprint": key, "schema": text})
    return text
