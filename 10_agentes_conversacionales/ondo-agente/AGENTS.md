# AGENTS.md · ondo-agente

Agente de atención al cliente de Ondo, una tienda online ficticia de bicicletas eléctricas. Es un grafo de LangGraph que atiende por consola y por Telegram, y usa las herramientas de un servidor MCP.

## Entorno

El proyecto usa un entorno virtual clásico en `.venv/`. Ejecuta Python siempre desde él, aunque tu terminal no lo tenga activado: `.venv/bin/python` en macOS y Linux, `.venv\Scripts\python` en Windows. En los comandos de abajo, `python` significa ese Python.

## Comandos

- Instalar dependencias: `python -m pip install -r requirements.txt`
- Tests (sin clave de OpenAI, sin red): `python -m pytest`
- Solo los tests de un fichero: `python -m pytest tests/test_<flujo>.py`
- Hablar con el agente en la terminal: `python -m canales.consola --traza` (recorrido por el grafo y estado en cada turno; `--estado` solo el estado)
- Bot de Telegram: `python -m canales.telegram_bot`
- Evaluación con conversaciones simuladas (usa la clave de OpenAI y cuesta céntimos): `python -m evaluacion.suite`, o `--solo <id>` para un escenario

No instales paquetes nuevos ni cambies `requirements.txt` sin que te lo pidan.

## Terminado significa

1. Los tests de lo que te han pedido pasan. Si te piden un solo paso de un flujo, los tests de los pasos que no te han pedido pueden seguir en rojo: dilo en tu resumen y no los toques.
2. Has explicado qué ficheros has cambiado y por qué, en pocas líneas.
3. No has tocado nada fuera de lo que se pidió.

## Dónde va cada cosa

- `agente/flujos/`: un fichero por flujo (pedido, cita, devolución). Aquí se trabaja casi siempre.
- `agente/grafo.py`: el enrutado entre nodos. Cámbialo solo si el cambio no cabe en un flujo.
- `agente/llm.py`: los prompts de interpretar y redactar.
- `ondo_mcp/` y `data/`: el servidor MCP y los datos de Ondo. Se dan hechos: no los modifiques.
- `evaluacion/`: la suite de evaluación. Los escenarios (`escenarios.json`) se pueden ampliar; no cambies lo que espera un escenario para que pase.

## Cómo se escribe un flujo

- Un flujo es una función `async def flujo_x(estado, h) -> dict` que devuelve solo los campos del estado que cambian.
- Cada paso pide un solo dato y anota en `pendiente` qué está esperando.
- Lo que el agente tiene que decir va en `borrador(instruccion, datos, opciones)`: qué decir y con qué datos, nunca el texto final. El nodo `redactar` escribe el mensaje con el tono de Ondo y en el idioma del cliente.
- Para saber qué opción eligió el cliente, usa `eleccion(estado, opciones)` de `agente/flujos/comun.py`.
- Las herramientas se llaman con `await h.llamar("nombre", argumento=valor)` y devuelven un dict.
- Al terminar un flujo, devuelve `fin_de_flujo()`, que conserva al cliente identificado.

## Reglas de la conversación

Son las reglas de diseño de Ondo. Cualquier cambio en un flujo las cumple:

- Una acción con efecto (`reservar_cita`, `crear_devolucion`) solo se ejecuta después de un «sí» claro: `estado["ultima"]["confirma"] is True` o el botón de confirmar. Una respuesta ambigua no cuenta como sí.
- Si no se entiende lo que elige el cliente, se suma uno a `intentos_fallidos` y se le vuelven a ofrecer las opciones. Al superar `MAX_REINTENTOS`, se pasa a una persona devolviendo `"intencion": "persona"`. Si se sabe el motivo, se guarda en `datos["motivo_escalado"]`.
- Nunca se inventan datos (fechas, códigos, importes, plazos): salen de las herramientas.
- Si una herramienta falla, no se da la operación por hecha y se le dice al cliente.
- La seguridad (batería que se calienta, frenos) la resuelve el grafo antes de llegar a los flujos. No la toques desde un flujo.

