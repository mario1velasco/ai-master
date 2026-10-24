# Explicación completa — Tema 01: De LLM a Agentes, Harness y Tools

Este documento explica **todo** el contenido de esta carpeta (los tres PDFs y el código de los tres proyectos) con un lenguaje sencillo, paso a paso, y sin dar nada por sabido. Todo lo que aquí se afirma viene directamente de `Tema 6_LLM_Agents_tools.pdf`, `Enunciado - Ejercicio propuesto.pdf`, `Guia de uso de UV.pdf`, o del código real de `Cli-harness-v1/`, `Cli-harness-v8/` y `ebis-cli-proyect/`. Cuando se usa un ejemplo propio para aclarar un concepto, se dice explícitamente que es un ejemplo ilustrativo.

Si solo quieres un resumen rápido, lee el [`README.md`](README.md) de esta carpeta. Este documento es la versión larga, pensada para entender el "por qué" de cada pieza.

---

## 1. Lo más básico: ¿qué es un LLM y cómo "piensa"?

Un LLM (*Large Language Model*, como GPT) **no es una base de datos con respuestas guardadas**. Es, según lo describe literalmente la teoría del curso:

> "Un gigantesco predictor del siguiente token: una arquitectura diseñada para analizar el texto y calcular qué debería venir después."

Es decir: su única tarea es, dado un trozo de texto, calcular qué palabra (o fragmento de palabra) es más probable que venga a continuación. Nada más. Todo lo demás — que parezca que "razona", que "sabe" cosas, que "conversa" — es un efecto que emerge de repetir esa tarea simple millones de veces a una escala enorme.

El proceso interno, explicado en 7 pasos por el material del curso, es este:

1. **El texto se divide en tokens.** Un token es un trozo de palabra (a veces una palabra entera, a veces solo un fragmento). Ejemplo del material: la frase «El gato duerme en el» se convierte en la secuencia de tokens `El`, `gato`, `duerme`, `en`, `el`.
2. **Cada token se vectoriza.** Cada token se transforma en un vector numérico (una lista de números) que el modelo puede procesar matemáticamente. Un ordenador no entiende "gato", pero sí entiende una lista de números.
3. **Busca pistas en el contexto.** Para predecir lo que viene después, el modelo compara cada token con los tokens anteriores (esto es, a grandes rasgos, lo que en la arquitectura *Transformer* se llama mecanismo de atención).
4. **Combina la información.** Muchas capas repiten ese análisis una y otra vez, construyendo una representación cada vez más rica del contexto completo.
5. **Puntúa todos los posibles tokens.** En una sola pasada, el modelo asigna una puntuación a *cada* token de su vocabulario (que puede tener decenas de miles de tokens posibles).
6. **Convierte las puntuaciones en probabilidades.** Por ejemplo, tras «El gato duerme en el», el modelo podría calcular: `sofá` 41%, `suelo` 24%, `jardín` 14%, `cama` 9%, `día` 7%, `.` 5%.
7. **Selecciona el siguiente token.** Con una técnica de muestreo (*sampling*) se hace un sorteo ponderado: cuanto mayor la probabilidad, más opciones tiene ese token de salir elegido. En el ejemplo, es probable (pero no seguro) que salga `sofá`.

Un punto clave que subraya el material: **los LLM no escriben la respuesta completa y luego la muestran**. La van construyendo **token a token**: generan un token, ese token pasa a formar parte del contexto, se recalculan las probabilidades del siguiente token con ese contexto ampliado, y así sucesivamente («nuevo token → nuevo contexto → volver a calcular»).

### Ejemplo ilustrativo (no del material, solo para fijar la idea)
Imagina que le pides al modelo que continúe "La capital de Francia es". El modelo no "busca" la respuesta en una tabla; calcula, token a token, que tras esas palabras la continuación más probable estadísticamente (dado todo lo que ha visto en su entrenamiento) es "París". Si en el mismo contexto hubiera aparecido antes información falsa o ambigua, el resultado podría cambiar — porque el modelo no consulta una fuente de verdad, solo continúa el patrón.

---

## 2. El problema de fondo: "probable" no es lo mismo que "verdadero"

Esta es una de las ideas más importantes del tema:

> "Un LLM no busca la verdad: busca una continuación basada en probabilidades. Probable no significa necesariamente verdadero."

El material lo ilustra con un ejemplo muy claro: si le preguntas a un modelo *sin acceso a tu calendario* "¿A qué hora tengo mañana la reunión con Marta?", el modelo no tiene forma de saberlo. Pero como su trabajo es generar la continuación más probable del texto, puede generar algo como "La reunión con Marta es mañana a las 10:00" porque estadísticamente esa es una respuesta plausible a ese tipo de pregunta — aunque sea inventada. A esto se le llama **alucinación**: una respuesta que "encaja perfectamente con el lenguaje" y "parece razonable", pero es incorrecta o inventada porque el modelo no disponía de suficiente información real.

Esto no es un fallo puntual del modelo, es una consecuencia directa de cómo funciona: genera la continuación *más probable dado lo que tiene delante*, no la continuación *más verdadera*.

---

## 3. La solución: el contexto

Si el problema es la falta de información, la solución es dársela. El material lo resume así:

> "Un LLM contiene una enorme cantidad de conocimiento y patrones aprendidos. Pero para aprovecharlos correctamente necesitamos reducir la incertidumbre sobre lo que queremos que haga. La herramienta fundamental para hacerlo es → CONTEXTO."

Cuanto mejor sea el contexto que le damos al modelo, mejor se orientan sus probabilidades hacia una respuesta útil. El contexto puede incluir:
- Información relevante (datos, documentos).
- Instrucciones (qué queremos que haga y cómo).
- Restricciones (qué no debe hacer).
- Resultados de herramientas (lo que ha ido descubriendo al usar tools).

Las fuentes habituales de contexto que menciona el material son: **RAGs** (sistemas de recuperación de documentos), **documentos y archivos**, **búsqueda web**, **consultas a bases de datos**, **APIs** (Google Calendar, Slack...) y el **historial** de la conversación. La idea de fondo es importante: **no se trata de reentrenar el modelo constantemente**, sino de mejorar, en cada petición, el contexto desde el que responde.

