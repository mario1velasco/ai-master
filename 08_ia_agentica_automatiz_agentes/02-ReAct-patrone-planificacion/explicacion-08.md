# Sesión 2: Razonar y actuar, ReAct y patrones de planificación

Explicación sencilla de la sesión 2 del Tema 8, centrada en las ideas principales. Se construye a partir del PDF de la sesión (`Tema8_Sesion2_ReAct_y_planificacion.pdf`), de las capturas de clase, del resumen de la clase (`Resumen Clase 2-7 Tema 8.pdf`), del código de `../tema8-agentes/sesion2/` y de la solución de los deberes (`Solución deberes sesión 2/`). Los ejemplos propios van marcados como *ilustrativos*.

---

## 0. Dónde estamos

| Sesión | Bloque | Qué se añade |
|---|---|---|
| 1 | Agente | Un agente desde cero |
| **2** | **Planificar** | **ReAct y patrones de planificación (esta sesión)** |
| 3 | Herramientas | LangGraph, APIs externas y MCP |
| 4 | Memoria | Contexto, memoria y estado |
| 5 | Equipos | Sistemas multiagente |
| 6 | Producción | Integración en la empresa |

En la sesión 1 construimos el bucle del agente: el modelo pide una herramienta, el código la ejecuta, le devuelve el resultado, y así hasta que responde. Esta sesión mira **cómo razona y se organiza** ese agente:

1. **¿Quién escribe la llamada a la herramienta?** ¿El modelo en texto libre (ReAct) o la API en un formato fijo (tool calling)?
2. **¿Conviene hacer un plan antes de actuar?** (plan-and-execute).
3. **¿Cómo se revisa lo que ha hecho?** (reflexión).

La frase con la que se resume la clase:

> No basta con que un agente sea capaz de razonar: también hay que **estructurar sus acciones, controlar su ejecución y verificar sus resultados**.

### Los ficheros de la práctica (`../tema8-agentes/sesion2/`)

| Fichero | Qué hace, en una frase |
|---|---|
| `react_prompting.py` | **Demo 1: un agente «a la antigua».** El modelo escribe en texto «Pensamiento / Acción / Entrada» y nuestro código lo lee para ejecutar la herramienta |
| `plan_and_execute.py` | **Demo 2: primero el plan, luego la acción.** Un planificador hace la lista de pasos, el agente de la sesión 1 resuelve cada uno y al final se redacta la respuesta |
| `reflexion.py` | **Demo 3: un revisor.** El agente escribe un borrador, un crítico lo revisa con unos criterios y, si no lo aprueba, se rehace |
| `comparar_estrategias.py` | **La misma pregunta con las cuatro estrategias** (tool calling, ReAct, plan-and-execute y reflexión), midiendo llamadas, tokens y tiempo |

Todas reutilizan el agente de la sesión 1 (`sesion1/agente_minimo.py`) y las herramientas de `comun/`.

**Cómo ejecutarlas** (siempre desde `tema8-agentes/`, con el entorno activado):

```bash
python -m sesion2.react_prompting "Soy marta.lopez@email.com, ¿puedo repetir mi último pedido?"
python -m sesion2.plan_and_execute "Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?"
python -m sesion2.reflexion "Quiero comprar 10 protectores solares, ¿me los enviáis?"
python -m sesion2.comparar_estrategias
```

**Los datos que importan en esta sesión** (de `comun/tienda.py`): Marta tiene dos pedidos, `ORD-10231` (el antiguo: un sérum de vitamina C) y `ORD-10544` (el último: crema hidratante + contorno de ojos). La **crema hidratante tiene 0 unidades** y el **protector solar SPF50 tiene 8**. Casi todas las demos giran alrededor de estos dos detalles.

---

## 1. Corrección de los deberes de la sesión 1

### 1.1 Nivel base: una herramienta más

**El deber:** añadir al agente la herramienta `consultar_pedido`.

```python
CONSULTAR_PEDIDO = {"type": "function", "function": {
  "name": "consultar_pedido",
  "description": "Devuelve estado, productos, importe y seguimiento de un pedido. "
                 "Úsala cuando el cliente pregunte por un pedido concreto.",
  "parameters": {... "id_pedido": formato ORD-12345}}}

HERRAMIENTAS += [CONSULTAR_PEDIDO]
FUNCIONES["consultar_pedido"] = tienda.obtener_pedido
```

