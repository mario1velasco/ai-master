# Sesión 2: Construir con tests y evaluar

Explicación sencilla del día 2 del Tema 10, centrada en las ideas principales. Se construye a partir de los `.md` de `clase_02/`: las diapositivas de la sesión, la guía de clase «Construir y evaluar» y los dos ejercicios complementarios con su corrección. Lo que se cuenta del código sale de esos materiales; el kit está en `../ondo-agente/`.

---

## 0. Dónde estamos

### El mapa del tema

| Día | Bloque | Qué se hace |
|---|---|---|
| 1 · 23/11 | Diseño y chat | Reglas para diseñar una conversación, el agente de Ondo por dentro y el bot de Telegram |
| **2 · 25/11** | **Tests y evaluación** | Completar el flujo de cita con tests primero, convertir ese proceso en una skill, construir la devolución con ella y medir el agente (esta sesión) |
| 3 · 30/11 | Voz y teléfono | Voz en el navegador, llamada por teléfono y paso a una persona |

El día 1 se vio **cómo está hecho** el agente de Ondo. Hoy se **termina** (la cita y la devolución, que el día 1 estaban a medias) y se aprende a **medir** si atiende bien.

### La idea de toda la sesión

La guía lo dice en la primera línea: es **una forma de trabajar que sirve para cualquier implementación asistida con IA**.

1. Primero, **los tests como especificación**.
2. Después, **la implementación**.
3. Al final, **la validación** con los tests.

Con ese proceso se construye la cita, después se guarda como **skill** y con la skill se construye la devolución. Por último se **mide** el agente con conversaciones simuladas, se elige un fallo, se arregla y se vuelve a medir.

### Repaso de los complementarios del día 1

| Ejercicio | Lo que había que sacar |
|---|---|
| Sé el grafo | **El orden de la ruta decide**: primero la seguridad, después el caso abierto y luego los flujos |
| Diagnostica la conversación | Fallos reales: «¿Eres una persona?» abre un caso y el RAG no encuentra el plazo de devolución |

---

## 1. Repaso: el código y las piezas que guían al chat

La primera parte de la clase repasa lo del día 1 (secciones 5 y 6 de `../clase_01/explicacion-10.md`): los cinco ficheros de `agente/` y los **dos agentes distintos** (el de Ondo, que habla con los clientes, y el chat de VS Code, que te ayuda a programarlo).

Lo nuevo del repaso son dos cosas.

### 1.1 Prompt, prompt file y skill no son lo mismo

| Pieza | Qué es |
|---|---|
| **Prompt** | Lo que escribes ahora. Vive solo en esa conversación y hay que repetirlo cada vez |
| **Prompt file** | Una plantilla de prompt guardada en un fichero. **La lanzas tú a mano** con `/`; no se carga sola |
| **Instrucción de carpeta** (`AGENTS.md`, `CLAUDE.md`) | Contexto y reglas del proyecto. La IA arranca con esa memoria sin que se lo expliques |
| **Skill** | Una carpeta con instrucciones, reglas o scripts que la IA **carga bajo demanda**, solo cuando la tarea lo requiere, «como un especialista temporal» |
| **Agente** | IA que persigue un objetivo en varios pasos: planifica, actúa, comprueba e itera |
| **Servidor MCP** | El puente que conecta la IA con datos reales y acciones de otros sistemas |

La diferencia práctica entre un prompt file y una skill: el prompt file **siempre lo lanzas tú**; la skill la puede elegir **el propio agente** cuando su descripción encaja con la tarea.

### 1.2 Caso · Completar y probar

Un proyecto con varias piezas (`AGENTS.md`, dos skills, dos subagentes —`qa` y `revisor_conversacion`—, `AGENTS.md` dentro de `tests/` y de `evaluacion/`) y esta petición:

> «Añade al flujo de devolución el caso del pedido en camino y pide al agente qa que lo pruebe.»

Hay que adivinar qué entra en memoria y en qué orden trabaja el asistente. La solución:

| Pieza | Cómo entra |
|---|---|
| `AGENTS.md` de la raíz | **Siempre** |
| Skill `completar-flujo` | **Al vuelo**: «añade al flujo de devolución» encaja con ella |
| Subagente `qa` | **Al vuelo**: la petición lo nombra |
| `tests/AGENTS.md` | **Al vuelo**: se va a escribir un test |
| Skill `afinar-prompt` y subagente `revisor_conversacion` | **Solo la descripción**: se sabe que existen, pero no se leen |
| `evaluacion/AGENTS.md` | **No entra**: no se toca esa carpeta |

