Tema 4 · Clase 4 1 Evento 2 Estado
APIs propias, FastAPI y
Llega un mensaje o cambio externo. La API carga y actualiza el caso.
workflows LLM
Del script con estado al servicio HTTP probado con
Postman
3 Operación 4 Respuesta
Se decide preguntar, escalar o ejecutar. Se devuelve JSON estable al cliente.
Una API LLM no “pregunta al modelo”: recibe eventos, actualiza estado y devuelve la siguiente
operación.
Máster en Ingeniería de Automatización con IA Agéntica
www.ebiseducation.com

Clase 4
Convertimos el workflow con estado de la Clase 3 en un servicio API.
| APIs LLM           | Prompting | Contexto   | FastAPI     | LLMOps       |
| ------------------ | --------- | ---------- | ----------- | ------------ |
| Python             | + JSON    | + sesiones | + endpoints | + despliegue |
| ✓ Resultado de hoy |           |            | IMPORTANTE  |              |
!
Una API FastAPI que recibe eventos por caso,  HTTP y el LLM son stateless. La aplicación
actualiza estado y devuelve operation + state. conserva estado.
Después de gestionar contexto en scripts, aprendemos a exponer la misma lógica como contrato HTTP consumible por frontend, Postman o sistemas externos.
Tema 4 · Integración de LLMs vía API y LLMOps 2

Objetivos de aprendizaje de la sesión
Al terminar, debemos poder diseñar y probar una API LLM con estado operativo.
01 Distinguir script y servicio 02 Diseñar contratos API
Qué cambia cuando pasamos de ejecución local a endpoint HTTP. Request, response, case_id, state, operation y errores.
03 Exponer el workflow de Clase 3 04 Probar con Postman y Swagger
Recibir eventos, cargar sesión, llamar al LLM y aplicar reglas. Ejecutar varios turnos y observar cómo cambia el estado.
Entregable práctico: api_models.py · session_store.py · app.py · postman_collection.json · endpoints con state/trace
Tema 4 · Integración de LLMs vía API y LLMOps 3

El cambio clave: de script batch a backend orientado a eventos
La lógica LLM deja de ejecutarse una vez; ahora responde a llamadas HTTP independientes.
| Clase 1        | Clase 2          | Clase 3          | Clase 4     |
| -------------- | ---------------- | ---------------- | ----------- |
| Invocar modelo | Controlar salida | Controlar estado | Exponer API |
Ahora llega un evento La API conserva estado La respuesta es operación
Un frontend, Postman o sistema externo envía  El endpoint carga el case_id, construye contexto  No devolvemos solo texto: devolvemos
un mensaje/cambio mediante HTTP. y actualiza la sesión. assistant_message, state, operation y métricas.
El objetivo no es “usar FastAPI”, sino convertir el workflow LLM en un componente reutilizable y trazable.
Tema 4 · Integración de LLMs vía API y LLMOps 4

BLOQUE 1
1. De script a servicio
Qué cambia al exponer un workflow LLM como API.
www.ebiseducation.com

Clase 3 nos dejó un workflow local con estado
Ahora lo encapsulamos detrás de un contrato HTTP.
call_llm_with_sche
| build_context | →   | →   |             | →   |           | →   |       |
| ------------- | --- | --- | ----------- | --- | --------- | --- | ----- |
|               |     |     | apply_rules |     | operation |     | trace |
ma
| Antes |     | Ahora |     |     | Criterio |     |     |
| ----- | --- | ----- | --- | --- | -------- | --- | --- |
python run_conversation.py POST /cases/{case_id}/events El mismo core lógico, otra interfaz de entrada y
Lee CSV, itera turnos y guarda un trace al final. Recibe un evento y devuelve estado + operación. salida.
La API no sustituye a la lógica de Clase 3: la reutiliza y la hace consumible por otras aplicaciones.
Tema 4 · Integración de LLMs vía API y LLMOps 6

