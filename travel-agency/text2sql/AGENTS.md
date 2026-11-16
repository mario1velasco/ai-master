# AGENTS.md — `text2sql/`

> Estado: **fase 5, línea base hecha**: validador (`guard.py`, TRAVEL-002) y `ask()` con Qwen3-4B, bucle de
> corrección, telemetría y comando para probarlo (TRAVEL-005), y la herramienta de evaluación (TRAVEL-007). Falta el
> examen real y la primera medida (TRAVEL-008). Sin fine-tuning (fase 9, opcional).

## Propósito

Traduce una pregunta a SQL con Qwen3-4B, lo valida (solo `SELECT`, solo vistas permitidas) y lo ejecuta en DuckDB (sección 6).

Depende de: `contracts`, `telemetry`, `database`, `pandas`, `requests`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/text2sql/__init__.py`: exporta `ask`.
- `src/text2sql/loop.py`: `ask()`, el bucle (el modelo pide `run_sql`, el código lo valida y lo ejecuta) y la tool.
- `src/text2sql/ollama.py`: `chat()` contra `/api/chat` con sus métricas y sus errores con código
  (`ComponentError`, que vive en `contracts.errors` desde TRAVEL-006).
- `src/text2sql/prompt.py`: instrucciones + `cached_schema()` + `GUIDE`, y `PROMPT_VERSION`.
- `src/text2sql/guard.py`: `run_safe_sql(con, query) -> (ok, texto)`, la barrera del SQL del modelo.
- `src/text2sql/__main__.py`: el comando `python -m text2sql -q "…"`.
- `src/text2sql/evaluation/` (TRAVEL-007): `exam.py` (`load_exam`, `view`), `evaluate.py` (`evaluate_case`,
  `evaluate_trajectory`, `equal`, `normalize`), `measure.py` (`run_cases`, `compute_metrics`, `percentile`, informe) y
  `__main__.py` (el comando `python -m text2sql.evaluation`). Los exámenes, en `evaluation/exams/` (TRAVEL-008).
- `evaluation_results/`: un JSON por medida (`<examen>_<fecha>.json`), versionado: es la evidencia de la línea base.
- `tests/conftest.py`: fixture `con` de sesión con `open_db()` (la de `database/tests` no llega aquí),
  `session_schema_cache` (los esquemas guardados, a una carpeta temporal de la sesión), `log_dir` (telemetría a una
  carpeta temporal, en modo estricto), `fake_ollama` y `data_con` (la base de `data/`, la que se mide: TRAVEL-007).
- `tests/fake_ollama.py`: Ollama falso que responde como `/api/chat` y guarda cada petición; una excepción en
  `answers` se lanza como haría `requests.post` (p. ej. `requests.exceptions.Timeout()` → `ollama_timeout`).
- `tests/test_text2sql_guard.py` (TRAVEL-002), `tests/test_text2sql_ask.py` y `tests/test_text2sql_cli.py`
  (TRAVEL-005), `tests/test_text2sql_schema_cache.py` (TRAVEL-009, por `ask()`) y
  `tests/test_text2sql_evaluation.py` (TRAVEL-007): un test por criterio de cada ticket.
- `dataset/`, `finetune/`: vacíos, de la fase 9, opcional y aplazada (2026-11-08).

## Función pública

```python
from contracts.errors import ComponentError
from text2sql import ask

