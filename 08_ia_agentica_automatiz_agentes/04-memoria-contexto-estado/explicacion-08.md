# Sesión 4: Memoria, contexto y estado

Explicación sencilla de la sesión 4 del Tema 8, centrada en las ideas principales. Se construye a partir del PDF de la sesión (`Tema8_Sesion4_Memoria_contexto_y_estado.pdf`), del código de `../tema8-agentes/sesion4/` y de la solución de los deberes (`Solución deberes sesión 4/`). Los ejemplos propios van marcados como *ilustrativos*.

---

## 0. Dónde estamos

| Sesión | Bloque | Qué se añade |
|---|---|---|
| 1 | Agente | Un agente desde cero |
| 2 | Planificar | ReAct y patrones de planificación |
| 3 | Herramientas | LangGraph, APIs externas y MCP |
| **4** | **Memoria** | **Contexto, memoria y estado (esta sesión)** |
| 5 | Equipos | Sistemas multiagente |
| 6 | Producción | Integración en la empresa |

Hasta ahora el agente de Lumen Shop **empezaba de cero en cada conversación**: no sabía nada del cliente y, si el programa se cerraba, se perdía todo. Esta sesión responde a tres preguntas:

1. **¿Qué metemos en cada llamada al modelo?** (el contexto es limitado).
2. **¿Qué recuerda el agente de un cliente entre una conversación y otra?** (memoria a largo plazo).
3. **¿Cómo se guarda una conversación a medias para seguirla después?** (estado).

### Los ficheros de la práctica (`../tema8-agentes/sesion4/`)

Son tres ficheros. Dos son demos que se ejecutan y uno es una pieza que usa la primera demo:

| Fichero | Qué hace, en una frase |
|---|---|
| `memoria.py` | **La «libreta» de cada cliente.** Guarda notas sobre él, busca las que vienen a cuento y las borra si lo pide. No se ejecuta solo: lo usa el siguiente |
| `agente_con_memoria.py` | **Demo 1: el agente que se acuerda de ti.** Antes de responder mira la libreta del cliente y, al terminar, apunta lo nuevo |
| `checkpointing.py` | **Demo 2: el marcapáginas de una conversación.** Guarda cada paso de la conversación para seguirla otro día, ver el historial o volver atrás |

**`memoria.py`, la libreta.** Hace tres cosas:
- **Escribir:** le pasa la conversación al modelo y le pregunta «¿qué merece recordarse de este cliente?». Lo que diga se guarda como notas.
- **Recuperar:** cuando el cliente vuelve, da una nota a cada recuerdo (cuánto se parece a lo que pregunta y lo reciente que es) y devuelve los 3 mejores.
- **Olvidar:** borra todas las notas de un cliente.

Todo se guarda en un fichero, `datos/memoria.json`: una lista de notas por email.

**`agente_con_memoria.py`, la demo de la memoria.** Atiende un mensaje en tres pasos: pide a la libreta los recuerdos de ese cliente, se los pone al agente en sus instrucciones («lo que sabemos de conversaciones anteriores: …») y, cuando el agente ha respondido, le pide a la libreta que apunte lo nuevo. Con `--olvidar` borra al cliente. Se explica en la sección 3.

**`checkpointing.py`, la demo del estado.** Es el agente normal de la sesión 3, pero guardando cada paso de la conversación en una base de datos (`datos/checkpoints.sqlite`). Cada conversación tiene un nombre (`--hilo ticket-42`). Con ese nombre puedes seguirla aunque el programa se haya cerrado, ver todos sus pasos (`--historial`) o volver a uno anterior y seguir por otro camino (`--volver 2`). Se explica en la sección 6.

**La diferencia entre las dos demos:** la primera recuerda **al cliente** (sirve para todas sus conversaciones); la segunda recuerda **una conversación** (sirve para retomarla). Es la sección 5.3: memoria frente a estado.

**Cómo ejecutarlas:**
- Siempre desde `tema8-agentes/`, con el entorno activado, y como módulo: `python -m sesion4.agente_con_memoria ...`.
- Lo que guardan va a `tema8-agentes/datos/`. **Si borras esa carpeta, empiezas de cero.**
- La demo de memoria funciona mejor con el modelo de embeddings `nomic-embed-text` en Ollama. Si no lo tienes, usa una alternativa más simple y avisa con «ℹ️ Sin modelo de embeddings disponible».