HTTP es stateless. El LLM también. La aplicación no.
Cada request llega aislada, pero el backend reconstruye continuidad con case_id y state.
HTTP request LLM call Application state
No recuerda la request anterior. Cada llamada No conserva memoria real. Recibe contexto Guarda sesión, estado, resumen, trace y reglas
debe traer identificador y payload. construido en cada llamada. deterministas.
request backend
POST /cases/S-001/events case_id = "S-001"
{ state = store[case_id]
"message": "The order is 8921" context = build_context(state, event)
}
La continuidad no está en el protocolo ni en el modelo: está en el diseño de la aplicación.
Tema 4 · Integración de LLMs vía API y LLMOps 7

De CSV/script a endpoint: cambia la forma de entrada
Las peticiones sustituye al CSV como forma de simular eventos reales.
Script Clase 3 API Clase 4
Lee filas de CSV Recibe JSON por HTTP
Itera todos los turnos Procesa un evento por request
Guarda trace al final Devuelve respuesta inmediata
Útil para batch/debug Útil para frontend/integración
Consecuencia técnica
Necesitamos modelos de request/response, store de sesiones, control de
errores y pruebas HTTP.
Tema 4 · Integración de LLMs vía API y LLMOps 8

La API debe devolver más que una respuesta textual
Un cliente necesita saber qué ocurrió y qué debe hacer después.
request response
{ {
"event_type": "user_message", "assistant_message": "Could you provide the order number?",
"message": "I want to return an item", "operation": "ask_for_order_id",
"metadata": {"channel": "web"} "state": {...},
} "metrics": {...}
}
State Operation Metrics
Foto operativa actual del caso. Siguiente acción que debe ejecutar el sistema. Latencia, tokens y modelo para trazabilidad.
Tema 4 · Integración de LLMs vía API y LLMOps 9

Endpoint central: eventos sobre casos
El endpoint recibe lo que ha ocurrido; la API decide cómo evoluciona el estado.
endpoint Por qué “events”
POST /cases/{case_id}/events
No todo será chat: también puede llegar un email, un comentario de
operador o un campo manual.
{
"event_type": "user_message",
"message": "It arrived broken"
}
Por qué “case_id”
Agrupa llamadas independientes bajo la misma instancia de workflow.
Por qué “operation”
El backend devuelve qué toca hacer, no solo texto para mostrar.
El endpoint recibe eventos; las operaciones son resultado del workflow, no necesariamente endpoints separados.
Tema 4 · Integración de LLMs vía API y LLMOps 10

BLOQUE 2
2. Diseño de una API LLM con
estado
Request/response, sesiones, trace y operaciones como contrato.
www.ebiseducation.com

Arquitectura del servicio
El endpoint coordina; el modelo interpreta; Python valida y enruta.
Client FastAPI Session store Context builder LLM client Business rules
|     | →   | →   | →   | →   | →   |
| --- | --- | --- | --- | --- | --- |
envía evento HTTP valida request carga state/trace prepara entrada LLM devuelve update  decide operation
estructurado
| Validación de entrada |     | Salida estructurada |     | Respuesta estable |     |
| --------------------- | --- | ------------------- | --- | ----------------- | --- |
Pydantic valida el payload antes de tocar lógica de  Reutilizamos tool/schema para recibir  El cliente recibe assistant_message, operation, state
| negocio. |     | ConversationUpdate validado. |     | y métricas. |     |
| -------- | --- | ---------------------------- | --- | ----------- | --- |
Tema 4 · Integración de LLMs vía API y LLMOps 12

Request y response son parte del producto
La API se gobierna con modelos Pydantic, no con diccionarios sueltos.
class EventRequest(BaseModel):
api_models.py
event_type: str = "user_message"
Entrada controlada
message: str
metadata: dict = Field(default_factory=dict)
No aceptamos cualquier JSON: definimos qué campos son válidos.
class EventResponse(BaseModel):
case_id: str
assistant_message: str
operation: str
Salida predecible
state: ConversationState
metrics: RequestMetrics
El frontend no parsea texto: consume una estructura de dato.
Documentación automática
FastAPI genera OpenAPI/Swagger desde estos modelos.
Tema 4 · Integración de LLMs vía API y LLMOps 13

