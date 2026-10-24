# CLAUDE.md — `src/` (código Python de la sesión 7)

Carpeta con **dos paquetes Python** (layout `src/`, instalados en modo editable por `pip install -e .` desde
[`../pyproject.toml`](../pyproject.toml), paquete `umbra-rag-lab`, `where = ["src"]`). Contexto general y
precauciones de coste en [`../CLAUDE.md`](../CLAUDE.md).

| Paquete | Qué es | Documentación |
|---|---|---|
| [`umbra/`](./umbra/) | **Código nuevo** de la sesión 7: recuperación de solo lectura, generación con citas, comparación, extras y API FastAPI. | [`umbra/CLAUDE.md`](./umbra/CLAUDE.md) |
| [`retrieval_lab/`](./retrieval_lab/) | **Copia** del laboratorio de evaluación de la [sesión 6](../../06-Const-evaluacion/src/retrieval_lab/). | [`retrieval_lab/CLAUDE.md`](./retrieval_lab/CLAUDE.md) |

No hay `README.md` en esta carpeta (el notebook lo cita, pero no existe).

## Cómo se relacionan

```
umbra.api ─► umbra.generation (service, flows, context, client, prompts)
                  └► umbra.retrieval (baseline, hybrid) ──► retrieval_lab.retrieval.engine.reciprocal_rank_fusion
                                                        └─► retrieval_lab.representations.vectors.unit_vectors
umbra.experiments / umbra.evaluation / umbra.presentation ─► umbra.domain, umbra.generation
notebook Parte I (opcional, REPLAY_SESSION06) ────────────► retrieval_lab completo (evaluación de la sesión 6)
```

- **`umbra` depende de `retrieval_lab` solo en dos puntos**, ambos en `umbra/retrieval/hybrid.py`:
  `reciprocal_rank_fusion` y `unit_vectors`. El resto de `retrieval_lab` solo lo usa la Parte I del notebook.
- **`retrieval_lab` no importa `umbra`.** La dependencia es de un solo sentido: `umbra → retrieval_lab`.
- Los dos paquetes se instalan a la vez con `-e .`, y el notebook además añade `src/` a `sys.path`
  (`ROOT = primer directorio que contiene src/umbra`).

## Reglas para trabajar aquí

1. **No editar `retrieval_lab` para "arreglar" `umbra`.** Es una copia de la sesión 6 (solo difiere en un
   comentario eliminado en `configuration/settings.py`): un cambio aquí **divergería** de la sesión 6 y de su
   caché/huellas. Si `umbra` necesita otra utilidad, impórtala solo si ya existe; si no, impleméntala en `umbra`.
2. **Los flujos de RAG viven en `umbra/generation/`.** Notebook y aplicación usan el mismo `RAGService`; no crear
   una segunda implementación en otro sitio.
3. **La recuperación es de solo lectura sobre Pinecone**: nada aquí crea índices, sube documentos ni borra
   namespaces. Mantenerlo.
4. **Nada de claves en el código**; se leen del entorno (`OPENAI_API_KEY`, `PINECONE_API_KEY`) ya cargado por
   `load_settings`.
5. **No ejecutar código que llame a OpenAI/Pinecone** (embeddings, `RAGService.answer`, `compare_modes`,
   `build_local_graph`, `build_summary_tree`) sin petición expresa del usuario.
6. Ejecutar con el `.venv` de la raíz del proyecto (ver `../CLAUDE.md`). Los paquetes se importan como `umbra.*` y
   `retrieval_lab.*` (no rutas relativas).

## Gotchas

- `umbra` y `retrieval_lab` **no tienen tests aquí**: `tests/` no existe en esta copia aunque el README lo cita.
- Hay `__pycache__` de CPython 3.12 dentro de `umbra/` y `retrieval_lab/`; no editarlos ni añadirlos a git si no lo están ya.
- `python -m uvicorn umbra.api.server:app` exige que el paquete sea importable (`-e .` o `PYTHONPATH=src`).
