# AGENTS.md — `rag/`

> Estado: **fase 3 en curso**. Corpus externo reunido con `rag/corpus/SOURCES.md` (TRAVEL-003, hecho). Documentos
> de `empresa/` pendientes (TRAVEL-004). El paquete sigue vacío: la fase 3 es solo de datos.

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

## Corpus y licencias

- `corpus/SOURCES.md`: una fila por archivo (`Archivo` · `Título` · `URL` · `Descarga` · `Licencia` · `Carpeta` ·
  `En git` · `SHA-256`). Licencia poco clara → el documento no entra.
- `corpus/seguridad/aesa/` y `corpus/seguridad/exteriores/` son **de uso privado**: están en `.gitignore` y se
  vuelven a descargar desde la URL de su fila. Los archivos de más de 10 MB también van fuera de git (regla por
  archivo en `.gitignore`).
- Los originales no se tocan: la conversión (fase 4) escribe en `markdown/`.

Comprobar el corpus cuando cambie (desde `travel-agency/`; no hay tests, es un entregable de datos):

```bash
cd rag/corpus
# Huellas: todos OK
grep '^| [a-z]' SOURCES.md | awk -F' \\| ' '{gsub(/^\| /,"",$1); gsub(/ \|$/,"",$8); print $8"  "$1}' | sha256sum -c --quiet
# Cada archivo con su fila: sin salida
diff <(find . -type f ! -name .gitkeep ! -name SOURCES.md | sed 's|^\./||' | sort) \
     <(grep '^| [a-z]' SOURCES.md | awk -F' \\| ' '{gsub(/^\| /,"",$1); print $1}' | sort)
cd ../..
git check-ignore rag/corpus/seguridad/aesa rag/corpus/seguridad/exteriores   # las dos carpetas
git ls-files rag/corpus/seguridad/aesa rag/corpus/seguridad/exteriores       # sin salida
find rag/corpus -type f -size +10M | xargs -r git check-ignore -v            # cada uno, ignorado
```

## Decisiones y trampas

- Solo se importa la función pública de otros paquetes, nunca sus módulos internos.
- Qué hay en cada carpeta: `leyes/` (EUR-Lex y BOE, PDF), `salud/` (guía del Ministerio de Sanidad y Tu Europa),
  `seguridad/` (EASA, AESA y Exteriores, HTML tal cual se sirve), `general/tabiji/` (5 tablas Parquet en inglés,
  registros y no documentos: la fase 4 tiene que pasarlos a texto). Detalle y licencias en `SOURCES.md`.
- El Yellow Book de CDC no se puede descargar gratis (y CDC bloquea `curl`): se descartó, ver `PROYECTO.md` §4.
- Las páginas HTML cambian en origen: una nueva descarga da otra huella y hay que actualizar su fila.
