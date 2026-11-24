# AGENTS.md — Módulo "Agentes conversacionales: automatización de chats y llamadas telefónicas"

## De qué va este curso

Esta carpeta contiene los materiales y ejercicios del módulo **10 · Agentes conversacionales: automatización de chats y llamadas telefónicas** (Tema 10), parte del [Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica) de EBIS Business Techschool. Profesor: Álvaro Lamas.

Caso nuevo (ya no es Lumen Shop): **Ondo**, una tienda online ficticia de bicicletas eléctricas que vende en España, Francia, Italia y Portugal. Quiere un agente que atienda por **chat y por teléfono**, resuelva lo sencillo y pase a una persona lo demás. Datos del kit: 30 clientes, 40 pedidos, 7 talleres, 10 documentos de política y un servidor MCP con 7 herramientas. Atiende cuatro motivos de contacto: dónde está mi pedido, devoluciones, cita en el taller y seguridad (esta última, siempre a una persona).

Las tres sesiones del tema (según las diapositivas del día 1):

1. Día 1 · 23/11 — Diseño conversacional y agente de chat (Telegram).
2. Día 2 · 25/11 — Construir con tests y evaluar (escenarios y juez).
3. Día 3 · 30/11 — Voz en el navegador con Pipecat, llamada por Twilio, transferencia a una persona y buenas prácticas.

(La guía de preparación del entorno pone otro orden —día 2 voz y teléfono, día 3 evaluar—; manda el de las diapositivas.)

## Estructura de la carpeta

- `clase_01/`: sesión 1 — qué es un agente conversacional (frente a uno de tareas), seis conceptos (turno, estado, intención, slots, reparación, traspaso), reglas de diseño (tono, bienvenida, una pregunta por turno, confirmar según el riesgo, reparación en tres escalones, cuándo pasar a una persona, idioma y datos personales), el agente ReAct genérico que falla, el grafo de Ondo (interpretar → `ruta()` → nodo → redactar), el RAG como herramienta, el bot de Telegram (polling frente a webhook) y las piezas que guían al chat de VS Code (`AGENTS.md`, skill `completar-flujo`, subagente `revisor_conversacion`, MCP). Tiene:
  - `Diapositivas Tema 10 - Sesión 1.pdf`: la teoría.
  - `T10 - Preparación Entorno - Guia .pdf`: instalación previa (Python ≥ 3.11, git, VS Code con su chat y clave de OpenAI, ngrok).
  - `T10 - Guia de Ejercicio de Clase - Dia 1 - Agente_de_chat_en_Telegram.pdf`: la práctica del día.
  - Dos ejercicios complementarios con su corrección: «Sé el grafo» (8 casos para predecir el camino por el grafo) y «Diagnostica la conversación» (5 conversaciones mal diseñadas).
  - `explicacion-10.md`: explicación didáctica de la sesión.
  - `tutorial-bot-telegram.md`: paso a paso para crear el bot con @BotFather, conseguir el token, ponerlo en el `.env`, arrancar el bot y qué hacer si falla.

Las siguientes sesiones irán en `clase_02/`, `clase_03/`… cuando se den.

- `ondo-agente/`: el kit de código del tema, compartido por todas las sesiones (ver la sección siguiente).
- `changelog.md`: lo que ha hecho falta para poner el kit a funcionar, lo más reciente arriba, más lo que queda pendiente según la guía del día.

## El kit de código (`ondo-agente`)

El código está en **`ondo-agente/`**, clonado el 23-11-2026 del repositorio público `https://github.com/alamasfu10/ondo-agente.git` (último commit `43dafbd`, del 19-11-2026). Es **el mismo kit para las tres sesiones**: el día 1 se entiende y se usa por Telegram, el día 2 se completan los flujos con tests y se evalúa (`evaluacion/`), y el día 3 la API de `app/` recibe las llamadas con ngrok. Tiene su propio `README.md` y su propio `AGENTS.md`, que son las instrucciones **del chat de VS Code de la clase** sobre el kit; cuando se trabaje dentro de `ondo-agente/`, se leen y mandan allí. Piezas principales:

| Pieza | Dónde | Qué hace |
|---|---|---|
| Puerta de entrada | `agente/agente.py` | `AgenteOndo`: recibe el mensaje de cualquier canal, lo pasa al grafo con su hilo y devuelve texto, botones y estado |
| Estado | `agente/estado.py` | Lo que el agente sabe en cada turno: cliente, intención, datos, pendiente, opciones, intentos fallidos, escalado, idioma |
| Grafo | `agente/grafo.py` | Nodos y `ruta()`; la constante `PELIGRO` (palabras de seguridad) y `MAX_INTENTOS = 3` |
| Flujos | `agente/flujos/` | Pedido, devolución y cita paso a paso (en el día 1, la cita no llega a reservar y la devolución pasa siempre a persona) |
| Modelo | `agente/llm.py` | Tres llamadas: interpretar, redactar y resumir; el prompt `PERSONA_ONDO` |
| Herramientas | `agente/herramientas.py` | Una sesión stdio con el servidor MCP `ondo_mcp/` (7 herramientas) |
| Canales | `canales/telegram_bot.py`, `canales/consola.py` | Telegram (polling) y la consola con `--estado` / `--traza` |
| Servidor MCP y datos | `ondo_mcp/`, `data/` | 7 herramientas y el RAG; 30 clientes, 40 pedidos, 7 talleres y 10 documentos de política. No se tocan |
| Evaluación (día 2) | `evaluacion/` | Escenarios, cliente simulado, juez e informe (`python -m evaluacion.suite`) |
| API (día 3) | `app/main.py` | FastAPI (`GET /salud`, `POST /chat`); con ngrok recibe el audio de las llamadas |
| Tests | `tests/` | Pruebas del servidor MCP (sin clave de OpenAI); los del flujo de cita se escriben el día 2 |
| Para el chat | `AGENTS.md`, `.agents/skills/completar-flujo/SKILL.md`, `.github/agents/revisor_conversacion.agent.md` | Reglas del proyecto, skill de tests primero y subagente revisor de solo lectura |

El 24-11-2026, a petición de Mario, se **borró `ondo-agente/.git`** para ver y versionar el kit dentro de `ebis` (antes de borrarlo se comprobó que no tenía commits locales ni stash: todo su historial está en GitHub, commit `43dafbd`). El `.gitignore` del propio kit sigue valiendo dentro de `ebis` y deja fuera `.env`, `.venv/`, `data/estado/`, `data/.cache/` y `evaluacion/salidas/`; aun así, antes de cada commit comprueba con `git status` que no entra ninguno.

Consecuencia: **ya no hay `git pull`** de los cambios del profesor para los días 2 y 3. Para traerlos, clona el repo en una carpeta aparte (en el scratchpad, no en `ebis`), compara con `43dafbd` (`git diff 43dafbd..origin/main`) y aplica esos cambios a mano sobre `ondo-agente/`, respetando los cambios locales (Claude y bge-m3, ver `changelog.md`). Para deshacer lo que haga el chat de VS Code, se usa el git de `ebis` (`git restore` sobre rutas del kit).

Lo que crea el agente (citas, devoluciones, casos) se guarda en `data/estado/`; borrarla empieza de cero. El índice del RAG se guarda en `data/.cache/`.

## Cómo ejecutar el código

Entorno del kit: Python ≥ 3.11 (recomendado 3.12), `.venv` propio con `requirements.txt` y `.env` copiado de `.env.example` con `OPENAI_API_KEY` y `TELEGRAM_BOT_TOKEN`. El modelo del curso es de OpenAI (la corrección de los complementarios usa `gpt-4.1-mini`). Para el día 3 hace falta ngrok (Twilio solo funciona por webhook).

