# Guía — Evaluar estrategias del agente y detectar invenciones con un LLM evaluador

> Propuesta de diseño para la **evaluación del agente** de [`PROYECTO.md`](../PROYECTO.md) (sección 9 y fases 6 y 10).
> Nace de la [sesión 2 del tema 8](../../08_ia_agentica_automatiz_agentes/02-ReAct-patrone-planificacion/explicacion-08.md)
> (ReAct, plan-and-execute, reflexión y `comparar_estrategias.py`), donde se vio que **medir latencia y tokens no basta**:
> hay que comprobar además si la respuesta es correcta y si se ha inventado algo.
>
> Estado: **propuesta**, nada implementado. Las decisiones abiertas están al final (sección 9).

## Índice

1. [Lo que enseñó la sesión 2 del tema 8](#1-lo-que-enseñó-la-sesión-2-del-tema-8)
2. [Qué estrategias comparar en Travel Agency](#2-qué-estrategias-comparar-en-travel-agency)
3. [Qué se mide: tres familias de métricas](#3-qué-se-mide-tres-familias-de-métricas)
4. [El LLM evaluador: ¿se ha inventado algo?](#4-el-llm-evaluador-se-ha-inventado-algo)
5. [Evaluar al evaluador](#5-evaluar-al-evaluador)
6. [El banco de pruebas](#6-el-banco-de-pruebas)
7. [Cómo se decide qué estrategia gana](#7-cómo-se-decide-qué-estrategia-gana)
8. [Dónde encaja en el proyecto](#8-dónde-encaja-en-el-proyecto)
9. [Decisiones abiertas](#9-decisiones-abiertas)

---

## 1. Lo que enseñó la sesión 2 del tema 8

En `tema8-agentes/sesion2/comparar_estrategias.py` se lanza la misma tarea («Soy marta.lopez@email.com. Quiero
repetir exactamente mi último pedido. ¿Tenéis stock de todo lo que pedí?») con cuatro estrategias, y se mide con
`comun/medidor.py` (`ClienteMedido`: llamadas, tokens y segundos).

La ejecución de clase:

| Estrategia | Llamadas | Tokens | Tiempo | ¿Correcta? |
|---|---|---|---|---|
| Tool calling nativo | 2 | 1018 | 7,6 s | No: se para antes de mirar el stock e inventa una fecha |
| ReAct prompting | 3 | 1329 | 12,3 s | No: vuelve a pedir el email |
| Plan-and-execute | 6 | 2572 | 21,8 s | No: dice que no encuentra el pedido |
| Con reflexión | 10 | 7363 | 107,1 s | No: coge el pedido equivocado, y **el crítico lo aprueba** |

Cinco lecciones que se trasladan tal cual a este proyecto:

1. **Las métricas de coste no dicen nada de la calidad.** La estrategia más barata y la más cara fallan las dos.
   La calidad se mide aparte, contra datos.
2. **Un crítico que no ve los datos aprueba respuestas falsas.** En `reflexion.py` el crítico recibe solo la
   pregunta y la respuesta. Comprueba que la respuesta *tenga la forma* correcta («dice que no hay stock, ofrece
   alternativa»), pero no si es verdad. La diapositiva lo dice: la reflexión **funciona mejor con señales
   objetivas: tests, datos, reglas**.
3. **Los modelos pequeños inventan detalles verosímiles**: la fecha «16 de marzo» no existe en la base de datos.
   Exactamente el tipo de error que el principio «el código calcula, el modelo redacta» quiere evitar.
4. **Los resultados varían entre ejecuciones** con el mismo código y la misma tarea. Una sola ejecución no sirve
   para comparar.
5. **El estado compartido contamina la comparación.** Al ejecutar las cuatro estrategias en el mismo proceso, un
   contador global de llamadas repetidas (de una solución del reto de la sesión 1) hizo fallar a la última
   estrategia. Cada ejecución tiene que empezar limpia.

## 2. Qué estrategias comparar en Travel Agency

Las mismas cuatro de la sesión 2, más una que aquí importa porque Qwen3 la tiene: el modo razonamiento.

| Estrategia | Qué es en Travel Agency | Por qué probarla |
|---|---|---|
| **A. Tool calling nativo** | Bucle de `sesion1/agente_minimo.py` con `consultar_bbdd` y `buscar_documentos` | **Línea base** de la fase 6. La más barata en la sesión 2 |
| **B. ReAct a mano** | Formato Pensamiento / Acción / Entrada con parser | Solo como referencia: Qwen3 soporta tool calling. Muestra cuánto cuesta el parser frágil |
| **C. Plan-and-execute** | Planificador → un paso por herramienta → sintetizador | Las preguntas **mixtas** (la reserva R-1042: datos de la BBDD + la regla del documento) piden varios pasos ordenados. El plan se puede auditar |
| **D. Con verificador** | A o C + un verificador que comprueba la respuesta **contra los resultados de las herramientas** (no un crítico «a ciegas») | Es la lección 2: la reflexión solo sirve si ve las señales objetivas |
| **E. A con `thinking`** | La estrategia A con el modo razonamiento de Qwen3 activado | Diapositiva «¿Y los modelos de razonamiento?»: planifican por dentro, pero con más tokens y latencia. Hay que medir si compensa |

Las estrategias se implementan con **la misma firma**, como el diccionario `ESTRATEGIAS` de
`comparar_estrategias.py`: reciben la pregunta y un cliente medido, devuelven la respuesta y sus métricas. Así el
banco de pruebas (sección 6) no sabe qué estrategia está ejecutando.

## 3. Qué se mide: tres familias de métricas

### 3.1 Coste y velocidad (ya previstas en los contratos)

Salen solas de la telemetría (sección 8 de `PROYECTO.md`), sin trabajo extra:

| Métrica | De dónde sale |
|---|---|
| Latencia total y por paso | `BaseMetrics.latency_ms` de cada span |
| Tiempo de LLM frente a tiempo de herramientas | `AgentMetrics.tiempo_llm_ms` / `tiempo_herramientas_ms` (por implementar) |
| Llamadas al LLM y a herramientas, iteraciones | `AgentMetrics.llamadas_llm`, `llamadas_herramientas`, `iteraciones` |
| Tokens de entrada, salida y razonamiento | `LlmCallMetrics.input_tokens`, `output_tokens`, `thinking_tokens` |
| Tiempo hasta el primer token, tokens/s | `LlmCallMetrics.time_to_first_token_ms`, `tokens_per_second` |
| Arranque en frío | `OllamaTimings.cold_start` (para descartar la primera ejecución, sección 6) |
| Coste estimado equivalente en la nube | `CostEstimate.from_tokens` |

Se reportan como **mediana (p50) y p95** sobre todas las repeticiones, no como una sola cifra.

### 3.2 Calidad objetiva (se comprueba con código)

Lo que se puede comprobar sin LLM **no se le pregunta a un LLM**. Viene de los casos dorados (`agent/eval/casos.yml`):

| Comprobación | Cómo |
|---|---|
| Herramienta correcta | `LlmCallMetrics.tool_calls` frente a la herramienta esperada del caso |
| Cifras exactas | Los números de la respuesta deben aparecer en las filas que devolvió `consultar_bbdd` |
| Abstención | `AgentMetrics.abstencion` frente a lo esperado en el caso |
| Citas que existen | Cada documento y página citados están entre los pasajes que devolvió `buscar_documentos` |
| Ataques | Ningún SQL fuera de las reglas (validador) |

### 3.3 Fidelidad: ¿se ha inventado algo?

Lo que el código no puede comprobar: que **cada afirmación** de la respuesta esté respaldada por lo que
devolvieron las herramientas. Una fecha inventada, un derecho que la normativa no da, un importe deducido mal…
Para eso está el LLM evaluador (sección 4).

## 4. El LLM evaluador: ¿se ha inventado algo?

### 4.1 La regla de oro: el evaluador ve las pruebas

El error de `reflexion.py` es darle al crítico solo `pregunta + respuesta`. Aquí el evaluador recibe **siempre**
tres cosas:

1. La **pregunta** del cliente.
2. La **evidencia**: todo lo que devolvieron las herramientas en esa ejecución (filas SQL, pasajes del RAG con
   documento y página). Se toma de la traza (`trace_id`), no se le pide al agente que la resuma.
3. La **respuesta** del agente.

Y una instrucción cerrada: *juzga solo con la evidencia; lo que no esté en ella cuenta como no respaldado, aunque
sea verdad en el mundo real*. Es la versión para el evaluador de «sin evidencia, abstención».

### 4.2 Cómo juzga: afirmación por afirmación

Un «¿está bien? sí/no» global es poco fiable y no dice dónde está el fallo. El evaluador:

1. **Separa la respuesta en afirmaciones** comprobables («la reserva R-1042 llegó con 5 horas de retraso», «le
   corresponden 600 €», «según el artículo 7 del Reglamento 261/2004»).
2. **Clasifica cada una** contra la evidencia:
   - `respaldada`: está en la evidencia, o se deduce directamente de ella;
   - `contradicha`: la evidencia dice otra cosa;
   - `no_respaldada`: no aparece en la evidencia (**invención**).
3. Para cada afirmación **copia el fragmento de evidencia** que la respalda o contradice. Así una persona puede
   revisar el veredicto en segundos.

Ejemplo *ilustrativo* con el caso del retraso:

| Afirmación de la respuesta | Evidencia | Veredicto |
|---|---|---|
| «Su vuelo llegó con 5 h de retraso» | Fila SQL: `retraso_min = 300` | `respaldada` |
| «El vuelo era de 2.000 km» | Fila SQL: `distancia_km = 2000` | `respaldada` |
| «Le corresponden 400 €» | Pasaje del reglamento: tramo de 1.500 a 3.500 km | `respaldada` (deducción directa) |
| «Se le abonará en 7 días» | Ningún pasaje habla de plazos de pago | `no_respaldada` → **invención** |

### 4.3 Salida estructurada

El evaluador responde con JSON validado por Pydantic (como el planificador y el crítico del tema 8, que usan
`extraer_json`, pero con esquema estricto, como los contratos del tema 4). Propuesta de contrato
(`contracts/`, nombre provisional `JudgeVerdict`):

| Campo | Contenido |
|---|---|
| `claims` | Lista de afirmaciones, cada una con `text`, `verdict` (`supported` / `contradicted` / `unsupported`) y `evidence_quote` |
| `unsupported_count`, `contradicted_count` | Recuentos derivados (los calcula un validador, no el LLM) |
| `faithful` | `True` solo si no hay `unsupported` ni `contradicted` |
| `answers_question` | Si la respuesta contesta a lo que se preguntó (lo que falló en la sesión 2: «un momento, por favor») |
| `metrics` | `LlmCallMetrics` con `purpose = judge` (ya existe en `LlmPurpose`) |

Los nombres van en inglés, con descripciones en español, como el resto de `contracts/metrics`.

### 4.4 Reglas para que el evaluador sea fiable

- **Primero el código, luego el LLM.** Las comprobaciones de la sección 3.2 se hacen antes y su resultado no se le
  pregunta al juez. El juez solo cubre lo que el código no puede.
- **Configuración fija**: `temperature = 0`, `seed` fijo, prompt versionado (`versions.prompt` del evento). Si el
  prompt del juez cambia, las evaluaciones anteriores dejan de ser comparables.
- **Su coste va aparte.** Las llamadas del juez llevan `purpose = judge` y **no se suman** al coste de la
  estrategia evaluada. Si no, la estrategia D parecería todavía más cara.
- **Mejor otro modelo que el del agente.** Un modelo que se juzga a sí mismo tiende a compartir sus puntos ciegos
  (lo que pasó con el crítico de la sesión 2, que era el mismo modelo). Ver decisiones abiertas.
- **Los documentos y las respuestas son datos, no instrucciones** (principio del proyecto): la evidencia y la
  respuesta van delimitadas en el prompt del juez, para que un pasaje con instrucciones no cambie el veredicto.

### 4.5 El mismo evaluador como verificador (estrategia D)

El juez de evaluación y el verificador de la estrategia D son la misma pieza usada en dos momentos:

| | Verificador (estrategia D) | Juez (evaluación) |
|---|---|---|
| Cuándo | En producción, antes de responder al cliente | Después, en `agent/eval/`, sobre las respuestas ya dadas |
| Qué hace si falla | Pide rehacer la respuesta con los comentarios (máximo N rondas), o se abstiene | Solo lo anota en el informe |
| Coste | Cuenta para la estrategia | No cuenta (`purpose = judge`) |

Compartir el código evita mantener dos rúbricas distintas.

## 5. Evaluar al evaluador

Un juez que no se ha medido es otra fuente de errores sin vigilar. Antes de fiarse de él:

1. **Respuestas trampa.** Se preparan respuestas con invenciones **puestas a propósito** (una fecha que no está,
   un importe cambiado, una cita a una página que no existe) y otras correctas. El juez tiene que detectar las
   primeras y no marcar las segundas. Se mide su tasa de acierto en las dos.
2. **Revisión manual de una muestra** de veredictos reales, como pide la sección 9 de `PROYECTO.md` (tema 5: una
   cita válida no prueba fidelidad; `practica/herramientas/preparar_revision.py` como referencia).
3. **Estabilidad.** El mismo par evidencia–respuesta, juzgado varias veces, debe dar el mismo veredicto. Si no, el
   juez no sirve para comparar estrategias.

## 6. El banco de pruebas

Un script (nombre provisional `agent/eval/comparar_estrategias.py`, como el del tema 8) que ejecuta
**estrategias × casos dorados × repeticiones**:

```
para cada estrategia (A…E):
    para cada caso de casos.yml:
        repetir N veces:
            estado limpio (sesión nueva, contadores a cero, nada global)
            ejecutar → respuesta + traza (trace_id) + métricas
            comprobaciones de código (3.2)
            juez de fidelidad (4) con la evidencia de la traza
            escribir evento JSONL
informe CSV/JSON: por estrategia, por caso y por tipo de caso
```

Reglas para que la comparación sea justa:

- **Estado limpio en cada ejecución** (lección 5): nada de diccionarios globales ni sesiones reutilizadas.
- **Mismas condiciones**: mismo modelo, misma configuración, mismos casos, misma máquina. Si cambia algo, se anota
  en `versions` del evento.
- **Calentar el modelo y descartar la primera ejecución** si `OllamaTimings.cold_start` es `True`: la carga del
  modelo no es mérito ni culpa de ninguna estrategia.
- **Varias repeticiones** (lección 4); cuántas, en las decisiones abiertas.
- **Modo mock para los tests** del propio banco de pruebas (regla del proyecto: los tests no necesitan Ollama).

El informe, por estrategia:

| Columna | Qué es |
|---|---|
| `acierto_%` | Casos con todas las comprobaciones de código superadas |
| `fiel_%` | Respuestas con `faithful = True` según el juez |
| `invenciones_por_respuesta` | Media de afirmaciones `unsupported` + `contradicted` |
| `ataques_superados` | Debe ser 0 |
| `latencia_p50_ms`, `latencia_p95_ms` | Sobre todas las repeticiones |
| `tokens_medios`, `llamadas_llm_medias` | Sin contar las del juez |
| `coste_estimado` | `CostEstimate` medio por pregunta |
| `variabilidad` | Casos en los que distintas repeticiones dieron resultado distinto |

## 7. Cómo se decide qué estrategia gana

Por orden, sin mezclar calidad y coste en una sola nota:

1. **Filtro duro**: se descarta cualquier estrategia con ataques superados o con invenciones en casos de cifras o
   normativa (importes, derechos, plazos).
2. **Calidad**: entre las que pasan, la de mayor `acierto_%` y `fiel_%`.
3. **Coste y velocidad**: si la calidad es parecida, gana la más barata y rápida. Es lo que mostró la sesión 2:
   **una arquitectura más compleja no es necesariamente mejor**.
4. **Por tipo de pregunta**: puede que gane A en las preguntas «solo BBDD» y C en las mixtas. Eso es un argumento
   para un **enrutador** (sesión 2: agente enrutador hacia especialistas), que se valoraría en una fase posterior.

La estrategia elegida queda como **línea base** (sección 9 de `PROYECTO.md`): cada cambio de prompt, modelo o
corpus se compara contra ella antes de aceptarlo.

## 8. Dónde encaja en el proyecto

| Fase | Qué se hace de esta guía |
|---|---|
| **1c. Contratos** | `JudgeVerdict` y el resultado de una ejecución de estrategia, si se decide meterlos ya |
| **6. Agente mínimo** | Estrategia A como línea base y el banco de pruebas con las comprobaciones de código (3.2) y las métricas de coste (3.1), sin juez todavía |
| **8. RAG** | Las citas entran en las comprobaciones; las preguntas mixtas hacen interesante la estrategia C |
| **10. Evaluación completa** | Juez de fidelidad, evaluación del juez (5), estrategias B–E e informe comparado |
| **11. MLflow** | Cada estrategia es un *run*; los veredictos del juez, artefactos; las trazas, en MLflow Tracing |

Referencias del repo para cuando se implemente (rutas desde `ebis/`):

| Pieza | Dónde mirar |
|---|---|
| Estrategias y comparación | `08_ia_agentica_automatiz_agentes/tema8-agentes/sesion2/` (`comparar_estrategias.py`, `plan_and_execute.py`, `reflexion.py`, `react_prompting.py`), `comun/medidor.py` |
| Crítico con criterios explícitos | `sesion2/reflexion.py` (`CRITERIOS`, `CRITICO`, `max_rondas`); aquí se amplía con la evidencia |
| Casos dorados y ejecución mock/real | `llm-customer-support-triage/eval/` (`eval_cases.yml`, `run_eval.py`) |
| Métricas, estadística y selección | `05_rag_langchain/clases/06-Const-evaluacion/src/retrieval_lab/evaluation/`, `07-RAG/src/umbra/evaluation/comparison.py` |
| Revisión manual de una muestra | `05_rag_langchain/practica/herramientas/preparar_revision.py` |

## 9. Decisiones abiertas

Para Mario, antes de implementar (se registran como ADR en `docs/` cuando se tomen):

1. **Modelo del juez**: el mismo Qwen3-4B del agente (más sencillo, comparte puntos ciegos) u otro modelo local
   distinto (más memoria y más tiempo de evaluación).
2. **Repeticiones por caso**: cuántas para que la variabilidad se vea sin que la evaluación tarde horas en local.
3. **Si la estrategia D entra en producción** o el verificador se queda solo como juez de evaluación (coste y
   latencia en cada respuesta).
4. **Si `JudgeVerdict` va en `contracts/`** (lo usarían `agent/` y `api/eval/`) o se queda dentro de `agent/eval/`.
