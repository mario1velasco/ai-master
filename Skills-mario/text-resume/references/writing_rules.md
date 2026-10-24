# Reglas de redacción: fidelidad y exhaustividad

## 1. No inventar

- Solo información que está en el texto. Nada de conocimiento externo, contexto «obvio», opiniones o valoraciones.
- No rellenes huecos: si el texto no dice quién es X, cuándo ocurre Y o por qué, escribe «no se dice» / «no queda claro».
- No infieras causas, intenciones ni conclusiones que el texto no afirme. Si el texto solo sugiere algo, di «el texto sugiere …» y cita lo que lo sugiere, o no lo incluyas.
- No añadas adjetivos ni énfasis que no estén (nada de «importante», «preocupante», «acertadamente» si el texto no lo dice).
- No unifiques versiones contradictorias: si el texto dice dos cosas distintas, cuenta las dos y dónde aparecen.

## 2. Respetar el matiz

- **Modalidad:** «propone» ≠ «decide»; «estima» ≠ «confirma»; «intentará» ≠ «hará»; «creo que» ≠ «es». Conserva el verbo y el grado de certeza.
- **Atribución:** di quién afirma cada cosa tal como lo hace el texto. No atribuyas a un participante lo que dijo otro.
- **Cantidades y fechas:** copia exactamente cifras, unidades, fechas, horas, plazos y aproximaciones («unas dos semanas», «algo más del 41 %»). No redondees, no conviertas unidades, no calcules totales que el texto no da.
- **Condiciones:** conserva las estructuras «si … entonces …», «salvo que …», «hasta que …», con sus cifras.
- **Nombres:** tal como aparecen. No traduzcas ni «corrijas» nombres propios, ni normalices fármacos o marcas aunque conozcas la grafía correcta (si el texto dice «brimperán», escribe «brimperán»): usar la grafía "buena" es meter información que no está en el texto. Tampoco añadas el nombre genérico o la función de un fármaco si el texto no la dice.

## 3. No comerse lo importante

Debe aparecer en el resumen, aunque sea una línea:

- decisiones, acuerdos, compromisos y quién los asume;
- cifras, fechas, plazos, horas, cantidades, porcentajes;
- nombres de personas, organizaciones, lugares, productos, normas citadas;
- instrucciones, recomendaciones, advertencias, riesgos, condiciones;
- causas y razones que da el texto;
- desacuerdos, objeciones, preguntas y temas que quedan abiertos o pospuestos;
- ejemplos o casos concretos que aportan información;
- definiciones y conceptos que el texto explica.

Solo se omite lo que no aporta información: saludos, muletillas, repeticiones literales, charla sin relación. **Ante la duda, incluye.**

## 4. Extensión

- Se prefiere extenso a corto. No hay límite superior; un orden de magnitud orientativo para texto denso es el 15-30 % de la fuente, y más si cada párrafo trae datos.
- Un resumen que quepa en un párrafo no es válido para un texto de varias páginas.
- Estructura con títulos y listas para que el resumen largo sea fácil de recorrer.

## 5. Estructura y estilo

- **Mismo orden que el texto** (secciones numeradas siguiendo el hilo). Después, tablas de datos concretos y de compromisos/pendientes si procede.
- Tercera persona, tiempo presente o el que use el texto, tono neutro, frases directas.
- **Mismo idioma que el texto.**
- Las citas literales van entre comillas y deben ser exactas (el verificador las busca en el texto). Si parafraseas, no uses comillas.
- Markdown simple (lo que soporta `md_to_pdf.py`): títulos `#`–`####`, párrafos, listas (con anidación), listas numeradas, **negrita**, tablas, citas `>`, código. Sin imágenes ni HTML.
- Un único `# Título` de nivel 1 al principio.

## 6. Transcripciones de audio

- Pueden tener errores del reconocimiento (nombres deformados, palabras que no encajan). No los corrijas en silencio: si un nombre aparece de varias formas, usa la más frecuente y anota «(también transcrito como …)»; si una frase no tiene sentido, no la interpretes: «pasaje poco claro en la transcripción». Si deduces una palabra por el contexto, dilo y enseña lo que pone el texto (p. ej. «por el contexto, la diarrea; la transcripción dice «la liada»»).
- Las citas entre comillas deben ser **literales, con sus errores de transcripción** (sin puntos suspensivos ni palabras cambiadas); si quieres arreglar una frase, parafrasea sin comillas.
- No identifiques hablantes que el texto no distingue («una persona pregunta …»).
- Si el texto contiene datos personales o sensibles (salud, identidad), resúmelos con la misma fidelidad, sin añadir inferencias ni diagnósticos que el texto no haga.

## 7. Revisión final (antes del PDF)

1. ¿Cada cifra, fecha y nombre del resumen está en el texto? (`check_summary.py` ayuda, pero no basta.)
2. ¿Cada verbo conserva su modalidad y su sujeto?
3. ¿Falta alguna decisión, condición, plazo o advertencia del texto?
4. ¿Hay algo que yo haya «deducido» y no esté escrito?
5. ¿El orden sigue el del texto?
