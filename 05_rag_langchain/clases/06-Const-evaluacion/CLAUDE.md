# CLAUDE.md — Sesión 6: Construcción y evaluación de un sistema de recuperación

Directorio de la **sesión 6** del tema 5 (*Sistemas de recuperación de la información, RAG y LangChain*) del
máster EBIS. Construye y **evalúa offline** un sistema de recuperación sobre **TREC-COVID** (171.332 documentos,
50 consultas, 66.336 juicios) con **BM25 + embeddings de OpenAI (256/512/768 dims) + búsqueda densa/híbrida
(RRF) en Pinecone**. Compara 19 configuraciones (37 con Qwen), elige en desarrollo, **congela** la decisión y la
comprueba en una reserva final con bootstrap pareado. Idioma de todo el material: **español**.

Para la arquitectura del código, lee [`src/retrieval_lab/CLAUDE.md`](./src/retrieval_lab/CLAUDE.md).

## Entorno Python (`.venv` compartido)

- Se usa el **`.venv` común de la raíz** (Python **3.11**, `requirements.txt` raíz); ver [`../../CLAUDE.md`](../../CLAUDE.md), sección 4.
  **No crear un `.venv` local** ni seguir el `python -m venv .venv` / `ipykernel install` del `README.md`.
- Desde esta carpeta, sin activar:
  ```bash
  ../../scripts/lab.sh .          # JupyterLab con el venv común y las claves del .env raíz exportadas
  ```
- **Instalado:** LangChain, OpenAI, Pinecone, scikit-learn, scipy, pandas, matplotlib, tqdm, tenacity. **No instalado** (opcionales,
  pesados; `requirements-optional.txt` raíz): `torch`, `transformers`, `sentence-transformers`, `langchain-huggingface`,
  `google-genai` (solo Qwen/Gemini) y **`beir`** (solo para descargar TREC-COVID; arrastra torch). Sin `beir`, `load_trec_covid`
  falla si falta `data/trec-covid/`: hay que colocar `corpus.jsonl`, `queries.jsonl` y `qrels/test.tsv` a mano o instalar `beir`.
- El notebook hace `os.chdir(<carpeta 06>)` y carga `.env` **desde esa carpeta** con `override=False`: basta con lanzar Jupyter
  con `scripts/lab.sh` (exporta el `.env` raíz al proceso). El `.env` raíz **no se lee, imprime ni copia**.
- La salida guardada del notebook se generó con Python 3.14.5; el venv común es 3.11 (dentro de lo que pide el README).

## Contenido

| Ruta | Qué es |
|---|---|
| `01_retrieval_system_evaluation.ipynb` | Notebook principal (34 celdas: 15 Markdown + 19 código). **Fuente de verdad de las cifras.** Salidas guardadas solo hasta el barrido de desarrollo (celda 22). |
| `EXPLICACION_sesion_06.md` | Guía de estudio (notebook + diapositivas). Leer primero. |
| `README.md` | Instrucciones de entorno, credenciales, caché, entrega a alumnos y pruebas. |
| `src/README.md` | Arquitectura resumida del paquete. |
| `src/retrieval_lab/` | Paquete Python del laboratorio (8 subpaquetes, ~1.370 líneas). Tiene su propio `CLAUDE.md`. |
| `.env.example` | Nombres de variables: `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_PREFIX`, `PINECONE_CLOUD`, `PINECONE_REGION`, `OPENAI_EMBEDDING_RPM/TPM`. |
| `requirements.txt` | Dependencias con rangos (no versiones exactas). |
| `Lecturas adicionales/` | 5 papers: Survey of VDBMS (Pan, Wang & Li), Taipalus (VDBMS), Milvus (Wang et al.), FreshDiskANN, Filtered-DiskANN. |
| `../pdfs/T5-S6 Sistemas de almacenamiento y recuperacion.pdf` | Diapositivas (19 págs.) de esta sesión (el nombre no refleja su contenido: es "construcción y evaluación"). |

Se generan al ejecutar (no existen ahora y **no deben commitearse**): `data/trec-covid/` (corpus, consultas,
qrels), `artifacts/pinecone_v1/{embeddings,indexes,results}/`.

## Flujo del notebook

1. **Config:** `ExperimentConfig(include_qwen=False, candidate_depths=(20,50,100), comparison_depth=50,
   reference_dimension=768, latency_budget_ms=1500, quality_tolerance=0.01)`.
2. **Datos:** `load_trec_covid`, `make_query_split` (30 desarrollo / 20 reserva), recorte a 6.000 bytes UTF-8.
3. **Plan y credenciales:** `model_plan` (tamaños), `check_credentials`, `EmbeddingCache`, `PineconeWorkspace`,
   `RetrievalLab`.
