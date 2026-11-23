# Sesión 1: Diseño conversacional y agente de chat

Explicación sencilla del día 1 del Tema 10, centrada en las ideas principales. Se construye a partir de los PDF de `clase_01/`: las diapositivas de la sesión, la guía de preparación del entorno, la guía del ejercicio de clase (el bot de Telegram) y los dos ejercicios complementarios con su corrección. El código del kit (`ondo-agente`) todavía no está en el repositorio, así que lo que se cuenta del código sale de las diapositivas y de las guías. Los ejemplos propios van marcados como *ilustrativos*.

---

## 0. Dónde estamos

### El mapa del tema

En los Temas 8 y 9 el agente recibía **un encargo** y lo resolvía. En el Tema 10 el agente **conversa**: recibe un mensaje, contesta, recibe otro… y tiene que llevar bien la conversación entera, por chat y por teléfono.

| Día | Bloque | Qué se hace |
|---|---|---|
| **1 · 23/11** | **Diseño y chat** | Reglas para diseñar una conversación, el agente de Ondo por dentro y el bot de Telegram (esta sesión) |
| 2 · 25/11 | Tests y evaluación | Tests como especificación, completar el flujo de cita y evaluar con escenarios y un juez |
| 3 · 30/11 | Voz y teléfono | Voz en el navegador con Pipecat, llamada por Twilio y paso a una persona |

### El caso: Ondo

**Ondo** es una tienda online ficticia de **bicicletas eléctricas** que vende en España, Francia, Italia y Portugal. Quiere un agente que atienda por chat y por teléfono, **resuelva lo sencillo y pase a una persona lo demás**.

Datos de partida: 30 clientes, 40 pedidos, 7 talleres, 10 documentos de política y un servidor MCP con 7 herramientas.

Atiende **cuatro motivos de contacto**:

| Motivo | Qué hace el agente |
|---|---|
| ¿Dónde está mi pedido? | Estado, transportista, seguimiento e incidencias |
| Devoluciones | Las que están en plazo, las resuelve él; las que hay que revisar, una persona |
| Cita en el taller | Revisión o avería en un taller asociado: hueco, confirmación y reserva |
| Seguridad | Batería que se calienta o huele a quemado, frenos que fallan: **siempre a una persona** |

> La seguridad pasa siempre a una persona, **aunque el cliente lo cuente como una duda sin prisa**.

---

## 1. Qué es un agente conversacional

### 1.1 Agente de tareas frente a agente conversacional

| Agente de tareas (Temas 8 y 9) | Agente conversacional (Tema 10) |
|---|---|
| Recibe **un encargo completo** | Recibe un mensaje y luego otro, de una persona |
| Planifica, usa herramientas y devuelve un resultado | En **cada turno** decide: preguntar, actuar o pasar a una persona |
| Se evalúa por si cumplió el objetivo | Se evalúa por **cómo resolvió la conversación entera** |

### 1.2 Seis conceptos que salen todo el tema

| Concepto | Qué es, en palabras normales |
|---|---|
| **Turno** | Un mensaje del cliente y la respuesta del agente |
| **Estado del diálogo** | Lo que el agente sabe en este momento: quién es el cliente, qué quiere, qué datos tiene |
| **Intención** | Lo que quiere el cliente: pedido, devolución, cita, información… |
| **Slots** | Los «huecos» de datos que faltan para cumplirlo: email, número de pedido, ciudad, hora |
| **Reparación** | Qué hace el agente cuando no entiende o no le contestan |
| **Traspaso** | Pasar la conversación a una persona **con todo el contexto** |

*Ilustrativo*: si el cliente dice «quiero cita en el taller», la intención es *cita* y los slots que faltan son el motivo, la ciudad y el hueco. El agente irá preguntándolos uno a uno.

### 1.3 Del bot de intenciones al modelo de lenguaje

- Los bots antiguos (Dialogflow, Rasa) seguían un guion de intenciones fijo: **se rompían en cuanto el cliente se salía del guion**.
- Un agente con modelo de lenguaje entiende casi cualquier cosa, pero **improvisa**: hay que devolverle estructura y reglas.

Esa es la idea de todo el día: **aprovechar que el modelo entiende, pero que las decisiones importantes no dependan de su improvisación**.

### 1.4 Ejercicio 1 · ¿Qué entiende el agente?

Para cada mensaje, la intención y los datos que saca:

| Mensaje | Intención | Por qué |
|---|---|---|
| «¿Cómo va lo mío? Es el OND-10231» | Pedido (con `pedido_id`) | Caso base |
| «La batería se calienta mucho al cargarla, pero no corre prisa» | **Seguridad** | Cuenta lo que dice, no el tono. Además una expresión regular del código detecta «se calienta» |
| «¿Cuánto tardáis en devolverme el dinero?» | Información | Parece una devolución, pero es una duda de política: la contesta el RAG (14 días) |
| «Madrid», justo después de preguntar la ciudad | Continuar (con ciudad) | Sin contexto no se entiende: **la intención depende del estado** |
| «…hace un ruido raro al frenar» | Cita (avería) | Para Ondo, seguridad es que los frenos **no frenen**. Un ruido es una avería |
| «Paso de bots, pásame con alguien» | Persona | Siempre, sin intentar retenerle |
| «Quiero devolver el casco, llegó hace una semana» | Devolución | Aún falta saber qué pedido es |
| «lo de siempre» | No entendido | Abre el primer escalón de la reparación |

> **Interpretar es rellenar una ficha** (salida estructurada). Contestar viene después.

---

## 2. Diseñar la conversación

Antes de escribir código se decide **cómo tiene que hablar** el agente. La prueba para todo este bloque:

> Si una persona del equipo no respondería así por chat, el agente tampoco.

### 2.1 Tres reglas básicas

| Regla | Qué significa |
|---|---|
| **Personalidad y tono** | Tutea, frases cortas, sin tablas ni markdown. Cercano y profesional |
| **Bienvenida** | Dice que es **una IA**, qué sabe hacer y que puedes pedir una persona |
| **Una pregunta por turno** | Pide un solo dato cada vez. Lo que ya sabe no lo vuelve a pedir |

### 2.2 Confirmar según el riesgo

No todas las acciones son iguales:

- **Leer** (consultar un pedido) no cambia nada → se hace **sin preguntar**.
- **Escribir** (reservar una cita, crear una devolución) sí cambia algo → se **resume y se pide un sí claro**.
- Si la respuesta es ambigua → **se vuelve a preguntar**.

Ejemplo de la diapositiva:

| ✓ Confirma antes | ✗ Actúa directamente |
|---|---|
| «Te reservo el jueves 12 a las 10:00 en Calle del Prado 12, para una revisión. ¿Confirmo?» | «Hecho, tu cita está reservada.» |
| Si el modelo entendió mal, el cliente lo ve a tiempo | Un error de interpretación se convierte en una cita que nadie pidió |

**Relámpago · ¿Cuenta como sí?** El agente pregunta «¿Confirmo?» y el cliente contesta:

| Respuesta | Cuenta como | Qué hace el agente |
|---|---|---|
| «Sí, perfecto» | Sí claro | Reserva |
| «Vale, gracias» | Sí claro | Reserva |
| «Bueno… supongo» | Ni sí ni no | Vuelve a preguntar |
| «Sí, pero mejor el viernes» | Ni sí ni no | Es un cambio de hueco: vuelve a elegir |
| «¿A qué hora era?» | Ni sí ni no | Responde y vuelve a preguntar |
| «No, déjalo» | No | No reserva |

> **Una respuesta ambigua nunca cuenta como un sí.**

### 2.3 Cuando el agente no entiende: reparación en tres escalones

Ni rendirse a la primera ni insistir para siempre:

1. **Reformular**: «No te he entendido bien, ¿me lo cuentas de otra forma?», más un recordatorio de lo que sabe hacer.
2. **Ofrecer opciones**: botones concretos. Elegir es más fácil que redactar.
3. **Pasar a una persona**: al tercer intento, con un resumen. El cliente no repite nada.

### 2.4 Cuándo pasar a una persona

| Siempre, sin intentarlo | Después de intentarlo |
|---|---|
| Seguridad: batería, frenos, humo | Tres turnos sin entender al cliente |
| El cliente pide hablar con una persona | No hay taller en su ciudad o no quedan huecos |
| Una regla de negocio lo exige: devoluciones de **más de 1.500 €** | Una herramienta falla y no hay alternativa |

**Ejercicio 2 · ¿Actúa, confirma o pasa a una persona?**

