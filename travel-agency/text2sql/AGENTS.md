# AGENTS.md — `text2sql/`

> Estado: **fase 5, línea base hecha**: validador (`guard.py`, TRAVEL-002) y `ask()` con Qwen3-4B, bucle de
> corrección, telemetría y comando para probarlo (TRAVEL-005). Sin fine-tuning (fase 9, opcional).

## Propósito

Traduce una pregunta a SQL con Qwen3-4B, lo valida (solo `SELECT`, solo vistas permitidas) y lo ejecuta en DuckDB (sección 6).

Depende de: `contracts`, `telemetry`, `database`, `pandas`, `requests`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/text2sql/__init__.py`: exporta `ask` y `ComponentError`.
- `src/text2sql/loop.py`: `ask()`, el bucle (el modelo pide `run_sql`, el código lo valida y lo ejecuta) y la tool.
- `src/text2sql/ollama.py`: `chat()` contra `/api/chat` con sus métricas, y `ComponentError` (errores con código).
- `src/text2sql/prompt.py`: instrucciones + `schema()` + `GUIDE`, y `PROMPT_VERSION`.
- `src/text2sql/guard.py`: `run_safe_sql(con, query) -> (ok, texto)`, la barrera del SQL del modelo.
- `src/text2sql/__main__.py`: el comando `python -m text2sql -q "…"`.
- `tests/conftest.py`: fixture `con` de sesión con `open_db()` (la de `database/tests` no llega aquí), `log_dir`
  (telemetría a una carpeta temporal, en modo estricto) y `fake_ollama`.
- `tests/fake_ollama.py`: Ollama falso que responde como `/api/chat` y guarda cada petición.
- `tests/test_text2sql_guard.py` (TRAVEL-002), `tests/test_text2sql_ask.py` y `tests/test_text2sql_cli.py`
  (TRAVEL-005): un test por criterio de cada ticket.
- `dataset/`, `finetune/`, `eval/`: vacíos. `finetune/` es de la fase 9, opcional y aplazada (2026-11-08).

## Función pública

```python
from text2sql import ask, ComponentError

result = ask("¿Cuántas reservas tiene C-001?", con=open_db())   # -> contracts.sql.SqlResult
```

- Devuelve las consultas con su SQL, columnas, filas (recortadas a 50, con `truncated`) y sus `SqlMetrics`.
  **No redacta**: eso lo hace el agente (fase 6), que la llamará desde la tool `consultar_bbdd(pregunta)`.
- `status`: `ok`; `no_sql` (el modelo respondió con texto, en `model_text`, p. ej. «ese dato no existe»);
  `sql_error` (tras los reintentos quedó un SQL sin corregir; el último mensaje del validador en `error`).
- Como mucho **3 llamadas** al modelo (1 + 2 reintentos). El error del validador vuelve al modelo para que corrija.
- Si falla Ollama lanza `ComponentError` con `code`: `ollama_unavailable`, `ollama_timeout`,
  `model_not_installed` (el mensaje dice el `ollama pull`) u `ollama_error`.
- Telemetría (`logs/text2sql/`): un span `text2sql.ask` por pregunta y, colgando de él, un `llm.text2sql`
  (`LlmCallMetrics`, con `OllamaTimings`) por llamada y un `sql.run` (`SqlMetrics`) por cada SQL. Nunca se guarda
  el texto de la pregunta ni el SQL: solo longitudes y un hash.

**En qué se fija de clase**: el bucle de `conversar()` de
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/01_preguntar_datos.py` (mismos argumentos
aceptados, `consulta`/`query`/`sql`), el resultado sin redactar de `preguntar()` de `sesion_3/asistente/datos.py`,
el cliente y los errores de `sesion_3/asistente/ollama.py` (`requests`, `think: false`, `temperature 0`,
`num_predict 1024`, `timeout 600`) y el prompt de `construir_system_prompt()` de `sesion_2/02_capa_semantica.py`.

**Desvíos** (ticket TRAVEL-005): 3 llamadas como máximo (en clase, 4–6 rondas); se ejecutan todas las consultas de
una respuesta; texto sin SQL → `no_sql` con el texto; códigos de error en inglés; `ComponentError` en vez de
`ErrorComponente`; instrucciones sin la parte de redactar ni `PERIODOS`; el prompt se genera **una vez por
conexión** (`schema()` tarda ~5 s); un evento `SqlMetrics` por SQL.