case_id es el eje de continuidad entre requests
Cada llamada HTTP es independiente, pero apunta a la misma instancia de workflow.
same case_id
La store recupera sesión
POST /cases/S-001/events
{ "message": "I want to return an item" } sessions[case_id] devuelve messages, summary, state y trace.
POST /cases/S-001/events
{ "message": "The order is 8921" }
El contexto se reconstruye
GET /cases/S-001/state
El endpoint ensambla reglas + estado + resumen + nuevo evento.
El cliente ve continuidad
Aunque HTTP no recuerde, la API responde como flujo coherente.
En producción el store no sería memoria local: sería Redis, PostgreSQL, MongoDB o una tabla de casos.
Tema 4 · Integración de LLMs vía API y LLMOps 14

El endpoint no “pregunta al modelo”: procesa un evento
El modelo es una etapa dentro de una transacción de negocio más amplia.
1 validate 2 load session 3 build context 4 call LLM 5 apply rules 6 return
request response
LLM stage Application stage
Interpreta el evento y propone un updated_state estructurado. Valida, calcula missing_fields, decide operation y guarda trace.
La API debe ser más determinista que el modelo: controla el ciclo de vida completo de la request.
Tema 4 · Integración de LLMs vía API y LLMOps 15

Routing como resultado, no como endpoint separado
No creamos un endpoint por operación; devolvemos la operación que corresponde.
Mala lectura Patrón recomendado
POST /ask_order_id POST /cases/{case_id}/events → operation=ask_for_order_id
POST /start_refund_validation POST /cases/{case_id}/events → operation=start_refund_validation
POST /send_to_human_review POST /cases/{case_id}/events → operation=send_to_human_review
Por qué Qué gana el diseño
La operación depende del estado completo del caso, no solo del mensaje La API mantiene una única entrada de eventos y un contrato de salida
actual. coherente.
Tema 4 · Integración de LLMs vía API y LLMOps 16

Trazabilidad: state, trace y métricas en cada request
Una API LLM debe poder explicar qué pasó en cada turno.
trace event
Debug
{
"case_id": "S-001",
Ver qué contexto y estado produjo cada operación.
"event": "The order is 8921",
"operation": "ask_for_reason",
"state": {...},
"metrics": {
"latency_ms": 1840,
"input_tokens": 920 Evaluación
}
}
Comprobar si el estado converge correctamente.
Observabilidad
Preparar latencia, tokens, errores y routing para Clase 5.
Tema 4 · Integración de LLMs vía API y LLMOps 17

BLOQUE 3
3. FastAPI y HTTP
Cómo probar el workflow como servicio y manejar errores reales.
www.ebiseducation.com

Endpoint principal: POST /cases/{case_id}/events
Una llamada HTTP actualiza el workflow y devuelve una operación.
app.py
Entrada
@app.post("/cases/{case_id}/events")
def process_event(case_id: str, request: EventRequest):
case_id + EventRequest
session = get_or_create_session(case_id)
prompt = build_context_prompt(session, request.message, config)
result = call_llm_with_schema(...)
state = apply_business_rules(result.object.updated_state)
operation = determine_next_operation(state)
return EventResponse(...)
Proceso
session → context → LLM → rules → trace
Salida
EventResponse con state, operation y metrics
Tema 4 · Integración de LLMs vía API y LLMOps 19

Endpoints de soporte: inspeccionar y resetear el caso
No todo endpoint debe llamar al modelo.
|                              | Endpoint    |                                   | Responsabilidad                | LLM call |
| ---------------------------- | ----------- | --------------------------------- | ------------------------------ | -------- |
|                              | GET /health | Comprobar que el servicio arranca |                                | No       |
| GET /cases/{case_id}/state   |             |                                   | Consultar estado actual        | No       |
| GET /cases/{case_id}/trace   |             |                                   | Consultar eventos y decisiones | No       |
| DELETE /cases/{case_id}      |             |                                   | Eliminar sesión local          | No       |
| POST /cases/{case_id}/events |             |                                   | Procesar nuevo evento          | Sí       |
Idea clave Coste
Separar endpoints de lectura/gestión de los endpoints que invocan el modelo. Solo el endpoint de eventos debería generar coste LLM.
Tema 4 · Integración de LLMs vía API y LLMOps 20

