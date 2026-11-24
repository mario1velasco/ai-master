# Tema 10 · Día 1 · Ejercicio complementario 2 · Diagnostica la conversación

## Contexto

En clase viste las reglas de diseño de una conversación de atención al cliente:

- El asistente dice desde el primer mensaje que es una IA y qué sabe hacer, y no esquiva la pregunta de si es una persona.
- Confirma según el riesgo: una acción con efecto (reservar, devolver) solo se ejecuta con un sí claro, y si la elección del cliente es ambigua, pregunta en vez de suponer.
- Repara cuando no entiende al cliente: cambia de estrategia en cada intento y le da una salida hacia una persona.
- No inventa datos: fechas, códigos, importes y plazos salen de las herramientas o de la política de la empresa.
- Pasa a una persona con contexto: el cliente no repite nada y recibe un número de caso.
- Trata la seguridad como urgente, aunque el cliente diga que no tiene prisa.

Abajo tienes cinco conversaciones de una versión antigua y mal diseñada del asistente de Ondo. Son ficticias, escritas para este ejercicio, y cada una incumple al menos una de esas reglas.

## Qué tienes que conseguir

1. Para cada conversación de la 2 a la 5, completa sus tres apartados. La conversación 1 está resuelta como ejemplo de lo que se espera.
2. Elige dos conversaciones de entre la 1, la 3, la 4 y la 5 y repítelas con el agente real:

   ```
   python -m canales.consola --traza
   ```

Compara lo que hace el agente de Ondo con tu turno reescrito. Si el agente real también falla en algo, dilo y explica por qué.

| Apartado | Qué escribes |
|---|---|
| Reglas que incumple | La regla de diseño que falla (puede ser más de una) y en qué turno |
| Turno reescrito | El turno del asistente como debería ser |
| Qué lo evita | La pieza del agente de Ondo del kit que impide ese fallo (un nodo del grafo, un prompt, una herramienta del servidor MCP o los datos) y en qué fichero está |

No hace falta cambiar ningún fichero.

## Conversación 1

| Quién | Mensaje |
|---|---|
| Cliente | Hola |
| Asistente | ¡Hola! Soy Marta, de Ondo. ¿En qué te ayudo? |
| Cliente | ¿Eres una persona? |
| Asistente | Estoy aquí para ayudarte con lo que necesites. |

### Reglas que incumple

Incumple la regla de decir desde el primer mensaje que es una IA y qué sabe hacer: se presenta con un nombre de persona y no dice en qué puede ayudar. En el segundo turno esquiva la pregunta de si es una persona, y el cliente se queda sin saber con quién habla.

### Turno reescrito

El primer turno sería «¡Hola! Soy el asistente virtual de Ondo, una inteligencia artificial. Puedo decirte dónde está tu pedido, ayudarte con una devolución o darte cita en el taller. ¿Qué necesitas?», con un botón para cada opción. Ante «¿Eres una persona?», respondería «No, soy un asistente virtual. Si prefieres hablar con una persona del equipo, te paso».

### Qué lo evita

El nodo `saludar` de `agente/grafo.py` pide en su borrador que el agente recuerde que es el asistente virtual de Ondo, una IA, y ofrece tres botones con lo que sabe hacer. La respuesta a la pregunta de si es una persona la cubre el prompt de personalidad `PERSONA_ONDO` de `agente/llm.py`, que dice «Eres una inteligencia artificial y lo dices si te preguntan».

## Conversación 2

| Quién | Mensaje |
|---|---|
| Cliente | Quiero cita para revisar la bici en Madrid. Soy javier.ortega@example.com |
| Asistente | Hay hueco el viernes 20/11 a las 09:00, el viernes 20/11 a las 12:00 y el sábado 21/11 a las 10:00. |
| Cliente | el viernes |
| Asistente | Hecho, te he reservado el viernes 20/11 a las 09:00. Tu cita es CIT-0042. |

### Reglas que incumple

### Turno reescrito

### Qué lo evita

## Conversación 3

| Quién | Mensaje |
|---|---|
| Cliente | lo de la cosa |
| Asistente | No te he entendido. ¿Puedes repetirlo? |
| Cliente | pues eso, lo de ayer |
| Asistente | No te he entendido. ¿Puedes repetirlo? |
| Cliente | ya te lo he dicho |
| Asistente | No te he entendido. ¿Puedes repetirlo? |

### Reglas que incumple

### Turno reescrito

### Qué lo evita

## Conversación 4

| Quién | Mensaje |
|---|---|
| Cliente | ¿Qué plazo de devolución tiene Ondo? |
| Asistente | Tienes 60 días desde la compra, y te devolvemos el dinero en 24 horas. |

### Reglas que incumple

### Turno reescrito

### Qué lo evita

## Conversación 5

| Quién | Mensaje |
|---|---|
| Cliente | Sin prisa, pero la batería se calienta mucho al cargar. Soy javier.ortega@example.com, pedido OND-10233. |
| Asistente | Entiendo. Te paso con un compañero. |
| Persona de Ondo | Hola, ¿en qué puedo ayudarte? ¿Me das tu email y tu número de pedido? |

### Reglas que incumple

### Turno reescrito

### Qué lo evita

## Entrega

- No es necesario entregar ningún documento.
- La actividad se comentará al inicio de la clase del día siguiente.
- Se entregará una posible corrección en los materiales de los alumnos.
