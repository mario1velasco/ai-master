# Tema 10 · Día 2 · Ejercicio complementario 2 · Ampliar la evaluación

## Contexto

En clase mediste el agente con los diez escenarios del kit. Esos diez los escribió otra persona, con sus propias ideas de lo que puede salir mal. Una suite de evaluación crece con lo que va apareciendo en las conversaciones reales y con las reglas que el negocio da por obligatorias.

Este ejercicio trabaja sobre lo que construiste en clase (paso 5 de la cita y flujo de devolución). Puedes hacerlo con o sin el complementario 1: el aviso por Telegram no cambia lo que mide la suite.

## Qué tienes que conseguir

1. Primero el test, escrito con el chat: que cada escenario tenga los campos obligatorios y un cliente que exista en los datos, y que haya trece escenarios. Ejecútalo con los diez del kit y comprueba que falla. Después, tres escenarios nuevos en `evaluacion/escenarios.json` que cubran situaciones que los diez del kit no cubren. Ideas, por si no se te ocurren otras: el cliente que cambia de tema a mitad de conversación, el que da los datos a trozos o con una errata que corrige después, y el que está enfadado y pide que le llame alguien.
2. Cada escenario con un cliente real de los datos de Ondo que no use ningún otro escenario, un objetivo y un estilo que el cliente simulado pueda seguir sin ambigüedad, y un `esperado` que puedas defender con las reglas de `AGENTS.md`.
3. Un criterio nuevo en el juez (`evaluacion/juez.py`) que convierta una buena práctica de atención en algo que se valora en cada conversación. Por ejemplo: si el cliente se enfada, insiste en algo que el agente no puede resolver o pide hablar con alguien, el agente le ofrece una persona.
4. La suite completa ejecutada con los trece escenarios y el criterio nuevo.
5. Una lista corta de lo que has encontrado: cada fallo, clasificado como fallo del agente, del escenario o del juez, con una frase que lo justifique. Cada fallo del agente que anotes, léelo en la conversación de `conversaciones.json`, además de verlo en la tabla.

## Entrega

- No es necesario entregar ningún documento.
- La actividad se comentará al inicio de la clase del día siguiente.
- Se entregará una posible corrección en los materiales de los alumnos.