El orden: llega el mensaje → entra la skill → escribe el **test** del pedido en camino → cambia `devolucion.py` **hasta que el test pasa, sin tocar el test** → llama a `qa` para que pruebe → `qa` responde corto qué pasa y qué falla → el asistente lo resume y corrige.

> `qa` prueba con su propio contexto: **puede ejecutar los tests, pero no editar**. Si algo falla, lo corrige el asistente principal con la skill.

---

## 2. Cómo trabajar con un asistente de código: tests primero

### 2.1 Tres fases, dos son tuyas

| Fase | Qué es | Quién la hace |
|---|---|---|
| **1 · Especificación** | Qué tiene que pasar y cómo se comprueba: comportamientos, casos límite y tests | **Tú**. Fase crítica |
| **2 · Implementación** | El asistente escribe el código siguiendo la especificación y `AGENTS.md` | **La IA**, con el alcance que le fijas |
| **3 · Validación** | Los tests pasan, la especificación no ha cambiado y lees el diff antes del commit | **Tú**. Fase crítica |

> Vale para cualquier trabajo con IA: **las personas definen qué es correcto y lo comprueban; la IA trabaja en medio.**

### 2.2 Los tests son la especificación

Tres ideas:

- **«Qué tiene que pasar».** Cada test es un comportamiento: elegir hueco, pedir confirmación, no reservar sin un sí.
- **«Los escribe el chat; los decidís vosotros».** Tú das la lista de comportamientos y **lees los nombres de las funciones** de test: son la especificación.
- **«Antes que el código».** Escritos después, los tests tienden a **copiar lo que el código ya hace, aunque esté mal**.

### 2.3 Tres tiempos para cualquier cambio

1. **Tests**: primero y **en rojo**. Tienen que fallar por lo que falta, no por un error del test.
2. **Implementación**: antes, una pregunta en **modo Ask** («¿qué falta?»); después, **solo lo pedido**, en **modo Agent**.
3. **Validación**: los tests pasan y `git diff -- tests/` sale **vacío**: nadie ha cambiado la especificación.

Este proceso siempre debería ser igual, así que es **candidato a skill** (sección 4).

### 2.4 Un test en rojo puede fallar por dos motivos

| Motivo | Ejemplo | Qué haces |
|---|---|---|
| **Por lo que falta** | `AssertionError`: el flujo todavía no pide confirmación | Nada: es lo esperado antes de implementar |
| **Por el propio test** | `ImportError`, un nombre mal escrito, un estado mal construido | Arreglar el test antes de seguir |

### 2.5 Validar es comprobar dos cosas

1. Que los tests pasan: `python -m pytest tests/test_cita.py`.
2. Que **nadie ha tocado los tests para que pasen**: `git diff -- tests/` no debe mostrar nada.

> Si el agente cambió un test, se deshace con `git restore tests/`: `AGENTS.md` se lo prohíbe y **la especificación es tuya**.

---

## 3. Práctica: completar el flujo de cita

### 3.1 Las capas que se construyen hoy

| Capa | Dónde | Cómo |
|---|---|---|
| La cita, a mano | `agente/flujos/cita.py` | Pasos 4 y 5 del flujo, con tus tests |
| La devolución, con tu skill | `agente/flujos/devolucion.py` | Tu skill escribe los tests primero |
| La evaluación | `evaluacion/` | Diez clientes simulados |

Antes de empezar se actualiza el kit (`git pull` trae la carpeta `evaluacion/` sin tocar tu `cita.py`, o el ZIP del día 2) y se comprueba que `python -m pytest` pasa entero: de momento **solo hay tests del servidor MCP**.

### 3.2 El flujo de cita pide un dato en cada paso

```
Motivo → Ciudad → Huecos → Elegir hueco → Confirmar y reservar
paso 1   paso 2   paso 3   paso 4 (hoy)   paso 5 (hoy)
```

El **estado** recuerda en qué paso está:

- `pendiente` dice qué respuesta espera («hueco», «confirmar_cita»).
- `datos` guarda lo ya decidido.
- `intentos_fallidos` cuenta los mensajes que no se entienden: al superar `MAX_REINTENTOS = 2`, pasa a una persona.

> **El modelo interpreta; el código sabe en qué paso está.**

### 3.3 Los seis comportamientos: tu especificación

