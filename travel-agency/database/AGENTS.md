# AGENTS.md — `database/`

> Estado: **fase 2 terminada**: 2a (CSV a mano + capa semántica) y 2b (generador con semilla fija, ticket
> `docs/tickets/TRAVEL-001`): `data/` tiene miles de filas generadas a partir de las de `fixtures/`, que siguen dentro como casos ancla.

## Propósito

Los datos de Viajes Nimbo: **`data/`, la fuente de verdad que abre la app** (8 CSV con miles de filas), las filas
escritas a mano de las que sale (`fixtures/`, también los datos de los tests) y la **capa semántica** que el LLM text-to-SQL verá en lugar de las tablas (sección 3 de [`../PROYECTO.md`](../PROYECTO.md)). Son datos: no sabe nada de LLMs.

**Se implementa igual que en clase**: `semantic_layer.py` ejecuta el mismo código que
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py` (nombres y archivos pueden
cambiar). Antes de cambiar algo, mira cómo está allí.

## Archivos clave

```
data/*.csv                       # la fuente de verdad: fixtures + ~15.000 filas generadas (semilla 42, subido a git)
fixtures/*.csv                   # 8 tablas, ~80 filas a mano; cada fila rara está ahí por una trampa. Datos de los tests
src/database/semantic_layer.py   # VIEWS, COMMENTS, GUIDE, open_db(), schema(), CHECKS, run_checks()
src/database/seed.py             # generate(source_dir, out_dir, seed) y el comando: fixtures/ → data/
tests/test_database_audit.py     # auditoría de integridad (como 02_auditoria_integridad.py de la clase 1); AUDIT_QUERIES
tests/test_database_semantic_layer.py
tests/test_database_seed.py      # un test por AC de TRAVEL-001 sobre el conjunto generado
```

## Funciones públicas

```python
from database.semantic_layer import open_db, schema, GUIDE

con = open_db()      # DuckDB EN MEMORIA: CSV → esquema crudo, vistas v_* en main, COMMENT ON, sin acceso a archivos
text = schema(con)   # lo que verá el LLM: vistas, columnas, tipos, valores/ejemplo y comentarios (~4 s)
```

Desvío de la regla "una función pública por paquete": aquí son tres (`open_db`, `schema`, `GUIDE`), como en clase, porque
text2sql necesita la conexión y el texto por separado. No usan tipos de `contracts/` (son datos, no resultados).

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv run python -m database.semantic_layer           # lo que ve el modelo (y lo que no)
uv run python -m database.semantic_layer --check --data database/fixtures   # las cifras calculadas a mano
uv run python -m database.seed                     # regenera data/ desde fixtures/ (--seed N, --source, --out)
uv run pytest database/tests
```

Sin variables de entorno: la base se construye en memoria desde `data/` cada vez (como `abrir()` en clase, aquí `open_db()`).
Los tests abren las filas a mano: `open_db(FIXTURES_DIR)`, con `FIXTURES_DIR` de `database.seed` (también en
`text2sql/tests`). `semantic_layer.py` no nombra `fixtures/` (es lo que usa la app): `--check` va con
`--data database/fixtures` porque los `CHECKS` globales (7 reservas, 1.849 €) solo cuadran ahí; sobre `data/` fallan.

## Las trampas, fila a fila

| Trampa | Filas | Comprobación |
|---|---|---|
| Reserva ≠ vuelo | 7 reservas, 12 tramos | `SUM(tramos)` = 12 |
| Bruto vs neto | R-1042 (reembolso parcial), R-1045 (total), R-1048 | cobrado 2.319 €, neto 1.849 € |
| JOIN que duplica | R-1046: 2 tramos × 2 cargos | join directo 3.543 € frente a 1.849 € |
| Retraso a la llegada, no a la salida | VY1234: sale +200 min, llega +175 | `retraso_llegada_min` |
| Escala: distancia del viaje | R-1044 AMS → BCN → MAD: 1.461 km (la suma daría 1.724) | `v_itinerarios` |
| Zonas horarias | IB3166 MAD → JFK, MAD → TFN (Canarias) | duración 510 y 160 min |
| Cruce de medianoche | FR7312 | retraso 165 min |
| NULL ≠ 0 | IB0731 (programado), AF1001 (cancelado) | retraso NULL |
| Nombres repetidos | C-001 y C-004, las dos "Ana López" | distinguir por `cliente_id` |
| Cliente sin reservas | C-007 | aparece con 0 |

## Decisiones y trampas

- **Sin punto y coma dentro de los comentarios SQL de `VIEWS`**: se parte por `;`, como en clase.
- `COMMENT ON` de una columna que no existe hace fallar `open_db()`: los comentarios no se pueden quedar huérfanos.
- `crudo.*` sigue siendo consultable (igual que en clase): la lista blanca de vistas la pone el validador de
  text2sql (`text2sql/guard.py`).
- `schema()` hace ~200 consultas sobre vistas anidadas (~4 s): calcúlalo una vez al arrancar, no en cada pregunta.
  En los tests va en una fixture de sesión (`schema_text`).
- `email` existe en `crudo.clientes`, pero ninguna vista lo enseña (sin datos de contacto para el modelo).
- Las horas van en ISO 8601 con desfase; DuckDB las lee como `TIMESTAMP WITH TIME ZONE`. Los minutos se calculan con
  `epoch()`, y la hora local con `timezone(zona_horaria, …)`.
- `reservas_tramos.trayecto` (ida / vuelta) no estaba en el diseño inicial: sin él, el destino final de un ida y
  vuelta sería el aeropuerto de salida.
- `compensacion` de `incidencias` no es un pago de la reserva: no está en `pagos`.
- Si cambias un CSV, recalcula a mano las cifras de `CHECKS` (no las copies de lo que dé la vista).
- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.

## El generador (`seed.py`, fase 2b)

**No tiene referencia en el repo** (en clase los datos venían hechos): lo decidió Mario ciclo a ciclo (ticket TRAVEL-001).

- **Sin Faker**: nombres y apellidos en listas escritas a mano + `random.Random(semilla)`. Todos los repartos
  (10 % de reservas canceladas, 5 % de vuelos cancelados, 20 % retrasados…) son constantes al principio del archivo.
- **`data/` se genera, no se edita a mano**: el comando la sobrescribe entera. Las filas a mano (trampas, R-1042,
  IB3166…) se editan en `fixtures/` y luego se regenera. Normalmente se ejecuta una vez y se sube a git.
- Los tests van sobre `fixtures/`: los `CHECKS` globales (7 reservas, neto 1.849 €) solo cuadran ahí. Sobre el conjunto
  generado pasan la auditoría y los `CHECKS` que miran un id.
- **Si cambias el generador o `fixtures/`, regenera y sube `data/`**: `test_database_seed_same_seed_same_bytes` la
  compara byte a byte con lo que da el generador. Cualquier llamada nueva a `rng` (o en otro orden) cambia todos los
  datos que vienen después.
- `schema()` tarda ~4,8 s sobre `data/` (~4,2 s sobre `fixtures/`); `open_db()`, ~0,5 s.
- Fecha de corte `CUTOFF = 2026-11-01` («hoy»): lo que sale desde ese día está `programado`, y nada (reservas,
  pagos, incidencias) tiene fecha de ese día o posterior.
- Horas: la salida es una hora local del origen (06:00-22:55, así no cae en la hora que no existe al cambiar la hora);
  las sumas de tiempo se hacen en UTC y se escriben con `zoneinfo`. La distancia es la haversine de `VIEWS` en Python.
- Itinerarios: 70 % solo ida, 20 % ida y vuelta, 10 % con escala. El vuelo de escala o de vuelta se crea para la
  reserva (`_Fleet`), con código único en todo el conjunto.
- Reglamento 261/2004 simplificado (sin la reducción del art. 7.2 ni circunstancias extraordinarias): retraso del
  viaje ≥ 180 min o cancelación → 250 / 400 / 600 € según la distancia del viaje; menos de 180 min → `rechazada`.
- Sin telemetría (decidido el 2026-11-07): el generador es determinista y se ejecuta a mano; `database` no depende de
  `telemetry` ni de `contracts`.
- 12 aeropuertos añadidos al final de `fixtures/aeropuertos.csv` (coordenadas de OurAirports); las 8 primeras filas no se
  tocan porque los `CHECKS` de distancia salen de ellas (MAD difiere ~2,5 km de OurAirports).
