# database

Los datos de la app en `data/` (generados a partir de las filas a mano de `fixtures/`, que usan los tests) y capa semántica (`src/database/semantic_layer.py`): vistas DuckDB con comentarios, esquema generado y guía, como en clase. Generador con semilla fija (`uv run python -m database.seed`, fase 2b) que escribe `data/` desde `fixtures/`, sin Faker. Son datos: no sabe nada de LLMs (sección 3).

Ver [`AGENTS.md`](AGENTS.md) y [`../PROYECTO.md`](../PROYECTO.md).
