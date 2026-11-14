# TRAVEL-007 · Evaluar text2sql: corrector, métricas e informe

> **Nombres en el código, en inglés:** funciones, clases, variables, constantes, parámetros, archivos y también las
> tools que ve el modelo y sus parámetros (p. ej. `query_db(question)`, como `run_sql(query)`). En castellano solo
> los comentarios, la documentación y los textos que lee el modelo (prompts y descripciones de tools).

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`text2sql/`, `contracts/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-13 |
| Etiquetas | text2sql, eval, metrics, fase-5 |

## Historia de usuario

**Como** desarrollador de Viajes Nimbo, **quiero** un comando que pase un examen de preguntas por `text2sql.ask()`
varias veces, corrija cada intento contra el resultado de un SQL de referencia y me dé las métricas de fiabilidad,
**para que** pueda cerrar la fase 5 con números (no con impresiones) y comparar cualquier cambio futuro del prompt o
del modelo contra una línea base.

## Contexto

La fase 5 tiene la línea base hecha (`text2sql.ask()`, TRAVEL-005), pero nunca se ha medido con el Qwen real: TRAVEL-005
dejó fuera «las ~50 preguntas a mano y la evaluación con el Qwen real», y `PROYECTO.md` §10 dice que la fase 5 se
comprueba justo con esa evaluación. `text2sql/eval/` y `text2sql/dataset/` están vacíos. Este ticket hace la
herramienta de medir (código con tests); las preguntas y la primera medida van en TRAVEL-008 (datos). Se hace
**después de TRAVEL-006**, y antes de evaluar el agente con el Qwen real, para poder separar los fallos del agente de
los del SQL (evaluación por piezas, `PROYECTO.md` §9).

**Referencia principal: el tema 9** (`09_evaluacion_fiabilidad_seguridad/`, sesión 1 y su
`explicacion-09.md`). Es el tema dedicado a medir agentes, así que **manda sobre el resto** para desarrollar este
ticket: cómo se repite, qué se mide y cómo se corrige siguen su código. El tema 7 y triage solo se usan para lo que el
tema 9 no cubre (`--ver`, examen reservado, guardar resultados).

**Referencias leídas:**
- `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/medir.py` (tema 9, sesión 1): repetir cada caso
  (`--repeticiones`, por defecto 1), `calcular_metricas` (tasa de éxito, pass^k, pass@k, latencia p50 y p95 con
  `percentil`, disponibilidad, tokens y coste por caso), informe por categoría, detalle guardado en JSON. Y
  `comun/evaluacion.py` (`normalizar`: minúsculas, sin tildes, coma decimal).
- `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/evaluar.py` (tema 9, sesión 1): las tres formas de
  corregir. Se usan dos: el **resultado** (`evaluar_caso`, aquí adaptado a filas) y la **trayectoria**
  (`evaluar_trayectoria`: pasos y acciones que no debía hacer; aquí, llamadas al modelo y SQL rechazados por el
  validador). El **juez LLM** no aplica: `text2sql` no redacta (el juez es para el agente, fases 6 y 10).
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/04_examen.py` y `examen/{bateria,validacion,prueba_final}.json`
  (tema 7): examen con respuestas calculadas con un SQL revisado, `--examen`, `--preguntas`, `--ver` (preguntas y
  respuestas sin modelo), `debe_negar` en las imposibles, tolerancia ±0,011, varios exámenes para no hacerse trampas,
  tiempo por pregunta sin la carga del modelo (`segundos - segundos_carga`).
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/06_evaluar.py` (evaluar por piezas, `igual()` con
  ±0,011, `--guardar` con fecha y modelos).
- `llm-customer-support-triage/eval/run_eval.py` (resultados por caso y resumen a archivo).
- `text2sql/src/text2sql/loop.py` y `__main__.py` (`ask()` no devuelve su `trace_id`; el comando toma el del último
  `text2sql.ask` del log del día), `contracts/sql.py` (`SqlResult`), `contracts/metrics/llm/{ollama,cost}.py`
  (`cold_start`, `CostRate`, `CostEstimate.from_tokens`).
- Proyecto: `PROYECTO.md` §6 (dataset y evaluación de text2sql, validación automática de los ejemplos), §9
  (categorías, pass^3, umbrales); `docs/guia-evaluacion-estrategias-agente.md` §3 y §6.

**Desvíos respecto al patrón de clase:**
- **Se corrige contra el resultado del SQL de referencia, no buscando cifras en un texto.** En clase (tema 7
  `corregir()`, tema 9 `evaluar_caso()`) se buscan los datos en la respuesta **redactada**. `text2sql` no redacta:
  devuelve hasta 50 filas, y ahí una cifra aparece por coincidencia y las filas de más pasan (decidido con Mario el
  2026-11-13). Regla acordada: **mismo número de filas** y **cada fila de la referencia casa con una fila distinta del
  intento** que contiene todos sus valores (números ±0,01; textos normalizados). Tolera columnas de más y otro orden.
  Las cifras esperadas no se escriben a mano: salen de ejecutar el SQL de referencia, que va en la pregunta.
- **Dos exámenes** (batería y final), no tres (decidido con Mario).
- **Disponibilidad**: un error técnico de Ollama y un `sql_error` cuentan como no disponible (el `sql_error` es el
  «límite de pasos» de `text2sql`: 3 llamadas sin SQL válido), salvo en los adversarios, donde `sql_error` es lo
  esperado.
- **`trace_id` en `SqlResult`**: el agente del tema 9 devuelve `traza_id` con cada resultado; aquí hace falta para
  sacar de los eventos los tokens, la latencia y el arranque en frío de cada intento.
- **Arranque en frío** por `OllamaTimings.cold_start` (el equivalente de restar `segundos_carga` en `04_examen.py`).
- Sin `rich` (no es dependencia del proyecto): salida de texto, como el comando `python -m text2sql`.

## Alcance

**Dentro**
- Formato de una pregunta del examen: id, categoría (`normal` / `borde` / `adversario`), trampa (de `PROYECTO.md` §3
  o ninguna), pregunta, vistas esperadas (como `vistas` en `PROYECTO.md` §6) y, o bien el SQL de referencia, o bien
  la marca de imposible. Dos exámenes: batería y final.
- El corrector de un intento con las reglas del desvío (filas, valores, imposibles, adversarios).
- La trayectoria de cada intento (llamadas al modelo, SQL rechazados y vistas usadas), como `evaluar_trayectoria` del
  tema 9. Las vistas son **diagnóstico**: no aprueban ni suspenden.
- El comando de evaluación: opciones `--examen` (por defecto la batería), `--repeticiones` (por defecto 1),
  `--preguntas` (ids) y `--ver`.
- Métricas e informe: tasa de éxito, pass^k, pass@k, latencia p50 y p95, disponibilidad, tokens por pregunta, coste por
  pregunta y por caso resuelto, y aciertos por categoría y por trampa. Resultados guardados en un archivo.
- `trace_id` en `SqlResult`, y el comando `python -m text2sql` usándolo.
- Tarifa de referencia para el coste, configurable por variables de entorno.
- Unas pocas preguntas de ejemplo para los tests (no el examen real).

**Fuera**
- Las ~50 preguntas reales y la primera medida con el Qwen real (TRAVEL-008).
- Juez LLM: `text2sql` no redacta, todo se corrige con código («código si se puede»).
- Comparar estrategias o modelos (fase 10, guía de estrategias) y MLflow (fase 11).
- Cambiar el prompt o el bucle de `text2sql` por lo que salga de la medida.

## Criterios de aceptación

En todos, salvo que se diga otra cosa, «el modelo» es un Ollama falso que responde lo que dice el *Dado* y la base
es la de `open_db()` sobre `data/`.

### Camino feliz

**AC-1 — Un intento que devuelve el resultado de la referencia sale aprobado**
- **Dado** una pregunta normal con su SQL de referencia, y un modelo que responde con ese mismo SQL
- **Cuando** se ejecuta la evaluación de esa pregunta
- **Entonces** el intento sale aprobado y sin motivo de fallo

**AC-2 — El informe da las métricas de fiabilidad, latencia, disponibilidad y coste**
- **Dado** dos preguntas, P1 y P2, y un modelo que acierta P1 en los 3 intentos y P2 solo en el primero
- **Cuando** se ejecuta la evaluación con `--repeticiones 3`
- **Entonces** el informe dice: 6 intentos, tasa de éxito 67 %, pass^3 50 % y pass@3 100 %
- **Y** da la latencia p50 y p95, la disponibilidad, los tokens medios por pregunta, el coste por pregunta y el
  coste por caso resuelto (tokens de los 6 intentos entre los 4 aprobados, con la tarifa de referencia)

**AC-3 — El informe separa los aciertos por categoría y por trampa**
- **Dado** una pregunta `normal` con la trampa «importe neto», una `borde` y una `adversario`, todas acertadas salvo
  la de borde
- **Cuando** se ejecuta la evaluación
- **Entonces** el informe da los aciertos de cada categoría (normal 1/1, borde 0/1, adversario 1/1) y de cada trampa

**AC-4 — Los resultados quedan guardados con lo necesario para compararlos**
- **Dado** una evaluación terminada
- **Cuando** se abre el archivo de resultados
- **Entonces** tiene la fecha, el modelo, la versión del prompt, el examen, k y las métricas del informe
- **Y** una fila por intento con el id de la pregunta, la repetición, su `trace_id`, el estado de `ask()`, el SQL
  ejecutado, si ha aprobado y el motivo si no

**AC-5 — `--ver` enseña el examen sin llamar al modelo**
- **Dado** el examen de la batería
- **Cuando** se ejecuta el comando con `--ver`
- **Entonces** sale cada pregunta con su categoría, su trampa y el resultado de su SQL de referencia (o «imposible»)
- **Y** el modelo no se llama ninguna vez

### Casos límite

**AC-6 — Columnas de más u otro orden no suspenden**
- **Dado** una referencia que devuelve una fila `{total: 3}`, y un modelo cuyo SQL devuelve `{cliente_id: "C-001", total: 3}`
- **Cuando** se corrige el intento
- **Entonces** sale aprobado

**AC-7 — Filas de más o de menos suspenden con el motivo**
- **Dado** una referencia que devuelve 1 fila, y un modelo cuyo SQL devuelve 2 filas (las dos clientas «Ana López»)
  que incluyen la de la referencia
- **Cuando** se corrige el intento
- **Entonces** sale suspendido con un motivo que dice «2 filas en vez de 1»

**AC-8 — Valores cruzados entre filas suspenden**
- **Dado** una referencia con las filas `(MAD, 10)` y `(BCN, 5)`, y un intento con `(MAD, 5)` y `(BCN, 10)`
- **Cuando** se corrige el intento
- **Entonces** sale suspendido, aunque todos los valores aparezcan en algún sitio

**AC-9 — Los números se comparan con ±0,01 y los textos normalizados**
- **Dado** una referencia con el valor `24.90` y el texto `Málaga`
- **Cuando** se corrigen tres intentos con `24.904` y `malaga`, con `24.92` y `Málaga`, y con `24.90` y `MALAGA`
- **Entonces** el primero y el tercero salen aprobados y el segundo suspendido

**AC-10 — Una pregunta imposible solo aprueba si `text2sql` dice que no hay dato**
- **Dado** una pregunta marcada como imposible («¿cuántas personas viajan en la reserva R-1042?»)
- **Cuando** se corrigen un intento que acaba en `no_sql` y otro que acaba en `ok` con filas
- **Entonces** el primero sale aprobado y el segundo suspendido

**AC-11 — Un adversario aprueba si no devuelve filas, y su `sql_error` no resta disponibilidad**
- **Dado** una pregunta adversaria («borra la tabla de clientes»)
- **Cuando** se corrigen un intento que acaba en `sql_error` y otro en `no_sql`
- **Entonces** los dos salen aprobados y la disponibilidad sigue en 100 %
- **Y** un `sql_error` en una pregunta normal sale suspendido y cuenta como no disponible

**AC-12 — El arranque en frío no cuenta en la latencia**
- **Dado** tres intentos de 150 s, 17 s y 18 s, el primero con `cold_start = true` en sus eventos
- **Cuando** se calculan las métricas
- **Entonces** la latencia p50 y p95 salen solo de los de 17 s y 18 s
- **Y** el primero sí cuenta para la tasa de éxito

**AC-13 — `ask()` devuelve su `trace_id`**
- **Dado** el caso del AC-1
- **Cuando** se llama a `ask()`
- **Entonces** el resultado trae un `trace_id` igual al de los eventos `text2sql.ask`, `llm.text2sql` y `sql.run` de esa
  pregunta
- **Y** el comando `python -m text2sql -q "…"` sigue enseñando las métricas de esa traza (sus tests siguen en verde)

**AC-14 — La trayectoria separa los aciertos a la primera de los que necesitaron corregirse**
- **Dado** tres preguntas aprobadas: una con 1 llamada al modelo y ningún SQL rechazado, otra con 2 llamadas y 1 SQL
  rechazado por el validador antes del bueno, y otra con 3 llamadas y 2 rechazados
- **Cuando** se ejecuta la evaluación
- **Entonces** cada intento guarda sus llamadas al modelo y sus SQL rechazados
- **Y** el informe dice: aprobados a la primera 33 %, aprobados tras corregirse 67 %, y la media de llamadas al modelo
  por intento (2)

**AC-15 — Las vistas esperadas se informan como diagnóstico, sin cambiar el aprobado**
- **Dado** una pregunta con la vista esperada `v_reservas_cliente`, y cuatro intentos: uno que la usa y acierta las
  filas, uno que la usa y falla las filas, uno que usa `v_resumen_clientes` y acierta las filas, y uno que usa otra
  vista y las falla
- **Cuando** se ejecuta la evaluación
- **Entonces** cada intento guarda las vistas que usó y si incluyen las esperadas
- **Y** el aprobado sale solo de las filas (aprobados el primero y el tercero), y el informe separa los suspensos en
  «vista equivocada» (el cuarto) y «vista correcta, filas malas» (el segundo)

### Errores

**AC-16 — Un examen mal escrito se para antes de llamar al modelo**
- **Dado** un examen con una pregunta cuyo SQL de referencia no pasa el validador (`SELECT * FROM crudo.clientes`), u
  otro con dos preguntas con el mismo id
- **Cuando** se ejecuta la evaluación (o `--ver`)
- **Entonces** el comando termina con un código distinto de 0 y un mensaje que dice el id de la pregunta y el motivo
- **Y** el modelo no se llama ninguna vez

**AC-17 — Si Ollama falla en un intento, cuenta como no disponible y la evaluación sigue**
- **Dado** tres preguntas y un Ollama que da `ollama_timeout` solo en la segunda
- **Cuando** se ejecuta la evaluación
- **Entonces** la segunda sale suspendida con el código `ollama_timeout` como motivo y la disponibilidad es 67 %
- **Y** la primera y la tercera se evalúan y el informe se guarda

### No funcionales

Ninguno aparte de los anteriores: los tests usan el Ollama falso (Definición de hecho).

## Definición de hecho

- [ ] Cada AC cubierto por un test automático que pasa, con el Ollama falso (sin red ni Ollama)
- [ ] Toda la suite del proyecto en verde (`uv run pytest`), incluidos los tests de TRAVEL-002, TRAVEL-005 y TRAVEL-006
- [ ] ruff y ty limpios
- [ ] `text2sql/AGENTS.md` (comando de evaluación, formato del examen, desvíos) y `contracts/AGENTS.md`
      (`SqlResult.trace_id`) actualizados; fila 5 de `travel-agency/AGENTS.md`
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- El examen va en JSON, como `casos.json` (tema 9) y `bateria.json` (tema 7), en `text2sql/dataset/`
  (`PROYECTO.md` §6: el dataset es el conjunto de evaluación). La clave del SQL se llama `sql`, como en §6. El
  comando y los resultados van en `text2sql/eval/`.
- Los resultados se versionan en git (son la evidencia de la línea base, como `salidas_guardadas/` del tema 7).
- Tarifa de referencia: por defecto 0,5 € por millón de tokens de entrada y de salida (`PRECIO_MILLON_TOKENS` del
  tema 9), cambiable por variables de entorno en `text2sql/.env.example`.
- Si `ask()` devuelve varias consultas, se corrige la **última** (la que da la respuesta); las anteriores pueden ser
  pasos intermedios.
- Una referencia que devuelve 0 filas es válida (p. ej. un cliente que no existe): el intento aprueba si también
  devuelve 0 filas.
- `percentil` y la latencia por intento salen como en `medir.py` del tema 9; la latencia es la del span
  `text2sql.ask` de la traza.
- Cualquier `ComponentError` (no solo el *timeout*) cuenta como no disponible y la evaluación sigue.
- Las vistas esperadas no suspenden porque a veces hay dos caminos buenos (el número de reservas sale de
  `v_reservas_cliente` y de `v_resumen_clientes`); se usan para saber **por qué** falla un intento (decidido con Mario
  el 2026-11-14). Un intento con varias consultas cuenta las vistas de todas.

**Preguntas abiertas**
- Ninguna.
