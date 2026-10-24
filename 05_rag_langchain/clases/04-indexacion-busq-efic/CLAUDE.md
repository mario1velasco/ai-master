# CLAUDE.md — Sesión 4: Indexación y búsqueda vectorial eficiente

Directorio de la **sesión 4** del tema 5 (*Sistemas de recuperación de la información, RAG y LangChain*) del
máster EBIS. Compara cuatro índices FAISS (`IndexFlatIP` exacto, `IndexHNSWFlat`, `IndexIVFFlat`,
`IndexIVFPQ`) sobre 50.000 noticias de AG News, usando LangChain como interfaz común. Idioma de todo el
material: **español**.

## Contenido

| Archivo | Qué es |
|---|---|
| `indexacion_busqueda_vectorial_eficiente.ipynb` | Notebook principal (31 celdas). **Fuente de verdad de las cifras.** |
| `EXPLICACION_sesion_04.md` | Guía de estudio de la sesión (notebook + diapositivas). Es lo que hay que leer primero. |
| `README.md` | Instrucciones de entorno e instalación (no es la guía de estudio). |
| `requirements.txt` | Dependencias fijadas (`faiss-cpu`, `model2vec`, `langchain-community`, `datasets`…). |
| `verificar_entorno.py` | Comprueba Python 3.11 y las librerías clave. |
| `INICIAR_LINUX.sh` | Instala `uv` + Python 3.11, crea un `.venv` **local** y abre JupyterLab (no usar: se reutiliza el `.venv` raíz). |
| `Lecturas adicionales/` | 10 papers: HNSW, Product Quantization, FAISS, DiskANN, ScaNN, ANN-Benchmarks, Inverted Multi-Index, GPU similarity search, etc. |
| `../pdfs/T5-S4 Sistemas de recuperación de la información, RAG y Langchain.pdf` | Diapositivas (30 págs.) de esta sesión. |

## Flujo del notebook

1. Comprobación de Python 3.11 → imports y constantes (`SEED=42`, `MAX_DOCUMENTS=50_000`, `TOP_K=10`,
   `BENCHMARK_REPETITIONS=7`, modelo `minishlab/potion-retrieval-32M`).
2. AG News → `Document` de LangChain (`page_content` + `metadata{corpus_id, category}`).
3. Embeddings Model2Vec (512 dims, normalizados L2), cacheados en `cache_vector_search/*.npy`.
4. Utilidades comunes: `as_langchain_vector_store`, `search_by_vector`, `benchmark_store`,
   `serialized_size_mib`, `ranking_table`.
5. Baseline exacto → `recall_at_k` → HNSW (`efSearch`) → IVF (`nprobe`) → IVF-PQ (`m=16`, `nbits=8`).
6. `as_retriever()`, tabla comparativa, gráfica recall-latencia, inspección cualitativa, decisiones de diseño.

Resultados de referencia (50.000 docs): exact 1,6 ms; HNSW `efSearch=50` → recall 1.0 en 0,063 ms;
IVF `nprobe=64` → recall 1.0 en 0,52 ms; IVF-PQ → 2,1 MiB pero recall 0.33.

## Entorno Python (`.venv` compartido)

- Se usa el **`.venv` común de la raíz** (Python **3.11**, `requirements.txt` raíz); ver [`../../CLAUDE.md`](../../CLAUDE.md), sección 4.
  **No crear un `.venv` local** ni usar `INICIAR_LINUX.sh`/`uv venv` del README (crean uno local).
- Desde esta carpeta, sin activar:
  ```bash
  ../../.venv/bin/python verificar_entorno.py
  ../../scripts/lab.sh .          # JupyterLab con el venv común (kernel «Python (rag-curso)»)
  ```
- **Sin conflicto de versión:** el venv es 3.11, que es lo que exigen `verificar_entorno.py` y la primera celda del notebook.
  Paquetes de esta sesión ya instalados: `faiss-cpu==1.12.0`, `model2vec==0.9.0`, `datasets==3.5.0`, `langchain-community`,
  `matplotlib`, `pandas`. Ojo: `pandas` está resuelto a **3.0.x** (el `requirements.txt` local pedía 2.2.3); el notebook no se ha
  vuelto a ejecutar con esa versión.
- No se necesita ninguna clave de API. El `.env` raíz no se lee ni se imprime.

## Cómo ejecutar

- Para pruebas rápidas bajar `MAX_DOCUMENTS` a `10_000`.
- **No ejecutar el notebook salvo que haga falta**: descarga datos y modelo (~3 GB) y tarda minutos.
- `cache_vector_search/` se genera aquí dentro; no debe añadirse a git.

## Convenciones al editar

- Las guías `EXPLICACION_sesion_XX.md` de `clases/01…03` son la plantilla de estilo: título "Guía de estudio —
  Sesión N", cita inicial con enlaces al notebook/PDF/sesiones previas, índice con anclas, lenguaje sencillo,
  analogías cotidianas, tablas y código real, resumen final, "¿qué sigue?" y preguntas de repaso.
- Toda cifra citada debe contrastarse con los outputs del notebook; los números dependen de hardware y semilla.
- Enlaces relativos (`../pdfs/…` con espacios como `%20`); no reutilizar los enlaces rotos de las guías 02/03.

## Gotchas conocidos

- `README.md` menciona `INICIAR_WINDOWS.cmd`, `INICIAR_MAC.command` y `.python-version`, pero **solo existe
  `INICIAR_LINUX.sh`**.
- Markdown del notebook inconsistente con el código: la celda de PQ dice 384 dims y `m=12`; el código usa
  **512 dims y `m=16`**. La celda de IVF dice que subir `nprobe` mejora "recall y latencia": mejora el recall
  pero **empeora la latencia**.
- FAISS no expone los nodos visitados por HNSW: `candidates_per_query` es `NaN` para HNSW.
- IVF-PQ da recall 0.333 constante en todos los `nprobe` probados (límite = error de cuantización).
- La salida guardada del notebook contiene rutas del equipo del autor original (`/Users/aruizart/…`); es normal.

## Contexto del curso

Secuencia en `clases/`: 01 vectores → 02 sparse vs dense → 03 hybrid/reranking/ColBERT → **04 indexación
(este directorio)** → 05 almacenamiento (AWS) → 06 construcción y evaluación → 07 RAG. Las diapositivas de
todas las sesiones están en `clases/pdfs/` (T5-S1 … T5-S7).