---

## 1. Corrección de los deberes de la sesión 3

### 1.1 Nivel base: herramientas que ahorran pasos

**El deber:** rediseñar dos herramientas aplicando las reglas de diseño de la sesión 3.

| Antes | Después |
|---|---|
| `buscar_cliente` devuelve solo los números de pedido | `buscar_cliente_con_pedidos` devuelve **un resumen de cada pedido** |
| Una llamada más por cada pedido | **Una sola llamada** |
| «serum» no encuentra nada | Acepta **nombres parciales** y **ofrece opciones** si hay varias |

**La solución** (`soluciones/sesion3/deber_base.py`), en lo esencial:

- `buscar_cliente_con_pedidos`: busca al cliente y, en la misma respuesta, mete el estado, los productos y el importe de cada uno de sus pedidos.
- `consultar_stock_flexible`: busca todos los productos que **contienen** el texto. Si hay uno, devuelve su stock. Si no hay ninguno, devuelve la lista de productos disponibles. Si hay varios, dice «pregunta al cliente cuál quiere» con las opciones.

**Por qué importa:** la diapositiva lo resume así: **menos pasos = menos tokens y menos errores**. Y lo recuerda con el cálculo de la sesión 1: si cada paso sale bien el 95 % de las veces, diez pasos seguidos salen bien solo el 60 % (0,95¹⁰ ≈ 0,60). Cada llamada que ahorras es una ocasión menos de equivocarse.

### 1.2 Reto: un recurso MCP

**El deber:** añadir al servidor MCP de Lumen Shop una herramienta nueva y un **recurso** con la política de devoluciones.

```python
@servidor.resource("lumen://politica-devoluciones")
def politica_devoluciones() -> str:
    """Política de devoluciones de Lumen Shop."""
    return ("Devoluciones gratuitas en 30 días..."
            "Más de 50 € requiere supervisor.")
```

Las tres ideas de la diapositiva:

1. **Las herramientas actúan; los recursos aportan contexto.** Una herramienta se *ejecuta* (consulta un pedido). Un recurso se *lee* (un documento, aquí la política de devoluciones).
2. **El cliente MCP decide cuándo leerlos.** El servidor solo los ofrece; es el agente (o Claude Desktop, o el IDE) quien decide si los lee y cuándo.
3. **Buen puente con el tema de hoy: qué contexto damos al agente.** Un recurso es justo eso: información que le ponemos delante al agente para que decida mejor.

---

## 2. El contexto es finito

### 2.1 Más contexto no es mejor contexto

El **contexto** es todo lo que el modelo lee en cada llamada: las instrucciones, las descripciones de las herramientas, la conversación y los resultados de las herramientas. Tiene un límite, y además, **llenarlo tiene tres problemas**:

| Problema | Qué pasa |
|---|---|
| **Se pierde en el medio** | Los modelos atienden peor a lo que queda enterrado en mitad de un contexto largo |
| **Cuesta dinero** | Cada vuelta del bucle reenvía **todo** el historial |
| **Añade latencia** | Más texto de entrada → respuestas más lentas |

**«Se pierde en el medio»** viene de un estudio («Lost in the Middle», Liu et al., 2023): los modelos se fijan bien en lo que está **al principio** y **al final** del contexto, pero lo del medio se les «escapa». Como cuando lees un documento muy largo: recuerdas cómo empezaba y cómo acababa, pero no el párrafo 37.

La idea: **no se trata de meter todo lo posible, sino lo justo.**

### 2.2 Dónde se va el contexto de un agente

Lo que ocupa espacio en cada llamada:

- Las instrucciones y las descripciones de las herramientas.
- Cada llamada a una herramienta y su resultado.
- Los resultados largos (JSON, documentos).
- El historial de la conversación.

Y lo importante: **todo esto se reenvía completo en cada vuelta del bucle (×N).** Si el agente da 5 vueltas para responder, el modelo lee la conversación 5 veces, y cada vez un poco más larga, porque se le van sumando los resultados de las herramientas. Por eso en la sesión 3 insistíamos en las **salidas acotadas**: un JSON enorme no se paga una vez, se paga en cada vuelta.

### 2.3 Context engineering: cuatro estrategias

*Context engineering* («ingeniería del contexto») es **decidir qué entra en cada llamada al modelo**. Hay cuatro estrategias:

| Estrategia | Qué es | Ejemplo |
|---|---|---|
| **Escribir** | Guardar cosas **fuera** del contexto: notas, archivos, memoria | La memoria a largo plazo de la demo (sección 3) |
| **Seleccionar** | Recuperar **solo lo relevante** para este paso | Recuperar 3 recuerdos del cliente, no todos |
| **Comprimir** | Resumir el historial o recortar resultados largos | El deber base de esta sesión (sección 9) |
| **Aislar** | Repartir el trabajo entre **subagentes**, cada uno con su propio contexto | Lo veremos en la sesión 5 (multiagente) |

Toda la sesión es aplicar estas cuatro ideas.

---

## 3. Demo: memoria a largo plazo

### 3.1 Leer, responder, escribir

La memoria a largo plazo es lo que el agente **recuerda de un cliente entre una conversación y otra**. Funciona en cuatro pasos:

```
Mensaje ──► Recuperar ──► Responder ──► Escribir
```

1. **Mensaje:** el cliente escribe.
2. **Recuperar:** se buscan **solo los recuerdos relevantes para este mensaje**, no todo lo que sabemos del cliente (estrategia *seleccionar*).
3. **Responder:** el agente responde con esos recuerdos metidos en sus instrucciones.
4. **Escribir:** al terminar, el modelo lee la conversación y **extrae qué merece recordarse** (estrategia *escribir*).

¿Cómo se eligen los recuerdos relevantes? Con una puntuación: **similitud con la consulta + recencia** (sección 3.3).

### 3.2 En directo: el agente recuerda

```bash
python -m sesion4.agente_con_memoria marta.lopez@email.com "Tengo la piel muy sensible y me salen rojeces. ¿Qué tal es el sérum?"
python -m sesion4.agente_con_memoria marta.lopez@email.com "¿Qué me recomendáis para el sol?"
python -m sesion4.agente_con_memoria marta.lopez@email.com --olvidar
```

Cada comando es un programa nuevo, **como si fueran días distintos**. Lo que une una conversación con la siguiente no es el programa, sino un fichero (`datos/memoria.json`) donde se guardan los recuerdos de cada cliente.

**Qué observar**, según la diapositiva:

- **Qué memorias se guardan tras la primera conversación.** El programa imprime «💾 Memorias guardadas: …». *Ilustrativo:* algo como «Marta tiene la piel sensible y le salen rojeces» (un hecho estable) y «Preguntó por el sérum de vitamina C» (lo que pasó).
- **Qué recuerdos se recuperan en la segunda.** Imprime «🧠 Recuerdos recuperados: …». Marta pregunta por el sol, pero el agente ya sabe que tiene la piel sensible, y puede tenerlo en cuenta al recomendarle el protector solar. En la primera conversación pone «(primera conversación con este cliente)».
- **Derecho de supresión en una línea.** `--olvidar` borra todo lo que se recuerda de Marta e imprime cuántas memorias ha borrado.

**El código, en lo esencial** (`sesion4/agente_con_memoria.py`):

```python
def atender(email, mensaje, memoria):
    # 1. Leer: recuperamos lo relevante para ESTE mensaje
    recuerdos = memoria.recuperar(email, mensaje)
    instrucciones = f"{INSTRUCCIONES}\nLo que sabemos de conversaciones anteriores:\n{recuerdos}"

    agente = construir_agente(modelo, LECTURA, instrucciones)
    respuesta = agente.invoke(...)

    # 2. Escribir: al terminar, decidimos qué merece recordarse
    memoria.recordar_conversacion(email, f"Cliente: {mensaje}\nAgente: {respuesta}")
```

Fíjate en que los recuerdos **no se le pasan al agente como herramienta**: se meten directamente en sus instrucciones antes de empezar. Y que el agente es el mismo `construir_agente` de la sesión 3: la memoria va **por fuera**, alrededor del agente.

**Qué decide qué se guarda.** Las instrucciones del «extractor» (`sesion4/memoria.py`) le piden al modelo dos tipos de recuerdos:
- **Semántica**: hechos o preferencias estables del cliente («tiene la piel sensible»).
- **Episódica**: qué pasó en esta conversación, en una frase («preguntó por el sérum»).

Y una regla importante: **«No guardes datos de pago ni de salud más allá de lo necesario para recomendar productos.»** (Sección 5.4.)