| Grupo | Comportamiento |
|---|---|
| **Camino ideal** | 1 · El cliente elige un hueco |
| | 2 · El agente pide confirmación |
| | 3 · Solo con un sí claro se reserva |
| **Reparación** | 4 · Si no entiende, reintenta |
| | 5 · Si falla demasiadas veces, pasa a una persona |
| **Si algo falla** | 6 · Si la herramienta falla, no inventa éxito: lo dice y ofrece otros huecos |

Quién hace qué en una reserva:

- El **«sí»** lo interpreta **el modelo**.
- La decisión de **reservar** la toma **el código**.
- La **acción** en sí se hace **a través del MCP** (`reservar_cita`).

Ojo: si le preguntas al chat «¿Qué pasos debe cumplir el flujo de cita?», leyendo solo el código **puede no verlos todos**. Los que falten los añades tú, porque la lista es tu especificación.

### 3.4 Un prompt de implementación tiene cuatro partes

| Parte | Ejemplo de la clase |
|---|---|
| **Alcance** | «Solo la consulta de cita. La reserva la haremos después.» |
| **Comportamiento** | «Si no se entiende, súmale un intento y, si supera los reintentos, pásale con una persona.» |
| **Validación** | «Antes de cambiar nada, ejecuta `tests/test_cita.py`; al terminar, vuelve a ejecutarlo.» |
| **Límites** | «No cambies los tests ni uses la skill `completar-flujo`.» |

> **Cada parte quita una decisión que el agente tomaría por su cuenta.**

Y un detalle del paso 5: el prompt **describe el comportamiento** («con un sí claro, reserva…»), **no dice cómo programarlo** (ni funciones ni campos del estado).

### 3.5 Consultar no cambia nada; actuar, sí

| Leer: sin preguntar | Escribir: resumen y un sí claro |
|---|---|
| `buscar_cliente` y `estado_pedido` | `reservar_cita` |
| `huecos_taller` | `crear_devolucion` |
| `buscar_conocimiento` (la política, por RAG) | `escalar_a_humano`: **no se confirma**, se explica el motivo |

Pasar a una persona tiene efecto, pero no se pide permiso: se dice por qué. Esto vuelve a salir en la evaluación (sección 7).

### 3.6 La confirmación tiene tres respuestas (y un imprevisto)

Después de elegir hueco, el agente resume la cita y pregunta si la reserva:

| El cliente dice | El agente |
|---|---|
| **Un sí claro** | Reserva con `reservar_cita`, cierra el flujo y da el código `CIT-…` |
| **Un no** | No reserva y vuelve a enseñar huecos libres |
| **Algo ambiguo** («Vale, bueno, no sé») | Cuenta como duda: vuelve a preguntar, sin reservar |

El imprevisto: **el hueco se ocupa mientras el cliente decide**. `reservar_cita` devuelve un error si otra persona lo ha cogido entre la oferta y el sí.

- Lo que **no** se hace: dar la cita por hecha porque el cliente dijo que sí.
- Lo que se hace: decirle que ese hueco se acaba de ocupar y enseñarle otros, **en el mismo mensaje**.

Son las reglas del día 1 aplicadas: confirmar según el riesgo, **una respuesta ambigua nunca es un sí** y **no dar por hecho lo que ha fallado**.

### 3.7 Los pasos de la práctica

Las diapositivas y la guía numeran los pasos de forma distinta; aquí va el orden de la guía. No confundir con los «pasos 4 y 5» **del flujo** de cita (elegir hueco y confirmar).

| Paso | Modo del chat | Qué pides | Cómo compruebas |
|---|---|---|---|
| 1 · Entender | Ask | «¿Qué pasos debe cumplir el flujo de cita?» | Compara con los seis comportamientos y añade los que falten |
| 2 · Probar lo de ahora | — | La consola con Lucía | No consigue reservar: falta implementarlo |
| 3 · Solo los tests | Agent | Los tests de los seis comportamientos en `tests/test_cita.py`; para «solo con un sí claro», probar `confirma` `False` **y** `None` | Fallan **por lo que falta**. Lees los nombres de las funciones |
| 4 · Elegir hueco | Ask, después Agent | Primero «¿qué hay que implementar?»; después **solo** el paso 4 del flujo | Pasan los de elegir hueco, reintentos y persona; siguen en rojo los de reservar. `git diff -- tests/` vacío. Commit |
| 5 · Confirmar y reservar | Agent | El paso 5, sin cambiar los tests | `python -m pytest` entero en verde. Commit |
| 6 · Revisión | Agent | El subagente `revisor_conversacion` revisa `cita.py` | Lees su informe con criterio |
| 7 · Consola | — | Las dos conversaciones de Lucía | `CIT-…` con el sí; nuevos huecos con el no |

