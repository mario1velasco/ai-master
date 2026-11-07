# Sesión 5: Sistemas multiagente

Explicación sencilla de la sesión 5 del Tema 8, centrada en las ideas principales. Se construye a partir del PDF de la sesión (`Tema8_Sesion5_Sistemas_multiagente.pdf`), del código de `../tema8-agentes/sesion5/` y de la solución de los deberes (`Solución deberes sesión 5/`). Los ejemplos propios van marcados como *ilustrativos*. Los resultados «en mi máquina» son de ejecutar las demos con `qwen3:4b-instruct` en local (4-11-2026): con otro modelo saldrán otros números.

---

## 0. Dónde estamos

| Sesión | Bloque | Qué se añade |
|---|---|---|
| 1 | Agente | Un agente desde cero |
| 2 | Planificar | ReAct y patrones de planificación |
| 3 | Herramientas | LangGraph, APIs externas y MCP |
| 4 | Memoria | Contexto, memoria y estado |
| **5** | **Equipos** | **Sistemas multiagente (esta sesión)** |
| 6 | Producción | Integración en la empresa |

Hasta ahora había **un solo agente** que lo hacía todo: clasificar el ticket, consultar los pedidos y redactar la respuesta. Esta sesión responde a tres preguntas:

1. **¿Cuándo compensa repartir el trabajo entre varios agentes?** (y cuándo no).
2. **¿Cómo se organizan y se hablan entre ellos?** (patrones y comunicación).
3. **¿Cuánto cuesta un equipo frente a un agente solo?** (tokens, tiempo y fallos nuevos).

### Los ficheros de la práctica (`../tema8-agentes/sesion5/`)

Esta vez es **un solo fichero**, `equipo_supervisor.py`: **un equipo de atención al cliente con un jefe**. Llega un ticket y un **supervisor** decide, paso a paso, qué miembro del equipo trabaja a continuación:

| Agente | Qué hace | ¿Tiene herramientas? |
|---|---|---|
| **Supervisor** | Lee el ticket y lo que ya han hecho los demás, y decide quién sigue (o si se ha terminado) | No |
| **Clasificador** | Dice qué tipo de incidencia es (retraso, producto dañado, stock…), su urgencia, y saca el email y el pedido | No |
| **Logística** | Consulta los datos reales: pedidos, stock, transportista. Es el agente con herramientas de la sesión 3, solo con las de **lectura** | Sí |
| **Redactor** | Escribe la respuesta al cliente con lo que han averiguado los demás. Siempre es el último | No |

Cómo trabaja, en palabras normales:
- Hay una **ficha común** del ticket. Cada agente, al terminar, apunta en ella **su conclusión** (una «nota») y los **tokens** que ha gastado.
- Después de cada agente se vuelve al supervisor, que mira la ficha y decide el siguiente.
- Se acaba cuando el redactor ha escrito la respuesta o cuando se llega a **6 pasos** (protección contra bucles).
- Al final se imprime cuántos tokens ha gastado cada agente.

Las soluciones de los deberes añaden dos ficheros más (en `Solución deberes sesión 5/soluciones/sesion5/`):

| Fichero | Qué hace, en una frase |
|---|---|
| `deber_base.py` | Añade al equipo un **cuarto agente, el de devoluciones**, que aplica la política y propone un reembolso sin emitirlo |
| `deber_reto.py` | Resuelve el **mismo ticket con un agente solo y con el equipo**, y compara los tokens |

**Cómo ejecutarlos:**
- La demo, desde `tema8-agentes/` con el entorno activado: `python -m sesion5.equipo_supervisor "…"`.
- Las soluciones están fuera de `tema8-agentes/`, así que hay que decirle a Python dónde buscarlas (o copiar la carpeta `soluciones/` dentro de `tema8-agentes/`):

```bash
cd tema8-agentes
PYTHONPATH=".:../05-sistemas-multiagente/Solución deberes sesión 5" python -m soluciones.sesion5.deber_base "…"
```

---

## 1. Corrección de los deberes de la sesión 4

