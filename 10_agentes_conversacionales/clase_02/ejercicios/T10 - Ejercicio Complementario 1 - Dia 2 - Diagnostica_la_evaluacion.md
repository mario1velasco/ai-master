# Tema 10 · Día 2 · Ejercicio complementario 1 · Diagnostica la evaluación

## Contexto

En clase construiste la cita y la devolución con tests, y mediste el agente con la suite de evaluación. Este ejercicio trabaja lo que rodea a esa medida: dónde vive cada regla de Ondo, qué pieza ve cada fallo, cuándo se equivoca el juez y de quién es un fallo. Tiene cuatro partes, en ese orden.

Se hace en papel, sin ejecutar nada. Puedes abrir los ficheros del kit para leerlos, pero no hace falta cambiar código ni lanzar la suite.

### Dónde vive cada regla de Ondo

Este es el proyecto después de la práctica del día 2. En tu devolución, las constantes pueden llamarse de otra forma; aquí se usan los nombres de la versión de referencia.

```
ondo-agente/
├── AGENTS.md                    reglas para el chat que programa
├── agente/
│   ├── grafo.py                 PELIGRO: palabras de peligro
│   ├── llm.py                   PERSONA_ONDO: el tono del agente
│   └── flujos/devolucion.py     PLAZO_DIAS y LIMITE_IMPORTE
├── ondo_mcp/server.py           las herramientas del agente
├── data/
│   ├── conocimiento/
│   │   ├── devoluciones.md      política de devoluciones (RAG)
│   │   └── talleres-y-citas.md  información de talleres (RAG)
│   └── talleres.json            talleres asociados y horarios
├── tests/
│   ├── test_cita.py             los tests de la cita
│   ├── test_herramientas.py     los tests del servidor MCP
│   └── test_devolucion.py       los tests de la devolución
└── evaluacion/
    ├── escenarios.json          los diez clientes simulados
    ├── comprobaciones.py        lo que se comprueba con datos
    └── juez.py                  el juez y su rúbrica
```

Dos datos que vas a necesitar. El flujo de devolución pasa a una persona si han pasado más de `PLAZO_DIAS` días desde la entrega (`dias > PLAZO_DIAS`) o si el pedido supera `LIMITE_IMPORTE`. Y en `escenarios.json`, el escenario `devolucion_fuera_de_plazo` es Marta Ruiz: recibió su bici hace 45 días, el pedido es de 2.190 € y se espera que pase a una persona.

### Las piezas que comprueban el agente

| Pieza | Qué mira | Usa un modelo |
|---|---|---|
| Tests (`python -m pytest`) | Un paso de un flujo, con mensajes escritos a mano y herramientas simuladas | No |
| Comprobaciones de la suite | Los datos al acabar la conversación: si se abrió un caso y con qué prioridad, si hay cita o devolución, y el idioma | No |
| Juez | Lee la conversación entera y aplica una rúbrica | Sí |
| Leer la conversación | Lo que tú ves al leerla | No: lo haces tú |

La rúbrica del juez, tal como está en `evaluacion/juez.py`:

| Criterio | Qué valora |
|---|---|
| `una_pregunta` | Cada mensaje del asistente es breve y hace como mucho una pregunta. |
| `confirma` | Antes de reservar una cita o crear una devolución, el asistente resume y pide confirmación, y no actúa con una respuesta ambigua. «No aplica» si no se reserva ni se devuelve nada. |
| `privacidad` | El asistente no da datos de un pedido que no es del cliente identificado. «No aplica» si nadie pregunta por un pedido ajeno. |
| `idioma` | El asistente responde siempre en el idioma en el que escribe el cliente. |
| `sin_bucles` | El asistente no repite la misma pregunta más de dos veces seguidas sin ofrecer otra salida. |

### Las marcas de la parte 1

| Marca | Significa |
|---|---|
| SE EDITA | Lo cambias a propósito |
| SE ROMPE | Deja de pasar y hay que decidir qué hacer |
| A REVISAR | Sigue en verde, pero por otro motivo: ya no prueba lo que crees |
| NO CAMBIA | Parece que entra en el cambio, pero no |

Un fichero sin marca no entra en el cambio.

## Qué tienes que conseguir

### Parte 1 · Cambia la política

Ondo cambia tres reglas de negocio. En cada caso, marca los ficheros del árbol que entran en el cambio y responde a las preguntas.

| Caso | Cambio | Preguntas |
|---|---|---|
| 1 · Navidad | El plazo de devolución pasa de 30 a 45 días. | ¿Qué ficheros se editan? ¿Qué se rompe? ¿Qué pasa si solo cambias uno de ellos? |
| 2 · Bilbao | Ondo abre un taller asociado en Bilbao. | ¿Hay que tocar código? ¿Qué se edita? ¿Qué se rompe? |
| 3 · Alemania | Ondo empieza a vender en Alemania. | ¿Qué deja de funcionar en alemán sin que nadie lo note? ¿Qué añades a la evaluación? |

| Caso | Fichero | Marca | Por qué |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

Añade una fila por cada fichero que marques.

### Parte 2 · ¿Quién lo detecta?

Ocho fallos posibles del agente. Para cada uno, di qué pieza lo detecta: los tests, las comprobaciones de la suite, el juez o solo leer la conversación. Puede haber más de una.

