# CLAUDE.md — Arquitectura de `retrieval_lab`

Paquete Python del laboratorio de la **sesión 6** ([`../../CLAUDE.md`](../../CLAUDE.md) para el contexto del
curso y las precauciones de coste). Es un **laboratorio de evaluación offline de recuperación**: prepara
representaciones (BM25, embeddings), las carga en Pinecone, ejecuta experimentos pareados sobre TREC-COVID, mide
con métricas de ranking y elige/congela una configuración. Resumen previo en [`../README.md`](../README.md); este
documento detalla las responsabilidades, dependencias e invariantes.

> Se importa desde el notebook tras añadir `src/` al `sys.path` (`from retrieval_lab.… import …`). Ejecutar con el
> `.venv` de la raíz del proyecto. **No ejecutar código que llame a Pinecone/OpenAI sin petición expresa.**

## Modelo mental

Un **experimento** es un `Arm(model, dimension, strategy, depth)` con `strategy ∈ {"lexica","densa","hibrida"}`
(nombre determinista: `openai-large-d768-hibrida-k100`). El ciclo completo:

```
config ──► datos ──► preparación ──► experimentos ──► decisión ──► reserva final
(ExperimentConfig)  (corpus, qrels,  (BM25/embeddings   (run_experiments   (candidate_shortlist  (run_experiments
                     split, texts)    → Pinecone)         sobre desarrollo)  → freeze_decision)    holdout, fresh_
                                                                                                  embedding + bootstrap)
```

`RetrievalLab.pipeline(arm)` devuelve un `RunnableLambda` de LangChain que recibe un `query_id` y devuelve
`{"ranking", "latency_ms", "embedding_ms", "read_units", "candidate_union", "branches"}`.

## Mapa de subpaquetes

Todos incluyen `__init__.py` (solo el docstring; la raíz `__init__.py` también). Agrupación **por dominio**, no
por tipo de archivo.

