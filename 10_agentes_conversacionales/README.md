# Tema 10 · Agentes conversacionales

Material del módulo **Agentes conversacionales: automatización de chats y llamadas telefónicas** del Máster de EBIS: un agente de atención al cliente para **Ondo**, una tienda online ficticia de bicicletas eléctricas, por chat (Telegram) y por teléfono.

| Carpeta / fichero | Qué hay |
|---|---|
| `clase_01/` | Sesión 1: diseño conversacional y agente de chat. PDF, explicación y tutorial del bot de Telegram |
| `clase_02/` | Sesión 2: construir con tests y evaluar. PDF con su `.md` y explicación |
| `ondo-agente/` | El kit de código, el mismo para todas las sesiones |
| `changelog.md` | Lo que hizo falta para poner el kit a funcionar y lo pendiente |
| `AGENTS.md` | Instrucciones para agentes (el detalle de todo lo anterior) |

---

## Comandos útiles de `ondo-agente`

Cada ejemplo empieza con las dos líneas que llevan a la carpeta del kit y activan su entorno virtual, para pegarlo tal cual en una terminal nueva:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
```

Si la terminal ya está en `ondo-agente` con `(.venv)` delante del prompt, basta con la última línea de cada ejemplo.

Con `RAG_EMBEDDINGS=ollama` en el `.env`, **Ollama tiene que estar arrancado** (el RAG usa `bge-m3`). Con `--qwen`, también.

### Hablar con el agente en la terminal

Solo la conversación:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.consola
```

Con el estado del grafo tras cada turno:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.consola --estado
```

Con el estado y además el camino por el grafo en cada turno:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.consola --traza
```

Lo mismo, con qwen3 en Ollama en vez de Claude:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.consola --traza --qwen
```

`--qwen` vale también en el bot y en la suite. Sin el flag se usa el modelo del `.env`. Al arrancar, cada comando dice qué modelo usa (`Modelo: ollama · qwen3:4b-instruct`).

Dentro de la consola:

| Escribes | Qué hace |
|---|---|
| `1`, `2`, `3`… | Pulsa ese botón |
| `/reset` | Empieza una conversación nueva |
| `/salir` | Termina |

Así se ve un turno con `--traza`:

```
Tú: Quiero saber donde está mi pedido
   1. interpretar  entiende: pedido; intencion=pedido; pendiente=None; intentos_fallidos=0; idioma=es; datos={}
   2. identificar  pendiente=email; borrador: «Para ayudarle necesitas identificarle: pídele su email de compra.»
   3. redactar     escribe la respuesta
Ondo: Para ayudarte necesito que me identifiques. Por favor, dime el email con el que hiciste la compra.
   [estado] {"intencion": "pedido", "cliente": null, "datos": {}, "pendiente": "email", "intentos_fallidos": 0, "escalado": null, "idioma": "es"}
```

Cada línea numerada es un nodo del grafo: **interpretar** (el modelo entiende el mensaje), el nodo que eligió `ruta()` (aquí, **identificar**) y **redactar** (el modelo escribe la respuesta). `[estado]` es lo que el agente recuerda para el turno siguiente.

### El bot de Telegram

Con Claude (debe decir «Bot @… listo»):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.telegram_bot
```

Con qwen3 en Ollama:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m canales.telegram_bot --qwen
```

Solo contesta mientras esa terminal está abierta. Si dos procesos lo arrancan a la vez, falla con `Conflict: terminated by other getUpdates request`. Paso a paso y problemas en `clase_01/tutorial-bot-telegram.md`.

### Tests

Todos (no gastan clave: no llaman al modelo):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m pytest
```

Solo los del flujo de cita, y comprobar que nadie ha tocado los tests (el `git diff` debe salir vacío):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m pytest tests/test_cita.py && git diff -- tests/
```

### Evaluación (día 2)

Los diez escenarios (un par de minutos y unos céntimos):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m evaluacion.suite
```

Solo algunos escenarios (ids separados por comas):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m evaluacion.suite --solo pedido_ajeno
```

Solo las comprobaciones con datos, sin el juez:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m evaluacion.suite --sin-juez
```

De uno en uno, si la clave da límite de peticiones:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m evaluacion.suite --paralelo 1
```

Cortando antes las conversaciones (por defecto, 10 turnos):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m evaluacion.suite --max-turnos 6
```

En local con qwen3, gratis y mejor de uno en uno:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m evaluacion.suite --sin-juez --qwen --paralelo 1
```

Con `--qwen`, **todo** pasa a qwen3: el agente, el cliente simulado y el juez. El informe lo anota en su cabecera; no compares sus números con los de Claude como si fueran la misma medida.

El informe y las conversaciones quedan en `evaluacion/salidas/`, con fecha y hora. La suite usa su propio estado: no toca `data/estado/`.

### Otros

Comprobar el entorno (Python, dependencias, `.env`, modelo, embeddings, servidor MCP y ngrok; debe terminar en «Todo listo»):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python scripts/comprobar_entorno.py
```

Demo del día 1, el agente ReAct genérico que falla:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
python -m agente.react_fallo
```

La API (`GET /salud`, `POST /chat`), para el día 3:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
uvicorn app.main:app --port 8000
```

### Datos de prueba

| Cliente | Para probar |
|---|---|
| `lucia.martin@example.com` | Pedido `OND-10231` en camino; vive en Madrid (cita en el taller) |
| `javier.ortega@example.com` | Pedido `OND-10233` entregado hace 12 días: devolución que se resuelve sola |
| `marta.ruiz@example.com` | Pedido `OND-10234` entregado hace 45 días: devolución fuera de plazo, a una persona |
| `pau.ferrer@example.com` | Pedido `OND-10235` de 2.959 €: más de 1.500 €, a una persona |

### Empezar de cero o deshacer

Borrar las citas, devoluciones y casos creados por el agente:

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
rm -rf data/estado/
```

Deshacer los cambios del chat de VS Code en un fichero del kit (cambia la ruta por la del fichero):

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
git restore agente/flujos/cita.py
```

El kit va versionado dentro del repo `ebis` (sin su propio `.git`), así que `git restore` se hace sobre las rutas del kit. El `.env` no se sube nunca.

### Modelo y claves (`.env`)

| Variable | Valor en local |
|---|---|
| `LLM_PROVEEDOR` | `anthropic` (Claude con la cuenta de Mario), `openai` (el del curso) u `ollama` (local; para un solo comando, mejor `--qwen`) |
| `ANTHROPIC_MODEL` | `claude-haiku-5-5` |
| `OLLAMA_MODEL` | `qwen3:4b-instruct` (solo con `LLM_PROVEEDOR=ollama`) |
| `RAG_EMBEDDINGS` | `ollama` (`bge-m3` en local; Anthropic no tiene embeddings) u `openai` |
| `TELEGRAM_BOT_TOKEN` | El que da @BotFather |

Por qué y cómo se cambió el kit para usar Claude y Ollama: `changelog.md`.
