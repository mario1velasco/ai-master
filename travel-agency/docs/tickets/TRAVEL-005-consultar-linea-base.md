# TRAVEL-005 · Pregunta → SQL con Qwen3-4B: `text2sql.ask()` línea base

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`text2sql/`, `contracts/`) |
| Estado | Hecho  |
| Creado | 2026-11-08 |
| Etiquetas | text2sql, llm, ollama, fase-5 |

## Historia de usuario

**Como** agente de Viajes Nimbo (fase 6), **quiero** pasar a `text2sql` una pregunta en lenguaje natural y recibir
el SQL que ha escrito Qwen3-4B junto con sus filas, ya validado y ejecutado sobre las vistas, **para que** pueda
redactar la respuesta con datos reales sin ver el esquema ni escribir SQL yo mismo.

## Contexto

`text2sql/` solo tiene el validador (`guard.py`, `run_safe_sql`, TRAVEL-002). Falta la parte que habla con el modelo.
Se sigue la **opción A** acordada con Mario: el agente de la fase 6 (LangGraph, decisión 5) tendrá una tool
`consultar_bbdd(pregunta)` que llama a `text2sql.ask()`, y es el agente quien redacta. Es el mismo reparto que
`S3/asistente/flujo.py` → `datos.preguntar()` en clase: un bucle propio que escribe SQL y un paso aparte que redacta.
Escalones 1 y 3 de `PROYECTO.md` §6 (diccionario en el prompt + error devuelto al modelo); sin fine-tuning (fase 9
opcional) y sin ejemplos dinámicos (escalón 2, solo si la evaluación lo pide).

**Referencias leídas:**
- `07_llm_open_source/clase_01/Ejercicios/practica/08_herramienta_sql.py` (tool `ejecutar_sql(consulta)`, prompt con
  esquema generado, `ejecutar_sql_seguro`) y `07_herramienta_funcion.py` (`conversar_con_herramientas`: el bucle,
  los `tool_calls`, varias llamadas por respuesta, llamada escrita como texto).
- `07_llm_open_source/clase_01/Ejercicios/practica/04_conectar_ollama.py` (`/api/chat`, `num_ctx`, tiempos de Ollama).
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/01_preguntar_datos.py` (`conversar()`: error de
  DuckDB devuelto al modelo, `temperature 0`, `think false`, `tokens_entrada`) y `sesion_2/02_capa_semantica.py`
  (`INSTRUCCIONES`, `construir_system_prompt` = instrucciones + `esquema()` + guía).
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/asistente/{ollama.py, datos.py, config.py, flujo.py}`
  (cliente `/api/chat` con errores con código, `preguntar()` que devuelve SQL y filas, `CTX_TEXTO` único,
  `KEEP_ALIVE`).
- `07_llm_open_source/clase_02/EXPLICACION_tema_2.md` (el 4B llega al 67 % con la capa semántica).
- `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/llm.py` (usa `/v1`: no sirve para las métricas de Ollama).
- `04_api_sdks_ia/Clases/02` y `03` (`llm_client.py`: llamada con tiempos y tokens, salida con esquema).
- `ejercicio_3/herramientas.py` (tools con validación de argumentos).
- Proyecto: `PROYECTO.md` §5 (un único `num_ctx`, API nativa), §6, §8 (árbol de trazas); `text2sql/AGENTS.md`,
  `contracts/AGENTS.md` (`SqlMetrics`, `LlmCallMetrics`, `OllamaTimings`, `SqlResult` pendiente), `telemetry/AGENTS.md`
  (`span()`), `database/src/database/semantic_layer.py` (`open_db`, `schema()`, `GUIDE`).

**Desvíos respecto al patrón de clase:**
- **No redacta ni verifica cifras.** El bucle de clase sigue hasta que el modelo responde con texto y pasa
  `cifras_sin_respaldo()`; aquí se para en cuanto **todas las consultas pedidas en una respuesta se ejecutan bien** y
  devuelve SQL + filas. La redacción y el verificador pasan al agente (fase 6). Como `datos.preguntar()` de S3, que
  devuelve las consultas para que otro paso redacte.
- **Como mucho 3 llamadas al modelo** (1 + 2 reintentos, `PROYECTO.md` §6), frente a las 4–6 rondas de clase.
- **Respuesta sin SQL = resultado «sin SQL» con el texto del modelo** (p. ej. «ese dato no existe»). En clase solo se
  avisaba («respondió sin consultar los datos»).
