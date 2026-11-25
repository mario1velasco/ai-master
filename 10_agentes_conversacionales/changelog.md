# Changelog — Tema 10 · Agentes conversacionales (kit `ondo-agente`)

Todo lo que ha hecho falta para poner a funcionar `ondo-agente`, siguiendo la
**Guía de Ejercicio de Clase · Día 1 · Agente de chat en Telegram** (`clase_01/`).
Lo más reciente, arriba.

## Pendiente (lo hace Mario)

Siguen el orden de la guía del día 1:

1. **Clave y modelos** (guía, apartado 2): en `ondo-agente/.env`, `LLM_PROVEEDOR=anthropic` y
   `ANTHROPIC_API_KEY` (hecho) y **añadir `RAG_EMBEDDINGS=ollama`**. Después, con el entorno activado:
   `python scripts/comprobar_entorno.py` → debe terminar en «Todo listo» (el aviso de ngrok
   no importa hasta el día 3).
2. **Bot de Telegram** (paso 1): en Telegram, `@BotFather` → `/newbot` → nombre → username
   acabado en `bot`. Pegar el token en `.env` detrás de `TELEGRAM_BOT_TOKEN=`.
3. **Arrancar el bot** (paso 2): `python -m canales.telegram_bot` → debe salir
   «Bot @… listo». Probar `¿Dónde está mi pedido?` + `lucia.martin@example.com` y los botones
   tras un `Hola`.
4. **Entender el agente** (paso 3): preguntas al chat de VS Code en modo *Ask* y las cuatro
   pruebas con `python -m canales.consola --traza` (memoria, seguridad, pedido ajeno,
   reparación).
5. **AGENTS.md, skill y subagente** (paso 4): abrir los tres ficheros y contrastarlos con el chat.

## 2026-11-25 — qwen3 en Ollama con `--qwen` (o `LLM_PROVEEDOR=ollama`)

- **Qué:** el agente puede usar `qwen3:4b-instruct` en local, sin coste. Dos formas:
  - Por terminal, sin tocar el `.env`: `--qwen` en `python -m canales.consola`, `python -m canales.telegram_bot`
    y `python -m evaluacion.suite`. Sin el flag, todo sigue con el modelo del `.env` (Claude).
  - Por `.env`: `LLM_PROVEEDOR=ollama` y, si se quiere otro modelo, `OLLAMA_MODEL`.
- **Cómo:** `agente/llm.py`: `modelo()` devuelve `ChatOllama` con el proveedor `ollama`, y `usar_qwen()` cambia
  `PROVEEDOR` y `MODELO` para todo el proceso. Como el cliente simulado y el juez también llaman a `modelo()`, en
  la suite `--qwen` lo cambia **todo** (agente, cliente simulado y juez). Los tres comandos dicen al arrancar qué
  modelo usan, y el `informe.md` de la suite lo anota. `comprobar_entorno.py` no pide clave con `ollama`.
  `.env.example` documenta las dos formas. Sin dependencias nuevas: `langchain-ollama` ya estaba por bge-m3.
- **Comprobado (en mi máquina, 25/11/2026):** `pytest` (6 tests) pasa. En la consola con `--traza --qwen`,
  «¿dónde está mi pedido?» + `lucia.martin@example.com` llega bien a `buscar_cliente` y `estado_pedido`. Pero el
  «Hola» inicial lo interpretó como `no_entendido` (con Claude, `saludo`): el modelo pequeño falla más al interpretar.
- **Al traer cambios del profesor:** `canales/consola.py`, `canales/telegram_bot.py` y `evaluacion/suite.py`
  también llevan cambios locales; se suman a la lista de ficheros que hay que mezclar a mano.

## 2026-11-24 — `grafo.py` con nombres que se entienden