Se explican con detalle en `../04-memoria-contexto-estado/explicacion-08.md` (sección 9). Lo que la diapositiva destaca:

**Nivel base: comprimir sin romper.**
1. **Solo se comprime cuando hace falta**: si la conversación no pasa del límite de tokens, se deja como está.
2. El resumen **conserva emails, pedidos e importes**.
3. **El error típico**: cortar entre una llamada a herramienta y su resultado, dejando un resultado «huérfano». La API lo rechaza. Por eso el punto de corte se mueve hacia atrás hasta incluir la llamada.

**Reto: la importancia como tercer factor.** La puntuación de un recuerdo pasa a mezclar **similitud** con la pregunta, **recencia** e **importancia** (de 1 a 10, la pone el modelo al guardar). Una alergia pesa más que «preguntó por el horario».

---

## 2. ¿Por qué varios agentes?

### 2.1 Lo que aporta un equipo

| Ventaja | Qué significa |
|---|---|
| **Especialización** | Cada agente tiene **su prompt y sus herramientas**, pensados para una sola tarea |
| **Contextos separados** | Cada uno trabaja **solo con lo que necesita**, sin el ruido de lo que hacen los demás |
| **Paralelismo** | Las subtareas independientes se pueden hacer **a la vez** |

> Es la estrategia **«aislar»** de la sesión 4 llevada al diseño del sistema.

En la sesión 4 vimos que el contexto es finito y que lo que está en medio se pierde. Un equipo es una forma de que **ningún agente tenga que cargar con todo**: el redactor no necesita leerse los JSON de los pedidos, solo la conclusión.

### 2.2 Lo que cuesta

El dato de la diapositiva: el sistema multiagente de investigación de Anthropic consumía **unas 15 veces más tokens que un chat** (un agente solo, unas 4 veces).

A cambio:
- Da **mejor resultado en tareas de investigación amplias**.
- **Solo compensa si el valor de la tarea lo justifica.**
- La **latencia** y la **depuración** también se complican: hay más llamadas y, si algo sale mal, hay que averiguar qué agente se equivocó.

### 2.3 El debate: ¿construir multiagente o no?

En 2025 se publicaron, casi a la vez, dos artículos que parecían decir lo contrario:

| A favor (Anthropic) | En contra (Cognition, los de Devin) |
|---|---|
| Tareas **amplias y paralelizables** | «*Don't build multi-agents*» («no construyáis multiagentes») |
| Investigar muchas fuentes a la vez | Tareas **muy acopladas**, como programar |
| Cada subagente explora una línea | Al repartir **se pierde contexto** y salen **decisiones incoherentes** |

**Los dos tienen razón, en tareas distintas.** Investigar es fácil de repartir: cada subagente busca por su lado y al final se junta. Programar no: si un agente hace el diseño de la base de datos y otro la pantalla, sin compartir cada decisión, las piezas no encajan.

### 2.4 Regla práctica

> **Varios agentes para tareas amplias y paralelas; uno solo para tareas acopladas.**
>
> Empezad siempre con un agente. Pasad a un equipo cuando tengáis un problema concreto que lo justifique: **contexto saturado, especialización o paralelismo.**

---

## 3. Demo: un equipo con supervisor

### 3.1 El diseño

```
                          ┌──► Clasificador (sin herramientas) ──┐
Ticket ──► Supervisor ────┼──► Logística (con herramientas) ─────┤
           (decide quién  └──► Redactor (respuesta final) ───────┤
            sigue)  ▲                                            │
                    └────────── cada agente vuelve ──────────────┘
                                hasta que el supervisor dice FIN
```

Las cuatro claves del diseño (diapositiva):

1. **Cada agente vuelve al supervisor.** Nadie le pasa el trabajo directamente a otro: siempre decide el jefe.
2. **El redactor no ve las llamadas de logística, solo su conclusión.** Contextos separados.
3. **Máximo de pasos contra bucles** (6).
4. **Tokens medidos por agente**, para saber cuánto cuesta cada uno.

**¿Cómo sabe el supervisor a quién llamar?** Por una **descripción de una línea** de cada agente, igual que el modelo elige herramientas por su descripción en la sesión 3. El supervisor recibe algo así:

