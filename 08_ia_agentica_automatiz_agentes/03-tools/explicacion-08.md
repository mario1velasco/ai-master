# Sesión 3: Herramientas desde la perspectiva del agente

Explicación sencilla de la sesión 3 del Tema 8, centrada en las ideas principales. Se construye a partir de las capturas de clase y del código de `../tema8-agentes/sesion3/` y `../tema8-agentes/comun/`. Los ejemplos propios van marcados como *ilustrativos*.

---

## 0. Dónde estamos

| Sesión | Bloque | Qué se añade |
|---|---|---|
| 1 | Agente | Un agente desde cero |
| 2 | Planificar | ReAct y patrones de planificación |
| **3** | **Herramientas** | **LangGraph, APIs externas y MCP (esta sesión)** |
| 4 | Memoria | Contexto, memoria y estado |
| 5 | Equipos | Sistemas multiagente |
| 6 | Producción | Integración en la empresa |

En la sesión 1 construimos un agente a mano y en la 2 aprendimos a organizar cómo razona (planificar, revisar). Esta sesión mira las **herramientas**: cómo diseñarlas para que el agente las use bien, cómo conectarlo a APIs reales y cómo frenar las acciones peligrosas.


---

## 1. Corrección de los deberes de la sesión 2

### 1.1 Nivel base: reflexión sobre la síntesis

**El deber:** al plan-and-execute de la sesión 2 había que añadirle un crítico que revise la respuesta final antes de enviarla.

**La solución de clase** (`soluciones/sesion2/deber_base.py`), en resumen:

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

Las tres ideas de la diapositiva:

1. **Se reutilizan las piezas de las demos sin tocarlas.** Solo se escribe el «pegamento» entre planificar, ejecutar, sintetizar y criticar.
2. **El crítico revisa solo la respuesta final**, la que va a leer el cliente.
3. **Si el crítico la rechaza, solo se vuelve a redactar.** No se repiten las consultas a las herramientas: se reescribe la respuesta con los mismos datos y con los comentarios del crítico. Es barato.

**Lo que pasó en clase:** el crítico rechazó el primer borrador y la respuesta final sacó bien el pedido de Marta (`ORD-10544`), pero **no dijo que la crema hidratante no tiene stock**. En su lugar le pedía a Marta que confirmara los nombres de los productos.

**La lección:** reescribir con los mismos datos solo arregla la *forma* de la respuesta. Si falta un dato (aquí, el stock), el crítico no puede sacarlo de la nada, porque solo ve la respuesta, no los datos. Es la misma lección de la sesión 2.

### 1.2 Reto: replanificación ante fallos

**El deber:** en el plan-and-execute, si un paso falla (por ejemplo, el transportista no responde, que en Lumen Shop falla siempre a propósito), el plan sigue como si nada. Había que añadir un **verificador** que compruebe si cada paso se ha completado y, si no, pida al planificador **un plan nuevo para lo que queda**, con un **límite de replanificaciones** para no entrar en bucle.

La profesora ejecutó la solución (`soluciones/sesion2/deber_reto.py`) con «¿Dónde está el último pedido de marta.lopez@email.com?», pero no hay capturas de la explicación ni del resultado.

**La idea que hay detrás:** es la misma lección que en el nivel base, pero un paso antes. El crítico revisaba la respuesta final; el verificador revisa **cada paso** mientras se ejecuta, y si algo falla, se cambia el plan en vez de seguir adelante. Y como siempre, con un límite puesto por el código.

---

## 2. Herramientas para agentes

### 2.1 Idea clave: diseñad las herramientas para el agente

> **Diseñad las herramientas para el agente, no para el programador.**
> Igual que una interfaz se diseña para personas (UI), las herramientas son la interfaz del agente con el mundo: *agent-computer interface*.

Una web se diseña pensando en la persona que la usa, no en cómo está programada por dentro. Con las herramientas pasa lo mismo, pero el «usuario» es el agente. **El agente no ve el código**: solo ve el nombre de la herramienta, su descripción, sus parámetros y lo que devuelve. Esa es toda su «pantalla».

Por eso una función que a un programador le parece cómoda (un nombre corto, una abreviatura, una respuesta genérica) puede ser imposible de usar para el agente.

**El mal ejemplo de clase** (`sesion3/actividad_herramienta.py`): una herramienta llamada `fn_q`, con la descripción «Consulta.», que devuelve **todos los datos de la tienda** o, si no, «Error 500». El agente no sabe para qué sirve, recibe un montón de datos que no necesita y, si falla, no sabe por qué.

### 2.2 El modelo solo ve esto

```python
@tool
def consultar_pedido(id_pedido: str) -> dict:
    """[Lectura] Devuelve estado, productos, importe y número de
    seguimiento de un pedido (formato ORD-12345)."""
    return tienda.obtener_pedido(id_pedido)
```

Es la herramienta de siempre, escrita con `@tool` (de la librería LangChain). Este decorador crea automáticamente lo que lee el modelo a partir de la función: **el nombre de la función, su texto de descripción (docstring) y los parámetros**.

Las cuatro ideas de la diapositiva:

1. **Nombre: dice qué hace, no cómo.** `consultar_pedido`, no `fn_q`.
2. **Descripción: qué devuelve y cuándo usarla.**
3. **Parámetros: tipo y formato explícitos.** Decir «formato ORD-12345» evita que el modelo se invente otro formato.
4. **El cuerpo es invisible para el modelo.** La línea `return ...` no la ve nunca. Si algo no está en el nombre, la descripción o los parámetros, para el modelo no existe.

En resumen: **la descripción de la función ya no es solo un comentario para programadores; es el *prompt* de la herramienta.**

