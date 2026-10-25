# AGENTS.md — `contracts/`

> Estado: **fase 1a**. Hechas las métricas comunes (`BaseMetrics`) y las de una llamada a un LLM (`LlmCallMetrics`).
> Faltan las de SQL, RAG, agente, API y conversión, y los resultados (`SqlResult`, `RagHit`, `AgentAnswer`…).

## Propósito

Esquemas Pydantic compartidos por todos los paquetes. Cada resultado de cada paquete lleva sus métricas
(sección 8 de [`../PROYECTO.md`](../PROYECTO.md)). No depende de ningún otro paquete del proyecto: solo de `pydantic`.

## Archivos clave

```
src/contracts/metrics/
├── __init__.py      # reexporta todo lo público
├── enums.py         # Status, Component
├── base.py          # BaseMetrics, Versions, METRICS_SCHEMA_VERSION, short_hash, check_or_fill
└── llm/
    ├── enums.py     # LlmProvider, LlmPurpose, FinishReason
    ├── ollama.py    # OllamaTimings (tiempos en ns de la API nativa de Ollama + derivados)
    ├── cost.py      # CostRate, CostEstimate (misma fórmula que estimate_cost de triage)
    └── call.py      # LlmCallMetrics(BaseMetrics)
```

## API pública

```python
from contracts.metrics import (
    BaseMetrics, LlmCallMetrics, OllamaTimings, CostRate, CostEstimate, Versions,
    Status, Component, LlmProvider, LlmPurpose, FinishReason, METRICS_SCHEMA_VERSION, short_hash,
)
```

- `OllamaTimings.from_ollama_response(data)`: lee los tiempos del JSON de `/api/chat` e ignora el resto.
- `CostEstimate.from_tokens(input_tokens, output_tokens, rate)`: coste equivalente frente a una tarifa de referencia.
- `short_hash(text)`: sha256 de 16 caracteres para `input_hash`.

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
