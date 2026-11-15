# AGENTS.md — `agent/`

> Estado: **fase 6, agente mínimo hecho** (TRAVEL-006): grafo de LangGraph con `ChatOllama` y una sola tool,
> `query_db(question)` → `text2sql.ask()`, telemetría del turno y comando para probarlo. Falta del resto de la fase 6
> (ver «Lo que queda de la fase 6» en el ticket): citas y verificador, estrategia «plan cerrado» y casos dorados.

## Propósito

Decide si la pregunta necesita la BBDD (y, desde la fase 8, los documentos); llama a las herramientas y redacta la
respuesta con esos datos.

Depende de: `contracts`, `telemetry`, `text2sql` (`rag` desde la fase 8), `langgraph`, `langchain-ollama`, `ollama`,
`httpx`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/agent/__init__.py`: exporta `respond`.
- `src/agent/respond.py`: `respond()`, `INSTRUCTIONS`, `PROMPT_VERSION`, el mensaje fijo del límite de pasos, y las
  fuentes y los totales de `AgentMetrics` sacados de los mensajes del grafo.
- `src/agent/graph.py`: `build_agent`, el grafo de `construir_agente` (nodo `agent` → `ToolNode` → `agent`), con un
  span `llm.agent` alrededor de cada llamada al modelo.
- `src/agent/model.py`: `build_model()` (`ChatOllama` con la configuración del entorno), `as_component_error()`
  (errores de Ollama → `ComponentError`) y `llm_call_fields()` (los campos de `LlmCallMetrics`).
- `src/agent/tools.py`: la tool `query_db` (descripción para el modelo, lo que ve el modelo con `_for_model`, el
  `artifact` `QueryDbRun` y el candado de DuckDB).
- `src/agent/__main__.py`: el comando `python -m agent -q "…"`.
- `tests/conftest.py`: `con` de sesión con `open_db(FIXTURES_DIR)`, `log_dir` (telemetría a una carpeta temporal, en
  modo estricto) y `ollama` (el Ollama falso y la configuración).
- `tests/fake_ollama_server.py`: Ollama falso en la red: el agente llega por `httpx` y text2sql por `requests.post`,
  cada uno con su guion; también devuelve errores HTTP y lanza timeouts.
- `tests/test_agent_respond.py`, `tests/test_agent_ollama.py`, `tests/test_agent_cli.py`: un test por criterio de
  TRAVEL-006.
- `eval/`: vacío (casos dorados, siguiente ticket de la fase 6).

## Función pública

```python
from agent import respond
from contracts.errors import ComponentError

answer = respond("¿Cuántas reservas tiene C-001?", con=open_db())   # -> contracts.agent.AgentAnswer
```

- `AgentAnswer`: `answer` (texto del modelo), `status` (`ok` / `recursion_limit_reached`), `answered_without_data`
  (`true` si ninguna consulta salió bien; lo pone el código), `sources` (una por consulta `ok`: vistas, filas y su
  `sql`), `tools_used`, `versions` (`agent_prompt_v1`), `trace_id` y `metrics: AgentMetrics`.
- Al llegar al límite de pasos (`AGENT_RECURSION_LIMIT`, 20) devuelve «No he podido completar la consulta. Te paso
  con un compañero del equipo.» con `status = recursion_limit_reached`, sin lanzar error.
- Lanza `ComponentError` con `code`: `empty_question`, y los de Ollama (`ollama_unavailable`, `ollama_timeout`,
  `model_not_installed` con el `ollama pull`, `ollama_error`). Un `ComponentError` de text2sql sube tal cual.
- Telemetría (`logs/agent/`): un span `agent.respond` (`AgentMetrics`) por pregunta y, colgando de él, un `llm.agent`
  (`LlmCallMetrics`, con `OllamaTimings`) por llamada al modelo y los spans de text2sql. Nunca se guarda el texto de
  la pregunta ni el SQL.

**En qué se fija de clase**: `construir_agente` de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/grafo.py`
(grafo, `bind_tools`, instrucciones delante del historial, `ToolNode`), `conversar()` de `sesion3/agente_langgraph.py`
(`invoke`, `recursion_limit: 20`, la respuesta es el último mensaje, las instrucciones), `crear_modelo()` de
`comun/modelo_lc.py` (`temperature 0`), `@tool` de `comun/herramientas_lc.py`, el mensaje fijo de
`sesion1/agente_minimo.py`, la regla «si el dato no existe, dilo» de `02_capa_semantica.py` (tema 7 S2), la tool de
datos de `15_analista.py` (tema 7 S2), `estado_inicial()` de `flujo.py` y los errores de `ollama.py` (tema 7 S3).

