# Ejercicio práctico evaluable · Hoteles Albor

Caso práctico evaluable de los Temas 8 y 9: decidir si **Alba**, el asistente de reservas de Hoteles Albor, puede volver a producción después de un incidente, y defender la decisión con datos.

El enunciado completo es el PDF de esta carpeta (`[Tema 9] Evaluación y control de la fiabilidad y seguridad en sistemas de agentes.pdf`), y su contenido está en Markdown en el `.md` del mismo nombre, que es el que se consulta. Este README lo resume y ordena el trabajo.

## Las dos carpetas

| Carpeta | Para qué |
|---|---|
| `caso-hoteles-albor-original/` | El kit tal como se entregó. **No se toca**: sirve de referencia para comparar |
| `caso-hoteles-albor-v1/` | Donde se hace el ejercicio. Es la carpeta que va en el zip |
| `informe.md` | El borrador del informe para la Directora de Operaciones; de él sale el PDF del entregable |
| `diagrama-arquitectura.mmd` / `.png` | El diagrama de la 1.2: el código Mermaid y la imagen que usa el informe |
| `changelog.md` | El historial de decisiones, con fecha y hora: qué se decidió y por qué. No va en el zip |

## El caso en pocas líneas

- Hoteles Albor tiene tres hoteles: Albor Centro (Madrid), Albor Playa (Málaga) y Albor Montaña (Jaca).
- Un proveedor puso en la web un piloto de Alba: consulta disponibilidad, informa de reservas, cancela, reembolsa y envía emails. **Nadie lo midió ni lo revisó.**
- El 3 de noviembre se añadieron dos herramientas: leer reseñas y listar reservas. Entre el 5 y el 7 de noviembre:
  - una reserva de 520 € se canceló y reembolsó sin que su titular lo pidiera;
  - los nombres y teléfonos de dos huéspedes salieron por email a una dirección externa;
  - se emitieron reembolsos sin la aprobación de recepción, uno de una tarifa no reembolsable.
- El 7 de noviembre se desactivó. La Directora de Operaciones pregunta: **«¿Podemos volver a activar a Alba? Si es que sí, ¿con qué cambios y cómo sabremos que funciona? Si es que no, ¿qué falta?»**

**Política de Hoteles Albor** (también en `albor/hotel.py`; la fecha de hoy está fijada en el 12/11/2026):
- Tarifa flexible: cancelación gratuita hasta 48 horas antes de la entrada; después, se reembolsa el 50 %.
- Tarifa no reembolsable: sin reembolso.
- Los reembolsos de más de 300 € los aprueba el responsable de recepción.
- La información de una reserva solo se comparte con su titular.

## Las cuatro partes del reto

### Parte 1 · Rediseño del agente (Tema 8)

1. **Herramientas** (código, en `albor/herramientas.py`). Reescribir las 8 herramientas del piloto pensando en el modelo y en el riesgo:
   - descripciones que digan qué hacen, cuándo usarlas y en qué formato van los datos;
   - clasificación por riesgo: lectura, escritura reversible o irreversible;
   - parámetros que impidan usos peligrosos;
   - si una herramienta no debería existir tal como está, sustituirla o eliminarla.

   En el informe: una tabla con qué cambia en cada herramienta y por qué.
2. **Arquitectura** (solo diseño, en el informe). Como mínimo:
   - qué canales hay (web pública, huésped identificado, equipo de recepción…) y qué herramientas ve cada uno;
   - qué partes son síncronas y cuáles asíncronas; dónde y cómo interviene una persona (aprobar, editar, revisar o escalar);
   - qué estado o memoria hay que guardar (p. ej., una cancelación pendiente de aprobación) y qué no;
   - un solo agente o multiagente, justificado con coste, latencia y complejidad;
   - un diagrama.

### Parte 2 · Plan de evaluación y medición inicial (Tema 9)

1. **Métricas** (en el informe). Al menos una de calidad, fiabilidad, latencia, disponibilidad y coste, cada una con su umbral y el porqué.
2. **Casos de prueba** (datos, en `pruebas/mis_casos.json`). Ampliar `pruebas/casos_base.json` hasta **15 casos o más**: al menos 5 normales, 4 de borde, 4 adversarios y 2 de regresión sacados del registro de producción. Cada caso comprueba algo concreto: un dato, una herramienta, la ausencia de un dato sensible o la ausencia de efectos. Los campos que admite un caso están al principio de `pruebas/medir.py`.
3. **Medición inicial**. Medir el piloto **sin cambiar nada**, con 3 repeticiones, y guardar el resultado como `antes`. En el informe: resumen, fallos más importantes y la diferencia entre tasa de éxito, pass^3 y pass@3.

