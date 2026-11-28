# AGENTS.md — `agent/`

> Estado: **fase 6, agente mínimo hecho** (TRAVEL-006): grafo de LangGraph con `ChatOllama` y una sola tool,
> `query_db(question)` → `text2sql.ask()`, telemetría del turno y comando para probarlo. **Guardarraíles hechos**
> (TRAVEL-011, tema 9 sesión 2): chat solo para clientes, entrada, herramientas en tres capas y salida, con
> interruptor. Falta del resto de la fase 6 (ver «Lo que queda de la fase 6» en TRAVEL-006): citas y verificador,
> estrategia «plan cerrado» (TRAVEL-013) y el examen del agente (TRAVEL-012).

## Propósito

Decide si la pregunta necesita la BBDD (y, desde la fase 8, los documentos); llama a las herramientas y redacta la
respuesta con esos datos.

Depende de: `contracts`, `telemetry`, `text2sql`, `database` (la conexión filtrada de la capa 2 y `open_db` del
comando; `rag` desde la fase 8), `langgraph`, `langchain-ollama`, `ollama`, `httpx`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/agent/__init__.py`: exporta `respond`.
- `src/agent/respond.py`: `respond()`, `INSTRUCTIONS`, `CLIENT_LINE`, `PROMPT_VERSION`, el mensaje fijo del límite
  de pasos, y las fuentes y los totales de `AgentMetrics` sacados de los mensajes del grafo. `respond()` se lee como
  el bucle de clase, con una función pequeña por paso (`_validated_question`, `_guard_input`, `_turn_connection`,
  `_run_graph`, `_checked_answer`…).
- `src/agent/guardrails.py`: la clase `Guardrails` (TRAVEL-011): `check_session`, `check_input`, `check_tool`
  (capa 1), `check_result`/`check_rows` (capa 3), `check_output` y el registro `log`; `luhn_valid`.
- `src/agent/profiles.py`: `PROFILES` (`{"client": ["query_db"]}`) y `profile(session)` (`unknown_role`).
- `src/agent/graph.py`: `build_agent`, el grafo de `construir_agente` (nodo `agent` → `ToolNode` → `agent`), con un
  span `llm.agent` alrededor de cada llamada al modelo.
- `src/agent/model.py`: `build_model()` (`ChatOllama` con la configuración del entorno), `as_component_error()`
  (errores de Ollama → `ComponentError`) y `llm_call_fields()` (los campos de `LlmCallMetrics`).
- `src/agent/tools.py`: la tool `query_db` (descripción para el modelo, lo que ve el modelo con `_for_model`, el
  `artifact` `QueryDbRun` y el candado de DuckDB), las capas 1 y 3 antes y después de text2sql, y `TOOL_BUILDERS`
  (el catálogo por nombre del que eligen los perfiles).
- `src/agent/__main__.py`: el comando `python -m agent -q "…"`.
- `tests/conftest.py`: `con` de sesión con `open_db(FIXTURES_DIR)`, `log_dir` (telemetría a una carpeta temporal, en
  modo estricto) y `ollama` (el Ollama falso y la configuración).
- `tests/fake_ollama_server.py`: Ollama falso en la red: el agente llega por `httpx` y text2sql por `requests.post`,
  cada uno con su guion; también devuelve errores HTTP y lanza timeouts.
- `tests/test_agent_respond.py`, `tests/test_agent_ollama.py`, `tests/test_agent_cli.py`: un test por criterio de
  TRAVEL-006 (desde TRAVEL-011, con `guardrails=False` / `--no-guardrails`).
- `tests/test_agent_guardrails.py`: un test por criterio de TRAVEL-011 (y `test_agent_cli.py`, el del AC-20).
- `eval/`: vacío (casos dorados, siguiente ticket de la fase 6).

## Función pública

```python
from agent import respond
from contracts.errors import ComponentError