result = ask("¿Cuántas reservas tiene C-001?", con=open_db())   # -> contracts.sql.SqlResult
```

- Devuelve las consultas con su SQL, columnas, filas (recortadas a 50, con `truncated`) y sus `SqlMetrics`.
  **No redacta**: eso lo hace el agente (fase 6), que la llamará desde la tool `query_db(question)`.
- `trace_id`: la traza de la pregunta; con ella se sacan sus eventos (tokens, tiempos) de `logs/text2sql/`.
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
`ErrorComponente`; instrucciones sin la parte de redactar ni `PERIODOS`; un evento `SqlMetrics` por SQL.
El prompt se construye en cada pregunta, como en clase, pero el esquema sale de `cached_schema()` de `database`
(guardado por huella en memoria y en disco, TRAVEL-009): ~1 ms en vez de ~5 s. Hasta TRAVEL-009 se generaba una vez
por conexión con `@cache`, que retenía cada conexión para siempre.

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
`TEXT2SQL_MODEL`, `OLLAMA_NUM_CTX` (8192) y `OLLAMA_KEEP_ALIVE` (30m), los mismos que usará el agente; y
`PRICE_PER_MILLION_TOKENS` (0.5 €) para el coste de la evaluación.

En la GTX 1650 (4 GB) el 4B va 72 % en CPU: la primera pregunta tarda ~150 s (cargar el modelo y leer el prompt
de ~3 000 tokens) y las siguientes ~17 s (8 s generando a ~5 tokens/s y ~6 s de `schema()`, que el comando
generaba en cada ejecución; medido antes de TRAVEL-009, que lo guarda en `database/.cache/` y lo deja en ~1 ms).

## Evaluación (`python -m text2sql.evaluation`, TRAVEL-007)

Pasa un examen por `ask()` varias veces, corrige cada intento con código y da las métricas. Desde `travel-agency/`:

```bash
uv run python -m text2sql.evaluation --exam battery --view               # el examen, sin llamar al modelo
uv run python -m text2sql.evaluation --exam battery --repetitions 3      # cada pregunta 3 veces
uv run python -m text2sql.evaluation --exam final_test --repetitions 3   # el examen reservado
uv run python -m text2sql.evaluation --questions N01 N02                 # solo esas preguntas
```

- Opciones: `--exam` (`battery` por defecto, o `final_test`), `--repetitions` (1), `--questions` (ids) y `--view`
  (cada pregunta con su categoría, trampa, vistas y resultado de referencia; marca «0 filas, revisar» las vacías).
  La base es siempre la de `data/`.
- **Examen** (`src/text2sql/evaluation/exams/<examen>.json`): una lista de preguntas con `id`, `category` (`normal`,
  `edge`, `adversarial`), `trap` (una trampa de `PROYECTO.md` §3 o `null`), `question` (en castellano: la lee el
  modelo) y, o bien `sql` (la referencia), o bien `must_deny: true` (imposible). Los adversarios no llevan ninguna.
  Al cargarlo, la referencia se ejecuta con `run_safe_sql` y salen `expected_rows` y `expected_views`. Un id repetido
  o una referencia que no pasa el validador paran el comando con `[ERROR] examen …: <id>: <motivo>` y código 1, sin
  llamar al modelo.
- **Corrección** (`evaluate_case`): se corrige la **última** consulta. Aprueba si tiene el mismo número de filas que
  la referencia y cada fila de la referencia casa con una fila **libre** distinta del intento que contiene todos sus
  valores (números ±0,011, textos con `normalize`), sin mirar nombres de columna: tolera columnas de más y otro
  orden. Una imposible aprueba solo con `no_sql`; un adversario, si ninguna consulta devuelve filas.
- **Salida**: una línea por intento (✅/❌, segundos, tokens, estado, motivo y, si suspende, su vista), el informe de
  métricas, la línea «Suspensos», los aciertos por categoría y por trampa, y la ruta del JSON guardado en
  `evaluation_results/` (fecha, modelo, versión del prompt, examen, k, métricas y una fila por intento con su
  `trace_id`, estado, SQL, aprobado/motivo y trayectoria).
- Los tokens, la latencia y el arranque en frío de cada intento salen de los eventos de su `trace_id`.

**Métricas del informe** (cada una lleva también un comentario junto a su cálculo, en `measure.py`):

| Métrica | Qué mide | Cómo se calcula | Cómo leerla |
|---|---|---|---|
| Tasa de éxito | ¿Responde bien? (calidad) | aprobados / intentos | La nota del examen. Baja → mirar «Suspensos» y el desglose por trampa |
| pass^k | ¿Responde bien **siempre**? (fiabilidad) | preguntas con sus k intentos aprobados / preguntas | La que importa en producción: debe acercarse a la tasa de éxito. Por debajo → respuestas inestables |
| pass@k | ¿Sabe hacerlo alguna vez? | preguntas con al menos un intento aprobado / preguntas | Alta con pass^k baja: sabe pero es inestable (más ejemplos). Baja: no sabe (prompt o vistas) |
| Latencia p50 / p95 | Cuánto tarda una pregunta | mediana y percentil 95 de los segundos del span `text2sql.ask`, **sin** los intentos con arranque en frío ni los errores de Ollama | Se mira el p95 (lo que espera el cliente cuando va mal). ~17 s en la GTX 1650 |
| Disponibilidad | Cuántas veces pudo responder (bien o mal) | 1 − (errores de Ollama + `sql_error` fuera de los adversarios) / intentos | Debe ser ~100 %. Si baja: Ollama caído o el modelo no consigue un SQL válido en 3 llamadas |
| Tokens/pregunta | Tamaño del prompt y de los reintentos | tokens de entrada + salida de las llamadas / intentos con respuesta | Sube con el esquema en el prompt o con más correcciones |
| Coste por 1.000 preguntas | Lo que costaría con un proveedor de pago | tokens × `PRICE_PER_MILLION_TOKENS` / intentos con respuesta (en local es 0) | Para comparar modelos o prompts |
| Coste por 1.000 casos resueltos | Lo que cuesta una respuesta **buena** | coste de todos los intentos / aprobados | Un modelo barato que falla mucho sale caro |
| Aprobados a la primera | Si el modelo acierta **sin la ayuda del validador** | aprobados sin ningún SQL rechazado / intentos | Con «tras corregirse» suma la tasa de éxito. Cuanto más alta, mejor |
| Aprobados tras corregirse | Aciertos gracias al error que devolvió el validador | aprobados con algún SQL rechazado / intentos | Alta → el prompt deja escribir SQL que no vale (aunque al final acierte, cuesta llamadas y segundos) |
| Llamadas al modelo por intento | Pasos de cada pregunta (1 a 3) | media de `llm_calls` | Ideal cerca de 1; cada llamada suma ~8 s y tokens |
| Intentos con algún SQL rechazado | El «Cumple reglas» de `PROYECTO.md` §6 al revés | intentos con un SQL parado por el validador / intentos con respuesta | Debe ser bajo. Sube → el modelo intenta tablas crudas, escribir o vistas que no existen: reforzar las reglas del prompt |
| Suspensos (recuento) | **Por qué** falla, no cuánto | cada suspenso en «vista equivocada» (no usó las vistas de la referencia), «vista correcta, filas malas» u «otros» (imposibles, adversarios, errores de Ollama, sin consultas) | Vista equivocada → esquema o ejemplos del prompt. Filas malas → reglas de las trampas |
| Por categoría / por trampa | Dónde falla | aprobados / intentos de cada grupo | Una trampa baja dice qué regla del prompt o qué vista mejorar |

**En qué se fija de clase**: `medir.py` del tema 9 (`run_cases` = `ejecutar_casos`, `compute_metrics` =
`calcular_metricas`, `percentile` = `percentil`, `print_metrics` = `imprimir_metricas`, `print_breakdown` =
`por_categoria`, `PRICE_PER_MILLION_TOKENS` = `PRECIO_MILLON_TOKENS`, JSON con métricas y filas), `evaluar.py`
(`evaluate_trajectory` = `evaluar_trayectoria`), `comun/evaluacion.py` (`normalize` = `normalizar`), `04_examen.py`
del tema 7 (`load_exam` = `cargar`, `view` = `ver`, `--questions`, `must_deny` = `debe_negar`) y `06_evaluar.py`
(`equal` = `igual` con ±0,011, guardar con fecha y modelo).

**Desvíos** (ticket TRAVEL-007): se corrige contra las filas del SQL de referencia, no buscando cifras en un texto
(`text2sql` no redacta); emparejamiento voraz de filas (caso raro: un intento correcto con columnas de más puede
suspender, y se ve en el motivo); dos exámenes, no tres; las vistas esperadas salen del SQL y son diagnóstico, no
aprueban ni suspenden; `trace_id` en `SqlResult` y tokens/latencia de los eventos del archivo de hoy; arranque en frío
por `OllamaTimings.cold_start`; un `ComponentError` suspende y cuenta como no disponible pero no entra en latencia ni
tokens; un `sql_error` no resta disponibilidad en los adversarios; sin `rich`; tarifa con `CostRate` en EUR; claves,
opciones y nombres en inglés.

**Regla del examen reservado**: `final_test` no se usa para ajustar el prompt ni los ejemplos, solo para medir.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
- `pandas` se añadió solo para ejecutar el mismo `fetchdf()` / `to_json()` que en clase; `requests`, para el mismo
  cliente `/api/chat` de S3.
- Con aviso de recorte, el texto **no es JSON entero** (el aviso va detrás, como en clase): `loop.py` lo quita con
  `TRUNCATION_NOTE` de `guard.py` antes de leer las filas. Las columnas salen de la primera fila: con 0 filas, `[]`.
- Los tests no tocan Ollama: `fake_ollama` sustituye `text2sql.ollama.requests.post`. Los de Ollama caído usan
  `requests` de verdad contra `http://127.0.0.1:1`.
- `ask()` devuelve su `trace_id` (TRAVEL-007): el comando `-q` y la evaluación buscan con él los eventos de esa
  pregunta en el archivo de hoy de `logs/text2sql/`.
- `main.v_incidencias` (con el esquema delante) se rechaza: el esquema nunca le enseña `main.` al modelo.
- `enable_external_access = false` de `open_db()` es la segunda barrera: `read_csv_auto()` ya lo para la lista
  blanca antes de ejecutar.
- Ninguna vista llega a 50 filas: el test del recorte usa un `CROSS JOIN` de dos vistas (121 filas).
