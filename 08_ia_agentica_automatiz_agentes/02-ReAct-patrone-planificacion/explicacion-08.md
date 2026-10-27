# Explicación completa — Sesión 2: Razonar y actuar, ReAct y patrones de planificación

Este documento explica el contenido de la sesión 2 del Tema 8 con un lenguaje sencillo, paso a paso, y sin dar nada por sabido. Fuentes:

- `Resumen Clase 2-7 Tema 8.pdf` (en esta carpeta): resumen de la clase generado con IA por EBIS.
- Capturas de las diapositivas de la clase (`Tema8_Sesion2_ReAct...pdf`, 33 diapositivas, que la profesora proyecta pero que no está en el repo), que se van añadiendo a este documento.
- El código real de `../tema8-agentes/sesion2/` y `../tema8-agentes/comun/`.
- `../Tema8_Deberes_y_lecturas.pdf` (deberes y lecturas).

Todo lo que se afirma viene de esas fuentes. Cuando se usa un ejemplo propio para aclarar algo, se marca como **ilustrativo**.

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

### Agenda de la sesión

Según la diapositiva «Agenda de la sesión» (clase de 18:30 a 21:00):

| Hora | Bloque | En este documento |
|---|---|---|
| 18:30–18:40 | Repaso de los deberes | Sección 1 |
| 18:40–18:55 | De ReAct al tool calling | Sección 2 |
| 18:55–19:25 | Demo: ReAct a mano | Sección 3 |
| 19:25–19:40 | Actividad: tu plan o el suyo | Sección 7.0 |
| 19:40–19:55 | Planificar y reflexionar | Secciones 7 y 8 |
| 19:55–20:25 | Demo: plan y reflexión | Final de la sección 8 y sección 9 |
| 20:25–20:35 | Actividad: elige la estrategia | Sección 9 (enunciado pendiente de capturas) |
| 20:35–20:50 | Caso real: aprobar el plan | *pendiente de capturas* (relacionada con la sección 10) |
| 20:50–21:00 | Cierre: deberes | Sección 11 |

Las secciones 4, 5 y 6 salen del resumen de la clase y no tienen bloque propio en la agenda: aparecen dentro de los bloques anteriores.

### De dónde venimos

En la sesión 1 se construyó el bucle agéntico (`sesion1/agente_minimo.py`): el modelo pide herramientas, el código las ejecuta y le devuelve el resultado, hasta que el modelo responde. La sesión 2 parte de ese mismo bucle y se pregunta **cómo razona y se organiza el agente**: ¿quién estructura la llamada a la herramienta?, ¿conviene planificar antes de actuar?, ¿cómo se revisa lo que ha hecho?

La idea con la que el resumen de la clase cierra su *abstract*:

> No basta con que un agente sea capaz de razonar: también hay que **estructurar sus acciones, controlar su ejecución y verificar sus resultados**.

---

## 1. Corrección de los deberes de la sesión 1

La clase empieza corrigiendo los deberes de la sesión 1 (la solución se publica en `soluciones/sesion1/`, que todavía no está en el repo).

### 1.1 Nivel base: una herramienta más

Diapositiva «Nivel base: una herramienta más», con el código de `soluciones/sesion1/deber_base.py`:

```python
CONSULTAR_PEDIDO = {"type": "function", "function": {
  "name": "consultar_pedido",
  "description": "Devuelve estado, productos, importe y seguimiento de un pedido. "
                 "Úsala cuando el cliente pregunte por un pedido concreto.",
  "parameters": {... "id_pedido": formato ORD-12345}}}

HERRAMIENTAS += [CONSULTAR_PEDIDO]
FUNCIONES["consultar_pedido"] = tienda.obtener_pedido
```

(Copiado de la captura; los `...` están así en la diapositiva.)

Tres ideas de la diapositiva:

1. **El esquema es lo que el modelo lee: la descripción dice cuándo usarla.** El modelo no ve el código de `tienda.obtener_pedido`; solo ve el nombre, la descripción y los parámetros. Por eso la descripción no solo dice *qué devuelve* la herramienta, sino *cuándo usarla* («cuando el cliente pregunte por un pedido concreto»).
2. **El formato del parámetro evita llamadas erróneas.** Indicar `formato ORD-12345` en `id_pedido` hace que el modelo pase el identificador tal cual lo espera `tienda`, en vez de inventarse otro formato (por ejemplo, *ilustrativo*: `10544` o `pedido 10544`).
3. **El bucle no cambia: añadir capacidades es añadir herramientas.** Se añade una entrada a `HERRAMIENTAS` (lo que ve el modelo) y otra a `FUNCIONES` (lo que ejecuta el código); `ejecutar_agente` sigue igual.

En el repo, esta herramienta ya viene incluida en `comun/herramientas.py` para las sesiones 1 y 2, con la descripción «Devuelve estado, productos, importe y número de seguimiento de un pedido.» y el parámetro `id_pedido` descrito como «Formato ORD-12345». (La versión de la solución añade además la frase de *cuándo usarla*.)

### 1.2 Reto: detectar bucles

Enunciado: si una herramienta se llama más de dos veces con los mismos argumentos, el agente debe dejar de intentarlo y explicar al cliente qué pasa, **sin tocar el bucle**.

Diapositiva «Reto: detectar bucles sin tocar el bucle», con el código de `soluciones/sesion1/deber_reto.py`:

```python
def con_deteccion_de_bucles(funciones, max_rep=2):
    llamadas = Counter()

    def vigilada(**args):
        llamadas[(nombre, args)] += 1
        if llamadas[(nombre, args)] > max_rep:
            return {"error": "No lo intentes de nuevo: explica al cliente qué pasa"}
        return funcion(**args)
```

(Copiado de la captura.) Tres ideas de la diapositiva:

1. **Envolvemos cada herramienta en lugar de reescribir el agente.** `con_deteccion_de_bucles` recibe el diccionario `FUNCIONES` y devuelve otro en el que cada función está «vigilada». Al agente se le pasa ese diccionario nuevo con `funciones=...` y ni el bucle ni `ejecutar_herramienta` cambian. Es un *decorador* o *envoltorio*: añade comportamiento por fuera.
2. **Contamos llamadas idénticas.** Un `Counter` (de `collections`) lleva la cuenta por la clave `(nombre de la herramienta, argumentos)`. Mismos argumentos = misma clave.
3. **El error le dice al modelo qué hacer a continuación.** No basta con cortar: el mensaje de error es una instrucción («No lo intentes de nuevo: explica al cliente qué pasa»). Es la misma idea de la sesión 1 (los errores vuelven al modelo), pero ahora el error está pensado para guiar el siguiente paso.

