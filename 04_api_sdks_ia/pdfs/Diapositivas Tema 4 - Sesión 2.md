Tema 4 · Clase 2
Prompt engineering
para automatización y
salidas estructuradas
De respuestas naturales a objetos de negocio
parseables, validables y seguros.
Máster en Ingeniería de Automatización con IA Agéntica

Clase 2
Seguimos construyendo la aplicación LLM: de invocar el modelo a controlar su salida.
|         | 1   | 2       | 3       |     | 4       | 5       |     |
| ------- | --- | ------- | ------- | --- | ------- | ------- | --- |
| Clase 1 |     | Clase 2 | Clase 3 |     | Clase 4 | Clase 5 |     |
APIs desde Python Salida estructurada Contexto FastAPI LLMOps
latencia y tokens Pydantic y tools y sesiones streaming y errores evaluación y despliegue
Hoy cambiamos la aproximación: ya sabemos llamar a un LLM; ahora necesitamos que su respuesta sea consumible por una aplicación.
| www.ebiseducation.com |     |     |     | Tema 4 · Clase 2 |     |     | 2   |
| --------------------- | --- | --- | --- | ---------------- | --- | --- | --- |

Objetivos de aprendizaje de la sesión
Al final de la clase, el alumno debe poder convertir texto libre en un objeto de negocio validado y preparado para automatización.
1 Diseñar prompts operativos 2 Distinguir formatos estructurados
Especificar tarea, reglas, formato, vocabularios y comportamiento ante incertidumbre. Entender JSON por prompt como baseline y sus límites como contrato técnico.
3 Validar con Pydantic 4 Usar tool calls como schema
Convertir output probabilístico en un objeto tipado, validado y controlado. Forzar argumentos estructurados sin entrar aún en agentes ni ejecución de herramientas.
5 Usar Structured Outputs nativos 6 Comparar enfoques
Pasar el modelo Pydantic como schema fuera del prompt mediante output_format. Elegir según robustez, portabilidad y coste de integración.
www.ebiseducation.com Tema 4 · Clase 2 3

El cambio clave: de respuesta a objeto de negocio
Una automatización necesita datos que se puedan procesar, no solo texto que un humano pueda leer.
Respuesta libre Prompt operativo Structured output Tool call + schema Workflow seguro
Define tarea, reglas y
| Útil para leer | Objeto tipado | Automatizar o escalar |     |
| -------------- | ------------- | --------------------- | --- |
vocabulario Argumentos estructurados
| Difícil de parsear | Errores controlados | a revisión humana |     |
| ------------------ | ------------------- | ----------------- | --- |
Reduce ambigüedad
Mayor control de formato, validación y comportamiento de la aplicación
Principio de ingeniería: no automatizar una salida que no puedes validar.
| www.ebiseducation.com | Tema 4 · Clase 2 |     | 4   |
| --------------------- | ---------------- | --- | --- |

BLOQUE 1
Prompting operativo
El prompt deja de ser una pregunta y se convierte en un
contrato de automatización.
EBIS Business Techschool

Una respuesta libre no es una automatización
Puede ser útil para un humano, pero frágil para un sistema que tiene que decidir o accionar.
No parseable Ambigua
free text
No hay campos estables ni tipos La prioridad y el proceso no están
This looks like a refund request. The customer is unhappy because the item arrived broken. I would definidos. normalizados.
recommend checking the order and starting the refund process.
No testable No accionable
Cada ejecución puede cambiar de No puede alimentar directamente un
forma. workflow.
Respuesta libre Salida estructurada
“It looks like a refund request…” "process_type": "refund_request"
“The customer is unhappy…” "priority": "medium"
“Order may need review…” "order_id": “XXXX"
"suggested_action": "Validate refund
“Start the refund process…”
eligibility"
www.ebiseducation.com Tema 4 · Clase 2 6