| Caso | Qué hace | Por qué |
|---|---|---|
| A · Lucía, ya identificada, pregunta por OND-10231 | Actúa sin preguntar | Es una consulta: no cambia nada |
| B · Javier devuelve OND-10233: 990 €, hace 12 días | Resume y pide un sí claro | En plazo y por debajo de 1.500 €: la tramita el agente, pero tiene efecto |
| C · Pau devuelve OND-10235: 2.959 €, hace 9 días | Persona siempre | Pasa de 1.500 €: la revisa postventa |
| D · Marta devuelve OND-10234: 2.190 €, hace 45 días | Lo intenta; persona si reclama | Está fuera de plazo; el importe ya ni cuenta |
| E · Nerea, de Bilbao, pide cita | Lo intenta y luego persona | No hay taller en Bilbao: le da las siete ciudades con taller |
| F · Lucía elige «el jueves a las 10» | Resume y pide un sí claro | Reservar tiene efecto |
| G · Elena, OND-10236 con «dirección incompleta» | Actúa y pasa a persona la dirección | Informa de la incidencia; cambiar la dirección no tiene herramienta |
| H · En mitad de la cita: «el cargador huele a quemado» | Persona siempre, urgente | Seguridad: deja la cita a medias |

### 2.5 El mapa de la conversación

Todo lo anterior, en un dibujo:

```text
                     Mensaje del cliente
                             │
                        ¿Qué quiere?
   ┌──────────┬──────────┬───┴───────┬─────────────┐
 Pedido   Devolución    Cita     Información    Seguridad      No te entiendo
   └──────────┼──────────┘           │             │            1 → 2 → 3
     Identificar cliente             │             │                │
              │                      │             │             Persona
              └──────────────────────┴──────┬──────┴────────────────┘
                              Respuesta con el tono de Ondo
```

Lo importante: **pedido, devolución y cita** necesitan saber quién es el cliente; **información** y **seguridad** no.

### 2.6 Idioma y datos personales

1. **Responde en el idioma del cliente**: detecta el idioma en cada mensaje y redacta en ese idioma (Ondo vende en cuatro países).
2. **Identifica antes de dar datos**: el **email de compra** identifica al cliente. Un número de pedido no basta: se comprueba que ese pedido es de ese cliente.

---

## 3. Del agente que falla al grafo

### 3.1 Demo: el agente ReAct genérico

Se monta el agente «de siempre» (el ReAct del Tema 8) con las herramientas MCP de Ondo y un prompt de una línea: *«Eres el asistente de atención al cliente de Ondo… Ayuda al cliente con sus consultas»*. Sin estado de conversación.

```bash
python -m agente.react_fallo
```

Lo que respondió (extracto real de la diapositiva):

```text
Tú: Es el OND-10231                → «He encontrado el pedido...»
Tú: ¿Y cuándo me llega?             → «Necesito tu email o el número de pedido»
Tú: ¿Cómo va el pedido OND-10235?   → «Fue entregado el 2 de noviembre...»
Tú: ¿Cuántos días para devolver?    → «Generalmente tienes 14 días...»
Tú: La batería huele a quemado      → «¿Me das tu número de pedido?»
```

> Las herramientas funcionan y el modelo es bueno. **Falta todo lo demás**: memoria, comprobaciones, política y reglas de seguridad.

### 3.2 Cuatro fallos y su arreglo

| Fallo | Arreglo |
|---|---|
| **Olvida el pedido** (al turno siguiente vuelve a pedirlo) | Estado de la conversación guardado (un *checkpointer*), un hilo por chat |
| **Da datos de otro cliente** (OND-10235 es de Pau, no de quien pregunta) | Identificar por email y comprobar **en código** que el pedido es suyo |
| **Se inventa la política** («generalmente 14 días») | RAG sobre la política de Ondo y un umbral: si no lo sabe, lo dice |
| **Trata la batería como un trámite** (pide el pedido) | Regla de seguridad **determinista** que siempre pasa a una persona |

### 3.3 Qué guarda el estado

Más que la lista de mensajes: **lo que el agente sabe, escrito de forma explícita**, como una ficha de cliente:

| Campo | Qué guarda |
|---|---|
| cliente | Quién es, si ya se ha identificado |
| intención | Qué quiere ahora (pedido, devolución, cita…) |
| datos | Lo recogido: email, pedido, ciudad, motivo… |
| pendiente | Qué dato está esperando el agente |
| opciones | Los botones que ha ofrecido |
| intentos fallidos | Turnos seguidos sin entenderle |
| escalado | Si ya hay un caso abierto con una persona |
| idioma | En qué idioma contestar |

