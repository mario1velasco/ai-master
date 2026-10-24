---
name: media-resume
description: >
  Convierte audios y/o imágenes en un resumen extenso, fiel y sin inventar nada,
  de principio a fin: ordena las entradas, divide y transcribe los audios en
  local (Whisper), transcribe las imágenes palabra por palabra, lo junta todo en
  orden y genera descripcion.md, resumen.md y resumen.pdf. Actívala cuando el
  usuario adjunte uno o varios audios, imágenes, o ambos, y quiera su resumen o
  «de qué trata», sin pedir los pasos intermedios.
---

# Media Resume

Orquesta cuatro skills hermanas para ir de **audios e imágenes** a un **resumen en Markdown y PDF**. No reimplementa nada: llama a los scripts de `audio-split`, `audio-decoder`, `img-to-text` y `text-resume`, y automatiza lo mecánico (inventario, procesado de audio, montaje de la fuente, entrega). Las partes de **leer y redactar** las haces tú, siguiendo las reglas de esas skills. Ejecuta los scripts desde esta carpeta con `python3 scripts/<script>.py`.

```
entradas ─► inventory ─► (preguntar orden) ─┬► process_audio  [audio-split + audio-decoder] ─┐
                                            └► imágenes       [img-to-text, lo lees tú]     ├► build_source ─► text-resume ─► finalize
                                                                                            ┘     (fuente/)      (lees y redactas)   (entrega)
```

## Flujo de trabajo

0. **Entorno (una vez).** `python3 ../scripts/setup_env.py` crea el `.venv` compartido de la raíz del repo (el mismo para todas las skills) con todas las dependencias y avisa si falta `ffmpeg`. Todos los scripts posteriores usan ese `.venv` por su cuenta. Los modelos (Whisper `turbo` ≈ 1,6 GB, OCR) se descargan la primera vez; avisa al usuario antes de la primera ejecución.
1. **Inventario y orden. Aquí se pregunta.** Elige la carpeta de salida (si el usuario no dice otra: una carpeta nueva `resumen_<nombre>/` junto a las entradas) y ejecuta
   `python3 scripts/inventory.py ENTRADAS... --output-dir SALIDA`.
   Si termina con código **3**, **no sigas**: pregunta al usuario lo que indica «PREGUNTAR» (orden dudoso dentro de un tipo; orden entre audios e imágenes: `audio,images`, `images,audio` o intercalado `a01,img,a02`) y reejecuta con `--audio-order/--images-order FICHERO` (un nombre por línea) y/o `--sources-order`. Nunca adivines el orden: el resumen sigue el orden de las fuentes. Comunica al usuario la duración estimada de la transcripción.
2. **Audios** (si los hay). `python3 scripts/process_audio.py SALIDA/trabajo` **en segundo plano** (dura ≈ 1/3 de la duración del audio en CPU) y sigue el log. Divide los audios de más de 8 min en trozos de ~4 min cortando en silencios (si salen muchos cortes duros, repite solo con -30 dB), los transcribe con Whisper y verifica. Es reanudable. Mientras corre, haz el paso 3.
3. **Imágenes** (si las hay). Sigue `../img-to-text/SKILL.md` con `SALIDA/trabajo/imagenes` como carpeta de trabajo: `prepare_images.py` → mira **cada trozo** con Read → escribe `partes/NN_<nombre>.md` sin cambiar ninguna palabra → `join_parts.py` → `check_transcription.py` y contrasta cada aviso con `zoom_image.py`. Lee `../img-to-text/references/transcription_rules.md`.
4. **Monta la fuente.** Cuando audio e imágenes estén listos: `python3 scripts/build_source.py SALIDA/trabajo` (usa el orden confirmado; `--order` para cambiarlo). Crea `trabajo/fuente/NN_*.txt|md` en orden y se niega si falta alguna unidad.
5. **Resume.** Sigue `../text-resume/SKILL.md` con `SALIDA/trabajo/fuente` como entrada y `SALIDA/trabajo/resumen` como carpeta de trabajo: `collect_texts.py … --files-from SALIDA/trabajo/orden_final.txt` (el orden ya confirmado; sin él puede dar «ambiguo» por los números de los nombres originales) → lee **todos** los trozos → notas de lectura y comprensión global → `descripcion.md` → `resumen.md` (extenso, sin inventar; lee `../text-resume/references/writing_rules.md`) → `check_summary.py` y revisa cada aviso → `md_to_pdf.py`. Particularidades de esta fuente en `references/source_notes.md` (transcripción automática con errores, imágenes con marcadores de dudas).
6. **Entrega.** `python3 scripts/finalize.py SALIDA/trabajo` comprueba `.md` ↔ fuente ↔ PDF (el PDF debe coincidir palabra por palabra) y deja en `SALIDA/`: `resumen.md`, `resumen.pdf`, `descripcion.md` y `transcripciones/` (la fuente en orden). `trabajo/` queda como material auditable.
7. **Informa.** Rutas, qué se procesó y en qué orden, tiempos, y **limitaciones concretas**: pasajes de audio dudosos, `[ilegible]`/`[dudoso]` en imágenes, avisos de los verificadores no resueltos, datos sensibles que has omitido del resumen y siguen en `transcripciones/`.

## Reglas que no se saltan

- **Preguntar el orden** cuando es dudoso o hay audios e imágenes a la vez. Nada de suposiciones silenciosas.
- **No inventar.** Lo que aparece en el resumen sale de la transcripción o de las imágenes; lo dudoso se dice como dudoso. Las citas entre comillas son literales, con sus errores.
- **Leer todo antes de redactar**, trozo a trozo, y no resumir desde los avisos de un script.
- **Privacidad:** el audio y las imágenes se procesan en local; solo se contacta con Hugging Face para descargar modelos. Si el contenido tiene datos personales o de salud (identificadores, teléfonos), no los copies al resumen y dilo.
- No sobrescribas las entradas. No instales dependencias fuera del `.venv` compartido de la raíz.

## Límites deliberados

- La transcripción de voz es automática: errores en nombres propios, jerga y voz solapada; no separa hablantes ni traduce (solo transcribe en el idioma original).
- Las imágenes se leen con visión; el OCR es solo un segundo lector heurístico. Manuscrito, fotos borrosas o texto minúsculo pueden dar `[ilegible]`.
- `check_summary.py` y `check_transcription.py` son heurísticos: señalan, no demuestran. La relectura manual es obligatoria.
- No resume vídeo ni PDF (renderiza páginas a imagen antes si hace falta) ni imágenes sin texto.
- Con un audio de varias horas en CPU el proceso dura horas: avisa antes y usa `--model small` solo si el usuario prioriza velocidad sobre calidad.