```
Tu equipo:
- clasificador: identifica tipo de incidencia, urgencia, email y pedido
- logistica: consulta pedidos, envíos y stock con herramientas
- redactor: redacta la respuesta final al cliente; siempre es el último
Decide quién trabaja a continuación. Responde solo con JSON: {"siguiente": "<agente> o FIN", "motivo": "..."}
```

Y si el supervisor contesta algo que no es JSON, el código no se rompe: manda al redactor a cerrar el ticket.

### 3.2 En directo: el equipo resuelve un ticket

Dos tickets. **Qué observar**: las decisiones del supervisor en cada paso, la tabla de tokens por agente, y la segunda pregunta: **¿necesitaba un equipo?**

**Ticket 1:** «Soy marta.lopez@email.com. Mi pedido ORD-10544 no llega y lo necesito para un regalo el viernes.»

En mi máquina:

```
🧭 Supervisor → clasificador: Debo identificar el tipo de incidencia, urgencia, email y pedido…
🧭 Supervisor → logistica: Se necesita verificar el estado del pedido ORD-10544…
🧭 Supervisor → redactor: Se ha completado la clasificación y la consulta logística…

📊 Tokens por agente: redactor 411 · supervisor 920 · logistica 1552 · clasificador 154 · total: 3037
```

- El supervisor sigue el orden lógico: **clasificar → consultar → redactar**.
- **Logística es la que más gasta** (la mitad): es la única que usa herramientas y da varias vueltas.
- **El supervisor es el segundo**, y no hace nada «útil» por sí mismo: es el **coste de coordinar**. Se le llama antes de cada agente.
- Tardó **1 minuto y 42 segundos**.

**Un fallo que merece la pena ver:** la respuesta final a Marta habla de un número de seguimiento «TRK-12345» que no es el suyo (el real es TRK-58873) y le da un teléfono de soporte que no está en ningún sitio. El redactor tiene la orden de usar «SOLO los hechos de las notas del equipo», pero solo ve lo que logística le resume. Si el resumen viene mal, el redactor no tiene forma de comprobarlo. Es la **pérdida de contexto al delegar** (sección 5.3): el precio de los contextos separados.

**Ticket 2:** «¿Os queda crema hidratante?»

```
🧭 Supervisor → clasificador … → logistica … → redactor …
📊 Tokens por agente: clasificador 113 · supervisor 690 · logistica 1163 · redactor 191 · total: 2157

✉️  Lo siento, actualmente no queda stock de crema hidratante en nuestro almacén.
```

**Más de 2.000 tokens y 45 segundos** para responder «no queda» (la crema tiene 0 unidades). Para esta pregunta bastaba **una consulta de stock**: un agente solo, o incluso un workflow. **No todo ticket merece un equipo.**

### 3.3 Cada agente, su contexto

La diapositiva enseña el redactor, recortado a lo esencial:

```python
def redactor(estado):
    respuesta = modelo.invoke([
        SystemMessage(PROMPT_REDACTOR),                       # 1. su propio prompt
        HumanMessage(f"Ticket: {estado['ticket']}"            # 2. solo el ticket
                     f"Notas: {resumen_notas(estado)}")])     #    y las notas del equipo
    return {"respuesta": respuesta.content,
            "tokens": {"redactor": tokens_de(respuesta)}}     # 4. suma sus tokens a la ficha
```

1. **Su propio prompt.**
2. **Solo recibe el ticket y las notas del equipo.**
3. **Nada de llamadas a herramientas ni trazas ajenas.**
4. **Cada agente suma sus tokens al estado.**

Las «notas» son una línea por agente. Lo que lee el redactor es, más o menos (*ilustrativo*):

```
Ticket: Soy marta.lopez@email.com. Mi pedido ORD-10544 no llega…
Notas del equipo:
[clasificador] {"tipo": "retraso", "urgencia": "alta", "email": "marta.lopez@email.com", "pedido": "ORD-10544"}
[logistica] El pedido ORD-10544 está en tránsito… (3 frases de hechos)
```

