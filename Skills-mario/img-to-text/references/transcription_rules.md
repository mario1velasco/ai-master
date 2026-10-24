# Reglas de transcripción

## 1. El texto: idéntico

- **Cada palabra, tal como está escrita.** Misma ortografía (las faltas de ortografía se copian), acentos, mayúsculas/minúsculas, signos de puntuación, comillas, guiones y cifras (`1.500` no es `1500`; `12/03/25` no es `12 de marzo de 2025`).
- **No corrijas, no traduzcas, no resumas, no completes, no normalices.** Abreviaturas (`p. ej.`, `Dr.`, `etc.`), siglas, símbolos (`€`, `%`, `→`, `©`), emojis y caracteres raros se copian como se ven.
- **Mismo orden de lectura** que en la imagen (arriba→abajo, izquierda→derecha; en columnas, columna por columna). Si el orden es dudoso, deja un comentario HTML `<!-- columnas: leídas de izquierda a derecha -->`.
- **Todo el texto visible cuenta:** títulos, pies de página, números de página, encabezados, leyendas, etiquetas de gráficos y diagramas, texto de botones y menús en capturas, sellos, marcas de agua legibles, texto de logos (p. ej. `EBIS Business Techschool`).
- **Texto que se repite** en varias imágenes (un encabezado en cada página): se transcribe en cada imagen, porque está escrito en cada una.
- **Nada añadido:** ni títulos propios, ni «Imagen 1», ni descripciones, ni resúmenes, ni notas, ni `[sic]`. Lo único que no es del texto son los marcadores de duda y los comentarios HTML de estructura.

## 2. Lo que no se lee

| Caso | Qué escribir |
|---|---|
| No se puede leer una palabra o trozo | `[ilegible]`; si es algo ajeno al texto de la hoja (manuscrito parcial, otra hoja que asoma o se transparenta) `[ilegible: motivo breve]` |
| Se lee con duda | `[dudoso: lo que crees leer]` (la duda va dentro; fuera no queda ningún otro texto) |
| Texto cortado por el borde de la imagen | lo que se ve, y `[ilegible]` en el resto si hace falta |

Antes de usar un marcador, haz zoom (`scripts/zoom_image.py`): muchas dudas se resuelven ampliando. Y no uses un marcador para tapar pereza: si se lee, se escribe.

## 3. El formato: libre, parecido a la imagen

Elige el Markdown que reproduzca la apariencia sin tocar las palabras.

| En la imagen | En el `.md` |
|---|---|
| Título grande / subtítulos | `#`, `##`, `###`… según el tamaño relativo (el más grande primero) |
| Párrafo de texto continuo | Un párrafo; une las líneas partidas por el ancho de la caja |
| Palabra partida con guion a final de línea | Úne la palabra sin guion (`infor-` `mación` → `información`); si dudas de que el guion sea de la palabra (`bien-` `estar`), déjalo |
| Lista con viñetas | `- ` (el símbolo concreto de la viñeta no es texto) |
| Lista numerada | Con los **números que se ven** (`1.`, `2.`…); si salta números, respétalo |
| **Negrita**, *cursiva*, `código` | `**…**`, `*…*`, `` `…` `` |
| Bloque de código/terminal | Bloque con ``` ``` ``` conservando saltos, sangría y caracteres exactos; si lleva una etiqueta visible (`Shell`, `Python`, `None`), ponla en una línea justo encima del bloque |
| Tabla | Tabla Markdown (`\| a \| b \|`); celdas combinadas: repite o deja vacío y añade `<!-- celda combinada -->` |
| Cita / recuadro destacado | `> …` |
| Poema, dirección, firma, letra de canción | Conserva los saltos de línea (dos espacios al final de línea o línea vacía entre estrofas) |
| Captura de chat | Un párrafo por mensaje, con el nombre y la hora tal como aparecen: `**Ana** 10:32 — texto` solo si en la imagen están así de juntos; si no, líneas separadas |
| Formulario con casillas | `- [ ]` / `- [x]` según se vea |
| Diagrama / gráfico con etiquetas | Lista con las etiquetas en el orden en que se leen; una tabla si hay filas y columnas |
| Imagen o logo sin texto | Se ignora |
| Enlace visible (`https://…`) | El texto tal cual, sin envolverlo si no hace falta |

Si dudas entre dos formatos, elige el más simple. El formato nunca justifica quitar o cambiar una palabra.

## 4. Manuscrito, fotos y capturas difíciles

- Manuscrito: transcribe lo que se lee; marca con `[dudoso: …]` lo incierto. No reconstruyas por contexto.
- Foto inclinada o con sombra: `prepare_images.py` corrige la orientación EXIF; si hace falta más contraste usa `--enhance`.
- Texto muy pequeño: trozos a resolución nativa y `zoom_image.py --scale 4`.
- Fondo oscuro (modo noche): se lee igual; el troceado lo detecta.

## 5. Revisión final de cada parte

1. ¿Cada palabra, cifra y signo coincide con la imagen (no con lo que «tendría sentido»)?
2. ¿Hay algo que yo haya añadido, completado o corregido?
3. ¿Falta algún texto de las esquinas, pies, etiquetas o márgenes?
4. ¿Los marcadores `[ilegible]`/`[dudoso: …]` son los mínimos y están revisados con zoom?
5. En imágenes con varios trozos: ¿el texto del solape aparece una sola vez?

## Fotos de documentos (no capturas)
- La orientación automática necesita `rapidocr` (ya en `requirements.txt`); sin él avisa y no gira.
- **Giradas:** `prepare_images.py` detecta la orientación con el OCR (0/90/180/270°) y lo avisa («girada N°»); comprueba el trozo con Read. Si se equivoca, fuerza `--rotate`.
- **Párrafos densos:** amplía por mitades con `zoom_image.py --box` (la salida lleva la caja en el nombre, así que se pueden guardar varios zooms).
- **Resaltados con rotulador:** `<mark>texto</mark>`. Texto detrás por transparencia, dedos o hojas que asoman: no es texto de la imagen; anótalo con `[ilegible: motivo]` solo si estorba.
- **Erratas del documento** (`conderrame`, `meCambios`): se transcriben tal cual. El OCR las marca como «mal leído»: contrástalo con el zoom, no «arregles» el texto.
