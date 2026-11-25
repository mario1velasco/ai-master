# Tema 10 · Día 2 · Corrección del ejercicio complementario 2 · Ampliar la evaluación

Esta es una posible solución. Tus escenarios serán otros, y eso está bien: lo que cuenta es que cada uno pruebe algo que los diez del kit no probaban y que su `esperado` se pueda defender. Los cambios de abajo se aplicaron sobre el kit con la práctica del día 2 terminada y se midieron el 17/11/2026 con la suite completa. No se escribieron con el chat de VS Code: si se lo pides al chat, el resultado tiene que ser equivalente.

## La idea

- Tres escenarios con clientes que no salían en la suite: Irene, que cambia de tema; Nerea, que da el email con una errata y lo corrige; y Elena, enfadada por un pedido con incidencia, que acaba pidiendo que la llame una persona.
- Un criterio nuevo del juez, `salida_a_persona`, que convierte en rúbrica una buena práctica de atención: la salida a una persona tiene que estar a mano cuando el cliente la necesita.
- Medir con los trece escenarios y leer cada fallo para decidir de quién es.

> **[IMAGEN] Una suite que crece.** Prompt para Nano Banana: «Ilustración plana en formato 16:9, fondo blanco, paleta azul marino (#01415B), turquesa (#3298B3) y verde agua (#6ACBB8), con un acento naranja. Una estantería con diez fichas iguales de personajes cliente; una mano coloca tres fichas nuevas de otro color: una persona que gira la cabeza a un lado, una que escribe en un papel con una tachadura y una enfadada con un teléfono. Al lado, un juez con una tablilla añade una casilla nueva a su lista. Sin texto, letras ni logotipos dentro de la imagen.»

## Los tres escenarios

Se añaden al final de la lista de `evaluacion/escenarios.json`:

```json
{
  "id": "cambia_de_tema",
  "cliente": "Irene Soler, irene.soler@example.com. Vive en Barcelona. Su bici (pedido OND-10260) le llegó la semana pasada.",
  "objetivo": "Empieza preguntando si su pedido ya está entregado. Cuando le contestan, cambia de tema: en realidad quiere cita para una revisión en Barcelona. Acepta el primer hueco que le ofrezcan y confirma la reserva.",
  "estilo": "Cercana. Cambia de tema sin avisar, con frases como «ah, por cierto».",
  "idioma": "es",
  "esperado": {"escalado": false, "cita": true, "devolucion": false}
},
{
  "id": "datos_a_trozos",
  "cliente": "Nerea Etxeberria, nerea.etxeberria@example.com. Recibió su pedido OND-10240 hace unos días.",
  "objetivo": "Devolver el pedido porque no es lo que esperaba. Acepta las condiciones y confirma la devolución.",
  "estilo": "Escribe a trozos. El primer mensaje solo dice que quiere devolver algo. Cuando le piden el email, primero lo escribe mal (nerea.etxeberia@example.com) y en el mensaje siguiente lo corrige.",
  "idioma": "es",
  "esperado": {"escalado": false, "cita": false, "devolucion": true}
},
{
  "id": "incidencia_enfadada",
  "cliente": "Elena Navarro, elena.navarro@example.com. Su pedido OND-10236 tiene una incidencia.",
  "objetivo": "Saber qué pasa con su pedido, que no llega. Cuando le expliquen la incidencia, pide que una persona la llame para resolverlo.",
  "estilo": "Enfadada desde el principio, con frases cortas. No acepta explicaciones largas.",
  "idioma": "es",
  "esperado": {"escalado": true, "prioridad": "normal", "cita": false, "devolucion": false}
}
```

Por qué cada `esperado`:

- Irene vive en Barcelona, donde hay taller asociado, y confirma: tiene que haber cita.
- El pedido de Nerea se entregó el 30/10/2026 y cuesta 178 €: dentro de plazo y por debajo de 1.500 €, así que el agente la resuelve solo.
- Elena pide una persona. `AGENTS.md` dice que, si el cliente lo pide, se le pasa, con prioridad normal: no hay riesgo de seguridad.

## El criterio del juez

En `evaluacion/juez.py`, una línea más en la rúbrica y un campo más en la valoración:

```python
RUBRICA = {
    # ... los cinco criterios del kit ...
    "salida_a_persona": "Si el cliente se enfada, pide hablar con alguien o insiste en algo que el asistente no puede "
                        "resolver, el asistente le ofrece pasar con una persona o le pasa directamente. «No aplica» "
                        "si no ocurre nada de eso.",
}


class Valoracion(BaseModel):
    una_pregunta: Criterio
    confirma: Criterio
    privacidad: Criterio
    idioma: Criterio
    sin_bucles: Criterio
    salida_a_persona: Criterio
```

Y en `tests/test_evaluacion.py`, el test que escribiste antes de ampliar la suite falla con diez escenarios y pasa con trece.

## Lo que salió al medir

```
| Escenario | Comprobaciones | Juez | Turnos |
|---|---|---|---|
| pedido_en_camino | ✔ | ✘ sin_bucles, salida_a_persona | 10 |
| pedido_ajeno | ✔ | ✘ sin_bucles, salida_a_persona | 8 |
| cita_revision | ✔ | ✔ | 4 |
| cita_cambia_de_fecha | ✔ | ✔ | 6 |
| cita_cliente_confuso | ✔ | ✘ confirma, sin_bucles | 8 |
| devolucion_dentro_de_plazo | ✔ | ✔ | 4 |
| devolucion_fuera_de_plazo | ✔ | ✘ confirma | 2 |
| seguridad_sin_prisa | ✔ | ✔ | 2 |
| pide_una_persona | ✔ | ✔ | 2 |
| cita_en_ingles | ✔ | ✔ | 5 |
| cambia_de_tema | ✔ | ✔ | 5 |
| datos_a_trozos | ✔ | ✔ | 5 |
| incidencia_enfadada | ✔ | ✘ confirma | 3 |
```

Trece de trece escenarios superados en las comprobaciones, paso a persona correcto en los trece, 4,9 turnos de media y 60 de 68 criterios del juez cumplidos (88 %). Tus números serán algo distintos.

## Los fallos, uno a uno

| Fallo | De quién es | Por qué |
|---|---|---|
| `salida_a_persona` en `pedido_en_camino` y `pedido_ajeno` | Del agente | El cliente insiste (un enlace de seguimiento, un pedido ajeno) y el agente repite su respuesta sin ofrecer una persona. Es el fallo que buscaba el criterio nuevo, y coincide con el bucle que ya marcaba `sin_bucles` |
| `confirma` en `devolucion_fuera_de_plazo` e `incidencia_enfadada` | Del juez | Pasar a una persona no necesita confirmación, y en esas conversaciones no se reserva ni se devuelve nada. La rúbrica dice que entonces «no aplica», pero el juez no lo respeta. Arreglo: escribirlo más claro en la rúbrica («pasar a una persona no es una acción que haya que confirmar») y volver a medir |
| `confirma` y `sin_bucles` en `cita_cliente_confuso` | El primero, del juez; el segundo, del agente | No hubo reserva, así que `confirma` no aplica. El bucle sí es real: el agente pide tres veces que elija un hueco antes de pasar a una persona |

Lo que no marca nadie, y aparece al leer la conversación de Elena: el agente le dice que «necesitamos que nos confirmes o actualices tu dirección», pero no tiene ninguna herramienta para cambiar una dirección. Promete algo que no puede hacer. Es un buen candidato para un sexto criterio del juez («el asistente no ofrece acciones que no puede hacer») o para una regla en el prompt de redacción.

## Errores frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `test_los_escenarios_estan_bien_formados` falla | El test espera trece escenarios y aún no los has añadido, o un email del escenario no existe en los datos | Añade los escenarios que faltan y copia el email de `data/clientes.json` |
| `ValidationError` del juez | Has añadido el criterio a la rúbrica pero no a `Valoracion`, o al revés | Que el nombre sea el mismo en los dos sitios |
| La comprobación `devolucion` falla en un escenario de devolución que debería salir bien | El pedido está fuera de plazo o supera 1.500 €, o no está entregado | Revisa `fecha_entrega`, `total` y `estado` en `data/pedidos.json` |
| El cliente simulado no cambia de tema o no comete la errata | El objetivo o el estilo no lo dicen con claridad | Escribe la acción concreta en el objetivo («cuando le contestan, pide cita») y vuelve a medir solo ese escenario con `--solo` |
| Un escenario pasa y falla en ejecuciones seguidas | El cliente simulado escribe distinto cada vez | Mide dos o tres veces y anota cuántas pasa |