Cada conversación tiene su propia ficha (su **hilo**). Así dos clientes a la vez no se mezclan.

### 3.4 Cada turno, cuatro pasos

La idea más importante del día:

> **El modelo entiende y redacta. El código decide.**

```text
 Interpretar  →   Decidir   →  Herramientas  →  Redactar
   MODELO          CÓDIGO          MCP            MODELO
```

| Paso | Quién | Qué hace |
|---|---|---|
| **Interpretar** | Modelo | Convierte el mensaje en una ficha: intención, email, pedido, elección, confirmación |
| **Decidir** | Código (Python) | Qué falta, qué herramienta llamar, cuándo pasar a una persona |
| **Herramientas** | Servidor MCP | Consultan o cambian datos reales |
| **Redactar** | Modelo | Recibe un **borrador de qué decir** y decide **cómo** decirlo, con el tono de Ondo y en el idioma del cliente |

¿Por qué así? Porque las reglas de dinero, de seguridad y de datos personales **no pueden depender de que el modelo acierte**. El modelo es muy bueno entendiendo lenguaje; el código es fiable cumpliendo reglas.

### 3.5 El grafo de Ondo

Así queda un turno, como grafo de LangGraph:

```text
                  ┌→ identificar → flujo (pedido / devolución / cita) ─┐
                  ├→ reparar ─────────────────────────────────────────┤
 interpretar → ruta() ─→ informar ────────────────────────────────────┼→ redactar → FIN
                  ├→ saludar ─────────────────────────────────────────┤
                  ├→ ya_escalado ─────────────────────────────────────┤
                  └→ escalar ─────────────────────────────────────────┘
```

| Nodo | Qué hace | Herramienta |
|---|---|---|
| interpretar | Saca intención y datos. Además, una lista fija de palabras de peligro (humo, quemado, fuego, se calienta, no frena…) marca **seguridad** aunque el modelo no lo vea | — |
| reparar | Cuando no se entiende: primero reformula, luego opciones, al tercero persona | — |
| identificar | Pide el email y busca al cliente (al tercer email fallido, persona) | `buscar_cliente` |
| flujo | Lleva el pedido, la devolución o la cita paso a paso | `estado_pedido`, `huecos_taller`… |
| informar | Busca en la política y responde solo con lo que encuentra | `buscar_conocimiento` |
| saludar | Saluda, dice que es una IA y ofrece lo que sabe hacer | — |
| escalar | Abre un caso para una persona con un resumen (urgente si es seguridad) | `escalar_a_humano` |
| ya_escalado | Recuerda que su caso ya lo lleva una persona y le da el número | — |
| redactar | Escribe la respuesta final | — |

**Cómo elige camino `ruta()`**: comprueba estas reglas **en orden** y **gana la primera** que se cumple:

1. **Seguridad** → escalar
2. **Ya hay un caso abierto** → ya_escalado
3. **Pide una persona** → escalar
4. **No entendido** → reparar (excepción: si un flujo estaba esperando un dato de un cliente ya identificado, repara el propio flujo)
5. **Pedido, devolución o cita** → flujo si el cliente está identificado; si no, identificar
6. **Información** → informar
7. **Saludo** (o cualquier otra cosa) → saludar

El orden es lo que hace que la seguridad **interrumpa cualquier cosa**: va la primera.

### 3.6 Ejercicio 3 · Sé el grafo

Se da el estado y un mensaje, y hay que recorrer el grafo a mano.

| Caso | Estado | Mensaje | Camino | Qué pasa |
|---|---|---|---|---|
| 1 | Vacío | «¿Dónde está el OND-10235?» | interpretar → identificar → redactar | Intención pedido; no hay cliente, así que pide el email «para comprobar que el pedido es suyo». Arregla el fallo 2 del ReAct |
| 2 | Lucía, pidiendo cita, pendiente: ciudad | «pues no sé, donde sea» | interpretar → flujo → redactar | No hay ciudad. Repara el propio flujo: vuelve a preguntar con botones «Madrid» / «Otra ciudad». Los intentos fallidos **no suben** (es un fallo real que encuentra el revisor el día 2) |
| 3 | El mismo | «oye, la batería echa humo» | interpretar → escalar → redactar | «Humo» lo fuerza la lista `PELIGRO` del código aunque el modelo falle. Caso urgente con `escalar_a_humano`; le dice que deje la bici, no cargue la batería y llame al 112 si hay humo o fuego. **La cita se queda a medias** |

