# AGENTS.md — 03-skills

Guía operativa para cualquier agente (Claude Code u otro) que trabaje en esta carpeta. Teoría y contexto en [`README.md`](README.md); explicación extensa en [`explicacion.md`](explicacion.md).

## Qué es esta carpeta

Tema 03 del módulo 06: **Skills** (paquetes de know-how con `SKILL.md`) y **Decision Models** (Jev de TypeSafe: decisiones tipadas en una pasada). Contiene un PDF de teoría y siete proyectos (dos de referencia y las skills propias `audio-split/`, `audio-decoder/`, `text-resume/`, `img-to-text/` y la orquestadora `media-resume/`). **No hay enunciado de práctica ni TODOs**: todo es material de referencia.

## Proyectos

| Carpeta | Qué es | Tratamiento |
|---|---|---|
| `presentacion-open/` | Skill de presentaciones con `python-pptx==1.0.2`. | Referencia. No modificar salvo petición explícita. |
| `audio-split/` | Skill propia: divide audios largos en trozos de ~4 min (ffmpeg, sin modelos). | Sí modificable; mantén `name` = nombre de carpeta. |
| `audio-decoder/` | Skill propia: ordena y transcribe en local los audios de un directorio a un único `.txt` (faster-whisper). | Sí modificable; mantén `name` = nombre de carpeta. |
| `text-resume/` | Skill propia: lee textos (`.txt`/`.md`) y crea `descripcion.md`, `resumen.md` y `resumen.pdf` sin inventar nada. | Sí modificable; mantén `name` = nombre de carpeta. |
| `img-to-text/` | Skill propia: transcribe a `.md` el texto de imágenes sin cambiar palabras; OCR local como verificación. | Sí modificable; mantén `name` = nombre de carpeta. |
| `media-resume/` | Skill orquestadora: audios/imágenes → `resumen.md` + `resumen.pdf`. Depende de las otras cuatro skills propias (rutas relativas `../audio-split`, etc.). | Sí modificable; mantén `name` = nombre de carpeta. No dupliques lógica de las otras skills: llámala. |
| `ebis-cli-decision-model/` | EBIS-CLI con Jev: `decision_model/` (Choice + Routing), runtime, MCP multi-servidor, subagentes, TUI Textual. | Referencia. Su `AGENTS.md` interno (4 líneas) se inyecta como prompt del propio agente: no es documentación del tema, no lo edites. |

El directorio `ebis-cli-decision-model/` está en modo solo lectura en el sistema de archivos (`dr-xr-xr-x`).

## Cómo ejecutar

```bash
cd ebis-cli-decision-model && uv sync && cp .env.example .env   # OPENAI_API_KEY, TYPESAFE_API_KEY
uv run python -m ebis_cli.app

cd audio-split && python3 scripts/split_audio.py audio.m4a --output-dir out && python3 scripts/check_split.py out   # requiere ffmpeg

cd audio-decoder && python3 scripts/order_files.py DIR && .venv/bin/python scripts/transcribe_audio.py DIR   # venv con requirements.txt; descarga ~1,6 GB la 1ª vez

cd text-resume && python3 scripts/collect_texts.py ENTRADA --output-dir OUT   # luego, con venv (requirements.txt): scripts/check_summary.py y scripts/md_to_pdf.py

cd img-to-text && .venv/bin/python scripts/prepare_images.py IMG --output-dir OUT   # venv con requirements.txt; luego join_parts.py y check_transcription.py

cd media-resume && python3 scripts/setup_env.py && python3 scripts/inventory.py ENTRADAS --output-dir OUT   # luego process_audio.py, build_source.py, finalize.py

cd presentacion-open && python3 -m pip install -r requirements.txt
python3 scripts/compile_deck.py examples/capabilities.json --output out/presentation.pptx
python3 scripts/check_overflow.py out/presentation.pptx --spec examples/capabilities.json
python3 scripts/check_package_integrity.py out/presentation.pptx
```
Sin `TYPESAFE_API_KEY`, EBIS-CLI cae a function calling automático y al modelo `default`. Dentro de la app: `/decision on|off|status`, `/stat`, `/stats`, `/tools`, `/agents`.

## Dónde mirar

