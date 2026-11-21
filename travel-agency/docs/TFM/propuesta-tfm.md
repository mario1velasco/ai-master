# Propuesta de TFM: asistente agéntico para una agencia de viajes

**Máster en Ingeniería de Automatización con IA Agéntica (EBIS) · 1LSVER26**
**Alumno:** Mario Velasco Alonso
**Título provisional:** *Viajes Nimbo: un agente que sabe dónde buscar*

---

## 1. Descripción

Voy a construir un **asistente conversacional para los clientes de una agencia de viajes online**, Viajes Nimbo
(ficticia). Los clientes hacen preguntas que necesitan dos tipos de información muy distintos, y el asistente tiene que
saber **dónde buscar** cada una:

| Tipo de pregunta | Ejemplo | Dónde está la respuesta |
|---|---|---|
| Sus datos | «¿Cuántas reservas canceladas tengo este año?» | Base de datos (reservas, vuelos, pagos, incidencias) |
| Normativa y políticas | «¿Qué indemnización corresponde por 4 horas de retraso en un vuelo de 2.000 km?» | Documentos: leyes de la UE, BOE y políticas de la agencia |
| Mixta | «El vuelo de mi reserva R-1042 llegó con 5 horas de retraso, ¿a qué tengo derecho?» | Las dos: la base da el retraso y la distancia; el reglamento, la compensación |

**Cómo funciona.** Un agente hecho con LangGraph recibe la pregunta y decide qué herramienta usar:

```
cliente ──► API (FastAPI) ──► agente (LangGraph)
                                 ├─ query_db          → el modelo escribe SQL → validador → base de datos (DuckDB)
                                 └─ search_documents  → búsqueda híbrida en el corpus (RAG) → pasajes con su cita
                              ◄── respuesta en español, con las fuentes citadas
```

- **Base de datos:** el modelo traduce la pregunta a SQL (*text-to-SQL*) que solo puede leer unas vistas preparadas. Las
  vistas ya hacen los cálculos delicados (retraso a la llegada, distancia del viaje, importe neto) y un validador en
  código rechaza cualquier consulta fuera de las reglas.
- **Documentos (RAG):** búsqueda híbrida (palabras con BM25 + significado con embeddings), fusión de las dos listas y
  reordenación. Cada afirmación normativa va citada; si no hay evidencia, el asistente lo dice.
- **Chat:** API con sesiones que se recuperan aunque se reinicie el servidor y una memoria por cliente («siempre salgo
  desde Madrid») que el cliente puede ver y borrar.

**Todo open source y en local**, sin APIs de pago: Qwen3-4B en Ollama, en un portátil con una GPU de 4 GB. Los datos
de clientes son **sintéticos**, generados por mí. El corpus reúne fuentes oficiales con licencia comprobada (EUR-Lex,
BOE, Ministerio de Sanidad, EASA…) y 26 documentos propios de la agencia (condiciones, cancelaciones, equipaje,
fidelización…), algunos con trampas a propósito: una política derogada, una política que mejora la ley o un documento
con una instrucción inyectada.

## 2. Motivación

- **Un problema real.** El equipo de atención al cliente de una agencia responde cada día preguntas que mezclan los
  datos del cliente con la normativa. Hoy una persona tiene que consultar dos sistemas y conocer la ley; un asistente
  que haga las dos cosas, y diga de dónde lo saca, ahorra trabajo sin perder control.
- **Juntar el máster en un solo sistema.** El proyecto usa lo de casi todos los temas: APIs y FastAPI (temas 3 y 4),
  RAG (tema 5), agentes y MCP (tema 6), modelos open source en local (tema 7), LangGraph, memoria y humano en el bucle
  (tema 8), y evaluación, guardarraíles y observabilidad (tema 9).
