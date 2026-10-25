# AGENTS.md — `agent/`

> Estado: **fase 0 (esqueleto)**. Solo existe el paquete vacío y un test de importación.

## Propósito

Decide si la pregunta necesita la BBDD, los documentos o ambos; llama a las herramientas y redacta la respuesta citando fuentes.

Depende de: `contracts`, `telemetry`, `rag`, `text2sql`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/agent/__init__.py`: punto de entrada del paquete (`import agent`).
- `tests/`: tests con pytest.
- `eval/`

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest agent/tests
```

Variables en `.env` (copiar de `.env.example`): `OLLAMA_BASE_URL`, `AGENT_MODEL`.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