- Jev: `ebis_cli/decision_model/typesafe.py` (llamada al SDK), `choices.py` (qué acción), `routing.py` (qué modelo, valida `routing-llm.json`).
- Bucle: `ebis_cli/agent/runtime.py`, método `run` y `_request`. Prompts por fase: `ebis_cli/prompts.py`. Costes: `ebis_cli/workspace/usage.py` y `ebis_cli/settings.py`.
- Audio: `audio-split/SKILL.md` (flujo de 6 pasos); lógica de cortes en `scripts/split_audio.py` (`detect_silences`, `plan_cuts`, `cut_chunk`); medición de duración en `scripts/_common.py` (`probe`, `decoded_duration`: en `.aac` crudo `ffprobe` estima mal y el seek de entrada es inexacto).
- Transcripción: `audio-decoder/SKILL.md` (flujo de 6 pasos); orden en `scripts/_ordering.py` (`order_files` devuelve `ambiguities` → hay que preguntar al usuario; exit 3), transcripción en `scripts/transcribe_audio.py`. Fallos conocidos de Whisper mitigados: bucles de repetición dentro de un segmento (`collapse_repeats`) y ecos entre segmentos con velocidad de habla imposible (`clean_segments`, umbral 10 palabras/s; no lo bajes a 6: descarta habla real).
- Resumen: `text-resume/SKILL.md` (flujo de 8 pasos; el agente lee y redacta, no hay modelo). Orden en `scripts/_ordering.py` (exit 3 = preguntar al usuario; copia propia de la de `audio-decoder`, más permisiva con `001_parte_001`). Fidelidad en `scripts/check_summary.py` (heurística: `INVENTADO?`/`OMITIDO?`; no ve nombres al inicio de frase), PDF en `scripts/md_to_pdf.py` (el PDF debe coincidir palabra por palabra con el `.md`; el pie `pág. N` se ignora al comparar). Bugs ya corregidos que no debes reintroducir: `TODO` solo en mayúsculas en el detector de relleno (si no, salta con la palabra «todo») y `CondPageBreak` antes de cada título para evitar títulos huérfanos al pie de página.
- Imágenes: `img-to-text/SKILL.md` (flujo de 7 pasos; `prepare_images.py` autodetecta la orientación (`auto_rotation`, 4 pasadas de OCR sobre una miniatura; solo gira si mejora >1,5×) y las fotos de documentos giradas 90°/180° eran el caso real que lo motivó; `zoom_image.py` nombra la salida con la caja para poder hacer varios zooms; el agente lee las imágenes con `Read` y escribe `partes/NN_*.md`). Troceado en `scripts/prepare_images.py` (`cut_points` corta en filas sin tinta; no usar la media de la fila: partía líneas), verificación en `scripts/check_transcription.py` (RapidOCR; heurística por palabras). `_ordering.py` es copia adaptada de la de `text-resume`.
- Orquestadora: `media-resume/SKILL.md` (flujo de 8 pasos). `scripts/_env.py` carga por ruta los módulos de las hermanas (`load_module`: todas tienen `_ordering.py`, no se pueden importar por nombre) y fija el `.venv`. Ordenes confirmados: `inventory.py` sale con 3 si hay que preguntar; `build_source.py` escribe `orden_final.txt` y hay que pasarlo a `collect_texts.py --files-from` (sin él, la heurística de `text-resume` marca como ambiguos nombres como `02_audio_reunion_1.txt`). `process_audio.py` repite la división con -30 dB si >1/3 de cortes son duros.
- Skill: `presentacion-open/SKILL.md` (flujo de 7 pasos) y `references/`; compilador `scripts/compile_deck.py` + `scripts/pptx_components.py`.

## Discrepancias conocidas (no las "corrijas" por tu cuenta)

1. `routing-llm.json` pone `reasoning_effort: none` a `gpt-6.1-sol` (niveles `medium_no_reasoning` y `expensive_no_reasoning`), pero `routing.py` (`MODEL_REASONING_EFFORTS`) no lo admite: `LLMRouter()` lanza `ValueError` y la app no arranca. El README del proyecto describe `gpt-6-sol` y `gpt-5.6-sol` para esos niveles.
2. `SKILL.md` declara `name: presentations-open`; la carpeta es `presentacion-open`.
3. Las slides usan `r.choices[...]`; el código usa `result.answers["decision"].choice`.
4. `/stat` no aparece en la tabla de comandos del README del proyecto.

Si el código se corrige, actualiza esta sección y el aviso correspondiente en `README.md`/`explicacion.md` en el mismo cambio.

## Mantenimiento de la documentación

Cada vez que modifiques algo en esta carpeta, comprueba si `README.md`, este `AGENTS.md` y/o `explicacion.md` quedan desactualizados y actualízalos en el mismo cambio.

- Si el cambio es puntual (un dato, un fichero nuevo, una discrepancia resuelta), edita solo esas líneas; no reescribas secciones enteras.
- Si es grande (nuevo proyecto, se reestructura la carpeta, aparece un ejercicio con TODOs), replantea la sección afectada antes de parchearla.
- Si no hay nada que actualizar, no toques los docs "porque sí".