- **Instrucciones**: las de `INSTRUCCIONES` de la capa semántica de S2 sin la parte de redactar («Responde en español,
  en un máximo de 5 frases…») y sin `PERIODOS` (Viajes Nimbo no tiene periodos A/B). Se mantiene: una consulta
  `SELECT` por llamada a la tool, no inventar vistas ni columnas, operaciones dentro del SQL, si el dato no existe
  decirlo. Esquema y guía: los de `database` (`schema()` + `GUIDE`), como `construir_system_prompt` de clase.
- **Errores de Ollama con código en inglés** (`ollama_unavailable`, `ollama_timeout`, `model_not_installed`,
  `ollama_error`) en vez de `OLLAMA_NO_DISPONIBLE`… de `S3/asistente/ollama.py`; el mensaje sigue en castellano.
- **`requests` como dependencia nueva** de `text2sql`, para el mismo cliente `/api/chat` que S3 (sin OpenAI ni `/v1`).
  `OLLAMA_BASE_URL` pasa a ser la dirección sin `/v1` (`http://localhost:11434`).
- **Un evento `SqlMetrics` por cada SQL ejecutado o rechazado** (no uno por `ask`), porque una respuesta puede
  traer varias consultas. Se ajusta la descripción de `SqlMetrics`, que dice «span `text2sql.consultar`».

## Alcance

**Dentro**
- Contrato `SqlResult` en `contracts/` (pendiente desde la fase 1c): estado (`ok` / sin SQL / error de SQL), lista
  de consultas (cada una con su SQL, columnas, filas, si se recortó y sus `SqlMetrics`), texto del modelo cuando no
  hay SQL, último error y número de llamadas al modelo. Serializable a JSON (el agente lo recibirá como mensaje de
  la tool).
- Cliente de Ollama por la API nativa `/api/chat` con tiempos, tokens y errores con código.
- El prompt (instrucciones + esquema generado + guía) y la tool de SQL descrita al modelo.
- El bucle: ejecutar con `run_safe_sql` cada consulta pedida, devolver los errores al modelo, como mucho 2 reintentos.
- Telemetría: spans de `ask`, de cada llamada al LLM y de cada SQL.
- Configuración por variables de entorno (`OLLAMA_BASE_URL`, `TEXT2SQL_MODEL`, `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE`)
  y `.env.example` actualizado.
- Tests con un modelo falso (sin Ollama).
- Comando para probarlo a mano con el Qwen real, como los `main()` con `-q` de clase:
  `uv run python -m text2sql -q "¿Cuántas reservas canceladas tiene C-001?"`. Enseña, en bloques separados como el
  `04_conectar_ollama.py`, lo que recibiría el agente (el resultado entero en JSON) y las métricas de todos los
  pasos de esa pregunta.

**Fuera**
- El agente, la tool `consultar_bbdd` y la redacción (fase 6).
- El verificador de cifras `cifras_sin_respaldo()` (fase 6, en el agente).
- Las ~50 preguntas a mano y la evaluación con el Qwen real (siguientes tickets de la fase 5).
- Ejemplos dinámicos (escalón 2) y consultas fijas tipo `S3/asistente/datos.py`: solo si la evaluación lo pide.
- Las opciones `--sql` / `--solo-esquema` del 08 de clase (el esquema ya lo enseña `database`).
- Tiempo máximo de ejecución y conexión en solo lectura de `PROYECTO.md` §6 (ticket aparte, como en TRAVEL-002).
- El `.env.example` de `agent/` (también apunta a `/v1`): se cambia en la fase 6.

## Criterios de aceptación

En todos, «el modelo» es un modelo falso que responde lo que dice el *Dado*, y la base es la de `open_db()`.

### Camino feliz

**AC-1 — Una consulta correcta devuelve su SQL y sus filas**
- **Dado** un modelo que, ante «¿Cuántas reservas tiene C-001?», pide la tool de SQL con
  `SELECT COUNT(*) AS n FROM v_reservas_cliente WHERE cliente_id = 'C-001'`
- **Cuando** se llama a `ask` con esa pregunta
- **Entonces** el resultado tiene estado `ok` y una consulta con ese SQL, la columna `n` y la misma fila que da DuckDB
- **Y** se ha llamado al modelo una sola vez

**AC-2 — Varias consultas en la misma respuesta se ejecutan todas, en orden**
- **Dado** un modelo que en una sola respuesta pide dos consultas: el gasto neto de C-001 en `v_resumen_clientes`
  y sus incidencias en `v_incidencias`
- **Cuando** se llama a `ask`
- **Entonces** el resultado tiene estado `ok` y dos consultas, en el orden pedido, cada una con su SQL y sus filas
- **Y** se ha llamado al modelo una sola vez