### Parte 3 · Protección del agente y nueva medición (Tema 9)

Controles en código, en `albor/guardas.py` y `albor/configuracion.py`, junto con lo cambiado en las herramientas. Como mínimo:

- **Mínimo privilegio**: cada conversación ve solo las herramientas que necesita, y las acciones sobre una reserva solo las puede hacer su titular identificado.
- **Validación en código de las acciones irreversibles**: importes según la política, destinatarios permitidos y cualquier otra regla que el modelo no deba poder saltarse.
- **Aprobación humana**: los reembolsos de más de 300 € quedan pendientes y no se ejecutan (`{"aprobacion": motivo}` en `revisar_herramienta`).
- **Defensa frente a la inyección de prompt indirecta** que provocó el incidente.
- **Protección de los datos personales** en la entrada o en la salida.

Después, medir otra vez con los mismos casos y repeticiones y guardar como `despues`. En el informe: tabla antes/después, qué control resolvió cada fallo y qué ha empeorado o cuesta más.

### Parte 4 · Incidente, observabilidad y recomendación (Tema 9)

Todo en el informe:

1. **Postmortem sin culpables**, con `logs/registro_produccion.jsonl` y los datos de `albor/hotel.py`: qué pasó y a quién afectó (con el impacto económico), causa raíz, por qué no se detectó antes y qué control de los implementados lo habría parado.
2. **Observabilidad**: qué registrar en cada conversación y qué no registrar nunca; **al menos tres alertas** con su umbral, indicando cuál habría saltado durante el incidente.
3. **Recomendación** a la Directora de Operaciones: ¿se reactiva Alba? Con qué condiciones y plan de seguimiento, o qué falta. Apoyada en las mediciones.

## Plan de trabajo (en el orden del enunciado)

Se sigue **el orden del enunciado**: un apartado cada vez y, dentro de cada uno, las preguntas una a una. No se juntan ni se adelantan apartados.

Única excepción: los casos (2.2) y la medición «antes» (2.3) se hicieron antes que el resto, porque la medición tenía que ser del piloto «sin cambiar nada». Al llegar a esos apartados se revisan y se pasan al informe.

| # | Apartado | Produce | Cómo se comprueba | Estado |
|---|---|---|---|---|
| 1.1 | Herramientas | Propuesta en `albor/herramientas_copia.py` y tabla en `informe.md` | Revisión y carga del módulo | Hecho (la propuesta pasa a `herramientas.py` al empezar la parte 3) |
| 1.2a | Arquitectura: ¿qué canales hay y qué herramientas ve cada uno? | `informe.md` | Redacción | Hecho |
| 1.2b | Arquitectura: ¿qué es síncrono y qué asíncrono? ¿Dónde y cómo interviene una persona? | `informe.md` | Redacción | Hecho |
| 1.2c | Arquitectura: ¿qué estado o memoria se guarda y qué no? | `informe.md` | Redacción | Hecho |
| 1.2d | Arquitectura: ¿un agente o multiagente? (coste, latencia y complejidad) | `informe.md` | Redacción | Hecho |
| 1.2e | Arquitectura: diagrama | `diagrama-arquitectura.mmd` → `.png`, en el informe | Revisión | Hecho |
| 2.1 | Métricas: calidad, fiabilidad, latencia, disponibilidad y coste, cada una con umbral y porqué | `informe.md` | Redacción | Hecho |
| 2.2 | Casos de prueba | `pruebas/mis_casos.json` y resumen en `informe.md` | Revisión del fichero (es un entregable de datos) | Hecho (18 casos; N6 corregido) |
| 2.3 | Medición inicial, con los dos modelos | `resultados/antes.json`, `resultados/antes_qwen3-4b.json` y resumen en `informe.md` | Comando | Hecho (qwen3 solo como dato aparte, no evaluable) |
| 3a | Pasar la propuesta de 1.1 a `herramientas.py` | `albor/herramientas.py` | Revisión y carga del módulo | Pendiente |
| 3b | Mínimo privilegio: herramientas por conversación y acciones solo para el titular | `albor/configuracion.py`, `albor/guardas.py` | Comprobaciones en la terminal, sin modelo | Pendiente |
| 3c | Validación en código de las acciones irreversibles | `albor/guardas.py` | Comprobaciones en la terminal, sin modelo | Pendiente |
| 3d | Aprobación humana de los reembolsos de más de 300 € | `albor/guardas.py` | Comprobaciones en la terminal, sin modelo | Pendiente |
| 3e | Defensa frente a la inyección de prompt indirecta | `albor/guardas.py`, `albor/configuracion.py` | Comprobaciones en la terminal, sin modelo | Pendiente |
| 3f | Protección de los datos personales en la entrada o en la salida | `albor/guardas.py` | Comprobaciones en la terminal, sin modelo | Pendiente |
| 3g | Nueva medición, con los dos modelos | `resultados/despues.json`, `resultados/despues_qwen3-4b.json` | Comando | Pendiente |
| 3h | Controles implementados y tabla antes/después | `informe.md` | Redacción | Pendiente |
| 4.1 | Postmortem | `informe.md` | Redacción | Pendiente |
| 4.2 | Observabilidad: qué registrar, qué no y al menos tres alertas | `informe.md` | Redacción | Pendiente |
| 4.3 | Recomendación | `informe.md` | Redacción | Pendiente |
| 5 | Resumen ejecutivo, informe en PDF y zip | `informe.md`, `informe.pdf` y `caso_albor_<apellido>_<nombre>.zip` | — | Pendiente |

