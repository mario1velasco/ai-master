# CLAUDE.md — Sesión 7: RAG y la aplicación UMBRA (proyecto final)

Directorio de la **sesión 7** (última) del tema 5 (*Sistemas de recuperación de la información, RAG y LangChain*)
del máster EBIS. Continúa la sesión 6: reutiliza el recuperador **híbrido** ya elegido (OpenAI
`text-embedding-3-large` a **256 dims**, **100 candidatos por rama**, RRF) sobre TREC-COVID en Pinecone y le
añade un LLM (`gpt-4.1-mini`) para **responder con citas**. Incluye dos flujos (RAG estándar y búsqueda como
herramienta), dos extras (prototipos de GraphRAG y RAPTOR) y **UMBRA**, una aplicación web local
(FastAPI + React). Idioma de todo el material: **español**.

Documentación por subcarpeta (léela al entrar en ella):
[`app/CLAUDE.md`](./app/CLAUDE.md) · [`src/CLAUDE.md`](./src/CLAUDE.md) ·
[`src/umbra/CLAUDE.md`](./src/umbra/CLAUDE.md) · [`src/retrieval_lab/CLAUDE.md`](./src/retrieval_lab/CLAUDE.md).

## Entorno Python (`.venv` compartido)

- Se usa el **`.venv` común de la raíz** (Python **3.11**, `requirements.txt` raíz); ver [`../../CLAUDE.md`](../../CLAUDE.md), sección 4.
  **No crear un `.venv` local** ni seguir el `python -m venv .venv` del `README.md`.
- **No se instaló `-e .` de esta carpeta** (evita duplicar el paquete `retrieval_lab` de la sesión 6). El notebook añade `src/` al
  `sys.path` y la API se lanza indicando el directorio de la aplicación. Desde esta carpeta, sin activar:
  ```bash
  ../../scripts/lab.sh .                                                     # JupyterLab (venv común, claves exportadas)
  ../../.venv/bin/python -m uvicorn --app-dir src umbra.api.server:app --host 127.0.0.1 --port 8007
  ```
- **Instalado:** `openai`, `pinecone`, `fastapi`, `uvicorn`, `tiktoken`, `scikit-learn`, `PyYAML`, `langchain-core`, `httpx`,
  `pandas`, `matplotlib`. La salida guardada del notebook se generó con Python 3.14; el venv común es 3.11 (README: 3.11/3.12).
- El frontend usa **Node.js 20.19+ o 22.12+** (`npm`), independiente del venv de Python.
- `SESSION06_DIR` se toma del entorno: `.env.example` raíz propone `SESSION06_DIR=../06-Const-evaluacion`. El `.env` raíz **no se
  lee, imprime ni copia**; `umbra` además hereda el `.env` de la sesión 6 (si existe).

## Contenido

| Ruta | Qué es |
|---|---|
| `Notebooks/01_retrieval_y_rag.ipynb` | Notebook principal (69 celdas: 32 Markdown + 37 código). Parte I: sesión 6 como referencia (protegida por `REPLAY_SESSION06`); Parte II: RAG estándar y con herramienta; Parte III: extras; Parte IV: UMBRA. **Fuente de verdad de las cifras.** |
| `EXPLICACION_sesion_07.md` | Guía de estudio (notebook + diapositivas + código). Leer primero. |
| `README.md` | Entorno, arranque de la app, límites de seguridad y organización. |
| `config/rag.yaml` | Parámetros de RAG (modelo generativo, contexto, límites, caché). |
| `.env.example` | Solo comentarios y `RAG_LLM_MODEL`; las claves se heredan de la sesión 6. |
| `pyproject.toml` / `requirements.txt` | Paquete `umbra-rag-lab` y dependencias (rangos, no versiones exactas). |
| `src/umbra/` | Paquete nuevo de esta sesión: recuperación de solo lectura, generación, API, experimentos. |
| `src/retrieval_lab/` | **Copia** del paquete de la sesión 6 (solo se reutilizan 2 funciones). |
| `app/` | Frontend React 19 + Vite 6 (fuentes) y `app/dist/` (build **versionado** que sirve FastAPI). |
| `artifacts/rag/answers/` | Caché de respuestas (`<sha256>.json`). Hoy hay 2 (modo standard y tools, misma pregunta). |
| `../pdfs/T5-S7 Retrieval-Augmented Generation.pptx.pdf` | Diapositivas (18 págs.) de esta sesión. |

## Flujo de la sesión

```
pregunta ─► [standard] embedding literal ─► HybridRetriever (Pinecone: denso + BM25 → RRF) ─► pack_context ─► LLM ─► respuesta [D#]
        └─► [tools]    LLM propone search_library(query) ─► Python valida y busca (≤2 veces) ─► pack_context ─► LLM ─► respuesta [D#]
```