### 3.3 La puntuación de un recuerdo

```python
def puntuar(memoria, vector_consulta, ahora):
    dias = (ahora - memoria["fecha"]).days
    recencia = 0.5 ** (dias / vida_media)
    similitud = coseno(vector_consulta, memoria["vector"])
    return 0.7 * similitud + 0.3 * recencia
```

Leído en castellano: *cada recuerdo recibe una nota que mezcla cuánto se parece a lo que pregunta el cliente (70 %) y lo reciente que es (30 %).* Se ordenan por nota y se quedan los 3 mejores.

Las tres ideas de la diapositiva:

1. **La recencia decae a la mitad cada 30 días.** Un recuerdo de hoy vale 1; de hace 30 días, 0,5; de hace 60 días, 0,25. Lo reciente pesa más, pero lo antiguo no desaparece.
2. **La similitud viene de los embeddings (Tema 5).** Como en RAG: cada texto se convierte en un vector (una lista de números) y dos textos que hablan de lo mismo tienen vectores parecidos. «Coseno» es la forma de medir ese parecido. Así, si Marta pregunta por el sol, sale antes «tiene la piel sensible» que «preguntó por el horario».
3. **El peso de cada factor es una decisión de diseño.** El 70/30 no es una ley: lo decides tú según el negocio. Una tienda donde las preferencias cambian rápido daría más peso a la recencia; un historial médico, casi ninguno.

Un detalle del código: si no tienes un modelo de embeddings instalado (`nomic-embed-text` en Ollama), `memoria.py` usa una alternativa sencilla que compara palabras. Funciona peor, pero funciona en cualquier equipo.

**Ojo:** el código usa un almacén de memoria **escrito a mano** (un JSON con los vectores) para que se vea qué pasa por dentro. En el Tema 5 vimos bases vectoriales de verdad; aquí lo importante es la **lógica de la memoria**, no el motor.

---

## 4. Actividad: recordar u olvidar

**¿Lo guardarías en memoria?** Para cada frase de un cliente: ¿recordar, no recordar o recordar con condiciones? ¿Por qué?

No hay respuesta oficial en el PDF. Una propuesta (*ilustrativa*), aplicando la regla del extractor («nada de datos de pago ni de salud más allá de lo necesario»):

| Frase | Decisión | Por qué |
|---|---|---|
| 1. «Prefiero que me enviéis a la oficina» | **Recordar** | Preferencia estable y útil para el futuro |
| 2. «Mi número de tarjeta es…» | **No recordar nunca** | Dato de pago: no es trabajo del agente guardarlo y es un riesgo enorme si se filtra |
| 3. «Tengo la piel atópica» | **Con condiciones** | Es un dato de salud, pero en una tienda de cosmética es justo lo que permite recomendar bien. Guardarlo con el mínimo detalle, avisando al cliente y dejándole borrarlo |
| 4. «Estoy muy enfadado con vosotros» | **No (o solo el hecho)** | La emoción de hoy no es un rasgo del cliente. Como mucho, un recuerdo episódico del motivo: «se quejó porque su pedido llegó roto» |
| 5. «Es un regalo para mi madre, que cumple 60» | **No, o con caducidad** | Es de esta compra, no del cliente. Y son datos de otra persona (la madre) |
| 6. «Compré el sérum en 2024» | **No hace falta** | Ya está en el sistema de pedidos: no se duplica en la memoria |

La pregunta que guía: **¿esto me ayudará a atender mejor a este cliente en el futuro, y tengo derecho a guardarlo?**

---

## 5. Memoria y estado

### 5.1 Cuatro tipos de memoria

| Tipo | Qué es | En Lumen Shop |
|---|---|---|
| **De trabajo** | El contexto de la conversación actual | Los mensajes de esta conversación |
| **Episódica** | Qué pasó en interacciones anteriores | «Preguntó por el sérum» |
| **Semántica** | Hechos y preferencias del cliente o del negocio | «Tiene la piel sensible» |
| **Procedimental** | Cómo hacer las cosas: instrucciones y habilidades | Las instrucciones del agente (el *system prompt*) |

Es la clasificación del marco **CoALA**, inspirada en cómo funciona la memoria humana: lo que tienes ahora en la cabeza (de trabajo), lo que te pasó (episódica), lo que sabes (semántica) y lo que sabes hacer, como montar en bici (procedimental).

