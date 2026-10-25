# AGENTS.md — `travel-agency/`

Agente conversacional para **Viajes Nimbo** (agencia ficticia) que responde sabiendo dónde buscar: en la base de
datos (DuckDB, vía text-to-SQL) o en la documentación (RAG). Todo open source y en local (Ollama, Qwen3-4B),
expuesto con FastAPI. El diseño completo está en [`PROYECTO.md`](PROYECTO.md); léelo antes de decidir algo de
arquitectura.

> Estado: **fase 0 (esqueleto) terminada**. Siguiente: fase 1, `contracts/` + `telemetry/` (sección 10 de `PROYECTO.md`).

## Mapa de carpetas

| Carpeta | Qué hace | Depende de |
|---|---|---|
| `contracts/` | Esquemas Pydantic compartidos, todos con métricas | nada |
| `telemetry/` | Logger, `span()`, `trace_id`, eventos JSONL | `contracts` |
| `database/` | CSV propios → vistas DuckDB de solo lectura + diccionario | `telemetry` |
| `rag/` | Corpus, conversión a Markdown, búsqueda híbrida | `contracts`, `telemetry` |
| `text2sql/` | Pregunta → SQL validado → DuckDB | `contracts`, `telemetry`, `database` |
| `agent/` | Decide herramienta, combina y redacta | `contracts`, `telemetry`, `rag`, `text2sql` |
| `api/` | FastAPI, sesiones, observabilidad (paquete `app/`, como triage) | `contracts`, `telemetry`, `agent` |
| `docs/` | ADR, guías y diagramas | — |

Las dependencias van en un solo sentido: `api → agent → (text2sql, rag) → contracts`. Nada importa `api`.
Cada paquete expone **una función pública** con tipos de `contracts/`; no se importan módulos internos de otro paquete.

## Entorno

Es un **uv workspace**: un solo `.venv` y un solo `uv.lock` en esta carpeta; cada miembro tiene su `pyproject.toml`.
Python 3.12 (`.python-version`; 3.14 da problemas con PaddleOCR y torch).

```bash
cd travel-agency
uv sync                       # instala todos los paquetes en modo editable + herramientas de dev
uv run pytest                 # todos los tests
uv run pytest rag/tests       # los de un paquete
uv run ruff check . && uv run ruff format .
uv run ty check
```

Añadir una dependencia a un paquete: `uv add --package travel-<carpeta> <librería>`.
Dependencia entre paquetes: `travel-<otro>` en `dependencies` + `{ workspace = true }` en `[tool.uv.sources]`.

## Reglas

- `.env` **por carpeta** (se copia de su `.env.example`); nunca en la raíz, nunca se muestra ni se sube.
- Todo local y open source: sin APIs de pago. Los tests no necesitan Ollama (mock determinista).
- Datos de clientes **sintéticos**; no se registran datos personales en los logs salvo opción explícita.
- Nombres de test **únicos en todo el workspace** (`test_<paquete>_*.py`): pytest usa el modo `prepend` y dos
  archivos con el mismo nombre chocan. No uses `--import-mode=importlib`: hace que `database/` (la carpeta) tape
  al paquete `database`.
- Python con la skill `python-developer`; tipos en todo; ruff y ty en verde.
- No hagas commits salvo que se pidan.
- Cada `AGENTS.md` ≤ 400 líneas; el de una carpeta manda sobre este para lo que pase dentro de ella y se actualiza
  en el mismo cambio.

## A qué `AGENTS.md` ir

Esquemas o métricas → `contracts/` · logs y trazas → `telemetry/` · CSV, vistas, seed → `database/` ·
documentos y búsqueda → `rag/` · SQL → `text2sql/` · razonamiento y herramientas → `agent/` · HTTP → `api/`.
