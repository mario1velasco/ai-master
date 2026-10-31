# AGENTS.md — `api/`

> Estado: **fase 0 (esqueleto)**. Solo existe el paquete vacío y un test de importación.

## Propósito

HTTP, sesiones, observabilidad y errores. Copia el esqueleto de `llm-customer-support-triage/` (paquete `app/`, sin `src/`); el LLM no vive aquí: llama al paquete `agent/` (sección 7).

Depende de: `contracts`, `telemetry`, `agent`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `app/__init__.py`: punto de entrada del paquete (`import app`).
- `tests/`: tests con pytest.
- `eval/`

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest api/tests
```

Variables en `.env` (copiar de `.env.example`): `OLLAMA_BASE_URL`, `AGENT_MODEL`, `TEXT2SQL_MODEL`.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
