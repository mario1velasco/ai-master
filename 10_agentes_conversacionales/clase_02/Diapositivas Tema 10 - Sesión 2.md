<!-- diapositiva 1 -->

# Tema 10 · Día 2

**Agentes conversacionales: automatización de chats y llamadas telefónicas**

---

<!-- diapositiva 2 -->

## Lo que haremos hoy

1. **Agente conversacional en código**  
   Ejercicios complementarios y repaso
2. **Piezas que guían el código**
3. **Práctica - Completar agente en código**  
   Procesos para completar un flujos
4. **Flujo de devolución a partir de un proceso**
5. **Evaluar el agente**  
   Medir, mejorar y volver a medir
6. **Agentes No-Code vs código**

---

<!-- diapositiva 3 -->

## El caso de uso conductor del tema

Electric bikes, sold online

A fictional company, with fictional customers

<!-- imagen: logo de Ondo y esquema canales → FastAPI → Agente LangGraph → Servidor MCP de Ondo, con la evaluación debajo -->

---

<!-- diapositiva 4 -->

## El grafo de Ondo

NODOS Y RUTAS DE UN TURNO

<!-- imagen: grafo interpretar → identificar/reparar/informar/saludar/escalar → redactar → FIN -->

---

<!-- diapositiva 5 -->

## Repaso de los complementarios

1. **Sé el grafo**

   El orden de ruta decide: primero la seguridad, después el caso abierto y luego los flujos.

2. **Diagnostica la conversación**

   Fallos reales: «¿Eres una persona?» abre un caso y el RAG no encuentra el plazo de devolución.

---

<!-- diapositiva 6 -->

# Agente conversacional en código

---

<!-- diapositiva 7 -->

## agente.py conecta los canales con el grafo

AGENTE/AGENTE.PY · LA PUERTA DE ENTRADA

<!-- imagen: los canales entregan mensajes con su hilo a «AgenteOndo», que habla con el servidor MCP y devuelve texto, botones y estado -->

---

<!-- diapositiva 8 -->

## estado.py guarda lo que el agente sabe en cada turno

AGENTE/ESTADO.PY · LA MEMORIA EXPLÍCITA

<!-- imagen: ficha de cliente con sus campos y un archivador de hilos -->

---

<!-- diapositiva 9 -->

## grafo.py decide qué hacer en cada turno

AGENTE/GRAFO.PY · LA DECISIÓN DE CADA TURNO

<!-- imagen: vías de tren de interpretar a redactar, con las rutas numeradas del 1 al 7 -->

---

<!-- diapositiva 10 -->

## herramientas.py conecta el agente con el servidor MCP

AGENTE/HERRAMIENTAS.PY · UNA SESIÓN, SIETE HERRAMIENTAS

<!-- imagen: un portátil conectado por stdio, con una sola sesión, a las siete herramientas del servidor MCP de Ondo -->

---

<!-- diapositiva 11 -->

## En llm.py el modelo solo entiende y redacta

AGENTE/LLM.PY · TRES LLAMADAS AL MODELO

<!-- imagen: interpretar, redactar y resumir; entre medias, el código decide -->

---

<!-- diapositiva 12 -->

# Repaso: las piezas que guían al chat

---

<!-- diapositiva 13 -->

## Dos agentes diferentes

REPASO: LAS PIEZAS QUE GUÍAN AL CHAT

Uno atiende a los clientes de Ondo; el otro, el chat de VS Code, os ayuda a programarlo.

1. **El agente de Ondo**

   El grafo de agente/, sus prompts en llm.py y las herramientas del servidor MCP.

2. **El agente del chat**

   Lee AGENTS.md, carga skills y delega en subagentes. Edita el código si se lo pedís.

> **Cada uno con sus instrucciones**
>
> Cambiar AGENTS.md no cambia cómo habla el agente de Ondo, y al revés.

---

<!-- diapositiva 14 -->

## Las seis piezas: qué es cada una

DEFINICIÓN DE CADA PIEZA

| Pieza | Definición |
|---|---|
| **Prompt** | |
| **Prompt files** | |
| **Instrucción de carpeta** *CLAUDE.md, AGENTS.md* | |
| **Skill** | |
| **Agente** | |
| **Servidor MCP** | |

---

<!-- diapositiva 15 -->

## Las seis piezas: qué es cada una

DEFINICIÓN DE CADA PIEZA

| Pieza | Definición |
|---|---|
| **Prompt** | Instrucción directa que escribes a la IA en el momento para obtener un resultado inmediato. Vive solo en esa conversación y hay que repetirla cada vez. |
| **Prompt files** | Plantilla de prompt guardada en un fichero que lanzas tú a mano, con /, cada vez que la necesitas. No se carga sola. |
| **Instrucción de carpeta** *CLAUDE.md, AGENTS.md* | Fichero de contexto y reglas base en la raíz del proyecto o de una carpeta (AGENTS.md, CLAUDE.md). La IA arranca con esa memoria sin que se lo expliques. |
| **Skill** | Carpeta modular con instrucciones, reglas, documentación o scripts que la IA carga bajo demanda, solo cuando la tarea lo requiere, como un especialista temporal. |
| **Agente** | IA que persigue un objetivo complejo en varios pasos: planifica, actúa, comprueba e itera por su cuenta, y puede usar skills, instrucciones y herramientas externas. |
| **Servidor MCP** | Puente estandarizado (Model Context Protocol) que conecta la IA con el exterior para leer datos reales y ejecutar acciones en herramientas, bases de datos o aplicaciones. |

---

<!-- diapositiva 16 -->

## Siete piezas para dar contexto y límites

CUÁNDO ENTRAN EN EL CONTEXTO Y QUIÉN LAS LANZA

| Pieza | Cuándo entra | Quién la lanza | Úsala para |
|---|---|---|---|
| **AGENTS.md** | Siempre, al empezar | Nadie: se carga sola | Comandos y reglas que valen para cualquier tarea |
| **Instrucciones por carpeta** | Al tocar esos ficheros | Nadie | Reglas de un tipo de fichero (tests, migraciones) |
| **Prompt file** | Al escribir / | Tú | Una petición que repites siempre igual |
| **Skill** | Cuando la tarea encaja, o con / | El agente o tú | Un proceso con pasos, scripts y comprobación |
| **Subagente** | Cuando se le delega | El agente principal o tú | Trabajo con contexto limpio, permisos acotados u otro modelo |
| **Servidor MCP** | Sus herramientas, siempre | El agente | Acceso a datos o acciones de otro sistema |
| **Lint, tests, CI** | Al ejecutarse | Nadie: pasa o falla | Lo que debe cumplirse siempre |

---

<!-- diapositiva 17 -->

## Repaso

**ESTRUCTURA DEL PROYECTO**

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/
│   ├── completar-flujo/SKILL.md
│   └── afinar-prompt/SKILL.md
├── .github/agents/
│   ├── qa.agent.md
│   └── revisor_conversacion.agent.md
├── agente/flujos/
│   ├── cita.py
│   └── devolucion.py
├── ondo_mcp/server.py
├── tests/
│   ├── AGENTS.md
│   └── test_devolucion.py
└── evaluacion/
    ├── AGENTS.md
    └── escenarios.json
