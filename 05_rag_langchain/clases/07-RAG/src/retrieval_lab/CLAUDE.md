# CLAUDE.md — `retrieval_lab` en la sesión 7 (copia del laboratorio de la sesión 6)

Este paquete es una **copia** del laboratorio de evaluación de recuperación de la sesión 6. **La arquitectura,
los módulos, las dependencias entre subpaquetes, los flujos de datos, las invariantes del protocolo y cómo
extenderlo están documentados en detalle en**
[`../../../06-Const-evaluacion/src/retrieval_lab/CLAUDE.md`](../../../06-Const-evaluacion/src/retrieval_lab/CLAUDE.md)
**(léelo primero)**. Aquí solo se recogen las particularidades de esta copia. Contexto de la sesión 7 y
precauciones de coste en [`../../CLAUDE.md`](../../CLAUDE.md); visión de `src/` en [`../CLAUDE.md`](../CLAUDE.md).

## Relación con la sesión 6

- **Código idéntico** al de `../../../06-Const-evaluacion/src/retrieval_lab/`. Única diferencia verificada:
  falta el comentario `# Para correr en local sin APIs` sobre `include_qwen` en `configuration/settings.py`.
- **Mismas 8 subpaquetes**: `configuration`, `data`, `representations`, `storage`, `retrieval`, `evaluation`,
  `reporting`, `infrastructure` (~1.370 líneas), mismo `PROTOCOL_VERSION = "pinecone-v1"` y mismas huellas de
  caché/namespaces. Por eso puede reutilizar los artefactos y los índices de Pinecone creados en la sesión 6.
- **No hay `README.md` propio ni `tests/`**; el notebook cita `src/README.md`, que no existe en esta carpeta
  (léelo en `../../../06-Const-evaluacion/src/README.md`).

## Cómo lo usa la sesión 7

| Uso | Dónde | Qué |
|---|---|---|
| **Utilidades reutilizadas por `umbra`** | `umbra/retrieval/hybrid.py` | `retrieval_lab.retrieval.engine.reciprocal_rank_fusion` (fusión RRF de las dos ramas) y `retrieval_lab.representations.vectors.unit_vectors` (renormalizar el embedding). **Son las únicas dependencias de `umbra`.** |
| **Referencia (Parte I del notebook)** | `Notebooks/01_retrieval_y_rag.ipynb`, celdas protegidas por `REPLAY_SESSION06` | Repetir el benchmark de la sesión 6: `ExperimentConfig`, `load_trec_covid`, `EmbeddingCache`, `PineconeWorkspace`, `RetrievalLab`, `run_experiments`, etc. **Desactivado por defecto**; al activarlo escribe en `artifacts/retrieval_replay`, no sobre la sesión 6. |

`retrieval_lab` **no importa `umbra`**: la dependencia es unidireccional (`umbra → retrieval_lab`).

## Reglas al trabajar aquí

1. **No modificar esta copia.** Cualquier cambio la haría divergir de la sesión 6 (fórmulas de métricas, huellas
   de caché, namespaces). Si hace falta un cambio real en el laboratorio, hazlo en la sesión 6 y vuelve a copiarlo.
   Si `umbra` necesita algo distinto, impleméntalo en `umbra`, no aquí.
2. **No ejecutar código de este paquete que llame a Pinecone/OpenAI** (`prepare_lexical`, `prepare_dense`,
   `run_experiments`, `EmbeddingCache.encode`…) sin petición expresa: crea índices, descarga/calcula ~171.000
   embeddings y consume servicios. La sesión 7 solo necesita, en ejecución normal, `reciprocal_rank_fusion` y
   `unit_vectors` (funciones puras, sin red).
3. **El laboratorio nunca borra recursos remotos** y crea índices con protección de borrado; mantenerlo.
4. Ejecutar con el `.venv` de la raíz del proyecto (ver `../../CLAUDE.md`). Importa `langchain_core` al cargar
   `retrieval.engine`, y `numpy`; el resto de dependencias pesadas (`torch`, `sentence-transformers`,
   `google-genai`, `pinecone`, `beir`…) solo se importan al usar las clases concretas.

## Gotchas

- `retrieval.engine` importa `langchain_core.runnables.RunnableLambda`: aunque `umbra` solo use la función RRF,
  **`langchain-core` debe estar instalado** (está en `pyproject.toml`).
- Hay `__pycache__` de CPython 3.12 dentro de los subpaquetes; no editarlos.
- Si cambian ambas copias por separado, la documentación de esta carpeta deja de ser cierta: comprobar con
  `diff -rq src/retrieval_lab ../06-Const-evaluacion/src/retrieval_lab -x __pycache__ -x CLAUDE.md` (desde `07-RAG`).
