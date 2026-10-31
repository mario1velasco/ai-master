# AGENTS.md — `travel-agency/`

Agente conversacional para **Viajes Nimbo** (agencia ficticia) que responde sabiendo dónde buscar: en la base de
datos (DuckDB, vía text-to-SQL) o en la documentación (RAG). Todo open source y en local (Ollama, Qwen3-4B),
expuesto con FastAPI. El diseño completo está en [`PROYECTO.md`](PROYECTO.md); léelo antes de decidir algo de
arquitectura.

> Estado: **fase 2a terminada** (8 CSV a mano + capa semántica en `database/`). Siguiente: 2b, `seed/generar.py` (sección 10 de `PROYECTO.md`). Antes de cada fase, mira **Contratos pendientes** más abajo.

## Hoja de ruta y dónde mirar en el repo

**IMPORTANTE: no te inventes nada. Se implementa igual que en clase.** Antes de planear una fase o subfase, lee
**enteras** las referencias de su fila: el código que se ejecuta tiene que ser el mismo. Nombres, archivos y
organización pueden cambiar. **Código en inglés** (archivos, funciones, variables, constantes, opciones), **comentarios
y documentación en castellano**. No inventes otra implementación aunque te parezca mejor.
Solo se cambia lo que obligan las reglas del proyecto (uv workspace, tipos, ruff/ty, tests) o lo que la referencia no
cubre, y se dice como **desvío** en la propuesta. Si una fase no tiene referencia en el repo, dilo y pregunta a Mario antes
de proponer nada. Al terminar una subfase, actualiza esta tabla: estado, en qué te fijaste y qué se desvió del patrón.

Rutas relativas a la raíz del repo `ebis/`. Fases y entregables: sección 10 de `PROYECTO.md`.

