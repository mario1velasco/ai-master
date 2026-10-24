# Explicación completa — Tema 03: Skills y Decision Models

Este documento explica todo el tema desde cero. Las referencias "p. N" son páginas de `Tema 6_Decision_Models_Skills.pdf` (76 págs.). Los fragmentos de código son copias del código del repositorio. Las analogías, cuando aparecen, son aclaraciones mías y no figuran en el material.

---

## 1. Dónde estamos: lo que ya tiene un agente (pp. 3-4)

Hasta ahora el curso ha construido tres piezas:

| Pieza | Qué hace |
|---|---|
| **LLM** | Propone el siguiente paso a partir del contexto. |
| **Harness** | Gestiona el bucle, ejecuta las decisiones, aporta control y seguridad. |
| **Tools y MCP** | Permiten ejecutar operaciones y conectar servicios. |

El material afirma que con estas tres piezas se puede crear cualquier sistema automatizado. Y entonces plantea la pregunta "¿ya está?".

## 2. El problema: tener herramientas no es saber hacer el trabajo (pp. 5-8)

Ejemplo del PDF: un agente con `create_ppt_file()`, `run_python()`, `generate_image()`, `add_slide()` y una tool MCP `buscar_en_onedrive()`. Se le pide: *"Créame una buena presentación ejecutiva de 10 slides sobre los datos del fichero de cuentas.csv"*.

El agente **puede** añadir una slide, texto, imagen, gráfica, posicionar elementos y guardar un PPTX. Pero **necesita decidir**: qué slides, cuánto texto, cuándo usar imagen, qué gráfica comunica mejor, cómo componer, cómo validar. Y más: ¿10 slides o 20?, ¿qué narrativa?, ¿qué va primero?, ¿qué layout?, ¿cuándo dividir una slide?, ¿cómo mantener consistencia?, ¿cómo detectar overflow?, ¿cómo validar el PPTX final?

Conclusión del material: *"El Agente tiene las herramientas… Pero necesita saber cómo hacer el trabajo."* Eso es lo que aporta una **skill**.

## 3. Qué es una skill (pp. 10-14)

**Definición del material:** paquete modular con conocimiento sobre procedimientos, reglas y recursos auxiliares que guía al agente a resolver tareas complejas de extremo a extremo.

### Tool vs. skill (pp. 10, 12)
- **Tool (el músculo):** ejecución mecánica, aislada y concreta (escribir un fichero, invocar una API).
- **Skill (el *know-how*):** experiencia de dominio y orquestación (cómo maquetar diapositivas respetando jerarquías y evitando desbordamientos de texto).

| Dimensión | Tool | Skill |
|---|---|---|
| Rol | Músculo: primitiva de ejecución | Cerebro operativo: experiencia de dominio |
| Alcance | Acción puntual atómica | Workflow complejo y procedimental de inicio a fin |
| Control | Depende de la improvisación del LLM | Acota ambigüedades, previene fallos, aporta reglas de diseño |
| Garantía | Ejecución sintáctica | Resultado determinista y consistente |

> "Una tool permite actuar; una skill enseña a concatenar diferentes tools y a usarlas de formas concretas para resolver la tarea con criterio profesional." (p. 12)

### Qué aporta frente a la improvisación del LLM (p. 11)
- **Control de flujo:** procedimientos paso a paso que acotan decisiones ambiguas.
- **Robustez:** aporta el contexto necesario para prevenir errores típicos.
- **Determinismo:** utilidades (plantillas, scripts…) y validaciones auxiliares.

### "Si es solo un prompt detallado y un par de scripts, ¿qué aporta?" (pp. 13-14)
Tres respuestas del material:
1. **Modularidad y reutilización:** desacopla la lógica procedimental del flujo principal; un workflow se vuelve estándar auditable, versionable (Git) y reutilizable entre diferentes agentes.
2. **Cero saturación de contexto:** un mega-prompt satura la ventana antes de empezar; la skill se invoca **bajo demanda**.
3. **Consistencia y repetibilidad:** acota la dispersión probabilística; dos ejecuciones siguen las mismas reglas de parada, contratos y criterios de calidad.

Frase de cierre: una skill transforma un prompt improvisado y frágil en un activo de software modular, testeable, mantenible y reusable.

## 4. Cómo se construye una skill (pp. 15-23)

### 4.1 Estructura de carpetas (p. 16)
"Una skill mínima consta de un directorio y un `SKILL.md` con YAML y Markdown."

```text
executive-presentation/
├── SKILL.md          # OBLIGATORIO
├── references/       # OPCIONAL: consulta
├── scripts/          # OPCIONAL: ejecución
└── assets/           # OPCIONAL: plantilla
```
Contrato mínimo: un `SKILL.md` completo define la skill mínima; **el nombre de la carpeta coincide con `name`**. Descubrimiento: en Codex, repo `.agents/skills/` y usuario `~/.agents/skills/`; cada cliente configura sus rutas (el material cita también `~/.codex/skills/` y `.claude/skills/`).