### 3.7 Opcional · ¿Modelo o código?

| Tarea | Paso | Por qué |
|---|---|---|
| Detectar el idioma | Interpretar | Es un campo de la ficha |
| Sacar el email | Interpretar | Otro campo de la ficha; el código lo guarda |
| Comprobar los 30 días de una devolución | Decidir | Una regla de dinero va en el código |
| Persona al tercer intento | Decidir | `MAX_INTENTOS = 3`, en `grafo.py` |
| Huecos del taller | Herramienta | `huecos_taller`, del servidor MCP |
| Explicar por qué no se puede devolver | Redactar | El código decide **qué** decir y el modelo lo escribe con el tono de Ondo |
| Detectar seguridad | Interpretar **y** decidir | El modelo lo clasifica y la lista del código lo fuerza si el modelo falla |
| Comprobar que el pedido es del cliente | Herramienta **y** decidir | `estado_pedido` devuelve el titular y el código lo compara |

### 3.8 Un RAG sencillo, como herramienta

La política de Ondo (10 documentos) está detrás de la herramienta `buscar_conocimiento`:

- Un fragmento por sección de cada documento, *embeddings* de `text-embedding-3-small` y un almacén en memoria de LangChain.
- Devuelve los 3 mejores resultados **con un umbral de similitud**.
- **Si no lo sabe, lo dice**: por debajo del umbral devuelve «sin resultados» y el agente ofrece una persona. «¿Cuál es la capital de Francia?» no tiene respuesta en Ondo.

### 3.9 El mismo guion, con el grafo

```bash
python -m canales.consola --estado
```

```text
Tú: ¿Cómo va el pedido OND-10235?  → «Necesito el email de tu compra»
Tú: lucia.martin@example.com       → «Ese pedido no está asociado a tu cuenta»
Tú: La batería huele a quemado...  → «Deja de usar la bici... CASO-0001»
 [estado] cliente: C001 · pendiente: pedido_id · escalado: CASO-0001
```

Los cuatro fallos del ReAct, arreglados: recuerda, comprueba de quién es el pedido y la seguridad pasa a una persona.

---

## 4. Chatbot en Telegram

### 4.1 ¿Por qué Telegram y no WhatsApp?

| WhatsApp Business | Telegram |
|---|---|
| El canal de mensajería más usado en España | Un bot en un minuto con **BotFather**, gratis |
| Cloud API de Meta, plantillas aprobadas y ventana de 24 h | **Polling**: sin URL pública ni verificación de empresa |
| Desde el 15/01/2026, solo bots con función de negocio | Botones, comandos y grupos |

Para aprender, Telegram es mucho más fácil; en una empresa real en España probablemente sería WhatsApp.

### 4.2 Polling o webhook

La diferencia es **quién llama a quién**:

| | Polling (hoy) | Webhook (producción) |
|---|---|---|
| Quién inicia | Tu programa llama a Telegram y espera hasta 10 s a que llegue un mensaje | Telegram llama a una URL tuya en cada mensaje |
| URL pública | No hace falta: la conexión sale del portátil | Sí, con HTTPS (desde un portátil, con un túnel como ngrok) |
| Cuándo | Para desarrollar y practicar | En producción, con servidor |

El bot usa polling los tres días. Twilio (día 3) solo funciona con webhook: por eso hay que tener ngrok preparado.

### 4.3 La práctica en tres pasos

1. **El kit y tu bot**: clonar `ondo-agente`, crear el `.venv`, poner la clave de OpenAI en `.env` y crear el bot con `@BotFather` (`/newbot`, nombre, username acabado en `bot`, y pegar el token en `TELEGRAM_BOT_TOKEN`).
2. **Arrancar y probar**: `python -m canales.telegram_bot`, escribir «¿Dónde está mi pedido?», luego `lucia.martin@example.com`, y probar los botones.
3. **Entenderlo con el chat**: preguntar al chat de VS Code en modo **Ask** (solo contesta, no cambia nada) y **comprobar lo que dice** con la consola y `--traza`.

### 4.4 Comprobar con la traza

`python -m canales.consola --traza` enseña, en cada turno, **por qué nodos pasa el mensaje**, qué cambia cada uno y qué herramientas llama; al final, la línea `[estado]`. Las pruebas de la guía:

| Prueba | Qué escribir | Qué debe pasar |
|---|---|---|
| Memoria | «¿Dónde está mi pedido?», el email de Lucía, «¿y cuándo llega?» | Recuerda a Lucía y su pedido (cliente: C001) |
| Seguridad | «Sin prisa: la batería huele un poco a quemado al cargar, ¿es normal?» | Instrucciones de seguridad y caso urgente; pasa de interpretar a escalar **sin tocar ningún flujo** |
| Pedido ajeno | «¿Cómo va el pedido OND-10235?» y el email de Lucía | Dice que no es suyo y no da ningún dato |
| Reparación | Tres mensajes sin sentido | Reformula, ofrece opciones y al tercero pasa a una persona |

(`/reset` empieza una conversación nueva y `/salir` termina.)

> **Lo que dice el chat hay que comprobarlo.** El chat de VS Code puede equivocarse explicando el código; la traza enseña lo que hace de verdad.

---

## 5. El agente conversacional en código

Cinco ficheros de `agente/`, cada uno con una imagen en las diapositivas:

| Fichero | La imagen de la diapositiva | Qué hace |
|---|---|---|
| `agente.py` | Una recepcionista (`AgenteOndo`) que recibe cartas de Telegram, de la consola y (el día 2–3) del teléfono, cada una con su carpeta de **hilo**, y habla con el servidor MCP | **La puerta de entrada**: da igual el canal, todos los mensajes entran por aquí y salen como texto, botones y estado |
| `estado.py` | Una ficha de cliente sobre la mesa y un archivador con una ficha por hilo | **La memoria explícita**: lo de la sección 3.3 |
| `grafo.py` | Una estación de tren: tras interpretar, las vías se separan en las 7 rutas numeradas y vuelven a juntarse en redactar | **La decisión de cada turno**: los nodos y `ruta()` |
| `herramientas.py` | Un portátil conectado por un cable `stdio` (una sola sesión) a un armario con las 7 herramientas | **El puente con el servidor MCP** |
| `llm.py` | Tres casetas: interpretar (oreja que rellena la ficha), redactar (pluma que parte de un borrador) y resumir (pasa un resumen a una persona) | **Las tres llamadas al modelo**; entre interpretar y redactar, «el código decide» |

Las **7 herramientas** del servidor MCP de Ondo: `buscar_cliente`, `estado_pedido`, `huecos_taller`, `reservar_cita`, `crear_devolucion`, `buscar_conocimiento` y `escalar_a_humano`.

Ventaja del MCP (el mismo protocolo del Tema 6): **los datos y las acciones viven fuera del grafo**, así que pueden cambiar sin tocar el agente.

---

## 6. Las piezas que guían al chat de VS Code

### 6.1 Dos agentes en la misma carpeta

Esto es fácil de confundir:

1. **El agente de Ondo**: el grafo de `agente/`, sus prompts en `llm.py` (como `PERSONA_ONDO`) y las herramientas MCP. Habla con los clientes.
2. **El agente del chat de VS Code**: lee `AGENTS.md`, carga skills y delega en subagentes. **Te ayuda a programar** el de Ondo.

> Cambiar `AGENTS.md` **no cambia** cómo habla el agente de Ondo, y al revés.

### 6.2 Las piezas, una a una

| Pieza | Qué es | Cuándo entra en el contexto | Quién la lanza |
|---|---|---|---|
| **Prompt** | Lo que escribes ahora; vive solo en esa conversación | En ese momento | Tú |
| **Prompt file** | Una plantilla de prompt guardada en un fichero | Al escribir `/` | Tú |
| **`AGENTS.md`** (instrucción de carpeta) | Reglas y contexto del proyecto | **Siempre**, al empezar | Nadie: se carga sola |
| **Instrucciones por carpeta** | Reglas de un tipo de fichero (tests, migraciones…) | Al tocar esos ficheros | Nadie |
| **Skill** | Un proceso con pasos, scripts y comprobación | Cuando la tarea encaja, o con `/` | El agente o tú |
| **Subagente** | Otro agente con su propio contexto e instrucciones | Cuando se le delega | El agente principal o tú |
| **Servidor MCP** | Acceso a datos o acciones de otro sistema | Sus herramientas, siempre | El agente |
| **Lint, tests, CI** | Lo que debe cumplirse siempre | Al ejecutarse | Nadie: pasa o falla |