**`[Lectura]` es una categoría de riesgo.** Cada herramienta lleva una etiqueta que dice cuánto «daño» puede hacer:

| Categoría | Qué significa | Ejemplo |
|---|---|---|
| **Lectura** | Solo consulta, no cambia nada | consultar stock, pedido, cliente |
| **Escritura reversible** | Cambia algo que se puede deshacer | *ilustrativo:* cambiar la dirección de envío |
| **Escritura irreversible** | Cambia algo que no tiene vuelta atrás | emitir un reembolso |

Ojo: la etiqueta la lee el modelo, pero **no protege nada por sí sola**. Lo que de verdad frena un reembolso es el código, que pausa el agente y pide permiso a una persona (lo vemos en la sección 3).

### 2.3 Cuatro reglas de diseño

| Regla | Qué pide |
|---|---|
| **Descripciones claras** | Qué hace, cuándo usarla y cuándo no |
| **Granularidad** | Una herramienta por tarea con sentido de negocio |
| **Salidas acotadas** | Solo lo relevante, no 5.000 tokens de JSON |
| **Errores útiles** | Que el agente sepa cómo corregir la llamada |

**Descripciones claras.** Además de qué hace, decir **cuándo no usarla** evita confusiones cuando hay herramientas parecidas. *Ilustrativo:* «No la uses para saber dónde está un envío: para eso está `consultar_transportista`».

**Granularidad** es el «tamaño» de cada herramienta. Lo ideal es una herramienta por cada tarea que reconocería alguien del equipo: «consultar un pedido», «emitir un reembolso».
- Si es demasiado grande (`fn_q`, que lo hace todo), el agente no sabe usarla.
- Si es demasiado pequeña (*ilustrativo:* una herramienta por cada tabla de la base de datos), el agente tiene que encadenar muchas llamadas y cada una es una ocasión de equivocarse.

**Salidas acotadas.** Todo lo que devuelve una herramienta entra en la «memoria de trabajo» del modelo: cuesta dinero, tiempo y le distrae. Hay que devolver solo lo necesario. Si pregunto por un producto, me devuelve ese producto, no el catálogo entero.

**Errores útiles.** Cuando algo falla, el mensaje de error vuelve al modelo. Si el mensaje dice **qué hacer**, el agente puede corregirse. La diapositiva lo resume así:

> **«Formato esperado: ORD-12345»** frente a **«Error 404»**

Con el primero el agente sabe cómo reintentar; con el segundo solo sabe que algo ha ido mal, y puede insistir, rendirse o inventarse la respuesta.

Qué debería hacer el agente según el tipo de error:

| Qué pasa | Qué debe hacer | Ejemplo de error útil (del código del tema) |
|---|---|---|
| Ha escrito mal un dato | Corregirlo y reintentar | «Pedido no encontrado. El formato esperado es ORD-12345.» |
| El dato no existe, pero hay opciones | Elegir una opción válida | «Producto no encontrado» + la lista de productos disponibles |
| Un servicio externo no responde | No insistir; ofrecer una alternativa | «El servicio de divisas no responde. Da el precio en euros e indícalo al cliente.» |
| Ha repetido la misma llamada varias veces | Parar y explicárselo al cliente | «No lo intentes de nuevo: explica al cliente qué pasa» (reto de la sesión 1) |

La idea: **no todos los errores se arreglan reintentando.** Si el fallo es del agente, el error le dice cómo corregirse. Si el fallo es de fuera (una API caída), le dice qué hacer en su lugar, para que no insista ni se invente el dato.

### 2.4 APIs externas como herramientas

> Lo visto en el Tema 3, ahora con el agente como cliente.

En el Tema 3 (`../../03_API_Integracion_servicios/`) aprendimos a consumir APIs con scripts propios. Ahora quien llama a la API es el agente. Las precauciones son las mismas, en cuatro pasos:

```
Timeout ──► Rate limit ──► Errores traducidos ──► Salida limpia
```

| Paso | Qué significa |
|---|---|
| **Timeout** | Nunca esperar indefinidamente. Si la API no contesta en unos segundos, se da por fallida. Sin esto, el agente se quedaría colgado. |
| **Rate limit** | Las APIs limitan cuántas peticiones puedes hacer. Si te pasas, responden **429** («vas demasiado rápido»). Hay que esperar un poco y reintentar **una vez**. |
| **Errores traducidos** | Convertir el código técnico (404, 500…) en una frase que el agente entienda y le diga qué hacer. |
| **Salida limpia** | De todo lo que devuelve la API, pasar al agente solo los campos útiles. |

El ejemplo del código es `convertir_precio` (`comun/apis_externas.py`), que pasa precios de euros a otras monedas con una API pública real de tipos de cambio. Cumple los cuatro pasos.

**Lo nuevo respecto al Tema 3** es la pregunta de **quién arregla cada error**:
- **Que vas demasiado rápido (429)** → lo arregla **el código**: espera y reintenta sin que el agente se entere.
- **Que el agente pidió algo mal** (una moneda que no existe) → lo arregla **el agente**, gracias a un error que le explica cómo.
- **Que la API está caída** → no lo arregla nadie ahora mismo, así que el error le dice al agente **qué hacer en su lugar** (dar el precio en euros).

¿Por qué un solo reintento y no muchos, como en el Tema 3? (*interpretación propia*) Porque allí eran procesos por lotes que podían esperar; aquí hay un cliente esperando una respuesta en una conversación.

---

## 3. Demo: el agente en LangGraph

### 3.1 Qué es LangGraph

- **LangChain** es una librería de Python con **piezas** para trabajar con modelos de lenguaje: conectarse al modelo, convertir funciones en herramientas (`@tool`), manejar mensajes.
- **LangGraph**, del mismo equipo, sirve para construir **el bucle del agente** como un **grafo**: unas cajas unidas por flechas.

