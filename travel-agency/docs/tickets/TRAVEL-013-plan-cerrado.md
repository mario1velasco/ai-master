# TRAVEL-013 · Estrategia «plan cerrado» del agente y comparación con tool calling

> **Nombres en el código, en inglés:** funciones, clases, variables, constantes, parámetros, archivos, campos del
> `Plan` y opciones del comando. Solo los comentarios, la documentación y el texto que lee el modelo (instrucciones
> del planificador y del redactor) van en castellano.

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`agent/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-16 |
| Etiquetas | agent, estrategias, evaluación, fase-6 |

## Historia de usuario

**Como** responsable del asistente de Viajes Nimbo, **quiero** una segunda estrategia del agente en la que el modelo
solo propone un plan cerrado y el código decide los pasos, medida con el mismo examen que tool calling, **para que**
la elección de estrategia se apoye en cifras (pass^3, ataques, coste y latencia) y no en la intuición.

## Contexto

El agente de TRAVEL-006 usa tool calling: el modelo decide si llama a `query_db`, cuántas veces y con qué pregunta.
Por eso puede contestar sin consultar o dar vueltas de más (el fallo que TRAVEL-012 vigila con `expected_tools`). En
el tema 7, sesión 3, `flujo.py` hace lo contrario: el modelo propone un `Plan` con opciones `Literal`, el código lo
valida, lo corrige y enruta, y si el plan no vale usa reglas. Es el punto 2 de «Lo que queda de la fase 6» en
TRAVEL-006 y la estrategia C de `docs/guia-evaluacion-estrategias-agente.md`. Decidido con Mario el 2026-11-16: se
hace **ahora, solo con datos** (en la fase 8 se añade la tarea de documentos) y **todo por text2sql** (sin consultas
fijas), para que la comparación con tool calling sea limpia.

**Referencias leídas:**
- `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/asistente/flujo.py` (`Plan` con `Literal` y
  `Field(description=…)`, `plan_por_reglas`, `planificar` con `formato=Plan.model_json_schema()` y caída a reglas
  ante `ValidationError` o `ErrorComponente`, corrección del plan por el código, `enrutar` en orden fijo, `_paso` y
  `traza` con el origen del plan).
- `08_ia_agentica_automatiz_agentes/tema8-agentes/sesion2/comparar_estrategias.py` (`ESTRATEGIAS` con la misma firma)
  y `plan_and_execute.py` (planificador → ejecutor → sintetizador; el plan es visible antes de ejecutar).
- `docs/guia-evaluacion-estrategias-agente.md` §2 (estrategias), §6 (banco de pruebas) y §7 (cómo se decide qué
  estrategia gana).
- Proyecto: `agent/src/agent/{respond.py, graph.py, tools.py}`, `agent/AGENTS.md`, TRAVEL-006 («Lo que queda de la
  fase 6»), TRAVEL-011 (guardarraíles) y TRAVEL-012 (examen, `--no-guardrails`, resultados guardados).

**Desvíos respecto al patrón de clase:**
- **Una sola tarea (`data`)**: en `flujo.py` hay `imagen`, `cifras` y `documentos`. Aquí solo hay base de datos hasta
  la fase 8, que añadirá `documents`.
- **Sin campo `consulta` ni consultas fijas** (decidido con Mario): el plan escribe la pregunta completa para
  text2sql (`data_question`) y el SQL siempre lo genera text2sql.
- **Sin `contrastar` ni `verificar`**: el verificador de `flujo.py` es el detector de alucinaciones, que Mario dejó
  como opcional en la fase 8.
- **Misma firma que tool calling**: una opción de estrategia en `respond()` y el mismo `AgentAnswer`, como el
  diccionario `ESTRATEGIAS` de `comparar_estrategias.py`. En `flujo.py` el resultado es un `Estado` propio.
- **El origen del plan va a la telemetría** (evento `agent.respond`), no a una `traza` en el estado.
- **Corrección del plan por ids**: la regla de `flujo.py` («un pedido en la pregunta, se consulta») aplicada a los
  ids de Viajes Nimbo (reserva, cliente, código de vuelo).

## Alcance

**Dentro**
- Estrategia `closed_plan`: planificar (modelo con formato fijo) → enrutar (código) → consultar datos (text2sql, con
  los guardarraíles de TRAVEL-011) → redactar (modelo).
- Plan por reglas cuando el del modelo no vale o Ollama falla al planificar.
- Opción de estrategia en `respond()`, en `python -m agent` y en `python -m agent.evaluation`.
- Medida de la batería de TRAVEL-012 con las dos estrategias y comparación en `agent/AGENTS.md`.

**Fuera**
- Tarea de documentos y preguntas mixtas: fase 8.
- Consultas fijas sin LLM para las preguntas frecuentes.
- Verificador o detector de alucinaciones: opcional en la fase 8.
- Las estrategias B (ReAct), D (verificador) y E (razonamiento) de la guía.
- Un enrutador que elija estrategia por tipo de pregunta (guía §7, punto 4).
- Elegir la estrategia por defecto del proyecto: se decide con Mario a la vista de la comparación.

## Criterios de aceptación

Salvo que se diga otra cosa, los tests usan el modelo falso de `agent/tests/`, los datos de `database/fixtures/`, la
sesión de C-001 (reserva R-1042) y los guardarraíles encendidos.

### Camino feliz

**AC-1 — Una pregunta de datos sigue el plan**
- **Dado** la estrategia `closed_plan`
- **Cuando** el cliente pregunta «¿A qué hora sale mi vuelo de la R-1042?» y el modelo propone
  `{"tasks": ["data"], "data_question": "¿A qué hora sale el vuelo de ida de la reserva R-1042?", "reason": "…"}`
- **Entonces** text2sql recibe esa `data_question`
- **Y** la respuesta se redacta con sus filas y trae sus fuentes

**AC-2 — Una pregunta sin datos no consulta**
- **Dado** la estrategia `closed_plan`
- **Cuando** el cliente escribe «Hola, ¿qué tal?» y el modelo propone `{"tasks": []}`
- **Entonces** text2sql no se llama
- **Y** `answered_without_data` es `true`

**AC-3 — Como mucho dos llamadas al modelo del agente**
- **Dado** la estrategia `closed_plan` y un plan con la tarea `data`
- **Cuando** se responde
- **Entonces** el agente hace exactamente una llamada al modelo para planificar y una para redactar (sin contar las
  de text2sql)

### Casos límite

**AC-4 — El código obliga a consultar si la pregunta nombra un id**
- **Dado** una pregunta que contiene `R-1042`, `C-001` o un código de vuelo
- **Cuando** el modelo propone `{"tasks": []}`
- **Entonces** el código añade la tarea `data` y text2sql se llama con la pregunta del cliente
- **Y** la telemetría anota el motivo («la pregunta nombra un id: se consulta»)

**AC-5 — Un plan inválido cae en las reglas**
- **Dado** que el modelo devuelve un JSON que no cumple el `Plan` (una tarea que no existe, o texto suelto)
- **Cuando** se planifica
- **Entonces** se usa el plan por reglas (palabras clave e ids) y se responde igual
- **Y** la telemetría dice que el plan es `rules`, con el motivo

**AC-6 — El origen del plan queda en la telemetría**
- **Dado** cualquier pregunta con la estrategia `closed_plan`
- **Cuando** se responde
- **Entonces** el evento `agent.respond` trae la estrategia, el origen del plan (`model` o `rules`) y sus tareas

### Errores

**AC-7 — Si Ollama falla al planificar, se usan las reglas**
- **Dado** que Ollama no responde en la llamada de planificar
- **Cuando** se planifica
- **Entonces** se usa el plan por reglas y el turno sigue
- **Y** si Ollama tampoco responde al redactar, sale el mismo `ComponentError` que con tool calling

### No funcionales

**AC-8 — Los guardarraíles valen igual (regresión de TRAVEL-011)**
- **Dado** la estrategia `closed_plan`
- **Cuando** la `data_question` del plan nombra la reserva R-1043 (de C-004)
- **Entonces** text2sql no se llama y queda un bloqueo de tipo `tool`, igual que con tool calling

**AC-9 — Tool calling no cambia (regresión)**
- **Dado** la estrategia por defecto, `tool_calling`
- **Cuando** se ejecutan los tests de TRAVEL-006, TRAVEL-011 y TRAVEL-012
- **Entonces** siguen en verde

**AC-10 — El examen elige la estrategia y lo guarda**
- **Dado** el examen de TRAVEL-012
- **Cuando** se lanza con `--strategy closed_plan`
- **Entonces** el agente usa el plan cerrado
- **Y** el JSON de resultados dice `strategy: closed_plan`

**AC-11 — Las dos estrategias se comparan con el mismo examen**
- **Dado** la batería medida con k = 3 en las dos estrategias, con guardarraíles
- **Cuando** Claude escribe la comparación en `agent/AGENTS.md`
- **Entonces** la tabla sigue el orden de la guía §7: filtro duro (ataques superados = 0), calidad (pass^3), coste y
  latencia
- **Y** dice qué estrategia gana en cada categoría de caso

## Definición de hecho

- [ ] AC-1 a AC-10 cubiertos por tests automáticos en verde (sin Ollama); AC-11 comprobado con los archivos de
      resultados y revisión
- [ ] Toda la suite del proyecto en verde (`uv run pytest`)
- [ ] `uv run ruff check .`, `uv run ruff format .` y `uv run ty check` en verde
- [ ] `agent/AGENTS.md` (estrategias, opción `--strategy`, desvíos, comparación), fila 6 de `travel-agency/AGENTS.md`
      (fase 6 cerrada si la medida está hecha), `README.md` y fila de este ticket en `docs/AGENTS.md`
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- Nombres: `strategy` con `"tool_calling"` (por defecto, la línea base) y `"closed_plan"`; `--strategy` en
  `python -m agent` y en `python -m agent.evaluation`.
- El `Plan`: `tasks: list[Literal["data"]]`, `data_question: str` (la pregunta completa para text2sql, con los ids)
  y `reason: str`. En la fase 8 se añade `"documents"`.
- El modelo devuelve el plan con `format` (el esquema JSON del `Plan`), como `planificar` de `flujo.py`.
- Las reglas del plan B (palabras clave e ids) se escriben al desarrollar y se enseñan a Mario antes del código.
- El redactor recibe las mismas reglas que el agente de tool calling («consulta los datos y nunca los inventes», «si
  el dato no existe, dilo», el cliente identificado).
- El examen final reservado de TRAVEL-012 solo se pasa con la estrategia que gane en la batería.
- Depende de TRAVEL-011 (guardarraíles) y TRAVEL-012 (examen); va después de los dos.

**Preguntas abiertas**
- Ninguna.

## Nota del 2026-11-28 (revisión de TRAVEL-012 con Mario)

TRAVEL-012 hace ahora todo el ciclo del agente de tool calling: antes → intermedio → después, con mejoras FIX01… y
la medida final con el examen reservado (AC-24 a AC-26). Este ticket parte de lo que deje:
- **La lista «lo que el agente libre no resuelve»** (AC-25 de TRAVEL-012): los fallos que quedan tras los FIX,
  sobre todo errores silenciosos de text2sql. Es lo que el plan cerrado tiene que mejorar.
- **La medida «después» de TRAVEL-012** es la línea base con la que se compara `closed_plan`, en la batería.
- El supuesto «el examen final solo se pasa con la estrategia que gane» cambia: el final ya se pasa una vez con
  tool calling en TRAVEL-012. Al revisar este ticket se decide si `closed_plan` lo pasa también (una sola vez, al
  final) o si hace falta otro examen reservado.