Clave de las skills: **al principio el chat solo lee su nombre y su descripción**; el resto, cuando la necesita. Con una descripción vaga, no sabe cuándo usarla.

### 6.3 Caso · Documentar y revisar

Proyecto simulado `deriva-costes/` y la petición: *«Añade docstrings a las funciones públicas de `main.py` y pide una revisión independiente de lo que has cambiado.»*

Qué pasa:

1. Llega el mensaje. Ya están en memoria `AGENTS.md` de la raíz y **solo las descripciones** de skills, agentes y el MCP.
2. «Docstrings» encaja con la skill `documentar-codigo`: **entra su `SKILL.md`** con el formato del equipo.
3. Escribe los docstrings en `main.py` sin cambiar lógica.
4. Llama al subagente `revisor` con un encargo completo: **no ve la conversación** ni puede usar git.
5. El revisor empieza con contexto limpio, lee los ficheros y `AGENTS.md`. Solo tiene las herramientas `read` y `search`.
6. Devuelve un veredicto corto; el asistente lo resume y corrige.

Lo que **no entra**: los `AGENTS.md` de `tests/` y `proveedor_simulado/` (no se tocan esos ficheros) y la skill `diagnosticar-error` (no encaja).

> El revisor trabaja con contexto limpio y sin permiso de edición. **La frontera la pone la lista de herramientas, no una frase del fichero.**

### 6.4 Las tres piezas del kit de Ondo

| Pieza | Dónde | Qué aporta |
|---|---|---|
| `AGENTS.md` | Raíz del kit | **Comandos** (instalar, tests, consola con el Python de `.venv`), qué significa **terminado** (los tests de lo pedido pasan, un resumen corto y nada tocado fuera de lo pedido) y las **reglas de la conversación** de la sección 2 (confirmar antes de reservar, reintentos, paso a persona, no inventar datos) |
| Skill `completar-flujo` | `.agents/skills/completar-flujo/SKILL.md` | Un proceso que se repite: **tests primero**, después el código y al final la validación |
| Subagente `revisor_conversacion` | `.github/agents/revisor_conversacion.agent.md` | Revisa un flujo contra las reglas de `AGENTS.md` con su propio contexto. Solo `read` y `search`: no edita ni ejecuta |

El día 2 se usan las tres para escribir los tests del flujo de cita y construirlo.

---

## 7. Ejercicios complementarios (para el día 2)

### 7.1 Ejercicio 1 · Sé el grafo

Ocho casos para predecir en papel el camino por el grafo. La corrección (ejecutada con el agente real el 19/11/2026):

| Caso | Mensaje | Camino | Herramientas | Lo importante |
|---|---|---|---|---|
| 1 | «Hola» | interpretar → saludar → redactar | — | Regla 7: saluda, dice que es una IA y ofrece tres botones |
| 2 | «¿Dónde está mi pedido OND-10231?» | interpretar → identificar → redactar | — | Pide el email; el número de pedido ya queda guardado |
| 3 | «lucia.martin@example.com» | interpretar → identificar → flujo → redactar | `buscar_cliente`, `estado_pedido` | Es la respuesta a lo pedido: la intención sigue siendo pedido. Da el estado porque es suyo |
| 4 | «Quiero devolver la bici, no me convence» | interpretar → flujo → escalar → redactar | `escalar_a_humano` | Ya identificada, va directa al flujo; en el día 1 la devolución pasa siempre a persona |
| 5 | «¿Y cuánto tardarán en llamarme?» | interpretar → ya_escalado → redactar | — | Da igual cómo lo interprete: la regla 2 va antes. Le recuerda su número de caso |
| 6a-6c | «asdf», «qwerty», «zzz» | interpretar → reparar (→ escalar en el tercero) → redactar | `escalar_a_humano` al tercero | Intentos 1, 2, 3; cada vez otra estrategia y nunca un bucle |
| 7 | «Sin prisa: la batería huele un poco a quemado al cargar» (en mitad de la cita) | interpretar → escalar → redactar | `escalar_a_humano` urgente | «Quemado» está en la lista de peligro; la cita se queda a medias a propósito |
| 8 | «¿Cuánto dura la garantía de la batería?» | interpretar → informar → redactar | `buscar_conocimiento` | Responde 2 años o 500 ciclos |

### 7.2 Ejercicio 2 · Diagnostica la conversación