Las tres ideas de la diapositiva:

1. **El esquema es lo que lee el modelo: la descripción dice cuándo usarla.** El modelo no ve el código de la función; solo ve el nombre, la descripción y los parámetros.
2. **El formato del parámetro evita llamadas erróneas.** Decir «formato ORD-12345» evita que el modelo pase `10544` o «pedido 10544».
3. **El bucle no cambia: añadir capacidades es añadir herramientas.** Una línea para lo que ve el modelo (`HERRAMIENTAS`) y otra para lo que ejecuta el código (`FUNCIONES`).

### 1.2 Reto: detectar bucles sin tocar el bucle

**El deber:** si una herramienta se llama más de dos veces con los mismos datos, el agente debe dejar de intentarlo y explicar al cliente qué pasa.

```python
def con_deteccion_de_bucles(funciones, max_rep=2):
    llamadas = Counter()

    def vigilada(**args):
        llamadas[(nombre, args)] += 1
        if llamadas[(nombre, args)] > max_rep:
            return {"error": "No lo intentes de nuevo: explica al cliente qué pasa"}
        return funcion(**args)
```

(Versión resumida de la diapositiva.)

Las tres ideas:

1. **Se envuelve cada herramienta en vez de reescribir el agente.** Cada función se «vigila» por fuera: cuenta cuántas veces la llaman y, si se pasa, no la ejecuta. El agente no se toca.
2. **Se cuentan las llamadas idénticas**: misma herramienta con los mismos datos.
3. **El error le dice al modelo qué hacer a continuación.** No solo corta: le da una instrucción («explica al cliente qué pasa»).

**Una lección sobre mi solución** (`sesion1/agente_minimo.py`). Yo puse el contador dentro del agente, como una variable **global** que no se reinicia nunca. Eso dio un fallo raro en la demo `comparar_estrategias` (sección 6.3): como las cuatro estrategias se ejecutan seguidas en el mismo programa, las llamadas a `buscar_cliente` de las primeras estrategias contaban para la última, y a la tercera vez se bloqueaba aunque todo hubiera ido bien. La solución de clase no tiene ese problema porque crea un contador nuevo cada vez. **Para arreglar la mía:** reiniciar el contador al empezar cada conversación y contar solo las llamadas que fallan.

---

## 2. De ReAct al tool calling

### 2.1 Razonar, actuar o las dos cosas

ReAct (Yao et al., 2022) juntó dos formas de trabajar que fallaban por lados opuestos:

| Enfoque | Qué hace | Por qué falla |
|---|---|---|
| **Solo razonar** (*Chain-of-Thought*) | Piensa paso a paso | No consulta nada: **se inventa los datos** |
| **Solo actuar** | Llama a herramientas | Sin un plan: **se pierde en tareas largas** |
| **ReAct** | **Intercala pensar, actuar y observar** hasta resolver la tarea | Junta lo mejor de los dos |

*Chain-of-Thought* («cadena de pensamiento») es pedirle al modelo que razone paso a paso. Razona mejor, pero todo sale de su memoria: si le preguntas por el pedido de Marta, se inventa el estado. ReAct le añade lo que le faltaba: **consultar el mundo real** entre pensamiento y pensamiento.

### 2.2 El formato ReAct

Así es la «traza» (el registro) de un agente ReAct:

```
Pensamiento: necesito los pedidos de Marta
Acción: buscar_cliente
Entrada: {"email": "marta.lopez@email.com"}
Observación: {"pedidos": ["ORD-10231", "ORD-10544"]}

Pensamiento: el último es ORD-10544
Acción: consultar_pedido
Entrada: {"id_pedido": "ORD-10544"}
Observación: {"estado": "en tránsito", ...}

Respuesta final: tu pedido está en camino
```

Las cuatro ideas de la diapositiva:

1. **El modelo escribe texto con un formato fijo** (Pensamiento / Acción / Entrada).
2. **Nuestro código lee «Acción» y «Entrada» y ejecuta** la herramienta.
3. **La «Observación» la escribe el código, nunca el modelo.** Si la escribiera el modelo, se la inventaría.
4. **Termina con «Respuesta final».**

