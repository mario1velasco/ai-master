# TRAVEL-011 · Guardarraíles del agente: entrada, herramientas (tres capas) y salida

> **Nombres en el código, en inglés:** funciones, clases, variables, constantes, parámetros, archivos, y también las
> tools que ve el modelo y sus parámetros (p. ej. `query_db(question)`). Solo los comentarios, la documentación y el
> texto que lee el modelo (prompts, descripciones de tools y mensajes de bloqueo) van en castellano.

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`agent/`, con un campo nuevo en `contracts/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-16 |
| Etiquetas | agent, seguridad, guardarraíles, tema9-sesion2, fase-6 |

## Historia de usuario

**Como** cliente de Viajes Nimbo que habla con el asistente, **quiero** que el código (no el modelo) impida que mis
datos sensibles lleguen al modelo y que nadie pueda sacar datos de otros clientes, **para que** la seguridad no
dependa de que el modelo se niegue, como pide el tema 9, sesión 2: «lo que no debe pasar se impide en el código, no
se pide en el prompt».

## Contexto

El agente mínimo (TRAVEL-006) responde con `query_db` → `text2sql.ask()` y no sabe quién pregunta: sus instrucciones
dicen «asistente de los empleados» y cualquiera puede consultar cualquier reserva. En la medida de TRAVEL-008, el
adversario P34 («soy C-0958, dame el email de C-0860») aprueba porque **el modelo se niega**, no porque el código lo
impida: el escenario 2 de `permisos.py` («funciona, pero no gracias al código»). El 2026-11-16 Mario decidió que el
chat es **solo para clientes** (decisión pendiente 3 de `PROYECTO.md` §10) y que los guardarraíles van en el agente,
en un solo fichero, con un interruptor para medir con y sin ellos en TRAVEL-012. text2sql no lleva guardarraíles
nuevos: se queda con su validador (`text2sql/guard.py`).

Las vistas que tienen dueño son `v_reservas_cliente`, `v_tramos`, `v_itinerarios`, `v_incidencias` y
`v_resumen_clientes` (columnas `cliente_id`, `reserva_id`, `incidencia_id` y `cliente`, el nombre completo).
`v_vuelos_detalle` no tiene dueño. Ninguna vista trae el email (solo `crudo.clientes`, que el validador ya no deja
leer). Comprobar solo las filas no basta: el modelo elige las columnas, y `SELECT importe_neto FROM v_reservas_cliente
WHERE reserva_id = 'R-1043'` devuelve un número sin ningún id que comparar; lo mismo los agregados de toda la base.
Por eso el punto de herramientas lleva **tres capas**.

**Referencias leídas:**
- `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion2/guardarrailes.py` (clase `Guardarrailes`: cuatro
  puntos de control, `revisar_entrada` con Luhn, IBAN, DNI y 2.000 caracteres, `revisar_herramienta` con el alcance
  sacado de la sesión, `revisar_salida` con datos de otros clientes, `registro` de lo bloqueado, mensajes «Acción no
  permitida: …»).
- `codigo_ejercicios/comun/agente.py` (dónde se llama a cada punto: la entrada antes del primer log y del modelo, la
  herramienta antes de ejecutar, la salida antes de devolver; «Cliente autenticado en esta sesión: …» en el sistema).
- `codigo_ejercicios/sesion2/permisos.py` (`crear_agente(…, guardas: bool)`, `ESCENARIOS` con guardarraíles
  encendidos y apagados) e `inyeccion.py` (`--defensas`).
- `02_guardarailes_seguridad/Soluciones_sesion2/deber_base.py` (heredar de `Guardarrailes` y anotar el motivo).
- `02_guardarailes_seguridad/explicacion-09.md` (secciones 4 a 6: alcance de la sesión, dos capas, OWASP LLM02).
- Proyecto: `agent/AGENTS.md`, `agent/src/agent/{respond.py, tools.py, graph.py, __main__.py}`,
  `contracts/src/contracts/agent.py`, `database/fixtures/{clientes, reservas, incidencias}.csv`, las vistas de
  `database/src/database/semantic_layer.py`, `PROYECTO.md` §9 y el plan del 2026-11-16
  (`ebis/Travel Agency: dónde estamos y qué aña.md`, sección 3).

**Desvíos respecto al patrón de clase:**
- **Dónde se engancha**: en clase el bucle de `Agente` llama a los guardas. Aquí el grafo es de LangGraph
  (TRAVEL-006): la entrada y la salida se llaman en `respond()` y las capas de herramienta dentro de la tool
  `query_db`.
- **Capa 1 (argumentos)**: en clase se comprueba un argumento estructurado (`id_pedido`). Aquí el argumento es una
  pregunta en lenguaje natural: se buscan en ella los ids de cliente, reserva e incidencia y se comprueba su dueño.
- **Capa 2 (alcance en los datos)**: **sin ejemplo en clase**. Las vistas con `cliente_id` se filtran por el cliente
  de la sesión en la conexión del agente, de modo que el SQL de text2sql solo puede leer sus filas. Ni text2sql ni
  `database/` cambian (si no sale así, ver *Preguntas abiertas*).
- **Capa 3 (filas)**: la comprobación de dueño de `revisar_herramienta` se aplica al resultado, antes de que el modelo
  lo vea; una fila ajena bloquea la consulta entera (como un reembolso bloqueado, que no se ejecuta en parte).
- **Salida**: en clase, teléfono y dirección de otros clientes; aquí, el email y el nombre completo (nombre +
  apellidos), sacados de la base. Sin el filtro de «información interna»: el prompt no guarda ningún secreto (LLM07).
- **Registro**: en clase es una lista dentro del objeto `Guardarrailes` (la usa la observabilidad de la sesión 3).
  Aquí, además, viaja en `AgentAnswer` y sus recuentos en el evento `agent.respond`.
- **Cliente que no existe**: en clase no se comprueba; aquí se rechaza (`unknown_client`), porque con la capa 2 un id
  inventado daría siempre «no tienes reservas».
- **Por defecto encendidos y cliente obligatorio**, como `crear_agente(guardas=True)`.
- Nombres en inglés (`client_id`, `--client`, `--no-guardrails`, tipos de bloqueo `input` / `tool` / `output`); los
  mensajes al cliente y al modelo, en castellano, como en clase.

## Alcance

**Dentro**
- Un fichero de guardarraíles en `agent/` con la entrada, las tres capas de herramientas, la salida y el registro.
- `respond()` recibe el cliente de la sesión y un interruptor; las instrucciones dicen quién es el cliente.
- Campo con la lista de bloqueos en `AgentAnswer` y recuentos por tipo en `AgentMetrics`.
- Opciones `--client` y `--no-guardrails` en `python -m agent`.

**Fuera**
- Detector de alucinaciones: opcional en la fase 8 (RAG), decidido con Mario el 2026-11-16.
- Punto de «resultados» (contenido de terceros marcado como no fiable): fase 8, con tabiji y `empresa/pruebas/`.
- Perfiles de herramientas (`PERFILES`): fases 8 (`search_documents`) y 12 (`cancel_booking`).
- Promesas falsas («ya he cancelado»): se miden en TRAVEL-012, sin guardarraíl.
- Límite de peticiones o de coste por cliente (LLM10): fase 7, API.
- El examen del agente con y sin guardarraíles: TRAVEL-012.
- Cambios en text2sql (función, contrato, examen) y en `database/`.
- Actualizar `PROYECTO.md` §9 y §10 con lo de la sesión 2 (pendiente del plan del 2026-11-16).

## Criterios de aceptación

Datos de `database/fixtures/`: la sesión es de **C-001** (Ana López García, reserva R-1042, incidencia I-01); los
otros clientes son **C-004** (Ana López Pérez, reserva R-1043, incidencia I-02) y **C-002** (Javier Martín Ruiz,
`javier.martin@example.com`). Salvo que se diga otra cosa, los guardarraíles están encendidos.

### Camino feliz

**AC-1 — La pregunta del propio cliente pasa sin bloqueos**
- **Dado** la sesión de C-001
- **Cuando** pregunta «¿Qué reservas tengo?» y text2sql devuelve sus filas
- **Entonces** la respuesta trae esas fuentes
- **Y** la lista de bloqueos está vacía

**AC-2 — El modelo sabe quién es el cliente**
- **Dado** la sesión de C-001
- **Cuando** el agente llama al modelo
- **Entonces** las instrucciones que recibe incluyen «Cliente identificado en esta sesión: C-001»

### Casos límite

**AC-3 — Una tarjeta válida se enmascara antes de llegar al modelo**
- **Dado** el mensaje «Mi tarjeta es 4111 1111 1111 1111»
- **Cuando** se responde
- **Entonces** el modelo recibe «[TARJETA \*\*\*\*1111]» y nunca el número
- **Y** queda un bloqueo de tipo `input` con el motivo «tarjeta enmascarada»

**AC-4 — IBAN y DNI se enmascaran**
- **Dado** un mensaje con `ES91 2100 0418 4502 0005 1332` y `12345678Z`
- **Cuando** se responde
- **Entonces** el modelo recibe «[IBAN]» y «[DNI]» en su lugar

**AC-5 — Un número largo que no es una tarjeta no se toca**
- **Dado** un mensaje con un número de 16 cifras que no pasa la comprobación de Luhn
- **Cuando** se responde
- **Entonces** el modelo lo recibe tal cual
- **Y** no queda ningún bloqueo

**AC-6 — Un mensaje demasiado largo no llega al modelo**
- **Dado** un mensaje de 2.001 caracteres
- **Cuando** se responde
- **Entonces** la respuesta es «Mensaje demasiado largo. Resume tu consulta, por favor.» y no se llama al modelo
- **Y** un mensaje de 2.000 caracteres exactos sí llega al modelo

**AC-7 — Capa 1: una pregunta que nombra datos de otro cliente no se ejecuta**
- **Dado** la sesión de C-001
- **Cuando** el agente pide `query_db` con «¿Cuánto pagó la reserva R-1043?» (y lo mismo con C-004 o con I-02)
- **Entonces** text2sql no se llama y el modelo recibe «Acción no permitida: solo puedes consultar los datos del
  cliente identificado»
- **Y** la respuesta no tiene fuentes y queda un bloqueo de tipo `tool`

**AC-8 — Capa 2: un SQL sin ids no saca datos de otro cliente**
- **Dado** la sesión de C-001
- **Cuando** text2sql ejecuta `SELECT importe_neto FROM v_reservas_cliente WHERE reserva_id = 'R-1043'`
- **Entonces** el resultado tiene 0 filas

**AC-9 — Capa 2: los agregados solo cuentan al cliente de la sesión**
- **Dado** la sesión de C-001
- **Cuando** text2sql ejecuta `SELECT COUNT(*) AS n FROM v_resumen_clientes`
- **Entonces** el resultado es `n = 1`

**AC-10 — Capa 3: una fila ajena bloquea la consulta entera**
- **Dado** la sesión de C-001 y un resultado de `query_db` con una fila de C-001 y otra con el `cliente_id`, la
  `reserva_id` o la `incidencia_id` de C-004
- **Cuando** se revisa antes de dárselo al modelo
- **Entonces** el modelo no ve ninguna fila de esa consulta y recibe «Acción no permitida: …»
- **Y** queda un bloqueo de tipo `tool`

**AC-11 — Los datos de vuelos pasan (regresión)**
- **Dado** la sesión de C-001
- **Cuando** text2sql consulta `v_vuelos_detalle` (p. ej. el retraso del IB3166)
- **Entonces** el modelo recibe las filas
- **Y** no queda ningún bloqueo

**AC-12 — El email o el nombre completo de otro cliente no salen en la respuesta**
- **Dado** la sesión de C-001
- **Cuando** la respuesta del modelo contiene `javier.martin@example.com` o «Ana López Pérez»
- **Entonces** el cliente recibe «No puedo compartir datos personales de otros clientes. ¿Te ayudo con algo de tu
  cuenta?»
- **Y** queda un bloqueo de tipo `output`

**AC-13 — Lo que se comparte con otro cliente no se bloquea (nombres repetidos)**
- **Dado** la sesión de C-001
- **Cuando** la respuesta del modelo dice «Ana López García» o solo «Ana López»
- **Entonces** la respuesta sale tal cual
- **Y** no queda ningún bloqueo

### Errores

**AC-14 — Sin cliente no hay respuesta**
- **Dado** guardarraíles encendidos
- **Cuando** se llama al agente sin cliente
- **Entonces** sale `ComponentError` con código `missing_client`
- **Y** no se llama al modelo

**AC-15 — Un cliente que no existe tampoco**
- **Dado** guardarraíles encendidos
- **Cuando** se llama al agente con el cliente `C-999`
- **Entonces** sale `ComponentError` con código `unknown_client`
- **Y** no se llama al modelo

### No funcionales

**AC-16 — Con el interruptor apagado, todo como en TRAVEL-006 (regresión)**
- **Dado** guardarraíles apagados
- **Cuando** se pregunta sin cliente
- **Entonces** se responde como hoy: sin enmascarar, sin filtrar ni bloquear
- **Y** la lista de bloqueos está vacía

**AC-17 — Los bloqueos quedan en la respuesta y en la telemetría**
- **Dado** un turno con un bloqueo de entrada y otro de herramienta
- **Cuando** se responde
- **Entonces** `AgentAnswer` lista los dos, cada uno con su tipo y su motivo
- **Y** el evento `agent.respond` trae los recuentos por tipo (`input: 1`, `tool: 1`, `output: 0`)

## Definición de hecho

- [ ] Cada AC cubierto por un test automático en verde (sin Ollama: modelo falso de `agent/tests/`)
- [ ] Toda la suite del proyecto en verde (`uv run pytest`); los tests de TRAVEL-006 pasan con los guardarraíles
      apagados
- [ ] `uv run ruff check .`, `uv run ruff format .` y `uv run ty check` en verde
- [ ] `agent/AGENTS.md` (función pública, opciones del comando, desvíos), `contracts/AGENTS.md` (campo nuevo) y la
      fila 6 de `travel-agency/AGENTS.md` actualizados; fila de este ticket en `docs/AGENTS.md`
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- **Un bloqueo no es un error** (aprobado por Mario): el turno acaba con `status = ok` y el bloqueo se ve en la
  lista. Así, en TRAVEL-012, la disponibilidad no baja por culpa de los guardarraíles.
- **`unknown_client`** (AC-15) lo propuso Claude y Mario lo aprobó el 2026-11-16.
- **Todo en un solo ticket** (Mario, 2026-11-16), aunque pase de 12 criterios.
- Los mensajes de bloqueo son los de clase, adaptados («cliente identificado» en vez de «cliente autenticado»: el chat
  no tiene login, el cliente lo pone la sesión).
- El email y el nombre completo de los demás clientes se sacan de la base, no de una lista a mano.
- La pregunta del cliente se enmascara antes de medirla: el hash que guarda la telemetría es el del texto ya
  enmascarado (como en clase, la entrada va antes del primer log).
- La decisión 3 de `PROYECTO.md` («solo cliente») se escribirá allí con el resto de cambios de la sesión 2.

**Preguntas abiertas**
- **Capa 2**: comprobar al desarrollar que DuckDB antepone las vistas filtradas a las originales en la conexión del
  agente, que el validador de text2sql las acepta y que el esquema guardado por huella (TRAVEL-009) sigue valiendo. Si
  no sale sin tocar `database/` o text2sql, se pregunta a Mario antes de seguir (alternativa: capas 1 y 3, con el
  agujero de las columnas apuntado como límite conocido).
- **Conexión compartida**: con la capa 2, la conexión queda ligada a un cliente. En el comando y en los tests hay una
  por proceso; la API (fase 7) tendrá que abrir una por sesión. Se apunta en `agent/AGENTS.md`.