```

**REGLAS**

1. Esta es la estructura de un proyecto y una petición al asistente.
2. Simulamos una petición al asistente.
3. Qué piezas participan en la respuesta,, qué está siempre en memoria y qué se carga al vuelo

**CARGA EN MEMORIA**

- **SIEMPRE** en el contexto desde el primer mensaje
- **AL VUELO** entra cuando la tarea lo pide
- **SOLO DESCRIPCIÓN** se sabe que existe, no se lee el cuerpo
- **NO ENTRA** ni se lee en esta tarea

---

<!-- diapositiva 18 -->

## Caso · Completar y probar

**ESTRUCTURA DEL PROYECTO**

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/
│   ├── completar-flujo/SKILL.md
│   └── afinar-prompt/SKILL.md
├── .github/agents/
│   ├── qa.agent.md
│   └── revisor_conversacion.agent.md
├── agente/flujos/
│   ├── cita.py
│   └── devolucion.py
├── ondo_mcp/server.py
├── tests/
│   ├── AGENTS.md
│   └── test_devolucion.py
└── evaluacion/
    ├── AGENTS.md
    └── escenarios.json
```

**PETICIÓN AL ASISTENTE**

> *«Añade al flujo de devolución el caso del pedido en camino y pide al agente qa que lo pruebe.»*

**ADIVINAD**

1. ¿Qué piezas intervienen?
2. ¿Qué está siempre en memoria?
3. ¿Qué se carga al vuelo, y cuándo?
4. ¿En qué orden trabaja el asistente?

Pista: quien prueba tiene que poder ejecutar los tests, pero no le toca arreglar el código.

---

<!-- diapositiva 19 -->

## Caso · Completar y probar: solución

LO QUE ENTRA, LO QUE NO Y EL ORDEN DEL ASISTENTE

**ESTRUCTURA DEL PROYECTO**

```
ondo-agente/
├── AGENTS.md                              SIEMPRE
├── .agents/skills/
│   ├── completar-flujo/SKILL.md           AL VUELO
│   └── afinar-prompt/SKILL.md             SOLO DESCRIPCIÓN
├── .github/agents/
│   ├── qa.agent.md                        AL VUELO
│   └── revisor_conversacion.agent.md      SOLO DESCRIPCIÓN
├── agente/flujos/
│   ├── cita.py
│   └── devolucion.py                      SE EDITA
├── ondo_mcp/server.py
├── tests/
│   ├── AGENTS.md                          AL VUELO
│   └── test_devolucion.py                 SE EDITA
└── evaluacion/
    ├── AGENTS.md                          NO ENTRA
    └── escenarios.json
```

**FLUJO DEL ASISTENTE**

1. **Llega tu mensaje.** Con AGENTS.md y las descripciones de skills y agentes, como siempre.
2. **Skill.** «Añade al flujo de devolución» encaja con completar-flujo: entra su SKILL.md, tests primero.
3. **Test.** Escribe el test del pedido en camino en tests/test_devolucion.py, con las reglas de tests/AGENTS.md.
4. **Código.** Cambia devolucion.py hasta que el test pasa, sin tocar el test.
5. **Subagente.** Llama a qa con lo que ha cambiado y qué probar. Ejecuta python -m pytest, pero sin edit no toca nada.
6. **Respuesta corta.** qa devuelve qué pasa y qué falla. El asistente lo resume y corrige lo que haga falta.

> qa prueba con su propio contexto: puede ejecutar los tests, pero no editar.  
> Si algo falla, lo corrige el asistente principal con la skill.

---

<!-- diapositiva 20 -->

## El kit trae tres piezas para el chat

REPASO DEL TEMA DE IA AGÉNTICA

Vuestro prompt vale para una conversación. Estas tres se quedan en el proyecto.

1. **AGENTS.md**

   Reglas del proyecto, en cada petición. Lleva las reglas de la conversación del bloque 2.

2. **Skill completar-flujo**

   Un proceso que se repite: tests primero, después el código y la validación. Entra cuando la tarea encaja o con /.

3. **Subagente revisor_conversacion**

   Revisa el flujo con su propio contexto. Solo tiene read y search: no puede editar ni ejecutar.

---

<!-- diapositiva 21 -->

## AGENTS.md entra en cada petición

REPASO: LAS PIEZAS QUE GUÍAN AL CHAT

Lo que no se deduce del código: cómo se trabaja en este proyecto.

1. **Comandos**

   Instalar, ejecutar los tests y arrancar la consola con el Python de .venv.

2. **Terminado significa**

   Los tests de lo pedido pasan, un resumen corto y nada tocado fuera de lo pedido.

3. **Reglas de la conversación**

   Confirmar antes de reservar, reintentos, paso a persona y no inventar datos.

---

<!-- diapositiva 22 -->

## Una skill entra cuando la tarea encaja

REPASO: LAS PIEZAS QUE GUÍAN AL CHAT

Al principio el chat solo lee su nombre y su descripción; el resto, cuando la necesita.

1. **Nombre y descripción**

   Siempre en contexto. Con una descripción vaga, el chat no sabe cuándo usarla.

2. **Los pasos**

   completar-flujo: tests primero, después el código y al final la validación.

3. **Dónde vive**

   .agents/skills/completar-flujo/SKILL.md, en el repositorio: igual para todos.

---

<!-- diapositiva 23 -->

## Un subagente trabaja con su propio contexto

REPASO: LAS PIEZAS QUE GUÍAN AL CHAT

El chat le delega una tarea y recibe un informe, sin compartir vuestra conversación.

1. **Contexto propio**

   Empieza limpio: solo sabe lo que le pasa el chat y lo que lee del proyecto.

2. **Herramientas limitadas**

   revisor_conversacion tiene read y search: puede leer, pero no editar ni ejecutar.

3. **Cuándo se usa**

   Para una segunda opinión: revisar un flujo contra las reglas de AGENTS.md.

---

<!-- diapositiva 24 -->

## MCP separa al agente de las herramientas

REPASO: LAS PIEZAS QUE GUÍAN AL CHAT

Un servidor ofrece herramientas y el agente las llama para realizar las acciones correspondientes.

1. **El servidor ondo_mcp**

   Siete herramientas: clientes, pedidos, devoluciones, huecos, citas, escalar y RAG.

2. **La conexión**

   AgenteOndo abre una sesión por stdio al arrancar y herramientas.py la mantiene abierta.

3. **Lo que gana el diseño**

   Los datos y las acciones viven fuera del grafo: cambian sin tocar el agente.

---

<!-- diapositiva 25 -->

## Las piezas, en código

**1 · Abrid los tres ficheros y leedlos por encima.**

```
AGENTS.md · .agents/skills/completar-flujo/SKILL.md
.github/agents/revisor_conversacion.agent.md
```

