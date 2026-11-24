# Cómo funciona el agente de Ondo: el grafo y la devolución paso a paso

**La idea en una frase:** tu mensaje entra por Telegram, el agente mira en qué punto de la
conversación estáis, **Claude entiende** lo que has escrito, **el código decide** qué hacer (pedir un
dato, llamar a una herramienta, pasar a una persona) y **Claude redacta** la respuesta. Después todo
vuelve por Telegram.

---

## 1. Las piezas: qué hace cada fichero

| Fichero | Papel | Con un ejemplo de la vida real |
|---|---|---|
| `canales/telegram_bot.py` | Recibe los mensajes de Telegram y envía las respuestas (texto y botones) | El recepcionista que coge el teléfono |
| `agente/agente.py` | La puerta del agente: busca la conversación de ese chat y le pasa el mensaje al grafo | El que saca la ficha del cliente del archivador |
| `agente/estado.py` | Define la **ficha** de la conversación: quién es el cliente, qué quiere, qué dato esperamos… | La ficha en sí |
| `agente/grafo.py` | El **mapa de decisiones**: los pasos (nodos) y la función `ruta()`, que elige el siguiente paso | El protocolo de atención al cliente |
| `agente/llm.py` | Las tres llamadas a Claude: **interpretar**, **redactar** y **resumir** | El que lee entre líneas y el que escribe bien |
| `agente/flujos/devolucion.py` | Los pasos propios de una devolución | El procedimiento de devoluciones |
| `agente/flujos/comun.py` | Piezas compartidas: el `borrador` (qué hay que decir) y el menú de 4 botones | Plantillas comunes |
| `agente/herramientas.py` | El cable con el servidor MCP: llama a una herramienta por su nombre | La centralita interna |
| `ondo_mcp/server.py` | Las 7 herramientas de Ondo (`buscar_cliente`, `escalar_a_humano`, `crear_devolucion`…) | Los departamentos de la empresa |
| `ondo_mcp/datos.py` | Lee `data/*.json` y guarda lo nuevo en `data/estado/` | El archivo |

---

## 2. Al arrancar el bot

Cuando ejecutas `python -m canales.telegram_bot`:

1. `telegram_bot.py` lee el token del `.env` y se conecta a Telegram.
2. Crea el agente (`agente.py`), que a su vez:
   - arranca el **servidor MCP** (`ondo_mcp/server.py`) como un programa aparte y se queda conectado
     a él (`herramientas.py`);
   - monta el **grafo** (`grafo.py`) con una memoria donde guardar la ficha de cada conversación.
3. Sale `Bot @ondo_soporte_mario_bot listo` y el bot se pone a preguntar a Telegram cada poco: «¿hay
   mensajes nuevos?» (*polling*).

> Esa memoria vive dentro del programa: si paras el bot, las conversaciones se olvidan. Lo que crean
> las herramientas (casos, devoluciones, citas) sí queda guardado en `data/estado/`.

---

## 3. El viaje de un mensaje cualquiera (un turno)

```
Tú en Telegram
   │
   ▼
telegram_bot.py ── contestar() ── pone «escribiendo…»
   │
   ▼
agente.py ── responder() ── saca la ficha de ESTE chat y añade tu mensaje
   │
   ▼
grafo.py
   interpretar ──► llm.py: Claude rellena una ficha con lo que has dicho
       │            (intención, idioma, email, nº de pedido…)
       ▼
   ruta()  ──► código normal, sin IA: decide el siguiente paso
       │
       ▼
   un nodo (identificar, flujo, escalar, informar, saludar…)
       │   hace el trabajo: llama herramientas y deja un BORRADOR
       │   («qué hay que decir»)
       ▼
   redactar ──► llm.py: Claude convierte el borrador en el mensaje final
                 (tono de Ondo, tu idioma, sin markdown)
   │
   ▼
telegram_bot.py ── envía el texto y los botones
```

Tres ideas que explican todo el diseño:

- **El modelo solo entiende y redacta. Las decisiones las toma el código** (`ruta()`). Por eso el
  agente no se inventa pasos ni se salta ninguno.