### 3.4 El código por dentro: para qué sirve LangGraph aquí

**Sin LangGraph** tendrías que escribir a mano el «director de orquesta»: un bucle que pregunte al supervisor, llame al agente elegido, junte lo que devuelve con lo anterior, vuelva al supervisor y pare a tiempo.

**Con LangGraph** solo escribes **los agentes, como funciones normales**, y dibujas **quién va después de quién**. LangGraph se encarga de mover el ticket de uno a otro, de **juntar** lo que aporta cada uno en una ficha común y de parar.

Se usa en cuatro pasos.

**1. Definir la ficha común (`EstadoEquipo`)**

```python
class EstadoEquipo(TypedDict, total=False):
    ticket: str
    notas: Annotated[dict, operator.or_]       # cada agente AÑADE su nota
    tokens: Annotated[dict, sumar_dicts]       # los tokens se SUMAN por agente
    historial: Annotated[list, operator.add]   # la lista de quién ha trabajado CRECE
    siguiente: str                             # la decisión del supervisor (se sustituye)
    respuesta: str                             # el texto final (se sustituye)
```

Son las casillas que se pasan los agentes. Lo importante es **`Annotated`**: le dice a LangGraph **cómo juntar** lo nuevo con lo que ya había. Sin él, la nota de logística **borraría** la del clasificador; con `operator.or_`, se quedan las dos.

**2. Escribir cada agente como una función: recibe la ficha y devuelve solo su parte**

```python
def redactor(estado):
    respuesta = modelo.invoke([SystemMessage(prompt),                 # sus instrucciones
                               HumanMessage(ticket + notas)])         # solo ticket y notas
    return {"respuesta": respuesta.content, "tokens": {"redactor": ...}, "historial": ["redactor"]}
```

`SystemMessage` y `HumanMessage` son el `system` y el `user` de la sesión 1. Cada agente monta **su propia** lista de mensajes; por eso nadie ve el historial de los demás. Logística es la excepción: dentro lleva un agente completo de la sesión 3 (`construir_agente`), pero a la ficha solo pasa su conclusión.

El supervisor es otra función igual, que devuelve `{"siguiente": "logistica"}` o `"FIN"`. **No llama a nadie: solo apunta quién va después.**

**3. Dibujar el grafo (`construir_equipo`)**

```python
grafo = StateGraph(EstadoEquipo)                        # hoja en blanco, con la ficha
grafo.add_node("supervisor", supervisor)                # una caja
for nombre, (_, fabrica) in agentes.items():
    grafo.add_node(nombre, fabrica(modelo))             # una caja por agente
    grafo.add_edge(nombre, "supervisor")                # flecha fija: siempre vuelve al jefe
grafo.add_edge(START, "supervisor")                     # se empieza por el jefe
grafo.add_conditional_edges("supervisor",               # rombo: tras el jefe, ¿a dónde?
    lambda e: END if e["siguiente"] == "FIN" else e["siguiente"],
    list(agentes) + [END])
equipo = grafo.compile()                                # listo para ejecutar
```

| Pieza | Qué es |
|---|---|
| `add_node` | Una **caja**: un nombre y la función que se ejecuta |
| `add_edge(a, b)` | Una **flecha fija**: después de `a`, siempre `b` |
| `add_conditional_edges` | Un **rombo**: una función mira la ficha y devuelve el nombre de la siguiente caja |
| `compile()` | Pasa el dibujo a algo ejecutable |

El resultado:

```
START ──► supervisor ◄─────────────┐
            ├──► clasificador ─────┤
            ├──► logistica ────────┤
            ├──► redactor ─────────┘
            └──► END  (si «siguiente» = FIN)
```

El `for` monta **las cajas que haya en el registro `AGENTES`**. Por eso añadir un agente es añadir una línea (sección 6.1).

**4. Ejecutar**

```python
equipo.invoke({"ticket": "...", "notas": {}, "tokens": {}, "historial": []})
```

Con el ticket de Marta: supervisor → clasificador → supervisor → logística → supervisor → redactor → supervisor (ya hay respuesta: FIN) → END.