**2 · Comprobad con el chat, en modo Ask, que lo habéis entendido.**

```
Sin cambiar nada: explícame qué hacen en este proyecto AGENTS.md, la skill
completar-flujo y el subagente revisor_conversacion. Para cada uno, dime cuándo
lo usa el chat y pon un ejemplo con el flujo de cita.
```

---

<!-- diapositiva 26 -->

# Cómo trabajar con código

**Tests primero**

---

<!-- diapositiva 27 -->

## Buenas prácticas con un asistente de IA

BUENAS PRÁCTICAS CON UN ASISTENTE DE CÓDIGO

1. **Especificación**

   Qué tiene que pasar y cómo se comprueba: comportamientos, casos límite y tests.

   **Fase crítica: la hacemos nosotros.**

2. **Implementación**

   El asistente escribe el código siguiendo la especificación y AGENTS.md.

   **Fase de la IA, con el alcance que le fijamos.**

3. **Validación**

   Los tests pasan, la especificación no ha cambiado y leéis el diff antes del commit.

   **Fase crítica: la hacemos vosotros.**

> **VALE PARA CUALQUIER TRABAJO CON IA**
>
> Las personas definen qué es correcto y lo comprueban; la IA trabaja en medio.

---

<!-- diapositiva 28 -->

## Buenas prácticas con un asistente de código

LOS TESTS SON LA ESPECIFICACIÓN

1. **«Qué tiene que pasar»**

   Cada test es un comportamiento: elegir hueco, pedir confirmación, no reservar sin un sí.

2. **«Los escribe el chat; los decidís vosotros»**

   Vosotros dais la lista de comportamientos y leéis los nombres de las funciones.

3. **«Antes que el código»**

   Escritos después, tienden a copiar lo que el código ya hace, aunque esté mal.

---

<!-- diapositiva 29 -->

## Tres tiempos para cualquier cambio

1. **Tests**

   Primero y en rojo: tienen que fallar por lo que falta, no por un error del test.

2. **Implementación**

   Antes, una pregunta en modo Ask: qué falta. Después, solo lo pedido, en modo Agent.

3. **Validación**

   Los tests pasan y git diff -- tests/ sale vacío: nadie ha cambiado la especificación.

> **SKILL**
>
> Este es un proceso que siempre debería ser igual.
>
> Proceso -> potencial Skill

---

<!-- diapositiva 30 -->

## Un test en rojo puede fallar por dos motivos

ANTES DE IMPLEMENTAR, MIRAD POR QUÉ FALLA

1. **Por lo que falta**

   AssertionError: el flujo todavía no pide confirmación. Es lo esperado antes de implementar.

2. **Por el propio test**

   ImportError, un nombre mal escrito o un estado mal construido. Se arregla el test antes de seguir.

---

<!-- diapositiva 31 -->

## Validar es comprobar dos cosas

AL TERMINAR CADA CAMBIO

**1 · Que los tests pasan.**

```
python -m pytest tests/test_cita.py
```

**2 · Que nadie ha tocado el código para que el test pase.**

```
git diff -- tests/
# no debe mostrar nada
```

> **SI EL AGENTE CAMBIÓ UN TEST**
>
> Deshacedlo con git restore tests/: AGENTS.md se lo prohíbe y la especificación es vuestra.

---

<!-- diapositiva 32 -->

## Las capas que construimos hoy

Dos acciones con efecto, la skill que las une y una forma de medirlas.

| LA CITA, A MANO | | DEVOLUCIÓN, CON VUESTRA SKILL | | EVALUACIÓN |
|---|---|---|---|---|
| agente/flujos/cita.py | → | agente/flujos/devolucion.py | → | evaluacion/ |
| Pasos 4 y 5, con vuestros tests | | Vuestra skill escribe los tests primero | | Diez clientes simulados |

---

<!-- diapositiva 33 -->

## El flujo de cita pide un dato en cada paso

AGENTE/FLUJOS/CITA.PY · LOS PASOS 4 Y 5 SON DE HOY

| Motivo | | Ciudad | | Huecos | | Elegir hueco | | Confirmar y reservar |
|---|---|---|---|---|---|---|---|---|
| PASO 1 · HECHO | → | PASO 2 · HECHO | → | PASO 3 · HECHO | → | PASO 4 · HOY | → | PASO 5 · HOY |

> **EL ESTADO RECUERDA EN QUÉ PASO ESTÁ**
>
> pendiente dice qué respuesta espera («hueco», «confirmar_cita»), datos guarda lo ya decidido e intentos_fallidos cuenta los mensajes que no se entienden: al superar MAX_REINTENTOS = 2, pasa a una persona.

**El modelo interpreta; el código sabe en qué paso está.**

---

<!-- diapositiva 34 -->

# Práctica: completar el flujo de cita

---

<!-- diapositiva 35 -->

## Los comportamientos son nuestra especificación

1. **Camino ideal**

   1 · El cliente elige un hueco.  
   2 · El agente pide confirmación.  
   3 · Solo con un sí claro se reserva.

2. **Reparación**

   4 · Si no entiende, reintenta.  
   5 · Si falla demasiadas veces, pasa a una persona.

3. **Si algo falla**

   6 · Si la herramienta falla, no inventa éxito: lo dice y ofrece otros huecos.

> El “sí” lo interpreta el modelo.  
> La acción de “reservar” la decide el código.  
> La realización de la acción en sí, a través del MCP.

---

<!-- diapositiva 36 -->

## Un prompt de implementación tiene cuatro partes

| | |
|---|---|
| **Alcance**<br>«Solo la consulta de cita.<br>La reserva la haremos después.» | **Comportamiento**<br>«Si no se entiende, súmale un intento y, si supera los reintentos, pásale con una persona.» |
| **Validación**<br>«Antes de cambiar nada, ejecuta tests/test_cita.py; al terminar, vuelve a ejecutarlo.» | **Límites**<br>«No cambies los tests ni uses la skill completar-flujo.» |

Cada parte quita una decisión que el agente tomaría por su cuenta.

---

<!-- diapositiva 37 -->

## Consultar no cambia nada; actuar, sí

**LEER: SIN PREGUNTAR**

- buscar_cliente y estado_pedido
- huecos_taller
- buscar_conocimiento (la política, por RAG)

**ESCRIBIR: RESUMEN Y UN SÍ CLARO**

- reservar_cita
- crear_devolucion
- escalar_a_humano: no se confirma, se explica el motivo

---

<!-- diapositiva 38 -->

## La confirmación de la cita tiene tres respuestas

LO QUE TIENE QUE HACER LA CONFIRMACIÓN DE LA CITA

Después de elegir hueco, el agente resume la cita y pregunta si la reserva.

1. **Un sí claro**

   Reserva con reservar_cita, cierra el flujo y da el código CIT-…

2. **Un no**

   No reserva y vuelve a enseñar huecos libres.

3. **Algo ambiguo**

   «Vale, bueno, no sé» cuenta como duda: vuelve a preguntar, sin reservar.

---

<!-- diapositiva 39 -->

