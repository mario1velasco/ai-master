# Tema 01 – Agent Harness: de LLM a Agentes

Primer tema del módulo **06 · Integración con herramientas y MCP** del [Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica) de EBIS Business Techschool.

Antes de hablar de MCP (Model Context Protocol), este tema sienta las bases: qué es realmente un LLM, por qué solo no puede actuar en el mundo, y qué pieza de software ("harness" o arnés) hace falta construir alrededor para convertirlo en un agente capaz de usar herramientas (tools), recordar contexto y ejecutar tareas de forma fiable. MCP, que se verá en temas posteriores, es en el fondo un estándar para resolver una parte de este mismo problema (cómo conectar herramientas y contexto a un LLM), así que entender el harness "a mano" es el paso previo imprescindible.

## Contenido de la carpeta

```text
01-agents-harness/
├── Tema 6_LLM_Agents_tools.pdf        # Teoría: slides del tema
├── Enunciado - Ejercicio propuesto.pdf # Enunciado de la práctica guiada
├── Guia de uso de UV.pdf               # Chuleta de comandos de uv
├── Cli-harness-v1/                     # Demo del harness: versión mínima
│   └── ebis-cli-harness-v1/
├── Cli-harness-v8/                     # Demo del harness: versión completa
│   └── ebis-cli-harness-v8/
└── ebis-cli-proyect/                   # Ejercicio práctico (con TODOs por completar)
```

Los tres PDFs y los tres proyectos de código Python (basados en `uv` + SDK de OpenAI + interfaz Textual) forman una progresión: primero la teoría, luego dos "fotografías" de un mismo agente CLI en distintos estados de madurez (v1 mínimo vs. v8 completo) para ver el concepto en código real, y por último un ejercicio para completar tú mismo dos piezas clave.

## 1. Teoría — `Tema 6_LLM_Agents_tools.pdf`

Slides organizadas en tres bloques:

### ¿Qué puede hacer un LLM?
- Un LLM es, en esencia, un **predictor del siguiente token**: tokeniza el texto, lo vectoriza, atiende al contexto, combina información en varias capas, puntúa todos los tokens posibles del vocabulario, convierte esas puntuaciones en probabilidades y muestrea el siguiente token. Repite el proceso token a token.
- **"Probable" no significa "verdadero"**: si al modelo le falta información, puede generar una respuesta que suena razonable pero es una alucinación.
- La forma de reducir esa incertidumbre es darle mejor **contexto**: información relevante, instrucciones, restricciones y resultados de herramientas (PDF, web, bases de datos, APIs, memoria...). La idea no es reentrenar el modelo continuamente, sino mejorar el contexto desde el que responde.
- El propio modelo puede generar contexto intermedio razonando paso a paso (cadenas de pensamiento): descompone el problema, obtiene resultados intermedios y los usa como contexto para la respuesta final. Esto mejora mucho matemáticas, lógica, programación y planificación.

### Plataformas de IA: la era agéntica
Repaso histórico de cómo ha evolucionado la interacción con LLMs, en cuatro etapas:

| Etapa | Patrón | Limitación clave |
|---|---|---|
| **Chat tradicional** (2022-2023) | Reactivo: espera un input, procesa, devuelve output. Humano copia y pega todo el contexto necesario ("human-in-the-loop" total). | Conocimiento estático, alucinaciones, copy-paste manual, contexto que se degrada, sin memoria. |
| **Chat proactivo** (2024) | El sistema añade recuperación automática de contexto (búsqueda web, RAG) antes de responder. | Sigue sin poder escribir/actuar (read-only), sin razonamiento iterativo. |
| **Era de los agentes** (2025-) | Bucle de control **ReAct** (Reasoning + Acting): el modelo razona, decide una acción/tool, observa el resultado y repite hasta completar el objetivo, alterando el estado del mundo de forma autónoma. | Fragilidad del bucle, coste/latencia, saturación del contexto. |
| **Era multi-agente** (2026) | Un agente supervisor divide objetivos complejos y los delega en una red de agentes especialistas (orquestación y enrutamiento). | Complejidad de orquestación y *deadlocks*, pero gana seguridad (aislamiento) y *model routing*. |