### 4.2 Metadatos (pp. 17, 19)
Bloque YAML al inicio del archivo, entre marcas `---`. Sirve para identificar la skill y para que el enrutador decida cuándo activarla según la intención del usuario. Ejemplo del material:

```yaml
---
name: presentations
description: Read, create or edit PowerPoint or Google Slides decks. Use for
  presentation, slide deck, PowerPoint, PPT, PPTX, or Google Slides requests.
version: 2.16.4
---
```
Reglas (p. 19): `name`: a-z, 0-9 y guiones (1-64); `description`: intención y activación (1-1024). Opcionales: `license`, `compatibility`, `metadata`, `allowed-tools` (experimental). Alternativas al YAML: `skill.json`, `manifest.json`, `metadata.yaml`.

Ejemplo real de este repo (`presentacion-open/SKILL.md`):
```yaml
---
name: presentations-open
description: >
  Crea y valida presentaciones PowerPoint (.pptx) editables usando python-pptx
  y un validador geométrico de márgenes. Actívala para peticiones de diapositivas,
  decks y presentaciones corporativas sin dependencias propietarias.
---
```
(Observa que `name` es `presentations-open` y la carpeta `presentacion-open`: no coinciden, algo que el propio material pide.)

### 4.3 Instrucciones (p. 18)
El cuerpo Markdown tras el frontmatter marca la política operativa: flujo paso a paso, qué debe o no hacer, casos límite y formato de salida. Alternativas: `PROMPT.md`, `instructions.md`, `system.md`.

### 4.4 Schema de datos (p. 20)
Condicional. Un bloque `parameters:` (JSON Schema) en el YAML permite validar qué argumentos necesita la skill (el slide muestra `csv_path`, `quarter` con patrón, `audience` con enum, `slide_count` entre 4 y 12, `additionalProperties: false`). Pero el material advierte: *"en las skills de OpenAI/Codex esas instrucciones van en el cuerpo de la skill."*

### 4.5 Lógica ejecutable (p. 21)
`scripts/` (opcional): acciones deterministas fuera del LLM que resuelven tareas repetitivas. El nombre `scripts/` no es obligatorio; basta dejarlo descrito en `SKILL.md`. La skill `presentations` de OpenAI guarda los suyos en `container_tools/` y `template_following_scripts/`.

### 4.6 Documentación de apoyo (p. 22)
`references/` (opcional): archivos **leídos bajo demanda** (esquemas SQL, specs de APIs) para no gastar tokens. `SKILL.md` indica dónde está cada documento y cuándo consultarlo, así "el modelo lee solo las referencias necesarias".

### 4.7 Archivos estáticos (p. 23)
`assets/` o `templates/`: plantillas base o ficheros fijos. La skill de OpenAI incluye un PNG y un `openai.yaml` que describe cómo representar la skill en sus apps (`display_name`, `short_description`, iconos, `brand_color`, `default_prompt`).

## 5. Caso de estudio: de la skill privada de OpenAI a `presentacion-open` (pp. 24-34)

La historia que cuenta el material:
1. En ChatGPT Work el agente crea un sandbox (VM) y usa la skill `presentations`. Se le pide el ZIP de esa skill: 59 archivos (p. 25).
2. Esa skill **no existe en el dispositivo del usuario**: se instala siempre en el sandbox remoto; es privada (p. 27).
3. Se copia con todo su árbol a `.codex/skills` y Codex la detecta automáticamente (p. 28).
4. **Problema:** al usarla, Codex se bloquea: faltan variables `CODEX_PRIMARY_RUNTIME_*` y el módulo `@oai/artifact-tool`; "la skill usa dependencias/librerías privadas que OpenAI no comparte" y el sandbox no deja obtenerlas (pp. 29-30).
5. **Solución:** usando las mismas guías, recomendaciones e instrucciones, crear una skill nueva que use otra herramienta para generar pptx: **python-pptx**. El SKILL.md original decía literalmente lo contrario (`do not use python-pptx`) (p. 31). Se usa Codex para copiar la skill adaptando las herramientas privativas (p. 32).
6. Resultado: pidiendo una presentación de F1 con una imagen como plantilla, se genera un deck de seis slides con ilustraciones generadas y comprobación geométrica; no había visor para revisar el render (pp. 32-34).

Cierre (p. 34): en sistemas agénticos, **el verdadero activo técnico es el diseño del sistema**: restricciones, flujo lógico e instrucciones que guían al modelo.

### 5.1 Anatomía de `presentacion-open/`

```text
presentacion-open/
├── SKILL.md                 # flujo de 7 pasos + capacidades + límites
├── agents/openai.yaml       # interface: display_name, brand_color, default_prompt; policy.allow_implicit_invocation: true
├── requirements.txt         # python-pptx==1.0.2
├── assets/                  # base_theme.pptx + create_base_theme.py (lienzo en blanco 13.333x7.5 in)
├── examples/capabilities.json   # deck de ejemplo de 5 slides
├── references/              # 10 guías leídas bajo demanda
└── scripts/                 # compilador y validadores
```

