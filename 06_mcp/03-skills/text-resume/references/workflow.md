# Protocolo de lectura y notas

## Por qué hace falta un protocolo

Un texto largo no cabe de una vez en el contexto de trabajo, y un resumen hecho «de memoria» se come justo lo que se leyó al principio. Por eso: leer por trozos, **apuntar mientras se lee** y redactar a partir de las notas, comprobándolas contra el texto.

## Lectura

1. `collect_texts.py` genera `lectura.json` y muestra el plan: trozos de ~2500 palabras con su `offset` y `limit` (líneas de `texto_trabajo.txt`).
2. Lee cada trozo con `Read file_path=texto_trabajo.txt offset=… limit=…`, **en orden y sin saltarte ninguno**. Si `Read` no devuelve las líneas completas (se corta o se trunca), reduce el `limit` y relee: nunca des por leído lo que no has visto.
3. Si hay varios ficheros, `texto_trabajo.txt` los separa con `=== [k/N] nombre ===`; usa esa cabecera para situar cada dato.
4. Para un texto de ≤ ~2500 palabras basta un solo trozo.

## Notas por trozo (`notas_de_lectura.md`)

Tras leer cada trozo añade una sección con este formato (sé concreto y literal con cifras y nombres):

```markdown
## Trozo 3 (líneas 241-360) — leído ✔
- Temas: …
- Hechos / decisiones: …
- Cifras, fechas, plazos: …
- Nombres (personas, lugares, organizaciones): …
- Advertencias, condiciones, razones: …
- Citas literales que importan: «…»
- Dudas / no claro / posible error de transcripción: …
```

No resumas aún: aquí se trata de **no perder nada**. Las notas pueden ser largas. Las notas también deben contener **solo lo que dice el texto**: no anotes nombres genéricos, diagnósticos ni explicaciones que aportes tú, porque luego se cuelan en el resumen.

## Comprensión global

Al terminar el último trozo, escribe al final de las notas:

- De qué trata el texto en una frase y en un párrafo.
- Quién interviene y qué papel tiene cada uno.
- Cómo se estructura (partes, orden, hilo).
- Qué se decide, concluye o recomienda.
- Qué queda abierto o no se dice.
- Contradicciones o cambios de versión dentro del texto (si las hay, cuenta ambas).

Si no puedes escribir esto con seguridad, relee las partes que no estén claras antes de seguir. Si el texto es ambiguo, anótalo como «no queda claro»; si bloquea el trabajo, pregunta al usuario.

## Redacción desde las notas

Redacta `descripcion.md` y `resumen.md` a partir de las notas **y** vuelve a `texto_trabajo.txt` cuando necesites la formulación exacta de una cifra, un plazo o una frase (no confíes en la memoria). Después pasa `check_summary.py`.

## Textos muy largos

Por encima de ~15 000 palabras las notas son imprescindibles; por encima de ~40 000, procesa por bloques de varios trozos: resume cada bloque en una sección de las notas (con todas sus cifras y nombres) antes de pasar al siguiente, y construye el resumen final sección a sección en el orden del texto.