## El hueco que se ocupa mientras el cliente decide

LA ACCIÓN PUEDE FALLAR

> **reservar_cita devuelve un error si otra persona ha cogido el hueco entre la oferta y el sí.**

| Lo que no se hace | Lo que se hace |
|---|---|
| Dar la cita por hecha porque el cliente dijo que sí. | Decirle que ese hueco se acaba de ocupar y enseñarle otros, en el mismo mensaje. |

---

<!-- diapositiva 40 -->

## El subagente revisa con su propio contexto

REPASO DEL LUNES · .GITHUB/AGENTS/REVISOR_CONVERSACION.AGENT.MD

1. **Empieza de cero**

   No ve vuestra conversación: lee el código sin arrastrar lo que el chat principal dio por bueno.

2. **Solo puede leer**

   Tiene las herramientas read y search. No edita ni ejecuta nada.

3. **Devuelve un informe**

   El chat principal os lo resume. Qué se arregla lo decidís vosotros.

> **LA FRONTERA LA PONEN SUS HERRAMIENTAS**
>
> Lo visteis en el T9: los permisos limitan lo que puede hacer; las instrucciones solo lo orientan.

---

<!-- diapositiva 41 -->

## Antes de empezar

EL KIT DEL DÍA 2

**1 · Con git, en la carpeta ondo-agente y el entorno activado. Sin git, el ZIP del día 2.**

```
git pull
```

**2 · Comprobad el punto de partida.**

```
python -m pytest
# pasa entero: solo hay tests del servidor MCP
```

> **SI USASTEIS EL ZIP**
>
> El ZIP del día 2 es el kit del día 1 con la carpeta evaluacion/. Copiad vuestro .env y haced un commit antes del primer prompt.

---

<!-- diapositiva 42 -->

## Paso 1 · Entiende qué debe cumplir el flujo

MODO ASK, SIN CAMBIAR NADA · 5 MINUTOS

**1 · En el chat, con el control en Ask:**

```
¿Qué pasos debe cumplir el flujo de cita?
```

**2 · Leed su respuesta y apuntad qué comportamientos nombra.**

```
Pasos 1 a 3 (motivo, ciudad y huecos): ya están hechos.
Pasos 4 y 5 (elegir hueco, confirmar y reservar): por hacer.
¿Dice qué pasa si no se entiende al cliente? ¿Y si la reserva falla?
```

> **LEYENDO SOLO EL CÓDIGO**
>
> El chat puede no verlos todos. Lo que falte lo añadís vosotros: la especificación es vuestra, y está en la diapositiva siguiente.

---

<!-- diapositiva 43 -->

## Paso 2 · Pide solo los tests

MODO AGENT, SIN LA SKILL DEL KIT · 10 MINUTOS

**1 · En el chat, modo Agent, con el prompt del paso 2 de la guía.**

```
Escribe los tests del flujo de cita en tests/test_cita.py, siguiendo AGENTS.md. …
```

**2 · Un test por comportamiento, y que los ejecute.**

```
1 elige un hueco             4 si no entiende, reintenta
2 pide confirmación          5 tras varios fallos, una persona
3 reserva solo con un sí     6 no inventa si falla la herramienta
```

> **SOLO LOS TESTS**
>
> Pedid que los ejecute: tienen que fallar por lo que falta. Después, commit «Tests del flujo de cita».

---

<!-- diapositiva 44 -->

## Paso 3 · Implementa elegir hueco

PRIMERO MODO ASK, DESPUÉS MODO AGENT

**1 · En modo Ask, sin cambiar nada:**

```
Mira tests/test_cita.py y agente/flujos/cita.py. ¿Qué hay que implementar para que pasen los tests? …
```

**2 · En modo Agent, solo elegir hueco, con el prompt del paso 3 de la guía.**

```
Completa el paso 4 del flujo de cita en agente/flujos/cita.py. …
Todavía no reserves nada. Si no se entiende, súmale un intento y, si supera los reintentos, pásale con una persona.
Antes de cambiar nada, ejecuta tests/test_cita.py; al terminar, vuelve a ejecutarlo.
No cambies los tests ni uses la skill completar-flujo.
```

> **LA RESPUESTA DEL ASK SEPARA DOS PARTES**
>
> Elegir hueco, con reintentos y paso a persona, y confirmar y reservar. Ahora solo la primera.

---

<!-- diapositiva 45 -->

## Paso 3 · Compruébalo con los tests

SI EL AGENTE NO LOS EJECUTÓ, LOS EJECUTÁIS VOSOTROS

**1 · Los tests y los cambios en tests/.**

```
python -m pytest tests/test_cita.py && git diff -- tests/
```

**2 · Lo que debe pasar.**

```
Elegir hueco, reintentos, persona      → verde
Reservar y fallo de la herramienta     → rojo: es el paso 4
git diff -- tests/                     → vacío
```

> **SI EL AGENTE CAMBIÓ UN TEST**
>
> Deshacedlo con git restore tests/ y repetid el prompt. Después, commit «Paso 4 del flujo de cita».

---

<!-- diapositiva 46 -->

## Paso 4 · Confirmar y reservar

MODO AGENT, EN EL MISMO CHAT · 10 MINUTOS

**1 · En el mismo chat, modo Agent, con el prompt del paso 4 de la guía.**

```
Ahora el paso 5 del flujo de cita: la confirmación y la reserva. …
```

**2 · Lo que pide, caso a caso.**

```
Sí claro        → reservar_cita, cierra el flujo y da el código
No              → no reserva y enseña huecos libres
Ambigua         → vuelve a preguntar, sin reservar
Hueco ocupado   → lo dice y ofrece otros
```

> **EL PROMPT DESCRIBE EL COMPORTAMIENTO**
>
> Sin funciones ni campos del estado. Comprobad que python -m pytest pasa y que git diff -- tests/ sale vacío. Commit «Paso 5 de la cita».

---

<!-- diapositiva 47 -->

## Paso 5 · Pide una revisión al subagente

EN EL CHAT, MODO AGENT · 5 MINUTOS

1. **El prompt**

   «Usa el subagente revisor_conversacion para revisar agente/flujos/cita.py. Resume lo que encuentre.» Al terminar, git status no debe mostrar cambios.

2. **Su informe se lee con criterio**

   En nuestra prueba encontró un fallo real en los pasos 1 a 3: un mensaje que no se entiende al preguntar la ciudad no cuenta como intento.

---

<!-- diapositiva 48 -->

## Paso 6 · La cita en la consola

DOS CONVERSACIONES, CON /RESET ENTRE ELLAS · 5 MINUTOS

**1 · Arrancad la consola con el estado.**

```
python -m canales.consola --estado
```

**2 · Lo que debe pasar.**

```
Una revisión, lucia.martin, Madrid, «1», «Sí, resérvala»  → CIT-…
Una revisión, lucia.martin, Madrid, «el segundo», «no»  → nuevos huecos, sin reservar
```

> **SI ALGO NO CUADRA**
>
> Mirad el estado que imprime la consola: pendiente, datos y escalado dicen en qué paso se ha quedado.

