Tema 4 · Clase 1
Integración de modelos
generativos vía API desde
Python
LLM-as-a-Service: del prompt manual al componente software
medible
Máster en Ingeniería de Automatización con IA Agéntica
www.ebiseducation.com

Clase 1 dentro del Tema 4
Hoy construimos la base técnica: invocar un modelo, medirlo y encapsularlo para automatización.
| 1        | 2                   | 3          | 4           | 5            |
| -------- | ------------------- | ---------- | ----------- | ------------ |
| APIs LLM | Salida estructurada | Contexto   | FastAPI     | LLMOps       |
| Python   |                     | + sesiones | + streaming | + despliegue |
Resultado de hoy
|     |     | No entraremos aún |     | Tip |
| --- | --- | ----------------- | --- | --- |
Un cliente Python simple para llamar a un
RAG, agentes, herramientas, bases  Entender el patrón antes de añadir
LLM, medir latencia y comparar
vectoriales, despliegue cloud o MCP. complejidad.
configuraciones.
2
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Objetivos de aprendizaje de la sesión
Al terminar, el alumno debe poder explicar y programar una llamada LLM básica con criterio operativo.
Entender LLM-as-a-Service Construir una request
01 02
Modelo externo invocado por API, con límites, coste y latencia. API key, modelo, mensajes, parámetros y respuesta.
Medir una llamada Diseñar una primera automatización
03 04
Latencia, longitud de entrada/salida y coste estimado. Usar el modelo para resumir, clasificar o extraer información
simple.
Caso práctico llm_client.py · benchmark.py · main.py · config.yml · .env · results.csv
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 3

El cambio clave: de chatbot a componente software
En producción, el LLM no “conversa”: presta una capacidad dentro de un sistema controlado.
Automatización
Uso manual Uso productivo
El output alimenta un
• Usuario escribe un prompt • Aplicación construye la request
proceso posterior:
Respuesta no necesariamente Modelo responde bajo requisitos
clasificación,
estructurada Se validan resultados
extracción, respuesta,
Sin métricas ni trazabilidad Se registran coste, latencia y errores
alerta o revisión
Difícil de repetir Existe fallback
humana.
To sum up
Un sistema LLM debe diseñarse como una pieza de ingeniería: configurable, observable,
repetible y mantenible.
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 5

BLOQUE 1
1. Modelo generativo como
servicio
Arquitectura, responsabilidades y trade-offs antes de escribir código.
www.ebiseducation.com

Patrón base de una aplicación con LLM-as-a-Service
La aplicación conserva el control: el proveedor aporta inferencia, no gobierno del proceso.
Cliente / Frontend Backend propio Proceso
LLM Provider
Formulario, app web, script Reglas, prompts, validación, Ticket, workflow, email, ERP,
Inferencia mediante API
o Postman logs revisión
Observabilidad Contrato
latencia · coste · errores parámetros · formato · límites
Decisión de diseño
No enviamos “todo” al modelo: enviamos lo necesario, con parámetros controlados y salida procesable.
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 7

Proveedor, modelo y aplicación no son lo mismo
Separar estos conceptos evita decisiones incorrectas de arquitectura y coste.
Modelo
Proveedor Aplicación
• Capacidad concreta seleccionada en la
• Empresa/plataforma que expone la API • Tu sistema de negocio
request
• Gestiona infraestructura y seguridad • Construye prompts, valida salidas y
• Tiene trade-off de calidad, coste y
del servicio registra métricas
latencia
• Define autenticación, límites y • Decide cuándo usar modelo y qué
• Puede cambiar de versión con impacto
facturación hacer con la respuesta
funcional
Regla práctica Diseña tu código para poder cambiar de modelo sin reescribir toda la aplicación.
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 8

Elegir modelo es una decisión de producto y operación
No hay un “mejor modelo” universal: hay un mejor ajuste para cada tarea y restricción.
|     | Calidad |     | Latencia | Coste |
| --- | ------- | --- | -------- | ----- |
razonamiento, lenguaje, código tiempo hasta primera respuesta y total precio por input/output token
|     | Contexto | Multimodalidad |     | Gobierno |
| --- | -------- | -------------- | --- | -------- |
volumen máximo de información útil texto, imagen, audio, documentos región, privacidad, compliance
|                     | Caso | Prioridad dominante |     | Modelo típico   |
| ------------------- | ---- | ------------------- | --- | --------------- |
| Chat interno simple |      | Coste / latencia    |     | rápido y barato |
Análisis legal largo Contexto / precisión modelo avanzado con contexto largo
Clasificación masiva Coste / estabilidad modelo pequeño + validación
9
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

BLOQUE 2
2. Anatomía de una llamada LLM
Qué enviamos, qué recibimos y qué debemos medir.
www.ebiseducation.com