> **En un sistema multiagente, cada agente tiene que tolerar una respuesta inesperada de su modelo.** Si no, un eslabón débil tumba la cadena entera.

---

## 4. Actividad: ¿uno o un equipo?

**¿Un agente, un equipo o un workflow? Justificadlo.** (10 minutos)

No hay respuesta oficial en el PDF. Una propuesta (*ilustrativa*), aplicando la regla práctica de la sección 2.4 y los criterios de la sesión 1 (¿los pasos se conocen de antemano? → workflow):

| Caso | Propuesta | Por qué |
|---|---|---|
| 1. Responder preguntas frecuentes de clientes | **Workflow** (con RAG) | Los pasos son siempre los mismos: buscar la respuesta y redactarla. No hay nada que decidir |
| 2. Analizar 50 informes de competidores | **Equipo** (paralelo + agregación) | Amplio y paralelizable: cada subagente lee un grupo de informes y uno final lo junta. Es el caso de investigación de Anthropic |
| 3. Programar una nueva funcionalidad | **Un agente** | Tarea acoplada: cada decisión afecta a las demás. Es el caso de Cognition |
| 4. Propuesta comercial con datos de 3 departamentos | **Equipo pequeño** (supervisor) | Tres fuentes distintas, quizá con permisos distintos: un especialista por departamento y uno que escribe la propuesta. Si los datos caben juntos, basta un agente con tres herramientas |
| 5. Revisar contratos contra la política legal | **Workflow** (+ revisión humana) | Los pasos se conocen: sacar cláusulas, comparar con la política, marcar lo que no cumple. El riesgo pide que firme una persona |
| 6. Gestionar incidencias de IT 24/7 | **Un agente** para empezar | Clasificar y resolver con herramientas, como nuestro agente de Lumen Shop. Si crecen las áreas (redes, cuentas, hardware…) y el contexto se satura, pasar a un supervisor con especialistas |

La pregunta que guía: **¿qué problema concreto me resuelve el equipo** (contexto saturado, especialización o paralelismo) **y compensa lo que cuesta?**

---

## 5. Patrones y comunicación

### 5.1 Patrones multiagente

| Patrón | Cómo funciona | Ejemplo (*ilustrativo*) |
|---|---|---|
| **Supervisor** | Un agente central reparte el trabajo y decide | La demo de esta sesión |
| **Jerárquico** | Supervisores de supervisores, por áreas | Un jefe de atención al cliente con un supervisor para envíos y otro para devoluciones |
| **Secuencial** | Cadena de montaje: cada uno pasa al siguiente | Clasificador → logística → redactor, siempre en ese orden y sin jefe |
| **Handoffs** («traspasos») | Un agente transfiere el control a otro | Un agente de ventas que, cuando el cliente pide una devolución, le pasa la conversación al de devoluciones |
| **Paralelo y agregación** | Varios trabajan a la vez y se combinan | Tres subagentes buscan en fuentes distintas y uno junta los resultados |

### 5.2 Cómo se comunican

| | Estado compartido | Mensajes entre agentes |
|---|---|---|
| Cómo | Todos leen y escriben **el mismo estado** | Cada agente recibe **solo lo que se le envía** |
| Ventaja | Simple de implementar | Contextos limpios |
| Riesgo | El contexto **crece para todos** | **Perder información** al delegar |

> **Clave: ¿qué contexto recibe el agente al que se delega?**

La demo usa un **término medio**: hay una ficha común (estado compartido), pero en ella cada agente solo deja **su conclusión**, no todo lo que ha hecho. Así el contexto no crece sin control, pero, como vimos con Marta, lo que no llega en la nota se pierde.

### 5.3 Fallos típicos

| Fallo | Qué pasa | Solución |
|---|---|---|
| **Bucles entre agentes** | Se pasan la tarea indefinidamente | **Máximo de pasos** (en la demo, 6) |
| **Trabajo duplicado** | Dos agentes hacen lo mismo | **Responsabilidades claras** |
| **Delegación ambigua** | El subagente no sabe qué se espera de él | **Instrucciones de delegación explícitas** |
| **Pérdida de contexto** | Falta un dato clave al delegar | **Decidir qué se pasa** |