Notebook y app usan **el mismo `RAGService`**. Parámetros: 100 candidatos/rama, 6 documentos y 6.500 tokens de
fuentes por búsqueda, ≤1.200 tokens por documento, ≤1.200 de salida, hasta 2 búsquedas (3 llamadas LLM), historial
de 8 mensajes, preguntas de ≤2.000 caracteres.

Resultado de referencia guardado (2 preguntas, sin caché): standard ≈ 4,7 s, 1 llamada LLM, 2.128 tokens de
entrada; tools ≈ 6,3 s, 2 llamadas, 2.897 tokens (misma pregunta). La reserva de la sesión 6 dio nDCG@10 ≈ 0,791
(candidato) frente a ≈ 0,773 (referencia), con el cero dentro del intervalo.

## Conexión con la sesión 6 (crítico)

`umbra` **lee, sin modificar**, de la carpeta de la sesión 6: su `.env`, `data/trec-covid/corpus.jsonl`,
`artifacts/pinecone_v1/results/frozen_decision.json` y `artifacts/pinecone_v1/indexes/bm25-*/{ready,vocabulary}.json`.
Los índices de Pinecone deben existir en el proyecto de la clave. **El adaptador es de solo lectura**: no crea
índices, no sube documentos, no ajusta BM25.

- La carpeta se localiza buscando, junto a esta, un directorio llamado **"Sesión 06" / "Sesión 6"**. **Aquí se
  llama `06-Const-evaluacion`, así que no se encuentra sola: hay que definir `SESSION06_DIR`**
  (p. ej. `SESSION06_DIR=../06-Const-evaluacion`) en el entorno o en un `.env` de esta carpeta.
- **`../06-Const-evaluacion/` no contiene `data/` ni `artifacts/`** (se generan al ejecutar la sesión 6). Sin ellos,
  `Baseline`, `Corpus` y la parte "en vivo" fallan con errores explícitos; solo funciona el recorrido local del
  notebook.

## Precauciones (coste y efectos remotos)

- **El notebook guardado trae `RUN_LIVE = True` (celda 1) y `RUN_EXTRAS = True` (celda 58)**, al contrario que lo
  que dice el README. "Ejecutar todo" haría llamadas reales de pago (OpenAI embeddings, Pinecone, LLM). **No
  ejecutar el notebook, la API ni la comparación de modos sin petición expresa del usuario.**
- Las llamadas a `/api/chat`, `compare_modes`, `build_local_graph` y `build_summary_tree` consumen tokens.
- Nunca imprimir credenciales. `artifacts/rag/answers/` contiene **preguntas, respuestas y pasajes**: revisar
  privacidad antes de compartir o commitear más ficheros ahí.
- El servidor es una app docente **local** (`127.0.0.1`): no exponerlo a Internet.

## Convenciones al editar

- Las guías `EXPLICACION_sesion_XX.md` de `clases/01…07` son la plantilla de estilo: título "Guía de estudio —
  Sesión N", cita inicial con enlaces al notebook/PDF/sesiones previas, índice con anclas, lenguaje sencillo,
  analogías cotidianas, tablas y código real, resumen final, "¿qué sigue?" y preguntas de repaso.
- Toda cifra citada debe contrastarse con los outputs del notebook o el código.
- Las citas de la respuesta deben ser etiquetas **sueltas** `[D1] [D2]`: el patrón `\[(D\d+)\]` (servicio y
  frontend) no reconoce `[D1, D2]`.
- Si se cambia el frontend hay que **recompilar `app/dist`** (`npm run build`); el servidor sirve lo compilado.

## Gotchas conocidos

- **`tests/` y `design/` no existen** en esta copia, aunque el README y el notebook los mencionan
  (`tests/test_modular_retrieval.py`, "concepto visual y especificación"). Tampoco hay `src/README.md`, citado en la
  celda 4 del notebook.
- **README vs notebook:** el README dice que `RUN_LIVE=False` permite recorrer el cuaderno y que no se ejecutaron
  llamadas de pago, pero el notebook guarda salidas de ejecuciones reales (respuestas, tokens, latencias) con
  `RUN_LIVE = True`.
- La salida guardada contiene rutas del equipo del autor original (`/Users/aruizart/…`); es normal.
- `Settings` exige **`candidate_depth == 100`** y `Baseline` exige decisión **híbrida, profundidad 100, proveedor
  OpenAI**: otra decisión congelada en la sesión 6 hace fallar la sesión 7.
- La interfaz importa **Google Fonts** desde `styles.css` (petición de red externa desde el navegador).
- `retrieval_lab` está duplicado respecto a la sesión 6: no editar uno esperando que cambie el otro.

## Contexto del curso

Secuencia en `clases/`: 01 vectores → 02 sparse vs dense → 03 hybrid/reranking/ColBERT → 04 indexación
(HNSW/IVF/PQ) → 05 almacenamiento (Pinecone, filtros, CRUD) → 06 construcción y evaluación → **07 RAG (este
directorio, proyecto final)**. Las diapositivas de todas las sesiones están en `clases/pdfs/` (T5-S1 … T5-S7).