**LangChain pone las piezas; LangGraph pone el bucle que las une.** LangGraph no es una herramienta del agente: es otra forma de escribir el programa que lo hace funcionar.

Un grafo tiene:
- **Nodos** (cajas): cada uno hace un trabajo.
- **Flechas**: dicen a qué caja se pasa después. Algunas son fijas y otras dependen de lo que haya pasado.
- **Estado**: lo que va pasando de caja en caja. Aquí es **la conversación**, la lista de mensajes.

### 3.2 Del bucle manual a un grafo

```
                      pide
                ┌─────────────► herramientas
                │                     │
Inicio ──► agente ◄───────────────────┘
          (el LLM decide)              ▲
                │                      │ sí
                │  └──── sensible ──► aprobación
       responde │                  (pausa: un humano decide)
                ▼
               Fin
```

Es **el mismo bucle de la sesión 1**, solo que dibujado:

1. **agente**: el modelo lee la conversación y decide si pide una herramienta o responde. Es la única caja que «piensa».
2. Si **responde** → **Fin**.
3. Si **pide** una herramienta normal → **herramientas** la ejecuta y se vuelve al agente con el resultado.
4. Si pide una herramienta **sensible** (por ejemplo, emitir un reembolso) → **aprobación**: el programa **se pausa** y pregunta a una persona.
   - Si dice **sí**, se ejecuta.
   - Si dice **no** (la diapositiva no lo dibuja, pero el código lo tiene), el agente recibe «Acción rechazada por un supervisor humano» y se lo explica al cliente.

Aquí se ve lo que decíamos de la etiqueta `[Escritura irreversible]`: **quien protege no es la etiqueta, es el grafo.** La flecha «sensible» la decide el código, no el modelo.

**Qué ganamos** frente al bucle a mano:

1. **El estado se guarda en cada paso.** El agente recuerda la conversación y se puede retomar donde se quedó.
2. **Pausa para aprobación humana.** En el bucle de la sesión 1 no había forma de parar a mitad, preguntar a alguien y seguir después.
3. **Se puede dibujar y depurar.** El grafo se puede imprimir como diagrama (`sesion3/dibujar_grafo.py`).
4. **Base del resto del tema.** Las próximas sesiones (memoria, varios agentes, producción) se construyen sobre este mismo grafo, añadiendo cajas y flechas.

En resumen: **LangGraph no cambia qué es un agente, cambia cómo se escribe su bucle.** El bucle a mano sirve para entenderlo; el grafo sirve para ampliarlo sin que se convierta en un lío.

### 3.3 En directo: el agente con LangGraph

```bash
python -m sesion3.agente_langgraph
  > ¿Cuánto cuesta el sérum de vitamina C en dólares?
  > Soy jorge.ruiz@email.com, el pedido ORD-10598 llegó roto y quiero que me devolváis el dinero
```

Esta demo es una **conversación**: se escriben los mensajes uno a uno (y `salir` para terminar).

**Qué observar:**

- **La API de divisas en acción.** Para la primera pregunta el agente usa dos herramientas: consulta el precio del sérum (24,90 €) y lo convierte a dólares con la API real de tipos de cambio.
- **El grafo se pausa antes del reembolso.** En la segunda, el agente quiere emitir un reembolso. Antes de hacerlo, el programa se detiene y muestra: «⏸ El agente quiere ejecutar una acción irreversible… ¿Aprobar? (s/n)».
- **Rechazad con motivo y luego aprobad.** Si se rechaza, el agente recibe el motivo y se lo explica al cliente. Si se aprueba, el reembolso se emite. Así se ven los dos caminos de la caja «aprobación».

Un detalle curioso de los datos (`comun/tienda.py`): el pedido de Jorge (un protector solar de 15,90 €) figura como **«pendiente de envío»**, pero él dice que **llegó roto**. Ninguna herramienta compara las dos cosas, así que pillar esa incoherencia es justo el trabajo de la persona que aprueba.

**El código, en lo esencial.** El agente entero es una sola llamada que reúne las piezas:

```python
INSTRUCCIONES = ("Eres el agente de atención al cliente de Lumen Shop... "
                 "Consulta los datos con las herramientas y nunca los inventes. "
                 "Antes de emitir un reembolso, comprueba el pedido y que el importe "
                 "no supera su total. ...")
HERRAMIENTAS = TODAS + [convertir_precio]

def crear_agente(...):
    return construir_agente(modelo, HERRAMIENTAS, INSTRUCCIONES,
                            requieren_aprobacion=["emitir_reembolso"], ...)
```

- **Instrucciones**: el papel del agente y sus reglas. La regla del reembolso es un consejo para el modelo; la protección real es la pausa.
- **Herramientas**: las de consulta de la tienda, la de reembolso y la de divisas.
- **`requieren_aprobacion=["emitir_reembolso"]`**: la lista de herramientas que pasan por la caja de aprobación. **Esta línea es la que protege.**

El resto del fichero es la conversación por terminal: lee lo que escribe el cliente, se lo pasa al agente y, si el agente se ha pausado, pregunta «¿Aprobar? (s/n)» y continúa donde se quedó. Además lleva un **límite de pasos** (como el de la sesión 1) para que el agente no se quede en un bucle.

### 3.4 Ver el grafo dibujado

Como el agente es un grafo, **se puede dibujar solo**. El script `sesion3/dibujar_grafo.py` imprime el grafo como texto en formato **Mermaid** (un lenguaje para describir diagramas con texto):

```bash
python -m sesion3.dibujar_grafo
```

Si copias ese texto y lo pegas en **mermaid.ai** (o mermaid.live), aparece el dibujo. La profesora lo hizo en clase y salió esto:

```
            __start__
                │
                ▼
     ┌──────► agente ◄──────────────┐
     ┆        ┆    ┆                │
     ▼        ▼    ▼                │
  __end__  aprobacion ┄┄► herramientas
```

Es exactamente el diagrama de la diapositiva de la sección 3.2, pero generado por el propio programa:

- **`__start__` y `__end__`** son el Inicio y el Fin.
- **Flechas de puntos**: caminos que **se deciden en el momento**. Desde *agente* se puede ir al fin, a aprobación o a herramientas, según lo que pida el modelo. Desde *aprobación* se va a herramientas (sí) o se vuelve a agente (no).
- **Flechas continuas**: caminos **fijos**. Del inicio siempre se va al agente, y de herramientas siempre se vuelve al agente.

La idea: **lo que dibuja el diagrama es lo que hace el programa.** No es un dibujo hecho a mano que se pueda quedar desactualizado; si mañana se añade una caja al grafo, aparecerá en el dibujo. Por eso la diapositiva decía «se puede dibujar y depurar».

### 3.5 Las dos piezas reutilizables: `apis_externas.py` y `grafo.py`

La demo se apoya en dos ficheros de `comun/` que merece la pena entender bien, porque son **patrones que se pueden copiar a otro proyecto**: uno para envolver una API externa como herramienta y otro para construir el agente.

#### `comun/apis_externas.py`: la herramienta sobre la API

Diapositiva «La herramienta sobre la API»:

```python
@tool
def convertir_precio(importe_eur, moneda):
    """Convierte euros a otra moneda (USD, MXN...)."""
    try:
        r = httpx.get(URL, params=..., timeout=5)
    except httpx.HTTPError:
        return {"error": "El servicio no responde. Da el precio en euros."}
    if r.status_code == 429: esperar y reintentar
    return {"importe_convertido": ..., "fecha": ...}
```

(Versión resumida de la diapositiva; `httpx` es una librería para hacer peticiones HTTP, como `requests`.)

Son los cuatro pasos de la sección 2.4, ahora en código:

1. **Timeout explícito** (`timeout=5`): si la API no contesta en 5 segundos, se da por fallida. El agente nunca se queda colgado.
2. **El error dice al agente qué hacer**: no devuelve «HTTPError», devuelve «El servicio no responde. Da el precio en euros.». El agente sabe cómo seguir sin inventarse el tipo de cambio.
3. **Rate limit: un reintento**: si la API contesta 429 («vas demasiado rápido»), espera un poco y lo intenta **una** vez más. Si vuelve a fallar, devuelve un error. Esto lo resuelve la herramienta sola, sin molestar al agente.
4. **Salida reducida a lo útil**: de todo lo que devuelve la API, al agente solo le llegan el importe convertido, el tipo de cambio, la fecha y poco más.

El fichero real además traduce otros errores: si la moneda no existe, responde «Moneda no soportada. Usa un código ISO como USD o MXN.», para que el agente corrija la llamada.

**El docstring es lo que lee el agente.** En la diapositiva aparece recortado, pero en el fichero real es más completo, y con razón:

```python
"""Convierte un importe en euros a otra moneda con el tipo de cambio oficial del día.

Úsala cuando un cliente pregunte cuánto cuesta un producto en su moneda.
`moneda` es el código ISO de 3 letras: USD, GBP, MXN, CHF...
"""
```

Cada línea le resuelve una duda al agente:

| Línea del docstring | Qué le dice al agente |
|---|---|
| «Convierte un importe en euros a otra moneda…» | **Qué hace**: el importe que le pase tiene que estar en euros |
| «…con el tipo de cambio oficial del día» | **De dónde sale el dato**: es real y actual, no tiene que inventárselo |
| «Úsala cuando un cliente pregunte cuánto cuesta un producto en su moneda» | **Cuándo usarla**: sabe en qué situación elegirla |
| «`moneda` es el código ISO de 3 letras: USD, GBP, MXN, CHF…» | **Cómo rellenar el parámetro**: escribe `USD` y no «dólares» o «$» |

Sin este texto, el agente solo vería `convertir_precio(importe_eur, moneda)` y tendría que adivinar. Con él, sabe qué hace, cuándo usarla y cómo llamarla bien a la primera. Es la sección 2.2 en la práctica: **con `@tool`, el docstring deja de ser un comentario para programadores y se convierte en las instrucciones de la herramienta.** Escribirlo bien es tan importante como escribir bien el código de debajo, o más, porque el código el agente no lo ve.

**La idea para llevarse:** una herramienta sobre una API es **una capa de protección** entre el agente y el mundo exterior. Todo lo «feo» (esperas, reintentos, códigos HTTP) se queda dentro; al agente solo le llegan datos limpios o un error que entiende.

#### `comun/grafo.py`: el constructor del agente

Es el fichero que monta el grafo de la sección 3.2. Lo importante es que **es genérico**: no sabe nada de Lumen Shop. Recibe las piezas y devuelve un agente listo:

```python
construir_agente(
    modelo,                  # qué LLM usar
    herramientas,            # la lista de @tool
    instrucciones,           # el system prompt
    requieren_aprobacion=[...],  # qué herramientas pasan por un humano
    checkpointer=...,        # dónde se guarda la conversación
)
```

Por dentro hace tres cosas, que son las cajas del dibujo:

- **agente**: le pasa al modelo las instrucciones y la conversación, con las herramientas «enchufadas».
- **herramientas**: ejecuta las herramientas que pida el modelo (esta caja ya la trae LangGraph hecha).
- **aprobación**: si el modelo pide una herramienta de la lista `requieren_aprobacion`, **pausa** el programa y espera a que una persona diga sí o no. Si es que no, le devuelve al agente «Acción rechazada por un supervisor humano. Motivo: …».