### El modelo también puede generar su propio contexto: razonamiento

En lugar de intentar predecir directamente `Pregunta → Respuesta`, el modelo puede intercalar pasos intermedios ("cadenas de pensamiento"):

```text
Pregunta
   ↓
Descomponer el problema
   ↓
Obtener resultados intermedios
   ↓
Usar esos resultados como nuevo contexto
   ↓
Respuesta
```

¿Por qué ayuda esto? Porque **convierte una predicción difícil en varias predicciones más sencillas**. El material usa este ejemplo: resolver de un tirón "80€ → descuento 25% → IVA 21% → ¿precio final?" exige acertar varias relaciones matemáticas a la vez. Razonando paso a paso (calcular primero el descuento, luego aplicar el IVA sobre el resultado, y solo entonces dar el precio final), cada paso es una predicción mucho más sencilla, y el resultado final es mucho más fiable. Esto mejora notablemente tareas de matemáticas, lógica, programación y planificación.

---

## 4. Por qué un LLM solo no basta: necesita "manos y pies"

Un LLM, por sí solo, **solo puede generar texto**. Puede redactar, resumir o proponer un plan, pero no puede consultar un sistema en tiempo real ni ejecutar una acción. El material lo muestra con dos ejemplos muy concretos:

| Petición | Qué falta fuera del modelo |
|---|---|
| «¿Qué facturas siguen pendientes?» | Consultar el estado actual en el sistema de facturación. |
| «Guarda el resumen en un archivo» | Ejecutar código con acceso y permisos de escritura. |

Para que el modelo pueda hacer esas cosas, necesita **capacidades externas**: algo que consulte datos o ejecute acciones en su nombre. Eso es justo lo que resuelven el **harness** (sección 6) que coordina el trabajo y las **tools** (sección 7) que ejecuta.

---

## 5. La evolución histórica: de chatbot a agente

El material describe cuatro etapas, cada una resolviendo las limitaciones de la anterior pero introduciendo otras nuevas.

### 5.1 El Chat Tradicional (2022-2023) — patrón reactivo

El sistema es únicamente un motor de transformación de texto: **espera un input, lo procesa y libera un output**. Es un flujo de trabajo *human-in-the-loop* total: la persona hace todo el trabajo de conectar el modelo con el mundo real.

```python
def chat(messages, chat_history):
    # Invocación única por turno
    response = llm.invoke(messages, chat_history)
    return response
```

Ejemplo de flujo con objetivo «Revisar las facturas vencidas y guarda un resumen»:

| Quién | Qué hace |
|---|---|
| Persona | Exporta las facturas y las pega en la conversación. |
| LLM | Analiza los datos recibidos y redacta el resumen. |
| Persona | Verifica el contenido y lo guarda en un archivo. |

El modelo ayuda con el análisis, pero **la persona conecta cada paso con el sistema real** (exportar, pegar, guardar).

Limitaciones de esta etapa: conocimiento estático (*knowledge cutoff* — el modelo no sabe nada posterior a su entrenamiento), alucinaciones por falta de *grounding* (no tiene datos reales para apoyarse), *copy-paste-in-the-loop* (la persona hace de "pegamento" manual), saturación y degradación del contexto, y ser *stateless* (sin memoria entre turnos salvo lo que quepa en la conversación).

### 5.2 El Chat Proactivo (2024) — contexto automático

El sistema añade un **proceso previo de contextualización automática** (buscar en internet, leer documentos, consultar una base de datos) antes de generar la respuesta:

```python
def chat(user_input, chat_history):
    # 1. El LLM actúa como generador de intenciones/queries
    search_queries = llm.generate_queries(user_input)

    # 2. Recuperación síncrona de datos externos (Grounding)
    retrieved_docs = vector_db.search(search_queries)

    # 3. Inyección en la ventana de contexto y respuesta final
    enriched_prompt = setup_context(user_input, retrieved_docs)
    response = llm.invoke(enriched_prompt, chat_history)

    return response
```

Con el mismo objetivo de las facturas, si el chat tiene acceso a una base de datos o RAG:

| Paso previsto | Resultado |
|---|---|
| 1. Recuperar datos | Consulta las facturas mediante una integración. |
| 2. Aportar contexto | Incluye los registros recuperados en la petición. |
| 3. Generar respuesta | El LLM redacta el resumen con esos registros. |

Esto resuelve el conocimiento estático y reduce alucinaciones (porque ahora hay datos reales de apoyo), pero siguen sin resolverse: *copy-paste-in-the-loop*, saturación del contexto, ser *stateless*, la **ausencia de razonamiento iterativo** (todo se hace en una sola pasada) y la **limitación de solo lectura** (*read-only*: el sistema puede consultar, pero no actuar ni escribir). Y si a mitad de camino faltan datos, no hay ningún mecanismo para decidir qué consultar después — todo el proceso de búsqueda ocurre de una vez, antes de responder.

### 5.3 La era de los Agentes (2025-) — patrón agéntico (bucle ReAct)

Aquí es donde el sistema deja de ser reactivo y pasa a tener **un bucle de control** con capacidad de razonar, evaluar errores y **alterar el estado del mundo de forma autónoma** (no solo leer, también actuar):

```python
def agent_chat(user_goal, chat_history, tools):
    global task_completed
    global current_context

    current_context = {"chat_history": chat_history}

    while not task_completed:
        thought = llm.think(user_goal, current_context)
        action = llm.decide_tool(thought, tools)
        observation = execute(action)
        current_context.update(observation)

        if check_success(observation, user_goal):
            break

    return llm.generate_final_response(current_context)
```

Este patrón se llama **ReAct** (*Reasoning* + *Acting*): fusiona la capacidad de generar cadenas de pensamiento con la capacidad de interactuar con entornos externos. El agente itera por tres fases:

1. **Thought** (pensamiento): el modelo analiza el objetivo, evalúa lo que sabe hasta el momento y planifica el siguiente paso.
2. **Action** (acción): el modelo decide invocar una herramienta específica con los parámetros necesarios. Ejemplo del material: `execute_bash(command="cat /etc/os-release")`.
3. **Observation** (observación): el sistema ejecuta esa acción, captura la salida real y la inyecta de nuevo en el contexto. Ejemplo: `"Ubuntu 22.04 LTS"`.