El patrón **ReAct** es el núcleo técnico de todo lo que sigue: `Thought` (el modelo analiza y planifica) → `Action` (invoca una tool con argumentos) → `Observation` (el sistema ejecuta y devuelve el resultado al contexto) → se repite hasta cumplir el objetivo o alcanzar un límite.

### El arnés de un agente (Agent Harness)
Un LLM es solo un motor probabilístico: "no tiene brazos ni piernas". El **Agent Harness** (o andamiaje) es la capa de software **determinista** que envuelve, gobierna, alimenta y aísla al LLM para convertirlo en un sistema agéntico funcional y seguro. Sus responsabilidades:

- **Directrices de comportamiento**: ficheros tipo `AGENTS.md` (o `CLAUDE.md`) con instrucciones fijas que no hay que repetir en cada conversación.
- **Gestión del bucle**: cuándo parar un agente — objetivo alcanzado, número máximo de iteraciones (`MAX_STEPS`), presupuesto máximo (tokens/coste) o timeout. Más iteraciones no es igual a mejor respuesta.
- **Historial vs. contexto**: el *historial* es el registro completo de lo ocurrido (puede crecer sin límite); el *contexto* es lo que realmente se envía al modelo en cada llamada. Como la ventana de contexto es limitada, el harness debe traducir uno en otro mediante *context engineering*: (a) generar un resumen adaptado al objetivo actual, (b) seleccionar solo lo relevante, (c) compactar el historial cuando supera un umbral, o (d) guardar información clave en una memoria persistente (fichero clave-valor) y leerla cuando haga falta.
- **Verificación y frenos duros**: un patrón `ACT` (el bucle agéntico de siempre) + `REVIEW` (un verificador independiente compara el objetivo con la respuesta y las acciones realizadas y devuelve `PASS` o `FIX: ...`) permite generar → comprobar → dar feedback → corregir, en vez de fiarse de que el agente diga "he terminado".
- **Subagentes**: un orquestador puede delegar subtareas en subagentes con su propio objetivo y su propio contexto aislado, evitando que el contexto principal se sature con detalles de cada subtarea.
- **Seguridad y sandboxing**: tener una tool disponible no da permiso para usarla. Se puede definir un sistema de roles/permisos (similar a Linux) que limite qué tools puede invocar cada agente o subagente, reduciendo el riesgo de *prompt injection* (p. ej. "el agente que busca en internet no puede ejecutar comandos").
- **Monitorización y telemetría**: cuánto se ha gastado, cuántos pasos ha dado, qué ha hecho el agente.

### ¿Qué es una herramienta (tool)?
Como el LLM no ejecuta nada por sí mismo, hace falta un "idioma común" entre el harness y el modelo: el **function calling**. Cada tool se anuncia al modelo como un contrato JSON con tres partes:
- **Identificador único** (`name`): el nombre exacto de la función Python.
- **Descripción semántica** (`description`): el "manual de uso" que ayuda al modelo a decidir cuándo usarla.
- **Esquema JSON de parámetros** (`parameters`, `required`, `additionalProperties: false`, `strict: true`): define los argumentos, su tipo y una descripción de cada uno.

Cuando el modelo decide usar una tool, no responde con texto normal: devuelve `content: null` y una lista de `function_call` (o `tool_calls`, según el proveedor — OpenAI y Anthropic usan esquemas ligeramente distintos). El harness:
1. **Deserializa y despacha**: interpreta los argumentos JSON y ejecuta la función Python local (`dispatch_tool`).
2. **Inyecta el resultado**: añade un elemento `function_call_output` (con el `call_id` correspondiente) al historial/contexto para que, en la siguiente vuelta del bucle, el modelo pueda leer el resultado y decidir qué hacer.

