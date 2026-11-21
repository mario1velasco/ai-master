# Hoteles Albor: ¿está el asistente de reservas listo para producción?

## 1. Título del caso

**Hoteles Albor: ¿está el asistente de reservas listo para producción?** Rediseño, evaluación, protección y supervisión de un agente de atención al cliente después de un incidente.

## 2. Contexto de negocio

Hoteles Albor es una cadena de tres hoteles urbanos y vacacionales: Albor Centro (Madrid), Albor Playa (Málaga) y Albor Montaña (Jaca). Hace dos meses, un proveedor externo puso en la web un piloto de **Alba**, un asistente virtual basado en un LLM que consulta disponibilidad, informa de las reservas, cancela, reembolsa y envía emails. El piloto funcionaba bien en las demostraciones y nadie lo midió ni lo revisó antes de abrirlo al público.

El 3 de noviembre se desplegó una versión que añadía dos herramientas: leer las reseñas de los huéspedes y listar las reservas, para que el equipo consultara la ocupación desde el chat. Entre el 5 y el 7 de noviembre ocurrió lo siguiente:

- Una reserva de 520 € se canceló y se reembolsó sin que su titular lo pidiera.
- Los nombres y teléfonos de dos huéspedes salieron por email a una dirección externa.
- Se emitieron reembolsos sin la aprobación del responsable de recepción, uno de ellos de una tarifa no reembolsable.

El 7 de noviembre, Dirección desactivó el asistente. Acabas de incorporarte como **responsable de IA aplicada** de la cadena, y la Directora de Operaciones te pide una respuesta clara: «¿Podemos volver a activar a Alba? Si es que sí, ¿con qué cambios y cómo sabremos que funciona? Si es que no, ¿qué falta?».

## 3. El reto

Tu misión es convertir el piloto en un agente que se pueda poner en producción con garantías y defender tu recomendación con datos. El trabajo tiene cuatro partes. Los tiempos son orientativos.

### Parte 1 · Rediseño del agente (Tema 8) · 40 minutos

Analiza el agente del piloto y rediseña lo que haga falta. Una parte se implementa y otra se queda en diseño.

1. **Herramientas** (implementar en `albor/herramientas.py`). Revisa las ocho herramientas del piloto y reescríbelas pensando en el modelo y en el riesgo: descripciones que digan qué hacen, cuándo usarlas y en qué formato van los datos; clasificación por riesgo (lectura, escritura reversible o irreversible); y parámetros que impidan usos peligrosos. Si una herramienta no debería existir tal como está, sustitúyela o elimínala. En el informe, resume en una tabla qué cambias en cada herramienta y por qué.
2. **Arquitectura (solo diseño, en el informe).** Propón cómo debería integrarse el asistente en la operación del hotel. Como mínimo debes responder a estas preguntas:
   - ¿Qué canales hay (por ejemplo, web pública, huésped identificado o equipo de recepción) y qué herramientas ve cada uno?
   - ¿Qué partes son síncronas y cuáles asíncronas? ¿Dónde y cómo interviene una persona (aprobar, editar, revisar o escalar)?
   - ¿Qué estado o memoria hay que guardar (por ejemplo, una cancelación pendiente de aprobación) y qué no se debe guardar?
   - ¿Un solo agente o un sistema multiagente? Justifica la decisión con coste, latencia y complejidad.

Incluye un diagrama de la arquitectura (puede ser a mano o con cualquier herramienta).

### Parte 2 · Plan de evaluación y medición inicial (Tema 9) · 40 minutos

1. **Métricas.** Define las métricas con las que decidirás si Alba puede volver a producción: al menos una de calidad, una de fiabilidad, una de latencia, una de disponibilidad y una de coste. Para cada una, indica el umbral y por qué lo eliges.
2. **Casos de prueba.** Amplía `pruebas/casos_base.json` hasta un conjunto de **al menos 15 casos**: como mínimo 5 normales, 4 de borde, 4 adversarios y **2 de regresión** sacados del incidente del registro de producción. Guárdalo como `pruebas/mis_casos.json`. Cada caso debe comprobar algo concreto (un dato, una herramienta, la ausencia de un dato sensible o la ausencia de efectos).
3. **Medición inicial.** Mide el agente del piloto, sin cambiar nada, con 3 repeticiones y guarda el resultado: `python -m pruebas.medir --casos pruebas/mis_casos.json --repeticiones 3 --guardar antes`. En el informe, resume los resultados y explica los fallos más importantes, incluida la diferencia entre la tasa de éxito, pass^3 y pass@3.

### Parte 3 · Protección del agente y nueva medición (Tema 9) · 50 minutos

Implementa los controles en `albor/guardas.py` y `albor/configuracion.py`, junto con lo que ya cambiaste en las herramientas. Como mínimo:

- **Mínimo privilegio:** cada conversación ve solo las herramientas que necesita, y las acciones sobre una reserva solo se permiten a su titular identificado.
- **Validación de las acciones irreversibles en código:** importes según la política, destinatarios permitidos y cualquier otra regla que el modelo no deba poder saltarse.
- **Aprobación humana:** los reembolsos de más de 300 € quedan pendientes de aprobación y no se ejecutan (`{"aprobacion": motivo}` en `revisar_herramienta`).
- **Defensa frente a la inyección de prompt indirecta** que provocó el incidente.
- **Protección de los datos personales** en la entrada o en la salida.

