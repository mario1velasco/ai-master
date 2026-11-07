# AGENTS.md — `database/`

> Estado: **fase 2 terminada**: 2a (CSV a mano + capa semántica) y 2b (generador con semilla fija, ticket
> `docs/tickets/TRAVEL-001`): `data_generated/` amplía a miles de filas **conservando las filas a mano** como casos ancla.

## Propósito

Los datos de Viajes Nimbo: 8 CSV escritos por nosotros (`data/`), el conjunto grande generado a partir de ellos
(`data_generated/`) y la **capa semántica** que el LLM text-to-SQL verá en lugar de las tablas (sección 3 de [`../PROYECTO.md`](../PROYECTO.md)). Son datos: no sabe nada de LLMs.

**Se implementa igual que en clase**: `semantic_layer.py` ejecuta el mismo código que
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py` (nombres y archivos pueden
cambiar). Antes de cambiar algo, mira cómo está allí.

## Archivos clave

```
data/*.csv                       # 8 tablas, ~80 filas a mano; cada fila rara está ahí por una trampa
data_generated/*.csv             # las filas a mano + ~15.000 generadas con la semilla 42 (subido a git)
src/database/semantic_layer.py   # VIEWS, COMMENTS, GUIDE, open_db(), schema(), CHECKS, run_checks()
src/database/seed.py             # generate(source_dir, out_dir, seed) y el comando: escribe data_generated/
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
uv run python -m database.semantic_layer --check   # las vistas dan las cifras calculadas a mano
uv run python -m database.seed                     # regenera data_generated/ (--seed N, --source, --out)
uv run pytest database/tests
```

Sin variables de entorno: la base se construye en memoria desde `data/` cada vez (como `abrir()` en clase, aquí `open_db()`).
Para abrir el conjunto grande: `open_db(GENERATED_DIR)` (de `database.seed`).

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
- `data/` sigue siendo la base exacta de los tests: los `CHECKS` globales (7 reservas, neto 1.849 €) solo cuadran ahí.
  Sobre `data_generated/` pasan la auditoría y los `CHECKS` que miran un id.
- **Si cambias el generador, regenera y sube `data_generated/`**: `test_database_seed_same_seed_same_bytes` compara
  byte a byte. Cualquier llamada nueva a `rng` (o en otro orden) cambia todos los datos que vienen después.
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
- 12 aeropuertos añadidos al final de `data/aeropuertos.csv` (coordenadas de OurAirports); las 8 primeras filas no se
  tocan porque los `CHECKS` de distancia salen de ellas (MAD difiere ~2,5 km de OurAirports).
