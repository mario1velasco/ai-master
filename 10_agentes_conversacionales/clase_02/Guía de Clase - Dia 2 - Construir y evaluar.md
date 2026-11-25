# Tema 10 · Día 2 · Construir las capas que faltan y evaluarlas

Esta guía trata con una forma de trabajar que sirve para cualquier implementación asistida con IA:

- Primero los tests como especificación
- Después la implementación.
- Al final la validación con los tests.

Así se construye el flujo de cita, se convierte ese proceso en una skill y se construye con ella el flujo de devolución. Después medimos el agente con conversaciones simuladas, elegimos un fallo, lo arreglamos y volvemos a medir.

Tiene cuatro partes.

1. El flujo de cita, paso a paso: los tests, elegir hueco, confirmar y reservar, una revisión con el subagente y una prueba en la consola.
2. Una skill: el proceso que acabas de seguir con la cita, escrito para que el chat lo repita con otros flujos.
3. El flujo de devolución, construido con tu skill.
4. Evaluar: en clase, la suite de escenarios y tu primera medida; en casa, un fallo, una mejora y la medida de después.

Puedes seguirla por tu cuenta, sin la clase: todo lo que necesitas está aquí.

## Qué vamos a construir

| Capa | Dónde | Qué hace |
|---|---|---|
| Tests del flujo de cita | `tests/test_cita.py` | La especificación: seis comportamientos que el flujo tiene que cumplir. Los escribe el chat antes del código |
| Elegir hueco | `agente/flujos/cita.py`, paso 4 | El cliente elige un hueco; si no se entiende, se reintenta y, al superar los reintentos, pasa a una persona |
| Confirmar y reservar | `agente/flujos/cita.py`, paso 5 | Reserva solo con un sí claro; con un no o si el hueco se ocupa, vuelve a ofrecer huecos |
| Skill completar-flujo | `.agents/skills/completar-flujo/SKILL.md` | El proceso de la cita escrito para que el chat lo repita con otro flujo: tests primero, implementación y validación |
| Devolución | `agente/flujos/devolucion.py` | Plazo e importe decididos por el código; la política, explicada con el RAG; confirmación antes de crearla |
| Evaluación | `evaluacion/` | Diez escenarios con un cliente simulado, comprobaciones con datos y un juez con rúbrica |

## Antes de empezar

Si terminaste el día 1 con tu propio código, actualiza el kit en la carpeta `ondo-agente`, con el entorno virtual activado:

```
git pull
python -m pip install -r requirements.txt
```

`git pull` solo añade ficheros nuevos (la carpeta `evaluacion/`): no toca tu `cita.py`.

Si no terminaste el día 1, o prefieres partir de un punto conocido, descarga `ondo-agente-dia2.zip` de los materiales del tema: es el kit del día 1 con la carpeta evaluacion/ añadida. Descomprímelo, crea el entorno virtual e instala como el día 1, copia tu `.env` del día 1 a la carpeta nueva y haz un commit:

```
git init
git add -A
git commit -m "Kit del día 2"
```

En los dos casos, abre la carpeta en VS Code y comprueba:

```
python -m pytest
```

> ✓ **Compruébalo:** pasa entero, porque de momento solo hay tests del servidor MCP. Los del flujo de cita los escribes tú en el paso 2.

## Parte 1 · El flujo de cita, paso a paso

### Paso 1 - Entiende qué debe cumplir el flujo de cita (5 minutos)

En el chat, con el control Agent en Ask, escribe:

```
¿Qué pasos debe cumplir el flujo de cita?
```

Compara su respuesta con estos seis comportamientos. Leyendo solo el código, el chat puede no verlos todos: los que falten los añades tú, porque esta lista es tu especificación:

- el usuario elige un hueco
- el agente pide confirmación
- solo con un sí claro se reserva
- si no entiende, reintenta
- si falla demasiadas veces, pasa a una persona
- si la herramienta falla, no inventa éxito

### Paso 2 - Prueba el flujo actual en la consola (5 minutos)

En `python -m canales.consola --estado`, con `/reset` entre pruebas:

| Qué escribir | Qué debe pasar |
|---|---|
| `Quiero una revisión`, `lucia.martin@example.com`, `Madrid`, `1`, `Sí, resérvala` | No consigue reservar la cita por falta de implementación |
| `Quiero una revisión`, `lucia.martin@example.com`, `Madrid`, `el segundo`, `no, mejor otro día` | No consigue reservar la cita por falta de implementación |

### Paso 3 - Pide solo los tests (10 minutos)

Cambia el control a Agent y escribe:

```
Escribe los tests del flujo de cita en tests/test_cita.py, siguiendo la
sección Tests de AGENTS.md. A partir de la elección del hueco, el flujo debe
cumplir:
- el usuario elige un hueco
- el agente pide confirmación
- solo con un sí claro se reserva
- si no entiende, reintenta
- si falla demasiadas veces, pasa a una persona
- si la herramienta falla, no inventa éxito

Un test por comportamiento; para «solo con un sí claro», prueba confirma False
y también None. Ejecútalos y comprueba que fallan por lo que falta, no por un
error del test. Solo los tests: no cambies agente/flujos/cita.py ni uses la
skill completar-flujo.
```

Mientras trabaja, fíjate en el orden: lee `AGENTS.md` (la sección Tests) y `cita.py`, escribe `tests/test_cita.py` con herramientas simuladas y lo ejecuta. Antes de ejecutar un comando te pide permiso: léelo y pulsa Allow solo si es el que esperas.

> ✓ Compruébalo: python -m pytest tests/test_cita.py falla, y falla por lo que falta: el flujo todavía no deja elegir hueco ni reserva. Un ImportError o un fallo de sintaxis es un error del test, no del flujo: pídele al chat que lo corrija. Abre tests/test_cita.py y lee solo los nombres de las funciones: son la especificación del flujo. Comprueba que cubren los seis comportamientos y, si falta alguno, pídeselo. Alguno puede pasar ya, porque el flujo aún no reserva nada.

### Paso 4 - Implementa elegir hueco (10 minutos)

Antes de cambiar nada, pregúntale al chat qué hay que hacer. En modo Ask:

```
Mira tests/test_cita.py y agente/flujos/cita.py.
¿Qué hay que implementar para que se cumpla la especificación y pasen los tests?
Dime qué falta, en qué parte del flujo y qué tests dependen de cada parte. No cambies
nada.
```

Lee la respuesta. Tiene que separar dos partes: elegir hueco (con sus reintentos y el paso a una persona) y confirmar y reservar. Ahora implementas solo elegir hueco; confirmar y reservar es el paso 4. Cambia el control a Agent y pide:

```
Completa el paso 4 del flujo de cita en agente/flujos/cita.py. en el que el cliente
elige uno de los huecos que le hemos ofrecido. Trabaja únicamente en este paso, el
resto de pasos los haremos después.

Antes de cambiar nada, ejecuta los tests.
Al terminar la implementación, vuelve a ejecutarlos
Dime qué tests pasan y cuáles siguen en rojo.
```

Mientras trabaja, fíjate en el orden:

- lee `AGENTS.md`, los tests y `cita.py`
- ejecuta los tests antes de cambiar nada
- edita `cita.py`
- vuelve a ejecutar los tests.

Ese orden se lo pides tú en el prompt; este proceso seguraente siempre queramos que sea igual a la hora de implementar, es potencial candidato a guardarlo en una skill para no tener que repetirlo.

Si el agente no ha ejecutado los tests al terminar, ejecútalos tú. Mira también que no ha tocado ningún test:

```
python -m pytest tests/test_cita.py
git diff -- tests/
```

> ✓ Compruébalo: pasan los tests de elegir hueco, de los reintentos y del paso a una persona, y siguen en rojo los de reservar: son la especificación del paso 4. git diff -- tests/ no muestra nada. Si el agente ha cambiado lo que espera un test para que pase, deshazlo con git restore tests/: AGENTS.md se lo prohíbe y la especificación es tuya.

Haz un commit con el mensaje `Paso 4 del flujo de cita`.

### Paso 5 - Implementa confirmar y reservar (10 minutos)

En el mismo chat, con el control en Agent, escribe:

```
Ahora implementa el paso 5 del flujo de cita.
Ejecuta los tests antes y después de cambiar el código.
No cambies los tests.
```

El prompt no dice cómo programarlo: dice qué tiene que pasar en cada caso. Son las reglas de diseño del día 1: confirmar según el riesgo, una respuesta ambigua nunca es un sí, no dar por hecho lo que ha fallado.

> ✓ **Compruébalo:** `python -m pytest` pasa entero y `git diff -- tests/` no muestra nada.
> Haz un commit con el mensaje `Paso 5 de la cita`.

### Paso 6 - Pide una revisión al subagente (5 minutos)

```
Usa el subagente revisor_conversacion para revisar agente/flujos/cita.py.
Resume lo que encuentre.
```

El agente abre otro con su propio contexto, que aparece como una llamada plegada en el chat. El revisor solo tiene las herramientas `read` y `search`: puede leer, pero no editar ni ejecutar. Lee su informe con criterio:

- Si encuentra un incumplimiento en confirmar y reservar, pídele en modo Agent que lo arregle sin tocar los tests.

  ```
  Arregla estos cambios en código, vuelve a ejecutar los tests y vuelve a lanza
  al revisor_conversacion
  ```

### Paso 7 - Pruébalo en la consola (5 minutos)

En `python -m canales.consola --estado`, con `/reset` entre pruebas:

| Qué escribir | Qué debe pasar |
|---|---|
| `Quiero una revisión`, `lucia.martin@example.com`, `Madrid`, `1`, `Sí, resérvala` | Cita confirmada con código CIT-... |
| `Quiero una revisión`, `lucia.martin@example.com`, `Madrid`, `el segundo`, `no, mejor otro día` | Nuevos huecos, sin reservar |

## Parte 2 · Convierte el proceso en una skill

### Paso 8 - Crea tu skill completar-flujo (10 minutos)

Para la cita has repetido el mismo proceso en tres prompts:

- Primero los tests
- Después la implementación de un solo paso
- Al final la validación con los tests, siempre con las mismas instrucciones.

Una skill guarda ese proceso en un fichero para que el chat lo siga cuando la invocas con /.

En el mismo chat, con el control en Ask, escribe:

```
Quiero convertir este proceso de implementar cambios en una skill. Dime el
prompt por aquí para mandar al Agent para crear la skill
```

Ahora en el mismo chat, con el control en Agent, escribe:

```
Implementa la skill “implementar-cambios”
```

> ✓ **Compruébalo:** abre `.agents/skills/completar-flujo/SKILL.md`. La cabecera tiene `name` y una `description` que dice cuándo usarla, y los pasos son los que has seguido con la cita. Compárala con la del kit con `git diff .agents/skills/`: lo que tenga la de referencia y le falte a la tuya, decide si lo añades. Si prefieres seguir con la del kit, `git restore .agents/skills/` la recupera. Escribe `/` en el chat y comprueba que aparece `completar-flujo`. Haz un commit con el mensaje `Skill completar-flujo`.

## Parte 3 · El flujo de devolución con tu skill

### Paso 9 - Pide el flujo de devolución con tu skill (10 minutos)

Hoy `agente/flujos/devolucion.py` pasa cualquier devolución a una persona. La política de Ondo está en `data/conocimiento/devoluciones.md`. Haz un commit. En el chat, con el control en Agent, escribe / y elige tu skill `completar-flujo`; después, en el mismo mensaje:

```
/implementar-cambios Implementa el flujo de devolución.
   -  La política está en data/conocimiento/devoluciones.md.
   -  Cuando se ejecuta este flujo, el cliente ya está identificado.
   -  Primero averigua qué pedido quiere devolver: si tiene varios pedidos
      entregados, que elija con botones; si solo tiene uno, no le preguntes.
   -  Comprueba que el pedido es suyo, que está entregado y que no tiene ya
      una devolución.
   -  Comprueba que la devolución cumple las políticas de devolución
   -  Si está en camino, explícale que aún no se puede devolver.
   -  Si han pasado más de 30 días desde la entrega o el pedido supera los
      1.500 €, pásale con una persona explicándole por qué.
   -  Los días y el importe los comprueba el código, no el modelo.
   -  Si se puede devolver, pregúntale el motivo, resúmele cómo funciona la
      recogida y el reembolso según la política y pídele confirmación.
   -  Solo con un sí claro crea la devolución con crear_devolucion y dale el
      código y la fecha de recogida.
```

Mientras trabaja, fíjate en el orden:

- Anuncia que usa la skill
- Lee `AGENTS.md` y `devolucion.py`
- Resume los pasos
- Escribe los tests antes de tocar el código y los ejecuta en rojo.
- Implementa los cambios
- Ejecuta de nuevo los tests
- Lanza al sub agente revisor

> ✓ **Compruébalo:** `python -m pytest` pasa entero, con tests nuevos de devolución. Haz un commit con el mensaje `Flujo de devolución`.

Si te da tiempo, pruébalo en la consola; si no, hazlo en casa. En `python -m canales.consola --estado`, con `/reset` entre pruebas:

| Qué escribir | Qué debe pasar |
|---|---|
| `Quiero devolver mi bici`, `javier.ortega@example.com`, un motivo, `Sí` | Devolución `DEV-...` con fecha de recogida |
| `Quiero devolver mi bici`, `marta.ruiz@example.com` | Pasa a una persona: han pasado más de 30 días |