## Tests

- Los tests de flujos usan herramientas simuladas, sin modelo ni MCP, en `tests/test_<flujo>.py`. Dos piezas:
  - Una clase `HerramientasFalsas` con `async def llamar(self, nombre, **args)` que devuelve datos fijos (por ejemplo, `huecos_taller` con un taller y varios huecos, `reservar_cita` con éxito o con `{"ok": False, "error": ...}`), apunta cada llamada en una lista y lanza `AssertionError` si el flujo llama a una herramienta que no debería.
  - Una función que construye el estado a mano: `messages` con un `HumanMessage` del cliente, `cliente`, `datos`, `huecos`, `opciones`, `pendiente`, `intentos_fallidos` y `ultima` (la interpretación del modelo, con `intencion`, `eleccion` y `confirma`).
- Cada test llama a `await flujo_x(estado, herramientas)`, y comprueba el dict que devuelve (`pendiente`, `intencion`, `intentos_fallidos`, `borrador["opciones"]`...) y las herramientas llamadas. Los tests son `async def` sin decorador: `pytest.ini` ya los ejecuta.
- Si te piden los tests antes que el código, escríbelos desde la especificación que te den, sin implementar nada, y ejecútalos para comprobar que fallan por lo que falta, no por un error del propio test.
- Si un test falla porque el código está mal, se arregla el código. No cambies lo que espera un test para que pase.

## Límites

- Nunca leas, muestres ni copies el contenido de `.env`.
- No borres ficheros de `data/estado/` salvo que te lo pidan.

## Arquitectura del sistema

Resumen de cómo funciona el kit por dentro, sacado del código (kit del día 1, commit `43dafbd`). Sirve para orientarse antes de tocar nada; si el código cambia, manda el código.

### Visión general

```text
 Canal (consola · Telegram · API)                       Servidor MCP «ondo» (subproceso, stdio)
        │ texto del cliente                              ├─ buscar_cliente     ├─ reservar_cita
        ▼                                                ├─ estado_pedido      ├─ crear_devolucion
 AgenteOndo.responder(conversacion, texto)               ├─ huecos_taller      ├─ escalar_a_humano
        │ thread_id → checkpointer (estado en RAM)       └─ buscar_conocimiento (RAG)
        ▼                                                        ▲      │
 Grafo LangGraph:  interpretar → ruta() → nodo → redactar         │      ▼
                     (modelo)   (código)  (código+MCP) (modelo) ──┘   data/*.json (solo lectura)
        │                                                             data/estado/*.json (lo que crea)
        ▼
 RespuestaAgente(texto, opciones, estado)  → el canal pinta el texto y las opciones como botones
```

Principio de diseño: **el modelo entiende y redacta; el código decide**. El modelo solo interviene en `interpretar` (salida estructurada), `redactar` (texto final) y `resumir` (resumen para la persona al escalar). Qué hacer, qué herramienta llamar y cuándo pasar a una persona lo decide Python.

### Capas y ficheros

| Capa | Fichero | Responsabilidad |
|---|---|---|
| Canales | `canales/consola.py`, `canales/telegram_bot.py`, `app/main.py` | Reciben el texto, llaman a `AgenteOndo.responder()` y muestran texto + botones. No tienen lógica de negocio |
| Fachada | `agente/agente.py` | `AgenteOndo`: abre la sesión MCP, construye el grafo con `InMemorySaver` y traduce «id de conversación» → `thread_id` |
| Estado | `agente/estado.py` | `Estado` (TypedDict del grafo) e `Interpretacion` (esquema Pydantic de la salida estructurada) |
| Grafo | `agente/grafo.py` | Nodos, `ruta()`, red de seguridad `PELIGRO`, `MAX_INTENTOS = 3` |
| Flujos | `agente/flujos/{pedido,cita,devolucion}.py`, `comun.py` | Lógica paso a paso de cada intención con efecto o consulta de datos |
| Modelo | `agente/llm.py` | Prompts y llamadas al modelo (`interpretar`, `redactar`, `resumir`); `modelo()` elige OpenAI o Anthropic según `LLM_PROVEEDOR` |
| Herramientas | `agente/herramientas.py` | Cliente MCP (`langchain-mcp-adapters`), una sola sesión stdio; `Herramientas.llamar(nombre, **args) -> dict` |
| Servidor MCP | `ondo_mcp/server.py`, `datos.py`, `conocimiento.py` | Las 7 herramientas (FastMCP), acceso a datos y RAG |
| Evaluación | `evaluacion/` | Cliente simulado + comprobaciones con datos + juez LLM → informe |
| Demo | `agente/react_fallo.py` | Agente ReAct genérico (`create_agent`) para ver los fallos sin grafo |