En la demo se ven las soluciones: el máximo de pasos; una descripción por agente sin solapes; el prompt de logística dice exactamente qué entregar («un resumen de hechos en 3 frases, sin redactar para el cliente»); y las notas son lo que se pasa. Y aun así, en las ejecuciones de esta sesión aparecen dos de estos fallos: la pérdida de contexto (Marta, sección 3.2) y una variante de la delegación (Jorge, sección 6.1).

Un quinto fallo, el que se encontró al preparar la sesión (sección 3.4): **un agente que no tolera una respuesta rara de su modelo tumba a todo el equipo.** Solución: que cada agente tenga un plan B y deje un aviso en las notas.

### 5.4 Protocolos: MCP y A2A

| | MCP | A2A (*Agent2Agent*) |
|---|---|---|
| Qué conecta | Un agente con **herramientas y datos** | **Agentes entre sí**, aunque sean de distintos proveedores |
| Dirección | Agente → herramienta | Agente → agente |
| Pieza clave | Herramientas y recursos (sesión 3) | ***Agent card***: la ficha de lo que sabe hacer cada agente |

A2A lo lanzó **Google en 2025** y hoy lo gestiona la **Linux Foundation**. La *agent card* es la misma idea que la descripción de una línea de nuestra demo, pero estándar: un agente de otra empresa puede leerla y saber si le conviene delegarte algo.

---

## 6. Demo: ampliar el equipo

En directo se ejecutaron las dos soluciones de los deberes. **Qué observar:** el supervisor descubre al nuevo agente por su descripción, el factor de coste del equipo frente a un agente solo, y si la respuesta mejora lo suficiente.

### 6.1 Un cuarto agente (deber base)

**El enunciado:** añade un agente de devoluciones que aplique la política de la tienda y **proponga, sin emitirlo**, un reembolso. Pista: solo hay que crear su función y añadirlo al diccionario `AGENTES`; el supervisor lo descubre por su descripción.

**La solución** (`deber_base.py`) tiene dos piezas:

1. **El agente**, con la política de la tienda dentro de su prompt: devolución gratis en 30 días con el producto sin abrir; producto dañado en el envío, reembolso completo con foto; más de 50 €, lo aprueba un supervisor humano. Su orden: «Indica si procede, por qué importe y qué necesita aportar el cliente. **No emitas nada.**»
2. **Darlo de alta en el equipo**, que es **añadir una línea**:

```python
AGENTES_AMPLIADOS = {
    **AGENTES,                                  # 1. el registro de agentes del equipo
    "devoluciones": (
        "aplica la política de devoluciones y propone reembolsos",   # 2. lo que lee el supervisor
        crear_devoluciones),
}
```

3. **Igual que con las herramientas: diseñad la descripción para el modelo.** El supervisor no lee el código del agente, solo esa frase. Por eso la solución añade «consúltalo en productos dañados o devoluciones»: le dice **cuándo** llamarlo.

**«Proponer sin emitir»** es el **mínimo privilegio** de la sesión 3: el agente de devoluciones no tiene la herramienta `emitir_reembolso`. Ni aunque se equivoque puede devolver dinero.

**En mi máquina**, con «Soy jorge.ruiz@email.com, el protector solar del pedido ORD-10598 llegó roto.»:

```
🧭 Supervisor → devoluciones: El cliente menciona que el producto llegó roto…
🧭 Supervisor → redactor: … proceder a la devolución con reembolso completo, incluyendo la solicitud de una foto del daño.
📊 Tokens: supervisor 570 · redactor 256 · devoluciones 194 · total: 1020

✉️  Hola Jorge, lamentamos mucho que el protector solar de tu pedido ORD-10598 llegara dañado…
    te ofrecemos un reembolso completo. Para proceder, necesitamos que subas una foto…
```