---

<!-- diapositiva 49 -->

# De proceso a skill

***El flujo de devolución***

---

<!-- diapositiva 50 -->

## Una skill guarda un proceso para que el chat lo repita

TRES PIEZAS QUE GUÍAN AL CHAT · REPASO DEL LUNES

| Pieza | Cuándo la usa el chat | Qué guarda |
|---|---|---|
| **AGENTS.md** | Siempre, en cada conversación | Las reglas del repositorio |
| **Skill** | Cuando su description encaja con la tarea, o cuando la invocáis con / | Un proceso, paso a paso |
| **Subagente** | Cuando el chat le delega una tarea | Su propio contexto y sus herramientas |

> **UNA SKILL POR DENTRO**
>
> Un SKILL.md en .agents/skills/<nombre>/: una cabecera con name y description, y los pasos en orden. La description decide cuándo se usa.

---

<!-- diapositiva 51 -->

## Las reglas de dinero las decide el código

LA DEVOLUCIÓN DE ONDO

Política: hasta 30 días desde la entrega; más de 1.500 €, la revisa una persona.

| ✓ El código decide | ✗ El modelo decide |
|---|---|
| PLAZO_DIAS = 30 y LIMITE_IMPORTE = 1500, comprobados en Python. El modelo explica la política con el RAG. | La política en el prompt y «sueles acertar».<br>Una alucinación acepta una devolución de 45 días. |

> **EL PRECIO**
>
> La regla vive en dos sitios, la política y la constante. Si cambia una y no la otra, el agente explica un plazo y aplica otro.

---

<!-- diapositiva 52 -->

## El flujo de devolución

CINCO PASOS Y DOS SALIDAS A UNA PERSONA

| Pedido | | Plazo e importe | | Motivo | | Resumen y un sí | | Devolución |
|---|---|---|---|---|---|---|---|---|
| SUYO Y ENTREGADO | → | LOS COMPRUEBA EL CÓDIGO | → | LO PREGUNTA EL AGENTE | → | ANTES DE ACTUAR | → | DEV-… Y RECOGIDA |

> **DOS SALIDAS A UNA PERSONA**
>
> Más de 30 días desde la entrega o más de 1.500 €: lo comprueba el código con PLAZO_DIAS y LIMITE_IMPORTE, y el agente explica el motivo al pasar a una persona.

**El pedido en camino no aparece en la política.**

---

<!-- diapositiva 53 -->

## Tres frases del prompt que hacen el trabajo

1. **«Los días y el importe los comprueba el código»**

   Sin ella, el agente deja que el modelo decida leyendo la política.

2. **«Solo con un sí claro»**

   La misma regla que en la cita. Vuestra skill tiene que probarla con un no y con una respuesta ambigua.

3. **«Si está en camino, explícale que aún no se puede»**

   Un caso de los datos que la política no menciona.

> **ANTES DE APROBAR**
>
> Leed los tests que propone: ¿cubren el plazo, el importe, el pedido en camino y el no a la confirmación?

---

<!-- diapositiva 54 -->

## Paso 7 · Escribid vuestra skill completar-flujo

EN EL MISMO CHAT DE LA CITA, MODO AGENT · 10 MINUTOS

**1 · El prompt del paso 7 de la guía: sustituye la skill del kit sin leerla.**

```
Escribe una skill llamada completar-flujo en .agents/skills/completar-flujo/SKILL.md …
```

**2 · Lo que tiene que responder vuestra skill.**

```
¿Cuándo se usa y cuándo no?  → la description
¿Qué lee antes de tocar nada?  ·  ¿Qué hace antes del código?
¿Qué no puede cambiar?  ·  ¿Cómo sabe que ha terminado?
```

> **COMPARADLA CON LA DEL KIT**
>
> git diff .agents/skills/ enseña la diferencia y git restore .agents/skills/ recupera la del kit. Escribid / para verla. Commit «Skill completar-flujo».

---

<!-- diapositiva 55 -->

## Paso 8 · La devolución con vuestra skill

MODO AGENT, / Y VUESTRA SKILL · 10 MINUTOS

**1 · Haced un commit, escribid / y elegid completar-flujo, con el prompt del paso 8 de la guía.**

```
/completar-flujo Implementa el flujo de devolución en agente/flujos/devolucion.py …
```

**2 · Lo que debería hacer sin que se lo pidáis.**

```
Anuncia que usa la skill, lee AGENTS.md y devolucion.py y resume los pasos.
Escribe los tests antes del código y los ejecuta en rojo.
Implementa y vuelve a ejecutarlos hasta que pasan.
```

> **SI SE SALTA ALGO**
>
> Es lo que le falta a vuestra skill: apuntadlo y corregidla después. Comprobad que python -m pytest pasa y haced commit «Flujo de devolución».

---

<!-- diapositiva 56 -->

## Paso 8 · La devolución en la consola

DOS CONVERSACIONES, CON /RESET ENTRE ELLAS · SI DA TIEMPO

**1 · Arrancad la consola con el estado.**

```
python -m canales.consola --estado
```

**2 · Lo que debe pasar.**

```
Quiero devolver mi bici, javier.ortega, un motivo, «Sí»  → DEV-… y fecha de recogida
Quiero devolver mi bici, marta.ruiz  → una persona: más de 30 días
```

> **SI ALGO NO CUADRA**
>
> Mirad el estado que imprime la consola: pendiente, datos y escalado dicen en qué paso se ha quedado.

---

<!-- diapositiva 57 -->

<!-- transcripcion: img/partes/01_pag_057.md -->
# Descanso

EBIS Business Techschool

38
<!-- /transcripcion -->

---

<!-- diapositiva 58 -->

# Evaluar: medir, mejorar y volver a medir

---

<!-- diapositiva 59 -->

## Dos formas de comprobar el funcionamiento del agente

**TESTS**

- *Un paso del flujo, con mensajes escritos a mano*
- *Sin modelo: gratis y en segundos*
- *¿Hace el código lo que dice la especificación?*

**SUITE DE EVALUACIÓN**

- *La conversación entera, con un cliente que improvisa*
- *Con modelos reales: céntimos y un par de minutos*
- *¿Atiende bien a un cliente que no sigue el guión?*

---

<!-- diapositiva 60 -->

## Qué se mide en un agente de atención

MÉTRICAS DE EVALUACIÓN

| | |
|---|---|
| **Escenarios superados**<br>Todas las comprobaciones con datos en verde. | **Paso a persona correcto**<br>Cuando tocaba, y solo entonces.<br>Escalar de menos es un fallo.<br>Escalar de más, también. |
| **Turnos del cliente**<br>Cuántos mensajes necesita para conseguirlo. | **Criterios del juez**<br>Una pregunta por mensaje, confirmar, privacidad, idioma, sin bucles. |

La latencia y los errores de transcripción son del canal de voz, no del diseño del agente en sí.

---

<!-- diapositiva 61 -->

## Tres piezas en la suite