**Ojo al leer el código de la diapositiva:** es una versión resumida. No se ve el bucle que recorre `funciones` y da valor a `nombre` y `funcion` dentro de `vigilada`, ni el `return` del diccionario envuelto. Además, `args` es un diccionario y los diccionarios no se pueden usar como clave de un `Counter`. El fichero real tendrá que convertirlos en algo *hashable* (por ejemplo, *ilustrativo*: `tuple(sorted(args.items()))` o `json.dumps(args, sort_keys=True)`). Habrá que comprobarlo cuando se publique `soluciones/`.

**Comparación con mi solución** (`tema8-agentes/sesion1/agente_minimo.py`, `LLAMADAS_REPETIDAS`):

| | Solución de clase | Mi solución |
|---|---|---|
| Dónde se cuenta | En un envoltorio de cada función | Dentro de `ejecutar_herramienta` |
| Qué se toca | Nada del agente: se le pasa otro `funciones` | La función que ejecuta herramientas (el bucle no) |
| Clave | `(nombre, args)` ya convertidos de JSON | `(nombre, argumentos)` como texto JSON tal cual llega |
| Vida del contador | Una por diccionario envuelto | Global del módulo: **no se reinicia entre conversaciones** |
| Mensaje de error | Corto: no reintentes y explica | Más guiado: no la llames, di que el servicio no está disponible y ofrece alternativa |

Las dos cumplen el reto. Dos detalles de la mía:

- **El contador global es un problema** si se llama a `ejecutar_agente` varias veces en el mismo proceso, como hacen `plan_and_execute` (una vez por paso) o `comparar_estrategias`. Una llamada de una ejecución anterior cuenta para la siguiente.
- **Contar sobre el texto JSON** hace que `{"a":1,"b":2}` y `{"b":2,"a":1}` cuenten como llamadas distintas. Con modelos que repiten el mismo formato suele dar igual.

---

## 2. Dos formas de que el modelo use herramientas: ReAct y tool calling

### Razonar, actuar o las dos cosas

Según la diapositiva, ReAct (Yao et al., 2022) **combinó dos enfoques con carencias opuestas**:

| Enfoque | Qué hace | Su carencia |
|---|---|---|
| **Solo razonar** (*Chain-of-Thought*) | Piensa paso a paso | No consulta el mundo: **inventa datos** |
| **Solo actuar** | Llama a herramientas | Sin plan: **se pierde en tareas largas** |
| **ReAct** | **Intercala pensamiento, acción y observación** hasta resolver la tarea | Junta lo mejor de los dos |

*Chain-of-Thought* («cadena de pensamiento») es pedir al modelo que razone paso a paso antes de responder. Ayuda a razonar, pero todo sale de su memoria: si le preguntas por el pedido de Marta, se inventará el estado (*ilustrativo*). Un agente que solo llama a herramientas sí tiene datos reales, pero no lleva un hilo de qué está buscando ni por qué.

### El formato ReAct

Diapositiva «El formato ReAct», con la traza de un agente ReAct:

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

Cuatro ideas:

1. **El modelo escribe texto con un formato fijo** (Pensamiento / Acción / Entrada).
2. **Nuestro código lee «Acción» y «Entrada» y ejecuta** la herramienta.
3. **La «Observación» la escribe el código, nunca el modelo.** En `react_prompting.py` esto se asegura con `stop=["Observación:"]` (sección 3.3).
4. **Termina con «Respuesta final».**

La traza usa los datos reales de `comun/tienda.py`: Marta tiene `ORD-10231` y `ORD-10544`, y `buscar_cliente` los devuelve del más antiguo al más reciente. Por eso el modelo deduce que «el último es ORD-10544».

### Hoy: tool calling nativo

**El mismo ciclo, pero estructurado por la API:**

```
Usuario               →  Modelo                 →  Código                    →  Modelo
«¿Cómo va mi pedido?»    devuelve una llamada      ejecuta y devuelve           responde o pide
                         estructurada              el resultado                 otra herramienta
```

Y la frase clave de la diapositiva: **el antiguo «Pensamiento» es hoy el razonamiento interno del modelo.** Con tool calling ya no hace falta pedirle que escriba «Pensamiento:». Los modelos actuales razonan por dentro (o directamente) y entregan solo la llamada a la herramienta en un formato que la API garantiza. Lo que en ReAct eran «Acción» y «Entrada» en texto, aquí es un `tool_call` con `name` y `arguments`, como en `sesion1/agente_minimo.py`.

### ReAct: razonar + actuar (según el resumen de la clase)

**ReAct** (*Reasoning and Acting*) junta el razonamiento del modelo con la ejecución de acciones. El agente:

1. plantea qué necesita hacer,
2. elige una herramienta,
3. ejecuta la acción,
4. analiza el resultado,
5. y si no basta, ajusta su estrategia y vuelve a empezar, hasta resolver la tarea.

Lo importante es que el razonamiento **se apoya en resultados reales de las herramientas**, en vez de ser solo una cadena de pensamientos que el modelo se inventa de principio a fin.

### Tool calling: llamadas estructuradas

Con **tool calling**, el modelo pide una herramienta mediante una **llamada estructurada** (un objeto con nombre y argumentos en JSON), no con texto libre. El código recibe esa petición, ejecuta la función y le devuelve el resultado. Es lo que ya hacía el agente de la sesión 1.

### La diferencia

| | ReAct (por *prompting*) | Tool calling nativo |
|---|---|---|
| Quién define el formato | El desarrollador, en el *prompt*: Pensamiento / Acción / Entrada / Observación | La API del modelo |
| Qué devuelve el modelo | Texto que hay que interpretar (*parsear*) | Una llamada estructurada lista para ejecutar |
| Cuándo usarlo | Con modelos que no soportan tool calling | Cuando el modelo lo soporta; la clase lo destaca para **producción empresarial** por el mayor control |

La elección depende de las capacidades del modelo y de los requisitos del proyecto. Pero hay que tener claro que **el bucle es el mismo**: lo que cambia es *quién estructura la llamada a la herramienta* (nuestro *parser* o la API).

---

## 3. El código: `sesion2/react_prompting.py`

Bloque de la agenda «Demo: ReAct a mano» (18:55–19:25). La profesora lo ejecuta en directo:

```bash
python -m sesion2.react_prompting "Soy marta.lopez@email.com, ¿puedo repetir mi último pedido?"
```

**Qué observar**, según la diapositiva «En directo: ReAct prompting»:

- **El prompt contiene todo el «agente».** No hay herramientas registradas en la API: la lista de herramientas, el formato y las reglas van en `INSTRUCCIONES` (sección 3.2). Si borras el prompt, no queda agente.
- **Cada Pensamiento → Acción → Observación.** En la salida se ve un bloque `--- Paso N ---` por vuelta del bucle, seguido de la `Observación:` que añade el código.
- **`stop=["Observación:"]` corta al modelo** antes de que se invente el resultado (sección 3.3).

Es ReAct implementado a mano. Según su propio docstring, «así se construían los agentes antes del tool calling nativo, y así se siguen construyendo con modelos que no lo soportan».

### 3.1 Las herramientas, descritas en texto

Como el modelo ya no recibe las herramientas por la API, hay que describírselas en el *prompt*. `describir_herramientas()` recorre `HERRAMIENTAS` (las mismas de la sesión 1) y genera una línea por herramienta con su nombre, su descripción y sus argumentos, por ejemplo `Entrada: {"producto": "..."}`.

### 3.2 Las instrucciones: el formato ReAct

El *system prompt* (`INSTRUCCIONES`) obliga al modelo a responder siempre así:

```
Pensamiento: qué necesitas averiguar y por qué
Acción: nombre exacto de una herramienta
Entrada: argumentos en JSON en una sola línea
```

El sistema le devuelve una línea `Observación:` con el resultado, y el ciclo se repite. Cuando tiene todo, termina con `Pensamiento: ya tengo lo necesario` y `Respuesta final: ...`.

### 3.3 El bucle `ejecutar_react`

En cada paso (máximo `max_pasos = 8`):

1. **Llama al modelo con `stop=["Observación:"]`**. Este detalle es clave: corta la generación justo antes de que el modelo **se invente la observación**. Sin él, el modelo podría escribir él mismo «Observación: hay 132 unidades» sin haber llamado a nada.
2. Si el texto contiene `Respuesta final:` (expresión regular `PATRON_FINAL`), devuelve esa respuesta.
3. Si contiene `Acción:` + `Entrada:`08_ia_agentica_automatiz_agentes/02-ReAct-patrone-planificacion/video/Clase_2_Tema_8.mp4 (`PATRON_ACCION`), busca la función en `FUNCIONES`, la ejecuta con los argumentos JSON y construye `Observación: <resultado>`. Si la herramienta no existe, devuelve un error (`KeyError`); si falla, devuelve el tipo y el mensaje de la excepción. Igual que en la sesión 1, **los errores se devuelven al modelo**, no rompen el programa.
4. Si el modelo **no ha respetado el formato**, le responde: «formato incorrecto. Usa «Acción:» y «Entrada:» o termina con «Respuesta final:»».
5. La observación se añade como mensaje de usuario y se repite.

Si se acaban los pasos: «No he podido completar la consulta en el límite de pasos.»

#### El parser: la pieza frágil

La diapositiva resume ese bucle en versión corta (pseudocódigo: `llm(...)` sustituye a la llamada completa `cliente.chat.completions.create(...)`, y se omite el manejo de errores):

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

Tres ideas:

1. **`stop` evita que el modelo escriba la observación.**
2. **Expresiones regulares para leer el texto.** `PATRON_FINAL` busca `Respuesta final:` y `PATRON_ACCION` busca `Acción: <nombre>` seguido de `Entrada: {...}`.
3. **Si no respeta el formato, se lo decimos y reintenta.** El «formato incorrecto» vuelve al modelo como observación y el bucle sigue.

Por qué es **la pieza frágil**: todo depende de que el modelo escriba exactamente las palabras que esperan las expresiones regulares. Ejemplos *ilustrativos* de lo que las rompe: escribir `Accion:` sin tilde, poner el JSON en varias líneas, envolverlo en un bloque de código o escribir «Respuesta Final» con mayúscula. Con tool calling nativo este parser desaparece, porque la API ya entrega el nombre y los argumentos separados (sección 2, «Hoy: tool calling nativo»).

#### En el editor durante la demo

Captura del VS Code de la profesora durante la demo, con la carpeta `sesion2/` abierta (`comparar_estrategias.py`, `plan_and_execute.py`, `react_prompting.py`, `reflexion.py`):

- **En el terminal, la misma consulta con tool calling nativo**, para compararla con ReAct a mano: `[Paso 1] 🔧 consultar_pedido({"id_pedido":"ORD-10544"})` y su resultado (estado «en tránsito», productos `crema hidratante` y `contorno de ojos`, total 40,5). Ese formato `[Paso N] 🔧` lo imprime el agente de tool calling (`sesion1/agente_minimo.py`), el mismo que `sesion2/` reutiliza como estrategia «Tool calling nativo» en `comparar_estrategias.py` y como ejecutor en `plan_and_execute.py` y `reflexion.py`. ReAct a mano imprime en cambio `--- Paso N ---`.
- **`comprobar_entorno.py`** abierto: le pide al modelo «¿Qué hora es en Madrid? Usa la herramienta.» con una herramienta `hora_actual`. Si no devuelve `tool_calls`, avisa de que hay que usar otro modelo con soporte de tool calling. Viene a cuento de esta sesión: **un modelo sin tool calling nativo solo puede hacer de agente con ReAct a mano**, y esta comprobación es la que dice en cuál de los dos casos estás.
- En el explorador ya aparece `soluciones/sesion1/` (`deber_base.py`, `deber_reto.py`), los ficheros de la corrección de la sección 1. En nuestro repo todavía no está `soluciones/`.

Comparado con `sesion1/agente_minimo.py`: allí la API devolvía `tool_calls` ya estructurados; aquí todo ese trabajo lo hacen dos expresiones regulares y un `json.loads`, que pueden fallar si el modelo escribe algo ligeramente distinto. Por eso el tool calling nativo da más control.

```bash
python -m sesion2.react_prompting "Soy marta.lopez@email.com, ¿puedo repetir mi último pedido?"
```

### 3.4 ReAct a mano frente a nativo

Diapositiva de cierre de la demo:

| ReAct prompting | Tool calling nativo |
|---|---|
| Funciona con cualquier modelo | Estructura garantizada por la API |
| Razonamiento visible | Llamadas en paralelo |
| Parser frágil | Necesita soporte del modelo |
| Más tokens por paso | Es el estándar actual |

Qué significa cada punto, aterrizado en el código de `sesion2/` y `sesion1/`:

