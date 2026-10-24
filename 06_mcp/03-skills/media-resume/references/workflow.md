# Flujo y parámetros

## Estructura del trabajo
```
SALIDA/
├── resumen.md · resumen.pdf · descripcion.md      ← entregables
├── transcripciones/                               ← la fuente en orden (audio .txt, imágenes .md)
└── trabajo/
    ├── inventario.json                            ← unidades (a01…, img, t01…) y orden de fuentes
    ├── audio/a01_<nombre>/{trozos,transcripcion}/ ← audio-split + audio-decoder
    ├── imagenes/{tiles,partes,transcripcion.md}   ← img-to-text
    ├── fuente/NN_*.txt|md  · orden_final.txt      ← entrada de text-resume
    └── resumen/                                   ← text-resume: notas, descripcion.md, resumen.md, resumen.pdf
```

## Qué decide cada script
| Script | Decide / hace |
|---|---|
| `inventory.py` | Clasifica por extensión; ordena cada tipo (orden natural); pide confirmación si es dudoso o hay tipos mezclados; estima tiempos. Exit 3 = preguntar. |
| `process_audio.py` | Audios > 8 min → trozos de 4 min en silencios; > 1/3 cortes duros → repite con -30 dB / 0,3 s; transcribe (turbo por defecto) y verifica. Reanudable (`--force` rehace). |
| `build_source.py` | Copia cada unidad a `fuente/NN_*` en el orden final; falla si algo falta o el orden omite una unidad. |
| `finalize.py` | Verifica el resumen contra la fuente y el PDF contra el `.md`; copia los entregables a `SALIDA/`. |

## Parámetros útiles
- `process_audio.py --model small|turbo|large-v3 --language es --device cpu --unit a01 --force`.
- Audio muy normalizado o con ruido: `audio-split/references/workflow.md` explica `--silence-db`.
- Otro idioma: `--language xx` (si no, se detecta en el primer audio).
- Solo audios o solo imágenes: el flujo es el mismo; se omite el paso que no aplica.
- Textos ya escritos (`.txt`/`.md`) mezclados con lo demás: entran como unidades `t01…` sin procesar.

## Si algo falla
- `collect_texts.py` dice «ambiguo» sobre `fuente/`: usa `--files-from trabajo/orden_final.txt` (el orden ya está confirmado; la heurística se confunde con números del nombre original).
- `inventory.py` sale con 3: pregunta, no uses `--accept-order` sin que el usuario lo confirme.
- Faltan modelos o red: la primera transcripción/OCR descarga; sin red, usa un modelo ya en `~/.cache/huggingface` o `--model` con una ruta local.
- `finalize.py` dice que el `.md` es más reciente que el PDF: regenera con `../text-resume/scripts/md_to_pdf.py`.