En automatización, el prompt es un contrato
Debe describir qué se espera, qué valores están permitidos y qué hacer cuando hay incertidumbre.
|     | Rol | Tarea |     | Datos |     |
| --- | --- | ----- | --- | ----- | --- |
|     | 1   | 2     |     | 3     |     |
Qué perspectiva adopta el modelo Qué debe resolver exactamente Dónde empieza y termina el input
|     | 4 Reglas | 5 Formato |     | 6 Fallback |     |
| --- | -------- | --------- | --- | ---------- | --- |
Criterios de negocio y seguridad Cómo debe devolver el resultado Qué hacer si falta información
La diferencia entre “preguntar” y “automatizar” es la existencia de un contrato verificable.
| www.ebiseducation.com |     |     | Tema 4 · Clase 2 |     | 7   |
| --------------------- | --- | --- | ---------------- | --- | --- |

Mismo caso, dos prompts muy diferentes
La calidad del output cambia radicalmente cuando el prompt define contrato y vocabulario.
| Prompt débil |     |     | Prompt operativo |     |     |
| ------------ | --- | --- | ---------------- | --- | --- |
You are a customer service automation assistant.
Analyze this customer request and tell me what to do.
Classify the request using the allowed process types.
Extract the order ID only if it is explicitly present.
Do not invent missing information.
Set requires_human_review to true when the request
is ambiguous, incomplete or high-risk.
|                       | Dimensión       | Prompt débil  |                  | Prompt operativo          |     |
| --------------------- | --------------- | ------------- | ---------------- | ------------------------- | --- |
|                       | Tarea           | Abierta       |                  | Clasificar y extraer      |     |
|                       | Categorías      | No definidas  |                  | Vocabulario controlado    |     |
|                       | Campos          | Implícitos    |                  | Reglas explícitas         |     |
|                       | Datos ausentes  | Puede inferir |                  | Usa null                  |     |
|                       | Incertidumbre   | No gestionada |                  | Revisión humana           |     |
|                       | Formato técnico | No controlado |                  | Schema separado en la API |     |
| www.ebiseducation.com |                 |               | Tema 4 · Clase 2 |                           | 8   |

Anatomía de un prompt operativo
La plantilla debe separar instrucciones, datos y salida esperada.
template Role
Alinea tono y responsabilidad del modelo.
Task
ROLE
You are a customer service automation assistant.
Reduce ambigüedad: clasificar, extraer, normalizar.
TASK
Classify the request and extract the information
required by the customer service workflow.
Input
INPUT
Delimita los datos para evitar mezclar instrucciones y texto.
<request>
{customer_request}
</request>
RULES Rules
- Do not invent missing values
- Use null when information is absent Fija criterios de negocio, seguridad e incertidumbre.
- Set requires_human_review=true when ambiguous
- Keep suggested_action short and operational
Schema — fuera del prompt
Pydantic define campos, tipos, enums y restricciones mediante output_format.
No duplicamos el schema en el prompt: el prompt explica el negocio y la API
controla la estructura.
www.ebiseducation.com Tema 4 · Clase 2 9

Los vocabularios controlados reducen ambigüedad
El modelo puede seguir siendo probabilístico, pero el dominio de salida no tiene por qué ser libre.
|     | Texto del usuario | Valor normalizado |     |     | Acción del sistema |     |
| --- | ----------------- | ----------------- | --- | --- | ------------------ | --- |
“I want my money back” refund_request Abrir flujo de reembolso
“The item arrived broken” refund_request Solicitar validación de pedido
“Change my delivery
|     |     | delivery_change |     |     | Enviar a logística |     |
| --- | --- | --------------- | --- | --- | ------------------ | --- |
address”
“I was charged twice” billing_issue Priorizar revisión de facturación
“I cannot access my
|     |     | technical_support |     |     | Abrir ticket técnico |     |
| --- | --- | ----------------- | --- | --- | -------------------- | --- |
account”
|     | Regla práctica | Riesgo |     | Diseño |     |     |
| --- | -------------- | ------ | --- | ------ | --- | --- |
Cuanto más cerrado sea el vocabulario, más fácil será  Si el catálogo no cubre casos reales, el modelo forzará  Incluir “other” y revisión humana para gestionar
validar y automatizar. clasificaciones incorrectas. incertidumbre.
Un LLM interpreta lenguaje flexible.
El sistema consume etiquetas
estables.
| www.ebiseducation.com |     |     | Tema 4 · Clase 2 |     |     | 10  |
| --------------------- | --- | --- | ---------------- | --- | --- | --- |

