# AGENTS.md — `rag/`

> Estado: **fase 0 (esqueleto)**. Solo existe el paquete vacío y un test de importación.

## Propósito

Corpus documental (`corpus/`), conversión a Markdown con PaddleOCR (`conversion/` → `markdown/`) y búsqueda híbrida BM25 + FAISS + RRF + reranker (sección 4).

Depende de: `contracts`, `telemetry`. Detalle de diseño en [`../PROYECTO.md`](../PROYECTO.md).

## Archivos clave

- `src/rag/__init__.py`: punto de entrada del paquete (`import rag`).
- `tests/`: tests con pytest.
- `corpus/leyes/`
- `corpus/seguridad/`
- `corpus/salud/`
- `corpus/empresa/`
- `corpus/general/`
- `conversion/`
- `markdown/`

## Función pública

Todavía ninguna. Cuando exista, se documenta aquí con sus tipos de `contracts/`.

## Ejecutar y testear

Desde la raíz `travel-agency/`:

```bash
uv sync
uv run pytest rag/tests
```

Variables en `.env` (copiar de `.env.example`): `RAG_EMBEDDING_MODEL`, `RAG_RERANKER_MODEL`.

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
