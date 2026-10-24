# Particularidades de la fuente (audio + imágenes)

La fuente de `text-resume` aquí no es texto escrito por una persona: son transcripciones. Lo que cambia respecto a un resumen normal:

## Audios (transcripción de Whisper)
- Tiene **errores de reconocimiento**: nombres propios, fármacos o términos técnicos deformados, palabras repetidas, frases cortadas. No los «arregles» ni normalices: deja la grafía del texto o marca «(la transcripción dice «…»)» si deduces la palabra por contexto.
- **No hay hablantes**: no atribuyas frases a una persona concreta salvo que el propio texto lo diga. Usa «una voz dice…» o «se dice que…».
- Las fechas, cifras y nombres dictados pueden estar mal transcritos o ser contradictorios: recógelos tal cual y señala la contradicción en «Lo que el texto no aclara».
- Los números de documentos, teléfonos y similares dictados: no los reproduzcas en el resumen.
- Si los audios eran trozos de una grabación larga, la unión entre trozos puede cortar una frase: léela como continua.

## Imágenes (transcripción literal)
- Los comentarios `<!-- imagen N: nombre -->` marcan el origen de cada bloque: úsalos para citar de dónde sale algo («en la imagen 2…»).
- `[ilegible]` y `[dudoso: …]` son incertidumbre real: no los resuelvas en el resumen; menciónalos en «Lo que el texto no aclara».
- El formato (títulos, listas, tablas, código) es una reconstrucción aproximada: no saques conclusiones del formato.
- Los textos de logotipos, cabeceras y pies repetidos en cada imagen no son contenido: no los resumas como si lo fueran.

## Varias fuentes mezcladas
- Respeta el orden confirmado por el usuario (`orden_final.txt`).
- Si audio e imágenes tratan lo mismo (p. ej. diapositivas y la charla), no mezcles ni «completes» uno con otro: di de qué fuente viene cada dato. Si se contradicen, señálalo.
- En `descripcion.md`, indica el tipo de cada fuente (audio transcrito, imágenes) y cuánto aporta cada una.