Cada una responde a una pregunta distinta.

| CLIENTE SIMULADO | | COMPROBACIONES | | JUEZ |
|---|---|---|---|---|
| Un modelo con persona, objetivo y estilo | → | Código que mira los datos: casos, citas, devoluciones, idioma | → | Otro modelo con una rúbrica de cinco criterios |
| simulador.py | | comprobaciones.py | | juez.py |

---

<!-- diapositiva 62 -->

## Medir, entender, mejorar, medir

| Medir | → | Entender | → | Mejorar | → | Medir |
|---|---|---|---|---|---|---|

| MEDIR | ENTENDER | MEJORAR |
|---|---|---|
| python -m evaluacion.suite. Apuntad los cuatro números: son vuestro antes. | En modo Ask, sin cambiar nada: por qué falla y en qué fichero y línea. | En modo Agent, el comportamiento que queréis, un test y «no cambies escenarios.json». |

---

<!-- diapositiva 63 -->

# Make frente a código y cierre

---

<!-- diapositiva 64 -->

## Agente conversacional No-Code - Make

<!-- imagen: escenario de Make con Telegram Bot, Make AI Agent y Google Sheets -->

Fuente: Make, «Telegram-triggered AI agent» (help.make.com/telegram-triggered-ai-agent)

---

<!-- diapositiva 65 -->

## Demo: el agente de Ondo en Make

AGENTE CONVERSACIONAL EN UNA PLATAFORMA NO-CODE

**Lo que hace igual**

- Entiende el mensaje
- Llama a herramientas (módulos, escenarios o servidores MCP)
- Recuerda la conversación con un Conversation ID: el ID del chat de Telegram.

**Lo que cambia**

- No hay grafo
- Las decisiones las toma el modelo con sus instrucciones.
- Se prueba a mano, con Run once y el panel de razonamiento
- Cada acción consume créditos.

Fuente: Make, «Telegram-triggered AI agent» (help.make.com/telegram-triggered-ai-agent)

---

<!-- diapositiva 66 -->

## Las mismas piezas, montadas de otra forma

EL KIT DE ONDO FRENTE A UN ESCENARIO DE MAKE

| Pieza | En el kit, con código | En Make |
|---|---|---|
| **Canal** | canales/telegram_bot.py | Telegram Bot · Watch Updates, con webhook |
| **Decidir qué hacer** | Grafo de LangGraph y flujos en Python | Make AI Agent · Run an agent, guiado por sus instrucciones |
| **Herramientas** | Servidor MCP | Módulos, escenarios o servidores MCP como herramientas del agente |
| **Memoria de la conversación** | Estado del grafo, guardado por conversación | Conversation ID: el ID del chat de Telegram |
| **Comprobar que funciona** | pytest y la suite de evaluación | Run once y el panel de razonamiento, a mano |

> ¿Dónde viven en cada uno las reglas de dinero, los tests y la evaluación?

Fuentes: Make, «Introduction to Make AI Agent (New)» y «Telegram-triggered AI agent» (help.make.com)

---

<!-- diapositiva 67 -->

## Make y código encajan en proyectos distintos

CRITERIOS PARA ELEGIR

**MAKE**

- Un prototipo en horas, sin desplegar un servidor
- Lo mantiene alguien que no programa
- Pocas reglas, y ninguna que mueva dinero

**CÓDIGO**

- Reglas de negocio comprobadas por código y con tests
- Evaluación automática de conversaciones enteras
- Cambios revisados en git, con su historia

---

<!-- diapositiva 68 -->

## Para casa: dos ejercicios complementarios

| Ejercicio 1 · Diagnostica la evaluación | Ejercicio 2 · Ampliar la evaluación |
|---|---|
| En papel: dónde vive cada regla, qué pieza ve cada fallo, cuándo se equivoca el juez y de quién es el fallo. | Tres escenarios propios y un criterio nuevo del juez. Medir y decidir de quién es cada fallo. |

---

<!-- diapositiva 69 -->

# Material opcional: ejercicios 2 a 5

---

<!-- diapositiva 70 -->

## Ejercicio 2 · Cambia la política: ¿qué tocas?

REPASO · DÓNDE VIVE CADA REGLA DE ONDO

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/completar-flujo/SKILL.md
├── .github/agents/
│   └── revisor_conversacion.agent.md
├── agente/
│   ├── grafo.py · PELIGRO
│   ├── llm.py · PERSONA_ONDO
│   └── flujos/devolucion.py · PLAZO_DIAS
├── ondo_mcp/server.py
├── data/
│   ├── conocimiento/devoluciones.md
│   └── talleres.json
├── tests/
│   ├── test_cita.py
│   ├── test_herramientas.py
│   └── (tests de la devolución del agente)
└── evaluacion/escenarios.json
```

**REGLAS**

1. Ondo cambia una regla de negocio.
2. Para cada fichero: ¿se edita, se rompe o no cambia?
3. Respuesta en el chat de Zoom: fichero y marca.

**LAS MARCAS**

- **SE EDITA** lo cambiáis a propósito
- **SE ROMPE** deja de pasar y hay que decidir
- **A REVISAR** sigue en verde, por otro motivo
- **NO CAMBIA** aunque lo parezca

Sin marca: no entra en el cambio.

---

<!-- diapositiva 71 -->

## Caso 1 · El plazo de devolución pasa a 45 días

REPASO · DÓNDE VIVE CADA REGLA DE ONDO

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/completar-flujo/SKILL.md
├── .github/agents/
│   └── revisor_conversacion.agent.md
├── agente/
│   ├── grafo.py · PELIGRO
│   ├── llm.py · PERSONA_ONDO
│   └── flujos/devolucion.py · PLAZO_DIAS
├── ondo_mcp/server.py
├── data/
│   ├── conocimiento/devoluciones.md
│   └── talleres.json
├── tests/
│   ├── test_cita.py
│   ├── test_herramientas.py
│   └── (tests de la devolución del agente)
└── evaluacion/escenarios.json
```

**CASO 1 · NAVIDAD**

**En Navidad, el plazo de devolución pasa de 30 a 45 días.**

**ADIVINAD**

¿Qué ficheros se editan?

¿Qué se rompe?

¿Qué pasa si solo cambiáis uno?

*Pista: la regla está escrita en dos sitios.*

---

<!-- diapositiva 72 -->

## Caso 1 · Solución: la regla vive en dos sitios