### Configuración (`.env`)

| Variable | Por defecto | Uso |
|---|---|---|
| `LLM_PROVEEDOR` | `openai` | Modelo de chat de todo el kit: `openai` u `anthropic` (cambio local, no viene del kit) |
| `OPENAI_API_KEY` | — | Con `LLM_PROVEEDOR=openai`: agente, simulador y juez; y los embeddings si `RAG_EMBEDDINGS=openai` |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Modelo de chat con OpenAI (`agente/llm.py`) |
| `ANTHROPIC_API_KEY` | — | Con `LLM_PROVEEDOR=anthropic` |
| `ANTHROPIC_MODEL` | `claude-haiku-5-5` | Modelo de chat con Anthropic. Sin `temperature`: Haiku 5.5 la rechaza |
| `RAG_EMBEDDINGS` | `openai` | Embeddings del RAG: `openai` u `ollama` (Anthropic no tiene embeddings) |
| `OPENAI_EMBEDDINGS_MODEL` | `text-embedding-3-small` | Embeddings del RAG con OpenAI |
| `RAG_OLLAMA_MODEL` | `bge-m3` | Embeddings del RAG con Ollama (`ollama pull bge-m3`) |
| `RAG_UMBRAL` | `0.35` | Similitud mínima para que un fragmento cuente |
| `ONDO_ESTADO` | `data/estado/` | Carpeta donde el MCP guarda citas, devoluciones y casos (la suite la cambia) |
| `TELEGRAM_BOT_TOKEN` | — | Solo para `canales.telegram_bot` |

El subproceso MCP **no hereda todo el entorno**: `herramientas.py` solo le pasa las variables que empiezan por `OPENAI_`, `RAG_`, `ONDO_`, `PATH` y `HOME`. Una variable nueva que necesite el servidor tiene que seguir ese patrón.

### Un turno, paso a paso

1. **Canal → `AgenteOndo.responder(conversacion, texto)`**. El id de conversación (`"consola"`, `"telegram-<chat_id>"`, el id del escenario en la evaluación, o el que mande la API) se convierte en un `thread_id` = id + 6 caracteres aleatorios. `reiniciar()` olvida esa correspondencia, así que la siguiente vez sale un `thread_id` nuevo con el estado vacío.
2. **`interpretar`** (`grafo.py`):
   - Llama a `llm.interpretar()`: `gpt-4.1-mini` a temperatura 0 con `with_structured_output(Interpretacion)`, con los últimos 6 mensajes y, en el prompt, `pendiente`, `intencion` y las `opciones` mostradas.
   - Si el texto es exactamente un botón del `MENU`, la intención se fuerza (`MENU_INTENCION`).
   - Si el texto casa con la regex `PELIGRO` (quemad, humo, fuego, se calienta, hinchad, chispa, no frena, sin frenos… y equivalentes en en/fr/it/pt), la intención se fuerza a `seguridad`, **diga lo que diga el modelo**.
   - Copia `email`, `pedido_id` (en mayúsculas) y `ciudad` a `datos`. El `motivo` de cita **no** se toma del modelo: se busca en el texto con regex (`revis` → revisión; avería, no funciona, no enciende, roto, ruido, falla → avería).
   - Cambio de tema (nueva intención pedido/devolución/cita/información distinta de la actual): `fin_de_flujo()` y se conservan solo los datos de este mensaje. `continuar` y `no_entendido` no cambian la intención en curso.
   - `intentos_fallidos` vuelve a 0 con cualquier intención clara, se mantiene con `continuar` y no se toca con `no_entendido` (lo sube `reparar`).