- **Hacer fiable un modelo pequeño.** Con un modelo de 4B no basta con un buen prompt: la fiabilidad tiene que estar en
  el diseño. El proyecto se apoya en cuatro principios del máster:
  - *El código calcula, el modelo redacta*: las cifras salen de SQL, no del modelo.
  - *El modelo propone, el código decide*: las barreras están en el código, no en el prompt.
  - *Sin evidencia, abstención*: mejor «no lo sé» que una respuesta inventada.
  - *Los documentos son datos, no instrucciones*: protección frente a la inyección de prompt.
- **Privacidad y coste.** Al ser todo local, ningún dato sale del equipo y el coste por pregunta es cero. Quiero
  comprobar hasta dónde se llega con hardware modesto.

## 3. Objetivos

**Objetivo general:** construir y evaluar un agente que responda a los clientes con sus datos o con la normativa
citada, sin inventar, seguro y medido en cada paso.

**Objetivos específicos** (cada uno con su forma de comprobarlo):

1. **Datos consultables y bien definidos.** Base de datos con una capa semántica (vistas con descripciones) cuyo
   esquema se genera solo para el modelo. *Se comprueba con tests de integridad sobre cifras calculadas a mano.*
2. **Text-to-SQL seguro.** Solo `SELECT`, solo vistas permitidas, con validador y corrección del error.
   *Se mide con un examen de preguntas de cliente, comparando el resultado con el de un SQL de referencia.*
3. **RAG con citas** sobre leyes, guías oficiales y documentos de la agencia, usando la versión vigente de cada
   política. *Se mide con Hit@k (¿está el pasaje correcto entre los primeros?) en cada etapa de la búsqueda.*
4. **Agente que elige bien la herramienta**, combina los resultados y cita, o se abstiene si no hay evidencia.
   *Se mide con casos dorados: solo datos, solo documentos, mixtas y sin respuesta.*
5. **Seguridad.** El chat es solo para clientes identificados y cada uno ve solo sus datos, impuesto en el código.
   Guardarraíles de entrada (enmascarar tarjetas, IBAN y DNI), de herramientas y de salida. *Se comprueba con red
   teaming: ataques del OWASP Top 10 para LLM pasados con y sin defensas; objetivo, 0 ataques superados.*
6. **API con estado y memoria.** Chat que sobrevive a reinicios, resume las conversaciones largas sin perder los
   identificadores y recuerda las preferencias del cliente. *Se comprueba con casos de varios turnos.*
7. **Observabilidad.** Cada paso queda medido: traza con identificador común, tokens, latencia y coste equivalente.
8. **Evaluación completa.** Casos normales, de borde y de ataque, repetidos 3 veces (cuenta como acierto solo si
   acierta las tres), un LLM juez calibrado con etiquetas humanas y unos umbrales para dar el sistema por bueno.

**Extras, si hay tiempo:** visualizar las trazas en MLflow; cancelaciones con aprobación humana según el importe
(subagente con permiso para cancelar, cola de aprobación y registro de auditoría); un servidor MCP para que otros
agentes consulten al asistente; Docker para arrancarlo todo con un comando; y afinar el modelo de SQL (QLoRA) solo si
la evaluación lo justifica.

**Fuera de alcance:** el asistente no crea ni modifica reservas (salvo el extra de cancelaciones), no da información en
tiempo real (precios, estado de vuelos de hoy) y no sustituye el asesoramiento legal: resume y cita.

## 4. Estado actual

El proyecto ya está en marcha y se desarrolla por fases, cada una con algo que funciona y se puede probar:

- **Hecho:** estructura del proyecto; contratos de datos y telemetría; base de datos con generador reproducible;
  corpus reunido (fuentes oficiales y documentos de la agencia); text-to-SQL con validador y su herramienta de
  evaluación; primera versión del agente con LangGraph y la herramienta `query_db`.
- **Siguiente:** primera medida del text-to-SQL con el modelo real, guardarraíles, API, memoria del chat, RAG y
  evaluación completa.