- **El supervisor encontró al nuevo agente por su descripción**, sin tocar el código del supervisor.
- **Pero se saltó a logística.** Y en la tienda, el pedido ORD-10598 está **«pendiente de envío»**: todavía no ha salido, así que no puede haber llegado roto. Nadie lo comprobó y el equipo ofrece un reembolso completo. Cada agente hizo bien su parte; el fallo está en **quién decide qué se comprueba**. Por eso la política pide aprobación humana en los reembolsos grandes, y por eso este agente solo **propone**.

### 6.2 ¿Compensa el equipo? (reto)

**El enunciado:** ejecuta el mismo ticket con un **agente único** (todas las herramientas, un solo prompt) y con el **equipo**. Compara tokens y calidad. ¿En qué tickets merece la pena el equipo?

**La solución** (`deber_reto.py`) monta un agente único con las mismas herramientas de lectura y un prompt que lo junta todo («clasifica, consulta con las herramientas y responde al cliente»), le pasa el ticket, luego se lo pasa al equipo, y saca el factor.

**En mi máquina**, con «Soy marta.lopez@email.com. Mi pedido ORD-10544 no llega.»:

```
Agente único: 1246 tokens
Equipo:       2897 tokens (×2.3)
```

**El equipo gasta más del doble.** Lejos del ×15 de Anthropic, porque nuestro equipo es pequeño y la tarea corta, pero la dirección es la misma.

La solución lo dice así: **no hay una respuesta universal: depende del ticket, del modelo y de lo que valga la calidad extra.** Una forma de pensarlo (*ilustrativa*):

| Ticket | ¿Equipo? |
|---|---|
| «¿Os queda crema hidratante?» | **No.** Una consulta. El equipo es pagar ×2 por lo mismo |
| «Mi pedido no llega» | **Probablemente no.** Un agente con herramientas lo resuelve |
| Una reclamación con varios pedidos, devolución, política y un cliente enfadado | **Puede.** Hay especialidades distintas y el contexto de un agente solo se llenaría |

---

## 7. Actividad: diseña un equipo

**Caso:** onboarding («incorporación») de un empleado nuevo, en el que participan **IT, RR. HH. y formación**. Diseñad el equipo (10 minutos, con el grupo del máster o individualmente en diferido):

1. ¿Qué agentes hay y qué hace cada uno?
2. ¿Qué herramientas tiene cada agente?
3. ¿Quién coordina y con qué patrón?
4. ¿Qué acciones requieren aprobación humana?

Una propuesta (*ilustrativa*):

| Agente | Qué hace | Herramientas |
|---|---|---|
| **Coordinador** | Recibe «entra Ana el lunes como analista», reparte y comprueba que todo esté hecho | Ninguna; o solo leer el estado de cada tarea |
| **IT** | Cuenta de correo, accesos a sistemas, portátil | Crear usuario, asignar permisos, pedir equipo |
| **RR. HH.** | Contrato, alta en nómina, documentación | Generar documentos, sistema de nóminas |
| **Formación** | Plan de cursos de las primeras semanas | Plataforma de cursos (asignar cursos) |

- **Patrón:** **supervisor**, con los tres especialistas trabajando **en paralelo**, porque no dependen unos de otros. Es un caso «amplio y paralelizable», no acoplado.
- **Aprobación humana:** todo lo que es **irreversible o sensible**. Alta en nómina y contrato (dinero y datos personales); permisos de acceso a sistemas críticos; compras de equipo. Asignar cursos o crear el correo puede ir sin aprobación.
- **¿Y si fuera un agente solo?** También funcionaría. El argumento a favor del equipo es el **mínimo privilegio**: el agente de formación no necesita acceso a las nóminas.

---

## 8. Caso real: el sistema de investigación de Anthropic

```
                       ┌──► Subagente 1 ──┐
Pregunta ──► Agente principal              ├──► Agente principal (sintetiza) ──► Respuesta
            (planifica)├──► Subagente 2 ──┤
                       └──► Subagente 3 ──┘
```

Un **agente principal** recibe la pregunta, la divide en líneas de investigación, lanza **subagentes en paralelo** (cada uno busca por su lado, con su propio contexto) y al final **junta** lo que traen. Es el patrón **paralelo y agregación** con un jefe que planifica (el *plan-and-execute* de la sesión 2).

