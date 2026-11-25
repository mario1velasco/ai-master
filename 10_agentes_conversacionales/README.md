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

### Antes de nada (en cada terminal nueva)

```bash
cd ~/ebis/10_agentes_conversacionales/ondo-agente
source .venv/bin/activate
```

Con `RAG_EMBEDDINGS=ollama` en el `.env`, **Ollama tiene que estar arrancado** (el RAG usa `bge-m3`).

### Hablar con el agente en la terminal

```bash
python -m canales.consola            # solo la conversación
python -m canales.consola --estado   # y el estado del grafo tras cada turno
python -m canales.consola --traza    # y además el camino por el grafo en cada turno
```

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

```bash
python -m canales.telegram_bot       # debe decir «Bot @… listo»
```

Solo contesta mientras esa terminal está abierta. Si dos procesos lo arrancan a la vez, falla con `Conflict: terminated by other getUpdates request`. Paso a paso y problemas en `clase_01/tutorial-bot-telegram.md`.

### Tests

```bash
python -m pytest                     # todos (no gastan clave: no llaman al modelo)
python -m pytest tests/test_cita.py  # solo los del flujo de cita
git diff -- tests/                   # tras un cambio del chat: debe salir vacío
```

### Evaluación (día 2)

```bash
python -m evaluacion.suite                           # los diez escenarios (un par de minutos, céntimos)
python -m evaluacion.suite --solo pedido_ajeno       # solo esos escenarios (ids separados por comas)
python -m evaluacion.suite --sin-juez                # solo las comprobaciones con datos, sin el juez
python -m evaluacion.suite --paralelo 1              # de uno en uno, si la clave da límite de peticiones
python -m evaluacion.suite --max-turnos 6            # corta antes las conversaciones (por defecto 10)
```

El informe y las conversaciones quedan en `evaluacion/salidas/`, con fecha y hora. La suite usa su propio estado: no toca `data/estado/`.

### Otros

```bash
python scripts/comprobar_entorno.py  # Python, dependencias, .env, modelo, embeddings, servidor MCP y ngrok: debe terminar en «Todo listo»
python -m agente.react_fallo         # demo del día 1: el agente ReAct genérico que falla
uvicorn app.main:app --port 8000     # la API (GET /salud, POST /chat), para el día 3
```

### Datos de prueba

| Cliente | Para probar |
|---|---|
| `lucia.martin@example.com` | Pedido `OND-10231` en camino; vive en Madrid (cita en el taller) |
| `javier.ortega@example.com` | Pedido `OND-10233` entregado hace 12 días: devolución que se resuelve sola |
| `marta.ruiz@example.com` | Pedido `OND-10234` entregado hace 45 días: devolución fuera de plazo, a una persona |
| `pau.ferrer@example.com` | Pedido `OND-10235` de 2.959 €: más de 1.500 €, a una persona |

### Empezar de cero o deshacer

```bash
rm -rf data/estado/                  # borra citas, devoluciones y casos creados por el agente
git restore <ruta>                   # deshace cambios del chat de VS Code en ficheros del kit
```

El kit va versionado dentro del repo `ebis` (sin su propio `.git`), así que `git restore` se hace sobre las rutas del kit. El `.env` no se sube nunca.

### Modelo y claves (`.env`)

| Variable | Valor en local |
|---|---|
| `LLM_PROVEEDOR` | `anthropic` (Claude con la cuenta de Mario) u `openai` (el del curso) |
| `ANTHROPIC_MODEL` | `claude-haiku-5-5` |
| `RAG_EMBEDDINGS` | `ollama` (`bge-m3` en local; Anthropic no tiene embeddings) u `openai` |
| `TELEGRAM_BOT_TOKEN` | El que da @BotFather |

Por qué y cómo se cambió el kit para usar Claude y Ollama: `changelog.md`.