### 2.3 Hoy: tool calling nativo

**El mismo ciclo, pero estructurado por la API:**

```
Usuario  ──►  Modelo  ──►  Código  ──►  Modelo
«¿Cómo va     devuelve     ejecuta y    responde o pide
mi pedido?»   una llamada  devuelve el  otra herramienta
              estructurada resultado
```

Es lo que hacía el agente de la sesión 1. En vez de escribir «Acción: … Entrada: …» en texto, el modelo devuelve la llamada en un formato fijo (nombre de la herramienta + datos en JSON) que la API garantiza. Nadie tiene que «leer» texto libre.

> **El antiguo «Pensamiento» es hoy el razonamiento interno del modelo.**

Ya no hace falta pedirle que escriba «Pensamiento:»: los modelos actuales razonan por dentro y entregan directamente la llamada.

**La idea para llevarse:** ReAct y tool calling son **el mismo bucle** (pensar → actuar → observar). Lo único que cambia es **quién da forma a la llamada a la herramienta**: nuestro código leyendo texto, o la API.

---

## 3. Demo: ReAct a mano

### 3.1 En directo: ReAct prompting

```bash
python -m sesion2.react_prompting "Soy marta.lopez@email.com, ¿puedo repetir mi último pedido?"
```

Es ReAct escrito a mano, como se hacían los agentes antes del tool calling (y como se siguen haciendo con modelos que no lo soportan).

**Qué observar**, según la diapositiva:

- **El prompt contiene todo el «agente».** Las herramientas no se le pasan a la API: se le describen al modelo **en el texto de las instrucciones**, junto con el formato que debe seguir. Si borras el prompt, no queda agente.
- **Cada Pensamiento → Acción → Observación.** En la salida se ve un bloque por vuelta del bucle (`--- Paso N ---`).
- **`stop=["Observación:"]` corta al modelo.** Le dice a la API: «en cuanto el modelo vaya a escribir "Observación:", páralo». Así el modelo no puede inventarse el resultado de la herramienta; lo pone el código.

### 3.2 El parser: la pieza frágil

```python
texto = llm(mensajes, stop=["Observación:"])

if final := PATRON_FINAL.search(texto):
    return final.group(1)

if accion := PATRON_ACCION.search(texto):
    nombre, args = accion.groups()
    resultado = FUNCIONES[nombre](**json.loads(args))
else:
    resultado = "formato incorrecto"
```

Leído en castellano: *pide texto al modelo y córtalo antes de la observación. Si pone «Respuesta final», hemos terminado. Si pone «Acción» y «Entrada», ejecuta esa herramienta. Si no pone ni una cosa ni otra, dile que el formato es incorrecto.*

Un **parser** es el trozo de código que «lee» el texto del modelo y saca de él la herramienta y los datos. Aquí lo hace con **expresiones regulares** (patrones de búsqueda de texto).

Las tres ideas de la diapositiva:

1. **`stop` evita que el modelo escriba la observación.**
2. **Expresiones regulares para leer el texto.**
3. **Si no respeta el formato, se lo decimos y reintenta.**

**Por qué es frágil:** todo depende de que el modelo escriba **exactamente** lo esperado. *Ilustrativo:* basta con que escriba «Accion» sin tilde, ponga el JSON en varias líneas o escriba «Respuesta Final» con mayúscula para que el parser no lo entienda. Con tool calling nativo este problema desaparece.

**Aunque haya tool calling, hay que validar** (del resumen de la clase). La estructura reduce errores, pero no los elimina: el desarrollador sigue siendo responsable de comprobar que lo que devuelve el modelo tiene el formato esperado, validar los datos y reintentar si no. En el código del tema lo hace `extraer_json` (`comun/utilidades.py`): busca el JSON dentro del texto del modelo, porque «los modelos a veces añaden texto alrededor».

### 3.3 ReAct a mano frente a nativo

| ReAct prompting | Tool calling nativo |
|---|---|
| Funciona con cualquier modelo | Estructura garantizada por la API |
| Razonamiento visible | Llamadas en paralelo |
| Parser frágil | Necesita soporte del modelo |
| Más tokens por paso | Es el estándar actual |

