# TRAVEL-008 · Examen de text2sql y primera medida con el Qwen real

> **Nombres en el código, en inglés:** funciones, clases, variables, constantes, parámetros, archivos y también las
> tools que ve el modelo y sus parámetros (p. ej. `query_db(question)`, como `run_sql(query)`). En castellano solo
> los comentarios, la documentación y los textos que lee el modelo (prompts y descripciones de tools).

| Campo | Valor |
|---|---|
| Tipo | Task |
| Carpeta del proyecto | `travel-agency/` (`text2sql/`) |
| Estado | En curso: exámenes hechos (batería 37, final 18; 2026-11-16), falta la medida con el Qwen real |
| Creado | 2026-11-13 |
| Etiquetas | text2sql, eval, dataset, fase-5 |

## Historia de usuario

**Como** desarrollador de Viajes Nimbo, **quiero** un examen de ~50 preguntas escritas a mano, con su SQL de
referencia y repartidas en batería y examen final, y una primera medida de `text2sql` con el Qwen real, **para que**
la fase 5 quede cerrada con una línea base contra la que comparar cualquier cambio.

## Contexto

TRAVEL-007 deja la herramienta de medir (formato del examen, corrector, métricas e informe), con solo unas preguntas
de ejemplo para los tests. Este ticket es el **entregable de datos**: las preguntas reales y la medida. No lleva
código ni tests nuevos: se comprueba con el propio comando de evaluación (`--view`) y revisando. `PROYECTO.md` §6 pide
«~50 a mano: una por cada trampa de la sección 3, núcleo del conjunto de test», con validación automática de cada
ejemplo; §9 pide categorías normal / borde / adversario, k = 3 y pass^3.

**Referencia principal: el tema 9** (`09_evaluacion_fiabilidad_seguridad/`, sesión 1 y su
`explicacion-09.md`): manda sobre el resto para desarrollar este ticket (categorías normal / borde / adversario,
k = 3 y pass^3, casos de regresión). El tema 7 solo para lo que el tema 9 no cubre (examen reservado, tipo de cada
pregunta).