**Lo que aprendieron:**
- **Paralelizar búsquedas acelera la investigación.**
- **Las instrucciones de delegación lo son todo.** Si al subagente le dices solo «investiga X», puede repetir lo que hace otro o irse por las ramas. Hay que decirle el objetivo, qué devolver y dónde parar.
- **Coste muy superior al de un agente** (el ×15 de la sección 2.2).
- **Evaluar con casos reales desde el principio.**

### Idea clave

> **Un equipo de agentes es una herramienta para un problema concreto, no una mejora por defecto.**
> Empezad con un agente; pasad a un equipo cuando el contexto se sature, haga falta especializar o se pueda paralelizar. Y entonces, lo importante es **qué contexto recibe cada agente cuando se le delega.**

Lo hemos visto en nuestras propias ejecuciones: el equipo gasta el doble. Funciona bien cuando cada agente recibe lo que necesita, y falla cuando no le llega un dato (Marta) o nadie lo comprueba (Jorge).

---

## 9. Deberes para la sesión 6

Diapositiva «Deberes para la sesión 6». **No son evaluables**: se comentan al inicio de la próxima sesión. Las soluciones ya están en `Solución deberes sesión 5/soluciones/sesion5/` y se vieron en directo en la sección 6.

| Nivel | Deber | Solución |
|---|---|---|
| **Base · Un cuarto agente** | Añade un agente de devoluciones que aplique la política y proponga, sin emitirlo, un reembolso. Pista: crea su función y añádelo al diccionario `AGENTES` | `deber_base.py` · sección 6.1 |
| **Reto · ¿Compensa el equipo?** | Ejecuta el mismo ticket con un agente único y con el equipo. Compara tokens y calidad. ¿En qué tickets merece la pena el equipo? | `deber_reto.py` · sección 6.2 |

Una idea para ir más allá con el reto (*ilustrativa*): la solución compara **tokens**, pero no imprime la respuesta del agente único, así que la **calidad** hay que mirarla aparte. Probarlo con los tres tickets de la tabla de la sección 6.2 da la respuesta a «¿en qué tickets merece la pena?».

### Lectura recomendada

**«How we built our multi-agent research system»** (Anthropic, junio de 2025). Un caso real de sistema multiagente en producción, con sus números y sus errores (el de la sección 8). En qué fijarse:
- **Cuándo dicen que compensa y cuándo no.**
- **Cómo escriben las instrucciones de delegación.**
- **Cómo pasan del prototipo a producción.**

---

## Resumen de la sesión

- **Un equipo aporta** especialización, contextos separados y paralelismo. Es la estrategia **«aislar»** de la sesión 4.
- **Y cuesta**: muchos más tokens (×15 en el caso de Anthropic, ×2,3 en nuestra demo), más latencia y depuración más difícil.
- **Regla práctica:** varios agentes para tareas **amplias y paralelas**; uno solo para tareas **acopladas**. **Empezad siempre con uno.**
- **La demo:** un **supervisor** decide quién sigue; cada agente tiene su prompt y su contexto, deja **solo su conclusión** en una ficha común y vuelve al supervisor. Máximo de pasos contra bucles y tokens medidos por agente.
- **Por dentro:** la ficha común es `EstadoEquipo`, y `Annotated` dice cómo se junta lo que aporta cada agente (notas que se añaden, tokens que se suman, historial que se concatena). Y **cada agente tiene que tolerar una respuesta rara de su modelo**, o un solo fallo tumba al equipo entero.
- **Patrones:** supervisor, jerárquico, secuencial, *handoffs*, paralelo y agregación. **Comunicación:** estado compartido o mensajes. La pregunta clave: **¿qué contexto recibe el agente al que se delega?**
- **Fallos típicos:** bucles, trabajo duplicado, delegación ambigua y pérdida de contexto. Los dos últimos los vimos en directo.
- **Añadir un agente es añadir una línea**, y su **descripción** es lo que lee el supervisor: se diseña para el modelo, como las herramientas.
- **MCP** conecta agentes con herramientas; **A2A** conecta agentes entre sí (*agent card*).