Con esto se resuelven ya las limitaciones anteriores (conocimiento estático, alucinaciones, *copy-paste*, *stateless*, falta de razonamiento iterativo, *read-only*), pero aparecen limitaciones nuevas y propias de esta etapa: **saturación y degradación del contexto** (el bucle puede acumular mucha información), **coste y latencia** (cada vuelta del bucle es una llamada al modelo — lo que el material llama *"inference tax"*, el "impuesto" en tiempo y dinero de cada inferencia) y la **fragilidad del bucle** (nada garantiza que el agente no se quede atascado). Herramientas reales de este tipo mencionadas en el material: OpenAI Codex CLI y Claude Code.

### 5.4 La era Multi-Agente (2026) — orquestación

La siguiente evolución es un **ecosistema colaborativo**: un agente supervisor divide objetivos complejos y los delega en una red de agentes especialistas.

```python
def orquestador_multi_agente(user_goal):
    # 1. Supervisor planifica
    plan = llm_frontier.create_plan(user_goal)

    for task in plan:
        # 2. Enrutamiento y aislamiento de seguridad
        if task.type == "db_query":
            result = sql_agent.run(task, model="gpt-4o-mini", tools=[read_only_db])
        elif task.type == "coding":
            result = dev_agent.run(task, model="gpt-5.5", tools=[bash, github])

        # 3. El supervisor guarda solo el resultado limpio
        supervisor.memory.append(result.summary)

    return supervisor.generate_final_response()
```

Esto resuelve la saturación de contexto (cada subagente tiene el suyo propio, más pequeño y específico) y el coste/latencia se reparte (se puede usar un modelo barato para tareas simples y uno potente solo cuando hace falta — *model routing*). Ventajas: **mayor seguridad** (cada agente solo tiene las herramientas que necesita) y **model routing**. Limitación propia de esta etapa: la **complejidad de orquestar** varios agentes y el riesgo de *deadlocks* (bloqueos por dependencias cruzadas entre agentes).

---

## 6. El Agent Harness: la ingeniería alrededor del LLM

Esta es la sección central de todo el tema.

### 6.1 ¿Qué es?

> "Un LLM es únicamente un motor probabilístico" — no tiene ni brazos ni piernas.

El **Agent Harness** (también llamado *arnés* o *andamiaje*) es:

> "La capa de software **determinista** que envuelve, gobierna, alimenta y aísla a un modelo de lenguaje (LLM) para transformarlo en un sistema agéntico funcional y seguro."

La palabra clave es **determinista**: el LLM es probabilístico e impredecible por naturaleza, pero el código que lo rodea (el harness) sí es código normal, predecible, que se puede testear y controlar. El harness es "el control determinista necesario para blindar el resultado frente a la incertidumbre del modelo."

Sus responsabilidades, según el material:
- **Directrices de comportamiento**: ficheros como `AGENTS.md` o *prompts* pre-escritos que fijan cómo debe comportarse el agente.
- **Gestión inteligente de la ventana de contexto**: decidir qué información necesita realmente la tarea actual.
- **Verificación y frenos duros**: tests automáticos y límites deterministas (no dejar que el modelo decida solo cuándo algo está "bien").
- **Seguridad y sandboxing**: roles definidos y entornos aislados.
- **Monitorización y telemetría**: saber cuánto se ha gastado (en tiempo, dinero, tokens).

El diagrama del material lo resume así: la petición del usuario entra al harness; dentro, el LLM se comunica en ambas direcciones con una "memoria" (los datos/contexto) y con las "herramientas" (acciones que puede ejecutar), y ambas piezas están coordinadas por una especie de checklist/plan de trabajo. El harness produce, como salida, trabajo real hacia el objetivo. La frase que lo resume: **"El LLM propone el siguiente paso. El harness organiza el trabajo."**

### 6.2 El bucle del agente, explicado paso a paso

Este es el código de la primera versión (**v1**) del harness real que hay en esta carpeta (`Cli-harness-v1/ebis-cli-harness-v1/ebis_cli/agent.py`), que es literalmente el ejemplo "DEMO v1" del material:

```python
async def run(self, goal, emit):
    emit("Agente", "Empiezo el trabajo.")
    input_items = [{"role": "user", "content": goal}]

    while True:
        response = await self.client.responses.create(
            model=self.model, instructions=self.instructions, input=input_items, tools=TOOLS
        )
        input_items.extend(response.output)
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            emit("Agente", response.output_text or "Tarea terminada.")
            return

        for call in calls:
            arguments = json.loads(call.arguments)
            result = dispatch_tool(call.name, arguments)
            emit("Tool", f"{call.name} -> {result}")
            input_items.append({"type": "function_call_output", "call_id": call.call_id, "output": result})
```

Leído en voz alta, este código dice: "Prepara el objetivo. Mientras sea necesario: pregúntale al modelo qué hacer, dándole el objetivo, las instrucciones y las tools disponibles. Si no pide ninguna tool, hemos terminado. Si pide una o varias, ejecútalas localmente, y añade su resultado a la conversación para que el modelo lo vea en la siguiente vuelta." Esto **es** el bucle ReAct (sección 5.3) llevado a código Python real, usando la *Responses API* de OpenAI.

El diagrama del material lo simplifica así: `LLM → Acción → Entorno → Observación → LLM` (y vuelta a empezar).

### 6.3 El problema de un bucle sin control

Con `while True` (como en v1), nada impide que el agente se quede atrapado. El material da este ejemplo de lo que podría pasar:

```text
while True:
    1. Leer archivo A
    2. Leer archivo B
    3. Leer archivo A
    4. Leer archivo B
    5. Leer archivo A
    6. ...
```

> "Ahora mismo, nuestro arnés NO es determinista, no sabemos si se va a bloquear en un bucle… o no."

### 6.4 ¿Cuándo debe parar un agente?

Un agente puede repetir el ciclo tantas veces como necesite, pero **cada iteración consume tokens, herramientas, tiempo y dinero**. El material propone cuatro criterios de parada:

1. **Objetivo alcanzado**: el agente ya tiene una respuesta válida y completa.
2. **Número máximo de iteraciones**: limita el número de ciclos (ejemplo del material: `max_iterations = 10`).
3. **Presupuesto máximo**: un límite de tokens, de llamadas a herramientas o de coste económico.
4. **Tiempo máximo**: detener la ejecución tras un *timeout*.

> "Un buen agente no solo debe saber qué hacer. También debe saber cuándo parar. Más iteraciones ≠ mejor respuesta."

El diagrama de flujo del proceso es: `Thought → Action → Observation → ¿Continuar?` → si Sí, vuelve a `Thought`; si No, genera la `Respuesta final`.

En el código, esto se traduce en pasar de un `while True` a un bucle acotado:

```python
# Antes (v1): sin límite
while True:
    ...

# Después (v2 en adelante): con límite de pasos
for step in range(1, MAX_STEPS + 1):
    emit("Sistema", f"Paso {step}/{MAX_STEPS}")
    ...
```

Este es exactamente el patrón que usan tanto `Cli-harness-v8/` como `ebis-cli-proyect/` en esta carpeta, con `MAX_STEPS = 6`. El material lo resume bien: *"La dificultad es encontrar el punto dulce que minimice el número máximo de iteraciones y maximice el número de tareas exitosas."*

### 6.5 Cada llamada necesita contexto — y el contexto no se crea solo

Este es uno de los puntos más importantes y más fáciles de pasar por alto. La llamada principal a la API es:

```python
response = await self.client.responses.create(
    model=self.model,
    instructions=self.instructions,
    input=input_items,
    tools=TOOLS,
)
```

El material insiste en algo crucial: **`responses.create` no recuerda nada de una llamada a la siguiente por sí sola**. Cada vez que se llama, es como si fuera la primera vez, *salvo por lo que se incluya explícitamente en `input`*. Esto lo demuestra con un ejemplo real de fallo:

```text
OBJETIVO · TÚ:  Cuando te diga "EBIS" responde "anotado" y nada más
RESPUESTA FINAL: Anotado.

OBJETIVO · TÚ:  EBIS
RESPUESTA FINAL: ¡Hola! ¿En qué puedo ayudarte hoy con EBIS?
```

El modelo "olvida" la instrucción anterior porque, en esa versión con el fallo, cada llamada a `run()` reiniciaba `input_items = [{"role": "user", "content": goal}]` desde cero, sin incluir nada de lo dicho antes. La conclusión del material, subrayada literalmente:

> "La continuidad depende de la información que el agente envíe al LLM. **EL CONTEXTO NO SE CREA SOLO.**"

### 6.6 El historial como memoria

La solución es que el harness (el código, no el modelo) sea quien **construya y guarde el historial**, y lo incluya en cada petición. Comparando dos versiones del mismo agente:

```python
# Antes: el historial no se guarda entre llamadas a run()
class Agent:
    def __init__(self):
        load_environment()
        ...
        self.history = []

    async def run(self, goal, emit):
        emit("Agente", f"Empiezo el trab...")
        input_items = [{"role": "user", "content": goal}]  # <- siempre desde cero
        ...
```

```python
# Después: el historial persiste y se reenvía
class Agent:
    def __init__(self):
        load_environment()
        ...
        self.history = []

    async def run(self, goal, emit):
        self.history.append({"role": "user", "content": goal})
        emit("Agente", f"Recuerdo esta sesi...")
        ...
        response = await self.client.responses.create(
            model=self.model,
            instructions=self.instructions,
            input=self.history, tools=TOOLS   # <- se envía el historial completo
        )
```

> "El arnés es el que se encarga de construir el historial de la sesión y todo lo que debería aparecer ahí: petición y respuestas antiguas, ¿acciones de tools anteriores?, ¿chats antiguos?"

### 6.7 Historial vs. contexto: no son lo mismo

Aquí aparece un problema nuevo: **"el historial no para de crecer y el LLM tiene un límite de memoria (ventana de contexto)".** El material distingue con mucha claridad dos conceptos que se suelen confundir:

| HISTORIAL | CONTEXTO |
|---|---|
| El registro **completo** de lo que ha ocurrido. | Lo que **realmente recibe** el modelo para tomar la siguiente decisión. |
| Resultados enormes, errores ya resueltos, planes antiguos, información repetida. | Instrucciones vigentes, objetivo y estado actual, evidencia relevante, interacciones recientes. |

> "El historial completo se puede seguir guardando en local pero el LLM solo recibe una versión resumida o adaptada al problema siguiente."

Es decir: **guardar todo no es el problema; enviar todo en cada petición sí lo es.**

### 6.8 Estrategias de *context engineering*

El material propone cuatro estrategias (no son excluyentes, se pueden combinar):

- **A. Crear un resumen adaptado a la nueva pregunta del usuario.**
- **B. Seleccionar lo relevante.**
- **C. Compactar todo el historial para hacer hueco.**
- **D. Guardar información relevante en archivos** (memoria persistente).

El código de ejemplo (de `Cli-harness-v8/ebis_cli/agent.py`, tal cual existe en esta carpeta) implementa las estrategias A y C juntas:

```python
async def compact_history(self):
    if len(self.history) < MAX_CONTEXT_ITEMS:
        return
    response = await self.client.responses.create(
        model=self.model,
        instructions="Resume en español los objetivos, decisiones y resultados de esta conversación...",
        input=self.history,
    )
    self.history = [{"role": "assistant", "content": "Resumen de la sesión: " + response.output_text}]

async def build_context(self, goal):
    if not self.history:
        return "No hay contexto previo relevante."

    response = await self.client.responses.create(
        model=self.model,
        instructions=(
            "Prepara el contexto para el objetivo actual. Del historial, conserva solo "
            "hechos, decisiones y resultados anteriores que ayuden a cumplirlo. "
            "No resuelvas el objetivo ni inventes información. Si nada es relevante, "
            "responde: No hay contexto previo relevante."
        ),
        input=self.history + [{"role": "user", "content": f"Objetivo actual: {goal}"}],
    )
    return response.output_text or "No hay contexto previo relevante."
```