## El validador (`guard.py`)

**Igual que en clase**: `run_safe_sql` es `ejecutar_sql_seguro` de
`07_llm_open_source/clase_01/Ejercicios/practica/08_herramienta_sql.py`, línea a línea y con los mismos mensajes:
consulta vacía, error de sintaxis (`extract_statements`), una sola sentencia, solo `SELECT`, error al ejecutar,
`MAX_ROWS = 50` con aviso, decimales a 2 cifras y JSON con `fetchdf()` + `to_json()`. Única diferencia fuera de la
lista blanca: `cast(str, …)` en `to_json()`, que pide `ty` (el tipo de pandas dice `str | None`).

**Desvío: lista blanca de vistas** (`PROYECTO.md` §6), entre la comprobación de `SELECT` y la ejecución:
- Vistas permitidas = lo que hay en `main`, con la consulta de `esquema()` de DropLab S2
  (`information_schema.tables WHERE table_schema = 'main'`): el modelo solo puede leer lo que se le enseña.
  No hay lista escrita a mano; si se añade una vista en `database`, queda permitida.
- Las tablas del SQL salen de su árbol: `json_serialize_sql` de DuckDB (sin referencia en el repo; acordado).
  Se mira cada nodo del `FROM` (claves `from_table`, `left`, `right`) y solo se aceptan los tipos conocidos:
  `BASE_TABLE` si es una vista (con su esquema: `crudo.clientes` no lo es), y `JOIN`, `SUBQUERY`, `EXPRESSION_LIST`
  (`VALUES`) y `EMPTY` (sin `FROM`), que se miran por dentro. **Cualquier otro tipo se rechaza**: `TABLE_FUNCTION`
  (`duckdb_tables()`, `read_csv_auto()`), `SHOW_REF` (`SHOW ALL TABLES`) o uno nuevo de DuckDB. Los nombres de CTE
  sin esquema no cuentan como tablas.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest text2sql/tests                       # sin Ollama: el modelo es falso
uv run python -m text2sql -q "¿Cuántas reservas canceladas tiene C-001?"   # con el Qwen real
```

El comando enseña `[PREGUNTA]`, `[LO QUE RECIBIRÍA EL AGENTE]` (el `SqlResult` en JSON) y `[MÉTRICAS]` (los eventos
de esa pregunta, sin campos vacíos). Opciones: `-q` y `--data` (carpeta de los CSV, por defecto `data/`). Si Ollama
falla, escribe `[ERROR] código: mensaje` y sale con 1, sin traza.

Variables de entorno (`.env.example`; todas tienen valor por defecto): `OLLAMA_BASE_URL` (sin `/v1`),
`TEXT2SQL_MODEL`, `OLLAMA_NUM_CTX` (8192) y `OLLAMA_KEEP_ALIVE` (30m), los mismos que usará el agente.

En la GTX 1650 (4 GB) el 4B va 72 % en CPU: la primera pregunta tarda ~150 s (cargar el modelo y leer el prompt
de ~3 000 tokens) y las siguientes ~17 s (8 s generando a ~5 tokens/s y ~6 s de `schema()`, que el comando
genera en cada ejecución).

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
- `pandas` se añadió solo para ejecutar el mismo `fetchdf()` / `to_json()` que en clase; `requests`, para el mismo
  cliente `/api/chat` de S3.
- Con aviso de recorte, el texto **no es JSON entero** (el aviso va detrás, como en clase): `loop.py` lo quita con
  `TRUNCATION_NOTE` de `guard.py` antes de leer las filas. Las columnas salen de la primera fila: con 0 filas, `[]`.
- Los tests no tocan Ollama: `fake_ollama` sustituye `text2sql.ollama.requests.post`. Los de Ollama caído usan
  `requests` de verdad contra `http://127.0.0.1:1`.
- `ask()` no devuelve su `trace_id`: el comando toma el del último `text2sql.ask` del archivo de hoy.
- `main.v_incidencias` (con el esquema delante) se rechaza: el esquema nunca le enseña `main.` al modelo.
- `enable_external_access = false` de `open_db()` es la segunda barrera: `read_csv_auto()` ya lo para la lista
  blanca antes de ejecutar.
- Ninguna vista llega a 50 filas: el test del recorte usa un `CROSS JOIN` de dos vistas (121 filas).