**El flujo del `SKILL.md`** (los 7 pasos reales):
1. *Ingesta y normaliza* el encargo a `deck.json` (esquema en `references/deck_schema.md`); no inventar hechos.
2. *Verifica reglas de diseño* (`design_rules.md`, `writing_quality.md`, y según el caso `template_workflow.md`, `data_visuals.md`, `finance.md`, `google_slides.md`).
3. *Compila*: `python3 scripts/compile_deck.py /ruta/deck.json --output /ruta/out/presentation.pptx`.
4. *Bucle de QA*: `check_overflow.py`, `check_package_integrity.py`, y cuando corresponda `check_table_arithmetic.py` y `check_template_fidelity.py`; `inspect_presentation.py` para localizar problemas.
5. *Consulta Context7* para componentes avanzados de python-pptx (aquí aparece un MCP, tema 02, como apoyo de una skill).
6. *Revisa visualmente*: python-pptx no renderiza; los validadores geométricos no prueban que el texto se vea bien.
7. *Entrega* en archivo nuevo, sin sobrescribir la fuente, indicando limitaciones.

Observa cómo encaja con la teoría: el `SKILL.md` es corto (procedimiento), el detalle vive en `references/` (se lee según el caso, p. 22), el determinismo en `scripts/` (p. 21) y la plantilla base en `assets/` (p. 23).

**Qué contiene cada módulo** (leído de los ficheros):
- `deck_schema.md`: raíz (`metadata`, `template`, `slide_size`, `theme`, `font_policy`, `requirements`, `slides`), tipos de slide (`cover`, `content`, `existing`), layout automático (`items`, `columns`, `layout_mode`) o explícito (`elements`: `textbox`, `image`, `table`, `chart`, `shape`, `connector`), y 29 tipos de chart.
- `design_rules.md`: portada, jerarquía (guía de 42/32/≥17 pt), márgenes seguros de 0,6 in, máximo de 180 caracteres por contenedor (convención del compilador, no de la skill original), imágenes y evidencia.
- `writing_quality.md`: calidad editorial de títulos y copy. `data_visuals.md`, `finance.md`: tablas, gráficos, cifras. `google_slides.md`: solo genera PPTX local.
- `porting_matrix.md`: qué de la skill original tiene reemplazo directo, parcial o ninguno. `qa_delivery.md`: secuencia y límites del QA.
- `scripts/`: `compile_deck.py` (459 líneas, orquesta) y `pptx_components.py` (775, componentes), más cinco validadores.

Un fragmento real del ejemplo `examples/capabilities.json` (el contrato de aritmética que valida `check_table_arithmetic.py`):
```json
"arithmetic_contracts": [
  { "slide": 3, "table": 1, "operation": "sum",
    "inputs": [[1, 1], [2, 1]], "result": [3, 1], "tolerance": "0" }
]
```
Aquí está el "determinismo" de la skill en miniatura: una regla declarada (`40 + 60 = 100`) que un script comprueba, en vez de confiar en que el LLM sume bien.

## 6. ¿Alternativa a las tools? El coste del catálogo (pp. 35-41)

### 6.1 Las tools consumen contexto (p. 36)
Cada tool aporta nombre, descripción y esquema de parámetros, y se envía en cada petición:
```python
response = client.responses.create(input="Crea una presentación", tools=TOOLS)
```
Si cada solicitud incluye el catálogo completo, "la ventana de contexto está llena de tareas que no usa". Compruébalo en el código: `TOOLS` de `ebis_cli/tools/local.py` es una lista de siete diccionarios de este estilo:
```python
{
    "type": "function",
    "name": "read_file",
    "description": "Lee un archivo de texto dentro del workspace.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                   "required": ["path"], "additionalProperties": False},
    "strict": True,
}
```
y el runtime los envía con las tools de MCP: `schemas = [*TOOLS, *self.mcp.tools_for_model]` (`agent/runtime.py`, `available_tool_schemas`).

### 6.2 Hay problemas que exigen muchas tools (p. 37)
Hacer presentaciones solo con tools exigiría `parse_template()`, `fetch_context()`, `insert_shape()`, `export_preview()`, `check_bounds()`… y aun así habría que explicar al agente cómo combinarlas. "Una skill permite tanto articular protocolos, procedimientos y reglas de negocio, como empaquetar los scripts y recursos."

### 6.3 Las skills ocupan contexto por capas (p. 38)
| Cuándo | Qué entra al contexto |
|---|---|
| Al descubrir | Metadatos: `name`, `description` y `path` |
| Al seleccionar | `SKILL.md`: flujo principal y criterios |
| Cuando hacen falta | Recursos: `references/`, `scripts/`, `assets/` |

El runtime aporta los metadatos; el modelo lee `SKILL.md` al activar la skill y consulta referencias cuando el flujo las necesita (*divulgación progresiva*, término mío para describirlo).

### 6.4 `defer_loading` y Tool Search (p. 39)
Alternativa para el cuello de botella de las tools: al inicio solo se cargan nombre y descripción; **Tool Search** encuentra la herramienta y se carga su esquema de parámetros cuando hace falta. El slide compara "sin `defer_loading`: 85 % de contexto ocupado" con "con `defer_loading`: 15 %" (cifras ilustrativas del propio slide).

