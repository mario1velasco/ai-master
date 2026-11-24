# Tutorial: crear tu bot de Telegram y conseguir su token

**La idea en una frase:** Telegram no deja que cualquier programa hable por él. Primero le pides a
Telegram un bot (una cuenta especial para programas) y Telegram te da una **llave**: el *token*. Con
esa llave, el agente de Ondo puede leer los mensajes que le escriben a tu bot y contestarlos.

Los bots se crean hablando con otro bot oficial de Telegram que se llama **BotFather** ("el padre de
los bots"). Es gratis y se tarda unos 5 minutos.

> Basado en la *Guía de Ejercicio de Clase · Día 1* (paso 1 y paso 2) y en el código del kit
> (`canales/telegram_bot.py`).

---

## ▶️ Cada vez que quieras probar el bot

El bot ya está creado. **Solo contesta mientras este programa está abierto en una terminal.** Si no
lo arrancas, Telegram guarda tus mensajes y no te contesta nadie.

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.telegram_bot
```

Espera a ver `Bot @ondo_soporte_mario_bot listo` y **no cierres esa terminal**. Después, en
Telegram: `t.me/ondo_soporte_mario_bot` → `/reset` → a probar. Para pararlo: `Ctrl+C`.

---

## Lo que necesitas antes de empezar

- Una cuenta de Telegram (la del móvil vale).
- Telegram abierto en el móvil, en el ordenador (app de escritorio) o en el navegador
  (`web.telegram.org`). Da igual cuál: el bot es el mismo.
- El kit `ondo-agente` instalado (ya está: `.venv` creado y dependencias instaladas).

---

## Paso 1 · Abre el chat con BotFather

1. En Telegram, pulsa la **lupa** (buscar) y escribe `BotFather`.
2. Elige el que se llama **@BotFather** y tiene la **marca azul de verificado** ✔.
   Hay imitadores con nombres parecidos: si no tiene la marca azul, no es el bueno.
3. Abre el chat y pulsa **Iniciar** (o escribe `/start`). BotFather te contesta con la lista de
   cosas que sabe hacer.

---

## Paso 2 · Pide un bot nuevo con `/newbot`

Escribe:

```
/newbot
```

BotFather te hará **dos preguntas**, una detrás de otra.

### Pregunta 1 · El nombre (lo que verán los clientes)

Es el nombre "bonito" que sale arriba del chat. Puede tener espacios y mayúsculas. Ejemplo:

```
Ondo Soporte Mario
```

### Pregunta 2 · El *username* (la dirección del bot)

Es como la dirección de correo del bot: **única en todo Telegram**, sin espacios y **tiene que
terminar en `bot`**. Ejemplo:

```
ondo_soporte_mario_bot
```

Si BotFather te dice que ya está cogido (*"Sorry, this username is already taken"*), prueba otro
añadiendo algo tuyo: `ondo_mario_2026_bot`, `ondo_soporte_mv_bot`…

---

## Paso 3 · Copia el token

Si todo va bien, BotFather responde con un mensaje que incluye dos cosas importantes:

- El **enlace a tu bot**: `t.me/ondo_soporte_mario_bot` (guárdalo: es por donde le escribirás).
- El **token**, que tiene esta forma:

```
1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
└───┬────┘ └──────────────┬──────────────────┘
 número del bot      la parte secreta
```

Es decir: **unos números, dos puntos `:` y una ristra larga de letras, números, `_` y `-`**.
Cópialo entero (en el móvil, mantén pulsado el token; en el ordenador, haz clic sobre él y suele
copiarse solo).

> 🔒 **El token es una contraseña.** Quien lo tenga controla tu bot: puede leer lo que le escriben y
> contestar en su nombre. No lo pegues en el chat de VS Code, ni en capturas, ni en git. Su sitio es
> solo el `.env` (que git ignora).

---

## Paso 4 · Pégalo en el `.env`

1. En VS Code, abre `10_agentes_conversacionales/ondo-agente/.env`.
2. Busca la línea `TELEGRAM_BOT_TOKEN=` y pega el token **justo detrás del `=`**:

   ```
   TELEGRAM_BOT_TOKEN=1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
   ```

   - Sin espacios antes ni después del `=`.
   - Sin comillas.
   - Todo en una sola línea.

3. Aprovecha y comprueba que tienes también estas líneas (son las de Claude y el RAG):

   ```
   LLM_PROVEEDOR=anthropic
   ANTHROPIC_MODEL=claude-haiku-5-5
   RAG_EMBEDDINGS=ollama
   RAG_UMBRAL=0.5
   ```

4. **Guarda el fichero con `Ctrl+S`.** Fíjate en la pestaña: si tiene un **punto ●** en lugar de
   la ✕, el fichero **no está guardado** y el bot no verá el token.

---

## Paso 5 · Arranca el bot

En una terminal (el entorno virtual se activa con `source`):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.telegram_bot
```

Si todo está bien verás una línea así:

```
... INFO Bot @ondo_soporte_mario_bot listo. Escríbele en Telegram (Ctrl+C para parar).
```

**Mientras esa terminal esté abierta, el bot contesta.** Si la cierras o pulsas `Ctrl+C`, deja de
hacerlo.

> **¿Por qué no hace falta una URL pública?** El bot funciona en modo *polling*: es tu programa el
> que pregunta a Telegram cada poco "¿hay mensajes nuevos?". La conexión sale de tu portátil, así que
> Telegram no necesita encontrarte. (El día 3, con Twilio, será al revés: Twilio te llama a ti, y por
> eso hará falta ngrok.)

---

## Paso 6 · Pruébalo

1. Abre el enlace `t.me/tu_username_bot` que te dio BotFather (o búscalo por su username).
2. Pulsa **Iniciar**: el bot te da la bienvenida (`/start`).
3. Escribe, en dos mensajes:

   ```
   ¿Dónde está mi pedido?
   ```
   ```
   lucia.martin@example.com
   ```

   Debe reconocer a Lucía y decirte cómo va su pedido `OND-10231`.
4. Escribe `Hola` y pulsa uno de los **botones** que salen debajo de la respuesta.
5. `/reset` empieza una conversación nueva.

En la terminal del bot verás una línea por cada mensaje:

```
... INFO chat 123456789 | cliente: ¿Dónde está mi pedido? | ondo: ...
```

Para pararlo: `Ctrl+C` en esa terminal.

---

## Si algo falla

| Lo que ves | Por qué pasa | Qué hacer |
|---|---|---|
| `Falta TELEGRAM_BOT_TOKEN en el .env` | El token no está, o el `.env` no está guardado | Paso 4: pégalo y **guarda con Ctrl+S** |
| `telegram.error.InvalidToken` | Token mal copiado (le falta un trozo, tiene un espacio…) | Cópialo de nuevo de BotFather (ver abajo cómo recuperarlo) |
| `Conflict: terminated by other getUpdates request` | Tienes el bot arrancado en dos terminales | Cierra una de las dos |
| El bot no contesta nada | El bot no está arrancado (no hay ninguna terminal con `python -m canales.telegram_bot`) | Arráncalo (ver «Cada vez que quieras probar el bot», arriba). Los mensajes que mandaste mientras estaba parado los contesta al arrancar |
| El bot no contesta | La terminal del bot está parada o ha dado un error | Mira la terminal: cada mensaje deja una línea de log |
| El bot contesta «Perdona, he tenido un problema técnico» | Ha fallado el modelo (Claude); el motivo sale en la terminal tras `ERROR Error del agente` | Lee el error de la terminal; el más típico es el de la fila siguiente |
| `Your credit balance is too low to access the Anthropic API` | Tu cuenta de Anthropic se ha quedado sin crédito | Consola de Anthropic → **Plans & Billing** → compra crédito. Haiku es muy barato: una clase de pruebas cuesta céntimos |
| `telegram.error.NetworkError: httpx.ConnectError` al arrancar | Un corte de red pasajero al conectar con Telegram | Vuelve a arrancar el bot |
| `RuntimeError: Attempted to exit cancel scope…` al pulsar `Ctrl+C` | Ruido al cerrarse el programa | Nada: es normal y no afecta |
| `ModuleNotFoundError: No module named ...` | El entorno virtual no está activado | `source .venv/bin/activate` y repite |

### He perdido el token o creo que se ha filtrado

- **Volver a verlo:** en el chat de BotFather escribe `/mybots`, elige tu bot y pulsa **API Token**.
- **Cambiarlo por uno nuevo** (si se ha filtrado): `/mybots` → tu bot → **API Token** →
  **Revoke current token**. El token viejo deja de funcionar al momento; pega el nuevo en el `.env`.

---

## Resumen

```
@BotFather ──/newbot──► nombre + username (…bot) ──► TOKEN
                                                        │
                                   .env: TELEGRAM_BOT_TOKEN=…  (Ctrl+S)
                                                        │
                              python -m canales.telegram_bot ──► «Bot @… listo»
                                                        │
                                   t.me/tu_bot ──► Iniciar ──► ¡a probar!
```