| Subpaquete | Módulo | Responsabilidad y elementos clave |
|---|---|---|
| `configuration/` | `settings.py` | `ModelSpec` (clave, proveedor, nombre, dimensión nativa, dimensiones), `DEFAULT_MODELS` (OpenAI `text-embedding-3-large`: 256/512/768), `QWEN` (`Qwen/Qwen3-Embedding-0.6B`), **`ExperimentConfig`** (dataclass congelado con validaciones en `__post_init__`), `PROTOCOL_VERSION = "pinecone-v1"`, propiedades `active_models` y `results_dir`. |
| | `environment.py` | `configure(config)`: carga `.env` (`override=False`), crea `artifacts/{embeddings,indexes,results}`, fija semilla, escribe `environment.json` (versiones). `check_credentials`: **solo nombres**, nunca valores. |
| `data/` | `corpus.py` | `load_trec_covid` (descarga BEIR si faltan ficheros; valida que los qrels apunten a documentos existentes; devuelve huellas de fichero), `document_text` (título + texto), `prepare_text` (recorte por **bytes** UTF-8). No conoce proveedores ni clientes. |
| `representations/` | `providers.py` | `build_embedder(spec)`: OpenAI (`OpenAIEmbeddings`), Gemini (`GeminiEmbeddings`, prefijos propios) o HuggingFace/Qwen (detecta CUDA/MPS/CPU, prompt de consulta). |
| | `cache.py` | `EmbeddingCache`: matriz `float32` en `.npy` (memmap) + `manifest.json` + `progress.json` **reanudable por rangos**, lotes limitados por tokens/cuota, hilos acotados. Identidad por `fingerprint`. `output_spec` (dimensión de salida solicitada), `matrix`, `encode`, `query` (embedding en vivo). |
| | `vectors.py` | `unit_vectors(values, dimension)`: prefijo **Matryoshka** + renormalización L2; rechaza vectores nulos o no finitos. |
| | `bm25.py` | `SparseBM25`: pesos BM25 (`k1`, `b`) como matriz *sparse* guardada en `artifacts/.../indexes/bm25-*/`; `document(row)` (≤ 2048 términos) y `query(text)` (pesos 1,0). Tokenizer `word-2-plus-lowercase-english-stop-v1`. |
| `storage/` | `pinecone.py` | `PineconeWorkspace`: un índice por dimensión `{prefijo}-d{dim}` (coseno) + `{prefijo}-sparse` (dotproduct), *serverless*, **`deletion_protection="enabled"`**, valida dimensión/métrica/región y **nunca borra**. `upload` (namespace `{modelo}-{firma[:16]}`, idempotente, verificación de 3 muestras, marcador `upload-*.json`), `_upsert_bounded` (parte lotes > 1,8 MB), `search` (ranking + *read units*), `inventory`. |
| `retrieval/` | `lab.py` | `RetrievalLab`: estado compartido (config, corpus, textos, caché, remoto, `sparse`, `query_vectors`, `specs`) y **fachada docente**; delega en `preparation` y `engine` (funciones de módulo que reciben `self`). |
| | `preparation.py` | `prepare_lexical` (BM25 → índice sparse) y `prepare_dense` (prevalidación mínima, creación de índices, matrices en caché, carga por dimensión con `bounded_results`). |
| | `engine.py` | `retrieve(arm, qid, fresh_embedding)`: rama densa (embedding precalculado o en vivo → Pinecone) y/o léxica (BM25 sparse); **`reciprocal_rank_fusion`** (`1/(constante+posición)`, constante 60, desempate por ID); mide latencia total y `embedding_ms`. |
| `evaluation/` | `design.py` | `Arm`, `experiment_arms` (1 BM25 + modelos × dimensiones × {densa, híbrida} × profundidades), `make_query_split` (estratificado por nº de relevantes, guarda `split-*.json`), `model_plan` (N×d×4 bytes). |
| | `metrics.py` | Funciones **puras**: `precision_at_k`, `recall_at_k`, `normalized_recall_at_k` (`min(k, relevantes)`), `reciprocal_rank`, `average_precision`, `dcg`/`ndcg_at_k`, `evaluate_ranking` (valida duplicados y profundidad; añade `Fracción juzgada@10`). |
| | `statistics.py` | `paired_bootstrap` (mismos IDs, remuestreo pareado, IC95). |
| | `runner.py` | `run_experiments`: firma del protocolo, calentamiento excluido, orden aleatorio de consultas y brazos, repeticiones de latencia; escribe `protocol.json`, `rankings.json`, `latency.csv`, `*-metrics.csv`, `summary.csv` en `results/<split>/<firma[:16]>/`; `summarize_runs`, `table`. |
| | `selection.py` | `candidate_shortlist` (p95 ≤ presupuesto → tolerancia de nDCG@10 → menos bytes → menor latencia; error si nadie cumple), `freeze_decision` (→ `frozen_decision.json`, **bloquea sustituciones**), `conclude_evaluation` (bootstrap + veredicto → `final_report.json`). |
| `reporting/` | `views.py` | Presentación en el notebook: `corpus_overview`, `relevance_profile`, `show_results`, `controlled_comparisons`, `depth_and_hybrid`, `inspect_query`, `error_analysis`, `select_candidate`, `final_report`. **Único módulo que usa matplotlib/IPython.** |
| `infrastructure/` | `artifacts.py` | `fingerprint` (SHA-256 de JSON canónico), `write_json` (atómico, sin NaN), `file_digest`. |
| | `concurrency.py` | `bounded_results` (`ThreadPoolExecutor` acotado, cancelación cooperativa con `check_cancelled`). |
| | `rate_limits.py` | `RequestLimiter` (RPM/TPM de `{PROVEEDOR}_EMBEDDING_RPM/TPM`, `defer`, `learn`) y `transient_retry` (hasta 20 intentos en 429, backoff con jitter, respeta `Retry-After`, no reintenta cuotas terminales). |

## Dependencias entre subpaquetes

Regla: las flechas solo apuntan **hacia abajo**; nada de abajo importa lo de arriba.

```
reporting  ──►  evaluation  ──►  retrieval  ──►  representations ──►┐
     │              │               │                storage ─────►├─►  infrastructure
     │              │               └─► (usa lab.remote / lab.cache)│        ▲
     └──────────────┴──────────────────────────────────────────────┴─►  configuration
data  (solo infrastructure: fingerprint/write_json/file_digest)
```

- `metrics`, `statistics`, `runner` y `selection` **no dependen de Jupyter ni de matplotlib**.
- `evaluation/runner.py` no conoce Pinecone: recibe un `lab` con `pipeline()`, `queries` y `signature`.
- `retrieval/engine.py` y `preparation.py` acceden al mundo exterior solo a través de `lab.cache`
  (`EmbeddingCache`) y `lab.remote` (`PineconeWorkspace`).

## Flujos de datos

**Preparación (una vez; reanudable):**

```
corpus + queries ─► prepare_text (≤6000 B) ─► texts
texts ─► SparseBM25 ─► pesos sparse ────────────────────────────► {prefijo}-sparse / ns bm25-<huella>
texts ─► EmbeddingCache.matrix (proveedor, lotes, .npy) ─► unit_vectors(prefijo d) ─► {prefijo}-d{d} / ns <modelo>-<huella>
```