Una llamada LLM tiene más partes que un prompt
La request combina credenciales, modelo, mensajes, parámetros y restricciones.
| API key | Model | Messages |
| ------- | ----- | -------- |
identidad y permisos capacidad elegida system / user / assistant
| Parameters | Constraints | Response |
| ---------- | ----------- | -------- |
temperature, max tokens timeout, safety, format texto, metadatos, usage
La calidad depende tanto del modelo como de la request.
En automatización, los parámetros y el formato de salida son parte del diseño, no un detalle técnico.
11
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Los mensajes separan instrucciones, usuario e
historial
Esta estructura será crítica en las siguientes clases para contexto, seguridad y salida estructurada.
Rol Responsabilidad Ejemplo
system Comportamiento global y reglas permanentes “You are a process automation assistant…”
user Petición o dato enviado por el usuario/aplicación “Clasifica este ticket…”
assistant Respuestas previas si hay conversación “Necesito el número de pedido.”
tool/function Resultados externos, si el proveedor lo soporta “order_status=delivered”
Clase 1 Hoy usamos un patrón mínimo. En Clase 3 profundizaremos en historial, contexto y sesiones.
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 12

Los parámetros convierten el modelo en un
componente controlable
Para automatización buscamos estabilidad, límite de salida y comportamiento predecible.
Parámetro Qué controla Recomendación inicial
model Capacidad, precio y latencia empezar con uno equilibrado; escalar si falla
temperature Variabilidad de la generación 0.0–0.3 para extracción/clasificación
max_tokens Tamaño máximo de salida limitar para controlar coste y latencia
top_p / top_k Muestreo alternativo no tocar al inicio salvo razón clara
timeout Tiempo máximo de espera siempre definido en aplicaciones
stream Entrega incremental de tokens útil para UX; no siempre para salidas estructuradas
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 13

Temperatura: creatividad vs consistencia
Una configuración “creativa” puede ser mala para automatizar procesos repetibles.
| 0.0            | 0.3       | 0.7          | 1.0      |
| -------------- | --------- | ------------ | -------- |
| “determinista” | operativo | exploratorio | creativo |
Para clasificación / extracción Para ideación / redacción
• temperature baja • temperature media
• max_tokens limitado • más libertad de salida
• validación posterior • revisión humana esperable
14
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Tokens, coste y latencia son variables de diseño
Cada llamada tiene un coste aproximado: input + output + overhead del proveedor.
Fórmula mental de coste
≈
|     |     | Prompt | Modelo |     | Output |
| --- | --- | ------ | ------ | --- | ------ |
input_tokens × precio_input
|     | instrucciones + datos |     | inferencia |     | tokens generados |
| --- | --------------------- | --- | ---------- | --- | ---------------- |
+
output_tokens × precio_output
| Sube el coste cuando… | Baja el coste cuando… |     |     | Regla práctica |     |
| --------------------- | --------------------- | --- | --- | -------------- | --- |
• añades más contexto • resumes inputs • mide antes de optimizar
• pides respuestas largas • limitas max_tokens • compara por tarea
• repites llamadas en batch • usas modelos pequeños/eficientes • no optimices a ciegas
15
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

La latencia tiene varios causantes
Medir solo el tiempo total oculta dónde está el problema.
| Network | Queue | Context | Generation | Validation |
| ------- | ----- | ------- | ---------- | ---------- |
ida/vuelta API carga proveedor tokens de entrada tokens de salida postproceso propio
| Tiempo hasta primera respuesta |     |     | Tiempo total de tarea |     |
| ------------------------------ | --- | --- | --------------------- | --- |
Importante para experiencia de usuario; mejora con streaming. Importante para automatización batch y procesos síncronos.
16
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Errores frecuentes al integrar LLMs por API
Los fallos esperables deben formar parte del diseño desde el día uno.
| 401 / Auth | 429 / Rate limit | Timeout |
| ---------- | ---------------- | ------- |
clave incorrecta o sin permisos demasiadas peticiones el modelo no responde a tiempo
| Context length | Invalid output | Safety refusal |
| -------------- | -------------- | -------------- |
input demasiado largo formato no procesable respuesta bloqueada o parcial
Principio operativo
Toda llamada externa necesita timeout, gestión de errores y logging mínimo.
17
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Patrón mínimo de resiliencia para una llamada LLM
No buscamos perfección: buscamos fallar de forma controlada y observable.
| Timeout | Retry + backoff | Fallback |
| ------- | --------------- | -------- |
| 1       | 2               | 3        |
Evita que el proceso quede  Reintenta fallos transitorios sin  Cambia a modelo alternativo o
| bloqueado.                | saturar.                       | ruta manual. |
| ------------------------- | ------------------------------ | ------------ |
| Log                       | Validation                     |              |
| 4                         | 5                              |              |
| Registra input resumido,  | Comprueba que la salida sirve  |              |
| modelo, latencia, error.  | para el proceso.               |              |
Clase 2 La validación de salida estructurada se trabajará en profundidad con JSON/Pydantic.
18
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