BLOQUE 2
Salidas estructuradas
JSON ayuda, pero la aplicación debe validar y controlar el
contrato.
EBIS Business Techschool

El output objetivo: un objeto de negocio
La respuesta deja de ser un texto y pasa a ser una entidad que puede alimentar un flujo.
|     | JSON object |     | process_type        | priority       |     |
| --- | ----------- | --- | ------------------- | -------------- | --- |
|     |             |     | Selecciona workflow | Ordena trabajo |     |
{
|   "process_type": "refund_request", |     |     | order_id | reason |     |
| ----------------------------------- | --- | --- | -------- | ------ | --- |
  "priority": "medium",
|     |     |     | Permite consultar sistema | Normaliza causa |     |
| --- | --- | --- | ------------------------- | --------------- | --- |
  "order_id": "8921",
  "reason": "damaged_item",
  "requires_human_review": true,
  "suggested_action": "Validate refund eligibility"
}
|     |     |     | review             | action         |     |
| --- | --- | --- | ------------------ | -------------- | --- |
|     |     |     | Controla seguridad | Siguiente paso |     |
Objetivo: transformar input no estructurado en una pieza de software con campos esperados.
| www.ebiseducation.com |     | Tema 4 · Clase 2 |     |     | 12  |
| --------------------- | --- | ---------------- | --- | --- | --- |

Una estructura válida no significa una decisión correcta
Hay varios niveles de control y cada uno resuelve un problema diferente.
|     | Nivel |     | Pregunta |     | Control |     |
| --- | ----- | --- | -------- | --- | ------- | --- |
Formato ¿La respuesta tiene la estructura esperada? Structured Output de la API
|     | Schema | ¿Los campos, tipos y valores son válidos? |     |     | Pydantic |     |
| --- | ------ | ----------------------------------------- | --- | --- | -------- | --- |
Semántica ¿La clasificación y extracción son correctas? Dataset de evaluación y métricas
Negocio ¿Es seguro ejecutar la acción? Reglas, umbrales y revisión humana
Una estructura válida puede fallar semánticamente; por eso combinamos schema, evaluación y reglas de negocio.
| www.ebiseducation.com |     |     |     | Tema 4 · Clase 2 |     | 13  |
| --------------------- | --- | --- | --- | ---------------- | --- | --- |

Tres niveles para obtener salidas estructuradas
El nivel 1 explica el problema; la práctica se centra en Structured Outputs y tool calls.
1 Nivel 1 — Prompt JSON 2 Nivel 2 — Structured Output nativo 3 Nivel 3 — Tool call
El modelo sigue una instrucción textual, pero la API El schema se pasa como configuración técnica de la El contrato se define como argumentos de una
no garantiza la estructura. API, separado del prompt. herramienta. Claude devuelve un bloque tool_use con
un objeto estructurado.
Ventaja: simple y portable. Ventaja: mayor control del formato.
Riesgo: texto extra, markdown, campos incorrectos o Riesgo: estructura válida no garantiza decisión Ventaja: prepara flujos con herramientas.
JSON inválido. correcta. Riesgo: más complejidad e integración.
Uso: prototipos y bajo riesgo; siempre con validación Uso: extracción, clasificación y normalización de Uso: cuando el output representa una operación
posterior. objetos de negocio. ejecutable.
Structured Output devuelve un objeto; tool call solicita una operación con argumentos.
www.ebiseducation.com Tema 4 · Clase 2 14

