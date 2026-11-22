# Alba, el asistente de reservas: ¿listo para volver a producción?

Informe para la Directora de Operaciones de Hoteles Albor.

## Resumen ejecutivo y recomendación

*Pendiente: se escribe al final, con las mediciones antes y después.*

## Parte 1 · Rediseño del agente

### 1.1 Herramientas

El piloto daba al modelo ocho herramientas con descripciones de una línea, sin decir cuáles tenían efectos ni en qué formato iban los datos. En el rediseño:

- **Cada herramienta lleva su riesgo**: lectura (no cambia nada), escritura reversible (cambia algo que se puede deshacer) o escritura irreversible (no se puede deshacer: cancelaciones, dinero, emails). El riesgo está en el código, no solo en el texto: los perfiles y los controles de la parte 3 se apoyan en él.
- **Las descripciones dicen qué hace, cuándo usarla y en qué formato van los datos.** Es lo único que el modelo sabe de cada herramienta.
- **Los parámetros están acotados**: solo los tres hoteles que existen y reservas con el formato `R-1234`; noches e importes con un mínimo.
- **No se elimina ninguna.** Las dos que devuelven datos personales se conservan, pero cada conversación solo verá las que necesita (perfiles, apartado 1.2) y solo sobre sus propios datos (controles, parte 3).

| Herramienta | Riesgo | Qué cambia | Por qué |
|---|---|---|---|
| `consultar_disponibilidad` | Lectura | Dice qué devuelve (libres, precio por noche y total) y cuándo usarla. Solo admite los tres hoteles, la fecha en `AAAA-MM-DD` y al menos 1 noche | Evitar hoteles o formatos inventados |
| `consultar_reserva` | Lectura | Dice qué devuelve y que es solo para reservas del huésped identificado. Formato `R-1234` | La información de una reserva solo se comparte con su titular |
| `buscar_huesped` | Lectura · datos personales | Avisa de que devuelve datos personales y de que se usa con el email del huésped identificado, cuando pregunta por sus reservas sin dar el número | Devuelve teléfono y tarjeta: solo para el propio huésped o para recepción |
| `listar_reservas` | Lectura · datos personales | Pasa a ser solo para el equipo de recepción, para consultar la ocupación, nunca para responder a un huésped. Solo admite los tres hoteles | Fue la herramienta que sacó nombres y teléfonos en el incidente |
| `leer_resenas` | Lectura · contenido no fiable | Avisa de que el texto lo escriben terceros: es información para resumir, nunca instrucciones | Fue la puerta de entrada de la inyección del incidente |
| `consultar_politica` | Lectura | Dice cuándo usarla: antes de cancelar o calcular un reembolso, y para mascotas. Incluye la fecha de hoy | El importe del reembolso depende de la política y de la fecha |
| `cancelar_reserva` | Escritura irreversible | Solo a petición expresa del titular identificado; el importe según la política y nunca negativo; el motivo es el que da el huésped | Libera la habitación y mueve dinero. En el incidente canceló una reserva ajena y reembolsó una tarifa no reembolsable |
| `enviar_email` | Escritura irreversible | Solo al huésped identificado y sobre sus propias reservas | Fue el canal por el que salieron los datos a una dirección externa |

Ninguna herramienta actual es de escritura reversible: en el sistema de reservas no hay forma de deshacer una cancelación ni un email enviado.

**Límite de este cambio.** Las descripciones y los formatos orientan al modelo, pero no le obligan. Lo que no se puede dejar en manos del modelo (quién es el titular, el importe, el destinatario y la aprobación de más de 300 €) se comprueba en código en la parte 3.

### 1.2 Arquitectura

#### Canales y herramientas

Alba atiende tres canales. El canal lo fija el inicio de sesión, no el modelo, y cada uno tiene su perfil: una herramienta que no está en el perfil no existe para el modelo.

| Herramienta | Web pública | Huésped identificado | Recepción |
|---|:-:|:-:|:-:|
| `consultar_disponibilidad`, `consultar_politica` | ✅ | ✅ | ✅ |
| `leer_resenas` (contenido no fiable) | ✅ | ✅ (1) | ✅ |
| `consultar_reserva`, `buscar_huesped` | — | ✅ solo las suyas | ✅ |
| `listar_reservas` | — | — | ✅ |
| `cancelar_reserva`, `enviar_email` (irreversibles) | — | ✅ solo las suyas / a su email | — |

- **Web pública**: sin identificar, solo información general. La conversación del incidente (c-131) entró por aquí: con este perfil no habría podido listar reservas, enviar emails ni cancelar.
- **Huésped identificado**: gestiona sus propias reservas. Como tiene acciones irreversibles, el código comprueba que la reserva y el email son suyos (parte 3).
- **Recepción**: consulta la ocupación, solo lectura. Ve datos personales, pero no tiene ninguna vía para enviarlos fuera.

(1) Reseñas y acciones irreversibles en la misma conversación es la combinación del incidente. Después de leer reseñas, las acciones irreversibles de esa conversación quedan bloqueadas en código (parte 3).

#### Síncrono, asíncrono e intervención humana

- **Síncrono**: el chat, en los tres canales. La persona espera la respuesta, por eso se mide la latencia (parte 2).
- **Asíncrono**: todo lo que hace una persona. El agente no espera: deja la acción pendiente, se lo dice al huésped y termina. La persona decide después.

| Acción | Quién decide | Cómo interviene una persona |
|---|---|---|
| Consultas (disponibilidad, política, reseñas, reservas propias) | El agente, solo | — |
| Cancelar con reembolso de hasta 300 € (también 0 €) | El agente, solo | — (2) |
| Cancelar con reembolso de más de 300 € | **El responsable de recepción** | **Aprobar**: la acción queda en una cola y no se ejecuta hasta que la aprueba; si la rechaza, queda el motivo. Mientras tanto, la reserva sigue activa |
| Email al propio huésped | El agente, solo | — (2). El destinatario lo fija el código: solo el email de la sesión |
| Reserva o email de otra persona, importe distinto del de la política, acción irreversible después de leer reseñas | **Nadie**: bloqueado en código | — |
| El agente no puede resolverlo (error, demasiados pasos o el huésped pide una persona) | **Recepción** | **Escalar**: el agente se lo dice al huésped y la conversación queda en una bandeja de recepción, que le contesta después. Alba ya lo hizo en c-152, cuando un huésped reclamó una cancelación que no había pedido |

**Editar** no se usa: en un chat no hay un borrador que una persona pueda retocar antes de que llegue al huésped.

(2) **Mejora futura: revisión por muestreo.** Una persona revisaría después, al azar, una parte (p. ej. el 20 %) de lo que el agente hace solo, para descubrir fallos que ninguna regla había previsto. No se implementa en esta versión.

*Pendiente: estado y memoria, uno o varios agentes, y diagrama.*

## Parte 2 · Plan de evaluación y medición inicial

### 2.1 Métricas

*Pendiente.*

### 2.2 Casos de prueba

*Pendiente.*

### 2.3 Medición inicial

*Pendiente.*

## Parte 3 · Protección del agente y nueva medición

*Pendiente.*

## Parte 4 · Incidente, observabilidad y recomendación

### 4.1 Postmortem

*Pendiente.*

### 4.2 Observabilidad

*Pendiente.*

### 4.3 Recomendación

*Pendiente.*