BLOQUE 3
3. Demo y práctica guiada
Construimos un cliente Python medible para automatizar tareas simples.
www.ebiseducation.com

Demo: de cero a primera llamada medible
| Configurar   | Crear      | Enviar        | Medir          | Guardar     |
| ------------ | ---------- | ------------- | -------------- | ----------- |
| 1            | 2          | 3             | 4              | 5           |
| entorno      | cliente    | prompt        | latencia       | resultado   |
| .env +       | función    | resumen /     | perf_counter() | CSV o JSONL |
| requirements | call_llm() | clasificación |                |             |
Resultado esperado
No solo se “obtiene una respuesta”; se obtiene una respuesta con metadatos mínimos para decidir si el modelo es usable.
20
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Código base: cliente LLM con medición de latencia
La función encapsula la llamada y devuelve una estructura que podremos evaluar más adelante.
llm_client.py
def call_llm(
from dataclasses import dataclass client,
from time import perf_counter prompt: str,
model: str,
temperature: float = 0.2,
@dataclass max_tokens: int = 500
class LLMResult: ) -> LLMResult:
text: str start = perf_counter()
model: str
latency_ms: int response = client.messages.create(
input_tokens: int model=model,
output_tokens: int max_tokens=max_tokens,
input_chars: int temperature=temperature,
output_chars: int messages=[
# TODO 1: add the user message with the prompt
],
)
# TODO 2: extract the text from the response
text = ...
latency_ms = int((perf_counter() - start) * 1000)
return LLMResult(
text=text,
model=model,
latency_ms=latency_ms,
input_tokens=..., # TODO 3: read input tokens from response usage
output_tokens=..., # TODO 4: read output tokens from response usage
input_chars=len(prompt),
output_chars=len(text),
)
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 21

Configuración: las claves nunca van en el código
Separar configuración de lógica permite seguridad, cambios de modelo y despliegues más limpios.
.env.example main.py
# .env.example # main.py
from llm_client import call_llm
LLM_API_KEY=replace_with_your_api_key
LLM_MODEL=claude-haiku-4-5-20251001 prompt = "Summarize the following customer request..."
LLM_TIMEOUT_SECONDS=30 result = call_llm(client, prompt, model="selected-model")
print(result.text)
print(result.latency_ms)
Buenas prácticas Riesgos
Objetivo
• usar variables de entorno • API key expuesta
• cambiar proveedor sin tocar lógica
• no subir .env al repositorio • coste no controlado
• facilitar despliegue posterior
• crear .env.example • difícil rotación de claves
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 22

Caso práctico: AI Request Triage
Usaremos solicitudes de cliente para practicar resumen, clasificación y extracción simple.
Output inicial
Input
LLM call
• Resumen
Texto libre escrito por un cliente o usuario
Tipo de solicitud
interno. Prompt + modelo +
Entidades simples
parámetros
Acción sugerida
Ejemplo:
“El cliente quiere cancelar el pedido 8921 temperature=0.2
porque llegó roto y solicita reembolso max_tokens=250
En Clase 2 lo convertiremos
urgente.”
en JSON validado.
Foco Medir y comparar llamadas; todavía no exigimos salida perfectamente estructurada.
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 23

Ejercicio de la clase: tres entregables incrementales
El alumno empieza con una llamada aislada y termina con una comparación simple de configuraciones.
|     | Primera llamada |     | Batch de solicitudes |     | Comparación |
| --- | --------------- | --- | -------------------- | --- | ----------- |
| A   |                 | B   |                      | C   |             |
Implementa call_llm() y ejecuta un  Ejecuta el modelo sobre una lista  Compara dos temperaturas o dos
prompt de resumen. de tickets y guarda resultados. modelos: salida, latencia y coste
aproximado.
|     | Métrica    | Cómo medirla hoy |     |                              | Para qué sirve |
| --- | ---------- | ---------------- | --- | ---------------------------- | -------------- |
|     | latency_ms | perf_counter()   |     | comparar experiencia y batch |                |
input/output length caracteres o tokens estimados aproximar coste
output usefulness revisión manual rápida preparar evaluación futura
24
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Dataset: solicitudes cortas de cliente
ID Canal Tarea Solicitud del cliente Categoría esperada Prioridad
REQ-001 email classify The customer wants to cancel order 8921 because the item arrived broken. refund_or_cancellation medium
REQ-002 chat classify I need to change the delivery address for order 5520 before it ships. delivery_change medium
REQ-003 email classify The user reports that they have not been able to access the platform since yesterday. technical_support medium
Please summarize this complaint: the invoice amount is wrong and the client has already contacted
REQ-004 form summarize billing_issue high
support twice.
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 25

