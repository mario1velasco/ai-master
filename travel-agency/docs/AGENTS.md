# AGENTS.md — `docs/`

Documentación del proyecto que no es código: **guías de diseño** y **tickets**. El diseño general está en
[`../PROYECTO.md`](../PROYECTO.md); el estado de cada fase, en la hoja de ruta de [`../AGENTS.md`](../AGENTS.md).

## Los tickets son el histórico del proyecto

Cada ticket (`tickets/TRAVEL-NNN-*.md`) recoge **por qué** se hizo algo, no solo qué: las referencias de clase que se
leyeron, los **desvíos** respecto al patrón de clase y su motivo, las preguntas que se le hicieron a Mario y lo que
contestó, los supuestos y lo que quedó fuera. Juntos son el registro del flujo de trabajo seguido.

**Úsalos como fuente cuando necesites saber algo del proyecto**, antes de suponer o de volver a preguntar:

- **¿Por qué el código es así?** → *Contexto* y *Desvíos* del ticket que lo creó.
- **¿Esto ya se decidió?** → *Supuestos y preguntas abiertas* y las decisiones citadas «decidido con Mario».
- **¿Qué falta?** → *Fuera* (alcance) y, en algunos, «Lo que queda de la fase N» al final.
- **¿Qué referencias de clase hay para una pieza?** → *Referencias leídas*.
- **¿Qué comportamiento se garantiza?** → los criterios de aceptación: cada uno tiene un test (tickets de código).

Si un ticket contradice a `PROYECTO.md` o a un `AGENTS.md`, manda lo más reciente; si no está claro, pregunta a Mario.
El campo *Estado* de los tickets antiguos puede estar desfasado (p. ej. «pendiente de commit» ya commiteado): el
estado real de cada fase está en la hoja de ruta de `../AGENTS.md` y en `git log`.

### Cómo se crean y se desarrollan

1. **Planificar** con la skill `plan-ticket` (`ebis/.claude/skills/plan-ticket/`): historia de usuario, alcance,
   criterios en Dado / Cuando / Entonces, acordados con Mario pregunta a pregunta. Se guarda aquí como
   `TRAVEL-NNN-<slug>.md`, con el siguiente número libre.
2. **Desarrollar** con la skill `tdd` (tickets de código): un criterio cada vez, test en rojo → código mínimo en verde,
   parando a revisar en cada ciclo. Los tickets de **datos o documentos** (TRAVEL-003, 004, 008) no llevan tests: se
   comprueban con comandos o revisión, como dice cada criterio.
3. **Cerrar**: actualizar el *Estado* del ticket, la fila de la fase en `../AGENTS.md` y el `AGENTS.md` de la carpeta.

No reescribas un ticket cerrado para que cuadre con el código: si algo cambió después, se apunta en el ticket nuevo
que lo cambia (o una nota fechada al final del antiguo).

## Tickets