**AC-3 — El modelo recibe el esquema, la guía y la tool, nunca datos**
- **Dado** un modelo que guarda los mensajes que recibe
- **Cuando** se llama a `ask("¿Cuántas reservas tiene C-001?")`
- **Entonces** el mensaje de sistema contiene el esquema que genera `database` (todas las vistas de `main`) y la
  guía, incluido el bloque «Datos que NO existen»
- **Y** el mensaje de usuario es solo la pregunta, y la llamada ofrece una única tool de SQL con un parámetro de texto

**AC-4 — El comando enseña lo que recibiría el agente y las métricas de cada paso**
- **Dado** el modelo del AC-1
- **Cuando** se ejecuta `python -m text2sql -q "¿Cuántas reservas tiene C-001?"`
- **Entonces** la salida tiene, en este orden, un bloque con la pregunta, un bloque con el resultado entero en JSON
  (lo que recibiría el agente: estado, consultas con SQL, columnas y filas, llamadas al modelo) y un bloque con las
  métricas completas de cada evento de esa pregunta (la llamada al LLM con tokens y tiempos de Ollama, y el SQL)
- **Y** el comando termina con código 0

### Casos límite

**AC-5 — Un SQL que falla vuelve al modelo y la corrección se acepta**
- **Dado** un modelo que primero pide `SELECT COUNT(*) FROM v_reservas` (no existe) y, al recibir el error, pide
  `SELECT COUNT(*) AS n FROM v_reservas_cliente`
- **Cuando** se llama a `ask`
- **Entonces** el segundo mensaje al modelo incluye, como resultado de la tool, el texto de error que da el validador
- **Y** el resultado tiene estado `ok`, solo la consulta corregida y 2 llamadas al modelo

**AC-6 — Si una de varias consultas falla, la buena se conserva y solo la mala vuelve al modelo**
- **Dado** un modelo que pide dos consultas, una correcta y otra con una columna que no existe, y en el reintento
  pide solo la corregida
- **Cuando** se llama a `ask`
- **Entonces** el resultado tiene estado `ok` con las dos consultas correctas (la primera y la corregida)
- **Y** la primera consulta no se vuelve a pedir ni a ejecutar

**AC-7 — Una respuesta sin SQL se devuelve como «sin SQL» con el texto del modelo**
- **Dado** un modelo que, ante «¿Cuántas personas viajan en la reserva R-1042?», responde con texto «Ese dato no
  existe: la reserva no dice cuántas personas viajan» y sin pedir la tool
- **Cuando** se llama a `ask`
- **Entonces** el resultado tiene estado «sin SQL», ninguna consulta y ese texto
- **Y** se ha llamado al modelo una sola vez (no se reintenta)

**AC-8 — Más de 50 filas se recortan y se marca**
- **Dado** un modelo que pide `SELECT v.* FROM v_vuelos_detalle v CROSS JOIN v_itinerarios`
- **Cuando** se llama a `ask`
- **Entonces** la consulta del resultado trae exactamente 50 filas y está marcada como recortada

### Errores

**AC-9 — Tras 2 reintentos fallidos se devuelve el error, sin una cuarta llamada**
- **Dado** un modelo que siempre pide `SELECT * FROM v_reservas` (no existe)
- **Cuando** se llama a `ask`
- **Entonces** el resultado tiene estado de error de SQL, ninguna consulta y como último error el texto del validador
- **Y** se ha llamado al modelo exactamente 3 veces

**AC-10 — El modelo no puede saltarse el validador**
- **Dado** un modelo que pide `SELECT * FROM crudo.clientes` y después `DELETE FROM v_incidencias`
- **Cuando** se llama a `ask`
- **Entonces** ninguna de las dos se ejecuta: el modelo recibe los mensajes de «no está permitida» y «solo se permiten
  consultas SELECT», y el resultado no trae filas de `crudo`
- **Y** `v_incidencias` tiene las mismas filas que antes

**AC-11 — Ollama sin responder da un error con código**
- **Dado** `OLLAMA_BASE_URL` apuntando a un puerto donde no escucha nadie
- **Cuando** se llama a `ask`
- **Entonces** se lanza un error con código `ollama_unavailable` y un mensaje en castellano que dice la dirección
- **Y** queda un evento de telemetría con `status = "error"`

**AC-12 — Un modelo que no está instalado da un error con código**
- **Dado** un Ollama que responde HTTP 404 al pedir el modelo de `TEXT2SQL_MODEL`
- **Cuando** se llama a `ask`
- **Entonces** se lanza un error con código `model_not_installed` y el mensaje dice el `ollama pull` que falta