**Referencias leídas:**
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/examen/{bateria,validacion,prueba_final}.json`
  (tema 7): preguntas variadas, cada una con su tipo («qué pone a prueba»), su respuesta calculada con un SQL revisado
  y una nota; las imposibles con `debe_negar`; exámenes separados para no ajustar el prompt al examen.
- `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/casos.json` (tema 9): casos normales, de borde y
  adversarios; el deber base pide «al menos uno de cada categoría».
- `PROYECTO.md` §3 (las siete trampas), §6 (dataset y validación) y §9 (categorías, regresiones, umbrales);
  TRAVEL-007 (formato y comando).

**Desvíos respecto al patrón de clase:**
- Dos exámenes (batería ~35 y final ~15), no tres (decidido con Mario).
- Las respuestas esperadas no se copian a mano: las da el SQL de referencia de cada pregunta (desvío de TRAVEL-007).

## Alcance

**Dentro**
- `battery.json` (~35 preguntas, con ella se puede ajustar el prompt) y `final_test.json` (~15, reservado), en
  `src/text2sql/evaluation/exams/` (TRAVEL-007).
- Cada pregunta con las claves de TRAVEL-007: `category`, `trap` (o `null`), `question` (en castellano, como la haría
  un empleado), y `sql` o `must_deny: true`. Las vistas esperadas no se escriben: salen del `sql` (TRAVEL-007).
- Valores de `trap`, traducidos tal cual de `PROYECTO.md` §3 (decidido con Mario el 2026-11-15):

  | §3 | `trap` |
  |---|---|
  | Reserva ≠ tramo ≠ pasajero | `booking_vs_segment_vs_passenger` |
  | Importe bruto vs neto | `gross_vs_net_amount` |
  | Retraso a la llegada, no a la salida | `arrival_delay_not_departure` |
  | Vuelos con escala | `flights_with_layover` |
  | Zonas horarias | `time_zones` |
  | Nombres repetidos | `repeated_names` |
  | Datos ausentes | `missing_data` |
- Primera medida con el Qwen real de los dos exámenes, con `--repetitions 3`, y su resumen como línea base.

**Fuera**
- Mejorar `text2sql` según lo que salga (prompt, ejemplos dinámicos, consultas fijas): tickets siguientes si la
  medida lo pide (escalera de `PROYECTO.md` §6).
- Plantillas y paráfrasis del dataset (fase 9, opcional).
- Fijar los umbrales de despliegue de `PROYECTO.md` §9 (se deciden con Mario a la vista de la medida).

## Criterios de aceptación

### Camino feliz

**AC-1 — Los dos exámenes existen con su tamaño**
- **Dado** la batería y el examen final
- **Cuando** se ejecuta el comando de evaluación con `--view` para cada uno
- **Entonces** la batería enseña entre 30 y 40 preguntas y el final entre 12 y 18, sin error

**AC-2 — Cada trampa de la base tiene al menos una pregunta**
- **Dado** las siete trampas de `PROYECTO.md` §3 (reserva ≠ tramo ≠ pasajero, bruto frente a neto, retraso a la
  llegada, vuelos con escala, zonas horarias, nombres repetidos, datos ausentes)
- **Cuando** se revisa la salida de `--view` de la batería
- **Entonces** cada trampa aparece en al menos una pregunta

**AC-3 — Cada examen tiene preguntas de las tres categorías**
- **Dado** la batería y el examen final
- **Cuando** se revisa la salida de `--view` de cada uno
- **Entonces** cada examen tiene al menos una pregunta `normal`, una `edge` y una `adversarial`
- **Y** entre las `edge` hay al menos una imposible (`must_deny`: un dato que la base no tiene) y una sobre un cliente o una
  reserva que no existen

**AC-4 — La primera medida queda guardada y resumida como línea base**
- **Dado** los dos exámenes y `qwen3:4b-instruct` en Ollama
- **Cuando** se ejecuta la evaluación de cada examen con `--repetitions 3`
- **Entonces** quedan guardados sus dos archivos de resultados en `text2sql/evaluation_results/`
- **Y** `text2sql/AGENTS.md` tiene una tabla de línea base con la fecha, el modelo, la versión del prompt y, por examen:
  tasa de éxito, pass^3, pass@3, latencia p50 y p95, disponibilidad, coste por caso resuelto, aprobados a la primera,
  intentos con algún SQL rechazado, los aciertos por categoría y por trampa, y una fila «Suspensos: vista equivocada /
  vista correcta, filas malas / otros» con los recuentos (AC-15 de TRAVEL-007), que dice qué arreglar primero
- **Y** debajo de la tabla, una línea por métrica que diga qué mide (remite a la tabla de métricas de TRAVEL-007)

### Casos límite

**AC-5 — Cada referencia usa la vista que toca**
- **Dado** las preguntas con SQL de referencia
- **Cuando** se revisan en la salida de `--view` (que enseña las vistas que usa cada SQL)
- **Entonces** cada una usa la vista que mejor responde a la pregunta (p. ej. el gasto neto, de la vista que ya lo
  calcula, no sumando pagos), porque esas vistas son las esperadas del diagnóstico «vista equivocada»

**AC-6 — Las referencias sin filas son intencionadas**
- **Dado** las preguntas cuyo SQL de referencia devuelve 0 filas
- **Cuando** se revisan en la salida de `--view`
- **Entonces** todas son de la categoría `edge` (p. ej. cliente o reserva que no existen); son las que `--view` marca
  con «0 filas, revisar» (AC-5 de TRAVEL-007)

**AC-7 — El examen final no repite la batería**
- **Dado** los dos exámenes
- **Cuando** se revisan
- **Entonces** ninguna pregunta del final es la misma, ni una paráfrasis, de una de la batería
- **Y** los ids no se repiten entre los dos

### Errores

**AC-8 — Todas las referencias pasan el validador**
- **Dado** los dos exámenes
- **Cuando** se ejecuta `--view` (que se para ante una referencia que no pasa el validador o un id repetido, AC-16 de
  TRAVEL-007)
- **Entonces** termina con código 0 en los dos

### No funcionales

**AC-9 — La regla del examen reservado queda escrita**
- **Dado** `text2sql/AGENTS.md`
- **Cuando** se lee la sección de evaluación
- **Entonces** dice que el examen final no se usa para ajustar el prompt ni los ejemplos, solo para medir

## Definición de hecho

- [ ] Cada AC comprobado con el comando o la revisión que nombra
- [ ] Toda la suite del proyecto en verde (`uv run pytest`)
- [ ] Fila 5 de `travel-agency/AGENTS.md` en ✅ con la línea base, y `PROYECTO.md` §6 si la medida cambia algo de lo
      escrito
- [ ] Los pasos para lanzar la medida (Supuestos) en `travel-agency/README.md` («Comandos útiles») y en
      `travel-agency/AGENTS.md` («Entorno»). Cuando toque lanzarla, Claude se los indica a Mario paso a paso
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- Las preguntas las redacta Claude y Mario las aprueba por bloques (como los repartos de TRAVEL-001), con el SQL de
  referencia y el resultado a la vista (`--view`).
- Los tamaños (30–40 y 12–18) traducen las «~35 y ~15» acordadas; se pueden mover si al escribirlas sale otro reparto.
- Las preguntas son **de cliente con su identificador** (su reserva, su vuelo, su maleta, su reclamación), como el
  agente se las pasaría a `query_db`, y unas pocas de gestión (decidido con Mario el 2026-11-16, tras investigar qué
  pregunta un cliente por chat: estado del vuelo y de la reserva, equipaje, compañía, reembolsos). Se responden en
  modo empleado (acceso a todas las vistas); el modo cliente es la decisión pendiente 3 de `PROYECTO.md` §10, y por eso
  no hay adversarias del tipo «dame las reservas de otro cliente».
- Las preguntas de clase, asiento, maleta y aerolínea necesitan `v_tramos` (TRAVEL-010, hecho antes de medir).
- Hay preguntas de **dos vistas** en los dos exámenes (6 en la batería y 4 en el final): datos que solo están en otra
  vista (nivel o país del cliente, tipo de reserva, horas del vuelo) obligan a un JOIN, que es donde más falla un 4B.
- La medida la lanza Mario a mano (~45 min con el Qwen real) y Claude escribe la tabla de línea base a partir de los
  archivos de resultados. Pasos, desde `travel-agency/`:
  1. Ollama arrancado y el modelo instalado: `ollama list` muestra `qwen3:4b-instruct` (si no,
     `ollama pull qwen3:4b-instruct`).
  2. `uv sync`.
  3. Comprobar los exámenes sin modelo: `uv run python -m text2sql.evaluation --exam battery --view` y lo mismo con
     `--exam final_test`. Los dos terminan sin error.
  4. Calentar el modelo (el primer arranque tarda ~150 s): `uv run python -m text2sql -q "¿Cuántas reservas tiene C-001?"`.
     De todos modos, el comando descarta el arranque en frío de la latencia (AC-12 de TRAVEL-007).
  5. `uv run python -m text2sql.evaluation --exam battery --repetitions 3` (~30 min).
  6. `uv run python -m text2sql.evaluation --exam final_test --repetitions 3` (~13 min).
  7. Avisar a Claude: los resultados quedan en `text2sql/evaluation_results/`.

**Preguntas abiertas**
- Ninguna.