## Parte 4 · Evaluar

### Paso 10 - Mira qué se mide (3 minutos)

Abre `evaluacion/escenarios.json`. Cada escenario describe un cliente (quién es, qué quiere y cómo escribe) y lo que tiene que pasar: si se pasa a una persona y con qué prioridad, si hay cita o devolución y en qué idioma acaba la conversación.

La suite mide de tres formas distintas:

| Pieza | Fichero | Qué hace |
|---|---|---|
| Cliente simulado | `evaluacion/simulador.py` | Un modelo hace de cliente, con la persona y el objetivo del escenario |
| Comprobaciones | `evaluacion/comprobaciones.py` | Código que mira los datos: casos abiertos, citas y devoluciones creadas, idioma |
| Juez | `evaluacion/juez.py` | Otro modelo lee la conversación y aplica una rúbrica: una pregunta por mensaje, confirmar, privacidad, idioma, sin bucles |

Lo que se puede comprobar con datos lo comprueba el código; el juez solo valora lo que hay que leer.

### Paso 11 - Mide

En modo Ask, pregunta

```
¿Qué hace evaluacion.suite?
¿Qué escenarios se evalúan?
```

En modo Agente, pregunta

```
python -m evaluacion.suite
```

Tarda un minuto o dos y cuesta unos céntimos.

Al terminar enseña una tabla por escenario y las métricas:

- escenarios superados,
- paso a persona correcto
- turnos de media
- criterios del juez cumplidos.

El informe completo y las conversaciones quedan en `evaluacion/salidas/` con la fecha y la hora. La suite usa su propia carpeta de estado: tus citas de `data/estado/` no se tocan.

Apunta los cuatro números. Son tu «antes».

> ℹ **Nota:** los números cambian un poco de una ejecución a otra, porque el cliente simulado no escribe siempre igual. En nuestras pruebas, el kit con elegir hueco hecho y sin nada más dio 5 de 10 escenarios superados, y con el paso 5 y la devolución, 9 de 10.

### Paso 12 - Elige un fallo y entiéndelo

Este paso y el siguiente son para después de clase; en clase los verás hechos con pedido_ajeno. Elige un escenario que falle, en las comprobaciones o en el juez. En el chat, en modo Ask:

```
Lee el informe más reciente de evaluacion/salidas/ y la conversación del
escenario pedido_ajeno en conversaciones.json. Sin cambiar nada: explícame por
qué falla y en qué fichero y línea está la causa.
```

Cambia `pedido_ajeno` por el escenario que hayas elegido. Fallos que encontramos al preparar la clase:

- `pedido_ajeno`: el agente protege los datos del otro cliente, pero repite la misma petición una y otra vez: el email para comprobar que el pedido es suyo, o «¿Podrías comprobar si el número es correcto?». El juez lo marca como bucle.
- `cita_en_ingles`: el cliente escribe «Madrid» y el agente pasa al español.
- `pedido_en_camino`: si el cliente insiste en pedir un enlace de seguimiento, el agente repite el mismo párrafo de la política.

Comprueba lo que dice el chat abriendo el fichero que nombra.

### Paso 13 - Mejóralo y vuelve a medir

Haz un commit. En modo **Agent**, pide el arreglo describiendo el comportamiento que quieres. Para `pedido_ajeno`, por ejemplo:

```
La evaluación marca que el agente entra en bucle en el escenario pedido_ajeno:
cuando el cliente pregunta por un pedido que no es suyo.
Encuentra dónde se genera esa respuesta y cámbialo para que, si el cliente
insiste, el agente explique una sola vez que solo el titular puede consultar
ese pedido y le ofrezca ayuda con sus propios pedidos o hablar con una
persona. No reveles nunca datos del pedido ajeno. Añade un test que lo
compruebe sin llamar al modelo y no cambies escenarios.json.
```

Si en tu conversación el agente repite otra frase, cambia la que va entre comillas por la tuya. Mide primero solo ese escenario y después todos:

```
python -m evaluacion.suite --solo pedido_ajeno
python -m evaluacion.suite
```

Antes de mirar los números, lee la conversación nueva. Cuando preparamos la clase, con este prompt pasó esto:

- El bucle del final desapareció: el agente explicó una vez que solo el titular puede consultar el pedido y ofreció dos botones, «Dónde está mi pedido» y «Hablar con una persona».
- El cliente simulado, educado e insistente, pulsó «Hablar con una persona». El agente abrió un caso y la comprobación `escalado` pasó a fallar, porque el escenario esperaba que no se escalara.
- Apareció un bucle nuevo antes: el agente pidió el email de la vecina «para comprobar el pedido» y repitió dos veces «No encuentro ninguna compra con ese email».

