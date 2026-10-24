# Tema 03 – Skills y Decision Models

Tercer tema del módulo **06 · Integración con herramientas y MCP** del [Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica) de EBIS Business Techschool.

Los temas 01 y 02 dieron al agente un LLM, un harness y tools (locales y por MCP). Este tema añade dos piezas más: las **Skills** (el *know-how* para hacer bien una tarea compleja usando esas tools) y los **Decision Models** (modelos que, en vez de generar texto, devuelven una decisión tipada en una sola pasada; el material usa **Jev** de TypeSafe).

## Contenido de la carpeta

```text
03-skills/
├── Tema 6_Decision_Models_Skills.pdf   # Teoría: slides del tema (76 páginas)
├── presentacion-open/                  # Una skill completa (presentaciones PPTX con python-pptx)
├── audio-split/                        # Skill propia: divide audios largos en trozos de ~4 min con ffmpeg
├── audio-decoder/                      # Skill propia: transcribe audios de un directorio, en orden, a un único .txt (faster-whisper, local)
├── text-resume/                        # Skill propia: lee textos largos y crea descripción + resumen extenso (.md) + PDF
├── img-to-text/                        # Skill propia: transcribe a .md el texto de imágenes, palabra por palabra, con OCR local como segundo lector
├── media-resume/                       # Skill propia (orquestadora): audios e imágenes → transcripción → resumen .md + PDF, usando las cuatro anteriores
└── ebis-cli-decision-model/            # EBIS-CLI con Jev (Choice + Routing) integrado
```

En esta carpeta **no hay enunciado de práctica ni TODOs por resolver**: los dos proyectos son material de referencia para estudiar y ejecutar; `audio-split/`, `audio-decoder/`, `text-resume/`, `img-to-text/` y `media-resume/` son skills añadidas después, creadas a partir del patrón de `presentacion-open/`.

## 1. Teoría — `Tema 6_Decision_Models_Skills.pdf`

### ¿Cómo llevar a cabo una tarea? (págs. 3-8)
Con LLM + harness + tools/MCP ya se puede construir cualquier sistema automatizado. Pero ante "créame una presentación ejecutiva de 10 slides sobre cuentas.csv", el agente tiene las herramientas (añadir slide, insertar imagen, crear gráfica, guardar PPTX) y le falta **saber cómo hacer el trabajo**: cuántas slides, qué narrativa, qué layout, cómo detectar overflow, cómo validar el PPTX.

### Agent Skills (págs. 9-14)
Una skill es un paquete modular con procedimientos, reglas y recursos que guía al agente en tareas complejas de extremo a extremo.

| Dimensión | Tool | Skill |
|---|---|---|
| Rol | Músculo: primitiva de ejecución | Cerebro operativo: know-how |
| Alcance | Acción puntual atómica | Workflow complejo de inicio a fin |
| Control | Depende de la improvisación del LLM | Acota ambigüedades y aporta reglas |
| Garantía | Ejecución sintáctica | Resultado determinista y consistente |

Aporta: control de flujo, robustez y determinismo (scripts y validaciones); y frente a "un prompt largo + scripts": modularidad/reutilización (versionable en Git, reutilizable entre agentes), **cero saturación de contexto** (se carga bajo demanda) y consistencia/repetibilidad.

### Cómo crear una skill (págs. 15-23)
Estructura estándar: un directorio con `SKILL.md` (obligatorio: frontmatter YAML + cuerpo Markdown) y módulos opcionales `references/`, `scripts/`, `assets/`. El frontmatter lleva `name` (a-z, 0-9 y guiones, 1-64, igual que la carpeta) y `description` (1-1024, dice cuándo activarla). Opcionales: `license`, `compatibility`, `metadata`, `allowed-tools` (experimental). El material señala que un bloque `parameters:` en el YAML puede definir entradas en JSON Schema, pero en las skills de OpenAI/Codex esas instrucciones van en el cuerpo.

### Ejemplo: la skill `presentations` de OpenAI (págs. 24-34)
Se pide a ChatGPT Work que devuelva su skill privada (59 archivos), se instala en Codex (`.codex/skills`) y falla porque depende de librerías privadas (`@oai/artifact-tool`, variables `CODEX_PRIMARY_RUNTIME_*`). **Solución:** pedir a Codex una skill nueva con las mismas guías pero usando `python-pptx` → la carpeta `presentacion-open/` de este tema. Mensaje final: en sistemas agénticos el activo técnico es el diseño del sistema (restricciones, flujo e instrucciones).

### ¿Alternativa a las tools? (págs. 35-41)
Cada tool consume contexto (nombre + descripción + esquema) en cada petición. Hay dos salidas: `defer_loading` + Tool Search (el esquema se carga bajo demanda) y las skills, que ocupan contexto **por capas** (metadatos → `SKILL.md` → recursos). Una skill también permite usar una CLI ya instalada (ffmpeg) con shell genérica + protocolo + scripts, sin crear N tools. Tabla resumen: flujo repetible → Skill; acción estructurada → Tool/MCP; carga inicial del catálogo → `defer_loading`; CLI instalada → Shell + Skill.