- **Borrador frente a redactar:** cada nodo decide *qué* decir y `redactar` decide *cómo* decirlo.
- **La ficha (estado) recuerda en qué punto estáis.** Por eso, cuando escribes solo un email, el
  agente sabe que es la respuesta a lo que te había preguntado.

---

## 4. El grafo por dentro (`agente/grafo.py`)

### La idea: un edificio de tres pisos

Cada mensaje baja por tres pisos, siempre en este orden:

```
                         📩 mensaje del cliente
                                  │
  PISO 1 · ENTENDER        ┌──────▼──────┐
  (Claude + reglas fijas)  │ interpretar │
                           └──────┬──────┘
                                  │
                           ruta() elige UNA puerta  ← código normal, sin IA
                                  │
  PISO 2 · DECIDIR Y HACER        │
  ┌─────────┬───────────┬─────────┼──────────┬──────────┬──────────┐
  ▼         ▼           ▼         ▼          ▼          ▼          ▼
escalar  ya_escalado  reparar  identificar  flujo    informar   saludar
  │         │           │         │          │          │          │
  │  (cada uno deja un BORRADOR: «qué hay que decir»)   │          │
  └─────────┴───────────┴─────────┼──────────┴──────────┴──────────┘
                                  │
  PISO 3 · ESCRIBIR        ┌──────▼──────┐
  (Claude)                 │  redactar   │  tono de Ondo, idioma, sin markdown
                           └──────┬──────┘
                                  ▼
                                 FIN → respuesta al cliente
```

### Piso 1 · `interpretar`

Claude lee el mensaje y rellena una ficha: qué quiere, en qué idioma, email, número de pedido y
ciudad. Después, el código **corrige a Claude** con reglas fijas que no dependen de la IA:

- Si el texto es exactamente un botón del menú → esa intención.
- Si aparece una palabra de `PELIGRO` («humo», «quemado», «se calienta»…) → **seguridad**, diga lo
  que diga Claude.
- Si aparece «revis» → motivo de la cita «revisión»; si aparece «avería», «no funciona»… → «avería».
- Si cambias de tema (de pedido a devolución, por ejemplo) → se vacía el flujo anterior, pero el
  agente sigue sabiendo quién eres.

### La puerta · `ruta()`

Mira la ficha y **comprueba las reglas en orden; manda la primera que se cumple**:

| # | Si… | va a |
|---|---|---|
| 1 | es de seguridad | `escalar` |
| 2 | ya hay un caso abierto con una persona | `ya_escalado` |
| 3 | pide hablar con una persona | `escalar` |
| 4 | no se le entiende | `reparar` (o `flujo`, si el flujo estaba esperando un dato) |
| 5 | pedido, devolución o cita | `flujo` si ya sabemos quién es; si no, `identificar` |
| 6 | pregunta sobre la política de Ondo | `informar` |
| 7 | cualquier otra cosa (hola, gracias) | `saludar` |

El orden importa. La seguridad va la primera para que nada se le adelante. Y si ya hay un caso
abierto, el bot no empieza otra cosa.

### Piso 2 · los 7 nodos

| Nodo | Qué hace | Herramienta MCP |
|---|---|---|
| `escalar` | Claude resume la conversación y se abre un caso para una persona (urgente si es de seguridad) | `escalar_a_humano` |
| `ya_escalado` | Solo te recuerda tu número de caso. No llama a nada, porque el caso ya existe | — |
| `reparar` | No te entendió: la 1.ª vez te pide que lo digas de otra forma, la 2.ª que elijas un botón y la 3.ª te pasa a una persona | — |
| `identificar` | Te pide el email y te busca. A los 3 emails que no encuentra, te pasa a una persona | `buscar_cliente` |
| `flujo` | Reparte a `flujos/pedido.py`, `devolucion.py` o `cita.py` | depende del flujo |
| `informar` | Busca en la política (RAG) y contesta solo con lo que encuentra | `buscar_conocimiento` |
| `saludar` | Saluda, dice que es una IA y enseña 3 botones | — |

