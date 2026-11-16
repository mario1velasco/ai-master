# TRAVEL-010 · Vista `v_tramos`: clase, asiento, maleta, aerolínea y retraso de cada vuelo de una reserva

> **Nombres en el código, en inglés:** funciones, clases, variables, constantes, parámetros, archivos y también las
> tools que ve el modelo y sus parámetros (p. ej. `query_db(question)`, como `run_sql(query)`). En castellano solo
> los comentarios, la documentación y los textos que lee el modelo (prompts y descripciones de tools).

| Campo | Valor |
|---|---|
| Tipo | Task |
| Carpeta del proyecto | `travel-agency/` (`database/`) |
| Estado | Hecho (2026-11-16) |
| Creado | 2026-11-16 |
| Etiquetas | database, capa-semantica, fase-2, fase-5 |

## Historia de usuario

**Como** cliente de Viajes Nimbo que pregunta por el chat, **quiero** que el agente sepa la clase, el asiento, si
llevo maleta facturada, con qué aerolínea vuelo y si mi vuelo se retrasó, **para que** me responda con mis datos en
lugar de decir que no los tiene.

## Contexto

Las preguntas típicas de un cliente por chat son sobre **su** reserva y **su** vuelo: estado, horas, retraso,
equipaje, compañía (investigado para TRAVEL-008; el FAQ propio, `rag/corpus/empresa/atencion/preguntas_frecuentes.md`,
dice que «en Mis reservas, cada tramo indica si lleva equipaje facturado»). `clase`, `asiento` y
`equipaje_facturado` existen en `crudo.reservas_tramos` (PROYECTO.md §3), pero ninguna vista los enseña: las vistas
usan esa tabla solo para contar tramos (`v_reservas_cliente`) o sacar el viaje (`v_itinerarios`), y el validador de
text2sql prohíbe `crudo`. Tampoco hay forma limpia de saber la aerolínea de cada vuelo de una reserva:
`v_itinerarios` solo trae `codigos_vuelo` como texto (`'KL1701 + VY1002'`). No fue una decisión (no están en «datos
que NO existen» de la `GUIDE`): se quedaron fuera al diseñar las vistas para los cálculos del negocio. Va **antes de
la medida de TRAVEL-008**, para que la línea base no penalice al modelo por un dato que la base tiene y no le enseña.

