# Formatos de salida (md, pdf, docx)

El `.md` es la fuente: el `.pdf` y el `.docx` se generan desde él con scripts propios (sin pandoc, LaTeX ni Word) y `check_output.py` comprueba que dicen exactamente lo mismo.

| Markdown | PDF (`md_to_pdf.py`, reportlab) | DOCX (`md_to_docx.py`, python-docx) |
|---|---|---|
| `#`…`######` | Títulos (hasta 4 niveles de estilo) | Estilos «Título 1…6» de Word (navegables) |
| Párrafos, `**negrita**`, `*cursiva*`, `` `código` `` | Sí | Sí (código en Consolas) |
| `[texto](url)` | Enlace | Hipervínculo real |
| Listas con viñetas y numeradas, anidadas | Sí | Estilos de lista de Word hasta 3 niveles; cada lista numerada empieza en su número |
| `> cita` | Barra lateral | Estilo «Cita» |
| Bloques de código | Monoespaciada sobre fondo gris | Monoespaciada |
| Tablas | Rejilla con cabecera sombreada, columnas de igual ancho | Tabla «Table Grid», cabecera en negrita que se repite en cada página |
| `---` | Línea | Borde inferior de párrafo |
| `<!-- comentario -->` | No se imprime | No se escribe |
| Imágenes `![alt](…)` | Solo el texto alternativo | Solo el texto alternativo |
| Saltos duros (dos espacios o `<br>`) | Sí | Sí |

No soportado: imágenes, notas al pie, HTML con texto (`check_markdown.py` avisa), listas de tareas.

## PDF

- Fuente: Helvetica si todo el texto cabe en cp1252; si no, DejaVu Sans; los caracteres que DejaVu no tiene (chino, japonés…) se escriben con una fuente TrueType de reserva encontrada con `fc-list`. Si ninguna fuente instalada tiene un carácter, el script **falla** y lo dice (nunca lo pierde en silencio).
- Tablas con muchas columnas: `finalize.py` genera el PDF apaisado si alguna tabla tiene ≥ 7 columnas (`--landscape si|no|auto`; o `md_to_pdf.py --landscape`).
- Pie `pág. N` en cada página (el check lo ignora).

## DOCX

- Plantilla por defecto de python-docx (Calibri 11). El título del documento (propiedades) es el primer `#`.
- La numeración de listas es automática de Word: el texto no contiene los números; `check_output.py` lo tiene en cuenta.

## Verificación (`check_output.py`)

- **PDF**: texto extraído con pypdf, sin el pie; se compara con las palabras visibles del `.md` más los números de las listas. Signos: iguales, descontando viñetas y el punto tras cada número de lista.
- **DOCX**: párrafos y celdas en el orden del cuerpo; palabras y signos idénticos.
- Mismas palabras en otro orden → AVISO (celdas largas de tablas que el extractor de PDF intercala); cualquier diferencia → FALLO.
- Un `.pdf`/`.docx` más antiguo que su `.md` → FALLO: regenéralo.

## Revisión visual (obligatoria)

`pdftoppm -r 70 -png salida.pdf /tmp/pg` y mira las páginas con Read; para el DOCX, `soffice --headless --convert-to pdf --outdir /tmp/dx salida.docx` y lo mismo. Busca títulos huérfanos al pie, tablas demasiado estrechas (usa apaisado) y bloques de código cortados.