### 6.5 Skills sin crear tools nuevas (p. 40)
En vez de programar `tool_ffmpeg_cut_video(...)`, `tool_ffmpeg_extract_audio(...)`… (frágil, rígido, incompleto), el host aporta la CLI nativa, el agente una tool genérica (bash) y **la skill aporta el protocolo y los scripts**. "Cero código nuevo en el runtime del agente."

### 6.6 Piezas combinables (p. 41)
| Necesidad | Pieza | Aportación |
|---|---|---|
| Flujo repetible | Skill | Instrucciones, criterios y referencias |
| Acción estructurada | Tool / MCP | Entradas, ejecución y acceso controlado |
| Carga inicial del catálogo | `defer_loading` | Esquemas disponibles bajo demanda |
| CLI instalada | Shell + Skill | Uso guiado de herramientas existentes |

"Una skill puede guiar el uso de una tool, un MCP o una CLI según la ejecución requerida."

## 7. Generación vs. decisión cerrada (pp. 42-45)

Un LLM calcula una **distribución de probabilidad sobre el siguiente token** (tokenización → contexto → probabilidades sobre el vocabulario, p. 43). Es **autorregresivo**: cada token generado se añade al contexto y condiciona el siguiente; la caché KV evita recomputar el prefijo pero la salida conserva su dependencia secuencial (p. 44).

Consecuencia clave (p. 45): **un JSON también se genera token a token**. Cuando se pide una *Structured Output*, el schema se genera token a token; "una decisión pequeña puede ocupar una secuencia completa de salida". Imagina que solo necesitas saber si la respuesta es `buscar`, `responder` o `rechazar`: pagas y esperas por emitir `{"decision": "buscar"}` carácter a carácter.

## 8. Decision Models (pp. 46-52)

Idea: **conservar** la comprensión del contexto y **cambiar el motor de salida** (de texto libre a decisión tipada).

1. **Inferencia del contexto (p. 47):** la consulta se tokeniza, se convierte en embeddings y atraviesa los bloques transformer, igual que en un LLM generativo, hasta un vector final `h`.
2. **Sin vocabulario abierto ni bucle (pp. 48-49):** el modelo ya no puntúa los ~100k tokens del vocabulario ni itera para generar N tokens.
3. **Proyección a opciones cerradas (p. 50):** `h` pasa por una *decision head* (`W h + b`, softmax sobre K opciones) en **1 pase**. Ejemplo del slide: `buscar 0.94`, `responder_directo 0.04`, `rechazar 0.02`. "El resultado no es generado token a token, simplemente se devuelve la puntuación de las diferentes opciones solicitadas."

### Las tres primitivas (p. 51)
| Primitiva | Fórmula del slide | Devuelve |
|---|---|---|
| **Choice** | `z = W h + b`, `softmax(z)` sobre K opciones | elige una etiqueta y da la distribución (clasificación) |
| **Score** | `s = sigmoid(wᵀh + b)` | valor continuo en [0, 1] (riesgo, adecuación, intensidad; calibrar con datos) |
| **Noul / null** | `P(sí \| h)` | pregunta binaria con probabilidad; `null` = abstención si la política del harness no acepta la confianza o la entrada está fuera de dominio |

### Eficiencia (p. 52)
Un LLM del ejemplo emite 14 tokens = 14 pasos seriales de decodificación (≈450 ms). Un decision model devuelve `choice`, `score` y `noul` desde un estado compartido en **1 round-trip** (≈15 ms), con 0 tokens generativos de salida; "sigue existiendo coste por la llamada y por el input".

## 9. ¿Cuánto trabajo de un agente es decisión? (pp. 53-59)

Ciclo de vida de un agente (p. 53): crear código y diseñar un plan son **generativos**; elegir una tool y seleccionar una dificultad son **decisión discreta**; finalizar (puntuar una respuesta) es **scoring**. El material estima "en el 60 % de los trabajos de un agente existe una ineficiencia" (p. 54).

Caso de uso Codex (pp. 55-58), tarea "corregir un fallo en el inicio de sesión". Tipos de evento: **D** Decisión (elegir qué archivo leer), **G** Generación (escribir el parche), **M** Mixto, **R** Razonamiento (investigar un 401 intermitente), **X** Control (decidir si se cumplió el objetivo). Sobre 114 eventos observados:

| Tipo | Eventos |
|---|---|
| D · Decisión | 68 (59,6 %) |
| G · Generación | 21 |
| X · Control | 16 |
| M · Mixto | 7 |
| R · Razonamiento | 2 |

D + X = 84 eventos = 73,7 %: "margen arquitectónico observable". El resto, 30 (26,3 %), es trabajo abierto o híbrido.

**Arquitectura híbrida (p. 59):** mensaje + estado → **Decision Model** (enrutamiento, selección de tool, clasificación/guardarraíl) → ¿hace falta LLM? Sí → LLM generativo (redacción, síntesis); No → tool/API directa. "El Decision Model decide la rama; el harness aplica la regla y ejecuta."