3. **`ruta()`** elige el nodo con reglas en orden; gana la primera:
   1. seguridad (en el estado o en la última interpretación) → `escalar`
   2. ya hay `escalado` → `ya_escalado`
   3. intención `persona` → `escalar`
   4. `no_entendido` → `flujo` si hay flujo en curso con cliente y `pendiente` (repara el flujo); si no, `reparar`
   5. pedido/devolución/cita → `flujo` si hay `cliente`; si no, `identificar`
   6. información → `informar`
   7. lo demás → `saludar`
4. **Nodo de trabajo** (deja un `borrador` con *qué* decir; nunca el texto final):
   - `reparar`: intento 1 reformula, intento 2 pide elegir del `MENU`, intento 3 pone `intencion = persona` → `escalar`.
   - `identificar`: sin email lo pide (`pendiente = email`); con email llama a `buscar_cliente(email=...)`. Si no existe, suma un intento y lo vuelve a pedir; al tercero, persona. Si existe, guarda `cliente` (con su lista de pedidos) y sigue a `flujo` en el mismo turno. Solo identifica por email, aunque la herramienta admita pedido y teléfono.
   - `flujo`: delega en `flujo_pedido`, `flujo_cita` o `flujo_devolucion` según `intencion`.
   - `informar`: `buscar_conocimiento(pregunta=<texto literal del cliente>)`. Sin resultados, dice que no tiene información fiable y ofrece «Hablar con una persona» / «Otra consulta».
   - `saludar`: recuerda que es una IA y ofrece los tres primeros botones del `MENU`.
   - `escalar`: decide el motivo (seguridad > `datos.motivo_escalado` > pide persona > «no consigue resolver»), pide un resumen a `llm.resumir()` (últimos 12 mensajes + cliente + datos) y llama a `escalar_a_humano` con prioridad `urgente` si es seguridad. Guarda el caso en `escalado` y vacía `intencion` y `pendiente`.
   - `ya_escalado`: recuerda el número de caso.
5. **Aristas tras el nodo**: `reparar` y `flujo` van a `escalar` si dejaron `intencion = persona` y aún no hay caso (`tras_nodo`); si no, a `redactar`. `identificar` va a `escalar`, `flujo` o `redactar` (`tras_identificar`). El resto va directo a `redactar`.
6. **`redactar`**: `llm.redactar()` a temperatura 0.2 con `PERSONA_ONDO` (IA que lo admite, tuteo, frases cortas, una pregunta, sin markdown, sin inventar, no repetir los botones) en el idioma detectado. Devuelve `texto` y las `opciones` traducidas; si el modelo devuelve un número distinto de opciones, se usan las originales. Añade el `AIMessage`, guarda `opciones` y vacía `borrador`.
7. **Vuelta al canal**: `RespuestaAgente(texto, opciones, estado)`.

Coste por turno: 2 llamadas al modelo (interpretar + redactar), más 1 si se escala (resumir) y 1 embedding de la pregunta si pasa por `informar`.

### El estado (`agente/estado.py`)

