# Demo · Tema 2 · Sesión 4 · NLP

Notebook que da soporte a la sesión 4 del Tema 2 del Máster. Sirve dos demos durante la clase:

- **Mini-demo en el slide 9** — solo la sección 1 (tokenización con `tiktoken`). 3 minutos.
- **Demo de cierre en el slide 25** — secciones 2, 3 y 4 (embeddings, aritmética semántica, visualización). 10 minutos.

## Qué hay en el notebook

1. **Tokenización con `tiktoken`** — cómo GPT-4 trocea texto en subwords. Comparativa español-inglés, casos divertidos (emojis, palabras técnicas).
2. **Embeddings de frase con `sentence-transformers`** — modelo MiniLM-L6-v2 (~80 MB), matriz de similitud coseno, heatmap.
3. **Aritmética semántica con GloVe** — la analogía clásica rey−hombre+mujer ≈ reina, y otras (capitales, plurales, verbos).
4. **Visualización 2D con PCA** — proyectar embeddings de 100 dimensiones a 2D y ver los clusters semánticos en un plot.

## Requisitos

- Python 3.10+
- ~300 MB libres en disco (modelos cacheados después de la primera descarga).
- 4 GB de RAM libres.

Funciona en cualquier plataforma. Apple Silicon va acelerado con MPS.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab nlp-fundamentos.ipynb
```

## ⚠️ Importante: ejecutar antes de clase

**Ejecuta el notebook entero una vez antes de impartir la sesión.** La primera ejecución descarga ~200 MB de modelos (`all-MiniLM-L6-v2` ~80 MB + `glove-wiki-gigaword-100` ~128 MB). En segunda ejecución todo está en cache y arranca en segundos.

Si lo descargas en clase con WiFi mala, esperarás minutos en silencio incómodo.

## Tiempo de ejecución (segunda ejecución, modelos en cache)

- Sección 1 (tokenización) — 3 s
- Sección 2 (embeddings + heatmap) — 5 s
- Sección 3 (analogías GloVe) — 8 s (la carga es lo que tarda)
- Sección 4 (PCA + plot) — 2 s

**Total: ~20 segundos de ejecución pura. El resto es narración.**

## Solución de problemas

- **`ModuleNotFoundError: sentence_transformers`** — falta instalar dependencias: `pip install -r requirements.txt`.
- **GloVe no se descarga** — comprueba conexión, o ejecútalo en un terminal fuera del notebook: `python -c "import gensim.downloader as api; api.load('glove-wiki-gigaword-100')"`.
- **`Could not load model 'all-MiniLM-L6-v2'`** — proxy corporativo bloqueando Hugging Face Hub. Solución: configura `HF_ENDPOINT` o descarga el modelo manualmente.
- **El heatmap se ve negro** — actualiza `matplotlib >= 3.8` o cambia `cmap="viridis"` por `cmap="Blues"`.
- **La analogía `paris - france + italy` no da `rome`** — GloVe-wiki-gigaword-100 funciona bien para esta y la mayoría, pero algunas se desvían. Para resultados más sólidos, prueba `glove-wiki-gigaword-300` (cuádruple de tamaño, 400 MB).

## Ampliaciones opcionales (para alumnos avanzados)

Si quieres profundizar, en una segunda iteración se podría añadir:

- **Visualización de atención** con `bertviz` sobre un BERT pequeño. Muy visual.
- **Embeddings en español** con modelos como `paraphrase-multilingual-MiniLM-L12-v2` o `BAAI/bge-m3`.
- **Comparativa MiniLM vs un encoder más grande** (e.g. `all-mpnet-base-v2`) — para ver el tradeoff calidad/tamaño.