Mientras trabaja, fíjate en el **orden** que sigue el agente: lee `AGENTS.md`, los tests y `cita.py` → ejecuta los tests → edita → vuelve a ejecutarlos. Ese orden se lo pides tú en el prompt… y como siempre será igual, es lo que se guardará en la skill.

### 3.8 La revisión del subagente

El revisor abre **otro contexto**: no ve tu conversación, lee el código sin arrastrar lo que el chat principal dio por bueno. Solo tiene `read` y `search`: **no edita ni ejecuta**. Devuelve un informe y **tú decides** qué se arregla.

> La frontera la ponen sus herramientas: los permisos limitan lo que puede hacer; las instrucciones solo lo orientan (lo mismo que en el Tema 9).

En la prueba del profesor encontró **un fallo real** en los pasos 1 a 3: un mensaje que no se entiende al preguntar la ciudad **no cuenta como intento**. Es justo uno de los huecos que el kit del día 1 dejaba a propósito.

---

## 4. De proceso a skill: el flujo de devolución

### 4.1 Una skill guarda un proceso para que el chat lo repita

Para la cita has repetido tres veces lo mismo: primero los tests, después la implementación de un solo paso y al final la validación, siempre con las mismas instrucciones. Eso es una skill.

| Pieza | Cuándo la usa el chat | Qué guarda |
|---|---|---|
| `AGENTS.md` | Siempre, en cada conversación | Las reglas del repositorio |
| **Skill** | Cuando su `description` encaja con la tarea, o cuando la invocas con `/` | **Un proceso, paso a paso** |
| Subagente | Cuando el chat le delega una tarea | Su propio contexto y sus herramientas |

Una skill por dentro: un `SKILL.md` en `.agents/skills/<nombre>/` con una cabecera (`name` y `description`) y los pasos en orden. **La `description` decide cuándo se usa.**

### 4.2 Crear tu skill

Le pides al chat (primero en Ask, para que te proponga el prompt; después en Agent) que escriba la skill con el proceso de la cita. El nombre cambia entre materiales (la guía la llama `implementar-cambios`; las diapositivas, `completar-flujo`, como la del kit), pero lo que importa es el proceso.

Lo que tiene que responder tu skill:

- ¿Cuándo se usa y cuándo no? → la `description`.
- ¿Qué lee antes de tocar nada? ¿Qué hace antes del código?
- ¿Qué no puede cambiar? ¿Cómo sabe que ha terminado?

Después la comparas con la del kit (`git diff .agents/skills/`) y decides qué le añades, o recuperas la del kit con `git restore .agents/skills/`.

### 4.3 Las reglas de dinero las decide el código

Política de Ondo: **hasta 30 días** desde la entrega; **más de 1.500 €**, la revisa una persona.

| ✓ El código decide | ✗ El modelo decide |
|---|---|
| `PLAZO_DIAS = 30` y `LIMITE_IMPORTE = 1500`, comprobados en Python. El modelo **explica** la política con el RAG | La política en el prompt y «sueles acertar». **Una alucinación acepta una devolución de 45 días** |

El precio de hacerlo bien: **la regla vive en dos sitios**, la política (lo que explica el RAG) y la constante (lo que decide). Si cambia una y no la otra, el agente explica un plazo y aplica otro. Lo trabaja el ejercicio complementario 1 (sección 7).

### 4.4 El flujo de devolución

```
Pedido → Plazo e importe → Motivo → Resumen y un sí → Devolución
suyo y    los comprueba    lo pregunta  antes de        DEV-… y
entregado el código        el agente    actuar          recogida
```

**Dos salidas a una persona**: más de 30 días desde la entrega o más de 1.500 €. Lo comprueba el código con `PLAZO_DIAS` y `LIMITE_IMPORTE`, y el agente explica el motivo al pasar a una persona.

Y un caso que **la política no menciona**: el pedido que aún está en camino.

### 4.5 Tres frases del prompt que hacen el trabajo

| Frase | Por qué importa |
|---|---|
| «Los días y el importe los comprueba el código» | Sin ella, el agente deja que **el modelo decida leyendo la política** |
| «Solo con un sí claro» | La misma regla que en la cita. Tu skill tiene que probarla con un no y con una respuesta ambigua |
| «Si está en camino, explícale que aún no se puede» | Un caso de los datos que la política no menciona |

