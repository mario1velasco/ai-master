Tema 4 · Clase 5 1 Evaluación
Casos esperados y regresión
LLMOps, observabilidad
y
2 Observabilidad
despliegue controlado
Logs, métricas y trazas
De la API funcional al servicio evaluable, medible y
desplegable
3 Versionado
Prompt, schema, modelo y config
4 Despliegue
Docker, CI/CD y releases
Máster en Ingeniería de Automatización con IA Agéntica Una aplicación LLM no está lista cuando responde: está lista cuando puede evaluarse,
observarse y desplegarse con control.
www.ebiseducation.com

Clase 5
Cerramos el Tema 4 convirtiendo la API en un servicio operable.
| APIs LLM           | Prompting | Contexto   | FastAPI      | LLMOps       |
| ------------------ | --------- | ---------- | ------------ | ------------ |
| Python             | + JSON    | + sesiones | + endpoints  | + despliegue |
| ✓ Resultado de hoy |           |            | ! Importante |              |
Una API LLM con evaluación básica, trazas útiles, versionado operativo, tests y Dockerfile. No vamos a hacer DevOps genérico. Vamos a operar el workflow LLM construido en
Clase 4.
Cierre del tema
Pasamos de “funciona en local” a “puedo demostrar que sigue funcionando cuando cambian prompts, modelos, entradas, costes o latencias”.
Tesis de la clase: una app LLM no está lista cuando responde; está lista cuando puede evaluarse, observarse, versionarse
y desplegarse con control.
Tema 4 · Integración de LLMs vía API y LLMOps 2

Objetivos de aprendizaje de la sesión
Al terminar, debemos poder diseñar una estrategia mínima de LLMOps para nuestra API.
01 Entender LLMOps 02 Diseñar observabilidad
Qué cambia frente a MLOps clásico y qué piezas hay que operar. Registrar latencia, tokens, errores, operación, versión y estado.
03 Evaluar workflows 04 Preparar despliegue
Probar que el sistema produce estados y operaciones esperadas. Docker, tests, CI/CD y estrategias de release controladas.
Entregable práctico: observability.py · eval_cases.yml · run_eval.py · tests · Dockerfile · README de operación
Tema 4 · Integración de LLMs vía API y LLMOps 3

El cambio clave: de servicio funcional a servicio operable
La API de Clase 4 ya responde; ahora necesitamos gobernar cambios, fallos y coste.
| Clase 1 | Clase 2 |     | Clase 3 | Clase 4 | Clase 5 |
| ------- | ------- | --- | ------- | ------- | ------- |
Invocar modelo Controlar salida Controlar estado Exponer API Operar servicio
| Riesgo nuevo |     | Necesidad nueva |     | Práctica nueva |     |
| ------------ | --- | --------------- | --- | -------------- | --- |
Un cambio de prompt, modelo o contexto puede  Medir comportamiento, comparar versiones y detectar  Tests, evaluación offline, trazas, métricas y Docker para
modificar decisiones sin romper el código. degradaciones. despliegue.
El objetivo no es añadir herramientas por añadir: es poder responder “qué versión tomó esta decisión, con qué coste, con
qué latencia y con qué resultado esperado”.
Tema 4 · Integración de LLMs vía API y LLMOps 4

BLOQUE 1
LLMOps aplicado
Qué significa operar una aplicación LLM y por qué no basta con tener una API.
www.ebiseducation.com

De demo funcional a sistema operable
Lo que funciona en una prueba puede fallar cuando cambian entradas, modelo, coste o latencia.
Demo local Servicio operable
Probamos 3 mensajes Evaluamos casos críticos y regresiones
Vemos respuesta manualmente Medimos estado, operación, errores y coste
Una versión de prompt Versionamos prompt, schema, modelo y config
Sin trazabilidad formal Trace por request y por caso
Ejecuta en local Docker, CI/CD y estrategia de release
Mensaje de diseño Respuesta operativa
Una app LLM falla de formas distintas a una API tradicional: puede responder válido en Necesitamos gates de evaluación y trazas que detecten degradación semántica, no
HTTP, pero incorrecto en negocio. solo caídas técnicas.
Tema 4 · Integración de LLMs vía API y LLMOps 6

