# AGENTS.md — `telemetry/`

> Estado: **fase 1b**. Hechos `span()`, `write_event()` / `read_events()`, `get_logger()` y el evento JSONL
> versionado. Falta el exportador a MLflow (fase 11).

## Propósito

Las mismas piezas de observabilidad para todos los paquetes (sección 8 de [`../PROYECTO.md`](../PROYECTO.md)):
cronometrar cada paso, escribir su evento JSONL y un log de texto con el `trace_id`. Depende de: `contracts`.

## Archivos clave

```
src/telemetry/
├── __init__.py   # reexporta todo lo público
├── config.py     # TelemetryConfig, configure(), get_config()
├── context.py    # trace y span activos (contextvars) + new_trace_id / new_span_id
├── event.py      # Event, EVENT_SCHEMA_VERSION, METRICS_TYPES, git_commit()
├── writer.py     # write_event, read_events, events_path
├── logger.py     # get_logger, close_log_files
└── span.py       # span(), Span
```

## API pública

```python
from telemetry import span, get_logger, configure, read_events, events_path
from contracts.metrics import Component, LlmCallMetrics

with span("sql.validar", component=Component.text2sql, input_text=sql) as s:
    s.output_text = resultado
    s.attributes["vistas"] = 2
    if prohibido:
        s.reject("ddl_prohibido")          # status=rejected sin excepción

with span("llm.text2sql", component=Component.text2sql, metrics_cls=LlmCallMetrics) as s:
    s.fields.update(provider="ollama", model="qwen3:4b-instruct", input_tokens=600, ...)
resultado.metrics = s.metrics              # las métricas validadas, para el campo de métricas del resultado
```

- `span(name, *, component, metrics_cls=BaseMetrics, input_text=None, versions=None, trace_id=None)`:
  - sin traza activa empieza una (con `trace_id` si se pasa: lo hará la API); con traza activa cuelga del span abierto;
  - una excepción del bloque → `status=error`, `error_type` = nombre de la clase, mensaje recortado a 500; se relanza;
  - al cerrar valida `metrics_cls` con los campos del span + `s.fields` y escribe el evento.
- `get_logger(name)`: consola + `<log_dir>/<componente>/app.log` (rotado por tamaño, 5 MB × 3). El componente es la
  primera parte del nombre (`"text2sql.validar"` → `text2sql/`). Formato del tema 4 con `[trace_id]` (`-` fuera de traza).
- `configure(log_dir=..., environment=..., strict=...)`: por defecto `logs/`, `local`, `strict=False`. La API lo
  llamará con lo de su `config.yml`.
- `read_events(path)` → `list[Event]`, cada métrica revalidada con su clase.

## El evento

Una línea por span en `<log_dir>/<componente>/events-AAAA-MM-DD.jsonl` (día del `started_at`, en UTC):

```json
{"event_schema_version": "event_v1", "environment": "local", "git_commit": "886eeb1",
 "metrics_type": "LlmCallMetrics", "metrics": {"trace_id": "4bf9…", "span_id": "00f0…", "name": "llm.text2sql", "...": "..."}}
```

`metrics_type` dice con qué clase releer `metrics` (`extra="forbid"` no deja leer una `LlmCallMetrics` como
`BaseMetrics`). **Cada clase nueva de métricas de `contracts` se añade a `METRICS_TYPES` en `event.py`**; si no,
el span escribe bien pero `read_events` falla al releerlo. `test_every_metrics_class_in_contracts_is_registered`
falla si una clase exportada por `contracts.metrics` no está registrada.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest telemetry/tests
```

Sin variables de entorno. `tests/conftest.py` apunta cada test a su `tmp_path` con `strict=True` y cierra los
archivos de log al acabar; los tests de otros paquetes que abran spans deberían hacer lo mismo.

## Decisiones y trampas

- **La telemetría nunca rompe la petición**: si la métrica no valida o no se puede escribir, se registra en
  `telemetry/app.log` y se sigue. Con `strict=True` (tests) se lanza.
- **Una llamada a un LLM que falla** antes de tener tokens no llena `LlmCallMetrics`: el evento de error se guarda
  con `BaseMetrics` y `attributes["expected_metrics_type"]`. Así no se pierde justo el evento más importante.
- `input_text` / `output_text` **nunca se guardan**: solo su longitud y el hash de la entrada (datos de clientes).
- `ended_at` = `started_at` + `latency_ms` (de `perf_counter`), no otro `now()`: si el reloj salta, no queda antes.
- `git_commit` se calcula una vez por proceso (`@cache`); `None` si no hay git.
- Los loggers **no propagan**: si `text2sql` y `text2sql.validar` tienen handlers, las líneas saldrían dobles. Por
  eso `caplog` de pytest no las ve: los tests leen `app.log`.
- Un solo `RotatingFileHandler` por archivo, compartido entre loggers del mismo componente: si dos rotan el mismo
  archivo se pisan.
- `context.py` está aparte de `span.py` porque lo usan `span.py` y `logger.py`, y `span.py` usa `logger.py`.
- Desvíos del tema 4: el evento es un modelo Pydantic validado (allí un `dict`), el logger lleva `trace_id` y archivo
  (allí solo consola). La forma de escribir (una línea JSON añadida, crea la carpeta) es la misma.
- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
