# Travel Agency

Agente de **Viajes Nimbo** (agencia ficticia) que responde preguntas consultando la base de datos (text-to-SQL
sobre DuckDB) o la documentación (RAG con búsqueda híbrida), con modelos open source en local y una API FastAPI.

- Diseño: [`PROYECTO.md`](PROYECTO.md)
- Instrucciones para agentes de IA: [`AGENTS.md`](AGENTS.md)
- Tickets de cada fase: [`docs/tickets/`](docs/tickets/)

## Estado

| Fase | Qué hay |
|---|---|
| 0–1. Esqueleto, contratos y telemetría | ✅ uv workspace, esquemas Pydantic con sus métricas, logs y trazas en JSONL |
| 2. Base de datos | ✅ Filas escritas a mano con trampas a propósito, conjunto grande generado con semilla fija (~15.000 filas) y capa semántica de vistas DuckDB con comentarios |
| 3. Corpus | ✅ Corpus externo reunido en `rag/corpus/` (leyes, salud, seguridad y general), con fuente, licencia y huella de cada archivo en [`SOURCES.md`](rag/corpus/SOURCES.md); lo de uso privado, fuera de git. Y 26 documentos propios de la agencia (políticas, condiciones, FAQ…) en `rag/corpus/empresa/` |
| 5. Text-to-SQL | 🚧 Línea base hecha: `text2sql.ask()` (pregunta → SQL con Qwen3-4B → validador → DuckDB, con bucle de corrección) y el validador (una sentencia, solo `SELECT`, solo vistas permitidas, 50 filas como mucho); falta medirla con el Qwen real |
| 6. Agente | 🚧 Agente mínimo hecho: LangGraph con la tool `query_db` → `text2sql.ask()`, respuesta con fuentes (y su SQL) y la traza de cada paso; faltan citas y verificador, otra estrategia y casos dorados |
| 4, 7, 7b, 8 y 10–15 | Pendientes: hoja de ruta en [`PROYECTO.md`](PROYECTO.md) §10. La 9 (fine-tuning) es opcional, para el futuro |

## Paquetes

| Carpeta | Qué hace |
|---|---|
| [`contracts/`](contracts/) | Esquemas Pydantic compartidos, todos con métricas |
| [`telemetry/`](telemetry/) | Logger, `span()`, `trace_id` y eventos JSONL |
| [`database/`](database/) | `data/` (los datos de la app), `fixtures/` (las filas a mano, datos de los tests), capa semántica y generador |
| [`text2sql/`](text2sql/) | Pregunta → SQL validado → DuckDB |
| [`agent/`](agent/) | El agente: decide si consulta la base, llama a `text2sql` y redacta la respuesta |
| [`rag/`](rag/) | El corpus de documentos (la búsqueda, por hacer) |
| [`api/`](api/) | La API FastAPI (por hacer) |

## Puesta en marcha

```bash
uv sync
uv run pytest
```