Postman: probar el flujo como usuario o sistema externo
Cada request avanza el mismo case_id y modifica el estado.
|     | turn 1 |     | turn 2 |     | turn 3 |
| --- | ------ | --- | ------ | --- | ------ |
POST /cases/S-001/events POST /cases/S-001/events POST /cases/S-001/events
| {   |     | {   |     | {   |     |
| --- | --- | --- | --- | --- | --- |
  "message": "It arrived broken"
|   "message": "I want to return an item" |     |   "message": "The order is 8921" |     |     |     |
| --------------------------------------- | --- | -------------------------------- | --- | --- | --- |
| }                                       |     | }                                |     | }   |     |
→ operation: ask_for_order_id → operation: ask_for_reason → operation: start_refund_validation
Tres llamadas HTTP independientes convergen a un estado completo.
Tema 4 · Integración de LLMs vía API y LLMOps 21

FastAPI genera documentación viva del contrato
Swagger ayuda a probar.
local run OpenAPI
uvicorn app:app --reload
Documenta endpoints, schemas, ejemplos y errores esperados.
http://127.0.0.1:8000/docs
Frontend
Consume la misma respuesta JSON sin saber cómo funciona el LLM.
Tema 4 · Integración de LLMs vía API y LLMOps 22

Errores esperables en una API LLM
El servicio debe fallar de forma controlada y útil para el cliente.
| Situación        | HTTP | Respuesta segura          |
| ---------------- | ---- | ------------------------- |
| Payload inválido | 422  | Pydantic validation error |
| Mensaje vacío    | 400  | Rechazar input            |
| API key ausente  | 500  | Config error controlado   |
Timeout proveedor/ fallo operative del prov 504/503/429 Retry/fallback o error explícito
| Salida estructurada inválida | 502 | No avanzar workflow |
| ---------------------------- | --- | ------------------- |
Principio Buenas prácticas
Un error del modelo no debe corromper el estado del caso. Validar input, capturar excepciones y registrar trace con status.
Tema 4 · Integración de LLMs vía API y LLMOps 23

Latencia y métricas por request
Cada endpoint LLM debe devolver o registrar metadatos operativos.
response metadata
Latencia
"metrics": {
"model": "claude-haiku-4-5", Impacta UX y throughput del backend.
"latency_ms": 1840,
"input_tokens": 920,
"output_tokens": 140
}
Tokens
Explican coste y tamaño de contexto.
Modelo
Permite comparar versiones y depurar cambios.
Tema 4 · Integración de LLMs vía API y LLMOps 24

Streaming: útil para UX, no siempre para workflows estructurados
La entrega incremental mejora experiencia, pero complica validación.
Cuándo sí Cuándo no
Respuestas largas, chat visible, generación de texto para Outputs JSON críticos, routing, operaciones que
usuario. requieren validación completa.
optional
@app.get("/demo/stream")
def stream_demo():
return StreamingResponse(token_generator(), media_type="text/plain")
Tema 4 · Integración de LLMs vía API y LLMOps 25

BLOQUE 4
4. Demo y práctica guiada
Construimos la API de eventos sobre el workflow de Clase 3.
www.ebiseducation.com

Caso práctico: AI Request Triage API
Convertimos una conversación multi-turn en una API de eventos con estado.
| Entrada | Estado | Decisión | Salida |
| ------- | ------ | -------- | ------ |
Eventos HTTP con message,  ConversationState por case_id. operation: ask, execute, review. JSON estable + metrics.
event_type y metadata.
input event API response
| POST /cases/S-001/events |     | {                                      |     |
| ------------------------ | --- | -------------------------------------- | --- |
| {                        |     |   "operation": "send_to_human_review", |     |
  "message": "I was charged twice for order 9901"   "state": {"priority": "high", ...}
| }   |     | }   |     |
| --- | --- | --- | --- |
Tema 4 · Integración de LLMs vía API y LLMOps 27