El prompt completo también pide: averiguar qué pedido quiere devolver (con botones si tiene varios entregados; sin preguntar si solo tiene uno), comprobar que es suyo, que está entregado y que no tiene ya una devolución, preguntar el motivo y resumir la recogida y el reembolso antes de pedir confirmación.

> Antes de aprobar, **lee los tests que propone**: ¿cubren el plazo, el importe, el pedido en camino y el no a la confirmación?

### 4.6 Lo que debería hacer con tu skill, sin que se lo pidas

1. Anunciar que usa la skill.
2. Leer `AGENTS.md` y `devolucion.py` y resumir los pasos.
3. Escribir los tests **antes** del código y ejecutarlos en rojo.
4. Implementar y volver a ejecutarlos hasta que pasan.
5. Lanzar al subagente revisor.

> Si se salta algo, **es lo que le falta a tu skill**: apúntalo y corrígela después.

En la consola: Javier (`javier.ortega@example.com`) termina en `DEV-…` con fecha de recogida; Marta (`marta.ruiz@example.com`) pasa a una persona porque han pasado más de 30 días.

---

## 5. Evaluar: medir, mejorar y volver a medir

### 5.1 Tests y evaluación no son lo mismo

| Tests | Suite de evaluación |
|---|---|
| **Un paso** del flujo, con mensajes escritos a mano | **La conversación entera**, con un cliente que improvisa |
| Sin modelo: **gratis y en segundos** | Con modelos reales: **céntimos y un par de minutos** |
| ¿Hace el código lo que dice la especificación? | ¿Atiende bien a un cliente que **no sigue el guion**? |

### 5.2 Qué se mide en un agente de atención

| Métrica | Qué significa |
|---|---|
| **Escenarios superados** | Todas las comprobaciones con datos en verde |
| **Paso a persona correcto** | Cuando tocaba, y solo entonces. **Escalar de menos es un fallo; escalar de más, también** |
| **Turnos del cliente** | Cuántos mensajes necesita para conseguirlo |
| **Criterios del juez** | Una pregunta por mensaje, confirmar, privacidad, idioma, sin bucles |

La latencia y los errores de transcripción son del **canal de voz**, no del diseño del agente: no se miden aquí.

### 5.3 Tres piezas en la suite

Cada escenario de `evaluacion/escenarios.json` describe un cliente (quién es, qué quiere y cómo escribe) y lo que tiene que pasar (si se escala y con qué prioridad, si hay cita o devolución, en qué idioma acaba). Hay **diez**.

| Pieza | Fichero | Qué hace |
|---|---|---|
| **Cliente simulado** | `simulador.py` | Un modelo hace de cliente, con la persona, el objetivo y el estilo del escenario |
| **Comprobaciones** | `comprobaciones.py` | **Código** que mira los datos al acabar: casos abiertos, citas y devoluciones creadas, idioma |
| **Juez** | `juez.py` | **Otro modelo** lee la conversación y aplica una rúbrica de cinco criterios |

> **Lo que se puede comprobar con datos lo comprueba el código; el juez solo valora lo que hay que leer.**

La rúbrica del juez:

| Criterio | Qué valora |
|---|---|
| `una_pregunta` | Cada mensaje es breve y hace como mucho una pregunta |
| `confirma` | Antes de reservar o crear una devolución, resume y pide confirmación, y no actúa con una respuesta ambigua. «No aplica» si no se reserva ni se devuelve nada |
| `privacidad` | No da datos de un pedido que no es del cliente identificado |
| `idioma` | Responde siempre en el idioma en el que escribe el cliente |
| `sin_bucles` | No repite la misma pregunta **más de dos veces seguidas** sin ofrecer otra salida |

### 5.4 El ciclo: medir, entender, mejorar, medir

| Paso | Qué haces |
|---|---|
| **Medir** | `python -m evaluacion.suite`. Apunta los cuatro números: son tu **«antes»** |
| **Entender** | En modo Ask, sin cambiar nada: por qué falla y en qué fichero y línea |
| **Mejorar** | En modo Agent: el comportamiento que quieres, un test y **«no cambies escenarios.json»** |
| **Medir** | Primero solo ese escenario (`--solo pedido_ajeno`), después todos |

El informe y las conversaciones quedan en `evaluacion/salidas/` con fecha y hora; la suite usa su propia carpeta de estado, así que no toca tus citas.

