# Tema 10 · Día 1 · Ejercicio complementario 1 · Sé el grafo

## Contexto

En clase hiciste de grafo con tres casos: leíste un mensaje, decidiste por qué nodos pasaba y qué cambiaba en el estado. Este ejercicio repite el juego con ocho casos del agente de Ondo. Se hace en papel, sin ejecutar nada: todo lo que necesitas para predecir el camino está en este apartado.

### El grafo

Cada mensaje del cliente recorre el grafo de arriba abajo. Todos los caminos terminan en `redactar`, que escribe la respuesta con el tono y el idioma del cliente.

<!-- imagen: diagrama del grafo (página 1). Su texto no se extrae porque es una imagen -->

### Qué hace cada nodo

| Nodo | Qué hace | Herramienta que usa |
|---|---|---|
| `interpretar` | Un modelo lee el mensaje y saca la intención y los datos (email, número de pedido, ciudad, idioma). Además, una lista fija de palabras de peligro (humo, quemado, fuego, se calienta, no frena…) marca el mensaje como seguridad aunque el modelo no lo vea | Ninguna |
| `reparar` | Responde cuando no se entiende al cliente. Cambia de estrategia en cada intento: primero pide que lo cuente de otra forma, después que elija una opción. Al tercer intento seguido pasa a una persona | Ninguna |
| `identificar` | Pide el email de compra y busca al cliente. Si el email no existe, lo vuelve a pedir; al tercer email fallido pasa a una persona | `buscar_cliente` |
| `flujo` | Lleva el pedido, la devolución o la cita paso a paso. En esta versión del agente, el flujo de pedido da el estado del pedido y el de devolución todavía no está hecho: pasa cualquier devolución a una persona | `estado_pedido` en el flujo de pedido; `huecos_taller` en el de cita |
| `informar` | Busca en la política de Ondo y responde solo con lo que encuentra. Si no encuentra nada fiable, lo dice y ofrece una persona | `buscar_conocimiento` |
| `saludar` | Saluda, recuerda que es el asistente virtual de Ondo (una IA) y ofrece lo que sabe hacer | Ninguna |
| `escalar` | Abre un caso para una persona del equipo con un resumen de la conversación. Si es de seguridad, con prioridad urgente y con instrucciones de seguridad para el cliente | `escalar_a_humano` |
| `ya_escalado` | Recuerda al cliente que su caso ya está en manos de una persona y le da el número de caso | Ninguna |
| `redactar` | Escribe la respuesta final a partir de lo que decidió el nodo anterior | Ninguna |

### Cómo elige camino \`interpretar\`

Después de interpretar el mensaje, el agente comprueba estas reglas en orden. La primera que se cumple decide:

1. Si el mensaje es de seguridad, va a `escalar`.
2. Si ya hay un caso escalado en esta conversación, va a `ya_escalado`.
3. Si el cliente pide hablar con una persona, va a `escalar`.
4. Si no se ha entendido el mensaje, va a `reparar`. Hay una excepción: si un flujo estaba esperando un dato de un cliente ya identificado, lo repara el propio flujo.
5. Si la intención en curso es un pedido, una devolución o una cita, va a `flujo` cuando el cliente ya está identificado y a `identificar` cuando no.
6. Si es una pregunta sobre la política de Ondo, va a `informar`.
7. En cualquier otro caso (un saludo, un agradecimiento), va a `saludar`.

Cuando el cliente contesta a algo que le pidió el agente (un email, un botón), la intención en curso no cambia: el agente sigue con lo que estaba haciendo.

### Lo que guarda el estado

Entre un mensaje y el siguiente, el agente recuerda:

- la intención en curso (pedido, devolución, cita, persona, seguridad o ninguna);
- el dato pendiente, si está esperando uno (por ejemplo, el email o el hueco de la cita);
- el cliente identificado, si ya lo está;
- los intentos fallidos seguidos;
- el caso escalado, si ya se ha abierto uno.

## Los casos

Son cuatro conversaciones. Los mensajes van en este orden y, dentro de cada conversación, el agente recuerda lo anterior. Una conversación nueva empieza con el estado vacío.
| Caso | Conversación | Mensaje del cliente |
|---|---|---|
| 1 | A (nueva) | `Hola` |
| 2 | A | `¿Dónde está mi pedido OND-10231?` |
| 3 | A | `lucia.martin@example.com` |
| 4 | A | `Quiero devolver la bici, no me convence` |
| 5 | A | `¿Y cuánto tardarán en llamarme?` |
| 6 | B (nueva) | `asdf`, después `qwerty`, después `zzz` (tres mensajes; predice los tres) |
| 7 | C (nueva) | Primero `Quiero cita en el taller`, `lucia.martin@example.com`, el botón Revisión y el botón Madrid. Cuando el agente enseña los huecos libres: `Sin prisa: la batería huele un poco a quemado al cargar` |
| 8 | D (nueva) | `¿Cuánto dura la garantía de la batería?` |

`lucia.martin@example.com` es una clienta de Ondo, y el pedido OND-10231 es suyo.

## Tabla a completar

Para cada caso, escribe el camino (los nodos por los que pasa el mensaje, en orden), las herramientas que se llaman y lo que cambia en el estado. El caso 6 ocupa tres filas, una por mensaje. En el caso 7, solo el último mensaje.

| Caso | Mensaje | Camino | Herramientas | Qué cambia en el estado |
|---|---|---|---|---|
| 1 | `Hola` | | | |
| 2 | `¿Dónde está mi pedido OND-10231?` | | | |
| 3 | `lucia.martin@example.com` | | | |
| 4 | `Quiero devolver la bici, no me convence` | | | |
| 5 | `¿Y cuánto tardarán en llamarme?` | | | |
| 6a | `asdf` | | | |
| 6b | `qwerty` | | | |
| 6c | `zzz` | | | |
| 7 | `Sin prisa: la batería huele un poco a quemado al cargar` | | | |
| 8 | `¿Cuánto dura la garantía de la batería?` | | | |

## Entrega

- No es necesario entregar ningún documento.
- La actividad se comentará al inicio de la clase del día siguiente.
- Se entregará una posible corrección en los materiales de los alumnos.