- Solo nombres, misma lógica: `e` → `estado`, `h` → `herramientas`, `it` → `interpretacion`,
  `r` → `resultado`, `b` → `borrador_respuesta`, `res` → `respuesta`, `nueva` → `nueva_intencion`,
  `g`/`n`/`fn` → `grafo`/`nodo`/`funcion`. En `ruta()`, `intencion_mensaje` (lo que pide este mensaje)
  frente a `intencion_en_curso` (lo que estaba en marcha).
- Los flujos (`flujos/*.py`) siguen con `(estado, h)`, como en clase y en la skill `completar-flujo`.
- Comprobado: `ruff check` y `pytest` (6 tests) pasan, y en la consola el saludo + pedido, la devolución
  y la seguridad recorren los mismos nodos que antes.
- Es un fichero del profesor: al traer sus cambios, **mezclar a mano** (sus cambios usarán `e`/`h`).

## 2026-11-24 — Arreglo: pasar a una persona fallaba con Claude

- **Síntoma:** en devoluciones, seguridad o «quiero hablar con una persona», el bot contestaba «Perdona,
  he tenido un problema técnico» (en la terminal: `KeyError: 'caso'`).
- **Causa:** Haiku 5.5 a veces piensa antes de responder y `resumir()` devolvía `res.content`, que
  entonces es una lista de bloques (pensamiento + texto). La herramienta `escalar_a_humano` solo acepta
  texto en `resumen` y daba un error de validación.
- **Arreglo:** `agente/llm.py`, `resumir()` devuelve `res.text` (solo el texto). Con OpenAI no cambia
  nada. Probado 3 veces en la consola: devolución de Lucía → `CASO-0001..0003` y el turno siguiente
  pasa por `ya_escalado`. Al traer los cambios del profesor, **mantener esta línea**.
- De paso: `ondo-agente/como-funciona-el-agente.md` explica el viaje de un mensaje, el grafo por dentro
  (los tres pisos, `ruta()` y los desvíos a `escalar`) y la devolución fichero a fichero, y `clase_01/tutorial-bot-telegram.md` recuerda arriba del todo cómo arrancar el bot.

## 2026-11-24 — El kit entra en `ebis` (borrado su `.git`)

- Para ver los cambios del kit en el git de `ebis` (VS Code no detecta un repo anidado a dos niveles),
  se borró `ondo-agente/.git`. No tenía commits locales ni stash: su historial está en GitHub (`43dafbd`).
- El `.gitignore` del kit sigue valiendo dentro de `ebis`: `.env`, `.venv/`, `data/estado/` y
  `data/.cache/` no entran. Comprobado con `git check-ignore`; `ebis` ve 51 ficheros del kit.
- Dos commits en `ebis`, para ver nuestros cambios como diff: primero el **kit original** (idéntico a
  un clon limpio de `43dafbd`, comprobado con `diff -r`) y después **los cambios para que funcione**
  (Claude, bge-m3, comprobador, dependencias y la sección de arquitectura del `AGENTS.md` del kit).
  `git diff <commit-original> -- 10_agentes_conversacionales/ondo-agente` enseña todo lo que hemos tocado.
- Se pierde el `git pull` del profesor: para los días 2 y 3, clonar su repo aparte, ver
  `git diff 43dafbd..origin/main` y aplicar los cambios a mano (pasos en `AGENTS.md`).
- **RAG con bge-m3, medido** (11 preguntas, mejor fragmento): las 7 que están en los documentos dan
  0,651–0,797 y aciertan documento y sección (también una en portugués); las 4 de fuera, 0,266–0,426.
  Con el umbral de 0,35 se cuela «¿Vendéis patinetes eléctricos para niños?» (0,426 → «Envíos»).
  Propuesta: `RAG_UMBRAL=0.5`.

## 2026-11-24 — Claude como modelo y bge-m3 (Ollama) para el RAG

La clave de OpenAI da **401** (`Incorrect API key provided`). Ni otra variable en la terminal ni el formato
de la línea lo explican (las comillas las quita `python-dotenv`), así que es la propia clave. Para no
depender de ella, el kit puede usar la cuenta de Anthropic de Mario. Todo va detrás de dos interruptores
y **por defecto sigue en OpenAI**, como el curso.

