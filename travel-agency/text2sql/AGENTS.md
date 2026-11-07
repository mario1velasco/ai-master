# AGENTS.md — `text2sql/`

> Estado: **fase 5, validador hecho** (`guard.py`, ticket `docs/tickets/TRAVEL-002`). Falta generar el SQL con el
> modelo, el bucle de corrección y la función pública con `SqlResult`.

## Propósito

Traduce una pregunta a SQL con Qwen3-4B, lo valida (solo `SELECT`, solo vistas permitidas) y lo ejecuta en DuckDB (sección 6).

Depende de: `contracts`, `telemetry`, `database`, `pandas`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/text2sql/__init__.py`: punto de entrada del paquete (`import text2sql`).
- `src/text2sql/guard.py`: `run_safe_sql(con, query) -> (ok, texto)`, la barrera del SQL del modelo.
- `tests/conftest.py`: fixture `con` de sesión con `open_db()` (la de `database/tests` no llega aquí).
- `tests/test_text2sql_guard.py`: un test por criterio del ticket TRAVEL-002.
- `dataset/`, `finetune/`, `eval/`: vacíos.

## Función pública

Todavía ninguna. `run_safe_sql` es interna: la usará la función pública (con `SqlResult`) del siguiente ticket.

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
uv run pytest text2sql/tests
```

Variables en `.env` (copiar de `.env.example`): `OLLAMA_BASE_URL`, `TEXT2SQL_MODEL`.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
- `pandas` se añadió solo para ejecutar el mismo `fetchdf()` / `to_json()` que en clase.
- Con aviso de recorte, el texto **no es JSON entero** (el aviso va detrás, como en clase): para leer las filas,
  `json.JSONDecoder().raw_decode(text)`.
- `main.v_incidencias` (con el esquema delante) se rechaza: el esquema nunca le enseña `main.` al modelo.
- `enable_external_access = false` de `open_db()` es la segunda barrera: `read_csv_auto()` ya lo para la lista
  blanca antes de ejecutar.
- Ninguna vista llega a 50 filas: el test del recorte usa un `CROSS JOIN` de dos vistas (121 filas).