### Generación y decisiones cerradas (págs. 42-59)
Un LLM genera token a token (autorregresivo); incluso un JSON se genera así. Un **Decision Model** conserva el transformer pero cambia la salida: proyecta el vector contextual `h` directamente sobre opciones declaradas (sin vocabulario abierto ni bucle). Primitivas: **choice** (`softmax(Wh+b)` sobre K opciones), **score** (`sigmoid`, valor en [0,1]) y **noul/null** (pregunta sí/no con probabilidad, o abstención). Eficiencia: ≈450 ms vs ≈15 ms en el ejemplo del material. En el caso de uso de Codex (114 eventos), 68 son decisión (59,6 %) y 84 decisión o control (73,7 %) → arquitectura híbrida: el Decision Model enruta, el LLM solo escribe lenguaje abierto.

### Jev y modelos System One (págs. 60-70)
Jev (TypeSafe): decisiones tipadas con SDK Python (`typesafe-sdk`, Python ≥ 3.10, clave en `TYPESAFE_API_KEY`). Precio publicado: 0,042 USD/M tokens de entrada, salida gratis; respuesta 70-500 ms. El código de la app aplica su propio umbral de confianza (ejemplo 0.75). Alternativas citadas: `pplx-decider-v1-27b` (Perplexity), Tiny-Jev-1.7B y Kev-4B (abiertos), Jev Decision Index y la Decisions API de OpenAI (en preview).

### Ejemplos: LLMs vs Decision Models (págs. 71-75)
Snake como clasificación; **EBIS CLI + routing**; y dos ejercicios comparando Jev activado/desactivado: extracción sencilla (coste conjunto 0,00022687 vs 0,00284850 USD, 92 % menos) y tarea larga de auditoría de workspace (0,02646989 vs 0,04235182 USD, 38 % menos).

## 2. Proyectos de código

| Carpeta | Qué es | Estado |
|---|---|---|
| `presentacion-open/` | Skill de presentaciones: `SKILL.md`, 10 `references/`, 7 `scripts/` (compilador `compile_deck.py` + validadores), `assets/`, `examples/`, `agents/openai.yaml`. Depende solo de `python-pptx==1.0.2`. | Referencia (funcional) |
| `audio-split/` | Skill que divide un audio largo en trozos de ~4 min cortando en silencios (`ffmpeg silencedetect`, sin modelos): `SKILL.md`, 3 `scripts/` (`probe_audio.py`, `split_audio.py`, `check_split.py`, más `_common.py`), 3 `references/`, `examples/`, `agents/openai.yaml`. Solo biblioteca estándar + `ffmpeg`. | Skill propia (funcional) |
| `audio-decoder/` | Skill que ordena los audios de un directorio (orden natural; si es ambiguo, pregunta) y los transcribe en local con faster-whisper (modelo `turbo` por defecto) a un único `.txt`: `SKILL.md`, 3 `scripts/` (`order_files.py`, `transcribe_audio.py`, `check_transcript.py`, más `_ordering.py`), 2 `references/`, `examples/`, `agents/openai.yaml`. Depende de `faster-whisper==1.2.1`; el primer uso descarga el modelo de Hugging Face (~1,6 GB). | Skill propia (funcional) |
| `text-resume/` | Skill que lee a fondo un texto o una carpeta de textos ordenados (`.txt`/`.md`) y crea `descripcion.md` (de qué trata), `resumen.md` (extenso, sin inventar) y `resumen.pdf` idéntico al `.md`. Aquí el trabajo de leer y redactar lo hace el agente; los 3 `scripts/` preparan la lectura (`collect_texts.py`), verifican fidelidad y PDF (`check_summary.py`) y generan el PDF (`md_to_pdf.py`). Además: `references/` (3), `assets/` (plantillas), `examples/`, `agents/openai.yaml`. Depende de `markdown-it-py`, `reportlab` y `pypdf`. | Skill propia (funcional) |
| `img-to-text/` | Skill que transcribe a un `.md` el texto de una o varias imágenes, palabra por palabra y sin inventar nada, con formato Markdown parecido al de la imagen. El agente lee las imágenes (visión); un OCR local (RapidOCR) hace de segundo lector. 5 `scripts/` (`prepare_images.py` trocea y ordena, `join_parts.py`, `check_transcription.py`, `zoom_image.py`, más módulos `_`), `references/transcription_rules.md`, `examples/`, `agents/openai.yaml`. Depende de `Pillow`, `markdown-it-py` y `rapidocr`; el OCR descarga sus modelos la primera vez. | Skill propia (funcional) |
| `media-resume/` | Skill orquestadora: recibe audios y/o imágenes y hace todo el camino hasta `resumen.md` + `resumen.pdf` + `descripcion.md`. No copia código: llama a los scripts de `audio-split`, `audio-decoder`, `img-to-text` y `text-resume`. 6 `scripts/` (`setup_env.py`, `inventory.py`, `process_audio.py`, `build_source.py`, `finalize.py` y `_env.py`), `references/` (2), `examples/`, `agents/openai.yaml`. Un único `.venv` con las dependencias de las cuatro; pregunta el orden cuando es dudoso o hay audios e imágenes mezclados. | Skill propia (funcional) |
| `ebis-cli-decision-model/` | EBIS-CLI evolucionado: varios servidores MCP, subagentes como procesos, conversaciones persistentes, TUI Textual y **Jev** en `ebis_cli/decision_model/` (Choice de acción + Routing de modelo). | Referencia (ver avisos) |