### ¿En qué momento se llama al servidor MCP?

**Primero se decide y después, si hace falta, un nodo del piso 2 llama al MCP.** Ni `interpretar` ni
`ruta()` llaman nunca al MCP:

```
PISO 1   interpretar     → solo Claude (entender)                 ✗ sin MCP
PUERTA   ruta()          → solo código (decidir)                  ✗ sin MCP
PISO 2   el nodo elegido → AQUÍ se llama al MCP, si hace falta    ✓
PISO 3   redactar        → solo Claude (escribir)                 ✗ sin MCP
```

En el piso 2, solo algunos nodos llaman al MCP:

| Nodo | ¿Llama al MCP? | Herramienta |
|---|---|---|
| `identificar` | ✓ | `buscar_cliente` |
| `flujo` | ✓, depende del flujo | pedido → `estado_pedido`; cita → `huecos_taller`; devolución → ninguna todavía |
| `informar` | ✓ | `buscar_conocimiento` |
| `escalar` | ✓ | `escalar_a_humano` |
| `reparar`, `saludar`, `ya_escalado` | ✗ | no necesitan datos |

**Cómo llama un nodo al MCP:** el grafo se construye con `construir_grafo(herramientas)`, y
`herramientas` es la conexión con el servidor MCP (`herramientas.py`). Cualquier nodo que necesite
datos escribe `herramientas.llamar("buscar_cliente", email=...)`, y `herramientas.py` le pasa la
petición al servidor (`ondo_mcp/server.py`), que lee `data/`. (Dentro de los flujos, la misma
conexión se sigue llamando `h`, como en clase.)

### Los desvíos: tres nodos pueden acabar en `escalar`

Casi todos los nodos van directos a `redactar`. **Tres** pueden desviarse antes hacia una persona:

```
reparar ─────┐  3.er intento sin entenderte
identificar ─┤  3.er email que no existe
flujo ───────┘  el flujo decide que lo lleve una persona (p. ej. la devolución hoy)
      │
      ├── sí ──► escalar ──► redactar
      └── no ──────────────► redactar
```

En el código, estos desvíos son las funciones `tras_nodo` y `tras_identificar`. Las dos miran lo
mismo: si el nodo ha dejado la intención en «persona», se desvía a `escalar`.

`identificar` tiene una salida más: si te encuentra, va **directo a `flujo` en el mismo turno**. Por
eso, al dar tu email, el bot te contesta ya con tu pedido y no con un «gracias, ya te tengo».

### Dónde se conecta todo

Al final de `grafo.py` se monta el edificio con dos tipos de flechas:

- **`add_edge(A, B)`, flecha fija:** de A siempre se va a B. Por ejemplo, `informar`, `saludar`,
  `escalar` y `ya_escalado` → `redactar`.
- **`add_conditional_edges(A, función, [opciones])`, flecha con cruce:** la función elige el camino.
  Por ejemplo, `interpretar` → `ruta()` → una de las 7 puertas.

### La frase para recordar

**Claude entiende (piso 1) y Claude escribe (piso 3). Lo de en medio lo decide el código.** Por eso el
agente no se salta pasos ni se inventa caminos. Ese es el fallo del agente ReAct genérico
(`agente/react_fallo.py`), que deja todas las decisiones al modelo.

---

## 5. La devolución, turno a turno

Ejemplo real con Lucía Martín (cliente `C001`), probado en la consola con `--traza`.

### Turno 1 · «Quiero devolver un producto»

| Paso | Fichero | Qué pasa |
|---|---|---|
| 1 | `telegram_bot.py` | Llega el mensaje y se le pasa al agente |
| 2 | `agente.py` | Saca la ficha de tu chat (vacía, porque la conversación es nueva) |
| 3 | `grafo.py` → `llm.py` | **interpretar**: Claude entiende que la intención es *devolución*, en español, sin email. El código comprueba además dos cosas que no dependen del modelo: si has pulsado un botón del menú y si hay palabras de peligro («humo», «quemado»…) |
| 4 | `grafo.py` | **ruta()**: quieres una devolución, pero no sabemos quién eres, así que el siguiente paso es *identificar*. `ruta()` solo decide: no llama a nada |
| 5 | `grafo.py` | **identificar**: no hay email, así que deja el borrador «pídele su email» y apunta en la ficha que **está esperando el email** |
| 6 | `grafo.py` → `llm.py` | **redactar**: Claude escribe *«Claro, te ayudo con la devolución. Para poder localizar tu pedido, ¿me indicas el email que usaste en la compra?»* |
| 7 | `telegram_bot.py` | Te lo envía |