LLMOps no es MLOps con otro nombre
Hay solape, pero las piezas que cambian son distintas.
Dimensión MLOps clásico LLMOps en nuestra API
Activo principal Modelo entrenado y dataset Prompt, schema, modelo externo, contexto y reglas
Evaluación Métricas offline del modelo Estados esperados, operación, seguridad y regresión
Drift Datos/features cambian Cambian inputs, modelo proveedor, prompt o contexto
Coste Infra de entrenamiento/inferencia Tokens, latencia, modelo y retries
Release Modelo o pipeline Prompt/model/config/schema/API contract
En LLMOps versionamos y evaluamos más que código: también prompts, schemas, herramientas, modelos, reglas de
negocio y presupuestos de contexto.
Tema 4 · Integración de LLMs vía API y LLMOps 7

Qué hay que operar en nuestra API LLM
Partimos de la API de Clase 4 y añadimos gobierno alrededor de cada pieza.
| FastAPI endpoint | Session store | Prompt builder | LLM client |
| ---------------- | ------------- | -------------- | ---------- |
contrato HTTP estado y trace contexto enviado modelo y latencia
| Schema | Business rules | Evaluation set | Docker/CI |
| ------ | -------------- | -------------- | --------- |
salida estructurada routing seguro casos esperados release reproducible
La pregunta operativa es: ¿puedo saber qué ha pasado, repetir la prueba, comparar versiones y desplegar sin
perder control?
Tema 4 · Integración de LLMs vía API y LLMOps 8

Ciclo de vida mínimo de una aplicación LLM
Diseñar, evaluar, desplegar, observar y mantener forman un ciclo continuo.
| Diseñar | →   | Evaluar | →   | Desplegar | →   | Observar | →   | Mantener |
| ------- | --- | ------- | --- | --------- | --- | -------- | --- | -------- |
prompt + schema + reglas casos esperados Docker + CI/CD logs + métricas retries + versiones
| No lineal |     |     |     | Criterio de madurez |     |     |     |     |
| --------- | --- | --- | --- | ------------------- | --- | --- | --- | --- |
La monitorización alimenta nuevas evaluaciones. Los errores reales deben convertirse  No basta con “se ha desplegado”. Debemos poder pausar, volver atrás, comparar
| en casos de regresión. |     |     |     | versiones y explicar decisiones. |     |     |     |     |
| ---------------------- | --- | --- | --- | -------------------------------- | --- | --- | --- | --- |
Tema 4 · Integración de LLMs vía API y LLMOps 9

Riesgos que LLMOps debe controlar
No todos los fallos son errores 500: algunos son decisiones incorrectas con respuesta válida.
| Riesgo  | Síntoma              | Control mínimo              |
| ------- | -------------------- | --------------------------- |
| Calidad | operation incorrecta | eval set + regression gates |
Coste tokens crecen por contexto context budget + coste por caso
| Latencia | respuesta lenta | timeout + métricas p95 |
| -------- | --------------- | ---------------------- |
Seguridad input intenta modificar reglas validación + prompt boundaries
| Estado    | pierde campos entre llamadas | merge controlado + trace    |
| --------- | ---------------------------- | --------------------------- |
| Proveedor | rate limit / caída           | retry, fallback o safe stop |
La regla operativa: un fallo del modelo no debe avanzar el workflow ni corromper el estado del caso.
Tema 4 · Integración de LLMs vía API y LLMOps 10

BLOQUE 2
Observabilidad
Convertir las trazas de la API en señales útiles para operar el servicio.
www.ebiseducation.com

De trace local a observabilidad operativa
Clase 4 ya guardaba eventos. Ahora decidimos qué señales deben ser explotables.
trace Log
trace_event = {
"case_id": case_id,
Registro de algo que ha ocurrido: request, error, operación o decisión.
"operation": operation,
"state": state.model_dump(),
"latency_ms": result.latency_ms,
"input_tokens": result.input_tokens,
"output_tokens": result.output_tokens,
Metric
"model": result.model
} Número agregable: latencia media, error rate, token rate, human review rate.
Trace
Secuencia de pasos de una request/caso para depurar el flujo completo.
Observabilidad no es guardar todo. Es guardar lo suficiente para depurar, medir y tomar decisiones operativas.
Tema 4 · Integración de LLMs vía API y LLMOps 12

