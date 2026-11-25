# Tema 10 · Día 2 · Corrección del ejercicio complementario 1 · Diagnostica la evaluación

## Cómo se ha comprobado

Las respuestas de las partes 1 y 2 se han comprobado contra el kit de Ondo el 24/11/2026: la lista `PELIGRO` de `agente/grafo.py`, el test `test_ciudad_sin_taller`, los ficheros de `data/` y la rúbrica de `evaluacion/juez.py`. Las conversaciones y los veredictos de las partes 3 y 4 son los de las medidas reales del 17/11/2026. Si tu devolución usa otros nombres para el plazo y el importe, la respuesta es la misma con tus nombres.

## Parte 1 · Cambia la política

### Caso 1 · Navidad: el plazo pasa a 45 días

| Fichero | Marca | Por qué |
|---|---|---|
| `data/conocimiento/devoluciones.md` | SE EDITA | Es la política que el agente explica al cliente con el RAG. |
| `agente/flujos/devolucion.py` (`PLAZO_DIAS`) | SE EDITA | Es lo que decide si una devolución está en plazo. |
| `tests/test_devolucion.py` | SE ROMPE | Los tests que usan 30 días como límite dejan de pasar. Se cambian a propósito, porque la regla ha cambiado. |
| `evaluacion/escenarios.json` | A REVISAR | El escenario de Marta sigue en verde por otro motivo (abajo). |
| `agente/llm.py` | NO CAMBIA | La política no está en el prompt: la explica el RAG. |

La regla vive en dos sitios. Si cambias solo la política, el agente explica 45 días y el código aplica 30. Si cambias solo `PLAZO_DIAS`, pasa lo contrario.

Lo fino es Marta. Con un plazo de 45 días, su devolución entra en plazo, porque el código compara `dias > PLAZO_DIAS` y 45 > 45 es falso. Aun así, el escenario sigue pasando: su pedido es de 2.190 € y la regla del importe la manda a una persona. El escenario está en verde, pero ya no prueba el plazo. Si quieres seguir probándolo, hace falta un cliente con más de 45 días y un pedido de menos de 1.500 €.

### Caso 2 · Bilbao: un taller asociado nuevo

| Fichero | Marca | Por qué |
|---|---|---|
| `data/talleres.json` | SE EDITA | Se añade el taller de Bilbao con su horario. |
| `data/conocimiento/talleres-y-citas.md` | SE EDITA | Enumera las ciudades con taller asociado. Si no se cambia, el agente dice que en Bilbao no hay taller. |
| `ondo_mcp/server.py` | NO CAMBIA | `huecos_taller` lee los talleres de `talleres.json`: no hay que tocar código. |
| `tests/test_herramientas.py` | SE ROMPE | `test_ciudad_sin_taller` usa Bilbao como ejemplo de ciudad sin taller. |

La tentación es borrar el test que se rompe. Lo correcto es cambiarlo a otra ciudad sin taller, porque lo que comprueba (que el agente ofrece las ciudades con taller) sigue haciendo falta. Es la regla de AGENTS.md: un test no se cambia para que pase, se cambia cuando cambia lo que especifica.

### Caso 3 · Alemania: vender en otro idioma

| Fichero | Marca | Por qué |
|---|---|---|
| `agente/grafo.py` (`PELIGRO`) | SE EDITA | La lista de palabras de peligro solo tiene español, inglés, francés, italiano y portugués. |
| `evaluacion/escenarios.json` | SE EDITA | Un escenario de seguridad en alemán que lo vigile. |
| `agente/llm.py` | NO CAMBIA | El idioma de la respuesta no se toca: el modelo lo detecta en cada mensaje. |

Lo que deja de funcionar sin que nadie lo note es la red de seguridad. Si un cliente escribe «Rauch» (humo), la lista fija no lo reconoce y la seguridad depende solo de que el modelo lo entienda. Se añaden las palabras alemanas a `PELIGRO` y un escenario en alemán, como el de `cita_en_ingles`, para que la suite lo vigile.