Nivel 1 — Prompt-only JSON
El enfoque más simple: pedir formato estructurado directamente en el prompt.
prompt
Ventaja
Muy simple y portable entre proveedores.
Analyze the customer request and return only valid JSON.
JSON schema:
Riesgo
{
"process_type": "...",
Puede devolver texto extra, markdown o campos inválidos.
"priority": "...",
"order_id": "... or null",
"requires_human_review": true/false
}
Uso recomendado
Rules:
- Return only JSON
Prototipos y casos de bajo riesgo; siempre con validación posterior.
- Do not include markdown
- Use null for missing fields
www.ebiseducation.com Tema 4 · Clase 2 15

Errores típicos de salida estructurada
El modelo puede cumplir la intención, pero romper el contrato que necesita el software.
|     | Error         | Qué significa       |     | Ejemplo            |     |
| --- | ------------- | ------------------- | --- | ------------------ | --- |
|     | JSON inválido | No se puede parsear |     | Texto antes del {} |     |
Falta campo obligatorio El contrato está incompleto No viene priority
Valor no permitido Rompe vocabulario cerrado priority = urgent
Dato inventado El modelo alucina un campo order_id no presente
Salida demasiado larga No es operativa Explicación dentro del JSON
La salida inválida no es un fallo menor: es una señal para no automatizar sin control.
| www.ebiseducation.com |     |     | Tema 4 · Clase 2 |     | 16  |
| --------------------- | --- | --- | ---------------- | --- | --- |

EBI Business
Techschool
Caso 1 — Prompt + JSON + Pydantic
S
El contrato no termina en el prompt: termina cuando la aplicación valida el objeto.
Prompt con  LLM response json.loads() TicketAnalysis Business object
|     |     | →   | →   |     | →   | →   |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
schema
|     | Qué hace Pydantic |     | Qué no hace Pydantic |     |     | Validación |     |
| --- | ----------------- | --- | -------------------- | --- | --- | ---------- | --- |
Valida campos, tipos, enums, opcionales y  No garantiza que la clasificación sea  Pydantic valida después de recibir la
|                       | restricciones. |     | correcta. |                  |     | respuesta. |     |
| --------------------- | -------------- | --- | --------- | ---------------- | --- | ---------- | --- |
| www.ebiseducation.com |                |     |           | Tema 4 · Clase 2 |     |            | 17  |

Nivel 2 — Structured Output nativo
El schema se pasa como configuración técnica de la API, separado del prompt.
Prompt de negocio Modelo Pydantic client.messages.parse() parsed_output Business object
Schema:
Tarea, input y reglas Schema fuera del prompt Instancia validada Listo para workflow
TicketAnalysis
El schema no se escribe en el prompt: se proporciona como configuración técnica de la llamada.
www.ebiseducation.com Tema 4 · Clase 2 18

Schema: tipos, enums y campos opcionales
Definimos el contrato de salida una vez y lo reutilizamos en Structured Outputs y tool calls.
schemas.py
Qué aporta
Un contrato único para prompt, API, validación y CSV final.
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
class ProcessType(str, Enum):
Qué validamos
refund_request = "refund_request"
delivery_change = "delivery_change"
delivery_delay = "delivery_delay" Tipos, campos requeridos, enums, opcionales y restricciones.
technical_support = "technical_support"
billing_issue = "billing_issue"
product_question = "product_question"
account_management = "account_management"
other = "other"
Qué no validamos aún
class Priority(str, Enum):
low = "low" Que la clasificación sea correcta; eso requiere evaluación.
medium = "medium"
high = "high"
class TicketAnalysis(BaseModel):
process_type: ProcessType
priority: Priority
order_id: Optional[str] = None
reason: Optional[str] = None
requires_human_review: bool
suggested_action: str = Field(min_length=3, max_length=180)
www.ebiseducation.com Tema 4 · Clase 2 19