Qué registrar por request LLM
Cada llamada debe dejar una huella mínima: qué versión, qué operación y qué coste tuvo.
Campo Para qué sirve
case_id Agrupar eventos de un mismo workflow
event_type / operation Entender qué hizo el sistema
status / error_type Separar éxito, timeout, rate limit o salida inválida
model / prompt_version Depurar cambios de comportamiento
latency_ms / tokens Controlar UX, coste y capacidad
schema_validation_ok Saber si el output era consumible
requires_human_review Medir automatización segura vs escalado
Si no queda en log o trace, en producción no ha ocurrido. Y si no tiene versión, no se puede comparar.
Tema 4 · Integración de LLMs vía API y LLMOps 13

Métricas por capa: no todo mide lo mismo
El dashboard debe separar salud técnica, coste y calidad del workflow.
| Técnica | Coste | Workflow | Calidad |
| ------- | ----- | -------- | ------- |
status_code input_tokens operation_distribution expected_operation_match
timeout_rate output_tokens human_review_rate invalid_output_rate
provider_error_rate cost_per_case ready_rate invented_id_rate
| p95 latency | retry_rate | missing_fields | regression_failures |
| ----------- | ---------- | -------------- | ------------------- |
Una API puede estar operativa y aun así estar tomando malas decisiones. Por eso necesitamos métricas técnicas y de
negocio.
Tema 4 · Integración de LLMs vía API y LLMOps 14

Dashboards y alertas: qué mirar primero
No hace falta empezar con una plataforma compleja: empieza con señales accionables.
Señal Alerta razonable Posible acción
invalid_output_rate sube respecto a baseline rollback prompt/model o activar repair
p95 latency supera umbral revisar contexto, proveedor o modelo
human_review_rate sube abruptamente analizar nuevos inputs o reglas
cost_per_case sube por tokens resumir, recortar contexto, enrutar modelos
provider_error_rate 429/503 frecuentes backoff, fallback, cuotas
Principio Conexión Clase 5
Una alerta debe tener una acción asociada. Si nadie sabe qué hacer, es ruido. Los outputs de evaluación se convierten en baseline; producción se compara contra
baseline.
Tema 4 · Integración de LLMs vía API y LLMOps 15

BLOQUE 3
Evaluación
Probar workflows LLM por estado y operación, no solo por “respuesta bonita”.
www.ebiseducation.com

Probar manualmente no es evaluar
Tres llamadas que funcionan en Swagger no garantizan que el sistema resista cambios.
Prueba manual Evaluación offline Regression gate
Útil para entender el flujo, pero no detecta regresiones Ejecuta casos esperados y compara process_type, Si un cambio empeora casos críticos, no se despliega
cuando cambia el prompt o el modelo. operation, missing_fields y seguridad. aunque la API arranque.
En LLM workflows, la pregunta no es “¿responde algo razonable?” sino “¿termina en el estado y operación
correctos?”.
Tema 4 · Integración de LLMs vía API y LLMOps 17

Pirámide de evaluación para la API LLM
Combinamos tests deterministas con evaluación de comportamiento del modelo.
Más abajo: tests rápidos y deterministas. Más arriba: pruebas más caras, pero más cercanas al comportamiento real.
Release gate comparar versión actual vs baseline
LLM eval casos esperados con modelo real o stub
API tests /health, /state, /trace, validation 422
Unit tests business_rules, merge_state, schemas
Tema 4 · Integración de LLMs vía API y LLMOps 18

Golden dataset: casos mínimos que no deben romperse
Un dataset pequeño y bien elegido vale más que cien ejemplos redundantes.
eval_cases.yml Cubre intención
- case_id: EVAL-001
input: "I want to return an item"
expected: refund, delivery, billing, support, ambiguous.
process_type: refund_request
operation: ask_for_order_id
missing_fields: [order_id, reason]
- case_id: EVAL-002
input: "I was charged twice for order 9901" Cubre riesgo
expected:
process_type: billing_issue alta prioridad, datos ausentes, prompt injection, IDs inventados.
operation: send_to_human_review
Cubre routing
ask_missing, execute, human_review, general_queue.
El dataset de evaluación es un contrato de comportamiento: define lo que la app no puede dejar de hacer.
Tema 4 · Integración de LLMs vía API y LLMOps 19