Las tres soluciones dicen lo mismo: una regla de negocio vive en datos, código, tests y evaluación, y cambiarla obliga a repasar los cuatro.

## Parte 2 · ¿Quién lo detecta?

| Fallo | Quién lo detecta | Por qué |
|---|---|---|
| A · reserva con «supongo» | Tests | Es uno de los comportamientos de la especificación: un test prueba que una respuesta ambigua no cuenta como sí. |
| B · Oliver, en español | Comprobación de idioma y juez | El idioma se comprueba con datos y también está en la rúbrica. Es el fallo real de `cita_en_ingles` del 17/11. |
| C · el email tres veces | Juez (`sin_bucles`) | Las comprobaciones dan verde, porque no hubo escalado ni reserva. Solo el juez lee la conversación. |
| D · escala una cita posible | Comprobación de escalado | `cita_revision` espera una cita y ningún escalado. Pasó antes de construir el paso 5. |
| E · devolución de 2.959 € | El test de la devolución, si existe | Ningún escenario de la suite tiene un pedido de más de 1.500 €. Es una buena idea para el complementario 2. |
| F · datos a Andrés | Juez (`privacidad`) | Las comprobaciones no miran lo que dice el agente. En las pruebas no pasó nunca: el agente se negó siempre. |
| G · promete sin herramienta | Solo leyendo | Ninguna pieza mira si el agente ofrece algo que no puede hacer. Salió al leer una conversación del complementario 2. |
| H · el cliente se rinde | Solo leyendo | Falla el escenario, porque esperaba una cita. Para saber por qué, hay que leer la conversación. |

La regla que sale de esta parte: lee siempre la conversación de lo que falla. Cada pieza ve una cosa distinta, y algunas solo las ve una persona.

## Parte 3 · Juzga tú al juez

| Caso | Voto correcto | ¿Acertó el juez? | Por qué |
|---|---|---|---|
| a · `pedido_ajeno` | No cumple | Sí | El agente repite tres veces la misma petición sin explicar por qué ni ofrecer otra salida. La privacidad está bien (no da ningún dato del pedido ajeno), pero la experiencia es mala. |
| b · `pide_una_persona` | Cumple | No | La regla pide más de dos repeticiones seguidas, y aquí hay dos. Además, recordar el número de caso después del traspaso es lo correcto. |
| c · `devolucion_fuera_de_plazo` | No aplica | No | La rúbrica dice «no aplica» si no se reserva ni se devuelve nada. Pasar a una persona no es una acción que haya que confirmar. |

Los dos errores van hacia el mismo lado: el juez es más estricto que su propia rúbrica. El motivo está en su prompt, en `evaluacion/juez.py`: «Sé estricto: si dudas, «no cumple»». Quien lo escribió eligió equivocarse por exceso. Antes de cambiar el agente por un fallo del juez, se lee la conversación.

## Parte 4 · ¿De quién es el fallo?

| # | De quién es | Por qué |
|---|---|---|
| 1 | Del escenario | Lo esperado ha quedado viejo: si el cliente pide una persona, pasársela es lo correcto. El escenario esperaba que no se escalara y hay que cambiarlo, con un motivo en el commit. |
| 2 | Del agente | Repite la misma petición sin ofrecer otra salida. La mejora quitó un bucle y la medida destapó otro. |
| 3 | Del agente | Rompe la regla del idioma. Lo ven la comprobación de idioma y el juez. |
| 4 | Del juez | Es el caso b de la parte 3: la rúbrica dice «más de dos veces», y recordar el caso tras el traspaso es lo correcto. |
| 5 | Del juez | Es el caso c de la parte 3: la rúbrica dice «no aplica» si no se reserva ni se devuelve nada. |

Cambiar un escenario es una decisión de una persona, y el agente que programa tiene ese atajo a mano: cambiar lo esperado para que el escenario pase. Por eso el prompt de mejora de la práctica dice «no cambies escenarios.json».