Requisitos: [uv](https://docs.astral.sh/uv/) y, a partir de la fase 5, [Ollama](https://ollama.com) con `qwen3:4b-instruct`.

## Comandos útiles

Todos desde `travel-agency/`. El detalle de cada uno está en el `AGENTS.md` de su paquete.

**Desarrollo**

```bash
uv sync                                                    # instala todo (un solo .venv para el workspace)
uv run pytest                                              # todos los tests, sin Ollama (modelos falsos)
uv run pytest agent/tests                                  # los de un paquete
uv run ruff check . && uv run ruff format . && uv run ty check   # estilo y tipos
```

**Base de datos** (`database/`)

```bash
uv run python -m database.semantic_layer                                    # lo que ve el modelo: vistas y comentarios
uv run python -m database.semantic_layer --check --data database/fixtures   # las vistas dan las cifras calculadas a mano
uv run python -m database.seed                                              # regenera database/data/ desde fixtures/
uv run python -m database.seed --seed 7 --out /tmp/datos                    # otra semilla u otra carpeta (--source, --out)
```

`database/data/` se genera: no se edita a mano. Las filas a mano se cambian en `database/fixtures/` y después se
regenera (un test avisa si `data/` se queda desfasada).

Los dos comandos siguientes usan el Qwen real: Ollama en marcha (`systemctl status ollama`) y, una vez,
`ollama pull qwen3:4b-instruct`.

**Text-to-SQL** (`text2sql/`): convierte una pregunta en SQL y lo ejecuta. El modelo escribe el SQL viendo las
vistas de la base, un validador lo deja pasar solo si es un `SELECT` sobre vistas permitidas, y DuckDB lo ejecuta. Si
el SQL falla, el error vuelve al modelo para que lo corrija (3 intentos como mucho). Devuelve el SQL y las filas,
**sin redactar**: es la pieza que usa el agente para consultar la base.

```bash
uv run python -m text2sql -q "¿Cuántas reservas tiene C-001?"            # pregunta → SQL → filas
uv run python -m text2sql -q "…" --data database/fixtures                # contra las filas a mano (cifras conocidas)
uv run --env-file text2sql/.env python -m text2sql -q "…"                # con un .env (antes: cp text2sql/.env.example text2sql/.env)
```

Enseña la pregunta, lo que recibiría el agente (el SQL, las columnas y las filas, en JSON) y las métricas de cada paso
(la llamada al modelo y cada SQL).

**Evaluar text2sql** (`text2sql.evaluation`): pasa un examen de preguntas con su SQL de referencia, varias veces, y
corrige cada intento comparando sus filas con las de la referencia. Da la tasa de éxito, pass^k, pass@k, latencia,
disponibilidad, coste y por qué falla (vista equivocada o filas malas). Los resultados quedan en
`text2sql/evaluation_results/`.

```bash
uv run python -m text2sql.evaluation --exam battery --view               # el examen y sus resultados, sin modelo
uv run python -m text2sql.evaluation --exam battery --repetitions 3      # medir: cada pregunta 3 veces (pass^3)
uv run python -m text2sql.evaluation --exam final_test --repetitions 3   # el examen reservado: solo para medir
uv run python -m text2sql.evaluation --questions N01 N02                 # solo esas preguntas
```

**Agente** (`agent/`): responde la pregunta como lo haría un empleado. Decide si necesita datos de la base; si los
necesita, se los pide a text2sql con la tool `query_db` (una o varias veces) y redacta la respuesta con esas filas,
sin inventar cifras. Si el dato no existe, lo dice. Devuelve la respuesta con sus fuentes (cada una con su SQL).

```bash
uv run python -m agent -q "¿Cuántas reservas tiene C-001?"               # la respuesta del agente
uv run python -m agent -q "¿Cuántas reservas tiene C-001?" --no-trace    # sin los eventos de cada paso
uv run python -m agent -q "…" --data database/fixtures                   # contra las filas a mano (cifras conocidas)
uv run --env-file agent/.env python -m agent -q "…"                      # con un .env (antes: cp agent/.env.example agent/.env)
```

Enseña la pregunta, la respuesta en JSON (texto, fuentes con su SQL y los totales del turno) y las métricas de cada
paso de la traza: las llamadas al modelo del agente y, dentro, las de text2sql. Todo queda también en `logs/`.

**Corpus del RAG** (`rag/corpus/`, sin tests: es un entregable de datos)

```bash
git check-ignore rag/corpus/seguridad/aesa rag/corpus/seguridad/exteriores   # lo de uso privado, fuera de git
find rag/corpus -type f -size +10M | xargs -r git check-ignore -v            # los archivos grandes, también
```

Las huellas SHA-256 de cada archivo se comprueban contra `SOURCES.md` con los comandos de
[`rag/AGENTS.md`](rag/AGENTS.md) («Comprobar el corpus»).
