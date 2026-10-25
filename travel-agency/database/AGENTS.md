# AGENTS.md — `database/`

> Estado: **fase 0 (esqueleto)**. Solo existe el paquete vacío y un test de importación.

## Propósito

CSV creados por nosotros (`data/`), generador con semilla fija (`seed/`), vistas DuckDB de solo lectura (`schema/`) y diccionario de datos (`docs/`). Son datos: no sabe nada de LLMs (sección 3).

Depende de: `telemetry`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/database/__init__.py`: punto de entrada del paquete (`import database`).
- `tests/`: tests con pytest.
- `data/`
- `schema/`
- `seed/`
- `docs/`

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest database/tests
```

Variables en `.env` (copiar de `.env.example`): `DUCKDB_PATH`.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