Prompt operativo sin duplicar el schema
El prompt describe la tarea; el contrato técnico va por output_format.
prompts.py
Diseño
El prompt explica negocio, reglas y tratamiento de
incertidumbre.
def build_business_prompt (customer_request: str, config: dict) -> str:
return f"""
Separación
You are a customer service automation assistant.
Task: El schema no viaja como texto: se pasa en output_format.
Analyze the customer request and convert it into
an operational workflow object.
Customer request:
<request> Regla clave
{customer_request}
</request> No inventar datos; usar null y revisión humana cuando haga
falta.
Business rules:
- Do not invent missing information.
- Use null when a value is not explicitly present.
- Set requires_human_review to true when the request
is ambiguous, incomplete or high-risk.
- Keep suggested_action short and operational.
""".strip()
www.ebiseducation.com Tema 4 · Clase 2 20

Structured Output: parsear y validar en una llamada
La API guía la forma de la respuesta y el SDK devuelve un objeto Pydantic.
structured_extract_2.py
Qué cambia
try:
No hacemos json.loads(): el SDK entrega parsed_output.
response = client.messages.parse(
model=model,
max_tokens=config["llm"]["max_tokens"],
temperature=config["llm"]["temperature"],
messages=[{"role": "user", "content": prompt}],
output_format=TicketAnalysis, Objeto final
)
analysis ya es una instancia de TicketAnalysis.
analysis = response.parsed_output
status = "valid"
error = ""
except (ValidationError, ValueError) as e:
analysis = None Límite
status = "error"
error = str(e)
Objeto válido no implica decisión correcta de negocio.
www.ebiseducation.com Tema 4 · Clase 2 21

Respuesta segura ante errores
La robustez no consiste en ocultar errores, sino en tener una salida segura cuando ocurren.
1. Petición 2. Generación 3. Validación 4. Si falla 5. Si persiste
| Prompt operativo + schema        |                              |                        |                  | Human review |     |
| -------------------------------- | ---------------------------- | ---------------------- | ---------------- | ------------ | --- |
|                                  | Structured Output o tool_use | Pydantic + reglas      | Retry / reformat |              |     |
| Pedir salida estructurada según  | json.loads() o recepción de  |                        |                  |              |     |
|                                  |                              | TicketAnalysis(**data) | Retry / reformat | Human review |     |
| contrato                         | objeto                       |                        |                  |              |     |
Automatización responsable: ante incertidumbre, escalar. No inventar ni forzar una acción.
| www.ebiseducation.com |     | Tema 4 · Clase 2 |     |     | 22  |
| --------------------- | --- | ---------------- | --- | --- | --- |

BLOQUE 3
Tool calls como schema
No hacemos agentes: usamos la tool definition como
mecanismo de salida estructurada.
EBIS Business Techschool

Tool calls no significa necesariamente agentes
En esta clase usamos tools solo para obtener argumentos estructurados, sin ejecutar acciones externas.
Uso en esta clase Uso en agentes
Una llamada puntual Loop multi-paso
Extraer argumentos estructurados Decidir acciones y herramientas
No ejecutamos efectos externos Puede ejecutar APIs o procesos
Se valida con Pydantic Se observa y controla el ciclo
Tool calls como salida estructurada. Los agentes, tools con efectos y loops se verán más adelante.
www.ebiseducation.com Tema 4 · Clase 2 24

Tool schema: el contrato se mueve a la API
La herramienta define nombre, descripción y un input_schema con los campos esperados.
tool_schema.py
Qué cambia
El schema se declara como input_schema de una herramienta,
no como respuesta directa.
TICKET_ANALYSIS_TOOL = {
"name": "extract_ticket_analysis",
"description": "Extract structured information from a customer request.",
"input_schema": {
Qué controla
"type": "object",
"properties": {
Nombre de la tool, campos, tipos, enums, requeridos y
"process_type": {
descripciones.
"type": "string",
"enum": [item.value for item in ProcessType]
},
"priority": {
"type": "string", Qué sigue faltando
"enum": [item.value for item in Priority]
},
Validación de aplicación, reglas de negocio y revisión humana.
"order_id": {"type": ["string", "null"]},
"reason": {"type": ["string", "null"]},
"requires_human_review": {"type": "boolean"},
"suggested_action": {"type": "string"}
},
"required": ["process_type", "priority", "order_id", "reason",
"requires_human_review", "suggested_action"]
}
}
www.ebiseducation.com Tema 4 · Clase 2 25