Y una función de ayuda, `acciones_pendientes`, que le dice al programa «el agente está pausado esperando aprobación de esto».

**La idea para llevarse:** con este constructor, crear un agente distinto es solo cambiar las piezas (otras herramientas, otras instrucciones, otra lista de acciones sensibles). Por eso el README dice que es «el constructor del grafo que usaremos hasta la sesión 6».

#### ¿Y para travel-agency? (*ideas propias*)

Mirando `../../travel-agency/PROYECTO.md`, hay dos encajes claros:

- **El patrón de `apis_externas.py` sirve para cualquier herramienta que pueda fallar o tardar**, no solo para APIs de internet. En travel-agency, las herramientas `consultar_bbdd` (text2sql) y `buscar_documentos` (RAG) son locales, pero pueden tardar, dar error o devolver demasiado. Aplica igual: límite de tiempo, errores que digan al agente qué hacer («la consulta no es válida, prueba con…»), y devolver solo las filas o pasajes útiles. Si algún día se añade una API externa de verdad (tiempo, vuelos, divisas), el fichero es casi una plantilla.
- **El patrón de `grafo.py` encaja con el «escalar a humano».** En travel-agency esa decisión la toma el código (`domain/rules.py`), no el modelo, que es la misma filosofía de la caja de aprobación: **la protección la pone el código**. La diferencia es que allí no hay acciones peligrosas que aprobar (el agente solo consulta), así que no haría falta pausar; pero si en el futuro el agente pudiera *hacer* algo (cancelar una reserva, emitir un reembolso), esta es la forma de añadirle un humano en medio.

Antes de meter LangGraph en travel-agency habría que decidirlo con calma: el proyecto plantea su propio bucle del agente (fase 6 del roadmap), y LangGraph añade una dependencia más. Lo que sí se puede copiar ya, sin LangGraph, son las ideas: herramientas que se protegen solas y controles puestos por el código.

### 3.6 Clasificad las herramientas por riesgo

Diapositiva «Clasificad las herramientas por riesgo». Es la idea de las etiquetas `[Lectura]`, `[Escritura reversible]` y `[Escritura irreversible]` que van al principio del docstring de cada herramienta (sección 2.2), ahora con la regla de qué hacer con cada una:

| Categoría | Ejemplos | Qué control necesita |
|---|---|---|
| **Lectura** | `consultar_stock`, `consultar_pedido` | Ninguno. No cambia nada: **autonomía total** |
| **Escritura reversible** | Cambiar la dirección de envío | **Registrar** lo que hizo y **permitir deshacerlo** |
| **Escritura irreversible** | Reembolsos, envío de emails, borrados | **Aprobación humana** y **límites en código** |

Y la flecha de abajo lo resume: **más riesgo → más control.**

La pregunta para clasificar una herramienta es sencilla: **si el agente se equivoca, ¿qué pasa?**
- Si solo ha leído algo, no pasa nada: como mucho, una respuesta mala que se corrige.
- Si ha cambiado algo que se puede deshacer, basta con poder ver qué hizo y darle marcha atrás.
- Si ha hecho algo sin vuelta atrás (el dinero ya salió, el email ya se envió), hay que pararlo **antes**: que lo apruebe una persona, y que el código ponga límites (por ejemplo, *ilustrativo*: no reembolsar más que el total del pedido).

En la demo, solo `emitir_reembolso` es irreversible, y por eso es la única que está en `requieren_aprobacion`.

### 3.7 Humano en el bucle con `interrupt()`

Diapositiva «Humano en el bucle con interrupt()», con la caja de aprobación de `comun/grafo.py`:

```python
def aprobacion(estado):
    llamadas = estado["messages"][-1].tool_calls

    decision = interrupt({"acciones": llamadas})

    if decision["aprobar"]:
        return Command(goto="herramientas")
    return Command(goto="agente",
        update=rechazo(decision["motivo"]))
```

`interrupt` y `Command` son **dos piezas de LangGraph**:
- **`interrupt()`**: «para aquí y espera a un humano».
- **`Command`**: «sigue por este camino». Se usa para decidir a qué caja ir después (`goto`) y, al reanudar, para pasar la respuesta del humano (`resume`).

Leído en castellano: *coge las herramientas que quiere usar el agente, para y enséñaselas a una persona. Si dice que sí, ve a ejecutarlas. Si dice que no, vuelve al agente con el motivo del rechazo.*

Las tres ideas de la diapositiva:

1. **`interrupt()` pausa el grafo y guarda el estado.** El programa no se queda «esperando con la mano levantada»: guarda la conversación tal cual está y se detiene.
2. **Se reanuda horas después con `Command(resume=...)`.** Como el estado está guardado, la persona puede contestar cuando pueda (en la demo es al momento, por terminal; en una empresa podría ser un supervisor que lo revisa por la tarde). Al reanudar, el grafo sigue exactamente donde se quedó.
3. **Si se rechaza, el agente recibe el motivo y responde al cliente.** El rechazo no rompe nada: le llega al agente como el resultado de la herramienta («Acción rechazada por un supervisor humano. Motivo: …») y él se lo explica al cliente.

Esto es lo que el bucle a mano de la sesión 1 no podía hacer: **parar a mitad, esperar a una persona el tiempo que haga falta y seguir.**

---

## 4. MCP: ¿herramienta propia o servidor MCP?

MCP (*Model Context Protocol*) ya se vio en el **Tema 6** (`../../06_mcp/`): es un estándar para que un agente se conecte a herramientas que **viven fuera de su código**, en un programa aparte llamado **servidor MCP**. Es como un enchufe universal: cualquier agente o aplicación que «hable MCP» puede usar las herramientas de cualquier servidor MCP.

