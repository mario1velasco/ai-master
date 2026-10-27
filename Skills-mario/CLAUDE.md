# Skills-mario

Colección de **skills** para Claude Code: cada carpeta de primer nivel es una skill independiente que automatiza una tarea con audio, imágenes, texto o presentaciones. Todo el contenido está en español.

## Estructura común de cada skill

```
<skill>/
├── SKILL.md           # instrucciones y flujo de trabajo (lo que lee Claude); su cabecera YAML (name, description) define cuándo se activa
├── requirements.txt   # dependencias de esa skill (referencia; se instalan desde el requirements.txt de la raíz)
├── scripts/           # scripts de Python que hacen el trabajo mecánico y las verificaciones
├── references/        # documentación de apoyo que SKILL.md manda leer en cada paso
├── examples/          # entradas/salidas de ejemplo
├── assets/            # plantillas y recursos (solo en algunas)
└── agents/openai.yaml # metadatos para otros agentes (no se usa en Claude Code)
```

## Convenciones

- **Ejecuta los scripts desde la carpeta de la skill**: `python3 scripts/<script>.py ...`.
- **Un único entorno virtual compartido**: `.venv/` en la **raíz del repo**, con las dependencias de todas las skills (`requirements.txt` de la raíz). **No crees `.venv` dentro de cada skill.** Se crea una vez con `python3 scripts/setup_env.py` (también comprueba `ffmpeg` y que las versiones instaladas sean las fijadas; vuelve a ejecutarlo tras actualizar el repo) y se usa así, desde la carpeta de la skill:
  ```bash
  PY="$(git rev-parse --show-toplevel)/.venv/bin/python"   # no uses ../.venv: Python avisa de sys.prefix inesperado
  $PY scripts/<script>.py ...
  ```
- **No instales dependencias sin avisar**: propón al usuario ejecutar `scripts/setup_env.py`. Si añades una dependencia a una skill, añádela también al `requirements.txt` de la raíz.
- **Todo se procesa en local** (Whisper, RapidOCR, ffmpeg); la primera ejecución descarga modelos a `~/.cache/huggingface` y después funciona sin red.
- **Orden ambiguo = preguntar.** Los scripts de ordenación devuelven código de salida `3` cuando no pueden deducir el orden de los ficheros (nombres sin números, series mezcladas…). En ese caso hay que parar y preguntar al usuario, nunca adivinar.
- **Fidelidad**: no inventar, no corregir, no resumir de más. Cada skill termina con un script `check_*.py` que verifica el resultado.
- **Nunca sobrescribir los originales**: la salida va a una carpeta nueva.
- `.venv/` no se edita ni se versiona (está en `.gitignore`).

## Las skills

### audio-split — trocear un audio largo
Divide un audio largo (aac/m4a, mp3, wav, flac, opus) en trozos de ~4 min cortando en silencios con `ffmpeg`, para no partir palabras. No usa IA; solo requiere `ffmpeg`/`ffprobe` (`sudo apt install ffmpeg`).

```bash
python3 scripts/probe_audio.py audio.m4a                       # duración, códec, nº de trozos previstos
python3 scripts/split_audio.py audio.m4a --output-dir out      # divide (genera manifest.json)
python3 scripts/check_split.py out --max-chunk-seconds 300     # verifica
```
Ajustes: `--silence-db -30 --min-silence 0.3`, `--window 30`, `--hard-cuts` (cortes exactos), `--reencode`, `--force`.

### audio-decoder — audio a texto
Transcribe en local con Whisper (`faster-whisper`) todos los audios de un directorio, los ordena (`_2` antes que `_10`) y produce un único `transcripcion_completa.txt`. Úsala sobre los trozos de audio-split.

```bash
python3 scripts/order_files.py /ruta/dir                       # propone el orden (código 3 = preguntar)
python3 scripts/transcribe_audio.py /ruta/dir                  # genera /ruta/dir/transcripcion/
python3 scripts/check_transcript.py /ruta/dir/transcripcion    # verifica
```
Modelo por defecto `turbo` (mejor calidad, ≈3× tiempo real en CPU); `--model small` es ~3× más rápido pero peor. Opciones: `--timestamps`, `--file-headers`, `--language es`, `--task translate`, `--force`. Es reanudable.

### img-to-text — imágenes a texto (OCR fiel)
Transcribe palabra por palabra el texto de imágenes (capturas, fotos, escaneos, pizarras) a un `.md`, sin corregir ni inventar. Claude lee las imágenes con visión y RapidOCR actúa de segundo lector para detectar errores. Usa `[ilegible]` / `[dudoso: ...]` cuando no se lee bien.

