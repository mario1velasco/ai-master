# TRAVEL-001 · Validador de SQL con lista blanca de vistas

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`text2sql/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-07 |
| Etiquetas | text2sql, seguridad, fase-5 |

## Historia de usuario

**Como** responsable del agente de Viajes Nimbo, **quiero** que todo SQL generado por el modelo pase por un validador en el código antes de ejecutarse, **para que** el modelo solo pueda leer las vistas de la capa semántica y nunca las tablas crudas, archivos ni otras sentencias.

## Contexto

`text2sql/` está en fase 0 (paquete vacío). La fase 5 necesita la barrera que en clase hace `ejecutar_sql_seguro`: una sola sentencia, solo `SELECT`, conexión sin acceso a archivos y como mucho 50 filas. `PROYECTO.md` §6 pide además **solo vistas de la lista blanca**, que la barrera de clase no tiene (`travel-agency/AGENTS.md`, fila 5: «añadirla»). Las tablas viven en el esquema oculto `crudo` y las vistas `v_*` las crea `database/semantic_layer.py`.

**Referencias leídas:** `07_llm_open_source/clase_01/Ejercicios/practica/08_herramienta_sql.py` (`ejecutar_sql_seguro`, `MAX_FILAS`, `enable_external_access = false`), `travel-agency/PROYECTO.md` §6 «En producción: el modelo propone, el código decide», `travel-agency/AGENTS.md` fila 5, `text2sql/AGENTS.md`, `database/src/database/semantic_layer.py`, `database/tests/conftest.py`

**Desvíos respecto al patrón de clase:**
- Lista blanca de vistas (no existe en clase; la pide `PROYECTO.md`).
- Nombres en inglés (`run_safe_sql`, `MAX_ROWS`), como pide el proyecto; los mensajes de error siguen en castellano, como en clase.

## Alcance

**Dentro**
- Función que recibe una conexión y un SQL y devuelve `(ok, texto)` como en clase: filas en JSON o un error controlado.
- Las barreras de clase y la lista blanca de vistas.

**Fuera**
- Generar el SQL con el modelo y el bucle de corrección (siguientes tickets de la fase 5).
- Tiempo máximo de ejecución y conexión en solo lectura de `PROYECTO.md` §6 (ticket aparte).
- El contrato `SqlResult` (se crea cuando haya función pública).

## Criterios de aceptación

### Camino feliz

**AC-1 — Un SELECT sobre una vista permitida se ejecuta**
- **Dado** la base de la capa semántica abierta
- **Cuando** se valida `SELECT COUNT(*) AS n FROM v_reservas_cliente`
- **Entonces** el resultado es correcto (`ok = True`)
- **Y** el texto es el JSON de una fila con la clave `n`

**AC-2 — Un JOIN entre vistas permitidas se ejecuta**
- **Dado** la base de la capa semántica abierta
- **Cuando** se valida un `SELECT` que une `v_reservas_cliente` y `v_resumen_clientes` por `cliente_id`
- **Entonces** el resultado es correcto (`ok = True`)

### Casos límite

**AC-3 — Más de 50 filas se recortan y se avisa**
- **Dado** una vista con más de 50 filas
- **Cuando** se valida un `SELECT *` sobre ella
- **Entonces** el JSON trae exactamente 50 filas
- **Y** el texto termina con «(resultado recortado a 50 filas)»

**AC-4 — Un punto y coma final y espacios no molestan**
- **Dado** la base abierta
- **Cuando** se valida `"  SELECT COUNT(*) FROM v_incidencias;  "`
- **Entonces** el resultado es correcto (`ok = True`)

**AC-5 — Un CTE sobre vistas permitidas se acepta**
- **Dado** la base abierta
- **Cuando** se valida `WITH r AS (SELECT * FROM v_reservas_cliente) SELECT COUNT(*) FROM r`
- **Entonces** el resultado es correcto: el nombre del CTE `r` no cuenta como vista no permitida

### Errores

**AC-6 — Leer una tabla cruda se rechaza**
- **Dado** la base abierta
- **Cuando** se valida `SELECT * FROM crudo.clientes`
- **Entonces** `ok = False` y el mensaje dice que `crudo.clientes` no está permitida y lista las vistas que sí lo están
- **Y** la consulta no se ejecuta

**AC-7 — Leer el catálogo de la base se rechaza**
- **Dado** la base abierta
- **Cuando** se valida `SELECT * FROM information_schema.tables`
- **Entonces** `ok = False` con el mensaje de vista no permitida

**AC-8 — Una sentencia que no es SELECT se rechaza**
- **Dado** la base abierta
- **Cuando** se valida `DELETE FROM v_incidencias`
- **Entonces** `ok = False` y el mensaje es «solo se permiten consultas SELECT (recibido: DELETE)»
- **Y** `v_incidencias` tiene las mismas filas que antes

**AC-9 — Varias sentencias se rechazan**
- **Dado** la base abierta
- **Cuando** se valida `SELECT 1 FROM v_incidencias; SELECT 2 FROM v_incidencias`
- **Entonces** `ok = False` y el mensaje es «envía exactamente una sentencia»

**AC-10 — SQL vacío o con errores de sintaxis da un error controlado**
- **Dado** la base abierta
- **Cuando** se valida `""` y, aparte, `SELEC * FROM v_incidencias`
- **Entonces** las dos dan `ok = False` con un texto que empieza por «ERROR», sin lanzar excepción

### No funcionales

**AC-11 — No se pueden leer archivos del disco**
- **Dado** la base abierta
- **Cuando** se valida `SELECT * FROM read_csv_auto('/etc/passwd')`
- **Entonces** `ok = False` y no se lee el archivo

## Definición de hecho

- [ ] Cada AC cubierto por un test automático que pasa
- [ ] Toda la suite del proyecto en verde (`uv run pytest`)
- [ ] ruff y ty limpios
- [ ] `text2sql/AGENTS.md` actualizado (archivo nuevo `guard.py`; pasa de fase 0) y la fila 5 de `travel-agency/AGENTS.md` con lo que se siguió de clase y los desvíos
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- `MAX_ROWS = 50`, como en clase (`PROYECTO.md` no da otra cifra).
- Los nombres de vista se comparan sin distinguir mayúsculas, porque DuckDB tampoco lo hace.

**Preguntas abiertas**
- ¿De dónde sale `ALLOWED_VIEWS`? Leerla de las claves de `COMMENTS` de `database` evita duplicar la lista, pero importa un módulo interno de otro paquete (lo prohíbe `travel-agency/AGENTS.md`). ¿Se expone desde `database` como parte de su función pública o se copia en `text2sql`?
- ¿Basta `json_serialize_sql` de DuckDB para sacar las tablas, o se acepta `sqlglot` como dependencia nueva (sería otro desvío)?