Idea clave: `compact_history` **sustituye** todo el historial por un único mensaje-resumen cuando crece demasiado (estrategia C). `build_context` no modifica el historial guardado, sino que genera, para el objetivo concreto que acaba de llegar, una versión filtrada y adaptada de ese historial (estrategia A + B) — nótese que a la propia API se le pide explícitamente "no resuelvas el objetivo ni inventes información", para que esa llamada solo prepare contexto, no conteste la pregunta del usuario.

> **Importante para no confundirse con el ejercicio de esta carpeta:** en `Cli-harness-v8` el umbral de `compact_history` se mide en **número de elementos** del historial (`MAX_CONTEXT_ITEMS = 20`). En el ejercicio de `ebis-cli-proyect/` (ver sección 9), el umbral que hay que implementar se mide en cambio en **número de palabras** (`MAX_HISTORY_WORDS = 300`). La idea de fondo (compactar cuando se supera un umbral) es la misma; la métrica exacta no.

### 6.9 `AGENTS.md`: fijar el comportamiento por defecto

Si queremos que el agente se comporte siempre igual, la alternativa ingenua sería repetir las mismas instrucciones en cada conversación. La solución que adopta la comunidad (el material cita que **el estándar `AGENTS.md` se adoptó a principios de 2024**, y que Anthropic usa el equivalente `CLAUDE.md`) es tener un fichero de instrucciones fijas dentro del proyecto:

```text
project/
├── AGENTS.md
├── src/
├── data/
└── docs/
```

```markdown
# AGENTS.md

- Escribe los informes en español.
- Conserva los datos originales.
- Separa hechos y recomendaciones.
- Guarda el resultado en report.md.
```

Otra variante que menciona el material: en vez de (o además de) cargar instrucciones fijas, se puede **obligar al agente a leer un archivo siempre**, y ese archivo es el que define su comportamiento en cada sesión.

*(Nota: en el código de esta carpeta, `context.py::load_instructions` combina las instrucciones por defecto del agente con el `AGENTS.md` del proyecto de código y el `AGENTS.md` de la carpeta de trabajo actual — es una aplicación directa de esta idea.)*

### 6.10 Memoria persistente en disco (estrategia D)

Más allá de resumir el historial, se le puede dar al agente la capacidad de guardar datos sueltos en disco, en un almacén clave-valor, para recuperarlos cuando los necesite en el futuro (incluso en otra sesión). Código real de `Cli-harness-v8/ebis_cli/tools.py`:

```python
def save_memory(key: str, value: str) -> str:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    memory = json.loads(MEMORY_FILE.read_text(encoding="utf-8")) if MEMORY_FILE.exists() else {}
    memory[key] = value
    MEMORY_FILE.write_text(json.dumps(memory, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Recuerdo guardado: {key}"


def read_memory(key: str) -> str:
    memory = json.loads(MEMORY_FILE.read_text(encoding="utf-8")) if MEMORY_FILE.exists() else {}
    return memory.get(key, f"No hay ningún recuerdo llamado {key}")
```

En la demo del material, esto permite que el agente responda correctamente a "¿te acuerdas de tareas_ids?" en un paso posterior, tras haber usado `read_memory` para recuperar el valor `1,2,3` que se había guardado antes con `save_memory`.

### 6.11 Verificación: ¿cómo sabemos si el agente cumplió de verdad?

Que el agente diga **"He terminado"** no significa que el resultado sea correcto. El harness debería poder preguntarse: ¿existen los archivos que dijo crear? ¿están todos los apartados? ¿cumple el esquema pedido? ¿pasan las comprobaciones automáticas? ¿hace falta revisión humana? El ciclo que propone el material es:

```text
Generar → Comprobar → Feedback → Corregir
```

En código (`Cli-harness-v8/ebis_cli/agent.py`), esto se implementa como un patrón **ACT + REVIEW**:
- **ACT**: es el bucle agéntico de siempre (el de la sección 6.2/6.4).
- **REVIEW**: un verificador **independiente** compara el objetivo original con la respuesta obtenida y decide si se cumple.

```python
async def review(self, goal, answer, notes):
    response = await self.client.responses.create(
        model=self.model,
        instructions="Eres un verificador independiente. Compara el objetivo con la respuesta y las pruebas. "
                     "Responde con PASS si está completo; si no, empieza con FIX: y explica el cambio concreto.",
        input=f"Objetivo: {goal}\nRespuesta: {answer}\nAcciones y resultados: {notes}",
    )
    return response.output_text.strip()
```

Y el bucle que los combina:

```python
for review_number in range(2):
    answer, notes = await self.act(emit, run_history)
    verdict = await self.review(goal, answer, notes)
    emit("Verificador", verdict)
    if verdict.upper().startswith("PASS"):
        self.history.extend(run_history[history_start:])
        self.run_count += 1
        emit("Agente", answer)
        return
    if review_number == 0:
        run_history.append({"role": "user", "content": "Feedback del verificador: " + verdict + " Corrige el trabajo."})
```

Si el verificador no da el visto bueno, se añade su feedback como un nuevo mensaje ("Feedback del verificador: ... Corrige el trabajo.") y se vuelve a ejecutar el bucle `ACT`, dándole al agente la oportunidad de corregirse él solo, **antes** de devolver la respuesta al usuario. El material incluye un ejemplo real donde el verificador detecta que el agente marcó como correcto un resultado que en realidad no seguía las instrucciones al pie de la letra (había que dejar sin cierto marcador en el primer intento y el agente se lo saltó), y le obliga a repetir el proceso correctamente.

### 6.12 Subagentes: dividir y aislar el contexto

Un **subagente** es, literalmente, otro bucle ReAct, con su propio objetivo y su propio contexto — no comparte el historial del agente principal. Esto permite que un **orquestador** reparta un objetivo complejo entre varios subagentes especializados (por ejemplo: Investigar, Analizar, Redactar), cada uno con su contexto propio:

> "Permite aislar contexto: cada subagente tiene el suyo para el objetivo que tiene asignado."

En código, delegar es simplemente **otra tool más** que el modelo puede decidir invocar:

```python
DELEGATE_TOOL = {
    "type": "function", "name": "delegate_task",
    "description": "Delega una parte del objetivo a un subagente con contexto propio.",
    "parameters": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"], "additionalProperties": False},
    "strict": True,
}

# En el despacho de llamadas:
for call in calls:
    arguments = json.loads(call.arguments)
    if call.name == "delegate_task":
        result = await self.run_subagent(arguments["task"], emit)
    else:
        result = self.execute("lead", call.name, arguments)
```

Y el subagente es un bucle agéntico prácticamente idéntico al principal, pero arrancando con un objetivo (`task`) distinto y su propia lista de mensajes:

```python
async def run_subagent(self, task, emit):
    emit("Subagente", f"Empiezo: {task}")
    messages = [{"role": "user", "content": task}]
    for _ in range(3):
        response = await self.client.responses.create(
            model=self.model,
            instructions=self.instructions + "\nAdemás, eres un subagente con permisos limitados. "
                         "Resuelve solo la tarea delegada en la carpeta de trabajo actual.",
            input=messages, tools=self.tools_for("worker"),
        )
        messages.extend(response.output)
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text or "Subtarea terminada."
        for call in calls:
            result = self.execute("worker", call.name, json.loads(call.arguments))
            messages.append({"type": "function_call_output", "call_id": call.call_id, "output": result})
            emit("Subagente tool", f"{call.name} -> {result}")
    return "Subagente detenido al llegar a 3 pasos."
```

### 6.13 Seguridad: permisos por rol

Punto de partida: **"Tener una capacidad disponible no concede permiso para utilizarla."** Igual que en un sistema operativo como Linux se pueden dar permisos distintos a distintos usuarios, se pueden limitar las tools que puede usar cada agente o subagente. Esto reduce directamente el riesgo de *prompt injection* (el material da un ejemplo muy claro: "el agente que busca en internet no puede ejecutar comandos"). Tabla de ejemplo del material:

| Rol (ejemplo) | Leer | Buscar | Escribir | Borrar | Enviar |
|---|---|---|---|---|---|
| Researcher | Sí | Sí | No | No | No |
| Writer | Sí | No | Sí | No | No |
| Reviewer | Sí | No | No | No | No |
| Main | Sí | Sí | Sí | Aprobar | Aprobar |

Código real de `Cli-harness-v8/ebis_cli/agent.py`:

```python
LEAD_PERMISSIONS = {"list_files", "read_file", "write_file", "save_memory", "read_memory", "verify_file", "delegate_task"}
WORKER_PERMISSIONS = {"list_files", "read_file", "write_file"}

def tools_for(self, role):
    allowed = LEAD_PERMISSIONS if role == "lead" else WORKER_PERMISSIONS
    definitions = TOOLS + [DELEGATE_TOOL]
    return [tool for tool in definitions if tool["name"] in allowed]

def execute(self, role, name, arguments):
    allowed = LEAD_PERMISSIONS if role == "lead" else WORKER_PERMISSIONS
    if name not in allowed:
        return f"Permiso denegado: {role} no puede usar {name}"
    ...
```

Es decir: el agente principal ("lead") puede además usar memoria, verificar archivos y delegar; el subagente ("worker") solo puede listar, leer y escribir archivos. Y hay **doble comprobación**: `tools_for` filtra qué esquemas ve el modelo (para que ni siquiera "sepa" que existen tools que no puede usar), y `execute` vuelve a comprobar el permiso en tiempo de ejecución (por si acaso el modelo intentase invocar algo que no debería). El material lo demuestra con un experimento: en la versión sin permisos (v7), el subagente conseguía guardar y leer memoria sin problema porque tenía acceso a esas tools; en la versión con permisos (v8), al pedirle exactamente lo mismo, el subagente **no puede** hacerlo porque `save_memory`/`read_memory`/`verify_file` no están en `WORKER_PERMISSIONS`, y el verificador detecta el fallo y reintenta sin éxito ("El subagente no conoce esa tool").

---

## 7. ¿Qué es una tool en la práctica? (function calling)

El LLM no ejecuta nada — solo es "el cerebro". El objetivo de esta sección es explicar el **"idioma común"** que permite al harness y al LLM entenderse para solicitar y ejecutar herramientas: el **function calling**.

### 7.1 Las tres partes de una tool

Una tool se anuncia al modelo como un contrato en JSON, con tres partes:

- **Identificador único** (`name`): el nombre que identifica la herramienta sin ambigüedad, y que debe coincidir exactamente con el nombre de la función Python real.
- **Descripción semántica** (`description`): el "manual de uso" de la herramienta — qué hace, cómo funciona, cuándo es útil. Es lo que le permite al modelo decidir *si* debe pedirla o no.
- **Esquema JSON de parámetros** (`parameters`): una tool es, al final, una función; este apartado define sus argumentos, el tipo de cada uno (string, number, integer...), una descripción, cuáles son obligatorios (`required`) y si se permiten argumentos extra (`additionalProperties`).

Ejemplo real, tal como aparece en `tools.py` de los proyectos de esta carpeta:

```python
TOOLS = [
    {
        "type": "function",
        "name": "list_files",
        "description": "Lista los archivos de la carpeta de trabajo actual.",
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Lee un archivo de la carpeta de trabajo actual.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]
```

`strict: True` le pide a la API que valide de forma estricta que los argumentos recibidos cumplen exactamente el esquema declarado.

### 7.2 OpenAI vs. Anthropic: dos "idiomas" parecidos pero no idénticos

El material señala explícitamente que **Anthropic y OpenAI usan esquemas de tools diferentes**. En el esquema de OpenAI, los parámetros van bajo la clave `"parameters"`. En el de Anthropic, la clave equivalente es `"input_schema"` (y no se usan las claves `"type": "function"` ni `"strict"` en el nivel superior de la misma forma). El *contenido* del esquema (tipo objeto, propiedades, tipos de cada campo, `required`) es prácticamente igual; lo que cambia es el "envoltorio" JSON concreto que espera cada proveedor.

### 7.3 Cómo "aprendió" el modelo a rellenar ese esquema