**Evaluación (por brazo y consulta):**

```
query_id ─► [densa]  vector (precalculado | cache.query en vivo) ─► Pinecone dense ─┐
         └► [léxica] SparseBM25.query ────────────────────────► Pinecone sparse ───┴─► [RRF si híbrida] ─► ranking
ranking + qrels ─► evaluate_ranking ─► métricas por consulta ─► resumen (media, p50/p95, RU) ─► selección ─► congelado
```

## Invariantes (no romper)

1. **Huellas (`fingerprint`)** definen caché de embeddings, namespaces, índices BM25 y carpetas de resultados.
   Un cambio de textos, IDs, modelo, formato o protocolo debe cambiar la huella; nunca reutilizar en silencio.
2. **Las fórmulas de `metrics.py` son parte del protocolo:** cambiarlas exige subir `PROTOCOL_VERSION`. AP divide
   por *todos* los relevantes; el recall normalizado, por `min(k, relevantes)`; nDCG usa ganancia lineal y trata
   grados negativos como 0.
3. **Los qrels nunca llegan a Pinecone ni a los embeddings.** Los metadatos guardan solo ID, título, extracto,
   modelo y firma.
4. **La reserva final no sirve para elegir.** `freeze_decision` bloquea una decisión distinta; la evaluación
   final usa `fresh_embedding=True` y cuenta la calidad de la **primera** repetición.
5. **No se borra nada remoto** y los índices llevan protección de borrado. Un índice existente incompatible
   (dimensión, métrica, región) **falla**, no se recrea.
6. **Sin caché de resultados de búsqueda:** cada medición consulta Pinecone de nuevo (para medir latencia real).
7. **Un fallo no es una métrica a cero:** timeouts/autenticación levantan excepción; nunca se rellenan filas.
8. **Las latencias no se mezclan:** barrido = embedding precalculado; reserva = incluye embedding en vivo.
9. La carga es **idempotente** (mismos IDs → upsert) y verifica muestras remotas contra las locales.

## Cómo extender

| Quiero… | Toca… |
|---|---|
| Otro modelo de embeddings | `settings.py` (`ModelSpec`), rama en `providers.build_embedder`, y `check_credentials` si necesita otra clave. Cada modelo debe incluir `reference_dimension` en sus `dimensions` (lo valida `ExperimentConfig`). |
| Otra dimensión / profundidad | `ModelSpec.dimensions` / `ExperimentConfig.candidate_depths` (deben incluir `comparison_depth`; 10 ≤ k ≤ 1000). |
| Otra estrategia (p. ej. fusión ponderada, reranker) | Nueva rama en `engine.retrieve`, valor en `experiment_arms`, y **medirla como experimento aparte** con su propia hipótesis. |
| Otra métrica | Función pura en `metrics.py`, clave en `METRICS`/`evaluate_ranking`; revisar `PROTOCOL_VERSION`. |
| Otro dataset BEIR | `data/corpus.py` (URL y rutas) y revisar el recorte de texto y el `split`. |
| Otro backend vectorial | Implementar la interfaz de `PineconeWorkspace` (`index`, `upload`, `search`, `inventory`) y pasarlo a `RetrievalLab`. |

## Convenciones y gotchas del código

- `from __future__ import annotations` en todos los módulos; mensajes y errores en **español**.
- `RetrievalLab` mantiene la interfaz docente y delega en **funciones de módulo que reciben `self`**
  (`preparation.prepare_*`, `engine.retrieve/pipeline`): no son métodos de otra clase.
- `reporting.views.select_candidate` **llama** a la lógica de selección (`candidate_shortlist`): la vista muestra,
  pero la regla vive en `evaluation/selection.py`.
- Gemini está implementado (`GeminiEmbeddings`) pero **no hay `ModelSpec` por defecto**; Qwen solo con
  `include_qwen=True` (descarga pesos, un hilo de codificación, lotes pequeños).
- `EmbeddingCache.client` reutiliza un cliente por clave de modelo; `output_spec` fija la dimensión pedida a la
  API de OpenAI/Gemini al máximo configurado (768) para guardar una sola matriz y derivar las demás por prefijo.
- No existe carpeta `tests/` en esta copia (el `README.md` la menciona). Las pruebas sin credenciales requerirían
  servicios simulados para `EmbeddingCache` y `PineconeWorkspace`.
- No editar los `__pycache__/` (compilados con CPython 3.12).