**AC-12b — Ollama que no contesta a tiempo da un error con código**
- **Dado** un Ollama que no responde antes del tiempo máximo de la petición
- **Cuando** se llama a `ask`
- **Entonces** se lanza un error con código `ollama_timeout` y el mensaje dice el modelo y los segundos esperados

**AC-12c — Cualquier otra respuesta de error de Ollama da un error con código**
- **Dado** un Ollama que responde con un código HTTP distinto de 200 y de 404 (p. ej. 500)
- **Cuando** se llama a `ask`
- **Entonces** se lanza un error con código `ollama_error` y el mensaje dice el código HTTP y el texto que devolvió

**AC-13 — El comando con Ollama caído explica el fallo sin traza de Python**
- **Dado** `OLLAMA_BASE_URL` apuntando a un puerto donde no escucha nadie
- **Cuando** se ejecuta `python -m text2sql -q "¿Cuántas reservas tiene C-001?"`
- **Entonces** la salida dice el código `ollama_unavailable` y su mensaje, sin un *traceback*
- **Y** el comando termina con un código distinto de 0

### No funcionales

**AC-14 — Cada paso deja su evento de telemetría en la misma traza**
- **Dado** el caso del AC-5 (2 llamadas al modelo, 1 SQL rechazado y 1 ejecutado)
- **Cuando** se leen los eventos escritos
- **Entonces** hay 2 eventos `LlmCallMetrics` con `purpose = "generate_sql"`, `provider = "ollama"`, `num_ctx = 8192`
  y los tiempos de Ollama, y 2 eventos `SqlMetrics` (uno con `sql_valid = false` y su motivo, otro con las filas
  devueltas y las vistas usadas)
- **Y** todos comparten `trace_id`, cuelgan del span de `ask` y ninguno guarda el texto de la pregunta

**AC-15 — Lo que se envía a Ollama sale de la configuración**
- **Dado** `TEXT2SQL_MODEL=qwen3:4b-instruct`, `OLLAMA_NUM_CTX=8192` y `OLLAMA_KEEP_ALIVE=30m`
- **Cuando** se llama a `ask` con un Ollama falso que guarda la petición
- **Entonces** la petición va a `/api/chat` con ese modelo, `num_ctx = 8192`, `keep_alive = "30m"`,
  `temperature = 0`, `think = false` y `stream = false`

## Definición de hecho

- [x] Cada AC cubierto por un test automático que pasa, con el modelo falso (sin red ni Ollama). Los de Ollama
      caído (AC-11, AC-13) usan `requests` de verdad contra `127.0.0.1:1`, sin salir del equipo
- [x] Toda la suite del proyecto en verde (`uv run pytest`), incluidos los tests de TRAVEL-002
- [x] ruff y ty limpios
- [x] `text2sql/AGENTS.md` y `contracts/AGENTS.md` actualizados (función pública, `SqlResult` tachado de pendientes),
      la fila 5 y «Contratos pendientes» de `travel-agency/AGENTS.md`
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- La tool se llama `run_sql` con el parámetro `query` (código en inglés); su descripción va en castellano, como en
  clase. Por si el modelo usa otro nombre de parámetro, se acepta también `consulta` y `sql`, como hace
  `01_preguntar_datos.py` (`args.get("consulta") or args.get("query") or args.get("sql")`).
- Una llamada escrita como texto JSON en vez de `tool_calls` (el «llamada_en_texto» del 07) se trata como respuesta
  sin SQL: no se intenta interpretar.
- Si el modelo responde con texto en un reintento, después de un error, el resultado es de error de SQL (con lo que
  se haya ejecutado bien hasta entonces), no «sin SQL».
- `temperature = 0`, `think = false`, `num_predict = 1024`, como `01_preguntar_datos.py`. `OLLAMA_KEEP_ALIVE=30m`
  como `KEEP_ALIVE` de `S3/asistente/config.py` (`PROYECTO.md` §5 pide un único `num_ctx` y `keep_alive`).
- La pregunta llega ya autocontenida: `ask` no recibe historial (lo resuelve el agente en la fase 6).
- El modelo no ve las filas: cuando todas las consultas van bien no hay más llamadas, así que el resultado no
  vuelve a pasar por él.
- La versión del prompt (`text2sql_prompt_v1`) va en las `Versions` de las métricas.
- El comando enseña como «lo que recibiría el agente» el resultado entero en JSON. Si en la fase 6 se decide
  mandarle al agente menos (p. ej. sin las métricas), se cambia allí.
- El bloque de métricas sale de los eventos de telemetría de esa traza (lo que ya se escribe en
  `logs/text2sql/events-*.jsonl`), no de un cálculo aparte. Salida con `print` y bloques `[…]` como el 04, sin `rich`.

**Preguntas abiertas**
- Ninguna.