- **Modelo de chat → Claude Haiku 5.5** (`claude-haiku-5-5`, el más barato de Anthropic).
  - `agente/llm.py`: `modelo()` devuelve `ChatAnthropic` o `ChatOpenAI` según `LLM_PROVEEDOR`. Interpretar,
    redactar, resumir, el juez, el simulador y el ReAct pasan todos por ahí: no hay que tocar nada más.
  - Sin `temperature` con Claude: Haiku 5.5 rechaza con un 400 cualquier valor distinto del de por defecto.
  - La salida estructurada (`with_structured_output`) funciona tal cual. Probado con «la batería huele
    un poco a quemado al cargar» → `intencion: seguridad`.
- **Embeddings del RAG → bge-m3 en Ollama**. Anthropic no tiene API de embeddings. bge-m3 es el mismo
  modelo que usará travel-agency (allí con `sentence-transformers`, porque necesita también el reranker
  y no quiere competir por la GPU con qwen3; aquí no hay LLM local, así que Ollama no compite con nada).
  - `ondo_mcp/conocimiento.py`: `_embeddings()` elige según `RAG_EMBEDDINGS`. Las variables empiezan por
    `RAG_` para que lleguen al subproceso MCP sin tocar `agente/herramientas.py`.
  - La huella de la caché incluye el modelo: al cambiarlo, el índice de `data/.cache/` se recalcula solo.
  - `ollama pull bge-m3` (~1,2 GB).
- `requirements.txt`: bloque nuevo al final con `langchain-anthropic`, `langchain-ollama` y sus
  dependencias; `langchain-core` sube a 1.8.4 y `langchain-protocol` a 0.0.22.
- `.env.example`: `LLM_PROVEEDOR`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `RAG_EMBEDDINGS`, `RAG_OLLAMA_MODEL`.
- `scripts/comprobar_entorno.py`: comprueba la clave y llama al modelo del proveedor elegido; con
  `RAG_EMBEDDINGS=ollama`, comprueba también que Ollama calcula los embeddings.
- Resultado: «Todo listo» con `anthropic` / `claude-haiku-5-5` y 6 tests pasan.
- Ficheros tocados respecto al kit del profesor: `llm.py`, `conocimiento.py`, `comprobar_entorno.py`,
  `requirements.txt`, `.env.example` y `AGENTS.md`. Son los que habrá que mezclar a mano con sus cambios.

## 2026-11-24 — Entorno del kit listo (falta la clave)

- Comprobado que no hay cambios nuevos del profesor (`git fetch`: el kit sigue en `43dafbd`).
- Creado `ondo-agente/.venv` con **Python 3.12.13** (el recomendado). Se usa el CPython 3.12
  que instaló uv, no el `python3` de la terminal, que apuntaba al `.venv` de `travel-agency`.
- Instaladas las dependencias: `python -m pip install -r requirements.txt`.
- Copiado `.env.example` a `.env` (todavía sin clave ni token).
- `python scripts/comprobar_entorno.py`: Python, dependencias y servidor MCP (7 herramientas)
  correctos; **falla solo `OPENAI_API_KEY`**; ngrok sin instalar (no hace falta hasta el día 3).
- `python -m pytest`: **6 tests pasan** (pruebas del servidor MCP, sin clave).

## 2026-11-23 — Kit descargado y documentado

- Clonado el kit: `git clone https://github.com/alamasfu10/ondo-agente.git` (commit `43dafbd`).
  Conserva su propio `.git` para recibir con `git pull` los cambios de los días 2 y 3.
- El kit no se versiona en `ebis`, pero tampoco va en `.gitignore` para que se vea en la
  búsqueda de VS Code (`git status` lo muestra como `??`; nunca se añade).
- Añadida al `AGENTS.md` del kit una sección «Arquitectura del sistema» (cambio local, sin
  commit en el repo del kit).
- Escritos `10_agentes_conversacionales/AGENTS.md` y `clase_01/explicacion-10.md`.