| Campo | Qué guarda | Quién lo escribe |
|---|---|---|
| `messages` | Historial (reducer `add_messages`, se acumula) | canal (humano) y `redactar` (IA) |
| `ultima` | La `Interpretacion` del último mensaje (`intencion`, `idioma`, `email`, `pedido_id`, `ciudad`, `motivo`, `eleccion` en base 1, `confirma`) | `interpretar` |
| `intencion` | Intención **en curso** (no la del último mensaje) | `interpretar`, flujos, `escalar` |
| `idioma` | Código ISO del último mensaje | `interpretar` |
| `cliente` | Cliente identificado + `pedidos` resumidos | `identificar` (sobrevive a `fin_de_flujo`) |
| `datos` | email, pedido_id, ciudad, motivo, taller, pagina, motivo_escalado… | `interpretar`, flujos |
| `pendiente` | Qué dato espera: `email`, `pedido_id`, `motivo`, `ciudad`, `hueco`, `confirmar_cita` (previsto) | nodos y flujos |
| `opciones` | Botones mostrados en el último mensaje | `redactar` |
| `huecos`, `hueco_elegido` | Huecos ofrecidos y el elegido (el segundo se usa en el día 2) | `flujo_cita` |
| `intentos_fallidos` | Turnos seguidos sin entender | `interpretar`, `reparar`, `identificar`, flujos |
| `escalado` | Caso abierto (`id`, `prioridad`, `resumen`…) | `escalar` |
| `borrador` | `{instruccion, datos, opciones}` para `redactar` | nodos y flujos |

Memoria: `InMemorySaver`, es decir, **solo en RAM**. Se pierde al parar el proceso, cada `thread_id` guarda todos sus checkpoints y nada se borra (`reiniciar` deja el hilo viejo en memoria). En producción haría falta un checkpointer persistente (SQLite/Postgres) y una política de caducidad.

Una vez hay `escalado`, ese hilo va siempre a `ya_escalado` (salvo seguridad) hasta un `/reset`.

### Flujos (`agente/flujos/`)

- **`comun.py`**:
  - `borrador(instruccion, datos, opciones)`.
  - `MENU` con 4 botones: pedido, devolver, cita y persona.
  - `fin_de_flujo()`: vacía intención, pendiente, huecos, datos e intentos, y conserva `cliente`.
  - `eleccion(estado, lista)`: primero mira si el texto coincide exactamente con un botón; si no, usa `ultima.eleccion`. Devuelve un índice en base 0 o `None`.
- **`pedido.py`** (completo):
  1. Si no hay `pedido_id`, se queda con el único pedido activo (preparando, enviado o incidencia) o el único pedido. Si hay varios, ofrece hasta 4 como botones (`pendiente = pedido_id`).
  2. Llama a `estado_pedido`. Si el pedido no existe, vuelve a pedir el número.
  3. **Comprueba en código que `pedido.cliente_id == cliente.id`**. Si no coincide, no da ningún dato.
  4. Si todo va bien, explica estado, fechas, transportista, seguimiento e incidencia, y cierra con `fin_de_flujo()`.
- **`cita.py`** (a medias; `MAX_REINTENTOS = 2` definido pero aún sin usar):
  1. Motivo: Revisión o Avería.
  2. Ciudad: propone la del cliente y «Otra ciudad». Si escribe otra, la recoge `interpretar` en `datos.ciudad`.
  3. Llama a `huecos_taller`. Sin taller en la ciudad, da las ciudades con taller y el botón de persona. Sin huecos, persona. Si hay, ofrece 3 huecos con etiquetas tipo «Jueves 12/11 a las 10:00» (`pendiente = hueco`). La paginación está en `datos.pagina`, pero todavía nada la avanza.
  4. y 5. Elegir hueco, confirmar y `reservar_cita`: **TODO del día 2**. De momento responde «en construcción».
  - Fallo conocido: cuando el flujo repara (por ejemplo, la ciudad no se entiende), `intentos_fallidos` no sube.
- **`devolucion.py`** (por hacer): pasa siempre a persona con `motivo_escalado = "devolución"`. La política que tendrá que aplicar el día 2: 30 días naturales desde la entrega y más de 1.500 € → persona (`data/conocimiento/devoluciones.md`).

### Servidor MCP (`ondo_mcp/`)

Lo arranca el agente como subproceso (`python -m ondo_mcp.server`, transporte stdio, `FastMCP("ondo")`). También se puede inspeccionar con `mcp dev ondo_mcp/server.py`.