- **Funciona con cualquier modelo / necesita soporte del modelo.** ReAct solo pide que el modelo genere texto siguiendo instrucciones. El tool calling nativo exige que el modelo y la API admitan `tools`. Es lo que comprueba `comprobar_entorno.py` (sección 3.3).
- **Razonamiento visible.** En ReAct el «Pensamiento:» queda escrito en la traza (`--- Paso N ---`) y se puede leer para depurar. En nativo ese razonamiento es interno (sección 2, «Hoy: tool calling nativo») y solo se ve la llamada (`[Paso N] 🔧 ...`).
- **Parser frágil / estructura garantizada por la API.** En ReAct, `PATRON_ACCION` y `json.loads` pueden fallar si el modelo se sale del formato. En nativo la API devuelve `tool_calls` con `name` y `arguments` separados.
- **Más tokens por paso.** En ReAct, la descripción de las herramientas y las reglas del formato viajan en el *system prompt* (`INSTRUCCIONES`), y el modelo escribe además el pensamiento en texto en cada vuelta. Se puede medir con `comparar_estrategias.py` (sección 9).
- **Llamadas en paralelo.** Con tool calling nativo el modelo puede pedir varias herramientas en una misma respuesta: `message.tool_calls` es una lista y `agente_minimo.py` las ejecuta todas antes de volver al modelo. `PATRON_ACCION.search` solo encuentra la primera «Acción», así que ReAct hace una herramienta por vuelta.
- **Es el estándar actual.** Por eso el resto del tema (y el resumen de la clase, para producción empresarial) usa tool calling nativo. ReAct a mano queda para entender qué hace la API por dentro o para modelos sin soporte.

---

## 4. Diseño y organización de las herramientas

Según el resumen de la clase:

- Las herramientas deben tener **nombres descriptivos**, **instrucciones claras** y **parámetros con formato definido**. Así el modelo elige mejor la función y se equivoca menos en los datos de entrada (es lo mismo que mostraba la corrección del deber base, sección 1.1).
- Si un agente tiene un **catálogo de herramientas demasiado grande**, se puede dividir en **agentes especializados**: uno para pedidos, otro para atención al cliente, otro para reembolsos. Un **agente enrutador** recibe la solicitud y la manda al especialista adecuado. Esto **reduce el contexto y el coste** de cada ejecución (es el patrón de *enrutado* de la sesión 1, ahora aplicado a agentes; los sistemas multiagente se ven en la sesión 5).

---

## 5. Bucles y condiciones de parada

Un agente puede **repetir una acción indefinidamente** si no encuentra un cliente, recibe datos incorrectos o no consigue completar la tarea (en Lumen Shop, el caso típico es `consultar_transportista`, que siempre falla a propósito).

Formas de evitarlo que da la clase:

- **Límite de iteraciones** (como `max_pasos` en `ejecutar_react` o en el agente de la sesión 1).
- **Detectar llamadas repetidas** (justo el reto de la sesión 1).
- **Devolver mensajes que indiquen al modelo que pare** o que pida más información al cliente.

Y la idea fuerte: **este control se implementa desde el código**, sin depender solo de que el modelo se dé cuenta de sus propios errores.

### Controlar la ejecución (diapositiva)

La diapositiva reúne cuatro controles, todos puestos por el código y no por el modelo:

| Control | Qué es (diapositiva) | Dónde está en el código del tema |
|---|---|---|
| **Límite de iteraciones** | Red de seguridad que pone siempre el código | `max_iteraciones=8` en `ejecutar_agente`, `max_pasos=8` en `ejecutar_react`, `max_rondas=2` en `responder_con_reflexion` |
| **Límite de presupuesto** | Tokens o euros máximos por tarea | **No implementado.** `ejecutar_agente` suma los tokens y los imprime al terminar, y `ClienteMedido` los mide, pero nada corta la ejecución al pasar un tope |
| **Detección de bucles** | Llamadas repetidas con los mismos argumentos | El reto de la sesión 1 (sección 1.2) |
| **Escalado a humano** | Cuando no puede completar la tarea, lo dice y deriva | Al agotar los pasos, `ejecutar_agente` responde «No he podido completar la consulta. Te paso con un compañero del equipo.» |

El límite de iteraciones va **siempre**, aunque haya otros controles: es lo último que impide un bucle infinito si todo lo demás falla. Un límite de presupuesto (*ilustrativo*) se podría añadir comprobando `tokens` dentro del bucle de `ejecutar_agente` y saliendo con el mismo mensaje de escalado.

---

## 6. Control del formato y fiabilidad

Aunque las llamadas estructuradas mejoran el control, el desarrollador **sigue siendo responsable** de comprobar que el modelo respeta el formato. Herramientas para ello:

- Definir **esquemas de salida** y pedir **JSON**.
- **Validar los parámetros**.
- **Reintentar** cuando la respuesta no cumple las condiciones.
- **Probar distintos modelos**, porque cada uno se comporta distinto ante la misma petición.

En el código del tema esto se ve en `comun/utilidades.py`: `extraer_json` busca el primer objeto JSON dentro del texto del modelo y quita las marcas de bloque de código (*«los modelos a veces añaden texto alrededor»*). Lo usan el planificador y el crítico. La estructura **reduce** errores, pero **no elimina** la necesidad de validar.

---![alt text](image.png)

## 7. Plan-and-execute: planificar, ejecutar, sintetizar

### 7.0 Actividad: tu plan o el suyo

Bloque de la agenda de 19:25 a 19:40. Diapositiva «Plan humano frente a plan del agente» (actividad en grupo, 10 min):

**Tarea:** «Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?» ¿Qué pasos daríais?

1. Proponed los pasos en voz alta (**máximo 5**).
2. ¿Qué herramienta usa cada paso?
3. ¿Qué podría fallar en cada uno?
4. Ahora comparamos con el plan que genera el agente.

Es la misma tarea del ejemplo de uso de `sesion2/plan_and_execute.py`, y el «máximo 5» es el mismo límite que el *prompt* `PLANIFICADOR` impone al agente. La idea es hacer a mano lo que luego hace el planificador y comparar los dos planes.

#### Una posible respuesta (*mía, ilustrativa*; no es la de clase)

Hecha con los datos reales de `comun/tienda.py`:

| # | Paso | Herramienta | Qué podría fallar |
|---|---|---|---|
| 1 | Buscar a Marta y sus pedidos | `buscar_cliente("marta.lopez@email.com")` | Email mal escrito o inexistente → error «No existe ningún cliente…» |
| 2 | Identificar el último pedido | *(ninguna: razonamiento)* | Coger el pedido que no es. La lista viene del más antiguo al más reciente (`ORD-10231`, `ORD-10544`), así que el último es `ORD-10544`. |
| 3 | Ver qué productos tenía | `consultar_pedido("ORD-10544")` | Pasar el ID con otro formato → error que pide `ORD-12345` |
| 4 | Comprobar el stock de cada producto | `consultar_stock("crema hidratante")`, `consultar_stock("contorno de ojos")` | Nombre distinto del catálogo → «Producto no encontrado» (aunque la respuesta incluye la lista de productos disponibles) |
| 5 | Responder a Marta | *(ninguna: síntesis)* | Decir «sí» sin mirar el stock, o inventar plazos o alternativas |

**Resultado con estos datos:** no se puede repetir el pedido completo. `ORD-10544` tenía `crema hidratante` y `contorno de ojos`, y la **crema hidratante tiene 0 unidades** (el contorno de ojos tiene 47). La respuesta correcta es explicárselo y, como mucho, ofrecer el contorno de ojos solo.

Detalles que esta actividad pone sobre la mesa:

- El paso 4 son **dos llamadas**: el número de pasos del plan no coincide con el de llamadas a herramientas.
- Los pasos 2 y 5 no usan herramientas. Un planificador puede incluirlos o no, y en `plan_and_execute.py` cada paso lo resuelve el agente de la sesión 1 aunque no haga falta herramienta.
- El plan humano sabe de antemano que «último» significa «el más reciente de la lista». El agente solo lo sabe si lo dice la **descripción de la herramienta** (`buscar_cliente`: «…del más antiguo al más reciente»), lo que conecta con la sección 1.1.

Este patrón separa la resolución de una tarea en **tres papeles**:

1. **Planificador**: descompone el objetivo en pasos.
2. **Ejecutor**: realiza cada paso y recoge los resultados.
3. **Sintetizador**: usa la información obtenida para redactar la respuesta final.

La ventaja: **el plan se puede inspeccionar antes de ejecutarlo**, detectar errores y hacer que una persona lo revise o apruebe cuando haga falta.

### El esquema (diapositiva «Plan-and-execute»)

Abre el bloque «Planificar y reflexionar» de la agenda (19:40–19:55):

```
Tarea ──► Planificador ──pasos──► Ejecutor ──resultados──► Sintetizador ──► Cliente
          (1 llamada)             (un agente por paso)     (respuesta final)
```

| Pieza | En la diapositiva | En `plan_and_execute.py` |
|---|---|---|
| Planificador | 1 llamada | `planificar()`: una sola llamada con el *prompt* `PLANIFICADOR`, que devuelve `{"pasos": [...]}` |
| Ejecutor | Un agente por paso | `ejecutar_paso()`: lanza el agente de la sesión 1 (`ejecutar_agente`) una vez por cada paso |
| Sintetizador | Respuesta final | `sintetizar()`: una llamada que redacta la respuesta con todos los resultados |

**Ventajas y límites**, según la diapositiva:

- **El plan es visible antes de ejecutar.** En el código, `plan_and_execute` imprime `📋 Plan:` antes de ejecutar ningún paso.
- **Un humano puede aprobarlo.** Como el plan existe antes de actuar, se puede parar ahí para que alguien lo revise. La demo no lo hace; enlaza con el bloque «Caso real: aprobar el plan» de la agenda.
- **Pasos simples con un modelo barato.** Cada paso es una tarea pequeña («resuelve SOLO este paso»), así que el ejecutor podría usar un modelo más pequeño y barato que el planificador. En el código del tema todos usan el mismo `MODELO` de `.env`: es una posibilidad del patrón, no algo que haga la demo.
- **Rígido si algo falla a mitad.** Los pasos se ejecutan en orden sin revisar el resultado. Si `consultar_transportista` falla, el plan sigue como si nada. Es justo el reto de los deberes (replanificación, sección 11).

Coste en llamadas (*cuenta propia*): 1 (planificar) + al menos 1 por paso (cada `ejecutar_agente` hace una llamada más por cada vuelta con herramienta) + 1 (sintetizar). Con un plan de 4 pasos son como mínimo 6 llamadas, frente a las pocas que necesita el agente de tool calling solo. Se mide con `comparar_estrategias.py` (sección 9).

### El código: `sesion2/plan_and_execute.py`

- **`PLANIFICADOR`** (*system prompt*): «Eres el planificador del equipo de atención al cliente de Lumen Shop. Descompón la tarea en pasos concretos (máximo 5).» Incluye los nombres de las herramientas que tendrá el ejecutor y exige responder solo con JSON: `{"pasos": [...]}`.
- **`llamar(cliente, sistema, usuario)`**: una llamada simple al modelo (sistema + usuario) que devuelve el texto.
- **`planificar(tarea, cliente)`**: una sola llamada; con `extraer_json` saca la lista `pasos`.
- **`ejecutar_paso(tarea, paso, resultados, cliente)`**: le pasa al **agente de la sesión 1** (`ejecutar_agente`) la tarea global, los resultados de los pasos anteriores y la orden «Resuelve SOLO este paso».
- **`sintetizar(tarea, resultados, cliente, indicaciones="")`**: redacta la respuesta final «breve y amable, usando solo los resultados obtenidos». El parámetro `indicaciones` permite añadirle instrucciones extra (útil para el deber base, sección 10).
- **`plan_and_execute`**: planifica, imprime el plan (`📋 Plan:`), ejecuta los pasos en orden guardando `{"paso", "resultado"}` y sintetiza.

La limitación, dicha en el propio docstring: **si algo falla a mitad, el plan no se adapta**. Eso es el reto de los deberes.

```bash
python -m sesion2.plan_and_execute "Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?"
```

---

## 8. Reflexión: un crítico que revisa la respuesta

La clase insiste en **evaluar los resultados durante la ejecución** en lugar de dar por hecho que el plan inicial funcionará. Una forma es la **reflexión**: el agente genera un borrador, un crítico lo revisa y, si no lo aprueba, el agente lo rehace con esos comentarios.

### El esquema (diapositiva «Reflexión: un crítico con criterios»)

```
Borrador ──► Crítica ──► Corrección ──► Respuesta
el agente    un revisor   si no aprueba,  máximo
responde     evalúa con   el agente       2 rondas
             criterios    rehace con los
             explícitos   comentarios
```

