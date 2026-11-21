# ¿Encaja travel-agency con el TFM?

Comparación de `PROYECTO.md` (y del estado del repo a 2026-11-21) con *MAU - Orientaciones y pautas TFM.pdf*.

## Respuesta corta

**Sí encaja, y bastante bien en lo técnico**: agente con herramientas, Python, modelos locales, RAG, guardarraíles,
telemetría y una evaluación (pass^k, categorías, red teaming) que ya cubre casi todo lo que pide la guía, e incluso
varios de los «elementos valorables». Pero hay **tres cosas que hay que corregir ya**, antes de entregar la propuesta,
porque tocan requisitos mínimos:

1. **El TFM es en grupo** y el proyecto está pensado para una sola persona.
2. **Tal como está, el núcleo es un chatbot que solo informa**, y la guía dice que eso no basta. La acción
   (cancelaciones, fase 12) está como «extra» y al final.
3. **El alcance es demasiado grande** (15 fases). La guía premia lo acotado y bien resuelto.

La propuesta nueva (`propuesta-tfm-v2.md`) ya está escrita con estas tres correcciones.

## Lo que ya encaja

| Lo que pide la guía | Cómo lo cubre el proyecto |
|---|---|
| Agente que usa herramientas y toma decisiones justificadas | LangGraph con `query_db`, después `search_documents` y `manage_cancellation` |
| Backend y lógica en Python, aportación propia | Todo en Python: capa semántica, validador, alcance por cliente, evaluación, telemetría |
| Combinar lo determinista con lo basado en modelos | Es el principio del proyecto: «el código calcula, el modelo redacta» y «el modelo propone, el código decide» |
| Gestión de errores, límites y registro | `recursion_limit`, timeouts, reintentos de SQL, errores con nombre, telemetría JSONL con `trace_id` |
| Casos de prueba: habituales, límite y maliciosos | Categorías `normal` / `borde` / `adversario` del tema 9, k = 3 y pass^3 |
| Repetir cuando hay variabilidad | pass^3; ya está en el diseño |
| Registros que reconstruyen acciones sin exponer datos | Solo longitudes y huellas; árbol de spans; auditoría encadenada (fase 12) |
| Datos sintéticos, sin secretos, `.env.example` | Se cumple en todo el proyecto |
| Valorables: RAG, modelos locales, red teaming, observabilidad, idempotencia | Todos previstos |

## Lo que está mal o falta (por orden de importancia)

### 1. El TFM es en grupo

La guía habla en plural de principio a fin: «en grupo», «una entrega por grupo», «nombres de todos los integrantes»,
«contribución de cada integrante» en la memoria y en la defensa. El anuncio dice que **los grupos ya están asignados en
el Campus**.

- **Qué hacer:** mira en «Grupos» con quién estás. Si estás con más gente, este proyecto tiene que convertirse en el
  del grupo (o proponerlo como tal), con un reparto claro de piezas. Las carpetas independientes (`database/`,
  `text2sql/`, `rag/`, `agent/`, `api/`) facilitan el reparto.
- Si te dejan hacerlo solo, confírmalo por escrito con el tutor.
- Con grupo, sobran algunas reglas que ahora son tuyas: «Mario aprueba cada ciclo», memorias de Claude, el plan local…
  Habrá que acordar con el grupo cómo se trabaja.

### 2. Un chatbot que solo informa no basta

> «Un chatbot exclusivamente informativo […] no será suficiente. Un agente conversacional será válido cuando utilice
> herramientas y complete tareas dentro del proceso definido.»

El núcleo actual (fases 0–8) **solo lee y contesta**. Usa herramientas, que ya es algo, pero no completa ninguna tarea
con efecto. Además, la guía exige como **requisito mínimo** «al menos un punto de supervisión humana o de escalado», y
el ejemplo «gestión de citas o reservas por chat» de la guía (crear, modificar o cancelar pidiendo confirmación) es
casi tu fase 12.

- **Qué hacer:** pasar la **fase 12 (cancelaciones con aprobación humana) al núcleo**, justo después de la API. Es lo
  que convierte el proyecto en una automatización: entrada (mensaje) → tareas → resultado verificable (cancelado /
  ticket pendiente / bloqueado / escalado), comprobable en el estado final.
- `escalate_to_human` (decidido en `domain/rules.py`) también tiene que estar en el MVP, no solo en el diseño.
- Hay decisiones pendientes de la fase 12 que ahora pasan a ser urgentes: el umbral, dónde se guarda la cancelación
  (SQLite aparte), de dónde lee `compute_penalty` los plazos y cómo se entera el cliente.

### 3. Alcance demasiado grande

> «Un proyecto acotado y bien resuelto es preferible a uno amplio e inestable.» «La novedad de las herramientas, el
> número de agentes o la complejidad de la arquitectura no constituirán por sí mismos una mejora.»

Hay 15 fases y varias no aportan al proceso que se automatiza. Propuesta de recorte:

| Fase | Recomendación | Por qué |
|---|---|---|
| 4. Conversión con PaddleOCR | **Quitar el OCR** | Los 5 PDF ya tienen capa de texto; basta con extraer texto y MarkItDown para los HTML |
| 7b. Memoria a largo plazo por cliente | **Opcional** | El checkpoint de la sesión sí hace falta (multi-turno); la memoria entre sesiones no la pide nadie |
| 9. Fine-tuning | **Fuera** | Ya era opcional; Colab, GGUF… mucho trabajo para algo que la guía no valora |
| 11. MLflow | Opcional | La telemetría JSONL ya cumple «observabilidad»; MLflow es un extra |
| 13. Servidor MCP | Opcional | Valorable, pero no forma parte del proceso |
| 14. Modelos de decisión (Jev) | **Fuera** | Investigación aparte; no mejora el proceso |
| 15. Docker | **Al núcleo, simple** | La guía lo recomienda para que el corrector lo reproduzca «con el menor número de pasos» |
| Corpus | Reducir | tabiji (8.799 registros) y algunas fuentes no hacen falta para el proceso; deja lo de retrasos, cancelaciones, equipaje y viajes combinados, y un documento trampa para la inyección |

### 4. El flujo completo funciona demasiado tarde

La guía recomienda **un avance intermedio con el flujo funcionando de principio a fin**, aunque sea con datos de prueba.
Ahora mismo vas pieza a pieza y con mucha profundidad: la API (fase 7) todavía no existe.

- **Orden recomendado:** TRAVEL-008 (primera medida del SQL) → TRAVEL-011 (guardarraíles) → **API mínima** (flujo
  completo con `query_db`) → **cancelaciones con aprobación** → RAG → evaluación completa y memoria escrita → extras.
- Así, en el punto de control ya puedes enseñar: mensaje → agente → SQL → respuesta, y mensaje → cancelación pendiente
  → aprobación → auditoría.

### 5. Reproducibilidad y entrega

- **Repositorio propio.** `travel-agency/` vive dentro del repo `ebis`, junto a los PDF y el material del máster. Al
  corrector tienes que darle **un repo solo con el proyecto** (privado, con acceso para él).
- **Documentos fuera de git.** AESA y Exteriores (solo uso privado) y los archivos de más de 10 MB no están en el repo,
  así que el corrector no puede reconstruir el mismo corpus. Quita esas fuentes del MVP o añade un script de descarga
  y explica la diferencia.
- **Modelos locales.** Instrucciones para `ollama pull`, qué pasa sin GPU (CPU, más lento) y Docker Compose.
- La guía pide además: relación de servicios externos, permisos y **costes aproximados**, y limitaciones conocidas.

### 6. Aportación propia frente a «igual que en clase»

La regla del proyecto es ejecutar el mismo código que en clase. La guía lo permite («partir de un agente o framework
trabajado en el máster y ampliarlo»), pero exige una **aportación técnica propia y sustancial**. Si la memoria cuenta
cada pieza como «copiado de la sesión X», parecerá un montaje de ejercicios.

- **Qué hacer:** en la memoria, presenta las referencias de clase como **fundamentos** y pon el foco en lo tuyo: el
  dominio y los datos con trampas, la capa semántica, la lista blanca del validador, el alcance por cliente en tres
  capas, la integración de todas las piezas, el subagente con supervisión y la batería de evaluación. Los **desvíos**
  de los tickets son justo tus decisiones de diseño: úsalos.

### 7. Cosas que la guía pide y el diseño no tiene

| Falta | Qué añadir |
|---|---|
| **Justificar el agente frente a reglas o scripts** | Ya está en la propuesta v2; en la memoria, con datos: compara el agente con «consultas fijas» (la alternativa del tema 7) en los mismos casos |
| **Comparación con el proceso manual** | Estimación del tiempo de una persona por tipo de petición frente a la latencia medida; separa lo medido de lo estimado |
| **Análisis de costes completo** | Hoy solo hay coste equivalente por tokens; añade hardware, consumo eléctrico aproximado, mantenimiento y el coste en la nube como alternativa |
| **Declaración de uso de IA** | Obligatoria en la memoria: Claude Code con las skills `plan-ticket` y `tdd`. Los tickets sirven de prueba de que cada paso se revisó. Cada integrante tiene que poder explicar su código |
| **Qué está integrado y qué se simula** | El sistema de reservas es una réplica local; Slack, opcional. Dilo explícitamente |
| **Idempotencia** | En las cancelaciones: id de ticket y no repetir la acción al reanudar (ya está en las referencias del tema 8, sesión 6) |
| **Umbrales de despliegue** | Siguen «por decidir»: fíjalos antes de la primera evaluación completa |

## Lo que no hace falta cambiar

- El rigor de la evaluación (pass^3, juez calibrado, regresiones, red teaming con y sin defensas) está **por encima**
  de lo que pide la guía: es un punto fuerte en «evaluación experimental».
- La telemetría y los contratos con métricas encajan con «registro de las ejecuciones» y «trazabilidad».
- `PROYECTO.md` y los tickets son una base muy buena para la memoria de 60 páginas: su índice casi coincide con las
  secciones del proyecto (análisis → §1, arquitectura → §2, diseño agéntico → fase 6 y 12, seguridad → §9,
  evaluación → §9, viabilidad → §5 y costes).

## Siguientes pasos

1. Mirar el grupo asignado en el Campus y hablar con el grupo o con el tutor.
2. Revisar `propuesta-tfm-v2.md` (cancelaciones en el núcleo, recortes) y entregarla antes del **20/01/2027**.
3. Si la apruebas, actualizar `PROYECTO.md` §10 (orden y fases fuera) y la hoja de ruta de `AGENTS.md`.