Estructura recomendada del repositorio
Reutilizamos el core de Clase 3 y añadimos la capa API.
project
class_04_fastapi_llm_service/ Nuevo
├── .env
├── config.yml app.py, api_models.py, session_store.py.
├── app.py
├── api_models.py
├── session_store.py
├── llm_client.py
├── schemas.py
├── prompts.py Reutilizado
├── business_rules.py
└── session_manager.py schemas.py, prompts.py, business_rules.py, llm_client.py.
Resultado
API local ejecutable con uvicorn .
Tema 4 · Integración de LLMs vía API y LLMOps 28

Construcción de la práctica: de core LLM a API
El objetivo es entender responsabilidades, no copiar un backend enorme.
|               | api_models.py |                   | session_store.py |           | app.py |
| ------------- | ------------- | ----------------- | ---------------- | --------- | ------ |
| A             |               | B                 |                  | C         |        |
| contrato HTTP |               | estado en memoria |                  | endpoints |        |
D Swagger E errors
pruebas fallo controlado
Tema 4 · Integración de LLMs vía API y LLMOps 29

Paso 1 · api_models.py: contrato de entrada y salida
La API expone modelos pequeños, estables y documentables.
class EventRequest(BaseModel): api_models.py
event_type: str = "user_message"
Qué decide
message: str
metadata: dict = Field(default_factory=dict)
Cómo se comunica el cliente con la API.
class RequestMetrics(BaseModel):
model: str
latency_ms: int
input_tokens: int
output_tokens: int TODO
Añadir validaciones de message y metadata.
class EventResponse(BaseModel):
case_id: str
assistant_message: str
operation: str
state: ConversationState
metrics: RequestMetrics Criterio
Ningún endpoint debería devolver texto sin contrato.
Tema 4 · Integración de LLMs vía API y LLMOps 30

Paso 2 · session_store.py: memoria local por case_id
Para clase usamos memoria en proceso; en producción sería una base persistente.
session_store.py
sessions: dict[str, SessionManager] = {} Responsabilidad
def get_or_create_session(case_id: str): Separar almacenamiento de sesiones de los endpoints.
# TODO: create SessionManager if missing
...
def get_session(case_id: str):
# TODO: return existing session or raise 404
... Limitación
def delete_session(case_id: str):
Si reinicias el servidor, se pierde el estado.
# TODO: remove session from store
...
Producción
Redis / DB / tabla de casos con TTL y auditoría.
Tema 4 · Integración de LLMs vía API y LLMOps 31

Paso 3 · app.py: inicializar FastAPI y dependencias
El servicio carga config, entorno, cliente LLM y aplicación FastAPI.
app.py setup
Qué aporta
with open("config.yml", "r", encoding="utf-8") as f:
config = yaml.safe_load(f)
Punto de entrada único para todos los endpoints.
load_dotenv()
client = Anthropic(
api_key=os.getenv("LLM_API_KEY"),
timeout=int(os.getenv("LLM_TIMEOUT_SECONDS", 30)),
TODO
)
Comprobar API key/model y preparar health check.
app = FastAPI(title="AI Request Triage API")
Patrón
Config y secretos separados como en Clase 1.
Tema 4 · Integración de LLMs vía API y LLMOps 32

Paso 4 · endpoint de eventos: el core del servicio
El endpoint reutiliza el workflow de Clase 3 por cada request.
app.py
Entrada
@app.post("/cases/{case_id}/events")
def process_event(case_id: str, request: EventRequest):
session = get_or_create_session(case_id) case_id + EventRequest.
prompt = build_context_prompt(session, request.message, config)
result = call_llm_with_schema(
client=client,
prompt=prompt, TODO
schema=ConversationUpdate,
...
Actualizar session.messages, session.state y trace.
)
# TODO: apply rules, update session and return response
Salida
EventResponse con operation + state + metrics.
Tema 4 · Integración de LLMs vía API y LLMOps 33