El material plantea la pregunta "¿cómo sabe el LLM responder correctamente a ese schema?" y responde: mediante **Reinforcement Learning** orientado a uso de herramientas, en una progresión histórica:
- **ChatGPT 2022**: LLM entrenado con Reinforcement Learning para comportarse como un asistente.
- **Structured outputs 2024**: se permite un "modo JSON" para que el modelo responda en ese formato exacto.
- **Tools y Agent 2025**: el modelo aprende a usar tools y a comportarse de forma agéntica.

### 7.4 Cómo responde el LLM cuando decide usar una tool

Cuando el modelo, tras razonar, concluye algo como *"necesito leer un archivo para responder esto"*, **no responde con un mensaje de texto normal**:

1. Silencia su respuesta de texto: el campo de contenido llega como `"content": null`.
2. Devuelve, en su lugar, una **lista estructurada de llamadas a tools** (lo que además permite pedir varias herramientas distintas en un mismo turno):

```json
"tool_calls": [
  {
    "id": "call_K8s9D2xL1p0QmZ5vW4eR7tY",
    "type": "function",
    "function": {
      "name": "read_file",
      "arguments": "{\"filepath\":\"main.py\",\"max_lines\":10}"
    }
  }
]
```

### 7.5 Cómo el harness intercepta, ejecuta e inyecta el resultado

Cuando el harness detecta que la respuesta trae `function_call` (o `tool_calls`), hace dos cosas:

1. **Deserializa y despacha**: convierte el JSON de argumentos a un diccionario Python (`json.loads`) y ejecuta la función local correspondiente, validando los argumentos recibidos: `dispatch_tool(call.name, json.loads(call.arguments))`.
2. **Inyecta el resultado**: añade el resultado al historial/contexto de la conversación, para que en la siguiente vuelta del bucle el modelo pueda leerlo y decidir cómo seguir:

```python
run_history.append({
    "type": "function_call_output",
    "call_id": call.call_id,
    "output": result,
})
```

El dispatcher, en su forma más simple (código real de este mismo repositorio), es solo un diccionario que traduce nombres a funciones, con manejo de errores:

```python
def dispatch_tool(name: str, arguments: dict) -> str:
    functions = {
        "list_files": list_files,
        "read_file": read_file,
        "write_file": write_file,
    }
    try:
        return functions[name](**arguments)
    except Exception as error:
        return f"Error de herramienta: {error}"
```

Si falta el esquema en `TOOLS`, el modelo nunca sabrá que la herramienta existe. Si falta la entrada en el diccionario de `dispatch_tool`, la llamada nunca llegará a ejecutarse aunque el modelo la pida. **Las tres piezas (función Python, esquema JSON, entrada en el dispatcher) tienen que existir y coincidir en el nombre**, o la tool no funciona.

---

## 8. De la teoría al código real de esta carpeta

### 8.1 Comparativa rápida v1 vs v8

| | `Cli-harness-v1` | `Cli-harness-v8` |
|---|---|---|
| Bucle | `while True`, sin límite | `for step in range(1, MAX_STEPS + 1)` con `MAX_STEPS = 6` |
| Historial entre `run()` | No existe (`input_items` se reinicia cada vez) | `self.history` persiste y se reenvía |
| Gestión de contexto | Ninguna | `compact_history()` (por nº de items) + `build_context()` (resumen adaptado al objetivo, activo desde el 4º `run`) |
| Memoria en disco | No | `save_memory` / `read_memory` sobre `.agent-memory.json` |
| Verificación | No | Patrón `ACT` + `review()` con reintento si el veredicto no es `PASS` |
| Subagentes | No | `delegate_task` + `run_subagent()` |
| Permisos | Todas las tools para cualquiera | `LEAD_PERMISSIONS` / `WORKER_PERMISSIONS` + `tools_for(role)` + `execute(role, ...)` |
| Tools disponibles | `list_files`, `read_file`, `write_file` | Las anteriores + `save_memory`, `read_memory`, `verify_file`, `delegate_task` |

v8 no sustituye a v1: **lo contiene y lo amplía**. Cada capacidad nueva se añade sobre el mismo esqueleto de bucle ReAct de v1.

### 8.2 El ejercicio de `ebis-cli-proyect/` — cómo pensarlo (sin dártelo resuelto)

El punto de partida de `ebis-cli-proyect/` ya trae el bucle acotado (`MAX_STEPS = 6`) y un `self.history` que se actualiza al final de cada `run()`, pero tiene **dos fallos puestos a propósito** (ver `Enunciado - Ejercicio propuesto.pdf`):

1. Dentro del bucle, la llamada a la API usa `input=goal` en vez de `input=run_history`. Como viste en la sección 6.5, esto significa que el modelo solo ve el objetivo suelto, **sin** el historial previo ni los resultados de tools que el propio bucle acaba de añadir a `run_history`.
2. `self.history` se puede llenar sin límite: nada lo compacta nunca.

**TODO 1 — `tools.py`**: hay que añadir dos tools nuevas (`count_words` y `calculate_total`) siguiendo exactamente el patrón de la sección 7.1: función Python + entrada en `TOOLS` con su esquema + entrada en el diccionario de `dispatch_tool`. Para practicar el patrón sin copiarte la solución, aquí tienes un ejemplo *distinto* pero estructuralmente idéntico a lo que se pide (una tool inventada, `to_uppercase`, que no existe en el proyecto):

```python
# 1. La función Python
def to_uppercase(text: str) -> str:
    return f"Texto en mayúsculas: {text.upper()}"

# 2. Su esquema en TOOLS
{
    "type": "function",
    "name": "to_uppercase",
    "description": "Convierte un texto a mayúsculas.",
    "parameters": {
        "type": "object",
        "properties": {"text": {"type": "string", "description": "Texto a convertir."}},
        "required": ["text"],
        "additionalProperties": False,
    },
    "strict": True,
}

# 3. Su entrada en el dispatcher
def dispatch_tool(name: str, arguments: dict) -> str:
    functions = {
        "list_files": list_files,
        "read_file": read_file,
        "write_file": write_file,
        "to_uppercase": to_uppercase,   # <- así se añade
    }
    ...
```

El enunciado pide aplicar exactamente este mismo patrón a `count_words(text: str)` (usa `text.split()` para contar palabras) y a `calculate_total(unit_price: float, quantity: int)` (calcula `unit_price * quantity` y lo devuelve con dos decimales).