Frase clave de la diapositiva: **funciona mejor con señales objetivas: tests, datos, reglas.** Un crítico que es el mismo LLM «opinando» se equivoca igual que el autor. Funciona mejor cuando puede comprobar algo concreto. En la demo, el criterio «si un producto no tiene stock suficiente, lo dice» se puede contrastar con un dato real (8 unidades de protector solar). Otros ejemplos de señal objetiva (*ilustrativos*): que unos tests pasen, si se está generando código, o reglas fijas como «máximo 5 frases».

«Máximo 2 rondas» es `max_rondas=2` en `responder_con_reflexion`. Es otra vez un límite de iteraciones (sección 5): sin él, un crítico exigente podría rechazar respuestas para siempre.

### El código: `sesion2/reflexion.py`

- **`CRITERIOS`**, explícitos:
  - Responde a todo lo que pregunta el cliente.
  - Si un producto no tiene stock suficiente, lo dice claramente y ofrece una alternativa.
  - No promete plazos, descuentos ni acciones que no puede garantizar.
  - Es breve (máximo 5 frases) y amable.
- **`CRITICO`**: «revisor de calidad de atención al cliente en Lumen Shop», con esos criterios, y responde solo con JSON `{"aprobado": true/false, "comentarios": "..."}`.
- **`criticar(pregunta, respuesta, cliente)`**: llama al modelo con el crítico y devuelve ese JSON.
- **`responder_con_reflexion(pregunta, max_rondas=2)`**:
  1. Genera un borrador con el agente de la sesión 1.
  2. En cada ronda, el crítico lo revisa. Si está aprobado, lo devuelve.
  3. Si no, vuelve a llamar al agente con la pregunta, su respuesta anterior y los comentarios del revisor: «Redacta una respuesta corregida.»
  4. Si se acaban las rondas, devuelve la última respuesta.

Según el docstring, **funciona mejor cuanto más concretos son los criterios: un crítico que solo «opina» aporta poco.**

El ejemplo de la demo («Quiero comprar 10 protectores solares, ¿me los enviáis?») está pensado para el segundo criterio: en `comun/tienda.py` el protector solar SPF50 solo tiene **8 unidades**.

```bash
python -m sesion2.reflexion "Quiero comprar 10 protectores solares, ¿me los enviáis?"
```

### Replanificar ante fallos

Del resumen de la clase: si un paso falla, el sistema puede analizar el problema y **generar una alternativa**. Ejemplo: si un servicio externo no responde, **no debería seguir como si la operación hubiera salido bien**. El reto es añadir reflexión y replanificación **sin crear nuevos bucles ni ejecutar acciones innecesarias** (de ahí que el reto de los deberes pida limitar las replanificaciones).

### ¿Y los modelos de razonamiento?

Los modelos de razonamiento son modelos que «piensan» internamente antes de responder. La diapositiva se pregunta si con ellos sigue haciendo falta planificar de forma explícita:

| Ya planifican por dentro | El plan explícito sigue aportando |
|---|---|
| Descomponen la tarea internamente | Cuando hay que **auditar** |
| Menos necesidad de plan explícito | Cuando un **humano aprueba** el plan |
| Más tokens y latencia por llamada | En **tareas muy largas** |
| | Para usar **modelos baratos en cada paso** |

Es decir: el modelo de razonamiento hace por dentro lo que `planificar()` hace por fuera, pero ese plan interno **no se ve ni se puede aprobar**, y cada llamada cuesta más tokens y tarda más. Un plan explícito (como el `📋 Plan:` de `plan_and_execute.py`) sigue siendo útil cuando el plan tiene que quedar escrito, revisarse antes de actuar o repartirse entre modelos más baratos. Repite tres de las ventajas de la diapositiva de plan-and-execute (sección 7). Es la misma idea que «el antiguo Pensamiento es hoy el razonamiento interno del modelo» (sección 2), aplicada a la planificación.

### En directo: plan-and-execute y reflexión

Bloque «Demo: plan y reflexión» de la agenda (19:55–20:25). La profesora ejecuta las dos demos desde `tema8-agentes/`:

```bash
python -m sesion2.plan_and_execute "Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?"
python -m sesion2.reflexion "Quiero comprar 10 protectores solares, ¿me los enviáis?"
```

**Qué observar**, según la diapositiva, y dónde se ve en el código:

- **El plan aparece antes de ejecutar nada.** `plan_and_execute` imprime `📋 Plan:` con los pasos numerados y solo después empieza con `▶ Paso 1`.
- **Cada paso recibe los resultados anteriores.** `ejecutar_paso` le pasa al agente un `contexto` con todos los `{"paso", "resultado"}` ya obtenidos («Resultados de pasos anteriores»). Así el paso 2 sabe qué pedido encontró el paso 1.
- **El crítico pilla respuestas que prometen 10 si hay 8.** En `reflexion.py` se imprime `📝 Borrador N` y `🔍 Crítica`. Si el borrador promete los 10 protectores, el criterio «si un producto no tiene stock suficiente, lo dice claramente y ofrece una alternativa» lo rechaza y el agente lo rehace.

En el editor de la profesora durante la demo está abierto `sesion2/plan_and_execute.py`. En su explorador aparecen carpetas que nuestro repo no tiene: `docente/`, `soluciones/` y `tests/`.

#### Resultados en mi máquina

Ejecutado el 27-10-2026 con Ollama y `qwen3:4b-instruct` (el modelo de mi `.env`; en clase se usa `qwen2.5:7b`). Con modelos pequeños cada ejecución sale distinta, así que esto es **una** ejecución, no «el» resultado.

**`plan_and_execute`: el plan del agente** (para compararlo con el plan humano de la sección 7.0):

```
📋 Plan:
  1. buscar_cliente
  2. consultar_pedido
  3. consultar_stock
  4. verificar_disponibilidad
  5. confirmar_repetición
```

- **El planificador ha devuelto nombres de herramientas, no pasos.** Los tres primeros coinciden con el plan humano. Pero `verificar_disponibilidad` y `confirmar_repetición` **no existen** como herramientas: el planificador las ha inventado. No rompe nada porque cada paso lo resuelve el agente de la sesión 1 con las herramientas reales, pero son dos ejecuciones de más (10 llamadas al modelo en total, sección 9).
- **Cada paso responde como si hablara con el cliente.** El paso 1 ya dice «podemos ayudarte a repetirlo», y el paso 2 «Está todo listo para repetirlo»… antes de haber mirado el stock. Es el agente de la sesión 1 haciendo su trabajo de siempre: contestar al cliente.
- **El paso 3 encuentra el problema** («no hay stock disponible de la crema hidratante») y, como cada paso recibe los anteriores, los pasos 4 y 5 lo mantienen.
- **Respuesta final correcta:** no se puede repetir el pedido porque la crema hidratante no tiene stock. Le falta ofrecer el contorno de ojos solo, que sí tiene stock.