Qué significa cada punto:

- **Cualquier modelo / necesita soporte.** ReAct solo necesita un modelo que siga instrucciones. El tool calling necesita un modelo y una API que lo admitan. (`comprobar_entorno.py` comprueba precisamente si tu modelo lo soporta.)
- **Razonamiento visible.** En ReAct el «Pensamiento» queda escrito y se puede leer para entender qué hizo el agente. En nativo es interno.
- **Parser frágil / estructura garantizada.** Lo de la sección 3.2.
- **Más tokens por paso.** En ReAct, las descripciones de las herramientas y las reglas del formato van en el texto, y además el modelo escribe su pensamiento en cada vuelta.
- **Llamadas en paralelo.** Con tool calling el modelo puede pedir varias herramientas a la vez (por ejemplo, el stock de dos productos). ReAct hace una por vuelta.
- **Es el estándar actual.** Por eso el resto del tema usa tool calling. ReAct a mano sirve para entender qué hace la API por dentro.

---

## 4. Actividad: tu plan o el suyo

**Tarea:** «Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?» ¿Qué pasos daríais?

1. Proponed los pasos en voz alta (**máximo 5**).
2. ¿Qué herramienta usa cada paso?
3. ¿Qué podría fallar en cada uno?
4. Ahora comparamos con el plan que genera el agente.

La idea es hacer a mano lo que luego hará el planificador (sección 5.1) y comparar.

**Una posible respuesta** (*ilustrativa*), con los datos reales de la tienda:

| # | Paso | Herramienta | Qué podría fallar |
|---|---|---|---|
| 1 | Buscar a Marta y sus pedidos | `buscar_cliente` | Email mal escrito |
| 2 | Ver cuál es el último | *(ninguna: pensar)* | Coger el que no es. La lista va del más antiguo al más reciente, así que el último es `ORD-10544` |
| 3 | Ver qué productos tenía | `consultar_pedido` | Pasar el número con otro formato |
| 4 | Comprobar el stock de cada producto | `consultar_stock` (dos veces) | Escribir el nombre del producto distinto al del catálogo |
| 5 | Responder a Marta | *(ninguna: redactar)* | Decir «sí» sin haber mirado el stock |

**Resultado:** no se puede repetir el pedido completo, porque la **crema hidratante no tiene stock**. Se puede ofrecer el contorno de ojos solo (quedan 47).

Dos detalles que salen de la actividad:
- **«Último» es una trampa.** Una persona sabe que «último» es «el más reciente». El agente solo lo sabe si se lo dice la descripción de la herramienta (`buscar_cliente`: «del más antiguo al más reciente»). Es la lección del deber base: **la descripción es lo que lee el modelo**.
- **Un paso no es una llamada.** El paso 4 son dos llamadas, y los pasos 2 y 5 no usan ninguna herramienta.

---

## 5. Planificar y reflexionar

### 5.1 Plan-and-execute

```
Tarea ──► Planificador ──pasos──► Ejecutor ──resultados──► Sintetizador ──► Cliente
          (1 llamada)            (un agente por paso)      (respuesta final)
```

El trabajo se reparte en **tres papeles**:

1. **Planificador:** con una sola llamada al modelo, convierte la tarea en una lista de pasos (máximo 5).
2. **Ejecutor:** resuelve cada paso, uno detrás de otro, con el agente de la sesión 1. Cada paso recibe los resultados de los anteriores.
3. **Sintetizador:** con todos los resultados, redacta la respuesta para el cliente.

**Ventajas y límites**, según la diapositiva:

- **El plan es visible antes de ejecutar.** La demo imprime «📋 Plan:» antes de hacer nada.
- **Un humano puede aprobarlo.** Como el plan existe antes de actuar, alguien puede revisarlo (sección 8).
- **Pasos simples con un modelo barato.** Cada paso es una tarea pequeña, así que podría hacerla un modelo más pequeño y barato que el planificador. (En la demo todos usan el mismo modelo: es una posibilidad, no algo que haga el código.)
- **Rígido si algo falla a mitad.** Los pasos se ejecutan en orden sin mirar si han salido bien. Si el transportista no responde, el plan sigue como si nada. Es el reto de los deberes (sección 9.2).

