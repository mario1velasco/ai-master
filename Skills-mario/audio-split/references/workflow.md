# Elección de parámetros

## Algoritmo

1. `ffprobe` da la duración (en AAC crudo `.aac` se mide decodificando el archivo, porque `ffprobe` solo la estima).
2. Un solo paso `ffmpeg -af silencedetect` lista todos los silencios (inicio/fin). No escribe audio a disco.
3. Para cada objetivo (4 min, y los siguientes medidos desde el corte real anterior) se elige el silencio cuyo punto medio esté más cerca dentro de ±`--window`. Si no hay ninguno, corte duro en el objetivo.
4. Un resto final < 30 s se fusiona con el trozo anterior (el último trozo puede quedar algo más largo).
5. `ffmpeg -ss … -to … -i entrada` corta cada trozo (seek de entrada: rápido incluso con horas de audio; en AAC crudo se usa seek de salida, exacto pero más lento).

## Parámetros

| Parámetro | Por defecto | Cuándo cambiarlo |
|---|---|---|
| `--chunk-seconds` | 240 | Otra duración objetivo. Mínimo 60. |
| `--window` | 20 | Súbelo (30-45) si hay pocos silencios; bájalo (10) si necesitas trozos más uniformes. |
| `--silence-db` | -35 | Súbelo a -30/-25 con ruido de fondo (habitación, ventilador); bájalo a -40 en grabaciones muy limpias. |
| `--min-silence` | 0.4 | Bájalo a 0.25 con hablantes rápidos que apenas pausan. |
| `--hard-cuts` | off | Duración exacta, o cuando los silencios no importan. |

## Diagnóstico

- `manifest.json` → campo `cut`: `silence` (bien) o `hard` (no se halló silencio en la ventana).
- Si más de ~1/3 de los cortes son `hard`, ajusta `--silence-db` y `--window` y repite con `--force`.
- Audios muy normalizados (voz a ~-31 dB de media, como la grabación de ejemplo `audio/6.aac`): con -35 dB solo hubo silencios hasta el min 44 y 7 cortes duros; con `--silence-db -30 --min-silence 0.3` ninguno.
- Para estimar el nivel de ruido: `ffmpeg -i audio.m4a -af volumedetect -f null -` (mira `mean_volume`; el umbral útil suele estar 10-15 dB por encima del ruido de fondo).