Así queda la ficha: intención = devolución · esperando = email · cliente = ninguno.

### Turno 2 · «lucia.martin@example.com»

| Paso | Fichero | Qué pasa |
|---|---|---|
| 1–2 | `telegram_bot.py`, `agente.py` | Igual que antes, pero ahora la ficha ya dice «esperando email» |
| 3 | `grafo.py` → `llm.py` | **interpretar**: Claude ve que el mensaje responde a lo que esperábamos (*continuar*) y saca el email. La intención sigue siendo *devolución* porque la ficha la recuerda |
| 4 | `grafo.py` | **ruta()** → *identificar* |
| 5 | `grafo.py` → `herramientas.py` → `ondo_mcp/server.py` → `datos.py` | Ya en el piso 2, el nodo **identificar** llama al MCP: la herramienta `buscar_cliente`, que busca el email en `data/clientes.json`. Encuentra a Lucía, que tiene 2 pedidos: `OND-10231` (enviado) y `OND-10232` (entregado) |
| 6 | `agente/flujos/devolucion.py` | Ahora que el agente sabe quién eres, pasa al **flujo de devolución**. **Hoy (día 1) este flujo todavía está vacío:** se limita a decir «esto lo lleva una persona, motivo: devolución» |
| 7 | `grafo.py` → `llm.py` | **escalar**: Claude escribe un **resumen** para la persona del equipo (qué quiere el cliente, qué datos tenemos, de qué humor está), para que no tengas que repetir nada |
| 8 | `herramientas.py` → `server.py` → `datos.py` | La herramienta `escalar_a_humano` crea el caso (`CASO-0001`) en `data/estado/escalados.json` y devuelve cuándo te atenderán: en unos minutos si es horario laboral y, si no, el siguiente día laborable |
| 9 | `grafo.py` → `llm.py` | **redactar**: «paso tu consulta a una persona del equipo, no tendrás que repetir nada, tu número de caso es…» |
| 10 | `telegram_bot.py` | Te lo envía |

### Turno 3 y siguientes

La ficha ya tiene un caso abierto, así que `ruta()` lleva siempre a **ya_escalado**: el bot te
recuerda que una persona lleva tu consulta y te da el número de caso. Para empezar de cero, escribe
`/reset`.

---

## 6. Lo que hará la devolución cuando esté completa (día 2)

El código deja la tarea marcada en `agente/flujos/devolucion.py`, y la política está en
`data/conocimiento/devoluciones.md`. La idea es que el flujo:

1. Pregunte **qué pedido** quieres devolver (Lucía tiene dos).
2. Consulte la **política** con la herramienta `buscar_conocimiento` (el RAG).
3. Compruebe el **plazo** (30 días desde la entrega) y el **importe** (más de 1.500 € → lo revisa una
   persona).
4. Si se cumple todo, llame a `crear_devolucion`, que registra `DEV-0001` en
   `data/estado/devoluciones.json` y programa la recogida a 2 días laborables. Si no se cumple, pasa a
   una persona.

Lo veremos en clase.

---

## 7. Resumen

```
Telegram ─► telegram_bot.py ─► agente.py (ficha del chat)
                                   │
                                   ▼
                       grafo.py: interpretar (Claude)
                                   │
                                 ruta()  ← el código decide
                                   │
              identificar ──► flujos/devolucion.py ──► escalar
                   │                                     │
                   └── herramientas.py ─► ondo_mcp/server.py ─► data/
                                   │
                       redactar (Claude) ─► telegram_bot.py ─► Telegram
```