> Los números **cambian un poco** de una ejecución a otra, porque el cliente simulado no escribe siempre igual. En las pruebas del profesor: con solo elegir hueco hecho, **5 de 10** escenarios; con el paso 5 y la devolución, **9 de 10**. Por eso no hay que fiarse de una sola medida.

### 5.5 El ejemplo de clase: `pedido_ajeno`

Andrés pregunta por el pedido de una vecina. El agente protege sus datos, bien, pero **repite la misma petición una y otra vez** («necesito que me facilites el email…»). El juez lo marca como bucle.

Se pide el arreglo describiendo el comportamiento: si el cliente insiste, explicar **una sola vez** que solo el titular puede consultar ese pedido y ofrecerle ayuda con sus pedidos o hablar con una persona; nunca revelar datos del pedido ajeno; un test sin llamar al modelo; y no cambiar `escenarios.json`.

Al volver a medir pasaron **tres cosas**, y aquí está la lección de la sesión:

| Qué pasó | Qué significa |
|---|---|
| El bucle del final **desapareció**: explicó una vez y ofreció dos botones | La mejora que pediste |
| El cliente simulado pulsó «Hablar con una persona» y **la comprobación de escalado pasó a fallar**, porque el escenario esperaba que no se escalara | El agente hace bien en pasarlo a una persona. Lo que ha quedado viejo es **el escenario**. **Esa decisión es tuya, no del agente**: si la compartes, cambias tú lo esperado y lo explicas en el commit |
| **Apareció un bucle nuevo antes**: pidió dos veces el email de la vecina | Un fallo nuevo **que la medida ha destapado**. Es el siguiente arreglo |

> **Antes de mirar los números, lee la conversación.** Un arreglo puede quitar un fallo, destapar otro y dejar viejo un escenario.

El commit lleva el antes y el después, con tus números. Por ejemplo: `pedido_ajeno sin bucle al insistir: juez 6/8 → 7/8`.

Otros fallos que salieron al preparar la clase: en `cita_en_ingles` el cliente escribe «Madrid» y el agente **se pasa al español**; en `pedido_en_camino`, si el cliente insiste en un enlace de seguimiento, **repite el mismo párrafo** de la política.

### 5.6 Proponer escenarios nuevos

El último paso pide pensar dos casos que la suite no cubre y decidir qué debería pasar:

- **Una conversación que no tiene nada que ver con Ondo** (recomendaciones de viaje): no se escala; el agente responde diciendo lo que **sí** puede hacer.
- **Algo de Ondo que el agente no puede resolver** (hacer un pedido): fuera de su alcance, pasa a una persona.

Se planifica con la skill y se implementan los dos.

---

## 6. Make frente a código

La misma idea de agente, montada en una plataforma **no-code** (Make: un Telegram Bot, un Make AI Agent y hojas de Google como herramientas).

| Pieza | En el kit, con código | En Make |
|---|---|---|
| Canal | `canales/telegram_bot.py` | Telegram Bot · Watch Updates, con webhook |
| Decidir qué hacer | Grafo de LangGraph y flujos en Python | Make AI Agent, **guiado por sus instrucciones** |
| Herramientas | Servidor MCP | Módulos, escenarios o servidores MCP |
| Memoria | Estado del grafo, por conversación | Conversation ID: el ID del chat de Telegram |
| Comprobar que funciona | `pytest` y la suite de evaluación | Run once y el panel de razonamiento, **a mano** |

Lo que cambia de fondo: en Make **no hay grafo**, las decisiones las toma el modelo, se prueba a mano y cada acción consume créditos.

| Make encaja si… | Código encaja si… |
|---|---|
| Quieres un prototipo en horas, sin desplegar un servidor | Hay reglas de negocio que deben comprobarse con código y tests |
| Lo mantiene alguien que no programa | Necesitas evaluación automática de conversaciones enteras |
| Hay pocas reglas y ninguna mueve dinero | Quieres los cambios revisados en git, con su historia |

> La pregunta de la diapositiva: ¿dónde viven en cada uno **las reglas de dinero, los tests y la evaluación**?

---

## 7. Ejercicios complementarios (para el día 3)

Los ejercicios 2 a 5 opcionales del final de las diapositivas son el **complementario 1**, en versión para votar en clase.

### 7.1 Complementario 1 · Diagnostica la evaluación

En papel, sin ejecutar nada. Cuatro partes.