Métricas de evaluación: medir el workflow, no solo el texto
El assistant_message puede variar; el estado y la operación deben ser estables.
Métrica Qué comprueba
process_type_match La intención se clasificó correctamente
operation_match El routing final es el esperado
missing_fields_match El sistema pide lo que falta
no_invented_id No crea order_id si no aparece
human_review_match Escala casos de riesgo
schema_valid El output se puede consumir por software
La evaluación debe tolerar variación lingüística, pero no variación arbitraria en campos que gobiernan el proceso.
Tema 4 · Integración de LLMs vía API y LLMOps 20

Release gates: cuándo bloquear un cambio
Una versión nueva de prompt/modelo debe superar mínimos antes de llegar a producción.
| Gate              | Umbral ejemplo         | Decisión                  |
| ----------------- | ---------------------- | ------------------------- |
| schema_valid_rate | 100% en casos críticos | Bloquear si falla         |
| operation_match   | ≥ 95% global           | Revisar si baja           |
| invented_id_rate  | 0%                     | Bloquear                  |
| p95 latency       | < umbral UX            | Optimizar modelo/contexto |
| cost_per_case     | ≤ presupuesto          | Reducir tokens o routing  |
Principio de release
No desplegamos una versión porque “parece mejor”; la desplegamos porque supera criterios explícitos de calidad, seguridad, latencia y coste.
Tema 4 · Integración de LLMs vía API y LLMOps 21

BLOQUE 4
Versionado, errores y coste
Controlar qué cambió, cómo falla y cuánto cuesta operar el servicio.
www.ebiseducation.com

Versionar lo que afecta a la decisión
En LLMOps, una regresión puede venir de código, prompt, schema, modelo o configuración.
trace Prompt version
trace_event = {
"model": "claude-haiku-4-5-20251001",
Cambia instrucciones y ejemplos.
"prompt_version": "triage_prompt_v1",
"schema_version": "conversation_update_v1",
"rules_version": "business_rules_v1",
"config_version": "class5_config_v1",
"operation": operation Schema version
}
Cambia campos, tipos y contrato.
Model/config version
Cambia comportamiento, coste y latencia.
Sin versionado, una traza explica “qué ha pasado”, pero no “con qué configuración ha pasado”.
Tema 4 · Integración de LLMs vía API y LLMOps 23

Errores y respuestas seguras
El objetivo no es evitar todo fallo, sino impedir que un fallo avance el workflow mal.
Error Respuesta segura
Input inválido 422 · no llamar al LLM
Rate limit backoff / retry controlado
Timeout 504 · retry o fallback
Output inválido no actualizar estado; retry repair o safe stop
Alta incertidumbre human_review
Proveedor caído fallback model o degradación funcional
Regla: no se guarda estado nuevo hasta tener una salida validada y reglas aplicadas.
Tema 4 · Integración de LLMs vía API y LLMOps 24

Retries, repair y fallback: no todo error se trata igual
Cada mecanismo tiene coste y riesgo; no se debe reintentar sin control.
Retry Repair Fallback Safe stop
Mismo prompt, mismo modelo. Útil Pedir corregir formato/salida. Útil si el Cambiar modelo/proveedor. Útil ante No continuar y pedir revisión. Útil ante
para timeouts o errores transitorios. JSON/schema falla. caída o saturación. riesgo de negocio.
Lo que no hacemos: repetir indefinidamente, ocultar errores o actualizar estado con una salida no validada.
Tema 4 · Integración de LLMs vía API y LLMOps 25

Control de coste: tokens, modelo y contexto
Optimizar no es solo recortar: es enviar el contexto correcto al modelo correcto.
| cost | Context budget | Model routing |
| ---- | -------------- | ------------- |
estimated_cost = (
    input_tokens  * input_price_per_1k  +
|     | Últimos N mensajes + resumen + estado.  | Usar modelo barato para triage y potente  |
| --- | --------------------------------------- | ----------------------------------------- |
    output_tokens * output_price_per_1k
|     | Evitar historial completo. | para casos complejos. |
| --- | -------------------------- | --------------------- |
) / 1000
case_cost += estimated_cost
|     | Caching / reuse                  | Human review                            |
| --- | -------------------------------- | --------------------------------------- |
|     | Reutilizar summaries, estados y  | Escalar evita automatizar mal y gastar  |
|     | resultados deterministas.        | tokens en bucles.                       |
Coste operativo = tokens × modelo × retries × volumen. LLMOps decide dónde gastar capacidad.
Tema 4 · Integración de LLMs vía API y LLMOps 26