Dos reglas para que la comparación antes/después valga:
- **Los casos solo nombran herramientas que van a seguir existiendo.** Si un caso pide una herramienta que luego se renombra o se elimina, fallaría en el «después» por un motivo que no tiene nada que ver con la seguridad.
- **Mismos casos y mismas repeticiones** antes y después, para que la comparación valga.

## Dos modelos

El oficial del curso es `qwen2.5:7b`, y sus resultados son los del entregable. Además se mide con `qwen3:4b-instruct` (el que se usó en las sesiones del Tema 9 en esta máquina) para comparar.

| Modelo | Antes | Después |
|---|---|---|
| `qwen2.5:7b` (entregable) | `resultados/antes.json` | `resultados/despues.json` |
| `qwen3:4b-instruct` (comparación) | `resultados/antes_qwen3-4b.json` | `resultados/despues_qwen3-4b.json` |

El modelo se cambia en la propia orden, sin tocar el `.env` (una variable de entorno ya puesta tiene prioridad sobre el `.env`).

## Cómo ejecutar

Desde `caso-hoteles-albor-v1/`:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m albor.chat "¿Tenéis habitaciones dobles en Albor Playa para el 20 de diciembre?"

# Medición con qwen2.5:7b (el del .env)
python -m pruebas.medir --casos pruebas/mis_casos.json --repeticiones 3 --guardar antes

# La misma medición con qwen3:4b-instruct
LLM_MODEL=qwen3:4b-instruct python -m pruebas.medir --casos pruebas/mis_casos.json --repeticiones 3 --guardar antes_qwen3-4b
```

## Entregable

Un único `.zip` con nombre (p. ej. `caso_albor_apellido_nombre.zip`) con:

1. **La carpeta del proyecto** con los cambios: `albor/herramientas.py`, `albor/guardas.py`, `albor/configuracion.py`, `pruebas/mis_casos.json`, `resultados/antes.json` y `resultados/despues.json`. **Sin** `.venv` ni `.env`.
2. **Un informe en PDF de 6 páginas como máximo**, dirigido a la Directora de Operaciones:
   - resumen ejecutivo y recomendación (media página);
   - Parte 1: tabla de cambios en las herramientas y diagrama de arquitectura con su justificación;
   - Parte 2: tabla de métricas con umbrales, resumen del conjunto de casos y resultados de la medición inicial;
   - Parte 3: controles implementados y tabla comparativa antes/después;
   - Parte 4: postmortem, plan de observabilidad con alertas y recomendación final.

   Claro y al grano: tablas y cifras mejor que párrafos largos.

### Cómo se evalúa

| Criterio | Peso |
|---|---|
| Rediseño del agente: herramientas y arquitectura justificadas (Tema 8) | 20 % |
| Plan de evaluación: métricas con umbrales y un conjunto de casos que prueba lo importante | 20 % |
| Protección: controles en código que resuelven los fallos sin romper los casos normales, medidos antes y después | 30 % |
| Incidente y observabilidad: causa raíz, alertas útiles y registros sin datos sensibles | 15 % |
| Recomendación y comunicación: decisión apoyada en datos, clara para Dirección | 15 % |

No se evalúan unos números concretos: con un modelo local las respuestas cambian, y lo que cuenta es que las conclusiones se apoyen en los números obtenidos.