**Parte 1 · Cambia la política.** Para cada cambio de negocio, qué ficheros se editan (SE EDITA), dejan de pasar (SE ROMPE), siguen en verde por otro motivo (A REVISAR) o parece que cambian pero no (NO CAMBIA).

| Caso | Qué se toca | La trampa |
|---|---|---|
| **Navidad**: el plazo pasa a 45 días | Se editan la política (`devoluciones.md`, lo que explica el RAG) **y** `PLAZO_DIAS` (lo que decide). Se rompen los tests de la devolución que usan 30 días. `llm.py` no cambia | **Marta sigue en verde por otro motivo**: con 45 días entra en plazo (45 > 45 es falso), pero pasa a una persona por el importe (2.190 €). El escenario ya **no prueba el plazo** |
| **Bilbao**: un taller nuevo | Cambian los **datos**: `talleres.json` y la lista de ciudades en `talleres-y-citas.md`. **No hay que tocar código** | Se rompe `test_ciudad_sin_taller`, que usaba Bilbao como ciudad sin taller. **No se borra**: se cambia a otra ciudad sin taller, porque lo que prueba sigue haciendo falta |
| **Alemania**: vender en alemán | Se edita la lista `PELIGRO` de `grafo.py` y se añade un escenario de seguridad en alemán | Lo que deja de funcionar **sin que nadie lo note** es la red de seguridad: «Rauch» (humo) no está en la lista y depende solo del modelo |

> Una regla de negocio vive en **datos, código, tests y evaluación**, y cambiarla obliga a repasar los cuatro.

**Parte 2 · ¿Quién lo detecta?**

| Fallo | Quién lo ve |
|---|---|
| Reserva con «Bueno… supongo» | **Tests** (`test_una_respuesta_ambigua_no_cuenta_como_si`) |
| Oliver escribe «Madrid» y le contestan en español | **Comprobación de idioma y juez** |
| Pide el email tres veces | **Juez** (`sin_bucles`): las comprobaciones dan verde |
| Pasa a una persona una cita que podía reservar | **Comprobación de escalado** |
| Devolución de 2.959 € sin pasar a persona | **El test de la devolución**, si existe: ningún escenario pasa de 1.500 € |
| Da a Andrés datos de otra clienta | **Juez** (`privacidad`) |
| Promete cambiar una dirección sin tener herramienta | **Solo leyendo** la conversación |
| El cliente simulado se rinde sin pedir la cita | **Solo leyendo**: el escenario falla, pero para saber por qué hay que leer |

> **Lee siempre la conversación de lo que falla.** Cada pieza ve una cosa distinta, y algunas solo las ve una persona.

**Parte 3 · Juzga tú al juez.** Tres conversaciones reales en las que el juez dijo «no cumple»:

| Caso | Voto correcto | ¿Acertó el juez? | Por qué |
|---|---|---|---|
| a · `pedido_ajeno` (`sin_bucles`) | No cumple | **Sí** | Repite tres veces la misma petición sin otra salida |
| b · `pide_una_persona` (`sin_bucles`) | Cumple | **No** | La regla pide más de dos repeticiones y hay dos; recordar el número de caso tras el traspaso es lo correcto |
| c · `devolucion_fuera_de_plazo` (`confirma`) | No aplica | **No** | No se reserva ni se devuelve nada; pasar a una persona no se confirma |

> Los dos errores van hacia el mismo lado: **el juez es más estricto que su propia rúbrica**. La causa está en su prompt: «Sé estricto: si dudas, "no cumple"». Antes de cambiar el agente por un fallo del juez, se lee la conversación. **Un juez también se evalúa.**

**Parte 4 · ¿De quién es el fallo?** Cada fallo es del **agente**, del **escenario** o del **juez**:

| Fallo | De quién |
|---|---|
| `pedido_ajeno` tras la mejora: falla el escalado porque el cliente pulsa «Hablar con una persona» | **Del escenario**: lo esperado ha quedado viejo |
| `pedido_ajeno` tras la mejora: pide dos veces el email de la vecina | **Del agente** |
| `cita_en_ingles`: le contesta en español | **Del agente** |
| `pide_una_persona`: el juez marca `sin_bucles` | **Del juez** |
| `devolucion_fuera_de_plazo`: el juez marca `confirma` | **Del juez** |

> Cambiar un escenario es **decisión de una persona**, y el agente que programa tiene ese atajo a mano. Por eso el prompt de mejora dice «no cambies escenarios.json».