**Referencias leídas:**
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/02_capa_semantica.py` (tema 7): `ventas_lineas`,
  una fila por línea de pedido con los datos de su producto ya pegados; `COMENTARIOS`, `GUIA` y `COMPROBACIONES`.
- `database/src/database/semantic_layer.py`, `checks.py`, `database/AGENTS.md` y sus tests; `text2sql/guard.py`
  (lista blanca = las vistas de `main`).
- `PROYECTO.md` §3 (tablas y vistas) y la investigación de preguntas de cliente de TRAVEL-008.

**Desvíos respecto al patrón de clase:** ninguno. `v_tramos` es a la reserva lo que `ventas_lineas` al pedido: una
fila por línea con lo de su vuelo pegado, más su entrada en `COMMENTS`, `GUIDE` y `CHECKS`.

## Alcance

**Dentro**
- Vista `v_tramos`, una fila por vuelo de cada reserva, con: `reserva_id`, `cliente_id`, `trayecto`, `orden`,
  `vuelo_id`, `codigo_vuelo`, `aerolinea`, `origen`, `ciudad_origen`, `destino`, `ciudad_destino`, `clase`, `asiento`,
  `equipaje_facturado`, `retraso_salida_min`, `retraso_llegada_min` y `estado_vuelo` (decidido con Mario el
  2026-11-16: la opción media más el retraso y el estado).
- `equipaje_facturado` como booleano y `asiento` NULL cuando aún no está asignado (decidido con Mario).
- Sus comentarios (vista y columnas), su línea en la `GUIDE` y sus comprobaciones en `CHECKS`.

**Fuera**
- Horas de salida y llegada en `v_tramos`: siguen en `v_vuelos_detalle` (preguntas de dos vistas, como «¿a qué hora
  sale mi vuelo de la R-1042?»).
- Cambiar las otras cinco vistas, `fixtures/` o `data/`.
- Rehacer los exámenes de TRAVEL-008 con preguntas de cliente (se hace en TRAVEL-008, después de este ticket).
- Modo cliente (filtrar por `cliente_id`): decisión pendiente 3 de `PROYECTO.md` §10.

## Criterios de aceptación

### Camino feliz

**AC-1 — Una fila por vuelo de cada reserva**
- **Dado** la base de `fixtures/`
- **Cuando** se consulta `v_tramos`
- **Entonces** devuelve 12 filas, las mismas que `SUM(tramos)` de `v_reservas_cliente`
- **Y** sobre `data/` devuelve 3.855

**AC-2 — Clase, asiento y maleta de un vuelo de la reserva**
- **Dado** la base de `fixtures/`
- **Cuando** se consulta el tramo de ida de R-1042 en `v_tramos`
- **Entonces** devuelve IB3166, Iberia, MAD (Madrid) → JFK (Nueva York), clase `turista`, asiento `23A` y
  `equipaje_facturado = true`

**AC-3 — Retraso y estado del vuelo de cada tramo**
- **Dado** la base de `fixtures/`
- **Cuando** se consulta el tramo de ida de R-1042 en `v_tramos`
- **Entonces** devuelve `retraso_salida_min = 297`, `retraso_llegada_min = 312` y `estado_vuelo = 'retrasado'`,
  los mismos valores que IB3166 en `v_vuelos_detalle`

**AC-4 — Cada vuelo de una escala con su aerolínea**
- **Dado** la base de `fixtures/`
- **Cuando** se consultan los tramos de R-1044 en `v_tramos`
- **Entonces** devuelve dos filas de ida: orden 1, KL1701 de KLM; orden 2, VY1002 de Vueling

**AC-5 — El modelo ve la vista y sabe cuándo usarla**
- **Dado** el esquema generado y la `GUIDE`
- **Cuando** se leen
- **Entonces** el esquema incluye `v_tramos` con los comentarios de `clase`, `asiento`, `equipaje_facturado`,
  `retraso_salida_min` y `retraso_llegada_min`
- **Y** la `GUIDE` dice que `v_tramos` es la vista para la clase, el asiento, la maleta o la aerolínea de cada vuelo
  de una reserva

### Casos límite

**AC-6 — Asiento todavía sin asignar**
- **Dado** R-1047 en `fixtures/` (vuelo IB0731, programado, sin asiento en el CSV)
- **Cuando** se consulta su tramo en `v_tramos`
- **Entonces** `asiento` es NULL (no una cadena vacía) y los dos retrasos son NULL

**AC-7 — Vuelo cancelado**
- **Dado** el tramo de ida de R-1045 en `fixtures/` (AF1001, cancelado)
- **Cuando** se consulta en `v_tramos`
- **Entonces** devuelve `estado_vuelo = 'cancelado'`, `retraso_llegada_min` NULL y clase `business`

**AC-8 — Tramo sin maleta facturada**
- **Dado** el tramo de ida de R-1043 en `fixtures/` (`equipaje_facturado = 0` en el CSV)
- **Cuando** se consulta en `v_tramos`
- **Entonces** `equipaje_facturado` es el booleano `false`, no el número 0

**AC-9 — El mismo vuelo en dos reservas**
- **Dado** el vuelo AF1300 en `fixtures/`, que está en R-1045 (vuelta) y en R-1048
- **Cuando** se consultan sus tramos en `v_tramos`
- **Entonces** salen dos filas, una por reserva, cada una con lo suyo: R-1045 en `business` con maleta y R-1048 en
  `turista` sin maleta

### Errores

No aplica: es una vista de solo lectura sin entrada del usuario.

**Regresiones**

**AC-10 — Las vistas y las cifras de antes no cambian**
- **Dado** la base de `fixtures/`
- **Cuando** se ejecuta `uv run python -m database.semantic_layer --check --data database/fixtures`
- **Entonces** todas las comprobaciones que ya había siguen en ✓, junto con las nuevas de `v_tramos`

**AC-11 — El validador de text2sql acepta la vista nueva**
- **Dado** la base de `data/`
- **Cuando** se valida `SELECT clase, asiento FROM v_tramos WHERE reserva_id = 'R-1042'`
- **Entonces** pasa el validador y devuelve 2 filas
- **Y** el mensaje de vista no permitida (p. ej. ante `crudo.reservas_tramos`) lista las 6 vistas, `v_tramos` incluida

### No funcionales

Ninguno para este ticket.

## Definición de hecho

- [x] Cada AC cubierto por un test automático en verde (`database/tests/test_database_legs_view.py`, AC-1 a AC-10; `text2sql/tests/test_text2sql_guard.py::test_legs_view_is_allowed_and_listed`, AC-11)
- [x] Toda la suite del proyecto en verde (`uv run pytest`: 314 passed)
- [x] ruff y ty sin errores (los 5 avisos de `ruff format --check` son de bloques de código en Markdown y ya estaban antes)
- [x] `database/AGENTS.md` (vistas, tabla de trampas con el asiento NULL), `PROYECTO.md` §3 (tabla de vistas) y la
      fila 2 de `travel-agency/AGENTS.md` actualizados
- [x] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- El nombre `v_tramos` y sus columnas van en castellano, como las otras cinco vistas: son datos de la base, no
  nombres de código.
- Los dos retrasos van con los mismos comentarios que en `v_vuelos_detalle` (el que cuenta para compensar es el de
  la llegada), para que la trampa del retraso a la salida se lea igual en las dos vistas.
- El esquema guardado (TRAVEL-009) se regenera solo, porque cambia `semantic_layer.py`: no hace falta borrar nada.
- La lista blanca del validador sale de las vistas de `main`, así que `v_tramos` entra sin tocar `text2sql/guard.py`.

**Preguntas abiertas**
- Ninguna.