```bash
$PY scripts/prepare_images.py img1.png img2.png --output-dir trabajo   # orienta, amplía y trocea
# Claude lee cada trozo con Read y escribe trabajo/partes/NN_<nombre>.md
$PY scripts/join_parts.py trabajo                                      # une -> transcripcion.md
$PY scripts/check_transcription.py trabajo/transcripcion.md --work-dir trabajo
```
Los avisos del check se contrastan con `scripts/zoom_image.py`. Reglas en `references/transcription_rules.md`.

### text-resume — resumir textos largos
Lee a fondo un `.txt`/`.md` (o una carpeta de ficheros ordenados) y genera, sin inventar nada: `descripcion.md` (de qué trata), `resumen.md` (resumen extenso) y `resumen.pdf` (idéntico al resumen). Claude debe leer **todo** el texto antes de redactar.

```bash
python3 scripts/collect_texts.py /ruta/entrada --output-dir resumen   # ordena y crea texto_trabajo.txt + plan de lectura
# Claude lee por trozos, toma notas_de_lectura.md y redacta con assets/*_template.md
$PY scripts/check_summary.py ...                          # fidelidad
$PY scripts/md_to_pdf.py ...                              # resumen.md -> resumen.pdf
```
Reglas en `references/writing_rules.md` y `references/workflow.md`.

### media-resume — de audios e imágenes a resumen (orquestadora)
Pipeline completo: ordena entradas, divide y transcribe audios, transcribe imágenes, junta todo en orden y genera `descripcion.md`, `resumen.md` y `resumen.pdf`. No reimplementa nada: llama a audio-split, audio-decoder, img-to-text y text-resume (**deben estar como carpetas hermanas**). Úsala cuando el usuario adjunte audios y/o imágenes y quiera su resumen directamente.

```bash
python3 ../scripts/setup_env.py                                # (o desde la raíz, una vez) crea el .venv compartido
python3 scripts/inventory.py ENTRADAS... --output-dir SALIDA   # inventario y orden (código 3 = preguntar)
python3 scripts/process_audio.py SALIDA/trabajo                # audios (en segundo plano; reanudable)
# imágenes: flujo de img-to-text sobre SALIDA/trabajo/imagenes
python3 scripts/build_source.py SALIDA/trabajo                 # monta trabajo/fuente/ en orden
# resumen: flujo de text-resume sobre trabajo/fuente
python3 scripts/finalize.py ...                                # entrega
```

### any-to-any — cualquier fichero a md / pdf / docx (sin inventar)
Convierte casi cualquier entrada (PDF, Word, PowerPoint, Excel/CSV, HTML, EPUB, JSON, ODT/RTF vía LibreOffice, texto, imágenes, PDF escaneados, audios) al formato que elija el usuario (**se le pregunta siempre**: `.md`, `.pdf` y/o `.docx`), con el mismo contenido. Todo pasa por Markdown: extracción automática (`bruto.md`, con markitdown; conversor propio para hojas de cálculo) → Claude solo da formato (`final.md`) → PDF/DOCX por script. Delega imágenes y escaneados en img-to-text y audios en audio-split + audio-decoder (**deben estar como carpetas hermanas**). Cada paso se verifica palabra a palabra (y signos).

```bash
$PY scripts/inventory.py ENTRADAS... --output-dir SALIDA --formats md,pdf,docx --mode separado|combinado   # código 3 = preguntar
$PY scripts/convert_docs.py SALIDA/trabajo                  # bruto.md por unidad + segundo lector + vistas de PDF
$PY scripts/process_audio.py SALIDA/trabajo                 # audios (en segundo plano; reanudable)
# imágenes / PDF escaneados: flujo de img-to-text; formato: bruto.md -> final.md con Edit
$PY scripts/check_markdown.py .../final.md --reference .../bruto.md   # FALLO si se añade una palabra
$PY scripts/finalize.py SALIDA/trabajo                      # monta, genera pdf/docx y los verifica (check_output.py)
```
Reglas del paso de formato en `references/reglas_formato.md`; formatos en `references/formatos_entrada.md` y `formatos_salida.md`.

### presentacion-open — presentaciones PowerPoint
(Su `name` interno es `presentations-open`.) Crea y valida `.pptx` editables con `python-pptx`: se describe la presentación en un `deck.json` (esquema en `references/deck_schema.md`) y se compila con tablas y gráficos nativos, opcionalmente sobre una plantilla. Incluye validadores geométricos (márgenes, solapes, aritmética de tablas, integridad del paquete, fidelidad a plantilla).