Como dice la diapositiva: **el Tema 6 explicó cómo funciona MCP; aquí decidimos cuándo usarlo.**

### 4.1 ¿Cuándo una herramienta propia y cuándo un servidor MCP?

| En el código del agente (`@tool`) | En un servidor MCP |
|---|---|
| Solo la usa **este** agente | La **reutilizan varios** agentes y clientes |
| Su lógica está ligada a la tarea del agente | La mantiene **el equipo dueño del sistema** |
| Prototipos y pruebas rápidas | Se **versiona y despliega aparte** |

Dicho de otra forma:
- **Herramienta propia**: es parte del agente. Rápida de hacer, pero si otro agente la necesita, tiene que copiarla.
- **Servidor MCP**: es un «servicio» aparte. Se escribe una vez y lo usa quien lo necesite. Y lo mantiene quien conoce el sistema: el equipo del CRM mantiene el servidor del CRM, no cada equipo que hace un agente.

Ejemplo *ilustrativo*: una herramienta que formatea la respuesta para Lumen Shop es propia del agente. Pero «consultar un pedido» la van a necesitar el agente de atención al cliente, el de devoluciones y el equipo desde su editor: mejor un servidor MCP de pedidos.

### 4.2 Aplicaciones de MCP en la empresa

| Aplicación | Qué significa |
|---|---|
| **Un servidor por sistema** | ERP, CRM o helpdesk expuestos **una vez** y usados por **todos** los agentes |
| **También en el IDE** | El equipo consulta pedidos desde Claude Desktop o su editor, con el mismo servidor |
| **Servidores ya hechos** | GitHub, Slack, bases de datos…: **conectar en lugar de programar** |
| **Recursos como contexto** | Políticas y documentación que el agente puede **leer** (no solo herramientas que ejecutar) |

Y el aviso del pie: **revisad los servidores de terceros como una dependencia más.** Conectar un servidor MCP que ha hecho otro es como instalar una librería: le das acceso a tu agente, así que hay que mirar quién lo mantiene, qué hace y qué permisos tiene.


### 4.3 Demo: MCP en la práctica

#### Lumen Shop expuesto por MCP (`sesion3/servidor_mcp.py`)

```python
servidor = FastMCP("lumen-shop")

@servidor.tool()
def consultar_stock(producto: str) -> dict:
    """[Lectura] Precio y unidades disponibles."""
    return tienda.consultar_stock(producto)

servidor.run(transport="stdio")
```

Se parece muchísimo a una herramienta con `@tool` (sección 2.2). La diferencia es que aquí las funciones no forman parte de un agente: forman parte de un **servidor**, un programa aparte que ofrece sus herramientas a quien se conecte.

- **`FastMCP("lumen-shop")`** crea el servidor y le pone nombre.
- **`@servidor.tool()`** convierte cada función en una herramienta del servidor.
- **`servidor.run(transport="stdio")`** lo arranca. `stdio` significa que el servidor y el agente se hablan por la entrada y salida estándar, como dos programas conectados por una tubería: el agente lanza el servidor y se comunican por ahí.

Las tres ideas de la diapositiva:

1. **El sistema de la tienda, expuesto una sola vez.** Se escribe el servidor una vez y cualquiera puede usarlo.
2. **Cada función decorada es una herramienta.** Igual que con `@tool`.
3. **El docstring es lo que verá cualquier cliente: agente, IDE o Claude Desktop.** Lo mismo que en la sección 3.5, pero multiplicado: ahora no lo lee solo nuestro agente, lo lee cualquiera que se conecte. Por eso escribirlo bien importa todavía más.

En nuestro repo, el servidor ofrece dos herramientas de lectura: `consultar_stock` y `consultar_pedido`. Solo de lectura: las acciones peligrosas no se exponen a cualquiera.

#### En directo: un agente, varias fuentes (`sesion3/agente_mcp.py`)

```bash
python -m sesion3.agente_mcp "¿Cuánto cuesta el contorno de ojos en dólares y cuántas unidades quedan?"
```

Este agente junta herramientas de **dos sitios**:
- Del **servidor MCP**: `consultar_stock` y `consultar_pedido`. El agente no las tiene en su código: al arrancar, se conecta al servidor y le pregunta «¿qué herramientas tienes?».
- **Locales**: `convertir_precio`, la de divisas (sección 3.5), que está en el propio código del agente.

Y luego usa el mismo `construir_agente` de siempre (sección 3.5) con todas juntas. **Para el agente, una herramienta remota y una local son iguales**: solo ve nombre, descripción y parámetros.

**Qué observar**, según la diapositiva:

- **Combina herramientas del servidor y una local (divisas).** Al arrancar imprime las dos listas: «🔌 Herramientas del servidor MCP: …» y «🧰 Herramientas locales: ['convertir_precio']».
- **Añadimos una herramienta al servidor: el agente la usa sin tocar su código.** Esta es la idea fuerte de MCP.
- **El mismo servidor, conectado a Claude Desktop o al IDE.** El `sesion3/README.md` explica cómo: se añade el servidor al fichero de configuración de Claude Desktop y desde ahí se puede preguntar por el stock o los pedidos.

#### Lo que pasó en clase

**Primera ejecución**, con la pregunta del contorno de ojos. Respuesta del agente:

> El contorno de ojos cuesta 21.0 euros y hay 47 unidades disponibles. En dólares, el precio sería aproximadamente 11.13 USD.

El precio en euros y las unidades son correctos (`comun/tienda.py`). Pero **los dólares no cuadran**: un euro vale más de un dólar, así que 21 € deberían ser algo más de 21 $, no 11. El modelo se ha equivocado en la conversión o al pasar el importe a la herramienta. Recordatorio de siempre: **hay que leer la respuesta y comprobarla, aunque suene segura.**

