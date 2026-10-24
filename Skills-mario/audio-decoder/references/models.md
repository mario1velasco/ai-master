# Modelos de transcripción

Se usa [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2): modelos Whisper convertidos, publicados en Hugging Face (`Systran/faster-whisper-*`). Se descargan una vez a `~/.cache/huggingface` (o a `--model-dir`) y luego se ejecutan 100 % en local. Para trabajar sin red, descarga antes el modelo y pásalo como ruta local en `--model`.

## Medidas reales (CPU 12 núcleos, `int8`, español, 4 min de conversación)

| `--model` | Descarga | Velocidad | Calidad observada |
|---|---|---|---|
| `small` | ~0,5 GB | ~10× tiempo real (25 s por 239 s) | Errores frecuentes: palabras deformadas ("anuncia" por "anunciación", "reistado"), frases cortadas. |
| `turbo` (por defecto) | ~1,6 GB | ~3,3× tiempo real (73 s por 239 s) | Mucho mejor: nombres, lugares y frases completas correctas. |
| `medium` / `large-v3` | 1,5 / 3 GB | más lentos que `turbo` | `large-v3` es el más preciso; en CPU puede tardar ~1× tiempo real. No probados aquí. |
| `tiny` / `base` | <0,2 GB | muy rápidos | Solo para pruebas. |

Estimación: 1 h de audio ≈ 20 min con `turbo` en CPU.

## GPU

Con `--device auto` se intenta CUDA (`float16`) y, si falla, CPU. faster-whisper necesita CUDA 12 + cuDNN 9 instalados; en el equipo de desarrollo (GTX 1650, 4 GB) no están, así que se usó CPU. En 4 GB de VRAM `turbo` cabe en `int8_float16`.

## Parámetros que importan

- **Filtro de voz (VAD):** activado por defecto (Silero VAD integrado en faster-whisper); recorta silencios y reduce alucinaciones. `--no-vad` lo desactiva.
- **`condition_on_previous_text=False`:** evita que un bucle de repetición se propague al siguiente fragmento.
- **Colapso de repeticiones:** una secuencia repetida >3 veces ("no, no, no, …") dentro de un segmento se recorta a 3.
- **Descarte de ecos entre segmentos:** Whisper a veces emite varios segmentos idénticos de 0,02–0,3 s (p. ej. "El día 14, sí." ×4). Se descartan los segmentos de ≥3 palabras a >10 palabras/s. Con 6 palabras/s se perdía habla real (282 palabras en 75 min); con 10 solo caen 18, todas ecos. Se aplica al generar el texto, sobre los `.json` de `partes/`.
- **Idioma:** se detecta en el primer audio y se reutiliza; fíjalo con `--language es` si el primer audio es corto o tiene ruido.
- **Privacidad:** el audio no sale del equipo; solo se contacta con Hugging Face para descargar el modelo.