```bash
$PY scripts/compile_deck.py deck.json --output out/presentation.pptx
$PY scripts/check_overflow.py out/presentation.pptx --spec deck.json
$PY scripts/check_package_integrity.py out/presentation.pptx
$PY scripts/check_table_arithmetic.py out/presentation.pptx --spec deck.json     # si hay tablas
$PY scripts/check_template_fidelity.py plantilla.pptx out/presentation.pptx --allow-changed-slide N
$PY scripts/inspect_presentation.py out/presentation.pptx                        # localizar problemas
```
No renderiza diapositivas: hay que revisarlas visualmente. No sobrescribe la fuente. Guías de diseño y redacción en `references/`.

### campus-video-download — vídeos detrás de un login (campus EBIS)
Descarga vídeos protegidos por login (p. ej. grabaciones del campus de EBIS / Blackboard, alojadas en Bunny Stream por HLS) **con la sesión del Chrome en el que el usuario ya está logueado**: `yt-dlp --cookies-from-browser chrome` lee sus cookies (llavero de GNOME vía `secretstorage`) y `pycryptodomex` descifra el HLS AES-128 sin pasar por ffmpeg. No abras un Chrome nuevo o privado: no tiene la sesión. Alternativa con Playwright (`scripts/download_video.py`, perfil propio y login otra vez) solo si no se pueden leer las cookies.

```bash
$YTDLP --cookies-from-browser chrome --simulate --print "%(title)s | %(duration_string)s" "URL"   # prueba la sesión
$YTDLP --cookies-from-browser chrome --newline --no-mtime -o "SALIDA/clase.%(ext)s" "URL"          # en segundo plano
$PY scripts/check_video.py SALIDA/clase.mp4                                                         # ffprobe, duración, audio
```
Después: `ffmpeg -i video.mp4 -vn -c:a copy audio.m4a` → media-resume para resumir la clase.

## Cadena típica

```
audio largo ─► audio-split ─► audio-decoder ─┐
imágenes ────► img-to-text ──────────────────┴─► text-resume ─► descripcion.md + resumen.md + resumen.pdf
                     (media-resume automatiza todo este recorrido)

cualquier fichero ─► any-to-any ─► .md / .pdf / .docx con el mismo contenido (usa img-to-text y audio-* por dentro)
```

## Al modificar o añadir skills

- Mantén `SKILL.md` como fuente de verdad del flujo; si cambias un script, actualiza su sección y `references/`.
- La `description` de la cabecera YAML decide cuándo se activa la skill: debe decir qué hace y cuándo usarla.
- Los scripts auxiliares compartidos (`_ordering.py`, `_text.py`, `_common.py`, `_env.py`, `_md.py`) están duplicados por skill a propósito, para que cada una sea autónoma (excepto media-resume y any-to-any, que dependen de sus hermanas). `md_to_pdf.py` está en text-resume y en any-to-any: si cambias uno, cambia el otro.

## Cuando una skill falla: arregla el bug y documéntalo

Cada vez que uses una skill y falle (error de un script, resultado incorrecto, instrucción de `SKILL.md` que no funciona):

1. **Arregla la causa raíz** en la skill (script, `SKILL.md` o `references/`), no solo el caso puntual con un apaño temporal. Vuelve a ejecutar la skill para comprobar que el fallo desaparece.
2. **Documéntalo para que no vuelva a pasar**, en la propia skill:
   - Añade una entrada en `<skill>/references/errores_conocidos.md` (créalo si no existe) con: **síntoma** (mensaje de error o comportamiento), **causa**, **solución aplicada** y **cómo evitarlo**. Si el bug es de `media-resume` pero nace en una skill hermana, documéntalo en la hermana y enlázalo.
   - Si el fallo se previene con un paso, una comprobación o una advertencia, añádela también en el flujo de `SKILL.md` y enlaza `references/errores_conocidos.md` desde allí.
   - Si es posible, haz que el script lo detecte y dé un mensaje claro (validación de entrada, comprobación de dependencias) en vez de un traceback.
3. **Díselo al usuario**: qué falló, qué cambiaste y dónde quedó documentado.

Formato de entrada:

```markdown
## <título corto del error> (AAAA-MM-DD)
- **Síntoma:** ...
- **Causa:** ...
- **Solución:** ... (fichero/línea modificado)
- **Prevención:** ...
```