**Cambio local de Mario (no viene del kit):** la clave de OpenAI de EBIS da 401, así que el kit puede usar **Claude** con su cuenta de Anthropic (`LLM_PROVEEDOR=anthropic`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL=claude-haiku-5-5`, el más barato) y, como Anthropic no tiene embeddings, el RAG puede usar **bge-m3 en Ollama** (`RAG_EMBEDDINGS=ollama`; `ollama pull bge-m3` y Ollama arrancado). Es el mismo modelo de embeddings que travel-agency, que allí va con `sentence-transformers`. Por defecto todo sigue en OpenAI. Toca `agente/llm.py` (`modelo()`), `ondo_mcp/conocimiento.py` (`_embeddings()`), `scripts/comprobar_entorno.py`, `requirements.txt` y `.env.example`: al traer los cambios del profesor para los días 2 y 3, esos ficheros hay que mezclarlos a mano. Detalle en `changelog.md`.

```bash
cd ondo-agente
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env                      # pegar OPENAI_API_KEY y TELEGRAM_BOT_TOKEN
python scripts/comprobar_entorno.py       # debe terminar en «Todo listo»
python -m canales.telegram_bot            # el bot de Telegram
python -m canales.consola --traza         # la consola, con el camino por el grafo
python -m agente.react_fallo              # el agente ReAct genérico que falla (demo)
python -m pytest                          # pruebas (sin clave de OpenAI)
python -m evaluacion.suite                # evaluación con conversaciones simuladas (día 2)
uvicorn app.main:app --port 8000          # la API (día 3)
```

En la consola, `/reset` empieza una conversación nueva y `/salir` termina.

## Reglas al trabajar en el código

- Hay **dos agentes distintos** en el kit: el de Ondo (sus instrucciones son `PERSONA_ONDO` y los prompts de `agente/llm.py`) y el chat que programa (sus instrucciones son el `AGENTS.md` del kit, la skill y el subagente). Cambiar uno no cambia el otro.
- Las reglas de la conversación de Ondo no se tocan "para que funcione": la seguridad (batería, frenos, humo) pasa **siempre** a una persona con prioridad urgente; una acción con efecto (reservar, devolver) solo se ejecuta con un sí claro; devoluciones de más de 1.500 € o fuera de plazo no las resuelve el agente; tres intentos sin entender → persona; no inventar datos.
- Algunos huecos del kit del día 1 son **a propósito**: el flujo de cita no reserva (se construye el día 2, tests primero), la devolución pasa siempre a una persona y el contador de intentos no sube cuando el flujo repara (lo encuentra el revisor el día 2). No los "arregles" salvo que el usuario lo pida.
- Si el usuario pide ayuda con un ejercicio, guíale; no lo resuelvas entero salvo que lo pida explícitamente.
- No subas `.env` ni muestres la clave de OpenAI ni el token de Telegram.

## Documentación de cada sesión

- **`explicacion-10.md`**: explicación didáctica de la sesión (PDFs de la carpeta + código del kit cuando esté), en lenguaje sencillo, centrada en la idea principal y sin dar nada por sabido. Pensada para que la lea un humano (Mario). Todo lo que afirma debe venir de los PDF o del código real; los ejemplos propios se marcan como *ilustrativos* y los resultados de ejecutar las demos se marcan «en mi máquina» con el modelo y la fecha.
- No adelantes en un `explicacion-10.md` contenido de sesiones que aún no se han dado en clase.

## Mantenimiento de la documentación

Cada vez que modifiques algo en esta carpeta (código, materiales, estructura), comprueba si este `AGENTS.md` o algún `explicacion-10.md` se ha quedado desactualizado y actualízalo en el mismo cambio.

- Si el cambio es puntual (un dato, un ejercicio resuelto, un fichero nuevo), edita solo esas líneas.
- Si llega una sesión nueva o el kit se descarga en la carpeta, sí merece la pena replantear la sección afectada.
- Si no hay nada que actualizar, no toques los docs "porque sí".
