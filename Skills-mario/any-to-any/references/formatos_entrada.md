# Formatos de entrada

| Tipo (inventario) | Extensiones | Cómo se extrae | Qué vigilar |
|---|---|---|---|
| `doc` | `.pdf` (con capa de texto) | markitdown (pdfminer) | Sin títulos ni tablas; columnas y tablas pueden salir desordenadas → vistas de página en `vista/`. Las imágenes y gráficos no se leen. |
| `doc` | `.pdf` escaneado | `pypdfium2` renderiza las páginas a 200 ppp → img-to-text | Se detecta si ≥ ½ de las páginas tienen < 25 caracteres de texto. PDF mixto: solo las páginas sin texto van a img-to-text. |
| `doc` | `.docx` | markitdown (mammoth) | No incluye cabeceras/pies (se avisa con su texto); pierde citas y algunos estilos; imágenes → comentario + `incrustadas/`. |
| `doc` | `.pptx` | markitdown (python-pptx) | Títulos de diapositiva como `#`; notas del orador; tablas; gráficos solo si traen datos; imágenes → comentario + `incrustadas/`. |
| `doc` | `.html` `.htm` `.xhtml` | markitdown (BeautifulSoup + markdownify) | Ignora `<head>` (el `<title>` no sale); scripts y estilos fuera. |
| `doc` | `.epub` | markitdown | Capítulos en orden del índice. |
| `doc` | `.ipynb` | markitdown | Celdas de Markdown y de código; las salidas pueden no incluirse. |
| `doc` | `.json` `.jsonl` `.xml` `.rss` `.atom` | texto literal en un bloque de código | No se reformatea. |
| `sheet` | `.xlsx` `.xlsm` | conversor propio (openpyxl) | Valores guardados; `%` y decimales fijos según el formato de la celda; fechas ISO; booleanos TRUE/FALSE; fórmulas sin valor guardado → vacías con aviso; una tabla por hoja con su nombre como `##`; hojas ocultas marcadas con comentario. |
| `sheet` | `.xls` | conversor propio (xlrd) | Valores sin formato de número. |
| `sheet` | `.csv` `.tsv` | conversor propio (csv) | Separador detectado (`,` `;` tab `\|`); codificación detectada (utf-8, cp1252, latin-1). |
| `office` | `.doc` `.odt` `.rtf` `.wpd` → docx; `.ppt` `.pps` `.ppsx` `.odp` → pptx; `.ods` → xlsx | LibreOffice (`soffice --headless --convert-to`) y después como su tipo | Requiere LibreOffice instalado. La conversión puede cambiar detalles: revísalo. |
| `text` | `.txt` `.text` `.log` | texto escapado para Markdown (mismas palabras, mismos saltos de línea) | `convert_docs.py` comprueba que el escape no cambia ninguna palabra. |
| `text` | `.md` `.markdown` | se copia tal cual | |
| `image` | `.png .jpg .jpeg .webp .bmp .tif .tiff .gif` | img-to-text (visión + RapidOCR de control) | Ver `../img-to-text/SKILL.md`. |
| `audio` | `.aac .m4a .mp3 .wav .flac .opus .ogg` | audio-split + audio-decoder (Whisper local) | Transcripción automática; ≈ 1/3 de la duración en CPU con `turbo`. |

Otros formatos (vídeo, `.zip`, `.msg`, imágenes vectoriales…) se ignoran con AVISO. Para vídeo, extrae el audio con `ffmpeg -i video.mp4 -vn audio.m4a`; para un `.zip`, descomprímelo antes.

## Por qué no se usa markitdown para hojas de cálculo

markitdown pasa por pandas y cambia valores: `10` → `10.0`, celda vacía → `NaN`. Eso es inventar contenido, así que `convert_docs.py` usa su propio conversor.

## Rótulos de markitdown que se limpian

`convert_docs.py` quita lo que markitdown añade y no está en el original:

- `### Notes:` (pptx) → `<!-- notas del orador -->`; `<!-- Slide number: N -->` → `<!-- diapositiva N -->`.
- Imágenes `![nombre](PictureN.jpg)` → `<!-- imagen: nombre (PictureN.jpg) -->` (el nombre del fichero no es texto del documento).
- Fila de cabecera vacía en tablas de Word → se sube la primera fila real.

## Segundo lector

Para pdf, docx, pptx y html, `convert_docs.py` extrae el texto también con otra librería (pypdf, python-docx, python-pptx, BeautifulSoup) y compara las palabras con `bruto.md`. Los números de listas automáticas de Word/HTML no son texto y no se cuentan. Los avisos `OMITIDO?`/`AÑADIDO?` señalan, no demuestran: compruébalos en el original.