En la demo hemos visto la **episódica** y la **semántica**: son los dos tipos que el extractor guarda.

### 5.2 Tres decisiones de diseño

| Decisión | Opciones |
|---|---|
| **Qué guardar** | Hechos útiles en el futuro; **nunca datos sensibles innecesarios** |
| **Cuándo escribir** | Durante la conversación o **en segundo plano al terminar** |
| **Cómo recuperar** | Similitud, recencia, importancia |

En la demo: se guardan hechos y episodios, se escribe **al terminar** la conversación, y se recupera por **similitud + recencia**. La **importancia** es lo que falta, y es el reto de los deberes (sección 9.2).

### 5.3 Estado frente a memoria

Son dos cosas distintas que a menudo se confunden:

| Estado (*checkpointing*) | Memoria a largo plazo |
|---|---|
| La foto de **una** ejecución concreta | Lo aprendido **entre** ejecuciones |
| Permite **pausar y reanudar** | Permite **personalizar** |
| Vive en un **hilo** (*thread*) | Vive **por cliente** o por usuario |
| Ejemplo: el ticket-42 a medio resolver | Ejemplo: Marta tiene la piel sensible |

Dicho fácil:
- **El estado** es como un **marcapáginas**: guarda exactamente dónde se quedó **esta** conversación (todos los mensajes, en qué paso iba) para seguirla después. Ya lo usamos en la sesión 3: la pausa para la aprobación humana funcionaba porque el estado se guardaba.
- **La memoria** es como la **ficha del cliente**: unas pocas notas que sirven para **cualquier** conversación futura con él.

Un hilo es una conversación concreta (un ticket). Un cliente puede tener muchos hilos, pero una sola memoria.

### 5.4 La memoria también es un dato personal

> **Si vuestro agente recuerda, tiene que poder olvidar.**

Lo que guarda la memoria son datos personales, así que se aplica el **RGPD** (la ley europea de protección de datos). Tres principios:

- **Minimización de datos:** guardar solo lo necesario. Por eso el extractor tiene la regla de no guardar datos de pago ni de salud de más.
- **Transparencia:** el cliente tiene que poder saber qué se guarda de él.
- **Derecho de supresión:** si el cliente pide que le olvides, hay que poder borrarlo todo. En la demo, `--olvidar`.

Y la clave: **diseñadlo desde el principio.** Añadir el «olvidar» después, cuando los datos de un cliente están repartidos por varios sitios, es mucho más difícil.

---

## 6. Demo: checkpointing

### 6.1 En directo: retomar, revisar, volver atrás

```bash
python -m sesion4.checkpointing --hilo ticket-42 "Soy jorge.ruiz@email.com, ¿cómo va mi pedido?"
python -m sesion4.checkpointing --hilo ticket-42 "¿Y qué producto era?"
python -m sesion4.checkpointing --hilo ticket-42 --historial
python -m sesion4.checkpointing --hilo ticket-42 --volver 2 "Perdona, soy marta.lopez@email.com"
```

Aquí no hay memoria a largo plazo: hay **estado**. Cada paso del grafo se guarda en una base de datos (SQLite, en `datos/checkpoints.sqlite`). El `--hilo ticket-42` es el «nombre» de la conversación.

**Qué observar**, según la diapositiva:

- **El segundo mensaje recuerda el primero aunque el proceso se cerró.** «¿Y qué producto era?» no dice ni quién es ni qué pedido. Pero como el hilo está guardado, el agente recupera la conversación anterior y sabe que habla de Jorge y de su pedido `ORD-10598` (un protector solar SPF50, pendiente de envío).
- **Cada paso del grafo es un estado guardado.** `--historial` lista todos los estados del hilo: el inicio, el mensaje de Jorge, cada llamada a herramienta, cada respuesta… Cada uno es una «foto» a la que se puede volver.
- **Desde un estado anterior la conversación se bifurca.** `--volver 2` retoma la conversación desde el estado 2, como si lo que vino después no hubiera pasado, y continúa con un mensaje nuevo.

**El código, en lo esencial** (`sesion4/checkpointing.py`): es el mismo agente de siempre, con una pieza más:

```python
construir_agente(modelo, LECTURA, "Eres el agente de Lumen Shop...",
                 checkpointer=SqliteSaver(conexion))
```