Forzar el tool call en una llamada
El modelo devuelve un bloque tool_use en lugar de una respuesta narrativa.
tool_extract.py
tool_choice
Fuerza una herramienta concreta para ese request.
response = client.messages.create(
model=model,
max_tokens=config["llm"]["max_tokens"],
temperature=0.0, temperature=0.0
tools=[TICKET_ANALYSIS_TOOL],
tool_choice={
"type": "tool", Reducimos variación en tareas de extracción y clasificación.
"name": "extract_ticket_analysis",
},
messages=[{"role": "user", "content": prompt}],
)
Aun así
Aunque haya tool_use, seguimos validando con Pydantic.
www.ebiseducation.com Tema 4 · Clase 2 26

Extraer el bloque tool_use y validarlo
La tool call devuelve argumentos estructurados; la aplicación los valida igual que antes.
TODOs solución
tool_input = None
for block in response.content:
if block.type == "tool_use" and block.name == "extract_ticket_analysis":
tool_input = block.input
analysis = TicketAnalysis(**tool_input)
break
status = "valid"
if tool_input is None:
raise ValueError("No tool_use block returned")
analysis = TicketAnalysis(**tool_input)
Best practice: si no hay tool_use, no fuerces una acción. Registra error y escala.
www.ebiseducation.com Tema 4 · Clase 2 27

Structured Output vs Tool call
La diferencia no es el schema: es si el modelo devuelve un objeto o solicita una operación.
|     | Criterio | Structured Output + Pydantic |     |     | Tool call + Pydantic          |     |     |
| --- | -------- | ---------------------------- | --- | --- | ----------------------------- | --- | --- |
|     | Salida   | Objeto final del modelo      |     |     | Argumentos de una herramienta |     |     |
Uso típico Extraer, clasificar, normalizar Preparar una acción o integración
|                       | Complejidad        |                 | Media-baja |                  |                          | Media-alta |     |
| --------------------- | ------------------ | --------------- | ---------- | ---------------- | ------------------------ | ---------- | --- |
|                       | Control de formato |                 | Alto       |                  |                          | Alto       |     |
|                       | Mensaje clave      | Objeto validado |            |                  | Operación con argumentos |            |     |
| www.ebiseducation.com |                    |                 |            | Tema 4 · Clase 2 |                          |            | 28  |

BLOQUE 4
Práctica guiada
Construimos dos pipelines de extracción y comparamos el
resultado.
EBIS Business Techschool

Carpeta de práctica de la Clase 2
Reutilizamos el cliente de la Clase 1 y añadimos schemas, prompts y dos mecanismos estructurados.
project
Reutilizamos de Clase 1
Cliente Anthropic, .env, config.yml y CSV de solicitudes.
class_02_structured_outputs/
│
├── .env
├── llm_client.py
├── schemas.py Nuevo en Clase 2
├── prompts.py
├── structured_extract.py # baseline JSON prompt
├── structured_extract_2.py # Structured Output schemas.py, prompts.py y structured_extract_2.py con messages.parse().
├── tool_schema.py
├── tool_extract.py
│
├── data/
│ └── customer_requests_structured.csv
│
└── outputs/ Extra avanzado
├── prompt_json_results.csv
├── structured_output_results.csv
└── tool_call_results.csv tool_schema.py y tool_extract.py para extracción mediante tool_use.
www.ebiseducation.com Tema 4 · Clase 2 30

Práctica A — Structured Output nativo + Pydantic
El alumno completa el schema y genera un CSV de objetos estructurados.
1. Completar Priority enum 2. Añadir campos opcionales
schemas.py order_id y reason
3. Definir reglas del prompt 4. Llamar a client.messages.parse
prompts.py structured_extract_2.py
5. Leer response.parsed_output 6. Guardar structured_output_results.csv
TicketAnalysis outputs/
Objetivo: obtener objetos válidos sin duplicar el schema en el prompt y registrar errores controlados.
www.ebiseducation.com Tema 4 · Clase 2 31

