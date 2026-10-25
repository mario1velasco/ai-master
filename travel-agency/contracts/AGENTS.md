# AGENTS.md — `contracts/`

> Estado: **fase 0 (esqueleto)**. Solo existe el paquete vacío y un test de importación.

## Propósito

Esquemas Pydantic compartidos por todos los paquetes (`SqlResult`, `RagHit`, `AgentAnswer`…), todos con `metricas` (sección 8 de `PROYECTO.md`). No depende de nada.

Depende de: nada. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/contracts/__init__.py`: punto de entrada del paquete (`import contracts`).
- `tests/`: tests con pytest.

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest contracts/tests
```

Sin variables de entorno.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