**Por qué pasa: preguntas que necesitan varias herramientas encadenadas.** Esta pregunta obliga al agente a hacer dos cosas en orden: primero `consultar_stock` para saber el precio en euros, y luego `convertir_precio` **con ese precio**. Es un paso más difícil que usar una sola herramienta, y en desarrollo es habitual que el agente falle aquí: se salta una herramienta, la llama con un dato equivocado o se inventa el resultado. Con modelos pequeños, más.

Qué se puede hacer:

- **Mejorar el *prompt* del agente** (las instrucciones). Por ejemplo, *ilustrativo*: «Si el cliente pide un precio en otra moneda, primero consulta el precio en euros con `consultar_stock` y después conviértelo con `convertir_precio`. Nunca calcules el cambio tú».
- **Poner ejemplos** en las instrucciones: una pregunta de muestra y los pasos que debería seguir. Ver un caso resuelto ayuda mucho al modelo a copiar el patrón.
- **Mejorar las descripciones de las herramientas** (sección 2.3): que cada una diga cuándo usarla y qué necesita. Si `convertir_precio` dice «el importe tiene que estar en euros», el agente entiende que antes tiene que conseguirlo.
- **Probar con varias preguntas y comprobar las respuestas**, no fiarse de una ejecución que «parece» bien.

**Segunda ejecución: la profesora añadió una herramienta al servidor.** En su versión de `servidor_mcp.py` añadió `productos_sin_stock` (en nuestro repo no está; es lo que pide el reto de los deberes). Sin tocar `agente_mcp.py`, volvió a ejecutar:

```bash
python -m sesion3.agente_mcp "¿Qué productos están agotados?"
```

Y el agente ya la veía y la usó:

```
🔌 Herramientas del servidor MCP: ['consultar_stock', 'consultar_pedido', 'productos_sin_stock']
🧰 Herramientas locales: ['convertir_precio']
🤖 El producto "crema hidratante" está actualmente agotado en nuestro catálogo. ...
```

Correcto: la crema hidratante es el único producto con 0 unidades.

**La lección de la demo:** con MCP, **las herramientas se mantienen en un sitio y los agentes las descubren solos.** Si el equipo de la tienda añade o mejora una herramienta en su servidor, todos los agentes (y Claude Desktop, y el IDE) la tienen en la siguiente ejecución, sin cambiar una línea de su código. Es lo que la sección 4.1 llamaba «la mantiene el equipo dueño del sistema».

---

## 5. Actividad: ¿cuánto control?

No hay capturas del enunciado. Por el título y el lugar en que aparece (justo después de clasificar herramientas por riesgo y del humano en el bucle), va de decidir **cuánto control necesita cada herramienta**. Un ejercicio para practicarlo (*mío, ilustrativo*), aplicando la tabla de la sección 3.6:

| Herramienta | Riesgo | Control |
|---|---|---|
| Consultar el estado de un pedido | Lectura | Ninguno: autonomía total |
| Cambiar la dirección de envío de un pedido aún no enviado | Escritura reversible | Registrar el cambio y permitir deshacerlo |
| Enviar un email de disculpa al cliente | Escritura irreversible (el email ya no se puede «des-enviar») | Aprobación humana, o al menos plantillas fijas |
| Emitir un reembolso | Escritura irreversible | Aprobación humana y límite en código (nunca más que el total del pedido) |
| Borrar la cuenta de un cliente | Escritura irreversible | Aprobación humana; probablemente, que el agente ni siquiera la tenga |

La pregunta que guía todo: **si el agente se equivoca, ¿qué pasa y se puede arreglar?** Y una idea extra: la forma más segura de controlar una herramienta peligrosa a veces es **no dársela al agente**.

---

## 6. Deberes para la sesión 4

Diapositiva «Deberes para la sesión 4». **No son evaluables**: se comentan al inicio de la próxima sesión. La solución se publica tras la sesión 4.

### Nivel base · Rediseña dos herramientas

Es poner en práctica las **reglas de diseño** de la sección 2.3:

1. **`buscar_cliente` solo devuelve números de pedido** → haz que devuelva **un resumen de cada pedido**. Ahora, para saber algo de un pedido, el agente tiene que hacer una llamada más por cada uno. Si `buscar_cliente` ya trae el resumen (estado, productos, total…), se ahorra esas llamadas. Es la regla de **granularidad**: que la herramienta devuelva lo que el agente necesita de verdad para su tarea.
2. **`consultar_stock` falla con nombres parciales** → haz que acepte «serum» y **ofrezca opciones si hay varias**. Ahora, si el cliente dice «serum» en vez de «serum vitamina c», la herramienta responde «no encontrado». Es la regla de **errores útiles**: en vez de fallar, que encuentre el producto o le diga al agente «¿te refieres a alguno de estos?».

Después, **compara cuántas llamadas hace el agente antes y después**. Es la forma de comprobar que el rediseño sirve: menos llamadas significa menos tiempo, menos coste y menos ocasiones de equivocarse.

Punto de partida: `comun/herramientas_lc.py`.

### Reto · Amplía el servidor MCP

**Añade al servidor de Lumen Shop una herramienta nueva y un recurso MCP con la política de devoluciones, y conecta el agente a tu servidor.**

