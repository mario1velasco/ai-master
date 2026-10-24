---
name: any-to-any
description: >
  Convierte cualquier fichero (PDF, Word, PowerPoint, Excel, CSV, HTML, EPUB,
  JSON, ODT/RTF, texto, imágenes, PDF escaneados y audios) a Markdown, PDF y/o
  DOCX con exactamente el mismo contenido: sin inventar, sin resumir y sin
  corregir nada, solo dando formato. Pregunta siempre el formato de salida.
  Actívala cuando pidan pasar, convertir o exportar uno o varios ficheros a
  .md, .pdf o .docx, o «sacar el texto» de un documento manteniendo su
  contenido íntegro.
---

# Any to Any

Entrada: **uno o varios ficheros de casi cualquier tipo**. Salida: **`.md`, `.pdf` y/o `.docx`** (lo que elija el usuario) con **el mismo contenido que el original**. Todo pasa por Markdown, el formato pivote que se puede verificar palabra a palabra:

```
entrada ─► extracción automática ─► bruto.md ─► (tú: solo formato) ─► final.md ─► .md / .pdf / .docx
           markitdown · hojas propias · img-to-text · audio-split+audio-decoder            (por script, verificados)
```

Delega en las skills hermanas (deben estar como carpetas hermanas): imágenes y PDF escaneados → `img-to-text`; audios → `audio-split` + `audio-decoder`. Ejecuta los scripts desde esta carpeta con el entorno compartido de la raíz del repo (si no existe: `python3 ../scripts/setup_env.py`; propónselo al usuario, no lo instales sin avisar; después `PY="$(git rev-parse --show-toplevel)/.venv/bin/python"` y `$PY scripts/…`, sin `../` en la ruta).

## Reglas que mandan sobre todo lo demás

1. **Mismo contenido.** Mismas palabras, cifras, signos, idioma y orden de lectura. No corrijas faltas, no traduzcas, no resumas, no completes, no añadas títulos, rótulos ni explicaciones. Lo que no se lee: `[ilegible]` / `[dudoso: …]` (solo en imágenes y audio).
2. **El formato sí lo pones tú**, parecido al original: títulos, listas, tablas, negritas, citas, código. Lee `references/reglas_formato.md` antes de tocar nada.
3. **El formato de salida lo elige el usuario.** Nunca lo decidas tú.
4. **Nunca sobrescribas las entradas**: la salida va a una carpeta nueva.

## Flujo de trabajo

1. **Pregunta el formato de salida (siempre).** Si el usuario no lo ha dicho ya de forma explícita, pregúntalo con `AskUserQuestion` en multiselección: **Markdown (.md)**, **PDF (.pdf)**, **Word (.docx)**. Si hay **varias entradas**, pregunta también en la misma llamada si quiere **un documento por entrada** (`separado`) o **uno solo con todo en orden** (`combinado`). Elige la carpeta de salida: si no dice otra, una nueva `convertido_<nombre>/` junto a las entradas.
2. **Inventario.** `$PY scripts/inventory.py ENTRADAS... --output-dir SALIDA --formats md,pdf,docx --mode separado|combinado`
   - Código **3** = **para y pregunta** lo que pone en «PREGUNTAR AL USUARIO» (formatos o modo sin elegir, orden dudoso de una carpeta). Reejecuta con `--formats`, `--mode` y/o `--order FICHERO` (un nombre por línea). Nunca adivines el orden.
   - Indica el tipo de cada entrada, si un PDF está **escaneado** (sin capa de texto) o tiene **páginas sin texto**, y la duración del audio (avisa del tiempo: ≈ 1/3 de la duración en CPU).
   - Formatos admitidos en `references/formatos_entrada.md`; lo demás se ignora con AVISO.
3. **Extracción.** `$PY scripts/convert_docs.py SALIDA/trabajo` → `trabajo/unidades/uNN_<nombre>/bruto.md` por documento, hoja de cálculo o texto (no edites `bruto.md`). Lee lo que imprime:
   - **AVISO OMITIDO?/AÑADIDO?**: un segundo lector independiente (pypdf, python-docx, python-pptx, BeautifulSoup) ve palabras distintas. Mira `segundo_lector.txt` y el original; si markitdown perdió texto, recupéralo en `final.md` dentro de un bloque `<!-- original: segundo_lector.txt -->…<!-- /original -->` (ver `references/reglas_formato.md`) y dilo.
   - **PENDIENTE: PDF escaneado / páginas SIN TEXTO** → paso 5.
   - **PENDIENTE: imágenes incrustadas** (docx/pptx/xlsx/epub, extraídas a `incrustadas/`) → **pregunta** al usuario si quiere transcribir el texto de esas imágenes (markitdown no lo lee). Si dice que sí, paso 5.
   - Los formatos office antiguos (doc, odt, rtf, ppt, odp, ods) se convierten antes con LibreOffice (`soffice`); avisa de que la conversión puede alterar algo.