### Cómo ejecutar
```bash
# EBIS-CLI + Jev
cd ebis-cli-decision-model
uv sync
cp .env.example .env     # OPENAI_API_KEY y TYPESAFE_API_KEY
uv run python -m ebis_cli.app

# Skill de audio (requiere ffmpeg instalado)
cd audio-split
python3 scripts/split_audio.py /ruta/audio.m4a --output-dir out
python3 scripts/check_split.py out

# Skill de transcripción (en un venv; descarga el modelo la primera vez)
cd audio-decoder
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
python3 scripts/order_files.py ../../audio/6_chunks
.venv/bin/python scripts/transcribe_audio.py ../../audio/6_chunks
.venv/bin/python scripts/check_transcript.py ../../audio/6_chunks/transcripcion

# Skill de resumen (venv para el PDF y las comprobaciones; el resumen lo redacta el agente)
cd text-resume
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
python3 scripts/collect_texts.py ../../audio/6_chunks/transcripcion --output-dir ../../audio/6_chunks/transcripcion/resumen
.venv/bin/python scripts/check_summary.py RESUMEN.md --source ENTRADA --pdf RESUMEN.pdf

# Skill de imágenes a texto (venv; el agente transcribe y el OCR verifica)
cd img-to-text
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/prepare_images.py IMAGEN.png --output-dir TRABAJO
.venv/bin/python scripts/join_parts.py TRABAJO && .venv/bin/python scripts/check_transcription.py TRABAJO/transcripcion.md --work-dir TRABAJO

# Skill orquestadora de audios e imágenes → resumen (crea su propio .venv)
cd media-resume
python3 scripts/setup_env.py
python3 scripts/inventory.py AUDIO.aac IMAGENES/ --output-dir SALIDA   # exit 3 = hay que preguntar el orden
python3 scripts/process_audio.py SALIDA/trabajo                         # lento: segundo plano
python3 scripts/build_source.py SALIDA/trabajo && python3 scripts/finalize.py SALIDA/trabajo   # tras leer imágenes y redactar el resumen

# Skill de presentaciones (en el entorno de trabajo)
cd presentacion-open
python3 -m pip install -r requirements.txt
python3 scripts/compile_deck.py examples/capabilities.json --output out/presentation.pptx
python3 scripts/check_overflow.py out/presentation.pptx --spec examples/capabilities.json
```
Comandos de EBIS-CLI relevantes: `/decision [on|off|toggle|status]`, `/stat` (conversación) y `/stats` (workspace), `/tools`, `/agents`.

### Avisos detectados al revisar el código (no corregidos)
- **`routing-llm.json` no supera la validación de `routing.py`.** Define `medium_no_reasoning` y `expensive_no_reasoning` como `gpt-6.1-sol` con `reasoning_effort: none`, pero `MODEL_REASONING_EFFORTS` declara que `gpt-6.1-sol` no admite `none`; `LLMRouter()` lanza `ValueError` al construirse (comprobado con un stub de `typesafe_sdk`), de modo que `Agent()` no arrancaría. El `README.md` del proyecto dice que esos niveles usan `gpt-6-sol` y `gpt-5.6-sol`, que es lo que el JSON debería contener.
- **Nombre de la skill:** el `SKILL.md` declara `name: presentations-open`, pero la carpeta se llama `presentacion-open`; el material (pág. 17) dice que la carpeta debe coincidir con `name`.
- **API de Jev:** las slides leen resultados con `r.choices["x"]` (págs. 64-66); el código usa `result.answers["decision"].choice` (`typesafe.py`). Puede ser otra versión del SDK; no se ha comprobado.
- `/stat` existe en `app/main.py` pero no figura en la tabla de comandos del README del proyecto.

## 3. Orden de estudio recomendado
1. PDF págs. 3-14 (por qué skills) y 15-23 (estructura de `SKILL.md`).
2. Leer `presentacion-open/SKILL.md` y recorrer `references/` y `scripts/`; pág. 24-34 del PDF como historia de cómo se construyó.
3. PDF págs. 35-41 (contexto, `defer_loading`, skills vs tools).
4. PDF págs. 42-59 (token a token vs decisión tipada) y 60-70 (Jev).
5. `ebis-cli-decision-model/DECISION_MODEL.md`, luego `decision_model/{typesafe,choices,routing}.py` y `agent/runtime.py` (método `run`).
6. PDF págs. 71-75 y probar `/decision off` / `/decision on` con `/stats`.

Documentos del tema: [AGENTS.md](AGENTS.md) (guía operativa) y [explicacion.md](explicacion.md) (explicación extensa).
