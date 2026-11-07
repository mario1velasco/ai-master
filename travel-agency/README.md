# Travel Agency

Agente de **Viajes Nimbo** (agencia ficticia) que responde preguntas consultando la base de datos (text-to-SQL
sobre DuckDB) o la documentación (RAG con búsqueda híbrida), con modelos open source en local y una API FastAPI.

- Diseño: [`PROYECTO.md`](PROYECTO.md)
- Instrucciones para agentes de IA: [`AGENTS.md`](AGENTS.md)
- Tickets de cada fase: [`docs/tickets/`](docs/tickets/)

## Estado

| Fase | Qué hay |
|---|---|
| 0–1. Esqueleto, contratos y telemetría | ✅ uv workspace, esquemas Pydantic con sus métricas, logs y trazas en JSONL |
| 2. Base de datos | ✅ Filas escritas a mano con trampas a propósito, conjunto grande generado con semilla fija (~15.000 filas) y capa semántica de vistas DuckDB con comentarios |
| 5. Text-to-SQL | 🚧 Validador de SQL hecho (una sentencia, solo `SELECT`, solo vistas permitidas, 50 filas como mucho); falta la parte del modelo |
| 3, 4 y 6–13 | Pendientes: hoja de ruta en [`PROYECTO.md`](PROYECTO.md) §10 |

## Paquetes

| Carpeta | Qué hace |
|---|---|
| [`contracts/`](contracts/) | Esquemas Pydantic compartidos, todos con métricas |
| [`telemetry/`](telemetry/) | Logger, `span()`, `trace_id` y eventos JSONL |
| [`database/`](database/) | `data/` (los datos de la app), `fixtures/` (las filas a mano, datos de los tests), capa semántica y generador |
| [`text2sql/`](text2sql/) | Pregunta → SQL validado → DuckDB |
| [`rag/`](rag/), [`agent/`](agent/), [`api/`](api/) | Documentos y búsqueda, el agente y la API FastAPI (por hacer) |

## Puesta en marcha

```bash
uv sync
uv run pytest
```

Requisitos: [uv](https://docs.astral.sh/uv/) y, a partir de la fase 5, [Ollama](https://ollama.com) con `qwen3:4b-instruct`.

## Comandos útiles

```bash
uv run python -m database.semantic_layer                                    # lo que ve el modelo: vistas y comentarios
uv run python -m database.semantic_layer --check --data database/fixtures   # las vistas dan las cifras calculadas a mano
uv run python -m database.seed                                              # regenera database/data/ desde fixtures/
uv run ruff check . && uv run ruff format . && uv run ty check              # estilo y tipos
```

`database/data/` se genera: no se edita a mano. Las filas a mano se cambian en `database/fixtures/` y después se
regenera (un test avisa si `data/` se queda desfasada).