Práctica B — Tool call como extracción estructurada
El alumno compara el objeto directo de Structured Outputs con los argumentos devueltos por tool_use.
TODOs Resultado esperado
# TODOs in tool_extract.py
tool_call_results.csv con los mismos campos de negocio que Structured
tool_input = None
Outputs.
for block in response.content:
# identify the tool_use block
# extract block.input
pass
Comparativa
if tool_input is None:
raise ValueError("No tool_use block") ¿Cambia la latencia, los tokens o la estabilidad del formato?
analysis = TicketAnalysis(**tool_input)
Mensaje clave
No es un agente: no ejecutamos nada. Solo capturamos argumentos estructurados.
www.ebiseducation.com Tema 4 · Clase 2 32

Qué tiene que aparecer al final
El resultado debe ser un CSV con objetos estructurados y trazabilidad básica.
|     | request_id | status | process_type    | priority | review | latency_ms |     |
| --- | ---------- | ------ | --------------- | -------- | ------ | ---------- | --- |
|     | REQ-001    | valid  | refund_request  | medium   | true   | 1240       |     |
|     | REQ-002    | valid  | delivery_change | medium   | false  | 1185       |     |
|     | REQ-001    | valid  | refund_request  | medium   | true   | 1310       |     |
|     | REQ-002    | valid  | delivery_change | medium   | false  | 1265       |     |
Comparad método, validez, campos críticos, latencia y tokens antes de automatizar.
| www.ebiseducation.com |     |     |     | Tema 4 · Clase 2 |     |     | 33  |
| --------------------- | --- | --- | --- | ---------------- | --- | --- | --- |

Mini-quiz de cierre
1. ¿Por qué no basta un output en texto libre? 2. ¿Qué garantiza Pydantic y qué no?
3. ¿Qué cambia al usar Structured Outputs? 4. ¿Cuándo usarías un tool call?
5. ¿Por qué validar tras recibir tool_use?
| www.ebiseducation.com | Tema 4 · Clase 2 | 34  |
| --------------------- | ---------------- | --- |

To sum up
convertir una respuesta LLM en un contrato de software validado.
El baseline es útil para entender el problema, pero no es un contrato
1 1. Prompting operativo ≠ prompt bonito 2
robusto.
La clave es diseñar un contrato que otro sistema pueda consumir. El output debe parsearse y validarse contra un schema explícito.
Tipos, enums y restricciones convierten la salida en objeto de Structured Outputs devuelven objetos; tool calls preparan
3 4
aplicación. operaciones.
La aplicación puede trabajar con tipos, enums y campos obligatorios. No son solo para agentes; también sirven como mecanismo de salida estructurada.
prompt, schema y validación deben trabajar juntos antes de automatizar.
www.ebiseducation.com Tema 4 · Clase 2 35

de salida controlada a conversación con estado
La siguiente sesión añadirá contexto multi-turn sin entrar todavía en RAG.
|     | Clase 1          | Clase 2             |     | Clase 3            |     |
| --- | ---------------- | ------------------- | --- | ------------------ | --- |
|     | Modelo invocable | Output estructurado |     | Contexto, sesiones |     |
|     | y medible        | y validado          |     | y estado           |     |
Primero hacemos que la salida sea segura. Después haremos que el sistema recuerde y mantenga estado.
| www.ebiseducation.com |     |     | Tema 4 · Clase 2 |     | 36  |
| --------------------- | --- | --- | ---------------- | --- | --- |

Referencias y documentación
Fuentes recomendadas para ampliar la parte técnica.
Pydantic documentation Nota técnica
Structured Output devuelve un objeto; tool call devuelve argumentos de una
Schemas, BaseModel, enums and validation errors.
herramienta.
Structured Outputs, messages.parse(), tool use, input_schema and tool_choice. Próximo paso
Tool use, input_schema, tool_choice and tool_use blocks. Conectar salida validada con contexto y memoria de sesión.
www.ebiseducation.com Tema 4 · Clase 2 37