Estrategias de release: canary, blue-green y autoscaling
No todas las versiones deben llegar al 100% de tráfico de golpe.
| Estrategia | Idea | Aplicación LLM |
| ---------- | ---- | -------------- |
Blue-green dos entornos y cambio de tráfico desplegar prompt/model/API v2 con rollback rápido
Canary pequeño porcentaje usa versión nueva 5% con prompt_v2; comparar calidad/coste/error
Autoscaling más réplicas según carga escala API por tráfico; ojo con rate limits del proveedor
| Métrica de canary |     | Criterio |
| ----------------- | --- | -------- |
operation_match, invalid_output_rate, p95 latency, cost_per_case,  Si v2 empeora señales críticas, rollback aunque la API esté técnicamente sana.
human_review_rate.
Tema 4 · Integración de LLMs vía API y LLMOps 27

CI/CD y Docker: reproducibilidad antes que complejidad
El objetivo de esta clase no es Kubernetes; es empaquetar y comprobar el servicio.
commit → test → eval → build → deploy
código + config unit + api golden dataset Docker image staging/prod
Un pipeline LLM debe validar más que “la API arranca”: debe ejecutar casos esperados y bloquear regresiones de
comportamiento.
Tema 4 · Integración de LLMs vía API y LLMOps 28

BLOQUE 5
Demo y práctica guiada
Añadimos evaluación, observabilidad y empaquetado a la API de Clase 4.
www.ebiseducation.com

Caso práctico: AI Request Triage API encapsulado
No cambiamos de aplicación: reforzamos la API de Clase 4 para operarla.
Punto de partida Añadimos Resultado
API FastAPI con /cases/{case_id}/events, state, trace y versionado, observability.py, eval_cases.yml, Un servicio evaluable, medible y empaquetable para
business rules. run_eval.py, tests y Dockerfile. despliegue controlado.
La práctica estará más guiada: cada snippet indica objetivo, TODO, hint y check de validación.
Tema 4 · Integración de LLMs vía API y LLMOps 30

Estructura recomendada del repositorio
Partimos del servicio de Clase 4 y añadimos capa de operación.
project Nuevo
class_05_llmops_service/
├── .env.example
observability.py, eval_cases.yml, run_eval.py, tests y Dockerfile.
├── config.yml
├── app.py
├── observability.py
├── eval_cases.yml
├── run_eval.py
├── tests/ Reutilizado
│ ├── test_business_rules.py
│ └── test_api.py app.py, schemas.py, business_rules.py, llm_client.py y session_store.py.
├── Dockerfile
├── .dockerignore
└── README.md
Check
La API debe seguir ejecutando /health y /cases/{case_id}/events.
Tema 4 · Integración de LLMs vía API y LLMOps 31

Paso 0 · requirements y .env: preparar operación
Añadimos dependencias para tests y mantenemos secretos fuera del código.
setup Objetivo
# requirements.txt
fastapi
uvicorn[standard] Instalar lo necesario para API, tests y evaluación sin mezclar secretos con código.
anthropic
python-dotenv
pydantic
pyyaml
pytest
TODO
httpx
pandas
Añadir pytest y httpx. Copiar .env.example a .env y rellenar API key local.
# .env.example
LLM_PROVIDER=anthropic
LLM_API_KEY=replace_with_your_key
LLM_MODEL=claude-haiku-4-5-20251001
LLM_TIMEOUT_SECONDS=30 Hint
Los tests de API pueden usar TestClient/httpx sin llamar al LLM si aislamos
# For tests, evaluation and demos without provider cost: dependencias.
USE_MOCK_LLM=false
Check
python -m pytest debe descubrir tests aunque al principio fallen por TODOs.
Tema 4 · Integración de LLMs vía API y LLMOps 32

