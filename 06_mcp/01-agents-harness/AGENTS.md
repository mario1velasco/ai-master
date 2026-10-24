# AGENTS.md — 01-agents-harness

Instrucciones de orientación para cualquier agente (Claude Code u otro) que trabaje en esta carpeta. El contexto completo y la teoría están en [`README.md`](README.md); este archivo es la guía operativa rápida.

## Qué es esta carpeta

Tema 01 del módulo 06 (Integración con herramientas y MCP) del máster de EBIS. Trata sobre **Agent Harness**: la capa de software determinista que envuelve un LLM para convertirlo en un agente que usa tools, mantiene contexto y se comporta de forma fiable. No es MCP todavía — es la base conceptual y de código sobre la que luego se construye MCP.

Todo el código es Python gestionado con `uv` (no pip/venv manual). Antes de ejecutar cualquier proyecto: `uv sync`, copiar `.env.example` → `.env` y rellenar `OPENAI_API_KEY`.

## Los tres proyectos de código — no los confundas

| Carpeta | Qué es | Estado |
|---|---|---|
| `Cli-harness-v1/ebis-cli-harness-v1/` | Harness mínimo: bucle ReAct básico (`while True`), sin límite de pasos, sin historial persistente. | Código de referencia completo, funcional tal cual. |
| `Cli-harness-v8/ebis-cli-harness-v8/` | Harness completo: historial + compactación de contexto + memoria en disco + verificación (ACT/REVIEW) + subagentes + permisos por rol. | Código de referencia completo, funcional tal cual. |
| `ebis-cli-proyect/` | El ejercicio del alumno (Mario). Parte de una base tipo v1-v3 con **dos bugs deliberados** y **2 TODOs** sin resolver. | Incompleto a propósito — ver más abajo. |

Si el usuario pide "explica cómo funciona X" sobre el harness en general, compara v1 vs v8 (mismos ficheros `agent.py`/`tools.py`, distinto nivel de madurez) en vez de mirar solo uno.

Si el usuario pide ayuda para **resolver el ejercicio**, el trabajo va en `ebis-cli-proyect/`, nunca en las carpetas v1/v8 (esas son material de referencia, no se tocan).

## Dónde están los TODOs de `ebis-cli-proyect/`

Enunciado completo en `Enunciado - Ejercicio propuesto.pdf` (raíz de `01-agents-harness/`). Resumen:

1. **`ebis_cli/tools.py`** (antes de la lista `TOOLS`, marcado `TODO 1`): crear las funciones `count_words(text: str)` y `calculate_total(unit_price: float, quantity: int)`, añadir su esquema JSON a `TOOLS` (mismo formato que `list_files`/`read_file`/`write_file`: `type`, `name`, `description`, `parameters`, `required`, `additionalProperties: False`, `strict: True`) y registrarlas en el diccionario `functions` dentro de `dispatch_tool`.
2. **`ebis_cli/agent.py`** (marcado `TODO 2`, dentro de la clase `Agent`, antes de `run`):
   - `count_history_words(self, history)`: suma `len(text.split())` del campo `content` de cada elemento (dicts de usuario y objetos de la SDK; ignora elementos sin texto en `content`, como los resultados de tools que usan `output`).
   - `compact_history(self, goal)` (async): si `count_history_words(self.history) <= MAX_HISTORY_WORDS` no hace nada; si lo supera, pide un resumen al modelo (sin `tools=TOOLS`, solo texto) y sustituye `self.history` por un único mensaje de asistente con ese resumen.
   - En `run()`: llamar a `await self.compact_history(goal)` al principio, y corregir la llamada a `self.client.responses.create(...)` para que use `input=run_history` (no `input=goal`).

No modificar `app.py`, `context.py`, `style.tcss` ni el bucle/ejecución de tools ya existente (`run_history.extend(response.output)`, el bloque que añade `function_call_output`) — son intocables según el enunciado.

## Cómo ejecutar cualquiera de los tres

```bash
cd <carpeta-del-proyecto>          # p.ej. ebis-cli-proyect, o Cli-harness-v1/ebis-cli-harness-v1
uv sync
cp .env.example .env               # añadir OPENAI_API_KEY; OPENAI_MODEL ya trae un valor por defecto
uv run python -m ebis_cli.app
```

Dentro de la app: `/tools` lista las tools anunciadas al modelo, `/help` la ayuda, `/clear` limpia la vista, `/exit` cierra.

## Mantenimiento de la documentación

Cada vez que modifiques código en esta carpeta (en cualquiera de los tres proyectos), comprueba si `README.md` y/o este `AGENTS.md` se han quedado desactualizados (rutas, TODOs resueltos, tools nuevas, cambios de comportamiento del harness, etc.) y actualízalos en el mismo cambio.

- Antes de escribir, analiza el alcance real: si es una actualización puntual (un TODO resuelto, una tool añadida, un dato concreto que cambió), edita solo esas líneas — no reescribas secciones enteras ni generes ruido innecesario en el diff.
- Si el cambio es lo bastante grande como para que mantener la estructura actual del documento genere más ruido que claridad (p. ej. se añade un TODO 3, se reorganiza el ejercicio, cambia la relación entre v1/v8), entonces sí merece la pena replantear esa sección antes de tocarla, en lugar de ir parcheando encima.
- Si no hay nada que actualizar, no toques los docs "porque sí".

## Convención AGENTS.md dentro de cada proyecto

Cada uno de los tres subproyectos (`Cli-harness-v1`, `Cli-harness-v8`, `ebis-cli-proyect`) trae **su propio** `AGENTS.md` en la raíz — no es este archivo, es la instrucción que el propio agente EBIS-CLI carga en tiempo de ejecución (vía `context.py::load_instructions`) para saber cómo comportarse dentro de esa carpeta de trabajo. No los confundas con este archivo, que es para ti (el agente que asiste a Mario en el repo), no para el agente EBIS-CLI simulado dentro de cada demo.
