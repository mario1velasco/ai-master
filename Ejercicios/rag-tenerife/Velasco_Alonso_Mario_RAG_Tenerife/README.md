# Caso práctico RAG Tenerife

Lee el enunciado y la rúbrica. El notebook contiene cuatro funciones por completar; las utilidades de carga y registro ya están implementadas.

## Preparación antes de la actividad

Python 3.11 o 3.12, conexión y acceso al modelo preparado por el profesorado. Desde esta carpeta:

```bash
python -m venv .venv
```

Activa `.venv` (`source .venv/bin/activate` en macOS/Linux o `.venv\Scripts\Activate.ps1` en PowerShell), y ejecuta:

```bash
python -m pip install -r requirements.txt
python -m ipykernel install --user --name rag-tenerife --display-name "Python RAG Tenerife"
python -m jupyterlab
```

Selecciona el kernel **Python RAG Tenerife**. Copia `.env.example` a `.env` y configura tu clave local. No entregues `.env`. El chat y los embeddings son configurables: `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`. Los nombres incluidos son una configuración inicial que el profesorado debe comprobar con su cuenta. Si el modelo de chat elegido no admite `temperature`, ajusta su construcción.

Las llamadas de la sección 4 en adelante usan servicios externos y pueden consumir saldo. No se necesitan Pinecone, despliegue ni una interfaz web. Se admite otro proveedor preparado por el profesorado manteniendo los requisitos y documentando el cambio.

## Ejecución

1. Abre el notebook desde esta carpeta y comprueba que existe `data/TENERIFE.pdf`.
2. Completa las cuatro funciones y justifica los parámetros.
3. Ejecuta desde un kernel limpio; se crea un índice y se compara k = 2 con k = 4.
4. Revisa las 12 salidas en `resultados.json` y completa `revision.csv`. Un 0 indica fallo, un 1 cumplimiento; `NA` no aplica. Las celdas vacías son pendientes, no ceros.
5. Ejecuta el resumen y redacta la conclusión del notebook.

El guardado conserva `revision.csv` si ya existe para no borrar tu revisión. Al repetir llamadas, guarda una copia de los archivos anteriores y revisa que las filas se refieran a las respuestas nuevas. No presentes resultados de una prueba anterior como si fueran de la nueva configuración.

## Problemas habituales

- `FileNotFoundError`: abre Jupyter desde la carpeta del notebook y coloca la guía en `data/TENERIFE.pdf`.
- Clave ausente: configura `.env`; no pegues la clave en el notebook.
- Acceso denegado o modelo inexistente: confirma el identificador habilitado para la clase.
- Cuota o conexión: resuelve el error y repite; una llamada fallida no es una abstención correcta.
- Importación fallida: comprueba que has seleccionado el kernel del entorno instalado.

## Entrega

Un ZIP con el notebook ejecutado, resultados.json, revision.csv, README.md, requirements.txt, preguntas.csv y utilidades.py (más cualquier módulo que hayas añadido). No incluyas claves, `.env`, `.venv` ni cachés. El corrector aporta la misma guía en `data/TENERIFE.pdf`.

---

## Notas para el revisor

### Estructura de la entrega

| Archivo | Contenido |
|---|---|
| `rag_tenerife.ipynb` | Secciones 1–7: la práctica pedida (900/150, k = 2 y k = 4). Sección **EXTRA**: 4 mejoras (A–D). |
| `resultados.json`, `revision.csv` | Las 12 ejecuciones de la práctica y su revisión manual. |
| `utilidades.py`, `preguntas.csv`, `requirements.txt` | Infraestructura facilitada. |
| `experimentos/chunks.py` | Mejora A: barrido de tamaño/solapamiento (300–2500 × 0/150/300 × k = 2, 4, 6) con métricas automáticas. |
| `experimentos/revision_chunks.py` | Mejora A: exporta las 4 configuraciones finalistas para revisarlas a mano y resume la revisión. |
| `experimentos/rerank.py` | Mejora B: recupera 20 candidatos y los reordena con un cross-encoder. |
| `experimentos/resultados/` | `resultados_chunks.json` y `revision_chunks.csv`: revisión manual de las finalistas. |

Las mejoras C (recuperación híbrida) y D (prompt más estricto) están explicadas en el notebook, pero no implementadas.

### Configuración usada en cada parte

- **Práctica (secciones 1–7):** OpenAI, `gpt-5-nano` (temperatura 0) + `text-embedding-3-small`. Variables: `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`.
- **Mejoras A y B:** por coste (306 llamadas en el barrido), se ejecutaron con embeddings locales (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) y Claude Haiku (`claude-haiku-4-5-20251001`). Variables: `ANTHROPIC_API_KEY` y, de forma opcional, `ANTHROPIC_CHAT_MODEL` y `LOCAL_EMBEDDING_MODEL`. Sus cifras **no son comparables** con las de la sección 7, porque usan otro modelo y otros embeddings.
- En la celda del barrido, `LOCAL = False` usa la configuración de OpenAI de la práctica y `GENERAR = False` solo mide la recuperación, sin llamar al LLM.
- El primer uso descarga de Hugging Face el modelo de embeddings local y el cross-encoder `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`. Hace falta conexión.

### Cómo ejecutar

1. Secciones 1–7: igual que arriba (`.env` con `OPENAI_API_KEY`).
2. Sección EXTRA (opcional): añade `ANTHROPIC_API_KEY` al `.env`. **El barrido con `GENERAR = True` hace 306 llamadas al modelo.** Para revisarlo sin coste, usa `GENERAR = False`.
3. `revision_chunks.exportar_revision` no sobrescribe `experimentos/resultados/revision_chunks.csv` si ya existe, para conservar la revisión manual.

### Reglas respetadas

- Las páginas de referencia y las palabras clave (`EVIDENCIAS` en `chunks.py`) solo se usan para medir **después** de recuperar. Nunca llegan al buscador ni al modelo.
- No se incluyen claves, `.env`, `.venv` ni cachés.