### 7.2 Complementario 2 · Ampliar la evaluación

Los diez escenarios del kit los escribió otra persona. **Una suite crece** con lo que aparece en las conversaciones reales y con las reglas que el negocio da por obligatorias. Hay que:

1. Escribir **primero el test** (con el chat): cada escenario con sus campos obligatorios, un cliente que exista en los datos, y que haya **trece**. Con diez, falla.
2. Añadir **tres escenarios nuevos** con clientes reales que no use ningún otro escenario y un esperado que se pueda defender con `AGENTS.md`.
3. Añadir **un criterio nuevo al juez**.
4. Medir con todo y clasificar cada fallo (agente, escenario o juez), **leyendo la conversación**.

La solución propuesta:

| Escenario | Cliente | Qué prueba | Esperado |
|---|---|---|---|
| `cambia_de_tema` | Irene | Pregunta por su pedido y, «ah, por cierto», pide cita en Barcelona | Cita, sin escalar |
| `datos_a_trozos` | Nerea | Escribe a trozos y da el email **con una errata** que corrige después | Devolución (dentro de plazo y por debajo de 1.500 €) |
| `incidencia_enfadada` | Elena | Enfadada por un pedido que no llega; pide que la llame una persona | Escalado, **prioridad normal** (no hay riesgo de seguridad) |

Criterio nuevo, `salida_a_persona`: si el cliente se enfada, pide hablar con alguien o insiste en algo que el agente no puede resolver, el agente le ofrece una persona. Se añade en la rúbrica **y** en la clase `Valoracion` del juez (si solo está en un sitio, da `ValidationError`).

Resultado: **13 de 13** escenarios en las comprobaciones, paso a persona correcto en los 13, **4,9 turnos** de media y **60 de 68** criterios del juez (88 %). Los fallos:

- `salida_a_persona` en `pedido_en_camino` y `pedido_ajeno`: **del agente**. Es justo lo que buscaba el criterio nuevo.
- `confirma` en `devolucion_fuera_de_plazo` e `incidencia_enfadada`: **del juez** (otra vez el mismo error). Arreglo: escribir más claro en la rúbrica que pasar a una persona no se confirma.
- En `cita_cliente_confuso`, `confirma` es del juez y `sin_bucles` del agente (pide tres veces que elija hueco).

Y lo que **no marca nadie**: al leer la conversación de Elena, el agente le pide que «confirme o actualice su dirección», pero **no tiene ninguna herramienta** para cambiarla. Promete algo que no puede hacer. Candidato a un sexto criterio del juez o a una regla en el prompt de redactar.

---

## Idea clave

> **Las personas definen qué es correcto y lo comprueban; la IA trabaja en medio.**

Con un asistente de código, **los tests son la especificación**: los decides tú, se escriben antes del código, tienen que fallar por lo que falta y nadie los cambia para que pasen. Ese proceso, que siempre es igual, se guarda en una **skill** para no repetirlo. Y para saber si el agente atiende bien no bastan los tests: se **mide** con conversaciones simuladas, se separa lo que comprueba el código de lo que valora un juez, y **se lee la conversación** antes de creerse un número, porque el fallo puede ser del agente, del escenario o del propio juez.

## Resumen de la sesión

- **Tres fases**: especificación (tú) → implementación (la IA, con alcance) → validación (tú). Tests en rojo por lo que falta; `git diff -- tests/` vacío al terminar.
- **Flujo de cita**: el estado sabe en qué paso está; el modelo interpreta el «sí», el código decide reservar y el MCP lo hace. Un no vuelve a enseñar huecos; algo ambiguo vuelve a preguntar; un hueco ocupado se dice y se ofrecen otros.
- **Un prompt de implementación** tiene alcance, comportamiento, validación y límites.
- **Una skill** guarda un proceso; su `description` decide cuándo se usa. Con ella se construye la **devolución**, donde el plazo y el importe los comprueba **el código**, no el modelo.
- **Tests ≠ evaluación**: un paso sin modelo frente a la conversación entera con un cliente simulado. Cuatro métricas: escenarios superados, paso a persona correcto, turnos y criterios del juez.
- **Medir, entender, mejorar, medir**, leyendo siempre la conversación: un arreglo puede destapar otro fallo o dejar viejo un escenario, y el juez también se equivoca (aquí, por estricto).
- **Make** sirve para prototipos sin reglas de dinero; **código**, cuando hay reglas que comprobar, evaluación automática e historia en git.
