# Formatos y códecs

## `-c copy` frente a recodificar

- **Copy (por defecto cuando la extensión de salida = la de entrada):** no decodifica, es casi instantáneo y no pierde calidad. En AAC/MP3 los cortes se alinean a frames (~23 ms en AAC a 44,1 kHz). Puede quedar un pequeño desfase de decenas de ms respecto al punto pedido; `check_split.py` lo tolera (1 s por trozo).
- **Recodificar (`--reencode` o `--format` distinto):** necesario para cambiar de formato o para cortes con precisión de muestra. Cuesta CPU y, en formatos con pérdida, una pasada extra de compresión.

## Formatos de salida

| `--format` | Códec | Ajustes |
|---|---|---|
| `m4a` | AAC en MP4 | 128 kbit/s |
| `aac` | AAC crudo (ADTS) | 128 kbit/s; con entrada `.aac` se copia sin recodificar |
| `mp3` | libmp3lame | 128 kbit/s |
| `opus` | libopus | 64 kbit/s (ideal para voz) |
| `flac` | flac | sin pérdida |
| `wav` | PCM 16 bit | sin compresión; ~10 MB/min en estéreo 44,1 kHz |

Para voz y transcripción, `opus` a 64 kbit/s o `m4a` son suficientes. Si la entrada tiene una extensión no listada, la salida por defecto es `m4a` recodificado.

## Notas

- **AAC crudo (`.aac`, ADTS):** no tiene índice ni duración en cabecera. `ffprobe` la estima por bitrate y puede errar más de 10 s en una hora (en `audio/6.aac`: 4473,7 s estimados frente a 4489,0 s reales), y el seek de entrada se desvía ~1 s. Los scripts lo detectan, miden decodificando y cortan con seek de salida. Si puedes, convierte a m4a antes.
- Los metadatos y carátulas se descartan.
- Para que un audio con `.m4a` de varios GB no sature disco, comprueba el espacio libre: con `copy` los trozos suman aproximadamente el tamaño del original.