**El precio:** más llamadas. Una para planificar, al menos una por paso y una para redactar. Con 4 pasos, mínimo 6 llamadas, frente a las 2-4 del agente solo.

### 5.2 Reflexión: un crítico con criterios

```
Borrador ──► Crítica ──► Corrección ──► Respuesta
el agente    un revisor   si no aprueba,  máximo
responde     evalúa con   el agente       2 rondas
             criterios    rehace con los
             explícitos   comentarios
```

Es como pasarle un borrador a un compañero para que lo revise antes de enviarlo. Los criterios del crítico (`reflexion.py`):

- Responde a todo lo que pregunta el cliente.
- Si un producto no tiene stock suficiente, lo dice claramente y ofrece una alternativa.
- No promete plazos, descuentos ni acciones que no puede garantizar.
- Es breve (máximo 5 frases) y amable.

**«Máximo 2 rondas»** es otra vez un límite puesto por el código: sin él, un crítico muy exigente podría rechazar respuestas para siempre.

> **Funciona mejor con señales objetivas: tests, datos, reglas.**

Esta frase de la diapositiva es la clave. Si el crítico es el mismo modelo «opinando», se equivoca igual que el autor. Funciona cuando puede **comprobar algo concreto**: un dato real (hay 8 protectores, no 10), unos tests que pasan o no, una regla fija (máximo 5 frases). Lo veremos fallar en la sección 6 justo por esto.

### 5.3 ¿Y los modelos de razonamiento?

Los modelos de razonamiento «piensan» por dentro antes de responder. ¿Siguen haciendo falta los planes?

| Ya planifican por dentro | El plan explícito sigue aportando |
|---|---|
| Descomponen la tarea internamente | Cuando hay que **auditar** |
| Menos necesidad de plan explícito | Cuando un **humano aprueba** el plan |
| Más tokens y latencia por llamada | En **tareas muy largas** |
| | Para usar **modelos baratos en cada paso** |

El modelo de razonamiento hace por dentro lo que el planificador hace por fuera, pero **ese plan interno no se ve ni se puede aprobar**. Un plan escrito sigue sirviendo cuando hay que revisarlo, guardarlo o repartirlo entre modelos más baratos. Es la misma idea de la sección 2.3 («el antiguo Pensamiento es hoy el razonamiento interno»), aplicada a los planes.

### 5.4 Controlar la ejecución

Cuatro controles, todos puestos **por el código**, no por el modelo:

| Control | Qué es | En el código del tema |
|---|---|---|
| **Límite de iteraciones** | Red de seguridad que pone **siempre** el código | Máximo de pasos en el agente de la sesión 1 y en ReAct; máximo de rondas en la reflexión |
| **Límite de presupuesto** | Tokens o euros máximos por tarea | No está implementado: el agente cuenta los tokens, pero no corta al pasar un tope |
| **Detección de bucles** | Llamadas repetidas con los mismos datos | El reto de la sesión 1 (sección 1.2) |
| **Escalado a humano** | Cuando no puede completar la tarea, lo dice y deriva | Al agotar los pasos, el agente responde «Te paso con un compañero del equipo» |

Un agente puede quedarse repitiendo una acción si no encuentra un cliente, recibe datos raros o una herramienta falla siempre (en Lumen Shop, `consultar_transportista`). La idea de la clase: **este control se pone en el código**, sin esperar a que el modelo se dé cuenta solo.

### 5.5 Otra idea de la clase: dividir el agente

Del resumen de la clase: si un agente tiene **demasiadas herramientas**, se puede dividir en **agentes especializados** (uno de pedidos, otro de reembolsos…) con un **agente enrutador** delante que manda cada petición al especialista adecuado. Cada uno lleva menos herramientas en su contexto, así que es más barato y se equivoca menos. Se verá en la sesión 5 (multiagente).

---

## 6. Demo: plan y reflexión

### 6.1 En directo: plan-and-execute y reflexión

```bash
python -m sesion2.plan_and_execute "Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?"
python -m sesion2.reflexion "Quiero comprar 10 protectores solares, ¿me los enviáis?"
```

**Qué observar**, según la diapositiva:

- **El plan aparece antes de ejecutar nada.** Primero «📋 Plan:» con los pasos, y después «▶ Paso 1», «▶ Paso 2»…
- **Cada paso recibe los resultados anteriores.** Así el paso 2 sabe qué pedido encontró el paso 1.
- **El crítico pilla respuestas que prometen 10 si hay 8.** La pregunta de la reflexión está pensada para eso: solo quedan 8 protectores solares. Si el borrador promete 10, el criterio del stock lo rechaza.

### 6.2 Lo que salió en mi máquina

Ejecutado el 27-10-2026 con `qwen3:4b-instruct` (en clase, `qwen2.5:7b`). Con modelos pequeños cada ejecución sale distinta: esto es **una** ejecución, no «el» resultado.

**Plan-and-execute.** El plan fue:

```
📋 Plan:
  1. buscar_cliente
  2. consultar_pedido
  3. consultar_stock
  4. verificar_disponibilidad
  5. confirmar_repetición
```

- Los tres primeros coinciden con el plan humano de la sección 4. Pero los dos últimos **son herramientas que no existen**: el planificador se las inventó. No rompió nada (cada paso lo resuelve el agente con las herramientas reales), pero fueron dos pasos de más.
- Los primeros pasos ya le decían al cliente «está todo listo para repetirlo»… **antes de mirar el stock**.
- El paso 3 encontró el problema (la crema hidratante sin stock) y la **respuesta final fue correcta**. Le faltó ofrecer el contorno de ojos solo.

**Reflexión: el crítico no pilló nada.**

- El agente buscó «protección solar», un nombre que no está en el catálogo, y respondió que no había ese producto pero que «sí tenemos protector solar SPF50»: **le ofreció como alternativa lo mismo que había pedido**. Nunca llegó a ver las 8 unidades.
- El crítico lo **aprobó**: «indica falta de stock, ofrece una alternativa y es breve y amable».
- **Por qué:** el crítico solo ve la pregunta y la respuesta, **no los datos**. Comprueba que la respuesta *tenga la forma* correcta, pero no si es *verdad*. Es la frase de la sección 5.2 al revés: sin señales objetivas, la reflexión aprueba respuestas equivocadas.

**ReAct a mano.** Buscó a Marta, consultó `ORD-10544` y dijo «ya tengo toda la información necesaria»… **sin consultar el stock**. Respondió que se podía repetir. El formato ReAct salió perfecto, pero el razonamiento se cerró antes de tiempo. Es justo lo que intenta evitar un plan explícito.

### 6.3 En directo: cuatro estrategias, una tarea

```bash
python -m sesion2.comparar_estrategias
```

Hace la misma pregunta («Soy marta.lopez@email.com. Quiero repetir exactamente mi último pedido. ¿Tenéis stock de todo lo que pedí?») con las cuatro estrategias y mide cada una.

**Qué observar**, según la diapositiva:

- **Llamadas al modelo** de cada estrategia.
- **Tokens y tiempo.**
- **Calidad de la respuesta.** Las métricas no dicen si la respuesta es correcta: hay que leerla.
- **Ejecutadlo dos veces: los resultados varían.**

**Lo que salió en clase:**

| Estrategia | Llamadas | Tokens | Tiempo | ¿Qué respondió? |
|---|---|---|---|---|
| Tool calling nativo | 2 | 1018 | 7,6 s | Encontró el pedido bueno, pero **no miró el stock** («un momento, por favor») y se **inventó una fecha** («16 de marzo») |
| ReAct prompting | 3 | 1329 | 12,3 s | **Pidió el email**, que ya venía en la pregunta |
| Plan-and-execute | 6 | 2572 | 21,8 s | Dijo que **no encontraba el pedido** (que sí existe) |
| Con reflexión | 10 | 7363 | 107,1 s | **Cogió el pedido equivocado** (el antiguo) y dijo «podemos repetirlo sin problemas». Y el crítico **lo aprobó** |

**Ninguna acertó.** Lo correcto era decir que la crema hidratante no tiene stock.