Cinco conversaciones de una versión **mal diseñada** del asistente. Para cada una: qué regla incumple, cómo debería ser y qué pieza del kit lo evita.

| Conversación | Qué hace mal | Cómo debería ser | Qué lo evita en el kit |
|---|---|---|---|
| 1 · «Soy Marta, de Ondo» | Se hace pasar por persona y esquiva «¿eres una persona?» | «Soy el asistente virtual de Ondo, una inteligencia artificial…» y, si pregunta, «No, soy un asistente virtual. Si prefieres, te paso con una persona» | Nodo `saludar` de `grafo.py` y el prompt `PERSONA_ONDO` de `llm.py` |
| 2 · Reserva «el viernes» | «El viernes» encaja con dos huecos y elige uno; además reserva sin un sí claro | Pregunta cuál de los dos; luego resume y pide confirmación con botones | La regla está en `AGENTS.md`; los pasos de elegir y confirmar de `flujos/cita.py` se construyen el día 2 |
| 3 · «No te he entendido» × 3 | Repite lo mismo y deja al cliente atrapado | Reformula → opciones con botones → persona con número de caso | Nodo `reparar`, `MAX_INTENTOS = 3` y el menú con «Hablar con una persona» |
| 4 · «60 días y 24 horas» | Se inventa el plazo | 30 días naturales desde la entrega; reembolso en máximo 14 días desde que el almacén lo revisa | Nodo `informar` con `buscar_conocimiento`: responde solo con lo encontrado |
| 5 · Batería «sin prisa» | Trata la seguridad como un paso normal y la persona vuelve a pedir email y pedido | Instrucciones de seguridad, caso urgente con número, y la persona empieza con el resumen delante | Lista `PELIGRO` y `ruta()` de `grafo.py`; el resumen lo escribe `resumir` de `llm.py` |

**Lo que hizo el agente real** (19/11/2026, `gpt-4.1-mini`). Lo más interesante del ejercicio, porque enseña que el agente bueno **también falla**:

- **Conversación 1**: el saludo fue correcto, pero ante «¿Eres una persona?» interpretó que **pedía** una persona y abrió un caso. Fallo de **interpretación**: se arreglaría en el prompt de interpretar.
- **Conversación 3**: siguió los tres escalones exactamente.
- **Conversación 4**: no se inventó el plazo, pero **tampoco lo dio**: el RAG trajo primero un fragmento de «Pagos y facturas» y contestó que no tenía la información. El fragmento correcto existía: fallo de **recuperación**. Y con otra redacción («¿Cuánto tiempo tengo para devolver una bici?») lo entendió como una devolución y pidió el email: otro fallo de **interpretación**.
- **Conversación 5**: correcto: interpretar → escalar → redactar, caso urgente e instrucciones de seguridad.

Esos fallos se miden el día 2.

---

## Idea clave

> **El modelo entiende y redacta. El código decide.**

Un agente con modelo de lenguaje entiende casi cualquier mensaje, pero improvisa. Para que una conversación de atención al cliente sea fiable, se le da estructura: un **estado explícito** que recuerda lo que sabe, un **grafo** en el que el código decide qué hacer en cada turno (con la seguridad siempre la primera) y unas **reglas de diseño** claras: decir que es una IA, una pregunta por turno, confirmar lo que tiene efecto, reparar en tres escalones y pasar a una persona con contexto.

## Resumen de la sesión

- Un agente **conversacional** decide en cada turno si pregunta, actúa o pasa a una persona, y se evalúa por la conversación entera.
- **Diseño**: tono cercano, bienvenida que dice que es una IA, una pregunta por turno, leer sin preguntar y escribir con un sí claro, reparación en tres escalones, idioma del cliente e identificar por email antes de dar datos.
- **Cuándo persona**: siempre con seguridad, si la pide o por una regla de negocio (> 1.500 €); después de intentarlo, con tres fallos, sin taller o con una herramienta caída.
- El **ReAct genérico** falla en memoria, comprobaciones, política y seguridad. El **grafo** lo arregla: interpretar (modelo) → `ruta()` (código, 7 reglas en orden) → nodo con herramientas MCP → redactar (modelo).
- **Telegram** con polling para desarrollar; webhook (y ngrok) para producción y para Twilio el día 3.
- En el chat de VS Code: `AGENTS.md` siempre, la skill cuando encaja y el subagente revisor con contexto limpio y solo lectura. No confundir sus instrucciones con las del agente de Ondo.
