# AGENTS.md — `travel-agency/`

Agente conversacional para **Viajes Nimbo** (agencia ficticia) que responde sabiendo dónde buscar: en la base de
datos (DuckDB, vía text-to-SQL) o en la documentación (RAG). Todo open source y en local (Ollama, Qwen3-4B),
expuesto con FastAPI. El diseño completo está en [`PROYECTO.md`](PROYECTO.md); léelo antes de decidir algo de
arquitectura.

> Estado: **fase 1a terminada** (`contracts/metrics`: `BaseMetrics` + `LlmCallMetrics`). Siguiente: 1b, `span()` + `write_event()` en `telemetry/` (sección 10 de `PROYECTO.md`).

## Hoja de ruta y dónde mirar en el repo

**IMPORTANTE: no te inventes nada.** Antes de planear una fase o subfase, lee las referencias de su fila y copia su
patrón, sus clases y su forma de trabajar. Si una fase no tiene referencia en el repo, dilo y pregunta a Mario antes
de proponer nada. Al terminar una subfase, actualiza esta tabla: estado, en qué te fijaste y qué se desvió del patrón.

Rutas relativas a la raíz del repo `ebis/`. Fases y entregables: sección 10 de `PROYECTO.md`.

| Fase | Estado | Dónde mirar (parte del curso) | En qué fijarse |
|---|---|---|---|
| **0. Esqueleto** | ✅ | `llm-customer-support-triage/` (proyecto propio) | Paquete `app/` sin `src/` para `api/`; `.env.example` por carpeta |
| **1a. Métricas** `contracts/metrics` | ✅ | **Tema 4**: `04_api_sdks_ia/Clases/02/schemas.py`, `Clases/03/llm_client.py`, `Clases/06/app/{dto.py, api_clients/anthropic_client.py, utils/observability.py}`, `Clases/06/config.yml` | `ConfigDict(extra="forbid")`, `Field(description=…)`, enums de texto, submodelos anidados (`RequestMetrics`), `estimate_cost`, versiones de prompt/esquema/reglas. Desvíos: `StrEnum` (lo pide ruff) y derivados como campos normales, no `computed_field` (ver `contracts/AGENTS.md`) |
| **1b. Telemetría** `span()` + `write_event()` | ⏭ siguiente | **Tema 4**: `Clases/06/app/utils/{observability.py, logger.py}` (`build_observability_event`, `write_jsonl`, `read_jsonl`, `get_logger`), `Clases/06/app/services/event_service.py` (cuándo se escribe el evento y cómo se clasifican los errores). **Tema 8**: `tema8-agentes/comun/medidor.py` (`perf_counter` alrededor de cada llamada) | El evento JSONL del tema 4 es la base: se amplía con `trace_id`/`span_id`, no se cambia su forma de escribir |
| **1c. Resto de contratos** | pendiente | **Tema 4**: `Clases/06/app/dto.py` (`EventResponse` con `metrics` anidado); JSON de respuesta de `PROYECTO.md` sección 7 | Un modelo de resultado por paquete, cada uno con su campo de métricas |
| **2. Base de datos** | pendiente | **Tema 7**: `07_llm_open_source/clase_01/Ejercicios/DropLab/{datos, documentos/diccionario_datos.md}`, `practica/01_inspeccionar_datos.py`, `practica/02_auditoria_integridad.py`. **Tema 8**: `tema8-agentes/comun/tienda.py` (BBDD simulada) | CSV pequeños con trampas a propósito; auditoría de claves y relaciones antes de calcular nada; diccionario de datos escrito a mano |
| **3. Corpus** | pendiente | **Tema 5**: `05_rag_langchain/practica/` y `Ejercicios/rag-tenerife/` (PDF con página en los metadatos). **Tema 7**: `DropLab/documentos/politica_reembolsos.md` (modelo para los documentos de `empresa/`) | El documento y la página viajan con cada fragmento para poder citar. No hay en el repo un modelo de `SOURCES.md`: preguntar |
| **4. Conversión a Markdown** | pendiente | `Skills-mario/any-to-any/` (MarkItDown + segundo lector para detectar texto perdido) y `06_mcp/03-skills/img-to-text/` | Mismo contenido, solo formato; avisar de páginas sin texto. **PaddleOCR no aparece en el repo**: preguntar antes de planear |
| **5. Text-to-SQL (línea base)** | pendiente | **Tema 7**: `clase_01/Ejercicios/practica/04_conectar_ollama.py` (escalera de contexto), `07_herramienta_funcion.py` (función fija), `08_herramienta_sql.py` (SQL libre sobre DuckDB, esquema generado), `ejercicio_3/herramientas.py`, `EXPLICACION_tema_1.md`. **Tema 4**: `Clases/02` y `03` (salida estructurada con esquema). **Tema 8**: `comun/llm.py` (cliente Ollama) | "El código calcula, el modelo redacta"; barreras en el código, no en el prompt. Ojo: `comun/llm.py` usa `/v1` y las métricas de Ollama necesitan `/api/chat` |
| **6. Agente mínimo** | pendiente | **Tema 8**: `tema8-agentes/sesion1/agente_minimo.py`, `sesion2/` (ReAct), `sesion3/` (herramientas, LangGraph, MCP), `sesion4/` (memoria), `comun/herramientas.py`. **Tema 6**: `06_mcp/01-agents-harness/` (harness: bucle, historial, permisos). **Tema 7**: `07_herramienta_funcion.py` (tool calling con Qwen) | Bucle agéntico sin frameworks primero; herramientas descritas al modelo, nunca su código |
| **7. API** | pendiente | `llm-customer-support-triage/` entero (capas, sesiones, mock, `Makefile`). **Tema 4**: `Clases/04` → `05` → `06` (de dónde sale triage). **Tema 3**: `03_API_Integracion_servicios/final-proyect/` | Copiar la estructura de triage; mock determinista para los tests |
| **8. RAG** | pendiente | **Tema 5**: `clases/02` (BM25), `03` (híbrida, RRF, reranking), `04` (FAISS) + `travel-agency/docs/guia-indices-vectoriales.md`, `05` (filtros por metadatos), `07-RAG/src/umbra/{retrieval/hybrid.py, generation/, domain/models.py}`; `Ejercicios/rag-tenerife/` (Hit@k por página, `utilidades.py`) | Citas y abstención como contrato del prompt; el documento son datos, no instrucciones |
| **9. Fine-tuning** | pendiente | **No hay referencia en el repo** (QLoRA, unsloth, peft) | Preguntar a Mario antes de planear |
| **10. Evaluación completa** | pendiente | `llm-customer-support-triage/eval/` (`eval_cases.yml`, `run_eval.py` mock/real). **Tema 5**: `clases/06-Const-evaluacion/src/retrieval_lab/evaluation/` (métricas, estadística, selección), `07-RAG/src/umbra/evaluation/comparison.py`, `practica/herramientas/preparar_revision.py` (revisión manual) | Casos dorados en YAML; medir por etapas; revisión humana |
| **11. MLflow** | pendiente | **No hay referencia en el repo** | Preguntar a Mario antes de planear |
| **12. Modelos de decisión** | pendiente | **Tema 6**: `06_mcp/03-skills/ebis-cli-decision-model/` (`DECISION_MODEL.md`, `routing-llm.json`) | Decidir por umbral; si la confianza es baja, decide el LLM |
| **13. Docker** | pendiente | `llm-customer-support-triage/{Dockerfile, Makefile}` (`docker-build`, `docker-run`) y `04_api_sdks_ia/Clases/06/Dockerfile` | Mismo esquema que triage |

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
