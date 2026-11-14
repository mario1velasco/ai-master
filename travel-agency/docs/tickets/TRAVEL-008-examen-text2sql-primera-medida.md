# TRAVEL-008 · Examen de text2sql y primera medida con el Qwen real

| Campo | Valor |
|---|---|
| Tipo | Task |
| Carpeta del proyecto | `travel-agency/` (`text2sql/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-13 |
| Etiquetas | text2sql, eval, dataset, fase-5 |

## Historia de usuario

**Como** desarrollador de Viajes Nimbo, **quiero** un examen de ~50 preguntas escritas a mano, con su SQL de
referencia y repartidas en batería y examen final, y una primera medida de `text2sql` con el Qwen real, **para que**
la fase 5 quede cerrada con una línea base contra la que comparar cualquier cambio.

## Contexto

TRAVEL-007 deja la herramienta de medir (formato del examen, corrector, métricas e informe), con solo unas preguntas
de ejemplo para los tests. Este ticket es el **entregable de datos**: las preguntas reales y la medida. No lleva
código ni tests nuevos: se comprueba con el propio comando de evaluación (`--ver`) y revisando. `PROYECTO.md` §6 pide
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
- Batería (~35 preguntas, con ella se puede ajustar el prompt) y examen final (~15, reservado).
- Cada pregunta con categoría, trampa (o ninguna), pregunta en castellano como la haría un empleado, vistas
  esperadas, y SQL de referencia o marca de imposible.
- Primera medida con el Qwen real de los dos exámenes, con `--repeticiones 3`, y su resumen como línea base.

**Fuera**
- Mejorar `text2sql` según lo que salga (prompt, ejemplos dinámicos, consultas fijas): tickets siguientes si la
  medida lo pide (escalera de `PROYECTO.md` §6).
- Plantillas y paráfrasis del dataset (fase 9, opcional).
- Fijar los umbrales de despliegue de `PROYECTO.md` §9 (se deciden con Mario a la vista de la medida).

## Criterios de aceptación

### Camino feliz

**AC-1 — Los dos exámenes existen con su tamaño**
- **Dado** la batería y el examen final
- **Cuando** se ejecuta el comando de evaluación con `--ver` para cada uno
- **Entonces** la batería enseña entre 30 y 40 preguntas y el final entre 12 y 18, sin error

**AC-2 — Cada trampa de la base tiene al menos una pregunta**
- **Dado** las siete trampas de `PROYECTO.md` §3 (reserva ≠ tramo ≠ pasajero, bruto frente a neto, retraso a la
  llegada, vuelos con escala, zonas horarias, nombres repetidos, datos ausentes)
- **Cuando** se revisa la salida de `--ver` de la batería
- **Entonces** cada trampa aparece en al menos una pregunta

**AC-3 — Cada examen tiene preguntas de las tres categorías**
- **Dado** la batería y el examen final
- **Cuando** se revisa la salida de `--ver` de cada uno
- **Entonces** cada examen tiene al menos una pregunta `normal`, una `borde` y una `adversario`
- **Y** entre las de borde hay al menos una imposible (un dato que la base no tiene) y una sobre un cliente o una
  reserva que no existen

**AC-4 — La primera medida queda guardada y resumida como línea base**
- **Dado** los dos exámenes y `qwen3:4b-instruct` en Ollama
- **Cuando** se ejecuta la evaluación de cada examen con `--repeticiones 3`
- **Entonces** quedan guardados sus dos archivos de resultados
- **Y** `text2sql/AGENTS.md` tiene una tabla de línea base con la fecha, el modelo, la versión del prompt y, por examen:
  tasa de éxito, pass^3, pass@3, latencia p50 y p95, disponibilidad, coste por caso resuelto y los aciertos por
  categoría y por trampa

### Casos límite

**AC-5 — Las vistas esperadas cuadran con la referencia**
- **Dado** las preguntas con SQL de referencia
- **Cuando** se revisan en la salida de `--ver`
- **Entonces** las vistas esperadas de cada una son las que usa su SQL de referencia

**AC-6 — Las referencias sin filas son intencionadas**
- **Dado** las preguntas cuyo SQL de referencia devuelve 0 filas
- **Cuando** se revisan en la salida de `--ver`
- **Entonces** todas son de la categoría `borde` (p. ej. cliente o reserva que no existen)

**AC-7 — El examen final no repite la batería**
- **Dado** los dos exámenes
- **Cuando** se revisan
- **Entonces** ninguna pregunta del final es la misma, ni una paráfrasis, de una de la batería
- **Y** los ids no se repiten entre los dos

### Errores

**AC-8 — Todas las referencias pasan el validador**
- **Dado** los dos exámenes
- **Cuando** se ejecuta `--ver` (que se para ante una referencia que no pasa el validador o un id repetido, AC-16 de
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
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- Las preguntas las redacta Claude y Mario las aprueba por bloques (como los repartos de TRAVEL-001), con el SQL de
  referencia y el resultado a la vista (`--ver`).
- Los tamaños (30–40 y 12–18) traducen las «~35 y ~15» acordadas; se pueden mover si al escribirlas sale otro reparto.
- Las preguntas son de empleado (modo empleado, acceso a todas las vistas): el modo cliente es la decisión pendiente 3
  de `PROYECTO.md` §10.
- La medida se hace con el modelo calentado de antemano o descartando el arranque en frío, como hace el comando
  (AC-12 de TRAVEL-007).

**Preguntas abiertas**
- Ninguna.
