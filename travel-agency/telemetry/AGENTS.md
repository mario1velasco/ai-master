# AGENTS.md — `telemetry/`

> Estado: **fase 0 (esqueleto)**. Solo existe el paquete vacío y un test de importación.

## Propósito

Logger con `trace_id`, `span()` para cronometrar bloques, `write_event()` a JSONL y, en el futuro, exportador a MLflow (sección 8).

Depende de: `contracts`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/telemetry/__init__.py`: punto de entrada del paquete (`import telemetry`).
- `tests/`: tests con pytest.

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest telemetry/tests
```

Sin variables de entorno.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