Paso 1 · config.yml: versiones y política operativa
La configuración debe decir no solo cómo llamar al modelo, sino qué versión estamos probando.
config.yml Objetivo
app:
name: "AI Request Triage API"
version: "1.1.0" Que cada traza se pueda asociar a una versión concreta de prompt, schema y
deployment_environment: "local“ reglas.
llm:
temperature: 0.0
TODO
max_tokens: 700
Completar versions.
context:
max_recent_messages: 6
summarize_after_messages: 8
keep_last_messages_after_summary: 4
Hint
versions:
prompt_version: TODO
Usa nombres explícitos: triage_prompt_v1, conversation_update_v1, rules_v1.
schema_version: TODO
rules_version: TODO
eval_set_version: TODO
observability: Check
request_log_path: "logs/requests.jsonl"
include_prompt_preview: false El trace debe incluir estas versiones en cada evento procesado.
prompt_preview_chars: 400
cost:
currency: "USD"
input_cost_per_1m_tokens: 0.80
output_cost_per_1m_tokens: 4.00
Tema 4 · Integración de LLMs vía API y LLMOps 33

Paso 2 · observability.py: crear eventos de traza consistentes
Centralizamos el formato de observabilidad para no construir diccionarios distintos en cada endpoint.
observability.py Objetivo
def build_observability_event(*, case_id: str, event_type: str, message: str, operation:
str, state: dict, model: str, latency_ms: int, input_tokens: int, output_tokens: int,
status: str, config: dict, error_type: str | None = None, prompt: str | None = None) -> Un único builder para logs/traces operativos.
dict[str, Any]:
event = {
"timestamp": datetime.now(timezone.utc).isoformat(),
"deployment_environment": config["app"]["deployment_environment"],
"case_id": case_id,
"event_type": event_type, TODO
"message_chars": len(message),
"operation": operation, Leer versiones desde config y añadir status/error_type si aplica.
"status": status,
"error_type": error_type,
"model": model,
"latency_ms": latency_ms,
"input_tokens": input_tokens,
"output_tokens": output_tokens, Hint
"estimated_cost": estimate_cost(input_tokens, output_tokens, config),
"currency": config["cost"]["currency"], No metas secretos ni prompts completos en trazas productivas.
"prompt_version": TODO,
"schema_version": TODO,
"rules_version": TODO,
"state": state,
}
if config["observability"].get("include_prompt_preview") and prompt: Check
chars = config["observability"].get("prompt_preview_chars", 400)
event["prompt_preview"] = prompt[:chars] GET /trace debe mostrar versiones, tokens, latencia y operación.
return event
Tema 4 · Integración de LLMs vía API y LLMOps 34

Paso 3 · app.py: enriquecer trace sin cambiar el contrato principal
El endpoint sigue igual para el cliente, pero ahora deja señales operativas útiles.
app.py Objetivo
obs_event = build_observability_event(
case_id=case_id,
event_type=request.event_type, Mantener response simple, pero registrar suficiente información para operar.
message=request.message,
operation=operation,
state=state.model_dump(mode="json"),
model=result.model,
latency_ms=result.latency_ms,
TODO
input_tokens=result.input_tokens,
output_tokens=result.output_tokens,
status="success", Sustituir diccionario manual por build_observability_event().
config=config,
prompt=prompt,
)
session.add_trace_event(obs_event)
write_jsonl(config["observability"]["request_log_path"], obs_event)
Hint
El estado se actualiza solo después de validar el output y aplicar reglas.
Check
/cases/S-001/trace debe contener trace_event homogéneo.
Tema 4 · Integración de LLMs vía API y LLMOps 35

Paso 4 · eval_cases.yml: definir casos esperados
El dataset de evaluación debe ser pequeño, claro y cubrir riesgos reales.
eval_cases.yml Objetivo
case_id: "EVAL-001"
description: "Refund request completed after order and reason"
events: Definir comportamiento mínimo aceptable de la API.
- "I want to return an item."
- "The order number is 8921."
- "It arrived broken."
expected:
process_type: "refund_request"
order_id: "8921" TODO
reason: "damaged_item"
operation: "start_refund_validation" Añadir 6–10 casos: refund, delivery, billing, technical y prompt injection.
requires_human_review: false
ready_for_next_step: true
Hint
Evalúa campos de negocio; no obligues a que assistant_message sea idéntico.
Check
Cada caso debe tener expected.operation y al menos un campo esperado de
state.
Tema 4 · Integración de LLMs vía API y LLMOps 36

