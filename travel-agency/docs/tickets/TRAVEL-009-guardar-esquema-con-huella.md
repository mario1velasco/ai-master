# TRAVEL-009 · Guardar el esquema de la capa semántica en un archivo con huella

> **Nombres en el código, en inglés:** funciones, clases, variables, constantes, parámetros, archivos y también las
> tools que ve el modelo y sus parámetros (p. ej. `query_db(question)`, como `run_sql(query)`). En castellano solo
> los comentarios, la documentación y los textos que lee el modelo (prompts y descripciones de tools).

| Campo | Valor |
|---|---|
| Tipo | Task |
| Carpeta del proyecto | `travel-agency/` (`database/`, `text2sql/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-15 |
| Etiquetas | database, text2sql, performance, cache, fase-5 |

## Historia de usuario

**Como** desarrollador de Viajes Nimbo, **quiero** que el esquema que ve el modelo se guarde en un archivo y solo se
vuelva a generar cuando cambien los datos o la capa semántica, **para que** cada pregunta no pague los ~5,7 s de
generarlo y las conexiones a la base no se queden retenidas en memoria.

## Contexto

`text2sql` manda al modelo un prompt con el esquema que genera `schema()` (`database/src/database/semantic_layer.py`).
`schema()` hace unas 200 consultas sobre vistas anidadas: medido el 2026-11-15, **5,7 s sobre `data/`** (0,7 s
`open_db()`). Para no pagarlo en cada pregunta, `build_system_prompt(con)` (`text2sql/src/text2sql/prompt.py`) lleva
`@cache` (desvío acordado en TRAVEL-005). Eso deja dos problemas, que encontró el `simplify` al cerrar TRAVEL-006:

1. **Tiempo**: la caché vive en el proceso, y `python -m agent -q` / `python -m text2sql -q` abren un proceso por
   pregunta, así que cada pregunta paga los 5,7 s (~18 % del turno). Además, el prompt se construye dentro del span
   `text2sql.ask`, así que la primera pregunta de cada proceso sale 5,7 s más lenta en las métricas.
2. **Memoria**: `@cache` guarda cada conexión con su prompt y no la suelta nunca. Cada conexión en memoria ocupa
   ~11 MB (medido: 5 conexiones retenidas, +91 MB). Hoy no se nota (una conexión por proceso), pero la API (fase 7)
   abriría una por petición.

Con el esquema en un archivo, leerlo cuesta milisegundos (la huella SHA-256 de todo `data/`, 940 KB, tarda 0,015 s), y
la caché en memoria sobra: quitarla arregla el problema 2. Se hace **antes de TRAVEL-007 y TRAVEL-008**, para que el
examen de text2sql se mida ya sin los 5,7 s por pregunta (decidido con Mario el 2026-11-15).

**Referencias leídas:**
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py` (tema 7 S2): `esquema()` y
  `construir_system_prompt()`, que lo genera en cada pregunta.
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/asistente/vision.py` (tema 7 S3), `extraer()`:
  caché en disco con la **huella SHA-256 en el nombre del archivo** (`cache_vision/{sha256[:16]}_….json`); si el
  archivo existe se lee, si no se calcula y se escribe.
- `05_rag_langchain/clases/07-RAG/src/retrieval_lab/infrastructure/artifacts.py` (tema 5): `fingerprint()` (SHA-256),
  `file_digest()` (SHA-256 de un archivo por bloques) y `write_json()` (escritura atómica: archivo `.tmp` y
  `replace`). Y `representations/cache.py`: la huella en el nombre de la carpeta de la caché y una `format_version`
  dentro de la huella.
- Proyecto: `database/AGENTS.md` («calcúlalo una vez al arrancar»), `text2sql/AGENTS.md` (desvío del prompt «una vez
  por conexión»), `text2sql/src/text2sql/{prompt.py, loop.py}`, `database/src/database/semantic_layer.py`
  (`open_db()`, `schema()`, `main()`), los tests que comprueban el esquema que recibe el modelo
  (`text2sql/tests/test_text2sql_ask.py`) y `rag/corpus/SOURCES.md` (huellas SHA-256 del proyecto).

**Desvíos respecto al patrón de clase:**
- **El esquema no se genera en cada pregunta** (en clase, `construir_system_prompt()` llama a `esquema()` cada vez):
  se lee de un archivo y solo se regenera cuando cambia la huella. El patrón del archivo es el de `vision.py` (huella
  en el nombre) y el de `artifacts.py` (SHA-256 y escritura atómica).
- **La huella incluye el código** (`semantic_layer.py` y `schema.py`) y la versión de DuckDB, en lugar de una `format_version`
  escrita a mano como en el tema 5: así no hay que acordarse de subir ninguna versión (decidido con Mario).
- **Se quita el `@cache` de `build_system_prompt`**, que guardaba la conexión. En su lugar, las dos capas de
  `vision.py`: la caché en memoria **por huella** (`_SCHEMA_MEMORY_CACHE`, el `_CACHE` de clase; la clave es texto,
  nunca la conexión) y el archivo en disco (decidido con Mario el 2026-11-15).
- **La huella viaja dentro de la conexión**: `open_db()` la calcula y la guarda con `SET VARIABLE`; la clase no
  cubre esto (decidido con Mario el 2026-11-15).
- **`semantic_layer.py` se separa en tres archivos** (en clase es uno): `semantic_layer.py` con el negocio y la base
  (`VIEWS`, `COMMENTS`, `GUIDE`, `open_db()` y el comando), `schema.py` con el esquema y su caché, y `checks.py` con
  `CHECKS` (decidido con Mario el 2026-11-15). El comando sigue siendo `python -m database.semantic_layer`.

## Alcance

**Dentro**
- Guardar el esquema generado en un archivo cuyo nombre lleva la huella de lo que lo determina: los CSV de la
  carpeta de datos, el código que genera el esquema (`semantic_layer.py` y `schema.py`) y la versión de DuckDB.
- Separar `semantic_layer.py` en `semantic_layer.py`, `schema.py` y `checks.py` (refactor: sin cambiar comportamiento).
- Leer el archivo si existe; si no, generar el esquema y guardarlo con escritura atómica.
- Quitar la caché en memoria del prompt de `text2sql` (que retiene las conexiones).
- Seguir respondiendo, con un aviso en el log, si el archivo está dañado o no se puede escribir.
- La carpeta de la caché fuera de git (`.gitignore`).

**Fuera**
- El comando `python -m database.semantic_layer`: sigue generando el esquema al momento (sirve para comprobar qué ve
  el modelo y, si hiciera falta, comparar con el archivo guardado; decidido con Mario).
- Borrar los archivos de huellas antiguas (~6 KB cada uno).
- Hacer `schema()` más rápido o cambiar lo que escribe.
- La hipótesis de que Ollama pierde la caché del prompt al turnarse agente y text2sql (se mide en la fase 6).
- TRAVEL-007 y TRAVEL-008.

## Criterios de aceptación

En todos, salvo que se diga otra cosa, la carpeta de datos es una copia de `fixtures/` en una carpeta temporal, la
caché va en otra carpeta temporal, y «el modelo» es el Ollama falso de los tests de text2sql.

### Camino feliz

**AC-1 — La primera pregunta sobre una carpeta de datos guarda su esquema**
- **Dado** una carpeta de datos sin esquema guardado
- **Cuando** se hace una pregunta a text2sql
- **Entonces** el modelo recibe en su prompt el mismo esquema que genera `schema()` sobre esa carpeta
- **Y** en la carpeta de la caché queda un archivo con ese esquema y la huella en su nombre

**AC-2 — Las preguntas siguientes leen el esquema guardado sin generarlo**
- **Dado** el esquema de esa carpeta ya guardado, con un texto marcado añadido a mano al archivo
- **Cuando** una conexión nueva sobre la misma carpeta hace una pregunta
- **Entonces** el modelo recibe el esquema del archivo, con el texto marcado incluido

### Casos límite

**AC-3 — Cambiar un CSV regenera el esquema**
- **Dado** el esquema guardado, y después una fila más en `clientes.csv` de la carpeta de datos
- **Cuando** una conexión nueva sobre esa carpeta hace una pregunta
- **Entonces** queda guardado un segundo archivo, con otra huella en su nombre
- **Y** el modelo recibe el esquema nuevo, con una fila más en la línea de `v_resumen_clientes`

**AC-4 — Otra versión del código que genera el esquema o de DuckDB regenera el esquema**
- **Dado** el esquema guardado, y después un cambio en `semantic_layer.py`, en `schema.py` o en la versión de DuckDB
  (ampliado el 2026-11-15 al separar `schema.py`: el texto del esquema depende de los dos archivos)
- **Cuando** una conexión nueva sobre la misma carpeta hace una pregunta
- **Entonces** el esquema se genera de nuevo y se guarda en un archivo con otra huella en su nombre

**AC-5 — Dos carpetas de datos no se pisan**
- **Dado** dos carpetas de datos con CSV distintos (una copia de `fixtures/` y otra con una fila más)
- **Cuando** se hace una pregunta sobre cada una
- **Entonces** hay dos archivos de esquema, uno por carpeta
- **Y** cada pregunta recibe el esquema de su carpeta

**AC-6 — Un esquema escrito a medias nunca se usa**
- **Dado** una carpeta de datos sin esquema guardado, y una escritura del archivo que se corta a la mitad
- **Cuando** termina esa pregunta
- **Entonces** en la carpeta de la caché no queda ningún archivo de esquema con esa huella
- **Y** la pregunta siguiente genera el esquema entero y lo guarda

### Errores

**AC-7 — Un archivo de esquema dañado no tumba la pregunta**
- **Dado** el archivo de esa huella vacío, o con un contenido que no es un esquema guardado
- **Cuando** se hace una pregunta
- **Entonces** el modelo recibe el esquema recién generado por `schema()`
- **Y** el log tiene un aviso con la ruta del archivo
- **Y** el archivo queda reescrito con el esquema correcto

**AC-8 — Una carpeta de caché sin permiso de escritura no tumba la pregunta**
- **Dado** una carpeta de caché de solo lectura
- **Cuando** se hace una pregunta
- **Entonces** el modelo recibe el esquema generado por `schema()` y la pregunta termina igual que sin caché
- **Y** el log tiene un aviso con la carpeta que no se pudo escribir

### No funcionales

**AC-9 — Una conexión que ya no se usa se libera**
- **Dado** una conexión con la que text2sql ha respondido una pregunta
- **Cuando** quien la abrió deja de usarla
- **Entonces** la conexión se libera de memoria: nada de text2sql ni de database la sigue guardando

**AC-10 — Con el esquema guardado, el prompt sale en menos de 0,5 s**
- **Dado** el esquema de `fixtures/` ya guardado (hoy generarlo tarda ~4,2 s sobre `fixtures/`)
- **Cuando** una conexión nueva prepara el prompt de una pregunta
- **Entonces** el esquema del prompt está listo en menos de 0,5 s

## Definición de hecho

- [ ] Cada AC cubierto por un test automático que pasa, con el Ollama falso (sin red ni Ollama) y la caché en una
      carpeta temporal (los tests no escriben en el repo)
- [ ] Toda la suite del proyecto en verde (`uv run pytest`), incluidos los tests de TRAVEL-002, TRAVEL-005 y TRAVEL-006
- [ ] ruff y ty limpios
- [ ] `database/AGENTS.md` (funciones públicas, «calcúlalo una vez al arrancar», tiempos) y `text2sql/AGENTS.md` (el
      desvío del prompt «una vez por conexión») actualizados; filas 2 y 5 de `travel-agency/AGENTS.md`
- [ ] La carpeta de la caché en `.gitignore`
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- La carpeta de la caché por defecto es `database/.cache/`, y se puede cambiar (para los tests). Nombre exacto y
  forma de cambiarla, a decidir en el desarrollo.
- Las firmas públicas no cambian (`ask(question, *, con=…)`, `open_db(data_dir)`, `schema(con)`): el agente, los
  comandos y sus tests siguen igual. Cómo llega la carpeta de datos hasta el prompt (hoy `build_system_prompt` solo
  recibe la conexión) se decide al acordar las costuras en `tdd`.
- La huella sale del contenido de los CSV, no de su ruta: dos carpetas con los mismos CSV comparten archivo.
- El archivo guarda lo justo para reconocer que es un esquema guardado y leerlo (el «contenido que no es un esquema
  guardado» del AC-7). El formato, a decidir en el desarrollo.
- Los avisos van con `logging` de la biblioteca estándar: `database` no depende de `telemetry` (`database/AGENTS.md`).
- Si dos procesos generan el mismo esquema a la vez, los dos escriben el mismo contenido; con la escritura atómica
  gana el último y el archivo nunca queda a medias.

**Preguntas abiertas**
- Ninguna.