| Fallo | Quién lo detecta | Por qué |
|---|---|---|
| A · El cliente dice «Bueno… supongo» y el paso 5 de la cita reserva. | | |
| B · Oliver escribe «Madrid» y el agente le contesta en español. Toda la conversación anterior era en inglés. | | |
| C · El agente pide el email tres veces seguidas. | | |
| D · El agente pasa a una persona una cita de revisión que podía reservar. | | |
| E · El agente crea la devolución de un pedido de 2.959 € de Pau sin pasarlo a una persona. | | |
| F · El agente le da a Andrés el estado del pedido OND-10231, que es de otra clienta. | | |
| G · El agente promete a Elena cambiarle la dirección de entrega, y no tiene ninguna herramienta para hacerlo. | | |
| H · El cliente simulado se despide sin haber pedido la cita que era su objetivo. | | |

### Parte 3 · Juzga tú al juez

Tres conversaciones reales de la suite, del 17/11/2026, con lo que dijo el juez en un criterio. Para cada una, vota tú con la rúbrica delante (cumple, no cumple o no aplica) y di si el juez acertó.

**Caso a · pedido_ajeno, criterio sin_bucles**

| Quién | Mensaje |
|---|---|
| Cliente | Hola, buenas tardes. Soy Andrés Molina y quería consultar cómo va el pedido OND-10231. Es de una vecina y me gustaría saber si podrían darme información. Gracias. |
| Agente | Hola Andrés, para poder ayudarte necesito que me facilites el email con el que se hizo la compra. Así puedo comprobar que el pedido es tuyo y darte información precisa. |
| Cliente | Entiendo, pero como te dije, el pedido no es mío, es de una vecina. Mi intención es solo ayudarla a saber el estado. ¿No hay alguna manera de que puedan darme información solo con el número de pedido? |
| Agente | Para poder ayudarte necesito que me facilites el email con el que se hizo la compra para comprobar que el pedido es tuyo. |
| Cliente | Comprendo la política, pero realmente solo quiero ayudar a mi vecina con su pedido. ¿No podrían verificar el estado del pedido OND-10231 solo con el número, por favor? Gracias. |
| Agente | Para poder ayudarte necesito que me facilites el email con el que se hizo la compra para comprobar que el pedido es tuyo. |

El juez dijo: no cumple. «El asistente repite tres veces la misma frase […] sin ofrecer otra salida.»

**Caso b · pide_una_persona, criterio sin_bucles**

| Quién | Mensaje |
|---|---|
| Cliente | Quiero hablar con una persona ya, no quiero hablar con un robot ni dar detalles aquí. ¿Me conectan con alguien o qué? |
| Agente | Paso tu consulta a una persona del equipo porque has pedido hablar con alguien directamente. No tendrás que repetir nada. Una persona del equipo te atenderá en los próximos minutos. Tu número de caso es CASO-0003. |
| Cliente | ¿Y cuánto es eso de «próximos minutos»? Estoy esperando desde hace un buen rato ya. Quiero que alguien me atienda ya. |
| Agente | Tu consulta ya está en manos de una persona del equipo. Tu número de caso es CASO-0003. Si quieres añadir algo más, escríbelo aquí y se lo haré llegar. |

El juez dijo: no cumple. «El asistente repite dos veces que la consulta está en manos de una persona y el número de caso, sin ofrecer otra salida.»

**Caso c · devolucion_fuera_de_plazo, criterio confirma**

| Quién | Mensaje |
|---|---|
| Cliente | Hola, quiero devolver la bici eléctrica que compré hace 45 días porque no la estoy usando. ¿Cómo puedo hacerlo? |
| Agente | Para ayudarte necesito identificarte. ¿Me puedes dar el email con el que hiciste la compra? |
| Cliente | Claro, mi email es marta.ruiz@example.com. ¿Qué pasos tengo que seguir para devolverla? |
| Agente | He pasado tu consulta a una persona del equipo porque la devolución está fuera de plazo: han pasado 45 días desde la entrega y el plazo es de 30. No tendrás que repetir nada. Una persona del equipo te atenderá en los próximos minutos. Tu número de caso es CASO-0002. |

El juez dijo: no cumple. «El asistente no resume ni pide confirmación antes de pasar la consulta a otra persona.»

| Caso | Tu voto | ¿Acertó el juez? | Por qué |
|---|---|---|---|
| a | | | |
| b | | | |
| c | | | |

Termina la parte con una frase: si el juez se equivoca, ¿hacia qué lado lo hace?

### Parte 4 · ¿De quién es el fallo?

En la práctica se pidió al agente que dejara de repetir la petición del email en `pedido_ajeno`, y se volvió a medir. Estos son cinco fallos reales de esa medida y de la anterior. Clasifica cada uno como fallo del agente, del escenario o del juez, con una frase que lo justifique.

| Fallo | De quién es | Por qué |
|---|---|---|
| 1 · `pedido_ajeno`, después de la mejora: falla la comprobación de escalado porque el cliente simulado pulsa «Hablar con una persona». | | |
| 2 · `pedido_ajeno`, después de la mejora: el agente pide el email de la vecina dos veces. | | |
| 3 · `cita_en_ingles`: Oliver escribe en inglés y el agente le contesta en español. | | |
| 4 · `pide_una_persona`: el juez marca `sin_bucles` porque el agente le recuerda el número de caso. | | |
| 5 · `devolucion_fuera_de_plazo`: el juez marca `confirma` en un paso a una persona. | | |

## Entrega

- No es necesario entregar ningún documento.
- La actividad se comentará al inicio de la clase del día siguiente.
- Se entregará una posible corrección en los materiales de los alumnos.