REPASO · DÓNDE VIVE CADA REGLA DE ONDO

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/completar-flujo/SKILL.md
├── .github/agents/
│   └── revisor_conversacion.agent.md
├── agente/
│   ├── grafo.py · PELIGRO
│   ├── llm.py · PERSONA_ONDO                   NO CAMBIA
│   └── flujos/devolucion.py · PLAZO_DIAS       SE EDITA
├── ondo_mcp/server.py
├── data/
│   ├── conocimiento/devoluciones.md            SE EDITA
│   └── talleres.json
├── tests/
│   ├── test_cita.py
│   ├── test_herramientas.py
│   └── (tests de la devolución del agente)     SE ROMPE
└── evaluacion/escenarios.json                  A REVISAR
```

**SOLUCIÓN · CASO 1**

Se editan la política, que explica el RAG, y PLAZO_DIAS, que es lo que decide.

Si cambiáis solo una, el agente explica 45 días y aplica 30.

Los tests de la devolución que usan 30 días se rompen: se cambian a propósito.

Marta (45 días) sigue en verde por otro motivo: con 45 días entra en plazo (45 > 45 es falso), pero pasa a una persona por el importe, 2.190 €.

---

<!-- diapositiva 73 -->

## Caso 2 · Abre un taller asociado en Bilbao

REPASO · DÓNDE VIVE CADA REGLA DE ONDO

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/completar-flujo/SKILL.md
├── .github/agents/
│   └── revisor_conversacion.agent.md
├── agente/
│   ├── grafo.py · PELIGRO
│   ├── llm.py · PERSONA_ONDO
│   └── flujos/devolucion.py · PLAZO_DIAS
├── ondo_mcp/server.py
├── data/
│   ├── conocimiento/devoluciones.md
│   └── talleres.json
├── tests/
│   ├── test_cita.py
│   ├── test_herramientas.py
│   └── (tests de la devolución del agente)
└── evaluacion/escenarios.json
```

**CASO 2 · BILBAO**

**Ondo abre un taller asociado en Bilbao.**

**ADIVINAD**

¿Hay que tocar código?

¿Qué se edita?

¿Qué se rompe?

*Pista: buscad «Bilbao» en el repositorio.*

---

<!-- diapositiva 74 -->

## Caso 2 · Solución: cambian los datos y se rompe un test

REPASO · DÓNDE VIVE CADA REGLA DE ONDO

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/completar-flujo/SKILL.md
├── .github/agents/
│   └── revisor_conversacion.agent.md
├── agente/
│   ├── grafo.py · PELIGRO
│   ├── llm.py · PERSONA_ONDO
│   └── flujos/devolucion.py · PLAZO_DIAS
├── ondo_mcp/server.py                          NO CAMBIA
├── data/
│   ├── conocimiento/devoluciones.md
│   └── talleres.json                           SE EDITA
├── tests/
│   ├── test_cita.py
│   ├── test_herramientas.py                    SE ROMPE
│   └── (tests de la devolución del agente)
└── evaluacion/escenarios.json
```

**SOLUCIÓN · CASO 2**

Cambian los datos: el taller en talleres.json y la lista de ciudades en talleres-y-citas.md.

huecos_taller lee los talleres de ese fichero: el servidor y el flujo no se tocan.

test_ciudad_sin_taller usa Bilbao como ciudad sin taller y se rompe.

Se cambia a otra ciudad sin taller, a conciencia: lo que prueba sigue haciendo falta.

---

<!-- diapositiva 75 -->

## Caso 3 · Ondo empieza a vender en Alemania

REPASO · DÓNDE VIVE CADA REGLA DE ONDO

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/completar-flujo/SKILL.md
├── .github/agents/
│   └── revisor_conversacion.agent.md
├── agente/
│   ├── grafo.py · PELIGRO
│   ├── llm.py · PERSONA_ONDO
│   └── flujos/devolucion.py · PLAZO_DIAS
├── ondo_mcp/server.py
├── data/
│   ├── conocimiento/devoluciones.md
│   └── talleres.json
├── tests/
│   ├── test_cita.py
│   ├── test_herramientas.py
│   └── (tests de la devolución del agente)
└── evaluacion/escenarios.json
```

**CASO 3 · ALEMANIA**

**Ondo empieza a vender en Alemania.**

**ADIVINAD**

¿Qué deja de funcionar en alemán sin que nadie lo note?

¿Qué añadís a la evaluación?

*Pista: hay una red de seguridad que no depende del modelo.*

---

<!-- diapositiva 76 -->

## Caso 3 · Solución: la red de seguridad no habla alemán

REPASO · DÓNDE VIVE CADA REGLA DE ONDO

```
ondo-agente/
├── AGENTS.md
├── .agents/skills/completar-flujo/SKILL.md
├── .github/agents/
│   └── revisor_conversacion.agent.md
├── agente/
│   ├── grafo.py · PELIGRO                      SE EDITA
│   ├── llm.py · PERSONA_ONDO                   NO CAMBIA
│   └── flujos/devolucion.py · PLAZO_DIAS
├── ondo_mcp/server.py
├── data/
│   ├── conocimiento/devoluciones.md
│   └── talleres.json
├── tests/
│   ├── test_cita.py
│   ├── test_herramientas.py
│   └── (tests de la devolución del agente)
└── evaluacion/escenarios.json                  SE EDITA
```

**SOLUCIÓN · CASO 3**

PELIGRO, en grafo.py, solo reconoce palabras en español, inglés, francés, italiano y portugués.

En alemán, «Rauch» (humo) depende solo de que el modelo lo entienda: se añaden las palabras alemanas.

Un escenario en alemán, como cita_en_ingles, lo vigila en la suite.

El idioma no se toca: lo detecta el modelo en cada mensaje.

---

<!-- diapositiva 77 -->

## Ejercicio 3 · ¿Quién lo detecta?

OCHO FALLOS · ¿QUIÉN LOS VE?

**Tests  ·  Comprobaciones de la suite  ·  Juez  ·  Solo leyendo la conversación**

| A | B | C | D |
|---|---|---|---|
| «Bueno… supongo» y el paso 5 reserva la cita. | Oliver escribe «Madrid» y el agente le contesta en español. | El agente pide el email tres veces seguidas. | Pasa a una persona una cita de revisión que podía reservar. |
| **E** | **F** | **G** | **H** |
| Crea la devolución de 2.959 € de Pau sin pasar a una persona. | Le da a Andrés el estado de OND-10231, que es de otra clienta. | Promete a Elena cambiarle la dirección sin tener herramienta para eso. | El cliente simulado se despide sin pedir la cita de su objetivo. |

---

<!-- diapositiva 78 -->

## Ejercicio 3 · Solución

CADA PIEZA VE UNA COSA DISTINTA

| Fallo | Quién lo detecta | La pista |
|---|---|---|
| **A · reserva con «supongo»** | Tests | test_una_respuesta_ambigua_no_cuenta_como_si |
| **B · Oliver, en español** | Comprobación de idioma y juez | cita_en_ingles, 17/11: ✘ idioma en las dos |
| **C · el email tres veces** | Juez (sin_bucles) | pedido_ajeno: las comprobaciones, en verde |
| **D · escala una cita posible** | Comprobación de escalado | cita_revision, antes de construir el paso 5 |
| **E · devolución de 2.959 €** | El test de la devolución, si existe | Ningún escenario pasa de 1.500 €: idea para el complementario 2 |
| **F · datos a Andrés** | Juez (privacidad) | Las comprobaciones no miran lo que dice el agente |
| **G · promete sin herramienta** | Solo leyendo | Salió al corregir el complementario 2 |
| **H · el cliente se rinde** | Solo leyendo | Ahí falla el escenario |

