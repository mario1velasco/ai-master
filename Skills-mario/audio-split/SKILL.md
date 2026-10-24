---
name: audio-split
description: >
  Divide un archivo de audio muy largo (aac/m4a, mp3, wav, flac, opus; podcasts,
  reuniones, clases, grabaciones) en trozos de unos 4 minutos, cortando en
  silencios para no partir palabras. Actívala cuando pidan trocear, dividir o
  segmentar un audio, o prepararlo para transcribir o procesar por partes.
---

# Audio Split

Divide un audio largo en trozos de ~4 min con `ffmpeg` y Python 3 (solo biblioteca estándar). No usa modelos de IA: cortar en silencios con `silencedetect` es suficiente y no requiere descargas. Ejecuta los scripts desde esta carpeta. No instales nada automáticamente; si falta `ffmpeg`/`ffprobe`, díselo al usuario (`sudo apt install ffmpeg`).

## Flujo de trabajo

1. **Confirma la entrada.** Ruta del audio, duración de trozo (por defecto 240 s) y formato de salida (por defecto el mismo que la entrada). No sobrescribas el original; elige un directorio de salida nuevo.
2. **Inspecciona.** `python3 scripts/probe_audio.py /ruta/audio.m4a` muestra duración, códec y nº de trozos previstos (en `.aac` crudo tarda unos segundos: decodifica para medir la duración real).
3. **Divide.** `python3 scripts/split_audio.py /ruta/audio.m4a --output-dir /ruta/out`. Por defecto busca el silencio más cercano a cada múltiplo de 4 min (±20 s) y corta ahí; si no hay silencio, hace un corte duro. Con el mismo formato de entrada copia el stream (`-c copy`): rápido y sin pérdida. Un resto final menor de 30 s se fusiona con el trozo anterior.
4. **Verifica.** `python3 scripts/check_split.py /ruta/out --max-chunk-seconds 300` comprueba que existen todos los trozos, que sus duraciones coinciden con `manifest.json` y que la suma coincide con el original.
5. **Ajusta si hace falta.** Muchos cortes `hard` en `manifest.json` indican ruido de fondo o un umbral inadecuado: repite con `--silence-db -30 --min-silence 0.3` (suele bastar en voz muy normalizada), `--window 30` o `--min-silence 0.25` y usa `--force` para reescribir. Para cortes exactos cada N s usa `--hard-cuts`.
6. **Entrega.** Indica la carpeta, el nº de trozos, el modo (`copy`/`reencode`), cuántos cortes fueron duros y las limitaciones que apliquen.

Lee `references/workflow.md` para elegir parámetros, `references/formats_and_codecs.md` para `copy` frente a recodificar y `references/vad_optional.md` si el audio es muy ruidoso y quieres un detector de voz con modelo local.

## Salida

```
out/
├── audio_chunk_001.m4a … audio_chunk_NNN.m4a
└── manifest.json        # por trozo: file, start, end, duration, cut (start|silence|hard)
```

Ver `examples/manifest.example.json`.

## Límites deliberados

- Los trozos duran ~4 min ± la ventana (≈3:40–4:20), no exactamente 4:00. Para duración exacta usa `--hard-cuts`.
- Con `-c copy` los cortes caen en límites de frame del códec (~20-30 ms de precisión). Para precisión de muestra usa `--reencode`.
- Se procesa solo el primer stream de audio; se descarta vídeo y metadatos (`-vn`, `-map_metadata -1`).
- `silencedetect` es una heurística por nivel de volumen: con música o ruido constante puede no hallar silencios y caerá a cortes duros.
- En AAC crudo (`.aac`, ADTS) no hay índice: `probe_audio.py`/`check_split.py` decodifican el archivo para medir la duración (tarda unos segundos) y el corte usa seek exacto, más lento que en m4a.
- No transcribe ni analiza el contenido.
