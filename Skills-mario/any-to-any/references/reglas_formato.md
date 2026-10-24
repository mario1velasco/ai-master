# Reglas del paso de formato (bruto.md → final.md)

El paso de formato convierte la extracción automática en un Markdown limpio y parecido al original **sin cambiar el contenido**. `check_markdown.py` compara las palabras visibles y los signos de `final.md` con `bruto.md`: cualquier palabra nueva es un FALLO.

## Cómo trabajar

1. `cp bruto.md final.md` y edita `final.md` con **Edit, cambio a cambio**. No lo reescribas entero de memoria: es la forma más fácil de cambiar una palabra sin darte cuenta.
2. Ten delante el original: en PDF, las vistas de página (`vista/pag_NNN.png`); en el resto, el propio fichero si hace falta (o pide al usuario una captura).
3. Ejecuta `check_markdown.py` al terminar cada unidad y resuelve cada FALLO y cada AVISO.

## Se puede (formato)

| Qué | Ejemplo |
|---|---|
| Marcar títulos según su jerarquía visual | `Informe trimestral` → `# Informe trimestral`; secciones con `##`, `###` |
| Convertir viñetas y números de texto en listas | `• Revisar` → `- Revisar`; `1. Primera fase` (texto) → lista numerada (se conservan los números) |
| Anidar listas según la sangría del original | `  - uno de redes` |
| Rehacer tablas que el PDF desordenó, en el orden de la vista de página | `Mes Gasto (€) 1.200 Enero Febrero 980` → tabla de 2 columnas |
| Quitar la fila de cabecera vacía y subir la primera fila | ya lo hace `convert_docs.py` en docx |
| Unir líneas partidas por el ancho de la página del PDF y palabras cortadas con guion al final de línea | `pala-` + `bra` → `palabra` (el check lo admite) |
| Separar párrafos con una línea en blanco | |
| Negrita, cursiva, citas (`>`), código (``` ``` ```) cuando el original los tiene | |
| Escapar caracteres que Markdown interpretaría | `\*`, `\#`, `1\.` |
| Comentarios HTML invisibles para orientarse | `<!-- diapositiva 3 -->`, `<!-- notas del orador -->`, `<!-- imagen: … -->` |

## No se puede (contenido)

- Añadir palabras: ni títulos inventados («Resumen», «Tabla 1», «Diapositiva 2»), ni rótulos, ni explicaciones, ni traducciones, ni texto alternativo de imágenes visible.
- Corregir: faltas de ortografía, acentos, mayúsculas, cifras, unidades, fechas, nombres. Si el original pone `Fernandez`, se queda `Fernandez`.
- Cambiar signos con significado: `--` por `—`, comillas `"` por `«»`, `1.200` por `1200`, `%` por `por ciento`.
- Resumir, reordenar contenido (salvo para recuperar el orden de lectura real que el PDF perdió) o borrar repeticiones del original.
- Rellenar celdas vacías de una tabla, o poner `0`/`-` donde no hay nada.
- Cambiar URLs de enlaces.

## Excepciones que hay que justificar en la entrega

- **Cabeceras, pies y números de página repetidos** de un PDF (el mismo texto arriba o abajo de cada página): se pueden quitar porque son paginación, no contenido. `check_markdown.py` los listará como QUITADO: menciónalos al usuario («se han quitado las cabeceras "Informe 2025 – Confidencial" y los números de página»). Si el usuario los quiere, se dejan.
- **Texto que markitdown perdió** y sí está en el original (lo indica el segundo lector, OMITIDO?): cópialo literal de `segundo_lector.txt`, en su sitio, dentro de un bloque marcado; `check_markdown.py` comprueba que todas sus palabras están en ese fichero:
  ```
  <!-- original: segundo_lector.txt -->
  …texto copiado sin cambiar nada…
  <!-- /original -->
  ```
  Comprueba en el original que el texto va ahí y dile al usuario qué recuperaste. Nunca añadas nada que no veas en el original.
- **Texto de imágenes** (páginas sin texto, imágenes incrustadas): solo dentro de un bloque `<!-- transcripcion: ruta -->…<!-- /transcripcion -->` copiado de su parte de img-to-text.

## Particularidades por formato

- **PDF**: lo normal es que haga falta todo el paso de formato. Los PDF a varias columnas pueden mezclar el texto de las columnas: reordénalo según la vista de página (dará AVISO MOVIDO, es correcto).
- **PowerPoint**: cada diapositiva viene con `<!-- diapositiva N -->` y su título como `#`; las viñetas a veces llegan como líneas sueltas (pásalas a lista). Las notas del orador vienen tras `<!-- notas del orador -->`; puedes ponerlas como cita (`>`).
- **Word / HTML / EPUB**: markitdown ya da buen Markdown; normalmente basta con revisar tablas y listas.
- **Excel / CSV**: ya sale como tablas Markdown; no toques los valores.
- **Texto (.txt) y audio**: ya está escapado y con sus saltos de línea; no hace falta formato salvo que el usuario lo pida (p. ej. separar párrafos de una transcripción: solo líneas en blanco, nunca palabras).
- **JSON / XML**: van en un bloque de código; no se reformatean.