## 10. Jev y los modelos System One (pp. 60-70)

**Jev** es "un modelo de decisión que devuelve valores estructurados y probabilidades para tareas acotadas" (TypeSafe, "System One Models"). Precio publicado: 0,042 USD por millón de tokens de entrada, salida gratis; tiempo de respuesta 70-500 ms frente a 3-329 s de modelos frontera (pp. 61-62).

### 10.1 SDK en Python (pp. 63-66)
Instalación y clave (el SDK exige Python ≥ 3.10; la clave se guarda en el entorno, no en el código):
```bash
python -m pip install typesafe-sdk
export TYPESAFE_API_KEY="tu_clave"
```
Choice (código del slide, p. 64):
```python
from typesafe_sdk import Choice, TypeSafeClient

with TypeSafeClient() as client:
    r = client.system_one(
        state={"consulta": "¿Qué tiempo hace en Madrid?"},
        questions={
            "siguiente_paso": Choice(
                instructions="¿Qué debe hacer el agente?",
                criteria={"buscar": "Consultar información actual",
                          "responder": "Usar el contexto disponible",
                          "rechazar": "No continuar"},
            )
        },
    )
decision = r.choices["siguiente_paso"]
print(decision.choice, decision.confidence)
```
Campos devueltos: `choice`, `confidence`, `probabilities`. Choice + Score + Noul en una llamada (p. 65): `r.choices[...]`, `r.scores[...].score`, `r.nouls[...].noul`. El `state` se comparte entre las preguntas.

**La decisión gobierna la rama (p. 66):**
```python
if decision.confidence < 0.75:
    branch = "revision_humana"
elif decision.choice == "buscar":
    branch = "llamar_tool"
elif decision.choice == "rechazar":
    branch = "detener"
else:
    branch = "responder_con_llm"
```
El umbral 0.75 "es una política de ejemplo: ajústalo con evaluación de tu tarea". "Jev devuelve señales tipadas. Tu aplicación conserva el control del flujo y de las reglas de negocio."

### 10.2 Alternativas (pp. 67-70)
`pplx-decider-v1-27b` de Perplexity (pesos abiertos, API con Choice/Noul/Score, 0,04 USD/M entrada); modelos abiertos reproducidos por terceros (Tiny-Jev-1.7B, Kev-4B: "reproducciones independientes, pesos abiertos, coste de despliegue propio"); el *Jev Decision Index* (70 reproducciones, 43 benchmarks: accuracy, calibración, latencia); y la **Decisions API** de OpenAI, en preview (en su demo, 1,6 s/request con Responses API frente a 150 ms con Decisions API).

## 11. Ejemplos: LLM vs. Decision Model (pp. 71-75)

- **Snake (p. 72):** un juego donde decidir el movimiento es clasificación; también atención al cliente (`score 0.94`, `choice "escalar"`), clasificación de datasets y mitigación DDoS (`drop` en <5 ms) como usos de una sola pasada.
- **EBIS CLI + routing (p. 73):** la app del proyecto `ebis-cli-decision-model` muestra líneas como `JEV · CHOICE → automatic_tool_selection` y `JEV · ROUTING → gpt-6.1-sol (medium_reasoning; reasoning.effort=medium)`.
- **Ejercicio 1, extracción sencilla (p. 74):** "Extrae el nombre del proyecto, la versión y el lenguaje… Texto: *El proyecto Faro está en la versión 2.4 y está escrito en Python*."

  | | Jev activado | Jev desactivado |
  |---|---|---|
  | OpenAI | 1 llamada · 570 tokens · $0.00006660 | 1 llamada · 1,068 tokens · $0.00284850 |
  | Jev | 2 decisiones · 4,079 tokens · $0.00016027 | 0 |
  | Coste conjunto | $0.00022687 | $0.00284850 |

  Ahorro de 0.0026 (92 %). Los tokens de entrada de OpenAI son 546 con Jev frente a 1,044 sin él; el slide no explica la causa del coste menor (podría ser el modelo elegido por el routing y la acción acotada, pero eso es una suposición mía).
- **Ejercicio 1, procedimiento largo (p. 75):** auditoría de un workspace: 12 llamadas OpenAI en ambos casos; con Jev, 25 decisiones; coste conjunto $0.02646989 vs $0.04235182. Ahorro de 0.016 (38 %).

Moraleja (mía): el ahorro depende de la tarea; cuanto más sencilla, más compensa enrutarla a un modelo pequeño, y las decisiones de Jev tienen su propio coste.

## 12. Del PDF al código: `ebis-cli-decision-model` en detalle

### 12.1 Dónde encaja Jev: dos decisiones por iteración
Lo documenta `DECISION_MODEL.md` y lo implementa `agent/runtime.py`. En cada iteración de `Agent.run`:

1. **Choice de acción** (`ActionChooser.choose_next`): elige entre una tool concreta (`tool__<nombre>`), `build_context` o `final_answer`.
2. **Routing** (`LLMRouter.route`): para la request a OpenAI que sigue, elige un nivel de `routing-llm.json`.