session = Session(client_id="C-001")  # contracts.agent.Session: el cliente y su rol (por defecto "client")
answer = respond("¿Qué reservas tengo?", con=open_db(), session=session)  # -> contracts.agent.AgentAnswer
answer = respond("¿Cuántas reservas tiene C-001?", con=open_db(), guardrails=False)  # sin guardas ni cliente
```

- `AgentAnswer`: `answer` (texto del modelo), `status` (`ok` / `recursion_limit_reached`), `answered_without_data`
  (`true` si ninguna consulta salió bien; lo pone el código), `sources` (una por consulta `ok`: vistas, filas y su
  `sql`), `tools_used`, `blocks` (lo que bloquearon o modificaron los guardarraíles: tipo `input` / `tool` /
  `output` y motivo), `versions` (`agent_prompt_v2` desde TRAVEL-011), `trace_id` y `metrics: AgentMetrics`.
- Con los guardarraíles encendidos (por defecto) el cliente es obligatorio. Un bloqueo **no es un error**: el turno
  acaba con `status = ok` y el bloqueo en `blocks`.
- Al llegar al límite de pasos (`AGENT_RECURSION_LIMIT`, 20) devuelve «No he podido completar la consulta. Te paso
  con un compañero del equipo.» con `status = recursion_limit_reached`, sin lanzar error.
- Lanza `ComponentError` con `code`: `empty_question`, `missing_client`, `unknown_client` (el cliente no existe),
  `unknown_role` (un rol sin chat, p. ej. `manager`), y los de Ollama (`ollama_unavailable`, `ollama_timeout`,
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

## Guardarraíles (TRAVEL-011)

Como `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion2/guardarrailes.py` y el bucle de `comun/agente.py`:
«lo que no debe pasar se impide en el código, no se pide en el prompt». El chat es **solo para clientes** y nunca
salen datos de la empresa ni de otros clientes.

| Punto | Qué hace | Dónde |
|---|---|---|
| Sesión | cliente obligatorio y que exista (`missing_client`, `unknown_client`) | `Guardrails.check_session` |
| Perfil | el modelo solo recibe las tools de su rol (`PROFILES`); un rol sin chat, `unknown_role`. Se aplica siempre | `profiles.py` |
| Entrada | tarjeta (con Luhn), IBAN y DNI enmascarados antes del primer log; más de 2.000 caracteres no llega al modelo | `check_input` |
| Herramientas, capa 1 | la pregunta para `query_db` nombra un cliente, reserva o incidencia de otro → no se ejecuta | `check_tool` |
| Herramientas, capa 2 | text2sql consulta una conexión que solo ve las filas del cliente (también sus vuelos) | `database.client_filter.open_client_filtered_connection`, desde `respond()` |
| Herramientas, capa 3 | una fila con el id de otro cliente bloquea el resultado entero | `check_result` / `check_rows` |
| Salida | el email o el nombre completo de otro cliente → respuesta de clase; lo compartido con él, no | `check_output` |

- **El interruptor** (`guardrails=False`, `--no-guardrails`) apaga solo los guardas, como `crear_agente(guardas=…)`
  de `permisos.py`: las instrucciones (con la línea del cliente si hay sesión) y los perfiles no cambian. Así
  TRAVEL-012 mide con y sin ellos cambiando una sola cosa.
- **Una llamada bloqueada** devuelve «Acción no permitida: …» al modelo y, como artifact, el `Block` de su bloqueo:
  no cuenta como fuente ni en `tools_used`; un error de LangGraph (tool inventada, argumentos mal) sí cuenta.
- **Desvíos** (detalle en el ticket): capa 1 sobre una pregunta en lenguaje natural (se buscan los ids); capa 2 sin
  ejemplo en clase (esquema `client_filtered_schema` y `search_path` en un cursor; el cómo vive en `database/`);
  salida con email y nombre en vez de teléfono y dirección, sin el filtro de «información interna» (LLM07);
  `unknown_client` y `unknown_role`; sesión tipada (`Session`) en vez del `dict` `contexto`.
- **El esquema de text2sql** no se genera nunca desde la conexión filtrada (saldrían los valores de un cliente y se
  guardaría para todos): `open_client_filtered_connection` lo prepara con la conexión completa y pone su misma huella
  en el cursor.
- **El dueño de cada id** se recuerda durante el turno (`Guardrails._owner`): con `data/`, la capa 3 sobre 50 filas
  pasaba de ~1 s a ~20 ms.

**Límites conocidos y pendientes:**
- La capa 3 reconoce las columnas por su nombre: con un alias (`cliente_id AS id`) no la ve. La capa 2 sigue impidiendo
  que haya filas ajenas.
- Si el cliente pregunta por la empresa, la cifra es la suya (capa 2), pero el modelo podría presentarla como de la
  empresa: lo cubren las instrucciones y se mide en TRAVEL-012.
- Con dos clientes que se llaman igual, el nombre del otro no se bloquea (es el del propio cliente).
- **Conexión compartida (fase 7):** el esquema filtrado tiene un nombre fijo y es de la base: dos turnos a la vez de
  clientes distintos sobre la misma conexión se pisarían. La API tendrá que abrir una por sesión (o un nombre por turno).
- **Fase 8:** las capas 1 y 3 se llaman desde dentro de `query_db`; con la segunda tool, un envoltorio común alrededor
  de todas, como el bucle de `comun/agente.py` (decidido con Mario el 2026-11-28).

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest agent/tests                       # sin Ollama: el modelo es falso
uv run python -m agent -q "¿Qué reservas tengo?" --client C-001              # con el Qwen real y los guardarraíles
uv run python -m agent -q "¿Qué reservas tengo?" --client C-001 --no-trace   # sin el bloque de eventos de cada paso
uv run python -m agent -q "¿Cuántas reservas tiene C-001?" --no-guardrails   # sin guardarraíles ni cliente
```

El comando enseña `[PREGUNTA]`, `[RESPUESTA DEL AGENTE]` (el `AgentAnswer` entero en JSON, con las fuentes, su SQL y
los totales del turno) y `[MÉTRICAS]` (los eventos de esa traza, del agente y de text2sql). Opciones: `-q`, `--data`
(carpeta de los CSV, por defecto `data/`), `--no-trace`, `--client` (el cliente de la sesión; obligatorio con los
guardarraíles) y `--no-guardrails`. Si falla, escribe `[ERROR] código: mensaje` y sale con 1,
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