Estructura recomendada del repositorio de la clase
Una organización simple facilita mantener el proyecto durante las cinco sesiones.
Project structure
Por qué así
llm_api_demo/
│
• separa datos, lógica y resultados
├── .env
├── config.yml • prepara las siguientes clases
├── llm_client.py
• evita notebooks desordenados
├── main.py
├── benchmark.py
│
├── data/
│ └──
customer_requests_demo.csv
Salida de la práctica
│
└── outputs/
• results.csv con respuesta y latencia
└── benchmark_results.csv
• comparación manual de configuraciones
• cliente reutilizable
Siguiente evolución
• prompt templates y JSON validado en Clase 2
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 26

Código de benchmark simple
for _, row in df.iterrows():
prompt = f"""
{config["prompt"]["role"]}
Task:
No hace falta un framework complejo para empezar a operar con criterio.
{row["task"]}
Customer request:
{row["customer_request"]}
benchmark.py
Instructions:
{config["prompt"]["instructions"]}
import os
from pathlib import Path Output format:
{config["prompt"]["output_format"]}
import pandas as pd """
import yaml
from anthropic import Anthropic print(f'Processing {row["request_id"]}...')
from dotenv import load_dotenv
result = call_llm(
from llm_client import call_llm client=client,
prompt=prompt,
model=model,
with open("config.yml", "r", encoding="utf-8") as f: temperature=..., # TODO 1: read from config
config = yaml.safe_load(f) max_tokens=..., # TODO 2: read from config
)
load_dotenv()
results.append({
client = Anthropic( "request_id": row["request_id"],
api_key=os.getenv("LLM_API_KEY"), "task": row["task"],
timeout=int(os.getenv("LLM_TIMEOUT_SECONDS", 30)), "customer_request": row["customer_request"],
) "model": result.model,
"latency_ms": result.latency_ms,
model = os.getenv("LLM_MODEL") "input_tokens": ..., # TODO 3: add input tokens
"output_tokens": ..., # TODO 4: add output tokens
df = pd.read_csv(config["input_csv"]) "status": "ok",
"output": ..., # TODO 5: add model response
results = [] })
output_path = Path(config["output_csv"])
output_path.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8")
print(f"Benchmark completed: {output_path}")
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 27

BLOQUE 4
4. Debrief y cierre
Qué debe quedar claro antes de pasar a prompting estructurado.
www.ebiseducation.com

Errores habituales en la primera integración
Estos errores son simples, pero en producción generan coste, riesgo y comportamiento inestable.
| Clave en código | Sin timeout | Prompt gigante |
| --------------- | ----------- | -------------- |
riesgo de seguridad y coste procesos bloqueados latencia y coste innecesarios
| Temperatura alta | Sin logging | Sin separación por capas |
| ---------------- | ----------- | ------------------------ |
salidas poco repetibles imposible depurar difícil cambiar de proveedor
29
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Mini-quiz de cierre
¿Por qué no debemos hardcodear una API key?
1
¿Qué parámetro reducirías para una tarea de clasificación estable?
2
¿Qué dos variables explican el coste de una llamada?
3
¿Qué harías ante un error 429?
4
¿Por qué conviene encapsular la llamada en llm_client.py?
5
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 30

El patrón mínimo
Clase 2: una automatización más fiable mediante prompts y salidas estructuradas.
|     | Hoy |     | Clase 2 | Meta |
| --- | --- | --- | ------- | ---- |
Llamada LLM desde Python Prompt engineering operativo Automatizar
| Parámetros básicos   |     | Salida estructurada |     | procesos con outputs  |
| -------------------- | --- | ------------------- | --- | --------------------- |
| Medición de latencia |     | Pydantic            |     | procesables y         |
| Comparación simple   |     | Retry si no valida  |     | controlados.          |
To sum up
Primero hacemos que el modelo sea invocable y medible. Después haremos que sea fiable.
31
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps

Material de apoyo y checklist
Para preparar la práctica, basta con tener entorno Python y una API key del proveedor seleccionado.
Checklist técnico
Lecturas recomendadas
• Python
• entorno virtual creado • documentación oficial del proveedor usado (anthropic)
• paquete SDK del proveedor • guías de pricing del proveedor (anthropic)
• .env configurado • guías de seguridad para API keys
• carpeta outputs/ creada
Nota de diseño
• Los precios, modelos disponibles y límites de rate limit cambian con frecuencia. En clase se usará la documentación vigente del proveedor elegido.
www.ebiseducation.com Tema 4 · Integración de LLMs vía API y LLMOps 32