4. **Audios** (si los hay), **en segundo plano**: `$PY scripts/process_audio.py SALIDA/trabajo` (opciones: `--model small`, `--language es`). Divide, transcribe en local con Whisper, verifica y deja `bruto.md` con el texto literal. Es reanudable. Mientras, sigue con lo demás.
5. **Imágenes, PDF escaneados, páginas sin texto e imágenes incrustadas**: flujo de `../img-to-text/SKILL.md` (lee su `references/transcription_rules.md`): `prepare_images.py` → mira **cada trozo** con Read → `partes/NN_<nombre>.md` → `join_parts.py` → `check_transcription.py` y contrasta cada aviso con `zoom_image.py`. Carpetas de trabajo:
   - imágenes sueltas: **todas juntas** en `SALIDA/trabajo/imagenes` (`prepare_images.py IMG1 IMG2 … --output-dir SALIDA/trabajo/imagenes`, en el orden del inventario); cada imagen queda en su parte `partes/NN_<nombre>.md` y no hace falta más.
   - PDF escaneado: `prepare_images.py trabajo/unidades/uNN_<nombre>/paginas --output-dir trabajo/unidades/uNN_<nombre>/img` y `join_parts.py` → `img/transcripcion.md`.
   - páginas sin texto de un PDF mixto o imágenes incrustadas: transcríbelas igual (en `uNN_<nombre>/img`) e **insértalas en su sitio** de `final.md` dentro de un bloque marcado, que `check_markdown.py` compara con su parte:
     ```
     <!-- transcripcion: img/partes/03_pag_007.md -->
     …el texto de la parte, sin cambiar nada…
     <!-- /transcripcion -->
     ```
6. **Formato (tú).** Por cada unidad: copia `bruto.md` a `final.md` en la misma carpeta y haz **ediciones puntuales con Edit** (no reescribas el documento entero) siguiendo `references/reglas_formato.md`. En PDF compáralo con las vistas de página (`vista/pag_NNN.png`, míralas con Read) para recuperar títulos, listas, tablas y el orden de lectura. Si `bruto.md` ya está bien, no crees `final.md`. Para imágenes y escaneados la referencia es la transcripción (`img/transcripcion.md` o la parte); créales `final.md` solo si hay que retocar el formato.
7. **Verifica cada `final.md`.** `$PY scripts/check_markdown.py trabajo/unidades/uNN_<nombre>/final.md --reference trabajo/unidades/uNN_<nombre>/bruto.md`
   - **FALLO** por palabras o enlaces AÑADIDOS: quítalos (nunca se permiten). Tabla con columnas desiguales o código sin cerrar: arréglalo.
   - **AVISO QUITADO**: solo valen artefactos de paginación (cabeceras/pies/números de página repetidos); si no es eso, restáuralo. Lo que quites, dilo en la entrega.
   - **AVISO MOVIDO / SIGNOS**: correcto si reordenaste según la vista de página o convertiste «1.»/«•» en listas; si no, revísalo.
8. **Genera y entrega.** `$PY scripts/finalize.py SALIDA/trabajo` (`--name NOMBRE` para el combinado, `--landscape si|no|auto`): vuelve a verificar cada unidad, monta los `.md` (separado: uno por entrada; combinado: todos en orden separados por `<!-- fuente N: nombre -->` y `---`), genera el `.pdf` (`md_to_pdf.py`) y el `.docx` (`md_to_docx.py`) que se pidieran y comprueba con `check_output.py` que dicen **exactamente** lo mismo que el `.md` (palabras y signos). Se niega si falta algo. Después **mira** el resultado: PDF con `pdftoppm -r 70 -png SALIDA/x.pdf /tmp/pg` y Read; DOCX convirtiéndolo a PDF con `soffice --headless --convert-to pdf`.
9. **Informa.** Rutas entregadas, orden, formatos; palabras quitadas y por qué; `[ilegible]`/`[dudoso]`; páginas sin texto, imágenes incrustadas no transcritas, cabeceras/pies no incluidos, fórmulas sin valor, avisos sin resolver y la advertencia de que el audio es transcripción automática.

Si algo falla, sigue la norma del repo: arregla la causa, vuelve a ejecutar y documéntalo en `references/errores_conocidos.md`.

## Salida

```
SALIDA/
├── <nombre>.md / .pdf / .docx    # (separado) uno por entrada, solo los formatos pedidos
├── documento.md / .pdf / .docx   # (combinado) todo en orden
└── trabajo/                      # material auditable
    ├── inventario.json · conversion.json
    ├── imagenes/                 # trabajo de img-to-text para imágenes sueltas
    ├── salida/                   # .md montados + .pdf/.docx antes de copiarlos
    └── unidades/uNN_<nombre>/
        ├── bruto.md              # extracción automática (no se edita)
        ├── final.md              # tu versión con formato (si hizo falta)
        ├── segundo_lector.txt    # extracción independiente de control
        ├── estado.json           # avisos y pendientes de la unidad
        ├── vista/ · paginas/ · img/ · incrustadas/ · convertido/ · trozos/ · transcripcion/
```

Ejemplos en `examples/` (entradas pequeñas y su salida real en md, pdf y docx).

## Límites deliberados

- La extracción es tan buena como markitdown: en PDF se pierde la estructura (títulos, tablas) y a veces el orden de lectura en columnas; por eso hay vista de página y segundo lector. No lee texto dentro de imágenes de un documento ni de PDF con capa de texto (solo páginas completas sin texto).
- Word: markitdown no incluye **cabeceras y pies de página** (se avisa con su texto) ni conserva las citas. Excel: se escriben los **valores guardados** (punto decimal, fechas ISO, TRUE/FALSE), con porcentajes y decimales fijos según su formato pero sin formato regional ni de moneda; fórmulas sin valor guardado quedan vacías (se avisa). La primera fila de cada hoja hace de cabecera.
- Los verificadores comparan palabras y signos, no el significado ni el formato visual: la revisión a ojo del resultado es obligatoria.
- PDF/DOCX de salida: sin imágenes (quedan como comentario invisible `<!-- imagen … -->`), sin notas al pie ni HTML. Caracteres sin ninguna fuente instalada que los tenga (p. ej. emojis en color) hacen fallar `md_to_pdf.py` en vez de perderse.
- Audio: transcripción automática (errores en nombres propios y jerga; no se corrigen ni se separan hablantes). Vídeo no soportado (extrae antes el audio con `ffmpeg -i video.mp4 -vn audio.m4a`).
- No hay red: no convierte URLs; descarga antes la página como `.html`.