**En mi máquina** (dos ejecuciones, `qwen3:4b-instruct`), al revés: tool calling, ReAct y plan-and-execute **acertaron**, y plan-and-execute fue el más completo, pero a cambio de unas 2,5 veces más tokens y 3-4 veces más tiempo que el tool calling. La reflexión falló, pero por el fallo de mi solución del reto de la sesión 1 (sección 1.2): el contador bloqueó `buscar_cliente` y el agente respondió que «el servicio de clientes no está disponible».

**Las lecciones:**

- **Las métricas no dicen nada de la calidad.** La estrategia más barata y la más cara fallaron las dos en clase. Hay que **leer cada respuesta y compararla con los datos**.
- **Más complejo no es mejor.** La reflexión fue la más cara (10 llamadas, 107 segundos) y dio una respuesta segura de sí misma y equivocada.
- **Los resultados varían**: mismo código, distinta ejecución (o distinto modelo), distintos aciertos. Por eso hay que probar varias veces.

---

## 7. Actividad: elige la estrategia

**¿Qué estrategia usarías?** Tool calling directo, plan-and-execute o reflexión. Justificadlo.

El PDF no trae la respuesta. Una propuesta (*ilustrativa*):

| Caso | Estrategia | Por qué |
|---|---|---|
| 1. Responder «¿tenéis stock de X?» | **Tool calling directo** | Una herramienta, una respuesta. Cualquier otra cosa es pagar más por lo mismo |
| 2. Preparar el informe mensual de incidencias | **Plan-and-execute** | Tarea larga con pasos claros (recoger datos, agrupar, resumir). El plan se puede revisar y cada paso puede hacerlo un modelo barato |
| 3. Redactar la respuesta a una reclamación delicada | **Reflexión** | El tono y lo que se promete importan mucho. Un crítico con criterios claros («no prometer lo que no se puede garantizar») ayuda. Y probablemente, que la revise una persona |
| 4. Migrar 500 fichas de producto al nuevo formato | **Plan-and-execute** (o ni siquiera un agente) | Es lo mismo 500 veces. Mejor un plan que se aprueba una vez y se repite. La reflexión sirve si hay una señal objetiva: que la ficha cumpla el formato nuevo |
| 5. Un agente que hace compras a proveedores | **Plan-and-execute con aprobación humana** | Gasta dinero: el plan («comprar X unidades a Y por Z €») tiene que verlo una persona antes de ejecutarse (sección 8) |
| 6. Responder dudas en un chat de la web | **Tool calling directo** | El cliente espera respuesta rápida. Un plan o un crítico añadirían segundos y coste a cada mensaje |

La pregunta que guía: **¿cuánto vale acertar frente a lo que cuesta (en tiempo y dinero) cada estrategia?** Lo simple primero; lo complejo solo cuando el caso lo justifica.

---

## 8. Caso real: aprobar el plan

**El «modo plan» de los asistentes de programación** (Claude Code, Cursor y otros). Funciona en cuatro pasos:

| Paso | Qué pasa |
|---|---|
| **Petición** | «Añade pagos con tarjeta a la app» |
| **Plan** | El agente explora el código y **propone los pasos sin tocar nada** |
| **Aprobación** | El desarrollador revisa, corrige o aprueba el plan |
| **Ejecución** | Solo entonces el agente modifica archivos |

> **El mismo patrón sirve para cualquier proceso con acciones costosas.**

Es plan-and-execute (sección 5.1) con una persona en medio. Corregir un plan es barato; deshacer veinte archivos cambiados mal, no. *Ilustrativo:* en Lumen Shop, el agente de compras a proveedores de la actividad anterior propondría «pedir 200 cremas hidratantes al proveedor A» y un responsable lo aprobaría antes de enviar el pedido.

### Idea clave

> **Planificar no es un truco de *prompt*, es un punto de control.**
> El plan explícito es el mejor sitio para que un humano revise antes de que el agente actúe.

---

## 9. Deberes para la sesión 3

**No son evaluables**: se comentan al inicio de la sesión 3. La solución está en `Solución deberes sesión 2/soluciones/sesion2/`.

### 9.1 Nivel base · Añade reflexión al plan-and-execute

**El enunciado:** antes de devolver la respuesta final del plan-and-execute, que el crítico de `reflexion.py` la revise. Si no la aprueba, se vuelve a redactar con sus comentarios. Puedes reutilizar `planificar`, `ejecutar_paso`, `sintetizar` y `criticar`.