```text
Objetivo + historial → Choice (qué hacer) → Routing (con qué modelo) → request OpenAI → tool / contexto / respuesta → siguiente iteración
```

### 12.2 El adaptador mínimo: `decision_model/typesafe.py`
```python
def _choose_sync(state, instructions, criteria) -> TypeSafeDecision:
    with TypeSafeClient() as client:
        result = client.system_one(
            state=state,
            questions={"decision": Choice(instructions=instructions, criteria=criteria)},
        )
    ...
    return TypeSafeDecision(choice=result.answers["decision"].choice, usage=TypeSafeUsage(...))

async def choose(state, instructions, criteria) -> TypeSafeDecision:
    """Ejecuta una decisión Jev sin bloquear el event loop de Textual."""
    return await asyncio.to_thread(_choose_sync, state, instructions, criteria)
```
El SDK es síncrono y la app es asíncrona (Textual), así que se envuelve con `asyncio.to_thread`. Fíjate: una sola función `choose` sirve para Choice y para Routing; solo cambian `state`, `instructions` y `criteria`.

### 12.3 Choice de acción: `decision_model/choices.py`
Construye el diccionario `criteria` (etiqueta → significado):
```python
criteria = {FINAL_ANSWER: "Ya hay información suficiente para responder al usuario sin otra tool."}
if allow_context:
    criteria[BUILD_CONTEXT] = "El agente necesita crear contexto breve, separar hechos de dudas o formular una auto-pregunta antes de actuar."
for tool in tools:
    choice_key = f"tool__{tool['name']}"
    ...
    criteria[choice_key] = f"Invoca la tool {name}: {description[:300]}"
```
Es el mismo patrón del PDF (p. 64): `criteria` = opciones cerradas con su descripción. Además:
- El `state` es el objetivo, el número de paso, un extracto del historial (últimos 12 items, ≤ 6.000 caracteres) y las acciones disponibles.
- Una tool **sin argumentos requeridos** recibe la nota "No requiere argumentos; Jev puede ejecutarla directamente sin una llamada OpenAI". `runtime._can_execute_without_llm` lo comprueba y, si procede, el harness fabrica la `function_call` (`"arguments": "{}"`) y la ejecuta **sin pedir nada al LLM**: una request evitada (`openai_calls_avoided`).
- Si la tool sí necesita argumentos, la request siguiente recibe **solo ese esquema** y `tool_choice` fijado a su nombre: `tools=[schema], tool_choice={"type": "function", "name": selected_name}`.
- **La respuesta se valida**: si `selected` no es ninguna clave conocida, se devuelve `AUTO_TOOLS` con `failed=True` ("opción desconocida; fallback automático"). Lo mismo si falta `TYPESAFE_API_KEY` o Jev lanza excepción.

Estados posibles (`ActionChoice.action`): `"tool"`, `"build_context"`, `"final_answer"` y `"automatic_tool_selection"` (modo de reserva: el LLM elige con function calling, `tool_choice="auto"`).

### 12.4 Prompts por fase: `prompts.py`
`action_prompt(action, selected_tool)` adapta las instrucciones al resultado de Choice: para `"tool"` pide "una llamada de función con argumentos válidos y mínimos… no inventes su valor"; para `"build_context"`, una nota breve con hechos, lo que falta y la siguiente pregunta; para `"final_answer"`, responder sin pedir tools nuevas. Así el LLM recibe una tarea acotada, no el problema entero.

### 12.5 Routing: `decision_model/routing.py` + `routing-llm.json`
`LLMRouter` carga una **allowlist** local de seis niveles (nombre → modelo, `reasoning_effort`, descripción de cuándo usarlo, precios) y plantea a Jev una Choice cuyas opciones son esos niveles. Puntos importantes del código:
- `route()` devuelve siempre un `RouteChoice` con modelo y esfuerzo **tomados del JSON**, nunca de lo que diga Jev: `model=models[tier]["model"]`. Si Jev devuelve un nivel que no existe, cae a `default`.
- `_load()` valida el JSON: `models` no vacío, `reasoning_effort` en el conjunto soportado, compatibilidad modelo/esfuerzo (`MODEL_REASONING_EFFORTS`), precios no negativos, `default` y `savings_baseline` existentes.
- El prompt de routing indica cuándo usar `none`, `low`, `medium` o `high` y avisa: "La longitud del prompt por sí sola no lo justifica".
- El runtime fija `reasoning={"effort": route.reasoning_effort}` explícitamente en cada `responses.create`.

Los seis niveles (nombres de `routing-llm.json`): `cheap_no_reasoning`, `cheap_reasoning`, `medium_no_reasoning`, `medium_reasoning` (por defecto), `expensive_no_reasoning`, `expensive_reasoning` (`savings_baseline`).