| Herramienta | Entrada | Devuelve / reglas |
|---|---|---|
| `buscar_cliente` | `email` \| `pedido_id` \| `telefono` | `{encontrado, cliente (id, nombre, email, ciudad, pais, idioma), pedidos resumidos}`. Teléfono por los últimos 9 dígitos |
| `estado_pedido` | `pedido_id` | El pedido completo con `cliente_id` (el agente debe comprobarlo) y la devolución si la hay, o `{error}` |
| `crear_devolucion` | `pedido_id, cliente_id, motivo` | Comprueba que el pedido es del titular, que está entregado y que no está duplicado. **No comprueba plazo ni importe**: lo decide el agente. Recogida a 2 días laborables. Id `DEV-0001`… |
| `huecos_taller` | `ciudad, dias=14` | Taller de la ciudad y hasta 12 huecos de 60 min desde mañana, según su `horario` por día de la semana (0 = lunes), sin los ya reservados; si no hay taller, `ciudades_con_taller` |
| `reservar_cita` | `cliente_id, hueco_id, motivo` | Revalida que el hueco siga libre. Id `CIT-0001`… |
| `escalar_a_humano` | `motivo, resumen, prioridad, cliente_id, canal="chat"` | Caso `CASO-0001`…; `espera` según prioridad y horario (L-V 9:00–19:00) |
| `buscar_conocimiento` | `pregunta` | Hasta 3 fragmentos ≥ umbral, o `{resultados: [], mensaje: "sin resultados"}` |

- **Datos** (`data/`, solo lectura):
  - 30 clientes (24 de España, 2 de Francia, 2 de Italia, 2 de Portugal; hay 2 que hablan inglés).
  - 40 pedidos: 20 entregados, 13 enviados, 5 preparando, 1 con incidencia y 1 devuelto. 13 pasan de 1.500 €.
  - 10 productos de catálogo (5 bicicletas y 5 accesorios).
  - 7 talleres: Madrid, Barcelona, Valencia, Sevilla, Lyon, Milán y Lisboa.
  - Las fechas de los pedidos están guardadas como `hace_dias_*` y `datos.pedidos()` las convierte a fechas reales desde **hoy**, así que el kit da los mismos plazos relativos cualquier día.
- **Lo que crea el agente** se guarda en `data/estado/{citas,devoluciones,escalados}.json` (o en `ONDO_ESTADO`). Borrar la carpeta empieza de cero.
- **RAG** (`conocimiento.py`):
  - Hay 10 documentos `.md` en `data/conocimiento/`. Cada sección `##` es un fragmento, con el texto «Título. Sección. Texto».
  - Embeddings con `text-embedding-3-small` en un `InMemoryVectorStore`, con caché en `data/.cache/indice.json` (se invalida por un hash del modelo y los textos).
  - Devuelve como mucho 3 resultados (`K = 3`) con similitud ≥ `RAG_UMBRAL`.
  - Fallo conocido (corrección del complementario 2): «¿Qué plazo de devolución tiene Ondo?» puede traer antes «Pagos y facturas» que «Devoluciones».

### Canales

- **Consola** (`canales/consola.py`):
  - Usa siempre la conversación `"consola"`. Escribir un número pulsa ese botón; `/reset` empieza de nuevo y `/salir` termina.
  - `--estado` imprime `intencion, cliente, datos, pendiente, intentos_fallidos, escalado, idioma` después de cada turno.
  - `--traza` usa `grafo.astream(stream_mode="updates")` para imprimir cada nodo con sus cambios, y engancha `Herramientas.trazar` para listar cada herramienta con sus argumentos y su resultado (recortados).
- **Telegram** (`canales/telegram_bot.py`):
  - Funciona en polling con `python-telegram-bot` y la conversación `"telegram-<chat_id>"`. Hay un solo `AgenteOndo`, que se crea en `post_init`.
  - Los botones son `InlineKeyboard` con el índice en `callback_data` (Telegram limita ese campo a 64 bytes) y las opciones guardadas en `chat_data`.
  - `/start` reinicia y envía una bienvenida fija (no la escribe el modelo). `/reset` reinicia.
  - Si el agente falla, contesta «problema técnico» y deja la excepción en el log.
