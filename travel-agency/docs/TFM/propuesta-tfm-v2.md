# Propuesta de TFM: Viajes Nimbo, un agente de atención al cliente que consulta, cita y gestiona cancelaciones

**Máster en Ingeniería de Automatización con IA Agéntica (EBIS) · 1LSVER26**
**Integrantes:** Mario Velasco Alonso *(completar con el grupo asignado)*

## 1. Problema y motivación

**Usuarios:** los clientes de una agencia de viajes online (Viajes Nimbo, ficticia) y su equipo de atención al cliente.

**Proceso actual (manual).** Un cliente escribe por chat o correo: «el vuelo de mi reserva R-1042 llegó con 5 horas
de retraso, ¿a qué tengo derecho?» o «quiero cancelar mi reserva». La persona que atiende busca la reserva en el
sistema, calcula el retraso y la distancia, consulta el Reglamento (CE) 261/2004 y las políticas de la agencia, calcula
la compensación o la penalización, contesta y, si es una cancelación, la ejecuta o la pasa a un responsable cuando el
importe es alto. Son dos sistemas (datos y normativa), cálculos fáciles de equivocar (retraso a la llegada y no a la
salida, importe neto y no bruto) y respuestas que a menudo no citan de dónde salen.

**Motivación.** Automatizar este proceso ahorra trabajo repetitivo, da respuestas citadas y comprobables y deja a las
personas lo que de verdad necesita su criterio: las cancelaciones de importe alto y los casos que el sistema no
resuelve.

## 2. Automatización propuesta

- **Entrada:** un mensaje del cliente identificado en el chat (`POST /sessions/{id}/messages` con su `cliente_id`).
- **Tareas:** entender la petición; consultar los datos del cliente; buscar la norma o política aplicable; calcular
  (en código) compensaciones o penalizaciones; redactar una respuesta citada; y, si pide cancelar, tramitar la
  cancelación según la política de supervisión.
- **Resultado verificable:** una de estas cuatro salidas, cada una comprobable en el estado del sistema y en el
  registro: (1) respuesta con sus fuentes (SQL ejecutado y documento con página), (2) cancelación ejecutada y anotada en
  la auditoría, (3) ticket pendiente de aprobación humana, o (4) escalado a una persona.

## 3. Componente agéntico

**Por qué un agente y no reglas:** las preguntas llegan en lenguaje libre y en muchas formas. Hay que decidir en cada
caso si hacen falta los datos, la normativa o las dos cosas, y combinar los resultados. Unas reglas o un script no
cubren esa variedad. Lo que sí es determinista se queda en código: cálculos, validación del SQL, permisos, política de
supervisión y reglas de escalado.

| | Agente principal (LangGraph) | Subagente de cancelaciones |
|---|---|---|
| **Función** | Atender la petición del cliente | Tramitar una cancelación |
| **Decide** | Qué herramienta usar y en qué orden; si tiene evidencia suficiente o debe abstenerse; cómo combinar y redactar | Si la reserva se puede cancelar y qué penalización aplica (con los datos y la política) |
| **Herramientas** | `query_db` (text-to-SQL sobre vistas de lectura), `search_documents` (RAG con citas), `manage_cancellation` | `get_booking` (lectura), `compute_penalty` (código), `cancel_booking` (irreversible) |
| **Límites** | Solo lee; solo datos del cliente de la sesión (lo impone el código); máximo de pasos y tiempo | Automático hasta un umbral de importe; por encima, **aprobación humana**; bloqueo si la reserva es de otro cliente, ya está cancelada o el reembolso supera lo pagado |

**Supervisión humana y escalado:** cola de aprobaciones (`/aprobaciones`) para las cancelaciones por encima del umbral,
con revisión por muestreo de las automáticas; escalado a una persona decidido en código (reclamación formal, límite de
pasos alcanzado, falta de evidencia). El chat nunca dice «cancelado» si la cancelación está pendiente.

## 4. Arquitectura preliminar

```
cliente ─► API FastAPI ─► agente (LangGraph + Qwen3-4B en Ollama)
                            ├─ query_db ───────────► text-to-SQL ─► validador ─► DuckDB (vistas de lectura)
                            ├─ search_documents ───► RAG híbrido: BM25 + bge-m3/FAISS + RRF + reranker
                            └─ manage_cancellation ► subagente ─► cola de aprobación ─► auditoría (SQLite)
```

