# AGENTS.md — `text2sql/`

> Estado: **fase 0 (esqueleto)**. Solo existe el paquete vacío y un test de importación.

## Propósito

Traduce una pregunta a SQL con Qwen3-4B, lo valida (solo `SELECT`, solo vistas permitidas) y lo ejecuta en DuckDB (sección 6).

Depende de: `contracts`, `telemetry`, `database`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/text2sql/__init__.py`: punto de entrada del paquete (`import text2sql`).
- `tests/`: tests con pytest.
- `dataset/`
- `finetune/`
- `eval/`

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest text2sql/tests
```

Variables en `.env` (copiar de `.env.example`): `OLLAMA_BASE_URL`, `TEXT2SQL_MODEL`, `DUCKDB_PATH`.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
