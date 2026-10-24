# Demo · Tema 1 · Sesión 1

Notebook de cierre de la primera sesión del Máster. Demuestra los tres pilares de la IA Generativa en menos de 50 líneas de Python.

## Qué hay en este notebook

1. **Texto con cloud** — Una llamada a OpenAI y otra a Anthropic para ver lo simple que es invocar un LLM. Cambiamos `system` prompt para visualizar prompt engineering básico.
2. **Multimodalidad** — Generamos imagen (DALL·E 3), voz (TTS) y transcribimos (Whisper). Cerramos el círculo.
3. **Inferencia local en Apple Silicon** — Descargamos Phi-3-mini-4bit con MLX y lo corremos en local sin internet. Demuestra que la IA Generativa ya no está atada a la nube.

## Requisitos

- Python 3.10 o superior.
- macOS con chip Apple Silicon (M1/M2/M3/M4) para el bloque 3. En Windows/Linux, omitir ese bloque.
- API key de OpenAI (obligatoria). Anthropic es opcional.

## Setup rápido

```bash
# Entorno virtual recomendado
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Lanzar Jupyter
jupyter lab text-gen-examples.ipynb
```

> Si no estás en Apple Silicon, comenta la línea `mlx-lm` del `requirements.txt` antes de instalar.

## API keys

El notebook **nunca** hardcodea claves. La primera celda ejecutable las pide vía `getpass`, que oculta la entrada en consola.

Cómo obtenerlas:

- **OpenAI** — https://platform.openai.com → API Keys → "Create new". Da 5 USD de crédito de prueba.
- **Anthropic** (opcional) — https://console.anthropic.com → API Keys.

Si prefieres usar un `.env`:

```bash
# .env (NO subir a git)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Y antes de ejecutar:

```python
from dotenv import load_dotenv; load_dotenv()
```

## Coste estimado de la demo completa

- 2 llamadas a `gpt-4o-mini` : ~0.001 USD
- 1 llamada a `claude-sonnet-4-6` : ~0.005 USD (opcional)
- 1 imagen `dall-e-3` 1024x1024 : ~0.04 USD
- 1 TTS `gpt-4o-mini-tts` : ~0.001 USD
- 1 Whisper transcripción : ~0.001 USD
- Phi-3-mini local : 0 USD

**Total: ~0.05 USD por ejecución completa.**

## Tiempo de ejecución en vivo

- Bloque 1 (texto cloud): 10-15 s
- Bloque 2 (imagen + audio + transcripción): 30-60 s (DALL·E 3 es lento)
- Bloque 3 (local en M4): primer load ~30 s, inferencia 2-3 s

**Total: 2-3 minutos de ejecución pura + 15 min de narración = ~20 minutos de demo.**

## Solución de problemas

- **`openai.AuthenticationError`** → la API key es inválida o ha caducado.
- **`mlx_lm` no instalado** → solo funciona en macOS arm64; en otras plataformas, comenta esa parte del requirements.txt.
- **`anthropic.NotFoundError` con `claude-sonnet-4-6`** → tu organización aún no tiene acceso a ese modelo. Cambia a `claude-sonnet-4-5` o `claude-3-5-sonnet-latest` en la celda correspondiente.
- **DALL·E 3 falla con error de moderación** → cambia el prompt a algo más neutro.
- **Phi-3-mini lento al primer uso** → la primera descarga son ~2.2 GB. A partir de ahí está en cache (`~/.cache/huggingface/`).