**La solución** (`deber_base.py`):

```python
resultados = [ejecutar_paso(...) for paso in plan]
respuesta = sintetizar(tarea, resultados)

for _ in range(max_rondas):
    revision = criticar(tarea, respuesta)
    if revision["aprobado"]:
        break
    respuesta = sintetizar(tarea, resultados,
        indicaciones=revision["comentarios"])
```

Leído en castellano: *haz el plan y ejecuta los pasos como siempre. Redacta la respuesta. Pásasela al crítico; si la aprueba, listo. Si no, vuelve a redactarla con los mismos resultados y sus comentarios. Como mucho, dos veces.*

Las tres ideas (diapositiva de corrección en la sesión 3):

1. **Se reutilizan las piezas de las demos sin tocarlas.** Solo se escribe el «pegamento».
2. **El crítico revisa solo la respuesta final**, la que va a leer el cliente.
3. **Si la rechaza, solo se vuelve a redactar.** No se repiten las consultas a las herramientas: se reescribe con los mismos datos. Es barato.

**El límite de la solución** (lo que pasó en clase, ver `../03-tools/explicacion-08.md`, sección 1.1): volver a redactar con los mismos datos arregla la *forma* de la respuesta, pero si **falta un dato** (por ejemplo, el stock), el crítico no puede sacarlo de la nada, porque no ve los datos. Es la misma lección de la sección 6.2.

### 9.2 Reto · Replanificación ante fallos

**El enunciado:** si un paso falla (el transportista no responde), el plan sigue como si nada. Añade un **verificador** por paso y, si falla, pide **un plan nuevo para lo que queda**. **Limita las replanificaciones.** Prueba: «¿Dónde está el último pedido de marta.lopez@email.com?».

```
Plan ──► Ejecutar ──► Verificar ──► Replanificar
```

**La solución** (`deber_reto.py`):

- **El verificador** es otra llamada al modelo: le pasa el paso y su resultado y le pregunta «¿esto completa el paso?». Responde sí o no, y por qué.
- **Si no se ha completado**, el planificador recibe lo que ya se ha hecho y el motivo del fallo, con esta orden: «Propón los pasos que quedan, buscando una alternativa al paso fallido. **Si no hay alternativa, el último paso debe ser informar al cliente del problema.**»
- **Como mucho 2 replanificaciones.** La diapositiva lo avisa: **el plan también puede entrar en bucle**. Si el transportista falla siempre, sin límite se pedirían planes nuevos para siempre.

**La idea:** es la reflexión, pero **un paso antes**. El crítico revisa la respuesta final; el verificador revisa **cada paso** mientras se ejecuta y, si algo falla, cambia el plan en vez de seguir adelante. Y si no hay forma de conseguir el dato, **se le dice al cliente** en vez de inventárselo.

### 9.3 Lectura: el paper de ReAct

*ReAct: Synergizing Reasoning and Acting in Language Models* (Yao et al., 2022): https://arxiv.org/abs/2210.03629. Basta con la introducción y los ejemplos de trazas. Se comenta en la sesión 3 (`../03-tools/explicacion-08.md`, sección 6).

---

## Resumen de la sesión

- **ReAct** intercala pensar, actuar y observar. Antes se hacía con texto y un parser frágil; hoy, con **tool calling**, la API da forma a la llamada. **Es el mismo bucle**; cambia quién estructura la llamada.
- **Plan-and-execute:** planificar → ejecutar cada paso → redactar. El plan se puede ver y aprobar antes de actuar, pero es rígido si algo falla y cuesta más llamadas.
- **Reflexión:** un crítico revisa el borrador. Solo funciona con **señales objetivas**; si solo ve la respuesta y no los datos, aprueba respuestas equivocadas.
- **Controles en el código:** límite de pasos (siempre), presupuesto, detección de bucles y escalado a una persona.
- **Más complejo no es mejor.** En la comparativa de clase, ninguna estrategia acertó, y la más cara fue la que más se equivocó. Hay que **leer las respuestas** y repetir las pruebas, porque los resultados varían.
- **Planificar es un punto de control**: el mejor sitio para que una persona revise antes de que el agente actúe.
