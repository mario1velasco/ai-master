# Markdown soportado y PDF

`scripts/md_to_pdf.py` usa `markdown-it-py` (CommonMark + tablas) y `reportlab`. No necesita pandoc, LaTeX ni librerías del sistema.

## Soportado

| Markdown | Resultado |
|---|---|
| `# … ####` | Títulos (el primer `#` es el título del PDF) |
| Párrafos, `**negrita**`, `*cursiva*`, `` `código` `` | Texto con estilos |
| `- ` / `1. ` (anidadas) | Listas con viñetas / numeradas |
| `> cita` | Cita con barra lateral |
| ```` ``` ```` | Bloque de código en mono |
| Tablas `\|a\|b\|` con cabecera | Tabla con cabecera sombreada y columnas de igual ancho |
| `---` | Separador |
| `[texto](url)` | Enlace (el texto es visible; la URL solo es el enlace) |

No soportado: imágenes (se imprime el texto alternativo), HTML embebido, notas al pie, listas de tareas.

## Fuentes

- Si el texto cabe en cp1252 (español, francés, etc., con comillas y guiones tipográficos) usa Helvetica, con cursiva real.
- Si hay caracteres fuera de cp1252 (→ ≥ ✓, alfabetos no latinos) usa DejaVu Sans (Linux; `/usr/share/fonts/truetype/dejavu`). La cursiva se muestra como texto normal. En otros sistemas pasa `--font /ruta/fuente.ttf`.
- Los caracteres que DejaVu tampoco tiene (chino, japonés, coreano…) se escriben con una fuente TrueType de reserva que busca `fc-list` (p. ej. Droid Sans Fallback). Si ninguna fuente instalada tiene un carácter (p. ej. emojis en color), `md_to_pdf.py` **falla** y lista los caracteres, en vez de perderlos en silencio: instala una fuente que los tenga o pasa `--font`. Ver `errores_conocidos.md`.

## Garantía de contenido idéntico

El PDF solo contiene el texto del `.md` más un pie con `pág. N`. `check_summary.py --pdf` extrae el texto del PDF (pypdf) y lo compara palabra por palabra con el del `.md` (incluyendo los números de las listas numeradas); si no coincide, falla y muestra las diferencias. Si cambias el `.md`, **regenera el PDF**.

## Qué revisar a ojo

Saltos de página que dejen un título solo (el conversor mete un salto condicional antes de cada título para evitarlo, pero comprueba la última línea de cada página), tablas muy anchas o con celdas largas (se parten por filas pero no por columnas). Convierte una página a imagen (`pdftoppm -r 70 -png resumen.pdf pg`) y míralas.