- **API** (`app/main.py`):
  - FastAPI con `GET /salud` y `POST /chat {conversacion, texto} → {texto, opciones}`.
  - El agente se crea la primera vez que se usa, protegido con un `asyncio.Lock`.
  - Es la base del día 3: voz y Twilio por webhook con ngrok.

### Evaluación (`evaluacion/`, día 2)

- `python -m evaluacion.suite [--solo id1,id2] [--max-turnos 10] [--sin-juez] [--paralelo 4]`. Cada ejecución usa su propia carpeta `evaluacion/salidas/<fecha_hora>/` (pone `ONDO_ESTADO` en `…/estado`, así que no toca `data/estado/`) y deja ahí `informe.md` y `conversaciones.json`.
- **Simulador** (`simulador.py`): un modelo a temperatura 0.7 hace de cliente según el escenario (`cliente`, `objetivo`, `estilo`, `idioma`) y termina escribiendo `[FIN]`. La partida también se corta tras pasar a una persona.
- **Comprobaciones con datos** (`comprobaciones.py`, sin modelo): si hubo escalado, cita o devolución del cliente (leyendo `ONDO_ESTADO`), la prioridad y el idioma final contra lo `esperado`.
- **Juez** (`juez.py`): modelo a temperatura 0 con una rúbrica de 5 criterios (`una_pregunta`, `confirma`, `privacidad`, `idioma`, `sin_bucles`). Cada uno sale «cumple», «no cumple» o «no aplica»; ante la duda, «no cumple». No valora si se consiguió el objetivo: eso lo miran las comprobaciones.
- **Escenarios** (`escenarios.json`, 10): `pedido_en_camino`, `pedido_ajeno`, `cita_revision`, `cita_cambia_de_fecha`, `cita_cliente_confuso`, `devolucion_dentro_de_plazo`, `devolucion_fuera_de_plazo`, `seguridad_sin_prisa`, `pide_una_persona` y `cita_en_ingles`. Con el kit del día 1, los de cita que esperan reserva y `devolucion_dentro_de_plazo` **fallan a propósito**, porque esos pasos aún no existen.
- **Métricas del informe**: escenarios superados, paso a persona correcto, turnos medios y porcentaje de criterios del juez cumplidos.

### Tests

- `tests/test_herramientas.py` tiene 6 pruebas del servidor MCP llamando a las funciones directamente, sin OpenAI ni red, con `datos.ESTADO` redirigido a `tmp_path`.
- `pytest.ini` configura `asyncio_mode = auto` (los tests `async def` no necesitan decorador) y `pythonpath = .`.
- Los tests de flujos (`tests/test_<flujo>.py`) aún no existen: se escriben el día 2 con la skill `completar-flujo` y siguen el patrón de la sección **Tests**.

### Puntos delicados al cambiar código

- **Seguridad**: la decisión no depende solo del modelo, sino también de `PELIGRO` y del orden de `ruta()`. Ojo: «los frenos **fallan**» no está en `PELIGRO` y la regex de motivo lo tomaría como avería; en ese caso depende de que el modelo lo clasifique como seguridad.
- **Botones**: `eleccion()` compara el texto exacto del botón, y `redactar` puede traducir las opciones. En otro idioma, la coincidencia exacta falla y se depende de `ultima.eleccion` del modelo.
- **`informar`** busca con el texto literal del cliente, sin reformular.
- **Flujos**: devuelven solo los campos que cambian, y cada flujo es una función pura sobre `(estado, h)`. Por eso se pueden probar con `HerramientasFalsas` sin grafo ni modelo.
- **No confundir los dos agentes**: el prompt del agente de Ondo es `PERSONA_ONDO` (en `llm.py`); este `AGENTS.md` solo guía al asistente de código.
