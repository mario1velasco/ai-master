# Errores conocidos

Fallos que ya han ocurrido al usar esta skill, su causa y cómo se evitan. Añade una entrada cada vez que algo falle.

## La transcripción falla con «unexpected keyword argument 'metadata_errors'» (2026-10-09)
- **Síntoma:** `transcribe_audio.py` termina con `TypeError: open() got an unexpected keyword argument 'metadata_errors'` dentro de `faster_whisper/audio.py` (y `media-resume`/`any-to-any` dicen «falló la transcripción»).
- **Causa:** `requirements.txt` solo fijaba `faster-whisper==1.2.1`; su dependencia `av` quedaba libre y se instaló `av 19.0.1`, que quitó el parámetro `metadata_errors` de `av.open()` que usa faster-whisper 1.2.1. Además, `setup_env.py` solo comprobaba que los imports funcionaran, así que no lo detectaba.
- **Solución:** `av==18.1.0` fijado en `requirements.txt` (de la skill y de la raíz); `scripts/setup_env.py` (raíz) compara ahora las versiones instaladas con las fijadas y reinstala si difieren; `scripts/transcribe_audio.py` (`load_model`) se para con un mensaje claro si encuentra `av` ≥ 19.
- **Prevención:** ejecuta `python3 scripts/setup_env.py` desde la raíz tras actualizar el repo. Si actualizas `faster-whisper`, comprueba si la versión nueva admite `av` ≥ 19 antes de quitar el límite.