**`reflexion`: el crítico no ha pillado nada.**

- Borrador: «no tenemos el producto "protección solar" en stock. Sin embargo, sí tenemos disponibles otros productos como "protector solar SPF50"». El agente consultó un nombre que no está en el catálogo, recibió «producto no encontrado» y **ofreció como alternativa el mismo producto que pedía el cliente**. Nunca llegó a ver las 8 unidades.
- Crítica: `{'aprobado': True, ...}`. Según el crítico, «indica falta de stock, ofrece una alternativa y es breve y amable».
- **Por qué:** el crítico solo ve la pregunta y la respuesta, **no los datos**. Comprueba que la respuesta *tenga la forma* de los criterios (dice que no hay stock, ofrece algo), pero no puede comprobar si es verdad. Es la frase de la diapositiva al revés: sin **señales objetivas** (aquí, el resultado real de `consultar_stock`), la reflexión aprueba respuestas equivocadas. En esta ejecución, la de clase («pilla respuestas que prometen 10 si hay 8») no se ha dado.

**`react_prompting` (demo de la sección 3): una conclusión inventada.**

Busca a Marta, consulta `ORD-10544` y en el paso 3 escribe «Ya tengo toda la información necesaria» y responde que el pedido «está disponible para repetir». **No ha consultado el stock.** El formato ReAct se ha cumplido a la perfección (el parser no ha fallado), pero el razonamiento se ha cerrado antes de tiempo. Es justo lo que intenta evitar un plan explícito (el paso 3 del plan humano y del planificador).

---

## 9. Comparar estrategias: llamadas, tokens y tiempo

Para comparar arquitecturas, la clase propone **ejecutar la misma tarea con cada estrategia** y medir:

- número de **llamadas al modelo**,
- **tokens** utilizados,
- **tiempo** de ejecución,
- y comprobar si la respuesta **resuelve bien** la petición.

Las pruebas **hay que repetirlas**, porque los modelos no dan siempre el mismo resultado. Y una arquitectura **más compleja no es necesariamente mejor**: se evalúa por precisión, coste, velocidad y facilidad de supervisión.

### El código: `sesion2/comparar_estrategias.py` y `comun/medidor.py`

- **`ClienteMedido`** (`comun/medidor.py`) envuelve el cliente del modelo y, en cada `chat.completions.create`, suma una llamada, los tokens (`usage.total_tokens`) y los segundos. `resumen()` devuelve, por ejemplo, `5 llamadas · 3200 tokens · 12.4 s` (*cifras ilustrativas*).
- **`TAREA`** por defecto: «Soy marta.lopez@email.com. Quiero repetir exactamente mi último pedido. ¿Tenéis stock de todo lo que pedí?»
- **`ESTRATEGIAS`**: las cuatro que se comparan:
  1. Tool calling nativo (agente de la sesión 1),
  2. ReAct prompting,
  3. Plan-and-execute,
  4. Con reflexión.
- **`comparar`** crea un `ClienteMedido` nuevo para cada estrategia, la ejecuta (si falla, guarda `ERROR: ...`) e imprime el resumen y la respuesta.

El docstring avisa: **con modelos pequeños los resultados varían bastante entre ejecuciones, y eso también es parte de la lección.**

```bash
python -m sesion2.comparar_estrategias
```

### En directo: cuatro estrategias, una tarea

Diapositiva de la misma demo. **Qué observar:**

- **Llamadas al modelo** de cada estrategia.
- **Tokens y tiempo.**
- **Calidad de la respuesta.** Las métricas no dicen si la respuesta es correcta: hay que leerla. Con la `TAREA` por defecto, lo correcto es decir que la crema hidratante no tiene stock (sección 7.0).
- **Ejecutadlo dos veces: los resultados varían.** El mismo programa con la misma tarea da números y respuestas distintas en cada ejecución.

#### Ejecución en clase

La profesora lo ejecuta en directo (`python -m sesion2.comparar_estrategias`, con la `TAREA` por defecto). Salida transcrita de la captura de su terminal:

| Estrategia | Llamadas | Tokens | Tiempo |
|---|---|---|---|
| Tool calling nativo | 2 | 1018 | 7,6 s |
| ReAct prompting | 3 | 1329 | 12,3 s |
| Plan-and-execute | 6 | 2572 | 21,8 s |
| Con reflexión | 10 | 7363 | 107,1 s |

Respuestas de cada estrategia:

- **Tool calling nativo:** «Hola Marta López, Su último pedido (ORD-10544) se realizó el 16 de marzo. Vamos a verificar ahora si aún tenemos stock de todos los productos que compró en ese pedido. Un momento, por favor.»
- **ReAct prompting:** «Por favor, confirma tu correo electrónico nuevamente. Necesito asegurarme de buscar el pedido correcto para ti.»
- **Plan-and-execute:** «Hola Marta, Lo siento, parece que no encontramos tu último pedido. Para ayudarte a repetirlo, ¿podrías compartir detalles sobre los productos que deseas o el número completo del pedido? Tenemos stock disponible para nuestro serum de vitamina C (132 unidades disponibles). Gracias, Equipo Lumen Shop»
- **Con reflexión:** «¡Hola Marta! He revisado tu último pedido, ORD-10231, y veo que compraste el "serum vitamina C" por un total de 24.9€. Te confirmo que actualmente tenemos stock disponible. Podemos repetir tu pedido sin problemas. ¿Te parece bien que lo hagamos? Un saludo, Equipo de Lumen Shop»

**Ninguna de las cuatro respuestas es correcta.** Lo correcto es decir que no se puede repetir `ORD-10544` porque la crema hidratante no tiene stock (sección 7.0). Contrastando con `comun/tienda.py`:

| Estrategia | Qué falla |
|---|---|
| Tool calling nativo | Encuentra el pedido bueno, pero **se para antes de consultar el stock** y responde «un momento, por favor», como si fuera a seguir. Además, **la fecha «16 de marzo» es inventada**: `tienda.py` no guarda fechas de pedido. |
| ReAct prompting | **Pide el email** que ya venía en la tarea. No llega a usar ninguna herramienta útil. |
| Plan-and-execute | Dice que **no encuentra el pedido**, que sí existe, y ofrece el serum de vitamina C, que no venía a cuento. (El dato de 132 unidades sí es real.) |
| Con reflexión | **Coge el pedido equivocado:** `ORD-10231` es el más antiguo (la lista va del más antiguo al más reciente). Los datos de ese pedido son reales (serum vitamina C, 24,90 €), pero la conclusión «podemos repetir tu pedido sin problemas» es falsa para el último pedido. Y el crítico **la ha aprobado**. Es además la más cara: 10 llamadas, 7363 tokens, 107 s. |