El primer punto es la mejora que pediste. El segundo obliga a decidir quién se equivoca: el agente cumple la regla de pasar a una persona cuando el cliente lo pide, así que lo que ha quedado viejo es lo esperado en el escenario. Esa decisión es tuya, no del agente: si la compartes, cambia tú `"escalado"` a `true` en `pedido_ajeno` y explícalo en el commit. El tercero es un fallo nuevo del agente que la medida ha destapado, y es el siguiente arreglo.

> ✓ **Compruébalo:** el bucle que elegiste ya no aparece en la conversación, `python -m pytest` sigue en verde y el resto de escenarios no ha empeorado. Si algo empeora, `git restore .` y repite con un prompt más preciso. Haz un commit con el antes y el después en el mensaje, con tus números en lugar de los del ejemplo: `pedido_ajeno sin bucle al insistir: juez 6/8 → 7/8`.

### Paso 14 - Propón nuevos escenarios

En modo **Ask**,

```
En un escenario en el que la conversación no tenga nada que ver con Ondo, que
el usuario pida recomendaciones de viaje. ¿Cuál sería el resultado esperado?

En otro escenario en el que el usuario quiera realizar un pedido, ¿cuál sería
el resultado esperado?
```

En modo **Ask**,

```
En el caso de que un chat no tenga nada que ver con Ondo, no queremos
escalarlo, queremos que el agente responda limitandose a decir lo que puede
hacer

Si tiene que ver con Ondo pero el agente no tiene capacidad para resolverlo,
fuera e alcance y para persona

Elabora el plan para implementar estos cambios, usando la skill implementar-
cambios
```

En modo **Agent**,

```
Implementa ambos.
```

## Cómo saber que está terminado

- `python -m pytest` pasa entero, con los tests del flujo de cita que pediste en el paso 2, los de la devolución que escribió el agente y el de tu mejora.
- En la consola, la cita llega a un código `CIT-...` y la devolución de Javier a un `DEV-...`; la de Marta pasa a una persona.
- El revisor no ha dejado cambios.
- Tu skill `completar-flujo` está en `.agents/skills/completar-flujo/` y el chat la anunció al construir la devolución.
- Tienes dos informes de evaluación, antes y después de tu mejora, y has leído la conversación nueva: sabes qué arregló tu cambio y qué destapó.

## Si quieres ir más allá

- Ejecuta la suite dos veces seguidas sin cambiar nada y compara. ¿Cuánto varía? Es la razón de no fiarse de una sola medida.
- Lee la rúbrica de `evaluacion/juez.py` y busca un caso en el que el juez se equivoque. Un juez también se evalúa.
- Pídele al chat en modo Ask que te explique la diferencia entre lo que comprueba `comprobaciones.py` y lo que valora el juez, y por qué no se deja todo al juez.

## Errores frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `git pull` da un conflicto | Has cambiado un fichero que también viene en la actualización | `git stash`, `git pull` y `git stash pop`; o descarga el ZIP del día 2 |
| `ModuleNotFoundError: No module named 'evaluacion'` | Ejecutas la suite desde fuera de la carpeta del kit | Ejecútala en `ondo-agente`, con el entorno activado |
| La suite tarda mucho o da errores de límite de peticiones | Tu clave admite pocas peticiones por minuto | `python -m evaluacion.suite --paralelo 1` |
| La reserva aparece en la consola pero la suite dice que no hay cita | El escenario terminó antes de confirmar | Lee la conversación en `conversaciones.json`: si el cliente simulado no confirmó, el fallo es del escenario, no del agente |
| El agente cambia lo que espera un escenario para que pase | El modelo tomó el atajo | `git restore .` y repite el prompt diciendo «no cambies escenarios.json» |
| Los tests pasan pero el escenario sigue fallando | El test simula algo que no pasa en la conversación real | Lee la conversación completa y pide un test con lo que de verdad dijo el cliente |
| El agente no llama al subagente `revisor_conversacion` | Falta la herramienta de subagentes o VS Code no ha cargado el fichero | En **Configure Tools**, marca **Run Subagent**; después, **Developer: Reload Window** |
| <!-- original: segundo_lector.txt -->La skill `completar-flujo` no aparece al escribir `/`<!-- /original --> | VS Code no ha cargado la skill o el fichero no está en `.agents/skills/completar-flujo/SKILL.md` | Comprueba la ruta y el `name` de la cabecera; después, **Developer: Reload Window** |