- **Modelos (open source, en local):** Qwen3-4B-Instruct en Ollama para el agente y el SQL; bge-m3 (embeddings) y
  bge-reranker-v2-m3 para el RAG.
- **Frameworks:** Python 3.12, LangGraph, FastAPI + Pydantic, DuckDB, FAISS, pytest; entorno con uv.
- **Datos:** clientes, vuelos, reservas, pagos e incidencias **sintéticos** (CSV propios + generador con semilla). Corpus
  con licencia comprobada: Reglamento 261/2004, Directiva 2015/2302 y BOE, guías oficiales (Sanidad, EASA) y 26
  políticas propias de la agencia.
- **Estado y registro:** sesiones del chat con checkpoint en SQLite; telemetría propia en JSONL (traza por petición,
  tokens, latencia, coste) y auditoría encadenada de las cancelaciones.
- **Sistemas simulados:** el sistema de reservas es una réplica local (DuckDB + SQLite); el aviso de aprobación por
  Slack es opcional.

## 5. Objetivos y evaluación

**Objetivo general:** que el agente resuelva peticiones de clientes con datos y normativa citada, sin inventar, y
tramite cancelaciones con la supervisión proporcional a su importe.

| Objetivo | Métrica y criterio de éxito |
|---|---|
| Consultas de datos correctas | Exactitud del text-to-SQL contra un SQL de referencia en un examen de preguntas de cliente |
| Respuestas normativas citadas | Hit@k del RAG; citas que existen en el corpus; abstención cuando no hay evidencia |
| Proceso completo | pass^3 (acierta las 3 repeticiones) por categoría: casos habituales, límite y de ataque |
| Cancelaciones bien supervisadas | Se comprueba el **estado final**: por encima del umbral, nada se cancela sin aprobar; lo bloqueado nunca se cancela; la auditoría queda íntegra |
| Seguridad | 0 ataques superados (inyección en mensajes y documentos, datos de otro cliente, SQL fuera de las reglas), con y sin defensas |
| Supervisión | Tasa de escalado y de aprobaciones, con sus motivos |
| Tiempo y coste | Latencia p95 por tipo de petición; coste por caso resuelto (local) frente al equivalente en un modelo en la nube |
| Calidad de redacción | LLM juez con rúbrica sí/no que ve la evidencia, calibrado con etiquetas humanas |

Comparación con una alternativa más sencilla: consultas fijas por reglas frente al agente, en los mismos casos.

## 6. Alcance y viabilidad

**Incluido (MVP):** chat por API con sesiones, consultas a datos, RAG con citas, cancelaciones con aprobación humana,
guardarraíles, registro de ejecuciones, batería de pruebas y despliegue reproducible (instrucciones + Docker Compose).

**Excluido:** crear o modificar reservas, información en tiempo real (precios, vuelos de hoy), asesoramiento legal,
interfaz gráfica, datos personales reales y afinar el modelo (solo si la evaluación lo justificara).

**Recursos:** portátil con i7, 16 GB de RAM y GPU de 4 GB; todo el software es gratuito y open source. Coste de
inferencia: 0 € en local (se estimará el equivalente en la nube y el consumo del equipo).

**Estado:** ya funcionan la base de datos con su capa semántica, el corpus, el text-to-SQL con validador y una primera
versión del agente con la herramienta de datos.

**Riesgos y mitigación:**

| Riesgo | Mitigación |
|---|---|
| Un modelo de 4B se equivoca con el SQL o promete acciones que no ha hecho | Vistas que hacen los cálculos, validador, reintento con el error y medida con examen; el estado final se comprueba en código |
| Latencia de decenas de segundos en este hardware | Aceptable para una prueba de concepto; se mide y se documenta |
| Alcance demasiado amplio | Primero el flujo completo con datos; después RAG y cancelaciones; los extras (MCP, MLflow) solo si sobra tiempo |
| Reproducibilidad (modelos locales, documentos con licencia de uso privado) | Docker Compose, descarga del modelo con un comando y solo documentos redistribuibles en el repositorio |