| Fase | Estado | Dónde mirar (parte del curso) | En qué fijarse |
|---|---|---|---|
| **0. Esqueleto** | ✅ | `llm-customer-support-triage/` (proyecto propio) | Paquete `app/` sin `src/` para `api/`; `.env.example` por carpeta |
| **1a. Métricas** `contracts/metrics` | ✅ | **Tema 4**: `04_api_sdks_ia/Clases/02/schemas.py`, `Clases/03/llm_client.py`, `Clases/06/app/{dto.py, api_clients/anthropic_client.py, utils/observability.py}`, `Clases/06/config.yml` | `ConfigDict(extra="forbid")`, `Field(description=…)`, enums de texto, submodelos anidados (`RequestMetrics`), `estimate_cost`, versiones de prompt/esquema/reglas. Desvíos: `StrEnum` (lo pide ruff) y derivados como campos normales, no `computed_field` (ver `contracts/AGENTS.md`) |
| **1b. Telemetría** `span()` + `write_event()` | ✅ | **Tema 4**: `Clases/06/app/utils/{observability.py, logger.py}` (`build_observability_event`, `write_jsonl`, `read_jsonl`, `get_logger`), `Clases/06/app/services/event_service.py` (cuándo se escribe el evento y cómo se clasifican los errores). **Tema 8**: `tema8-agentes/comun/medidor.py` (`perf_counter` alrededor de cada llamada) | El evento JSONL del tema 4 es la base: se amplía con `trace_id`/`span_id`, no se cambia su forma de escribir. Desvíos: evento Pydantic con `metrics_type` para releer (allí `dict`), logger con `trace_id` y archivo rotado, sin propagar (ver `telemetry/AGENTS.md`) |
| **1c. Resto de contratos** | ✅ | **Tema 4**: `Clases/06/app/dto.py` (`EventResponse` con `metrics` anidado); JSON de respuesta de `PROYECTO.md` sección 7 | Un modelo de resultado por paquete, cada uno con su campo de métricas. Hecho: `SqlMetrics`, `RagMetrics`, `AgentMetrics`, `ApiMetrics`. Desvío: los resultados y `ConversionMetrics` se aplazan a su fase (ver **Contratos pendientes**); quitados `pasos`, `duracion_total_ms` y `request_id` (los da la traza) |
| **2. Base de datos** | 2a ✅ · 2b ⏭ siguiente | **Tema 7**: `07_llm_open_source/clase_01/Ejercicios/DropLab/{datos, documentos/diccionario_datos.md}`, `practica/01_inspeccionar_datos.py`, `practica/02_auditoria_integridad.py`. **Tema 8**: `tema8-agentes/comun/tienda.py` (BBDD simulada). **Tema 7 S2**: `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py` (`VISTAS`, `COMENTARIOS`, `GUIA`, `esquema()`, `COMPROBACIONES`) | CSV pequeños con trampas a propósito; auditoría de claves y relaciones antes de calcular nada. **Diccionario generado, no a mano**: tablas en un esquema oculto + vistas con `COMMENT ON` en cada vista y columna → el esquema que ve el LLM sale de `duckdb_views()`/`duckdb_columns()`; `GUIA` con qué vista usar y "datos que NO existen"; `COMPROBACIONES` con cifras calculadas a mano → tests de integridad. Hecho en 2a igual que en clase: `database/src/database/semantic_layer.py` con la misma implementación; auditoría de la clase 1 pasada a tests SQL. Desvíos: auditoría en SQL y no en pandas (los CSV ya están en DuckDB), sin `--sql`/`--prompt` ni `INSTRUCCIONES` (son de la fase 5), columna nueva `reservas_tramos.trayecto`, base en memoria sin `DUCKDB_PATH` |
| **3. Corpus** | pendiente | **Tema 5**: `05_rag_langchain/practica/` y `Ejercicios/rag-tenerife/` (PDF con página en los metadatos). **Tema 7**: `DropLab/documentos/politica_reembolsos.md` (modelo para los documentos de `empresa/`) | El documento y la página viajan con cada fragmento para poder citar. No hay en el repo un modelo de `SOURCES.md`: preguntar |
| **4. Conversión a Markdown** | pendiente | `Skills-mario/any-to-any/` (MarkItDown + segundo lector para detectar texto perdido) y `06_mcp/03-skills/img-to-text/` **Tema 7 S3**: `S3/08_leer_documentos.py` (texto / OCR PP-OCRv6 / parser PaddleOCR-VL-1.6 / VLM), `S3/asistente/lectura.py` (limpiar, unir fila partida, comprobar con la capa de texto, ficha "sin revisar"), `requirements_ocr.txt` en la raíz de `DropLab_sesion_3/` | Mismo contenido, solo formato; avisar de páginas sin texto. PaddleOCR en un **entorno aparte**. Allí se midió PaddleOCR-VL-1.6 y `PROYECTO.md` dice PP-StructureV3: decidirlo con Mario. GTX 1650 de 4 GB: medir antes (en CPU ~40 s/página) |
| **5. Text-to-SQL (línea base)** | pendiente | **Tema 7**: `clase_01/Ejercicios/practica/04_conectar_ollama.py` (escalera de contexto), `07_herramienta_funcion.py` (función fija), `08_herramienta_sql.py` (SQL libre sobre DuckDB, esquema generado), `ejercicio_3/herramientas.py`, `EXPLICACION_tema_1.md`. **Tema 4**: `Clases/02` y `03` (salida estructurada con esquema). **Tema 8**: `comun/llm.py` (cliente Ollama). **Tema 7 S2/S3**: `S2/01_preguntar_datos.py` (bucle, error de DuckDB devuelto al modelo, `cifras_sin_respaldo()`), `S3/asistente/datos.py` (consultas fijas con `?` + regex del valor), `S3/asistente/ollama.py` (cliente `/api/chat` con tiempos), `S3/asistente/config.py` | "El código calcula, el modelo redacta"; barreras en el código, no en el prompt. Ojo: `comun/llm.py` usa `/v1` y las métricas de Ollama necesitan `/api/chat`. Con la capa semántica el 4B solo llegó al 67 %: consultas fijas para las preguntas frecuentes, SQL libre para el resto. **Un único `num_ctx`** para Qwen3-4B, compartido con `agent/` (sección 5 de `PROYECTO.md`). La barrera de clase no tiene lista blanca de vistas: añadirla |
| **6. Agente mínimo** | pendiente | **Tema 8**: `tema8-agentes/sesion1/agente_minimo.py`, `sesion2/` (ReAct, plan-and-execute, reflexión, `comparar_estrategias.py`), `sesion3/` (herramientas, LangGraph, MCP), `sesion4/` (memoria), `comun/herramientas.py`, `comun/medidor.py`. **Tema 6**: `06_mcp/01-agents-harness/` (harness: bucle, historial, permisos). **Tema 7**: `07_herramienta_funcion.py` (tool calling con Qwen). `docs/guia-evaluacion-estrategias-agente.md`. **Tema 7 S2/S3**: `S3/asistente/flujo_simple.py` (bucle sin framework), `S3/asistente/flujo.py` (`Plan` con opciones `Literal`, `enrutar`, `contrastar`, `verificar` sin IA), `S2/15_analista.py` (citas `[S#]`/`[D#]` numeradas por código) | Bucle agéntico sin frameworks primero; herramientas descritas al modelo, nunca su código. Línea base = tool calling nativo, medido desde el principio; estado limpio en cada ejecución (sin contadores globales). **Plan cerrado** (`Literal` por `format` + enrutado por código) como estrategia a comparar con tool calling. Verificador sin IA: la cifra debe estar en la fuente **citada**, no en cualquiera (fallo de clase: 60 en vez de 40) |
| **7. API** | pendiente | `llm-customer-support-triage/` entero (capas, sesiones, mock, `Makefile`). **Tema 4**: `Clases/04` → `05` → `06` (de dónde sale triage). **Tema 3**: `03_API_Integracion_servicios/final-proyect/` | Copiar la estructura de triage; mock determinista para los tests |
| **8. RAG** | pendiente | **Tema 5**: `clases/02` (BM25), `03` (híbrida, RRF, reranking), `04` (FAISS) + `travel-agency/docs/guia-indices-vectoriales.md`, `05` (filtros por metadatos), `07-RAG/src/umbra/{retrieval/hybrid.py, generation/, domain/models.py}`; `Ejercicios/rag-tenerife/` (Hit@k por página, `utilidades.py`). **Tema 7 S2/S3**: `S2/10_corpus.py` (trocear por estructura, ficha por fragmento), `S2/11_indice.py`, `S2/12_buscar.py` (BM25 propio + RRF k=60), `S2/13_preguntar_documentos.py` (`REGLAS`, `verificar()`), `S3/09_indice_junio.py` (ampliar índice conservando ids) | Citas y abstención como contrato del prompt; el documento son datos, no instrucciones. La **versión va en la clave** del documento (caso "versión derogada"). El tokenizador BM25 de clase parte "261/2004" en dos: adaptarlo a los códigos legales |
| **9. Fine-tuning** | pendiente | **No hay referencia en el repo** (QLoRA, unsloth, peft) | Preguntar a Mario antes de planear |
| **10. Evaluación completa** | pendiente | `llm-customer-support-triage/eval/` (`eval_cases.yml`, `run_eval.py` mock/real). **Tema 5**: `clases/06-Const-evaluacion/src/retrieval_lab/evaluation/` (métricas, estadística, selección), `07-RAG/src/umbra/evaluation/comparison.py`, `practica/herramientas/preparar_revision.py` (revisión manual). **Tema 8**: `sesion2/comparar_estrategias.py`, `reflexion.py` (crítico). `docs/guia-evaluacion-estrategias-agente.md`. **Tema 7 S2/S3**: `S2/04_examen.py` + `S2/examen/` (diseñar / validar / decidir, `debe_negar`), `S2/14_evaluar_rag.py` (Hit@k + MRR sin LLM), `S3/06_evaluar.py` + `S3/examen/examen_sesion_3.json` (por piezas, `debe`/`no_debe`), `S3/07_comparar.py`, `S3/guardar_salidas.py` + `S3/salidas_guardadas/` | Casos dorados en YAML; medir por etapas; revisión humana. Juez de fidelidad con la **evidencia** de las herramientas (un crítico a ciegas aprueba respuestas falsas); varias repeticiones; coste del juez aparte (`purpose = judge`). **Salidas reales guardadas** como base del mock de los tests. Comprobar hechos concretos (el 4B omitió la cifra clave y nadie lo vio) |
| **11. MLflow** | pendiente | **No hay referencia en el repo** | Preguntar a Mario antes de planear |
| **12. Modelos de decisión** | pendiente | **Tema 6**: `06_mcp/03-skills/ebis-cli-decision-model/` (`DECISION_MODEL.md`, `routing-llm.json`) | Decidir por umbral; si la confianza es baja, decide el LLM |
| **13. Docker** | pendiente | `llm-customer-support-triage/{Dockerfile, Makefile}` (`docker-build`, `docker-run`) y `04_api_sdks_ia/Clases/06/Dockerfile` | Mismo esquema que triage |