**⚠ Aviso verificado:** el JSON actual asigna `gpt-6.1-sol` con `reasoning_effort: none` a `medium_no_reasoning` y `expensive_no_reasoning`, y `routing.py` declara que `gpt-6.1-sol` no admite `none`. Ejecutando `LLMRouter()` (con un stub de `typesafe_sdk`) el resultado es: `ValueError: El modelo gpt-6.1-sol no admite reasoning.effort=none; valores documentados aquí: high, low, max, medium, xhigh.` Como `Agent.__init__` crea `LLMRouter(...)`, la aplicación no arrancaría con este JSON. El `README.md` del proyecto describe otros modelos (`gpt-6-sol`, `gpt-5.6-sol`) para esos niveles, que es consistente con el validador. No se ha tocado el código.

### 12.6 El bucle en `agent/runtime.py` (método `run`)
Esquema simplificado de lo que hace cada iteración (hasta `MAX_AGENT_STEPS = 16`):
```python
choice = await self.chooser.choose_next(goal=goal, history=self.history, tools=tools,
                                        step=step, allow_context=context_builds < MAX_CONTEXT_BUILDS)
if choice.action == "build_context": ...   # request sin tools, nota de contexto, continue
if choice.action == "final_answer": ...    # request en streaming, return
if choice.action == "automatic_tool_selection": ...   # fallback con tools=auto
# si no: tool elegida → ejecución directa o request con solo ese esquema
```
`_request` llama primero a `self.router.route(...)`, emite el evento "Routing", construye la request (`model`, `reasoning`, `instructions`, `input`, `tools`, `tool_choice`), usa streaming solo para `final_answer`, registra el uso y añade `response.output` al historial. `_execute_call` ejecuta la tool (local, MCP o `delegate_task`) y guarda `function_call_output` truncado a `MAX_TOOL_OUTPUT_CHARS = 20_000`.

**Resiliencia:** si Choice o Routing fallan (`failed=True`), `_disable_decision_after_failure` desactiva el Decision Model automáticamente y la tarea continúa con function calling automático y el nivel `default`. Puedes alternarlo a mano con `/decision on|off|toggle|status`.

### 12.7 Estadísticas y comparación: `workspace/usage.py`
Aquí se reproduce, en el propio CLI, la comparación de los ejercicios de las pp. 74-75. `UsageTracker`:
- separa los contadores por modo (`decision_on` / `decision_off`) y por modelo y nivel;
- estima el coste de OpenAI con las tarifas de `routing-llm.json` (entrada, entrada en caché, escritura de caché, salida) y el de Jev con `JEV_INPUT_USD_PER_MILLION = 0.042` y salida 0 (`settings.py`, el mismo precio de la p. 62);
- calcula el **ahorro de routing** como estimación contrafactual: los mismos tokens al precio de `savings_baseline`, menos el coste real; y el **ahorro neto** restando el coste de Jev;
- cuenta tools ejecutadas directamente y requests de OpenAI evitadas;
- guarda todo en `.ebis_cli/usage.json` y por conversación. `/stat` muestra la conversación actual y `/stats` el workspace.

### 12.8 Otras partes del proyecto (herencia de los temas 01 y 02)
- **MCP multi-servidor** (`integrations/mcp/`): `config.py` valida `mcp_config.json` (hasta `MAX_MCP_SERVERS = 10`, transportes `stdio` y `http`), `client.py` conecta con `asyncio.gather` y un fallo individual no tumba a los demás, `schemas.py` normaliza nombres (`mcp_<servidor>_<tool>`, máx. 64 caracteres, sin colisiones) y convierte resultados.
- **Subagentes como procesos** (`agent/subagent.py` y `runtime._launch_subagent`): `delegate_task` lanza `python -m ebis_cli.agent.subagent`; la tarea entra por stdin y los eventos vuelven por stdout como JSON Lines (`event`, `usage`, `jev_usage`, `decision_failure`, `result`). El subagente usa las tools locales y el Router, pero no hace Choice.
- **Tools locales** (`tools/local.py`): `list_files`, `read_file`, `write_file`, `search_files`, `make_directory`, `run_command` (tope de 120 s) y `count_words`; `local_path` impide salir del workspace y oculta `.env*` y `.ebis_cli`.
- **Persistencia** (`workspace/conversations.py`): una conversación = un JSON con eventos visibles e historial para la Responses API, guardado de forma atómica (`os.replace`).
- **Instrucciones** (`workspace/context.py`, `load_instructions`): concatena el prompt base, el `AGENTS.md` del código y el `AGENTS.md` del workspace. Por eso el `AGENTS.md` de 4 líneas de ese proyecto es parte del prompt del agente.
- **TUI** (`app/`): Textual, progreso, mensajes plegables y respuesta final en streaming.

## 13. Cómo crear tu propia skill: patrón a seguir

*(Ejemplo propio e ilustrativo, no procede del material; sirve para practicar el patrón de las pp. 16-22.)*

