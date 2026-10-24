# Detección de voz con modelo local (opcional, NO implementado en los scripts)

La skill no usa modelos: `silencedetect` basta en la mayoría de los casos. Este documento recoge la alternativa por si un audio muy ruidoso o con música de fondo da demasiados cortes `hard`.

## Opción: Silero VAD

- Modelo pequeño (~2 MB) de detección de actividad de voz, corre en CPU y en local; paquete `silero-vad` (usa PyTorch) o su versión ONNX con `onnxruntime`. Se descarga una sola vez; luego funciona sin red.
- Idea de integración: leer el audio a 16 kHz mono (`ffmpeg -i audio -ac 1 -ar 16000 -f wav -`), obtener los segmentos de voz con `get_speech_timestamps` y usar los huecos entre segmentos como lista de silencios en lugar de la de `silencedetect`. `plan_cuts()` de `scripts/split_audio.py` solo necesita una lista `[(inicio, fin)]`, así que el cambio se limita a `detect_silences()`.

## Por qué no es el valor por defecto

- Añade dependencias pesadas (PyTorch ~2 GB, u onnxruntime ~50 MB) para un problema que ffmpeg resuelve.
- No se ha probado en este repositorio. Si se implementa, ponlo tras un flag `--vad silero` y sus dependencias en un `requirements-vad.txt` aparte.