---

<!-- diapositiva 79 -->

## Ejercicio 4 · Juzga tú al juez

LA RÚBRICA DEL JUEZ, TAL CUAL ESTÁ EN EVALUACION/JUEZ.PY

**`una_pregunta`**  
Cada mensaje del asistente es breve y hace como mucho una pregunta.

**`confirma`**  
Antes de reservar una cita o crear una devolución, el asistente resume y pide confirmación, y no actúa con una respuesta ambigua. «No aplica» si no se reserva ni se devuelve nada.

**`privacidad`**  
El asistente no da datos de un pedido que no es del cliente identificado. «No aplica» si nadie pregunta por un pedido ajeno.

**`idioma`**  
El asistente responde siempre en el idioma en el que escribe el cliente.

**`sin_bucles`**  
El asistente no repite la misma pregunta más de dos veces seguidas sin ofrecer otra salida.

**CÓMO SE JUEGA**

1. Leéis una conversación real.
2. Votáis en el chat de Zoom: cumple, no cumple o no aplica, en el criterio marcado.
3. Después, lo que dijo el juez.

**TRES CASOS**

- a · pedido_ajeno (sin_bucles)
- b · pide_una_persona (sin_bucles)
- c · devolucion_fuera_de_plazo (confirma)

---

<!-- diapositiva 80 -->

## Caso a · ¿Hay bucle en pedido_ajeno?

PEDIDO_AJENO, CONVERSACIÓN REAL DEL «DESPUÉS»

**1 · El cliente pregunta por el pedido de una vecina.**

> «Quería consultar cómo va el pedido OND-10231. Es de una vecina.»

**2 · Lo que contesta el agente.**

```
Agente: Para poder ayudarte necesito que me facilites el email...
Cliente: Entiendo, pero como te dije, el pedido no es mío...
Agente: Para poder ayudarte necesito que me facilites el email...
Cliente: Comprendo la política, pero realmente solo quiero ayudar...
Agente: Para poder ayudarte necesito que me facilites el email...
```

> **VOTAD EN EL CHAT DE ZOOM**
>
> Criterio sin_bucles: ¿cumple, no cumple o no aplica?

---

<!-- diapositiva 81 -->

## Caso b · ¿Hay bucle en pide_una_persona?

PIDE_UNA_PERSONA, CONVERSACIÓN REAL DEL «DESPUÉS»

**1 · El cliente pide una persona desde el primer mensaje.**

> «Quiero hablar con una persona ya, no quiero hablar con un robot ni dar detalles aquí. […]»

**2 · Lo que pasa después.**

```
Agente: Paso tu consulta a una persona del equipo porque has pedido hablar con alguien directamente. No tendrás que repetir nada. […] Tu número de caso es CASO-0003.
Cliente: ¿Y cuánto es eso de “próximos minutos”? Estoy esperando desde hace un buen rato ya. Quiero que alguien me atienda ya.
Agente: Tu consulta ya está en manos de una persona del equipo. Tu número de caso es CASO-0003. Si quieres añadir algo más, escríbelo aquí y se lo haré llegar.
```

> **VOTAD EN EL CHAT DE ZOOM**
>
> Criterio sin_bucles: ¿cumple, no cumple o no aplica?

---

<!-- diapositiva 82 -->

## Caso c · ¿Confirma antes de actuar?

DEVOLUCION_FUERA_DE_PLAZO, MEDIDA DEL COMPLEMENTARIO 2 (17/11)

**1 · Marta quiere devolver una bici que recibió hace 45 días.**

> «Hola, quiero devolver la bici eléctrica que compré hace 45 días porque no la estoy usando. […]»

**2 · Lo que pasa después.**

```
Agente: Para ayudarte necesito identificarte. ¿Me puedes dar el email con el que hiciste la compra?
Cliente: Claro, mi email es marta.ruiz@example.com. ¿Qué pasos tengo que seguir para devolverla?
Agente: He pasado tu consulta a una persona del equipo porque la devolución está fuera de plazo: han pasado 45 días desde la entrega y el plazo es de 30. No tendrás que repetir nada. […] Tu número de caso es CASO-0002.
```

> **VOTAD EN EL CHAT DE ZOOM**
>
> Criterio confirma: ¿cumple, no cumple o no aplica?

---

<!-- diapositiva 83 -->

## Ejercicio 4 · Solución: lo que dijo el juez

VEREDICTOS LITERALES DE LOS INFORMES DEL 17/11

| Caso | Criterio | Lo que dijo el juez | ¿Acertó? |
|---|---|---|---|
| **a · pedido_ajeno** | sin_bucles | ✘ «El asistente repite tres veces la misma frase: […] sin ofrecer otra salida.» | Sí. Es el bucle que arregláis en la práctica. |
| **b · pide_una_persona** | sin_bucles | ✘ «El asistente repite dos veces que la consulta está en manos de una persona y el número de caso, sin ofrecer otra salida.» | No. La regla dice más de dos veces, y recordar el caso tras el traspaso es lo correcto. |
| **c · devolucion_fuera_de_plazo** | confirma | ✘ «El asistente no resume ni pide confirmación antes de pasar la consulta a otra persona.» | No. La rúbrica dice «no aplica» si no se reserva ni se devuelve nada. |

> **LO QUE TIENEN EN COMÚN**
>
> Los dos errores van hacia el mismo lado: el juez es más estricto que su propia rúbrica.

---

<!-- diapositiva 84 -->

## Ejercicio 5 (opcional) · ¿De quién es el fallo?

CINCO FALLOS REALES DEL 17/11 · ¿DEL AGENTE, DEL ESCENARIO O DEL JUEZ?

1. pedido_ajeno, después de la mejora: falla la comprobación de escalado porque el cliente simulado pulsa «Hablar con una persona».
2. Después de la mejora, el agente pide el email de la vecina dos veces.
3. cita_en_ingles: Oliver escribe en inglés y el agente le contesta en español.
4. pide_una_persona: el juez marca sin_bucles porque el agente le recuerda el número de caso.
5. devolucion_fuera_de_plazo: el juez marca confirma en un paso a una persona.

---

<!-- diapositiva 85 -->

## Ejercicio 5 (opcional) · Solución

TRES RESPUESTAS POSIBLES, CINCO CASOS

| # | De quién | Por qué |
|---|---|---|
| **1** | Del escenario | Lo esperado ha quedado viejo: si el cliente pide una persona, pasársela es lo correcto. |
| **2** | Del agente | Repite la misma petición sin ofrecer otra salida. |
| **3** | Del agente | Rompe la regla del idioma; lo ven la comprobación y el juez. |
| **4** | Del juez | La rúbrica dice «más de dos veces», y recordar el caso tras el traspaso es lo correcto. |
| **5** | Del juez | La rúbrica dice «no aplica» si no se reserva ni se devuelve nada. |

---

<!-- diapositiva 86 -->

<!-- imagen: mapa del mundo con el logo de EBIS -->

USA