**Desvíos** (ticket TRAVEL-006):
- `ChatOllama` (API nativa `/api/chat`) en vez de `ChatOpenAI` sobre `/v1`, para tener los tiempos de Ollama.
- Sin nodo `aprobacion` ni checkpointer (fases 12 y 7b).
- `GraphRecursionError` capturado: mensaje fijo y evento `agent.respond` con `status = error`
  (`error_type = recursion_limit_reached`). Como `invoke` pierde los mensajes al cortar, ese evento se guarda con las
  métricas base, sin recuentos.
- La tool devuelve al modelo SQL, filas y `truncated` de cada consulta, sin métricas; con `no_sql`, el texto de
  text2sql; con `sql_error`, las consultas buenas y el error del validador. `content_and_artifact` para que el código
  se quede con el `SqlResult` y lo que tardó (`QueryDbRun`).
- Descripción de la tool en una constante (`QUERY_DB_DESCRIPTION`) y no en el docstring, para que no le llegue al
  modelo con saltos de línea y sangría.
- `threading.Lock` alrededor de `ask()`: `ToolNode` ejecuta en paralelo las tools de una respuesta y DuckDB no admite
  dos llamadas a la vez en la misma conexión.
- Span `llm.agent` dentro del nodo `agent` (en clase el nodo no mide nada).
- `answered_without_data` y `status` en vez de `abstencion` y `escalar_a_humano` (la API decide si escala).
- El SQL va en cada fuente (`PROYECTO.md` §7 lo dejaba para `/trace`, pero la telemetría no guarda el SQL).
- `num_predict = 1024` y timeout de 600 s, como text2sql.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest agent/tests                       # sin Ollama: el modelo es falso
uv run python -m agent -q "¿Cuántas reservas tiene C-001?"              # con el Qwen real
uv run python -m agent -q "¿Cuántas reservas tiene C-001?" --no-trace   # sin el bloque de eventos de cada paso
```

El comando enseña `[PREGUNTA]`, `[RESPUESTA DEL AGENTE]` (el `AgentAnswer` entero en JSON, con las fuentes, su SQL y
los totales del turno) y `[MÉTRICAS]` (los eventos de esa traza, del agente y de text2sql). Opciones: `-q`, `--data`
(carpeta de los CSV, por defecto `data/`) y `--no-trace`. Si falla, escribe `[ERROR] código: mensaje` y sale con 1,
sin traza.

Variables de entorno (`.env.example`; todas tienen valor por defecto): `OLLAMA_BASE_URL` (sin `/v1`), `AGENT_MODEL`,
`OLLAMA_NUM_CTX` (8192) y `OLLAMA_KEEP_ALIVE` (30m), los mismos que text2sql, `AGENT_RECURSION_LIMIT` (20) y
`TEXT2SQL_MODEL` (la tool llama a text2sql desde este proceso).

Con el Qwen real en la GTX 1650 una pregunta con una consulta tarda ~28 s: ~10 s en las dos llamadas del agente, ~12 s
en el SQL de text2sql y ~5 s en el `schema()` de text2sql, que el comando paga en cada ejecución (un proceso por
pregunta; la API lo pagará una vez).

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
- Los tests no tocan Ollama: el fixture `ollama` sustituye `httpx.HTTPTransport.handle_request` (agente) y
  `requests.post` (text2sql). Los de Ollama caído usan `httpx` de verdad contra `http://127.0.0.1:1`.
- `ChatOllama` pide en streaming: el falso responde una línea NDJSON, y con nadie escuchando sale `httpx.ConnectError`
  (sin traducir por el cliente `ollama`), que `as_component_error` convierte en `ollama_unavailable`.
- LangGraph 1.2 tiene un límite por defecto de 10 007 pasos: sin `recursion_limit` propio, un modelo que siempre pide
  la tool no para nunca.
- Los nombres de la tool y de su parámetro, en inglés (`query_db(question)`), aunque los lea el modelo; la
  descripción, en castellano.
- ty no ve que `MessagesState` cumple el `StateLike` de LangGraph: `# ty: ignore[invalid-argument-type]` en
  `StateGraph(MessagesState)`.