| Ticket | Fase | Tipo | Qué hace | Estado (2026-11-16) |
|---|---|---|---|---|
| [TRAVEL-001](tickets/TRAVEL-001-generar-datos-sinteticos.md) | 2b | Código | Generador con semilla fija (`database.seed`) que amplía los CSV a mano de `fixtures/` a miles de filas en `data/`, sin perder casos ancla ni trampas. Sin Faker: `random.Random(semilla)` y listas a mano | Hecho |
| [TRAVEL-002](tickets/TRAVEL-002-sql-guard-view-whitelist.md) | 5 | Código | Validador del SQL del modelo (`text2sql/guard.py`): `ejecutar_sql_seguro` de clase más una **lista blanca de vistas** (solo lo de `main`; nada de tablas crudas, archivos ni funciones de tabla) | Hecho |
| [TRAVEL-003](tickets/TRAVEL-003-reunir-corpus-externo.md) | 3 | Datos | Corpus externo del RAG (leyes, salud, seguridad, general) con `SOURCES.md`: fuente, licencia y huella SHA-256; lo de uso privado (AESA, Exteriores) fuera de git | Hecho |
| [TRAVEL-004](tickets/TRAVEL-004-redactar-documentos-empresa.md) | 3 | Datos | 26 documentos propios de Viajes Nimbo en `rag/corpus/empresa/`, coherentes con la base, con casos difíciles a propósito (versión derogada, política que mejora la ley, documento con inyección) | Hecho |
| [TRAVEL-005](tickets/TRAVEL-005-consultar-linea-base.md) | 5 | Código | `text2sql.ask()`: pregunta → SQL con Qwen3-4B → validador → DuckDB, con bucle de corrección (3 llamadas como máximo), telemetría y comando `python -m text2sql`. Devuelve filas, **no redacta** | Hecho (sin medir: ver 007 y 008) |
| [TRAVEL-006](tickets/TRAVEL-006-agente-minimo-consultar-bbdd.md) | 6 | Código | Agente mínimo con LangGraph (`construir_agente` de clase) y la tool `query_db` → `text2sql.ask()`; contrato `AgentAnswer`. Al final, «Lo que queda de la fase 6» (citas y verificador, plan cerrado, casos dorados) | Hecho |
| [TRAVEL-007](tickets/TRAVEL-007-evaluar-text2sql-corrector-metricas.md) | 5 | Código | Herramienta para evaluar `text2sql` (tema 9, sesión 1): corrige cada intento contra el resultado de un SQL de referencia (mismas filas, valores en su fila), métricas pass^k, latencia, disponibilidad y coste por acierto; `trace_id` en `SqlResult` | Hecho |
| [TRAVEL-008](tickets/TRAVEL-008-examen-text2sql-primera-medida.md) | 5 | Datos | Examen de ~50 preguntas (batería ~35 + final reservado ~15) por trampa y categoría, y primera medida con el Qwen real (k = 3) como línea base. Cierra la fase 5 | En curso: exámenes hechos con preguntas de cliente (batería 37, final 18); falta la medida |
| [TRAVEL-009](tickets/TRAVEL-009-guardar-esquema-con-huella.md) | 5 | Código | El esquema de `schema()` (~5,7 s) se guarda en un archivo con la huella SHA-256 (CSV + `semantic_layer.py` + DuckDB) en el nombre y solo se regenera si cambia; fuera el `@cache` de `build_system_prompt`, que retenía las conexiones; `semantic_layer.py` separado en tres archivos | Hecho |
| [TRAVEL-010](tickets/TRAVEL-010-vista-tramos-clase-asiento-equipaje.md) | 2 / 5 | Código | Vista `v_tramos`, una fila por vuelo de cada reserva: clase, asiento (NULL = sin asignar), maleta facturada (booleano), aerolínea, ruta, retrasos y estado del vuelo. Esas columnas solo estaban en `crudo.reservas_tramos` y son lo que más pregunta un cliente por chat. Va antes de la medida de 008 | Hecho |
| [TRAVEL-011](tickets/TRAVEL-011-guardarrailes-agente.md) | 6 | Código | Guardarraíles del agente (tema 9, sesión 2) en un solo fichero, con interruptor: entrada (tarjeta, IBAN, DNI, 2.000 caracteres), herramientas en tres capas (ids de la pregunta, vistas filtradas por el cliente de la sesión, filas ajenas) y salida (email y nombre de otros clientes); registro de bloqueos en `AgentAnswer` y en la telemetría. Chat solo para clientes | Borrador, pendiente de revisión |
| [TRAVEL-012](tickets/TRAVEL-012-examen-agente.md) | 6 | Código + datos | Examen del agente (tema 9, sesión 1): lo común de medir sale de text2sql a un paquete nuevo `evaluation/`; corrector de resultado y trayectoria, juez con la evidencia (aparte, sin calibrar hasta la fase 10), medida con y sin guardarraíles y recuento de bloqueos; batería ~20 y final reservado ~8 escritos por Mario con ayuda de Claude; primera medida como línea base | Borrador, pendiente de revisión |
| [TRAVEL-013](tickets/TRAVEL-013-plan-cerrado.md) | 6 | Código | Estrategia «plan cerrado» (`flujo.py` del tema 7 S3): el modelo propone un `Plan` con `Literal`, el código lo valida, obliga a consultar si la pregunta nombra un id y enruta; plan por reglas si falla. Solo datos (documentos en la fase 8), todo por text2sql. Misma firma que tool calling y comparación con el examen de TRAVEL-012. Cierra la fase 6 | Borrador, pendiente de revisión |

**Evaluación (TRAVEL-007, TRAVEL-008 y las de fases 6 y 10):** la referencia principal es el **tema 9**
(`../../09_evaluacion_fiabilidad_seguridad/`, sesión 1 en adelante); manda sobre el tema 7 y triage, que solo cubren
lo que el tema 9 no trae.

Al crear un ticket nuevo, **añade su fila** a esta tabla; al cerrarlo, cambia su estado.

## Guías

| Documento | Qué es | Cuándo leerlo |
|---|---|---|
| [`guia-evaluacion-estrategias-agente.md`](guia-evaluacion-estrategias-agente.md) | Cómo comparar estrategias del agente (tool calling, ReAct, plan-and-execute, verificador, razonamiento) y detectar invenciones con un LLM evaluador que **ve la evidencia**. Nace del tema 8, sesión 2, y se amplió con el tema 9, sesión 1 (pass^k, disponibilidad, coste por caso resuelto, normalizar números, calibrar al juez). La sección 8.1 dice qué reutilizar de la evaluación de text2sql (TRAVEL-007) y qué es propio del RAG y del agente. Estado: propuesta, con decisiones abiertas al final | Fases 6 (casos dorados), 8 (evaluación del RAG), 10 (evaluación completa) y 11 (MLflow) |
| [`guia-indices-vectoriales.md`](guia-indices-vectoriales.md) | Guía de estudio de los índices de FAISS (Flat, HNSW, IVF, IVF-PQ) y por qué el RAG usa `IndexFlatIP`. Complementa el tema 5, sesión 4 | Fase 8 (RAG), o si se replantea el índice |

Las decisiones de arquitectura se registrarán como **ADR** en esta carpeta cuando se tomen (lista de pendientes en
`../PROYECTO.md` §10, «Decisiones pendientes»). Todavía no hay ninguno.

## Reglas

- Todo en **castellano**; nombres de código, rutas y comandos tal cual.
- Los tickets siguen la plantilla de `plan-ticket` (`references/TEMPLATE.md`), con los encabezados en castellano.
- No inventes: lo que afirma una guía o un ticket sale de `PROYECTO.md`, del código, del material de clase o de una
  respuesta de Mario. Lo supuesto va marcado como supuesto.
- Este `AGENTS.md` no pasa de 400 líneas (regla del proyecto). Si crece, el detalle va a los propios documentos.