El *checkpointer* es «dónde se guarda la conversación». En la sesión 3 ya aparecía en `construir_agente`; ahora se guarda en un fichero en disco, así que **sobrevive a que el programa se cierre**.

### 6.2 Time travel: bifurcar desde un estado anterior

```
                               ┌──► Estado 4   «¿qué producto?»   (original)
Estado 0 ──► Estado 2 ─────────┤
 inicio     Jorge pregunta     └──► Estado 4'  «soy Marta»        (--volver 2)
```

*Time travel* («viaje en el tiempo») es volver a un estado anterior y seguir desde ahí **por otro camino**. El camino original no se borra: se crea una rama nueva, como en git.

**Para qué sirve:**

- **Depurar:** reproducir la conversación desde el paso que falló, sin repetir todo lo anterior. Si el agente se equivocó en el paso 7, vuelves al 6 y miras qué pasa.
- **Corregir un dato sin empezar de cero:** en la demo, el cliente se equivocó de email. En vez de empezar otra conversación, se vuelve al punto anterior y se sigue con el dato bueno.
- **Probar alternativas:** desde el mismo punto, ver qué haría el agente con otra respuesta o con otro *prompt*.

---

## 7. Actividad: diseña la memoria

**Pensad en un agente de vuestra empresa** y responded:

1. ¿Qué debería recordar entre conversaciones?
2. ¿Qué no debería recordar nunca?
3. ¿Memoria por usuario, por cliente o compartida?
4. ¿Durante cuánto tiempo?

Un ejemplo (*ilustrativo, idea propia*) con `../../travel-agency/`, el agente de agencia de viajes:

| Pregunta | Respuesta posible |
|---|---|
| ¿Qué recordar? | Preferencias de viaje: «prefiere playa», «viaja con niños», «presupuesto medio», destinos que ya ha visitado |
| ¿Qué nunca? | Pasaporte, tarjeta, datos de salud que no hagan falta para el viaje |
| ¿Por quién? | Por cliente. Pero lo que aprende el agente sobre los destinos («este hotel suele dar problemas») sería memoria **compartida** del negocio |
| ¿Cuánto tiempo? | Las preferencias, mientras sea cliente activo; los episodios («preguntó por Tenerife en marzo»), unos meses |

---

## 8. Caso real: memoria visible

Los asistentes de consumo (ChatGPT, Claude, Gemini…) **ya recuerdan** cosas de sus usuarios. Y todos han llegado al mismo diseño de controles:

| Control | Qué permite al usuario |
|---|---|
| **Visible** | Consultar qué se recuerda de él |
| **Editable** | Corregir o borrar recuerdos concretos |
| **Desactivable** | Desactivar la memoria o usar chats sin ella |

> **La memoria se diseña junto con sus controles.**

### Idea clave

> **La memoria es una función de producto, no solo técnica.**
> Qué se recuerda, cuánto tiempo y quién lo controla son decisiones que afectan a la confianza del cliente.

Hacer que un agente recuerde es fácil (lo hemos hecho en 100 líneas). Lo difícil es decidir **qué** debe recordar y que el cliente se sienta cómodo con ello. Un agente que te sorprende con algo que no recordabas haberle contado da más miedo que ayuda.

---

## 9. Deberes para la sesión 5

Diapositiva «Deberes para la sesión 5». **No son evaluables**: se comentan al inicio de la próxima sesión. Ya tenemos la solución en `Solución deberes sesión 4/soluciones/sesion4/`.

### 9.1 Nivel base · Comprime el historial

**El enunciado:** cuando la conversación supere un número de tokens (estímalos como **caracteres / 4**), sustituye los mensajes antiguos por un **resumen** y conserva literales los últimos. **Cuidado: no separes una llamada a herramienta de su resultado.**

Es la estrategia **comprimir** de la sección 2.3: la conversación crece, y en vez de reenviarla entera en cada vuelta, lo antiguo se convierte en un resumen corto.

**La solución** (`deber_base.py`), en tres piezas:

1. **Contar tokens a ojo.** Suma los caracteres de todos los mensajes y divide entre 4. No es exacto, pero basta para decidir **cuándo** comprimir.
2. **Elegir el punto de corte.** Se quieren conservar los últimos 4 mensajes tal cual. Pero si el corte cae justo en el **resultado** de una herramienta, se mueve hacia atrás hasta incluir también la **llamada** que lo pidió.
3. **Resumir lo antiguo.** Todo lo que queda antes del corte se le pasa al modelo con la instrucción: «Resume esta conversación en 5 frases como máximo. **Conserva emails, números de pedido, importes y lo que el cliente ha pedido.**» Y el historial queda así:

```
[Resumen de la conversación anterior] ...   ← sustituye a los mensajes antiguos
mensaje reciente 1                          ← literales
mensaje reciente 2
...
```

**¿Por qué no se puede separar una llamada de su resultado?** Porque el modelo exige que cada resultado de herramienta vaya justo después de la llamada que lo pidió. Si el resumen se «come» la llamada y deja suelto su resultado, el modelo recibe una respuesta a una pregunta que no existe, y la API da error (o el agente se confunde). Por eso la llamada y su resultado son **inseparables**: o se resumen juntos o se conservan juntos.

**¿Por qué pedir que conserve emails, pedidos e importes?** Porque un resumen puede perder justo el dato que importa. «El cliente preguntó por un pedido» no sirve; «Marta (marta.lopez@email.com) preguntó por el pedido ORD-10544» sí. Es la lección que se repite en todo el tema: **lo que no está en el contexto, para el modelo no existe.**

### 9.2 Reto · Memoria con importancia

**El enunciado:** ahora todas las memorias valen lo mismo. Haz que el modelo **puntúe de 1 a 10 la importancia** de cada memoria al guardarla, y que la recuperación combine **similitud, recencia e importancia**.

Es la tercera forma de recuperar de la sección 5.2. Ejemplo de la solución: **una alergia importa más que «preguntó por el horario».** Con la puntuación de la demo, si las dos son igual de recientes y parecidas a la pregunta, empatan. No debería.

**La solución** (`deber_reto.py`) reutiliza la memoria de la demo y cambia solo dos cosas:

1. **Al guardar:** el extractor ahora pide, además del texto, una nota: «puntúa su importancia de 1 (trivial) a 10 (crítica para atenderle bien en el futuro)». La nota se guarda con el recuerdo.
2. **Al puntuar:** se mezcla la nota de antes (similitud + recencia) con la importancia:

```python
def puntuar(self, memoria, vector_consulta, ahora):
    base = super().puntuar(memoria, vector_consulta, ahora)   # similitud + recencia, como antes
    return 0.7 * base + 0.3 * memoria["importancia"] / 10
```

La importancia se divide entre 10 para que quede entre 0 y 1, como las otras dos. Si un recuerdo antiguo no tiene nota, se le da un 5 (neutro).

La idea viene del paper **«Generative Agents»** (Park et al., 2023), el de los personajes simulados que vivían en un pueblo virtual: cada recuerdo se recuperaba por **relevancia, recencia e importancia**.

Lo bonito de la solución: **no se toca la demo.** Se crea una versión nueva de la memoria que hereda todo lo anterior y solo cambia esas dos funciones. Es lo mismo que pasaba en los deberes de la sesión 2: reutilizar las piezas y escribir solo lo nuevo.

---

## Resumen de la sesión

- **El contexto es finito.** Más contexto no es mejor: se pierde lo del medio, cuesta dinero y es más lento. Y se reenvía entero en cada vuelta del bucle.
- **Cuatro estrategias** para decidir qué entra: **escribir** fuera, **seleccionar** lo relevante, **comprimir** lo antiguo y **aislar** en subagentes.
- **Memoria a largo plazo:** recuperar lo relevante → responder → extraer qué recordar. Se recupera por **similitud + recencia** (y en el reto, **importancia**). Los pesos son una decisión de diseño.
- **Estado ≠ memoria.** El estado es el marcapáginas de **una** conversación (pausar, reanudar, volver atrás). La memoria es la ficha del cliente para **todas** las conversaciones.
- **Checkpointing:** cada paso se guarda, así que se puede retomar una conversación tras cerrar el programa y hacer *time travel* para depurar o corregir.
- **Si recuerda, tiene que poder olvidar.** La memoria es un dato personal (RGPD): guardar lo mínimo, ser transparente y permitir borrarlo. Y tiene que ser **visible, editable y desactivable**.
- **La memoria es una decisión de producto**, no solo técnica: afecta a la confianza del cliente.