- **La herramienta nueva** es lo que hizo la profesora en la demo con `productos_sin_stock` (sección 4.3): se añade al servidor y el agente la usa sin tocar su código.
- **El recurso MCP** es lo nuevo. Un recurso no es algo que se *ejecuta* sino algo que se *lee*: un documento que el servidor pone a disposición del agente. Es lo que la sección 4.2 llamaba «recursos como contexto»: políticas y documentación que el agente puede leer. Aquí, la política de devoluciones, para que el agente sepa qué puede prometer a un cliente que quiere devolver algo.
- **Opcional:** si usas Claude Desktop o un IDE con MCP, conecta también ahí el servidor siguiendo `sesion3/README.md`.

Punto de partida: `sesion3/servidor_mcp.py` y `sesion3/agente_mcp.py`.

### Lectura recomendada: el paper de ReAct

*ReAct: Synergizing Reasoning and Acting in Language Models* (Yao et al., 2022): https://arxiv.org/abs/2210.03629. Basta con la introducción y los ejemplos de trazas.

**Por qué leerlo** (diapositiva): es **el artículo que dio origen al patrón que usan hoy todos los agentes**. Hay que leerlo con ojo crítico, porque ya sabemos cómo se usa hoy.

**En qué fijarse**, con lo que ya sabemos de la sesión 2 (sección 2 de `../02-ReAct-patrone-planificacion/explicacion-08.md`):

| Pregunta | Pista para la lectura |
|---|---|
| **¿Qué problema resolvía de Chain-of-Thought?** | Chain-of-Thought («piensa paso a paso») razona, pero solo con lo que el modelo lleva en la memoria: no consulta nada, así que **se inventa datos**. ReAct intercala pensar con **actuar** (consultar algo fuera) y ver el resultado, para que el razonamiento se apoye en datos reales. |
| **¿Cómo eran las herramientas en 2022?** | Muy simples y escritas como **texto en el *prompt***. En el paper, el agente usa una API de Wikipedia con acciones del estilo `search[...]`, `lookup[...]` y `finish[...]`. El modelo las escribía como texto y un programa las leía: es lo que hicimos a mano en `sesion2/react_prompting.py`, con su *parser* frágil. |
| **¿Qué ha cambiado con el tool calling nativo?** | Hoy la API del modelo recibe las herramientas con su esquema y devuelve **llamadas estructuradas**: ya no hace falta pedirle que escriba «Acción: …» ni leerlo con expresiones regulares. El «Pensamiento» se ha vuelto interno. Y, como hemos visto en esta sesión, ahora las herramientas se diseñan con cuidado (descripciones, errores útiles, riesgo), se conectan a APIs reales y se comparten por MCP. **El bucle pensar → actuar → observar es el mismo; lo que ha cambiado es todo lo que lo rodea.** |

---

## 7. Avance: el proyecto `tema8-mlflow`

Al final de la clase la profesora enseñó un repositorio nuevo, **`tema8-mlflow`**, que nos pasará en unos días para que lo entendamos. *Esta sección se completará cuando lo tengamos.*

**Qué es MLflow**, en una frase: una herramienta para **registrar y revisar lo que hace un sistema de IA**: cada ejecución, sus parámetros, sus resultados y sus métricas. Ya apareció en la sesión 2 como forma de «registrar trazas y métricas» en producción.

Lo que se vio en la captura del editor:

- **Ficheros numerados, uno por demo:** `01_trazas.py`, `02_experimento.py`, `03_comparar.py` y `04_evaluar.py`. Por los nombres (*suposición* hasta tener el código): ver trazas, organizar experimentos, comparar versiones y evaluar respuestas.
- **Una carpeta `lumen/`** con el agente de Lumen Shop (`agente.py`, `experimento.py`, `casos.py`…).
- **`mlruns/` y `mlflow.db`**: donde MLflow guarda lo que registra.

**`01_trazas.py` — «Trazas: ver por dentro qué hace el agente».** Según su docstring, ejecuta una pregunta y deja en MLflow **la traza completa**: el paso del agente, **cada llamada al modelo** (con su *prompt*, su respuesta y sus tokens) y **cada herramienta** (con sus argumentos y su resultado). La pregunta por defecto es «Quiero 10 protectores solares spf50, ¿tenéis suficientes?» (el caso de las 8 unidades de la sesión 2). Al terminar imprime la respuesta, los pasos, los tokens, el tiempo y las herramientas usadas, y dice dónde ver la traza: en la interfaz de MLflow, experimento «Tema 8 · Agente Lumen Shop» → pestaña *Traces*.

**Por qué importa:** en esta sesión hemos visto respuestas que «sonaban bien» pero estaban mal (los 11,13 USD de la sección 4.3) sin poder ver qué había hecho el agente por dentro. Una traza permite **ver cada paso**: qué herramienta llamó, con qué datos y qué le devolvió. Así se encuentra dónde se equivocó.

---

## Resumen de la sesión

- **Las herramientas son la interfaz del agente.** El agente no ve el código: solo el nombre, la descripción (docstring), los parámetros y lo que devuelve. Hay que diseñarlas para él.
- **Cuatro reglas:** descripciones claras, una herramienta por tarea de negocio, salidas cortas y errores que digan qué hacer.
- **APIs externas:** *timeout*, reintento ante 429, errores traducidos y salida limpia. Todo lo «feo» se queda dentro de la herramienta.
- **LangGraph** escribe el mismo bucle de la sesión 1 como un grafo. Así se le pueden añadir cosas, como una **pausa para que un humano apruebe**.
- **Más riesgo → más control.** Lectura: autonomía. Escritura reversible: registrar y deshacer. Irreversible: aprobación humana y límites. **Lo que protege es el código, no la etiqueta.**
- **MCP** sirve para compartir herramientas entre varios agentes y aplicaciones. Se mantienen en un sitio y los agentes las descubren solos.
- **Siempre hay que comprobar las respuestas.** En esta sesión vimos varias que sonaban bien y estaban mal: el deber base sin stock y los dólares de la demo MCP.