Lecciones de esta ejecución:

- **Las métricas no dicen nada de la calidad.** La estrategia más barata (2 llamadas) y la más cara (10 llamadas, unas 7 veces más tokens) fallan las dos. Por eso la diapositiva pone «calidad de la respuesta» como un punto aparte: hay que leer cada respuesta y comprobarla con los datos.
- **Gastar más no garantiza acertar.** La reflexión, con 14 veces el tiempo del nativo, da una respuesta segura de sí misma y equivocada, y el crítico no lo detecta porque no ve los datos (lo mismo que en mi ejecución de `reflexion`, sección 8).
- **«Último» es una trampa** para un modelo pequeño: depende de saber que la lista va del más antiguo al más reciente. Está en la descripción de `buscar_cliente`, pero no garantiza que el modelo lo use.
- **Comparando con mi ejecución (abajo)**, con el mismo código salen números y aciertos muy distintos. Es justo el punto «ejecutadlo dos veces: los resultados varían», y aquí cambian también el modelo y la máquina.

#### Resultados en mi máquina

Dos ejecuciones seguidas, como pide la diapositiva (Ollama, `qwen3:4b-instruct`, 27-10-2026):

| Estrategia | Ejecución 1 | Ejecución 2 | ¿Respuesta correcta? |
|---|---|---|---|
| Tool calling nativo | 4 llamadas · 2650 tokens · 19,1 s | 4 llamadas · 2633 tokens · 15,0 s | Sí: no hay stock de la crema hidratante |
| ReAct prompting | 4 llamadas · 2404 tokens · 39,2 s | 5 llamadas · 3266 tokens · 41,8 s | Sí, en las dos |
| Plan-and-execute | 10 llamadas · 6495 tokens · 67,5 s | 10 llamadas · 6428 tokens · 59,3 s | Sí, y además menciona que el contorno de ojos sí está |
| Con reflexión | 8 llamadas · 4781 tokens · 53,3 s | 3 llamadas · 1462 tokens · 17,2 s | **No**: dice que el sistema de clientes no funciona (ver abajo) |

Lo que se ve:

- **Lo más simple gana aquí.** El tool calling nativo es el más barato y rápido y acierta. Plan-and-execute cuesta unas **2,5 veces más tokens y 3-4 veces más tiempo** para una respuesta solo algo más completa. Es la idea del resumen de la clase: una arquitectura más compleja no es necesariamente mejor.
- **ReAct a mano tarda el doble que el nativo con un número parecido de tokens.** En esta prueba ha acertado, al contrario que la demo suelta de la sección 3: mismo código, otra ejecución, otro resultado.
- **Los resultados varían**: ReAct pasa de 4 a 5 llamadas y la reflexión de 8 a 3, con la misma tarea.

**El fallo de «Con reflexión» no es del modelo: es de mi solución del reto de la sesión 1.** Las dos veces responde «no podemos verificar tu último pedido porque el servicio de búsqueda de clientes está temporalmente inactivo». La causa es `LLAMADAS_REPETIDAS` en `sesion1/agente_minimo.py`:

1. Es un diccionario **global del módulo**, y `comparar_estrategias` ejecuta las cuatro estrategias **en el mismo proceso**.
2. **Cuenta todas las llamadas, también las que salen bien**, aunque el mensaje de error diga «sin éxito».
3. Cuando le llega el turno a la reflexión, `buscar_cliente` con `{"email": "marta.lopez@email.com"}` ya se ha llamado dos veces (en el tool calling nativo y en plan-and-execute). La tercera se bloquea con el mensaje «explica al cliente que el servicio no está disponible», y el agente obedece.

Comprobado sin modelo: tres llamadas seguidas a `ejecutar_herramienta("buscar_cliente", ...)` devuelven datos, datos y el error. (ReAct a mano no se ve afectado porque usa su propio ejecutor, no `ejecutar_herramienta`.)

Es el riesgo que ya se apuntaba en la sección 1.2. La solución de clase lo evita porque crea un `Counter` nuevo cada vez que se envuelven las funciones. Para arreglar la mía: reiniciar el contador al empezar cada `ejecutar_agente` (o pasarlo como parámetro), y contar solo las llamadas que fallan.

### Actividad: elige la estrategia

Bloque de la agenda de 20:25 a 20:35. *Pendiente de las capturas del enunciado.*

---

## 10. Supervisión humana y preparación para producción

En aplicaciones reales el agente necesita **límites** y una forma de gestionar lo que no puede resolver:

- **Escalar a una persona** cuando faltan permisos, falla una herramienta o el problema supera lo que el sistema puede hacer.
- **Registrar trazas y métricas** con herramientas como **MLflow**, para analizar ejecuciones y detectar errores.
- **La autonomía se ajusta al riesgo** de cada tarea, y siempre se mantiene la posibilidad de intervenir.

---

## 11. Deberes y lectura (para la sesión 3)

Solución: se publica tras la sesión 3. Ejecutar desde `tema8-agentes/` como módulo.

**Nivel base · Añade reflexión al plan-and-execute.** Antes de devolver la respuesta final del plan-and-execute, el crítico de `reflexion.py` la revisa; si no la aprueba, se vuelve a sintetizar incluyendo sus comentarios. Pista: se pueden reutilizar `planificar`, `ejecutar_paso`, `sintetizar` y `criticar` **sin modificarlas**. Punto de partida: `sesion2/plan_and_execute.py` y `sesion2/reflexion.py`. (*Pista propia:* fíjate en el parámetro `indicaciones` de `sintetizar`.)

**Reto · Replanificación ante fallos.** Si un paso falla (por ejemplo, el transportista no responde), el plan sigue como si nada. Añade un **verificador** que decida si cada paso se ha completado y, si no, pide al planificador **un plan nuevo para lo que queda**. **Limita el número de replanificaciones.** Prueba: «¿Dónde está el último pedido de marta.lopez@email.com?». Punto de partida: `sesion2/plan_and_execute.py`.

**Lectura:** *ReAct: Synergizing Reasoning and Acting in Language Models* (Yao et al., 2022) — https://arxiv.org/abs/2210.03629. Basta con la introducción y los ejemplos de trazas. Léelo con ojo crítico: ¿qué problema resolvía y qué ha cambiado con el tool calling nativo?