4. **Preparación remota:** `lab.prepare_lexical()` (BM25 → índice sparse) y `lab.prepare_dense()` (embeddings →
   3 índices densos).
5. **Experimentos:** `run_experiments` de la referencia BM25, luego de las 18 configuraciones; comparaciones
   controladas (`controlled_comparisons`, `depth_and_hybrid`).
6. **Decisión:** `select_candidate` → `freeze_decision` (`frozen_decision.json`) → `error_analysis`.
7. **Reserva final:** `run_experiments(..., split="holdout", fresh_embedding=True)` → `final_report`
   (bootstrap pareado, `final_report.json`).

Resultados de referencia (desarrollo, 30 consultas): BM25 nDCG@10 0,60 (p95 228 ms); mejor
`openai-large-d768-hibrida-k100` 0,80 (p95 ≈ 318 ms, 2 RU/consulta); densa 0,73–0,76.

## Precauciones (coste y efectos remotos)

- **Ejecutar el notebook crea recursos reales y consume servicios:** 4 índices en Pinecone (`{prefijo}-d256`,
  `-d512`, `-d768`, `-sparse`) con ≈ 171 k vectores cada uno, generación de ≈ 171 k embeddings de OpenAI
  (si no hay caché) y > 1.000 consultas remotas en el barrido. Puede superar cuotas gratuitas.
- **No ejecutar el notebook, `prepare_*` ni `run_experiments` sin petición expresa del usuario.** Las celdas de
  Markdown y el análisis de código no requieren ejecutar nada.
- Los índices se crean con `deletion_protection="enabled"` y **el código nunca borra recursos**: mantener esa
  propiedad. Usar un `PINECONE_INDEX_PREFIX` propio (1–26 caracteres `a-z0-9-`).
- Nunca imprimir credenciales; `check_credentials` solo informa de nombres.
- No ejecutar a la vez versiones distintas del código sobre los mismos `artifacts/`.
- Si existe `artifacts/pinecone_v1/results/frozen_decision.json`, **no reutilizar la reserva final para retocar
  el ganador** (el código lo impide a propósito).

## Convenciones al editar

- Las guías `EXPLICACION_sesion_XX.md` de `clases/01…06` son la plantilla de estilo: título "Guía de estudio —
  Sesión N", cita inicial con enlaces al notebook/PDF/sesiones previas, índice con anclas, lenguaje sencillo,
  analogías cotidianas, tablas y código real, resumen final, "¿qué sigue?" y preguntas de repaso.
- Toda cifra citada debe contrastarse con los outputs del notebook o el código de `src/`.
- Enlaces relativos con espacios codificados (`%20`); verificar que existen.

## Gotchas conocidos

- **Markdown obsoleto en el notebook (celda 1):** habla de cinco ficheros `retrieval_core.py`,
  `embedding_providers.py`, `retrieval_backends.py`, `retrieval_reporting.py`, `retrieval_runtime.py` y de "no hay
  carpeta `src/`". La arquitectura vigente es `src/retrieval_lab/` (así lo admite `src/README.md`).
- **`README.md` inexacto:** cita `Notebooks/01_retrieval_system_evaluation.ipynb`, pero el notebook está en la
  raíz de esta carpeta y no existe `Notebooks/`; cita también `tests/` y "scripts antiguos" que no existen aquí.
- **Sin salida guardada** de las celdas 23–32 (comparaciones controladas, decisión, errores, reserva final,
  informe). El resultado se conoce por la sesión 7 (`../07-RAG/Notebooks/01_retrieval_y_rag.ipynb`, celda 39):
  decisión congelada = OpenAI, 256 dims, híbrida, 100 candidatos/rama; reserva nDCG@10 ≈ 0,791 (candidato) frente
  a ≈ 0,773 (referencia), intervalo con el cero dentro. No inventar más detalle (tablas, IC exacto) sin ejecutar.
- La salida guardada contiene rutas del equipo del autor original (`/Users/aruizart/…`); es normal.
- Hay `__pycache__` de CPython 3.12 dentro de `src/`; no editarlos ni añadirlos a git si no están ya.
- `check_credentials` solo pide `GEMINI_API_KEY` si hay un modelo Gemini activo, pero **no existe ningún
  `ModelSpec` de Gemini por defecto** (el adaptador está en el código sin activar).

## Contexto del curso

Secuencia en `clases/`: 01 vectores → 02 sparse vs dense → 03 hybrid/reranking/ColBERT → 04 indexación
(HNSW/IVF/PQ) → 05 almacenamiento y recuperación (Pinecone, filtros, CRUD) → **06 construcción y evaluación
(este directorio)** → 07 RAG. Las diapositivas de todas las sesiones están en `clases/pdfs/` (T5-S1 … T5-S7).