Paso 5 · endpoints de estado, traza y reset
Leer estado no debería llamar al modelo ni generar coste.
@app.get("/cases/{case_id}/state") app.py
def get_case_state(case_id: str): Diagnóstico
session = get_session(case_id)
return session.state
GET /state permite ver si el workflow converge.
@app.get("/cases/{case_id}/trace")
def get_case_trace(case_id: str):
# TODO: return session trace
... Auditoría
GET /trace permite revisar decisiones y métricas.
@app.delete("/cases/{case_id}")
def reset_case(case_id: str):
# TODO: delete session
...
Pruebas
DELETE permite reiniciar un caso desde Postman.
Tema 4 · Integración de LLMs vía API y LLMOps 34

Paso 6 · manejo de errores: proteger el estado
Si el LLM falla, el caso no debe quedar a medias.
app.py
Regla
try:
result = call_llm_with_schema(...) No actualices state hasta tener output validado.
except TimeoutError:
raise HTTPException(status_code=504, detail="LLM timeout")
except ValidationError:
raise HTTPException(status_code=502, detail="Invalid structured output")
except Exception:
TODO
raise HTTPException(status_code=500, detail="Internal error")
Devolver errores claros sin exponer secretos ni stack traces.
Clase 5
Esto será base de logging, métricas y alertas.
Tema 4 · Integración de LLMs vía API y LLMOps 35

Paso 7 · streaming demo: separado del workflow principal
Útil para enseñar UX incremental sin mezclarlo con routing estructurado.
streaming demo
Objetivo
from fastapi.responses import StreamingResponse
Ver cómo FastAPI puede devolver datos incrementalmente.
def token_generator():
for chunk in ["Processing", " case", "...", " done"]:
yield chunk
Cuidado
@app.get("/demo/stream")
def stream_demo(): No usarlo para decidir operation hasta validar salida completa.
return StreamingResponse(token_generator(), media_type="text/plain")
Práctica
Endpoint opcional; el core de eventos sigue siendo estructurado.
Tema 4 · Integración de LLMs vía API y LLMOps 36

Output: respuesta API con estado y operación
EventResponse
{ Para frontend
"case_id": "S-001",
"assistant_message": "What is the reason for the return?",
Mostrar assistant_message y decidir UI según operation.
"operation": "ask_for_reason",
"state": {
"process_type": "refund_request",
"order_id": "8921",
"reason": null,
"missing_fields": ["reason"],
Para backend
"ready_for_next_step": false
},
Ejecutar routing o escalar según operation.
"metrics": {"latency_ms": 1540}
}
Para observabilidad
Registrar métricas y trace para análisis posterior.
Tema 4 · Integración de LLMs vía API y LLMOps 37

Debrief: APIs LLM como workflows stateful
El endpoint no es una llamada al modelo: es una operación de negocio controlada.
| 1 HTTP stateless | 2 App stateful | 3 Contrato API |
| ---------------- | -------------- | -------------- |
Cada request llega aislada. case_id recupera estado y trace. Request/response con Pydantic.
| Salida estructurada | Reglas en código | Postman/OpenAPI |
| ------------------- | ---------------- | --------------- |
| 4                   | 5                | 6               |
El LLM devuelve update validable. routing y seguridad no dependen solo del prompt. La API se puede probar y compartir.
Una API LLM robusta recibe eventos, actualiza estado, aplica reglas y devuelve la siguiente operación del workflow.
Tema 4 · Integración de LLMs vía API y LLMOps 39

a la Clase 5
En la próxima sesión operaremos, evaluaremos y desplegaremos este servicio.
Clase 1 Clase 2 Clase 3 Clase 4 Clase 5
Cliente LLM Salida estructurada Estado/contexto API propia LLMOps
hoy Siguiente paso
POST /cases/{case_id}/events
Versionar prompts/modelos, evaluar calidad, registrar métricas, monitorizar
→ update state
errores y preparar despliegue controlado.
→ return operation
→ trace metrics
Meta: una API LLM no se considera lista hasta que puede evaluarse, observarse y operar con seguridad.
Tema 4 · Integración de LLMs vía API y LLMOps 41