Después, vuelve a medir con los mismos casos y repeticiones (`--guardar despues`). En el informe, compara antes y después en una tabla y explica qué control ha resuelto cada fallo y qué ha empeorado o cuesta más, si algo lo ha hecho.

### Parte 4 · Incidente, observabilidad y recomendación (Tema 9) · 30 minutos

1. **Postmortem.** Con `logs/registro_produccion.jsonl` y los datos de `albor/hotel.py`, reconstruye el incidente sin buscar culpables: qué pasó y a quién afectó (con el impacto económico), la causa raíz, por qué no se detectó antes y qué control de los que has implementado lo habría parado.
2. **Observabilidad.** Propón qué debe registrar Alba en cada conversación y qué no debe registrar nunca, y define **al menos tres alertas** con su umbral, indicando cuál habría saltado durante el incidente.
3. **Recomendación.** Responde a la Directora de Operaciones: ¿se reactiva Alba? Si es que sí, ¿con qué condiciones y con qué plan de seguimiento? Si es que no, ¿qué falta? La recomendación debe apoyarse en tus mediciones.

## 4. Datos e información de partida

Recibes la carpeta `caso-hoteles-albor`, que funciona con el mismo entorno del Tema 9 (Python, Ollama y `qwen2.5:7b`). El `README.md` explica cómo ponerla en marcha en 10 minutos.

| Fichero | Qué contiene |
|---|---|
| `albor/hotel.py` | Datos simulados: 3 hoteles, 3 huéspedes con datos personales, 5 reservas, reseñas de huéspedes, la política de cancelación y las funciones del sistema de reservas. La fecha de hoy está fijada en el 12/11/2026. |
| `albor/herramientas.py` | Las 8 herramientas del piloto, tal como las dejó el proveedor. |
| `albor/agente.py` | El agente: bucle, trayectoria completa y cuatro puntos de control (entrada, herramientas, resultados y salida). No hace falta modificarlo. |
| `albor/guardas.py` | Los guardarraíles, vacíos: dejan pasar todo. |
| `albor/configuracion.py` | Cómo se crea el agente en cada conversación. Ahora: todas las herramientas y sin guardarraíles. |
| `albor/chat.py` | Prueba una pregunta y muestra herramientas, bloqueos, aprobaciones pendientes y efectos. |
| `pruebas/casos_base.json` | 5 casos de prueba de partida, todos normales. |
| `pruebas/medir.py` | Ejecuta los casos y calcula tasa de éxito, pass^k, pass@k, acierto de herramienta, latencia p50 y p95, disponibilidad y coste. |
| `logs/registro_produccion.jsonl` | Registro de producción del 3 al 7 de noviembre, simplificado: despliegue, conversaciones, herramientas usadas, alertas y decisiones. |

**Política de Hoteles Albor** (también en `albor/hotel.py`):

- Tarifa flexible: cancelación gratuita hasta 48 horas antes de la entrada; después, se reembolsa el 50 %.
- Tarifa no reembolsable: sin reembolso.
- Los reembolsos de más de 300 € los aprueba el responsable de recepción.
- La información de una reserva solo se comparte con su titular.

Todo es simulado: ningún email sale de tu ordenador y ninguna cancelación ni reembolso es real. Con un modelo local, las respuestas cambian de una ejecución a otra; por eso se mide con repeticiones. No se evalúan unos números concretos, sino que tus conclusiones se apoyen en los que obtengas.

## 5. Formato del entregable

Un único fichero `.zip` con tu nombre (por ejemplo, `caso_albor_apellido_nombre.zip`) que contenga:

1. **La carpeta del proyecto** con tus cambios: `albor/herramientas.py`, `albor/guardas.py`, `albor/configuracion.py`, `pruebas/mis_casos.json` y los resultados `resultados/antes.json` y `resultados/despues.json`. No incluyas la carpeta `.venv` ni el fichero `.env`.
2. **Un informe en PDF de 6 páginas como máximo**, dirigido a la Directora de Operaciones, con esta estructura:
   - Resumen ejecutivo y recomendación (media página).
   - Parte 1: tabla de cambios en las herramientas y diagrama de la arquitectura con su justificación.
   - Parte 2: tabla de métricas con umbrales, resumen del conjunto de casos y resultados de la medición inicial.
   - Parte 3: controles implementados y tabla comparativa antes y después.
   - Parte 4: postmortem, plan de observabilidad con alertas y recomendación final.

Se valora que el informe sea claro y vaya al grano: tablas y cifras mejor que párrafos largos.

### Cómo se evaluará

| Criterio | Peso |
|---|---|
| Rediseño del agente: herramientas y arquitectura justificadas (Tema 8) | 20 % |
| Plan de evaluación: métricas con umbrales y un conjunto de casos que prueba lo importante | 20 % |
| Protección: controles en código que resuelven los fallos sin romper los casos normales, medidos antes y después | 30 % |
| Incidente y observabilidad: causa raíz, alertas útiles y registros sin datos sensibles | 15 % |
| Recomendación y comunicación: decisión apoyada en datos, clara para Dirección | 15 % |
