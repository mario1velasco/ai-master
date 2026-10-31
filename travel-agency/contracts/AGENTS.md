# AGENTS.md — `contracts/`

> Estado: **fase 1c**. Hechas las métricas `BaseMetrics`, `LlmCallMetrics`, `SqlMetrics`, `RagMetrics`,
> `AgentMetrics` y `ApiMetrics`. Lo que falta se crea en la fase de su paquete: ver **Pendiente** al final.

## Propósito

Esquemas Pydantic compartidos por todos los paquetes. Cada resultado de cada paquete lleva sus métricas
(sección 8 de [`../PROYECTO.md`](../PROYECTO.md)). No depende de ningún otro paquete del proyecto: solo de `pydantic`.

## Archivos clave

```
src/contracts/metrics/
├── __init__.py      # reexporta todo lo público
├── enums.py         # Status, Component
├── base.py          # BaseMetrics, Versions, METRICS_SCHEMA_VERSION, short_hash, check_or_fill
├── sql.py           # SqlMetrics (span text2sql.consultar)
├── rag.py           # RagMetrics, ScoreStats (span rag.search)
├── agent.py         # AgentMetrics (span agent.responder; solo totales)
├── api.py           # ApiMetrics (span raíz de cada petición)
└── llm/
    ├── enums.py     # LlmProvider, LlmPurpose, FinishReason
    ├── ollama.py    # OllamaTimings (tiempos en ns de la API nativa de Ollama + derivados)
    ├── cost.py      # CostRate, CostEstimate (misma fórmula que estimate_cost de triage)
    └── call.py      # LlmCallMetrics(BaseMetrics)
```

## API pública

```python
from contracts.metrics import (
    BaseMetrics, LlmCallMetrics, SqlMetrics, RagMetrics, ScoreStats, AgentMetrics, ApiMetrics,
    OllamaTimings, CostRate, CostEstimate, Versions,
    Status, Component, LlmProvider, LlmPurpose, FinishReason, METRICS_SCHEMA_VERSION, short_hash,
)
```

- `OllamaTimings.from_ollama_response(data)`: lee los tiempos del JSON de `/api/chat` e ignora el resto.
- `CostEstimate.from_tokens(input_tokens, output_tokens, rate)`: coste equivalente frente a una tarifa de referencia.
- `short_hash(text)`: sha256 de 16 caracteres para `input_hash`.
- `ScoreStats.from_scores(scores)`: máximo, mínimo y media de los scores; `None` si no hay pasajes.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest contracts/tests
```

Sin variables de entorno.

## Convenciones (patrón de la clase 4, `04_api_sdks_ia/Clases/02` y `06`)

- Todos los modelos con `ConfigDict(extra="forbid")`. Cada campo lleva `Field(description=...)` y sus restricciones
  (`ge=0`, `le=2`…); un test comprueba que ningún campo se queda sin descripción.
- Valores cerrados con `StrEnum`, la versión moderna de `class X(str, Enum)` de la clase 4.
- **Nombres de campo en inglés** (`latency_ms`, `input_tokens`); **descripciones y docstrings en español**.
- **Campos derivados** (`total_tokens`, `tokens_per_second`, `truncated`, `context_usage_pct`, los ms de Ollama…)
  son campos normales `= None` que rellena un `model_validator(mode="after")` con `check_or_fill`. **No uses
  `@computed_field`**: con `extra="forbid"` sale en `model_dump` pero hace fallar el `model_validate` de ese mismo
  volcado, y los JSONL se tienen que poder releer. Si el derivado ya viene relleno, se comprueba que cuadra.
- Fechas siempre con zona horaria. `status=error` obliga a `error_type`; `status=ok` lo prohíbe.
- Algo nuevo que medir sin cambiar el esquema → `attributes`. Si se cambia el esquema de forma incompatible,
  sube `METRICS_SCHEMA_VERSION`.

## Decisiones y trampas

- La `description` de un campo cuyo tipo es un enum **no puede ser igual al docstring del enum**: si lo es,
  Pydantic la quita del JSON Schema.
- Los tests construyen los modelos con `Model.model_validate(dict)`, no con `Model(**dict)`: así ty no se queja y
  es como llegan los datos al releer un JSONL.
- Los tiempos de `OllamaTimings` solo los da la API **nativa** de Ollama (`/api/chat`), no la compatible con
  OpenAI (`/v1`).
- **Clase de métricas nueva → regístrala en `METRICS_TYPES` de `telemetry/src/telemetry/event.py`.** Si no, se
  escribe pero no se puede releer. Un test de telemetry falla si se te olvida.
- Las métricas de un paso padre llevan **solo totales**: el detalle de cada paso hijo está en su propio span
  (`parent_span_id`). Por eso `AgentMetrics` no tiene lista de pasos y `ApiMetrics` no repite `latency_ms`
  (duración total) ni un `request_id` (es el `trace_id`).
- `ApiMetrics.http_method` usa `http.HTTPMethod` de la librería estándar, no un enum propio.
- Reglas entre campos: SQL rechazado ⇒ `rejection_reason` y nunca `execution_ms` ni `rows_returned`;
  RAG con pasajes ⇔ `scores`; `tools_used` sin repetidos y `tool_call_count` ≥ su longitud.
- `ruff format` también formatea los bloques de código de los `.md`: pásalo solo a `src/` y `tests/`.

## Pendiente (no olvidar)

Se decidió el 2026-10-31 no diseñarlos antes de tiempo: dependen de decisiones de su fase. Cada uno se crea
**en la fase indicada**, con su campo de métricas, y se tacha de aquí (y de la sección "Contratos pendientes"
del `AGENTS.md` raíz).

| Qué | Fase | Depende de |
|---|---|---|
| `ConversionMetrics` (archivo, formato, método, páginas, ms/página, tablas, páginas vacías) | 4 | Herramienta de conversión: referencia en el tema 7, sesión 3 (fila 4 del `AGENTS.md` raíz); decidir con Mario |
| `SqlResult` (SQL, columnas, filas + `metrics: SqlMetrics`) | 5 | Qué devuelve el validador y cómo viajan las filas |
| `AgentAnswer` (respuesta, fuentes, herramientas, abstención + `metrics: AgentMetrics`) | 6 | Forma de las fuentes (sección 7 de `PROYECTO.md`) |
| `SystemMetrics` (CPU, RAM, VRAM, GPU, modelos cargados), opcional | 7 | Si compensa medirlo por petición |
| `RagHit` / `RagResult` (pasaje, documento, página, score + `metrics: RagMetrics`) | 8 | Chunking (decisión pendiente 1) |