Paso 5 · run_eval.py: ejecutar evaluación offline
La evaluación compara el resultado del workflow contra expected fields.
run_eval.py Objetivo
def compare_expected(
final_state: dict,
operation: str, Producir un reporte simple: qué casos pasan y cuáles fallan.
expected: dict
) -> tuple[bool, list[str]]:
"""
Compara el estado final obtenido con el estado esperado.
TODO
Devuelve:
Completar comparaciones contra expected y calcular métricas globales.
- True si todo coincide.
- False y una lista de errores si encuentra diferencias.
"""
errors = []
Hint
Al principio puede ejecutarse con una función local; luego contra la API real.
# Recorremos cada dato que esperamos encontrar.
for key, expected_value in expected.items():
# El campo "operation" no está en final_state,
# por eso usamos el parámetro operation. Check
if key == "operation":
actual_value = operation outputs/eval_report.csv debe mostrar passed=True/False por caso.
else:
# Para el resto de campos buscamos su valor en final_state.
actual_value = TODO
# Si el valor obtenido no coincide con el esperado,
# guardamos una descripción del error.
if actual_value != expected_value:
error = (
f"{key}: "
f"expected={expected_value!r}, "
f"actual={actual_value!r}"
)
errors.append(error)
Tema 4 · Inte g r a c#ió nS die nLoL Mhsa vyí a eArPrI oyr LeLsM,O lpas comparación ha sido correcta. 37
is_correct = len(errors) == 0
return is_correct, errors

Paso 6 · tests/test_business_rules.py: asegurar lógica determinista
Las reglas de negocio son código; deben probarse sin llamar al LLM.
pytest Objetivo
def test_refund_request_missing_order_id():
state = ConversationState(
process_type=ProcessType.refund_request, Garantizar que routing y readiness no dependen de la interpretación del modelo.
reason="damaged_item",
priority=Priority.medium
)
state = apply_business_rules(state)
assert state.ready_for_next_step is False
assert state.missing_fields == TODO TODO
assert determine_next_operation(state) == TODO
Cubrir missing_fields, high priority y operación esperada.
def test_high_priority_goes_to_human_review():
# TODO: build high priority state
# TODO: assert requires_human_review is True state = apply_business_rules(state)
Hint
Estos tests deben ser rápidos y deterministas.
Check
pytest tests/test_business_rules.py debe pasar sin API key.
Tema 4 · Integración de LLMs vía API y LLMOps 38

Paso 7 · tests/test_api.py: probar contrato HTTP
No todo test debe llamar al proveedor LLM; primero valida endpoints y errores.
pytest Objetivo
from fastapi.testclient import TestClient
from app import app
Comprobar contrato de API, validación de entrada y endpoints sin coste LLM.
client = TestClient(app)
def test_health():
response = client.get("/health")
assert response.status_code == 200
TODO
assert response.json()["status"] == "ok"
def test_empty_message_returns_422(): Completar status esperado y añadir GET /state para caso inexistente.
response = client.post("/cases/T-002/events", json={"message": ""})
assert response.status_code == TODO
Hint
Un mensaje vacío devuelve 422 porque Pydantic valida min_length.
Check
pytest debe detectar errores de contrato antes de probar LLM real.
Tema 4 · Integración de LLMs vía API y LLMOps 39

Paso 8 · Dockerfile: empaquetar el servicio
Docker hace reproducible el entorno de ejecución, pero los secretos siguen fuera de la imagen.
Dockerfile Objetivo
FROM python:3.11-slim
WORKDIR /app Ejecutar la API de forma reproducible en cualquier entorno compatible.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
TODO
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
Crear .dockerignore y pasar .env en tiempo de ejecución.
Hint
Nunca copies .env con secretos dentro de la imagen.
Check
docker build y docker run deben exponer /health.
Tema 4 · Integración de LLMs vía API y LLMOps 40