```text
resumen-csv/
├── SKILL.md
├── references/formato_informe.md
└── scripts/estadisticas.py
```
```markdown
---
name: resumen-csv
description: Resume un archivo CSV (filas, columnas, nulos) en un informe breve. Actívala cuando el usuario pida analizar o resumir un CSV.
---

# Resumen de CSV

1. Comprueba que el archivo existe y es CSV; si no, pregunta.
2. Ejecuta `python3 scripts/estadisticas.py <archivo>` y usa su salida como única fuente de cifras.
3. Redacta el informe siguiendo `references/formato_informe.md`. No inventes valores.
```
Fíjate en que respeta cada capa: metadatos cortos que permiten decidir la activación, cuerpo con el procedimiento, el cálculo delegado a un script (determinismo) y el formato en una referencia que solo se lee si hace falta. Un `name` que coincida con la carpeta evita el desajuste señalado más arriba.

## 14. Glosario

- **Skill:** paquete modular (`SKILL.md` + recursos opcionales) con procedimientos, reglas y utilidades que guía al agente en una tarea compleja.
- **`SKILL.md`:** archivo obligatorio con frontmatter YAML (metadatos) y cuerpo Markdown (instrucciones).
- **Frontmatter:** bloque YAML entre `---` al inicio del archivo.
- **`references/`, `scripts/`, `assets/`:** módulos opcionales de consulta, ejecución y plantillas.
- **Know-how:** experiencia de dominio y orquestación; lo que aporta la skill frente a la tool.
- **`allowed-tools`:** campo YAML opcional (experimental) citado en el material.
- **`openai.yaml`:** fichero de la skill de OpenAI que describe cómo representarla en sus apps.
- **Sandbox:** máquina virtual aislada donde el agente de ChatGPT Work ejecuta sus operaciones.
- **`defer_loading` / Tool Search:** carga diferida de esquemas de tools; solo nombre y descripción al inicio.
- **Contexto por capas:** metadatos → `SKILL.md` → recursos.
- **Token / autorregresivo:** unidad de texto; generación que añade cada token al contexto antes de calcular el siguiente.
- **Caché KV:** evita recomputar el prefijo del contexto.
- **Structured Output:** salida con schema (p. ej. JSON), que igualmente se genera token a token.
- **Decision Model:** modelo que proyecta el contexto sobre opciones cerradas y devuelve puntuaciones en una pasada.
- **Decision head:** capa `W h + b` que proyecta el vector `h` a las opciones.
- **Choice / Score / Noul (null):** elección discreta / valor continuo en [0,1] / pregunta sí-no con abstención.
- **Jev, System One, TypeSafe:** modelo de decisión y su proveedor; `client.system_one(state=..., questions=...)` es la llamada del SDK.
- **Routing:** usar una Choice para elegir qué modelo y esfuerzo de razonamiento atiende una llamada.
- **`reasoning_effort`:** nivel de razonamiento que se solicita al modelo en la request (`none`, `low`, `medium`, `high`…).
- **Allowlist:** lista cerrada de opciones permitidas; el agente solo acepta claves que estén en ella.
- **Fallback:** camino de reserva (function calling automático + modelo `default`) cuando Jev no está disponible.
- **Arquitectura híbrida:** el Decision Model enruta; el LLM generativo solo se usa cuando hace falta lenguaje abierto.
- **`python-pptx`:** biblioteca pública de Python para crear/editar PPTX; no renderiza.
- **QA determinista:** validadores en `scripts/` (overflow, integridad, aritmética, fidelidad de plantilla).

## 15. Fuentes

Todo el contenido procede de:
- `Tema 6_Decision_Models_Skills.pdf` (76 páginas, leído completo).
- Código y documentación de `ebis-cli-decision-model/`: `README.md`, `DECISION_MODEL.md`, `AGENTS.md`, `pyproject.toml`, `.env.example`, `mcp_config.json`, `mcp_config.http.json`, `routing-llm.json`, y `ebis_cli/{settings.py, prompts.py, decision_model/*, agent/{runtime,events,subagent}.py, integrations/mcp/{config,client,schemas}.py, tools/local.py, workspace/{context,conversations,usage}.py, app/main.py}`. No se leyeron en detalle `style.tcss`, `app/screens/history.py` ni `app/widgets/*` (presentación visual, no afectan a lo explicado).
- `presentacion-open/`: `SKILL.md`, `agents/openai.yaml`, `requirements.txt`, `examples/capabilities.json`, `references/*.md` (los diez), `assets/create_base_theme.py` y el arranque de `scripts/compile_deck.py` y `scripts/check_overflow.py`. El resto del código de `scripts/` (incluido `pptx_components.py` completo y los demás validadores) no se leyó línea a línea; su descripción procede de `SKILL.md` y de las referencias.

Verificaciones propias: el error de carga de `routing-llm.json` se comprobó ejecutando `LLMRouter()` con un stub de `typesafe_sdk`. Las diferencias de API (`r.choices[...]` en el PDF vs. `result.answers[...]` en el código) no se han comprobado contra el SDK real.

Partes que **no** proceden del material: las analogías y comentarios señalados como "mío", la moraleja de la sección 11, el término "divulgación progresiva" (6.3) y el ejemplo `resumen-csv` de la sección 13 (ilustrativo propio). Los cuadros de cifras (p. 74-75, 57-58) son transcripción de las slides; el material no explica por qué cambian los tokens de entrada entre ambos modos; lo dicho al respecto en la sección 11 se marca allí como suposición propia.