## Contratos pendientes (no olvidar)

Se aplazaron a propósito en la fase 1c porque dependen de decisiones de su fase. Al empezar esa fase, créalos
en `contracts/` (y regístralos en `METRICS_TYPES` de telemetry si son métricas). Detalle en `contracts/AGENTS.md`.

| Fase | Contrato |
|---|---|
| 4. Conversión | `ConversionMetrics` |
| 5. Text-to-SQL | `SqlResult` (con `metrics: SqlMetrics`) |
| 6. Agente | `AgentAnswer` (con `metrics: AgentMetrics`) |
| 7. API | `SystemMetrics` (opcional) |
| 8. RAG | `RagHit` / `RagResult` (con `metrics: RagMetrics`) |

## Mapa de carpetas

| Carpeta | Qué hace | Depende de |
|---|---|---|
| `contracts/` | Esquemas Pydantic compartidos, todos con métricas | nada |
| `telemetry/` | Logger, `span()`, `trace_id`, eventos JSONL | `contracts` |
| `database/` | CSV propios → capa semántica en memoria (vistas + comentarios + esquema generado + guía) | `telemetry` (para los eventos del seed, 2b) |
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

- **Se implementa igual que en clase** (ver "Hoja de ruta"): el mismo código ejecutado; nombres y archivos pueden cambiar.
  Código en inglés (archivos, funciones, variables); comentarios y documentación en castellano.
- Antes de escribir código, se enseña la propuesta a Mario y se espera su visto bueno.
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
