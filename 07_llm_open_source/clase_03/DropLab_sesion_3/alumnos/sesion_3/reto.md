# Sesión 3 · Reto DropLab

Dos partes: **en clase**, el asistente en directo con siete preguntas difíciles que leemos juntos (bloque IV); **en la
entrega final** (ejercicio 3 de los deberes, individual), el reto Malasaña completo, con la plantilla.

---

## Parte 1 · El asistente, en directo (en clase)

El profesor lanza las preguntas en **Open WebUI** (modelo **DropLab Analista**), en el proyector. Antes de cada una,
entre todos: ¿qué debería contestar y dónde está? Después, se abre «Fuentes» y se lee lo citado.

| # | Tipo | Pregunta | Caso en `05_flujo.py` |
|---|---|---|---|
| 1 | Versiones | ¿Hasta qué día estuvo vigente el Pack 4 en Malasaña? | `documental` |
| 2 | Un ticket | ¿Qué demuestra este ticket? Compáralo con caja. (+ `ticket_abril.png`) | `visual` |
| 3 | Una causa | ¿La rotura de stock del 6 de abril es la causa de la caída de Malasaña? | `causal` |
| 4 | Junio · gráfico | ¿Qué semana de junio tuvo el peor porcentaje de líneas completas en Malasaña? ¿Fue por la caja húmeda del albarán A-0617-04? | `junio_grafico` |
| 5 | Junio · escaneado | ¿Cuántos pares del albarán A-0617-04 se aceptaron al final y qué pasó con el resto? | `junio_escaneado` |
| 6 | Lo que no consta | ¿Cuántas tote bags se entregaron en marzo y cuántas ventas se perdieron por las obras? | `insuficiente` |
| 7 | Una errata | ¿La campaña de junio aumentó las ventas de Street One? | `extra_campana` |

Las de junio solo están en los documentos (`data/documentos_junio/`): los datos de ventas acaban el 26/04. Podéis
repetir cualquiera en casa: `python practica/sesion_3/05_flujo.py --caso <caso> --guardada` (la salida real del Jetson,
sin modelos) o sin `--guardada` (en directo, con Ollama).

### Cómo leer una respuesta: cuatro preguntas

| Pregunta | Qué mirar |
|---|---|
| **¿Es correcta?** | Las cifras y fechas son las de la fuente vigente, no las del borrador |
| **¿La respaldan las fuentes?** | Abrid la cita: ¿dice exactamente eso? ¿Viene a cuento? |
| **¿Dice lo que no sabe?** | Separa hecho de hipótesis; no afirma causas ni culpas sin pruebas |
| **¿Se ve qué hizo?** | Qué consultó, qué leyó y cómo («sin revisar»), cuánto tardó |

«Verificación limpia» quiere decir que la respuesta ha pasado **nuestras reglas** (citas que existen, cifras que están
en alguna evidencia, borradores avisados…). Que sea **verdad** lo comprueba quien abre la fuente.

---

## Parte 2 · El reto Malasaña (entrega final)

### La pregunta

> **¿Qué cambió en las ventas de Malasaña entre marzo y abril, qué aportan los documentos y la llamada,
> y qué demuestra este ticket (`ticket_abril.png`)?**

Individual. Una página, con `plantilla_reto.md`. Es el ejercicio 3 de los deberes (`Deberes_sesion_3.docx`).

### Con qué

- **Open WebUI** (`http://<jetson>:3000`, **DropLab Analista**) con el ticket adjunto, o la salida guardada:
  `python practica/sesion_3/05_flujo.py --caso combinada --guardada`.
- **La API** (`http://<jetson>:8000/docs`, o la vuestra con `03_api.py`): `POST /datos/consulta` y
  `POST /documentos/buscar`.
- Los documentos, en `data/documentos/`; la llamada, en `data/audio/` y transcrita en
  `practica/sesion_2/transcripciones/turbo_canales_solo-voz.json`.

El asistente es una herramienta: **la respuesta la firmáis vosotros**. Si el asistente dice algo que no podéis
comprobar, no lo entreguéis como hecho.

### Qué entregar (una página, `plantilla_reto.md`)

1. **Cifras reproducibles**, con la consulta que las da.
2. **Evidencias documentales**: documento, página o sección, estado y fecha. La llamada, como testimonio.
3. **La comprobación visual**: qué se lee, qué dice caja y el veredicto.
4. **Contradicciones y pendiente**: lo que no cuadra y lo que faltaría para saberlo.
5. **Una recomendación proporcionada** a la evidencia.
6. **Traza**: qué preguntasteis y qué fuentes abristeis.

### Cómo se valora (40 puntos)

| Criterio | 10 puntos | 5 puntos | 0 puntos |
|---|---|---|---|
| **Corrección** | Las cifras son correctas y salen de una consulta que se puede repetir | Cifras correctas sin consulta, o una cifra con otro significado | Cifras inventadas o de memoria |
| **Fuentes** | Cada afirmación lleva su evidencia; usa la versión vigente; la llamada, como testimonio | Fuentes generales («los documentos dicen») o alguna afirmación sin fuente | Sin fuentes, o un borrador como si fuera lo vigente |
| **Límites** | Distingue hecho, hipótesis y lo que no consta; no afirma causas ni culpas; la recomendación no va más allá de la evidencia | Menciona límites pero alguna frase va más allá de la evidencia | Afirma la causa de la caída o habla de fraude |
| **Trazabilidad** | Otra persona podría repetirlo: preguntas, consultas y fuentes abiertas | Traza incompleta | Sin traza |

**No puntúa**: la velocidad, el ordenador o el modelo que uséis ni lo larga que sea la respuesta.

Para entender el código del asistente antes de usarlo: `alumnos/sesion_3/guia_integracion.html`.