Paso 9 · CI/CD: pipeline mínimo de seguridad
Antes de desplegar, el pipeline debe ejecutar tests y evaluación de regresión.
ci.yml Objetivo
name: ci
on: [push] Automatizar comprobaciones antes de construir o desplegar imagen.
jobs:
test:
runs-on: ubuntu-latest
steps:
TODO
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
with: Añadir umbrales de evaluación y bloquear si fallan.
python-version: "3.11"
- run: pip install -r requirements.txt
- run: pytest
- run: python run_eval.py # optional gate
Hint
El pipeline puede usar stubs si no quieres gastar tokens en cada push.
Check
Un cambio que rompe business_rules debe fallar antes de producción.
Tema 4 · Integración de LLMs vía API y LLMOps 41

Ejecución recomendada de la práctica
Primero local, después tests, evaluación y finalmente Docker.
runbook Orden didáctico
# 1. Run API locally
uvicorn app:app --reload
No empezamos por Docker. Primero comprobamos que la API y la lógica
# 2. Smoke test funcionan localmente.
curl http://127.0.0.1:8000/health
# 3. Run deterministic tests
pytest
# 4. Run offline evaluation Orden productivo
python run_eval.py
Tests y evaluación deberían ejecutarse antes de construir o promover una imagen.
# 5. Build container
docker build -t ai-triage-api .
# 6. Run container
docker run --env-file .env -p 8000:8000 ai-triage-api
Check final
/health, /docs, pytest y run_eval.py deben estar verdes.
Tema 4 · Integración de LLMs vía API y LLMOps 42

Output esperado: reporte de evaluación
La práctica termina generando una tabla simple para decidir si una versión es aceptable.
eval_report.csv Para depurar
case_id,operation_match,process_type_match,missing_fields_match,passed
EVAL-001,true,true,true,true
Qué casos fallaron y en qué criterio.
EVAL-002,true,true,true,true
EVAL-003,false,true,false,false
Summary:
operation_accuracy = 0.87
invalid_output_rate = 0.00 Para release
release_gate = FAILED
Si no supera umbral, no se despliega.
Para mejorar
Cada fallo real puede convertirse en nuevo caso de evaluación.
La evaluación convierte opiniones subjetivas en decisiones de release defendibles.
Tema 4 · Integración de LLMs vía API y LLMOps 43

Debrief: de API funcional a servicio gobernado
La última capa del tema es hacer que el sistema sea medible, evaluable y desplegable.
| 1  Operabilidad | 2  Evaluación | 3  Versionado |
| --------------- | ------------- | ------------- |
Una API LLM necesita logs, métricas y trazas útiles. No probamos texto: probamos estados, operaciones y  Prompt, schema, modelo, reglas y config afectan a
|          | seguridad.            | decisiones.   |
| -------- | --------------------- | ------------- |
| 4  Coste | 5  Release controlado | 6  Producción |
Tokens y modelo son decisiones de arquitectura. Canary, blue-green y gates reducen riesgo. Docker/CI/CD hacen el servicio reproducible y
comprobable.
Una app LLM robusta no solo responde: demuestra que sigue respondiendo bien cuando el sistema cambia.
Tema 4 · Integración de LLMs vía API y LLMOps 44

Mini-quiz de cierre
Cinco preguntas para comprobar el marco mental de LLMOps.
1 ¿Qué diferencia hay entre probar manualmente y evaluar con regression cases?
2 ¿Qué elementos versionarías además del código?
3 ¿Qué métrica mirarías si sube el coste por caso?
4 ¿Cuándo bloquearías un despliegue aunque la API arranque correctamente?
5 ¿Por qué un error de salida estructurada no debe actualizar estado?
Tema 4 · Integración de LLMs vía API y LLMOps 45

Cierre del Tema 4
Hemos construido el camino completo: cliente, salida, estado, API y operación.
Clase 1 Clase 2 Clase 3 Clase 4 Clase 5
Cliente LLM medible Salida estructurada Contexto y estado API propia LLMOps
end-to-end Meta final
POST /cases/{case_id}/events
→ update state
Una API LLM no se considera lista hasta que puede evaluarse, observarse
→ return operation
y operarse con seguridad.
→ trace metrics
→ evaluate baseline
→ deploy controlled release
Siguiente paso profesional
Conectar métricas reales a dashboards, persistir trazas y automatizar
gates de release.
Tema 4 · Integración de LLMs vía API y LLMOps 46
