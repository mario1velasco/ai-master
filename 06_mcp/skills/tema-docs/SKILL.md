---
name: tema-docs
description: Genera README.md, AGENTS.md y explicacion.md para una carpeta de tema de este máster/curso, a partir de todo su material (PDFs, enunciados, código). Úsala cuando el usuario pida documentar, explicar en detalle o generar esos documentos para una carpeta de tema nueva (p. ej. "documenta el tema 2", "haz lo mismo que en el tema 1 para 03-...", "genera el explicacion.md de esta carpeta", "créame el README y el AGENTS de este tema").
---

# Generar la documentación de un tema (README + AGENTS + explicación)

Esta skill reproduce el proceso que se usó para documentar `01-agents-harness/`: estudiar todo el material de una carpeta de tema y producir tres documentos con roles distintos. No te saltes pasos ni cambies el orden: cada documento depende de haber hecho bien el paso anterior.

## Paso 0 — Identificar la carpeta a documentar

- `args` puede traer ya la ruta (p. ej. `02-mcp-basico`). Si no, o si es ambigua, lista las carpetas numeradas en la raíz del repo (`ls` / `find . -maxdepth 1 -type d`) y usa `AskUserQuestion` para que el usuario elija — no asumas cuál es "la siguiente" sin confirmar.
- Comprueba si esa carpeta ya tiene `README.md`, `AGENTS.md` o `explicacion.md`. Si ya existen, esto es una actualización: sigue además la sección "Mantenimiento de la documentación" del `AGENTS.md` raíz (ediciones puntuales, no reescrituras completas, salvo que el cambio sea grande).

## Paso 1 — Inventariar y leer TODO el material antes de escribir nada

1. `find <carpeta> -type f` para ver qué hay: PDFs, código, enunciados, ejemplos.
2. Lee cada PDF por completo:
   - Si tiene más de 20 páginas, usa `Read` con el parámetro `pages` en bloques de ≤20 páginas hasta cubrirlo entero. No te quedes con las primeras páginas.
3. Lee cada fichero de código relevante **completo**, no solo extractos. Si hay varias versiones/copias del mismo proyecto (por ejemplo, una serie de demos progresivas tipo v1→v8, o una versión de referencia y un ejercicio con TODOs), léelas todas y compáralas para entender qué cambia entre ellas — esa comparación suele ser el mejor material didáctico.
4. Distingue explícitamente, si aplica:
   - **Código de referencia** (funcional, no se toca).
   - **Código de ejercicio** (con TODOs/bugs deliberados, es lo único que un alumno debe modificar).
5. Regla de oro: **cualquier afirmación técnica que escribas en los tres documentos debe poder rastrearse a un PDF concreto o a una línea de código que hayas leído en este paso.** Si no puedes rastrearla, no la escribas.

## Paso 2 — Generar los tres documentos, en este orden, dentro de la carpeta del tema

### a) `README.md` — para humanos
Explica de qué trata el tema para quien lo vaya a leer (el alumno). Estructura orientativa (adapta según el material real, no la fuerces si no encaja):
- Una línea de contexto: qué módulo/tema es y cómo enlaza con el curso.
- Resumen de la teoría (qué conceptos cubre cada PDF), con tablas/listas si el material las usa.
- Qué proyectos de código hay y para qué sirve cada uno (referencia vs. ejercicio).
- Si hay ejercicio: qué hay que hacer, sin resolverlo, y cómo ejecutarlo.
- Orden de estudio recomendado.

### b) `AGENTS.md` — para agentes (guía operativa)
Más corto y directo que el README, pensado para que un agente que trabaje en esa carpeta no se pierda. Debe incluir siempre:
- Qué es la carpeta, en 2-3 líneas, y cómo ejecutar el código (`uv sync`, `.env`, `uv run ...`).
- Tabla o lista que distinga claramente código de referencia (intocable) vs. código de ejercicio (a resolver), si existe esa distinción.
- Dónde están exactamente los TODOs/bugs a resolver del ejercicio (fichero, función, qué se espera), sin dar la solución.
- Una sección **"Mantenimiento de la documentación"** (copia el criterio ya usado en `01-agents-harness/AGENTS.md` y en el `AGENTS.md` raíz): tras cada cambio de código, comprobar si README/AGENTS/explicacion quedan desactualizados y actualizarlos; ediciones puntuales para cambios puntuales; replantear la sección solo si el cambio es grande.

### c) `explicacion.md` — explicación extensa y muy didáctica
El documento más largo y detallado, para quien quiera entenderlo todo sin dar nada por sabido:
- Lenguaje muy claro, explicando cada concepto desde cero, con analogías propias si ayudan (pero solo como aclaración, nunca presentadas como un hecho del material).
- Usa fragmentos de código **reales** (copiados del código leído en el paso 1) como ejemplos, no pseudocódigo inventado, salvo que sea para no desvelar la solución de un ejercicio (ver más abajo).
- No te saltes nada del material: si el PDF tiene 5 bloques temáticos, el documento debe cubrir los 5.
- Cierra con un **glosario** de los términos técnicos introducidos y una sección final de **fuentes** que liste de qué PDFs/ficheros de código sale cada cosa, y que declare explícitamente qué partes (si las hay) son ejemplos ilustrativos propios y no del material original.

## Paso 3 — No dar la solución de ejercicios con TODOs

Si la carpeta tiene un ejercicio con TODOs o bugs deliberados: explica en profundidad los conceptos y el patrón a aplicar, apóyate en el código de referencia existente (si lo hay) como ejemplo ya resuelto de ese mismo patrón, y si hace falta un ejemplo más, usa uno **estructuralmente análogo pero distinto** al que pide el ejercicio (nombres de función distintos, caso de uso distinto), dejando claro que es un ejemplo propio para practicar el patrón, no la respuesta. Esto aplica sobre todo en `explicacion.md`, que es donde más se detalla el "cómo".

## Paso 4 — Autorrevisión antes de terminar

Antes de dar el trabajo por acabado, relee `explicacion.md` completo (y de pasada README/AGENTS) contrastando cada afirmación, tabla y bloque de código contra el material que leíste en el paso 1. Corrige cualquier imprecisión, cita mal recordada o cruce de referencias interno (números de sección, nombres de ficheros) antes de continuar. Dilo explícitamente al usuario: que hiciste esta pasada de revisión y qué encontraste (aunque sea "nada que corregir").

## Paso 5 — Actualizar el índice de temas del repo

Si el `AGENTS.md` de la raíz del repo mantiene una lista de temas (busca una sección tipo "Cada carpeta numerada..."), añade una línea para el tema nuevo siguiendo el mismo formato que las existentes. Es una edición puntual de una línea, no una reescritura — sigue la regla de "Mantenimiento de la documentación" del propio archivo.

## No hacer

- No inventar contenido que no esté en el material ni en el código leído.
- No resolver el ejercicio del alumno escribiendo el código final de sus TODOs.
- No tocar el código de los proyectos — esta skill solo genera/actualiza documentación.
- No reescribir documentos existentes de arriba a abajo para un cambio pequeño; sigue siempre la regla de "Mantenimiento de la documentación".
- No omitir la pasada de autorrevisión del paso 4.