Cómo "aprendió" el modelo a usar tools correctamente: mediante *Reinforcement Learning* orientado a *tool use*, en una progresión histórica (chat asistente en 2022 → *structured outputs*/JSON mode en 2024 → uso de tools y comportamiento agéntico en 2025).

## 2. Demos progresivas del harness — `Cli-harness-v1/` y `Cli-harness-v8/`

Ambas carpetas contienen el **mismo agente CLI** ("EBIS-CLI"), una mini aplicación de terminal (Textual) que recibe un objetivo en lenguaje natural y usa la Responses API de OpenAI con tools locales. La diferencia entre ellas es el estado de madurez del harness, siguiendo la misma progresión "DEMO v1 → v8" que se explica en las slides:

| Versión | Qué añade (según las slides) |
|---|---|
| **v1** | Bucle ReAct básico (`while True`): pide, ejecuta tools si el modelo las solicita, termina cuando ya no hay `function_call`. Sin límite de pasos. |
| v2 | Límite de iteraciones (`for step in range(1, MAX_STEPS + 1)`) para evitar bucles infinitos. |
| v3 | El historial de la sesión se guarda de verdad (`self.history.append(...)`) y se reenvía en `input` en cada llamada. |
| v4 | *Context engineering*: `compact_history()` resume el historial cuando supera un umbral; `build_context(goal)` prepara un contexto adaptado al objetivo actual. |
| v5 | Memoria persistente en disco: tools `save_memory` / `read_memory` sobre un fichero `.agent-memory.json`. |
| v6 | Patrón `ACT` + `REVIEW`: un verificador (`review()`) da el veredicto `PASS`/`FIX` y, si falla, se reintenta con feedback. |
| v7 | Subagentes: nueva tool `delegate_task` que lanza `run_subagent()`, un bucle ReAct independiente con su propio objetivo y contexto. |
| **v8** | Seguridad por roles: `LEAD_PERMISSIONS` / `WORKER_PERMISSIONS` + `tools_for(role)` filtran qué esquemas ve cada agente, y `execute()` vuelve a comprobar el permiso en tiempo de ejecución antes de despachar la tool. |

En el repositorio solo tenemos el código completo de **v1** (el punto de partida más simple) y **v8** (el harness final, que integra *todas* las capacidades anteriores: historial, compactación de contexto, memoria, verificación, subagentes y permisos). Comparar `agent.py` y `tools.py` de ambas carpetas es la forma más rápida de ver, en código real, todo lo que añade cada capa del harness descrita en la teoría.

Cada carpeta trae su propio `README.md` con el detalle exacto de "qué cambia en esta versión" y cómo ejecutarla (`uv sync`, copiar `.env.example` a `.env` con tu `OPENAI_API_KEY`, y `uv run python -m ebis_cli.app`).

Estructura común a ambos proyectos:
```text
ebis-cli-harness-vX/
├── ebis_cli/
│   ├── agent.py     # Loop del agente (ReAct), permisos, subagentes, verificación...
│   ├── app.py        # Interfaz de terminal (Textual) — caja negra en este tema
│   ├── context.py    # Carga .env y combina AGENTS.md del código + de la carpeta de trabajo
│   ├── tools.py       # Funciones locales, esquemas TOOLS y dispatch_tool
│   └── style.tcss
├── AGENTS.md          # Instrucciones por defecto del agente
├── .env.example
└── pyproject.toml
```

## 3. Ejercicio práctico — `ebis-cli-proyect/` (ver `Enunciado - Ejercicio propuesto.pdf`)

Es el mismo tipo de agente CLI, pero como **punto de partida con dos problemas deliberados** para resolver. Ya incluye la interfaz, la configuración y tres tools de archivos (`list_files`, `read_file`, `write_file`) funcionando, y dos bloques marcados con `TODO`:

- **`ebis_cli/tools.py` → TODO 1**: implementar dos tools nuevas y conectarlas al modelo:
  - `count_words(text: str)`: cuenta palabras con `text.split()`.
  - `calculate_total(unit_price: float, quantity: int)`: calcula `unit_price * quantity`.
  - Para cada una: función Python, entrada en `TOOLS` (esquema JSON con `type`, `name`, `description`, `parameters`, `required`, `additionalProperties: False`, `strict: True`) y registro en el diccionario `functions` dentro de `dispatch_tool`.

- **`ebis_cli/agent.py` → TODO 2**: reparar y limitar la memoria de conversación:
  1. `count_history_words(self, history)`: cuenta las palabras del campo `content` de cada elemento del historial (soporta tanto dicts como objetos de la SDK, e ignora los que no tienen texto, como los resultados de tools).
  2. `compact_history(self, goal)` (async): si el historial supera `MAX_HISTORY_WORDS` (300), pide al modelo un resumen breve adaptado al objetivo actual y sustituye `self.history` por ese resumen; si no lo supera, no hace nada.
  3. Corregir la llamada principal a `responses.create(...)` para que reciba `input=run_history` (con el historial + objetivo + resultados de tools) en lugar de `input=goal`, y llamar a `await self.compact_history(goal)` al principio de `run()`.

El objetivo pedagógico es entender de primera mano por qué `responses.create` **no** recuerda nada por sí solo entre llamadas — todo lo que el modelo "recuerda" tiene que reconstruirse explícitamente en `input` en cada petición — y por qué ese historial necesita un mecanismo de compactación para no crecer sin límite.

### Cómo ejecutarlo
```bash
cd ebis-cli-proyect
uv sync
cp .env.example .env        # añade tu OPENAI_API_KEY
uv run python -m ebis_cli.app
```
Dentro de la app, `/tools` debe listar las cinco herramientas una vez completado el TODO 1. Pruebas sugeridas en el enunciado:
- `Usa count_words para contar las palabras de esta frase: "EBIS aprende a crear agentes útiles".` → 6 palabras.
- `Usa calculate_total con precio unitario 12.50 y cantidad 3.` → 37.50.

## 4. Guía de uso de UV — `Guia de uso de UV.pdf`

Referencia rápida de la herramienta [`uv`](https://docs.astral.sh/uv/) (Astral), usada para gestionar entorno y dependencias en los tres proyectos Python de esta carpeta:
- `pyproject.toml` es la única fuente de verdad (sustituye a `requirements.txt`/`setup.py`).
- `uv sync` crea el entorno virtual e instala dependencias.
- `uv run <comando>` ejecuta algo dentro de ese entorno (p. ej. `uv run python -m ebis_cli.app`).
- `uv add <paquete>` / `uv add --dev <paquete>` añade dependencias (actualiza `pyproject.toml` y `uv.lock`).
- `uv run --project <ruta>` permite ejecutar el agente usando el entorno de un proyecto de código distinto de la carpeta de trabajo actual — relevante porque `ebis-cli-*` distingue entre "carpeta del código" (`CODE_DIR`) y "carpeta de trabajo" (`WORK_DIR`, desde donde las tools leen/escriben archivos).

## Orden de estudio recomendado

1. Leer `Tema 6_LLM_Agents_tools.pdf` para entender los conceptos (LLM, contexto, ReAct, harness, tools).
2. Recorrer `Cli-harness-v1/` para ver el bucle ReAct más simple posible en código.
3. Recorrer `Cli-harness-v8/` y comparar `agent.py`/`tools.py` con la v1, identificando dónde aparece cada capacidad (historial, compactación, memoria, verificación, subagentes, permisos).
4. Completar el ejercicio en `ebis-cli-proyect/` siguiendo `Enunciado - Ejercicio propuesto.pdf`.
5. Usar `Guia de uso de UV.pdf` como chuleta de comandos mientras trabajas con cualquiera de los tres proyectos.