**TODO 2 — `agent.py`**: hay que escribir dos métodos nuevos en la clase `Agent`:
- `count_history_words(self, history)`: recorrer la lista y sumar `len(text.split())` del campo `content` de cada elemento — teniendo en cuenta que unos elementos son diccionarios (mensajes de usuario) y otros son objetos de la SDK (respuestas del modelo), y que algunos ni siquiera tienen `content` (los resultados de tools, que usan `output`), así que hay que ignorarlos.
- `compact_history(self, goal)` (asíncrono): si `count_history_words(self.history)` no supera `MAX_HISTORY_WORDS` (300), no hacer nada. Si lo supera, pedir al modelo un resumen (sin `tools=TOOLS`, porque solo se necesita texto) y sustituir `self.history` por un único mensaje de asistente con ese resumen — el mismo patrón que ya viste en `compact_history()` de v8 (sección 6.8), pero cambiando el criterio de "número de items" por "número de palabras".

Y luego corregir `run()` para que, al principio, llame a `await self.compact_history(goal)`, y para que la llamada a la API dentro del bucle use `input=run_history` (no `input=goal`).

Con esto en mente, el ejercicio deja de ser "copiar código de otro sitio" y pasa a ser aplicar, sobre un caso concreto, exactamente los mismos conceptos que ya se explican y se ven funcionando en `Cli-harness-v8/`.

---

## 9. Glosario

- **Token**: fragmento de texto (palabra o parte de una palabra) que un LLM procesa como unidad mínima.
- **Vector / vectorizar**: representar un token como una lista de números que el modelo puede procesar matemáticamente.
- **Contexto / ventana de contexto**: la información que efectivamente recibe el modelo en una petición concreta, y el límite de cuánta información puede recibir a la vez.
- **Alucinación**: respuesta generada por el modelo que suena plausible pero es incorrecta o inventada, normalmente por falta de contexto/datos reales.
- **Grounding**: apoyar las respuestas del modelo en datos reales y verificables (documentos, bases de datos, resultados de herramientas), en vez de dejar que "invente" a partir solo de su conocimiento entrenado.
- **RAG** (*Retrieval-Augmented Generation*): técnica de recuperar documentos relevantes (normalmente de una base de datos vectorial) para dárselos como contexto al modelo antes de que responda.
- **ReAct** (*Reasoning + Acting*): patrón de bucle en el que el modelo alterna entre pensar (`Thought`), actuar (`Action`, invocar una tool) y observar el resultado (`Observation`), repitiendo hasta cumplir el objetivo.
- **Agent Harness / arnés**: la capa de software determinista que rodea al LLM: gestiona el bucle, el contexto, las tools, la seguridad y la verificación.
- **Tool / function calling**: mecanismo por el que un LLM puede "pedir" la ejecución de una función externa, describiendo su nombre, su propósito y sus argumentos mediante un esquema JSON.
- **Dispatcher (`dispatch_tool`)**: la pieza del harness que recibe el nombre de una tool solicitada por el modelo y ejecuta la función Python real correspondiente.
- **`function_call_output`**: el elemento que el harness añade a la conversación con el resultado de una tool, para que el modelo pueda leerlo en el siguiente paso del bucle.
- **Historial**: registro completo (en memoria o disco) de todo lo ocurrido en una sesión con el agente.
- **Context engineering**: el conjunto de técnicas para decidir qué parte del historial (o qué versión resumida/filtrada de él) se envía realmente como contexto en cada petición.
- **Compactar el historial**: sustituir un historial largo por un resumen más corto que conserve lo importante.
- **`AGENTS.md` / `CLAUDE.md`**: fichero de instrucciones de comportamiento por defecto que el agente carga automáticamente en cada sesión, para no tener que repetirlas.
- **Memoria persistente**: datos guardados en disco (por ejemplo en un fichero JSON clave-valor) que sobreviven entre sesiones distintas del agente.
- **Verificador / patrón ACT+REVIEW**: un segundo paso, independiente del agente que actúa, que revisa si el resultado cumple realmente el objetivo antes de darlo por bueno.
- **Subagente**: un bucle ReAct independiente, con su propio objetivo y contexto, lanzado por un agente orquestador para resolver una subtarea concreta.
- **Permisos por rol**: restringir qué tools puede usar cada agente/subagente según el papel que desempeña, reduciendo el riesgo de *prompt injection* y de acciones no deseadas.
- **Prompt injection**: intento de manipular a un agente (por ejemplo, a través de contenido externo que lee) para que ejecute acciones no deseadas; limitar permisos por rol es una defensa contra esto.
- **Sandboxing**: aislar el entorno en el que un agente (o subagente) opera, para limitar el daño que podría causar si se comporta de forma inesperada.
- **`uv`**: gestor de entornos y dependencias de Python (de Astral) que usan los tres proyectos de esta carpeta; usa `pyproject.toml` como única fuente de verdad y genera `uv.lock` para reproducibilidad.

---

## 10. Fuentes usadas en este documento

Todo el contenido anterior procede de:
- `Tema 6_LLM_Agents_tools.pdf` (67 páginas, teoría completa del tema).
- `Enunciado - Ejercicio propuesto.pdf` (enunciado del ejercicio práctico).
- `Guia de uso de UV.pdf` (comandos de `uv`).
- El código real, leído completo, de `Cli-harness-v1/ebis-cli-harness-v1/ebis_cli/agent.py`, `Cli-harness-v8/ebis-cli-harness-v8/ebis_cli/agent.py` y `.../tools.py`, y `ebis-cli-proyect/ebis_cli/agent.py`, `.../tools.py` y `.../context.py`.

No se ha añadido ninguna afirmación técnica sobre el funcionamiento del harness, del bucle ReAct o del código de este repositorio que no esté respaldada por alguna de estas fuentes. Los únicos añadidos que no vienen literalmente del material son ejemplos ilustrativos marcados explícitamente como tales (la frase de "La capital de Francia" en la sección 1, y la tool de ejemplo `to_uppercase` en la sección 8.2), usados solo para aclarar un concepto general sin desvelar la solución del ejercicio.
