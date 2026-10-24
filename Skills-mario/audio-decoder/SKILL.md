---
name: audio-decoder
description: >
  Transcribe a texto, en local y con Whisper (faster-whisper), uno o varios
  audios (.aac, .m4a, .mp3, .wav…) de un directorio, los ordena y devuelve un
  único .txt con los textos en orden. Actívala cuando pidan pasar audios a texto,
  transcribir grabaciones o juntar la transcripción de trozos de un audio
  largo (p. ej. los generados por audio-split).
---

# Audio Decoder

Recibe la **ruta de un directorio** con audios, los ordena y los transcribe en local con `faster-whisper` (modelos Whisper de Hugging Face, sin API ni enviar el audio fuera). El resultado es un solo `.txt` con los textos concatenados desde el primer audio hasta el último. Ejecuta los scripts desde esta carpeta.

Instalación (no la hagas automáticamente; propónsela al usuario): usa el venv compartido de la raíz del repo, que se crea con `python3 ../scripts/setup_env.py` y se usa con `PY="$(git rev-parse --show-toplevel)/.venv/bin/python"` (`$PY scripts/...`; evita `../` en la ruta, da avisos). El primer uso descarga el modelo de Hugging Face a `~/.cache/huggingface` (turbo ≈ 1,6 GB, small ≈ 0,5 GB); después funciona sin red. Si la transcripción falla, mira antes `references/errores_conocidos.md` (p. ej. `av` incompatible: `setup_env.py` lo corrige).

## Flujo de trabajo

1. **Recibe la ruta del directorio.** Comprueba que existe y que contiene audios. Si el usuario da ficheros sueltos, pide el directorio o crea una carpeta de trabajo; no muevas los originales.
2. **Ordena y confirma el orden.** `python3 scripts/order_files.py /ruta/dir` lista el orden propuesto (orden natural por número: `_2` antes que `_10`).
   - Código de salida `0`: orden claro. Muéstraselo al usuario en una línea (primero → último) y sigue.
   - Código de salida `3` (**ambiguo**): **para y pregunta al usuario antes de transcribir.** Casos: nombres sin números, series mezcladas (`6_chunk_001` y `7_chunk_001`), varios números que cambian, números repetidos. Escribe el orden confirmado en un fichero (un nombre por línea) y úsalo con `--files-from`.
   - Un `AVISO` de huecos en la numeración (p. ej. falta el 3) no bloquea, pero díselo al usuario: puede faltar un audio.
3. **Elige modelo e idioma.** Por defecto `turbo` (buena calidad en español) y el idioma se detecta en el primer audio y se reutiliza en todos. Si hay prisa, `--model small` es ~3× más rápido pero comete bastantes errores. Lee `references/models.md`. Avisa de la duración estimada: en CPU, `turbo` ≈ 3× tiempo real (1 h de audio ≈ 20 min); `small` ≈ 10×.
4. **Transcribe.** `$PY scripts/transcribe_audio.py /ruta/dir`. Genera `/ruta/dir/transcripcion/`. Es reanudable: las partes ya transcritas se reutilizan (los filtros de limpieza se reaplican sobre ellas sin volver a transcribir); `--force` las rehace. En `manifest.json`, `elapsed_seconds` es el de la última ejecución, no el total si hubo reutilización. Opciones útiles: `--timestamps` (una línea por segmento con `[hh:mm:ss]` acumulado entre archivos), `--file-headers` (marca dónde empieza cada audio), `--language es`, `--task translate` (traducir **al inglés**).
5. **Verifica.** `python3 scripts/check_transcript.py /ruta/dir/transcripcion` comprueba que están todas las partes, que aparecen en el `.txt` final en el orden correcto y que la densidad de texto es plausible.
6. **Entrega.** Indica la ruta de `transcripcion_completa.txt`, el nº de archivos y su orden, el idioma, el modelo y las limitaciones (ver abajo). Si el audio es sensible, recuerda que todo se procesó en local.

## Salida

```
transcripcion/
├── transcripcion_completa.txt      # todos los audios, en orden
├── partes/NNN_<nombre>.txt|.json   # una por audio (el .json lleva segmentos con tiempos)
└── manifest.json                   # orden, duración, offset, idioma y palabras por audio
```

## Límites deliberados

- Whisper no es perfecto: incluso `turbo` comete errores con nombres propios, jerga médica o técnica y voz solapada; revisa lo importante. `small` es bastante peor (palabras deformadas).
- Puede inventar o repetir texto en silencios y ruido. El filtro de voz (VAD) está activado, las repeticiones dentro de un segmento se recortan a 3 y se descartan los segmentos con velocidad de habla imposible (>10 palabras/s: ecos de 0,1 s, vistos en un audio real), pero revisa los pasajes extraños.
- No distingue hablantes (no hay diarización) ni puntúa de forma fiable.
- `--task translate` solo traduce al inglés. Para otro idioma, transcribe y traduce el texto aparte.
- Los cortes entre trozos de un audio largo pueden partir una frase; los textos se concatenan tal cual. Con trozos de `audio-split` esto es poco frecuente porque se corta en silencios.
- Sin GPU compatible (CUDA 12 + cuDNN) usa CPU en `int8`; `--device auto` prueba la GPU y cae a CPU si falla.
