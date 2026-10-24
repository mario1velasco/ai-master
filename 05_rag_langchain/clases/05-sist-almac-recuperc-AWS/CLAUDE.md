# CLAUDE.md — Sesión 5: Sistemas de almacenamiento y recuperación

Directorio de la **sesión 5** del tema 5 (*Sistemas de recuperación de la información, RAG y LangChain*) del
máster EBIS. Pasa del índice ANN (sesión 4) a una **base de datos vectorial**: registros
`{id, embedding, content, metadata}`, filtros, CRUD, persistencia, namespaces, versionado/migración y criterios
de arquitectura. Idioma de todo el material: **español**.

> El nombre "…AWS" es engañoso: el notebook usa **Pinecone serverless** (por defecto `cloud=aws`,
> `region=us-east-1`) + **OpenAI embeddings**; no usa servicios AWS directamente.

## Entorno Python (`.venv` compartido)

- Se usa el **`.venv` común de la raíz** (Python **3.11**, `requirements.txt` raíz); ver [`../../CLAUDE.md`](../../CLAUDE.md), sección 4.
  **No crear un `.venv` local** ni seguir el `uv venv --python 3.12` del `README.md`.
- Ya están instalados los pines de esta sesión (`langchain-core==1.6.3`, `langchain-openai==1.6.2`, `langchain-pinecone==0.2.13`,
  `pinecone==7.3.0`, `python-dotenv==1.2.3`, `jupyterlab==4.6.3`); `pandas` resuelto a 3.0.x. El README pide 3.12 (el límite real es
  `langchain-pinecone` `<3.14`), pero **3.11 lo cumple**.
- Se usa sin activar, con el `.env` raíz exportado al proceso (el notebook carga `Path.cwd()/.env` con `override=False`, así que
  respeta lo ya exportado):
  ```bash
  ../../scripts/lab.sh .          # JupyterLab con el venv común y las claves del .env raíz
  ```
- El `.env` raíz **no se lee, imprime ni copia**. Necesita `OPENAI_API_KEY` y `PINECONE_API_KEY` (opcionales `PINECONE_INDEX_NAME`,
  `PINECONE_CLOUD`, `PINECONE_REGION`). Ejecutar el notebook **consume servicios y crea un índice**: solo si el usuario lo pide.

## Contenido

| Archivo | Qué es |
|---|---|
| `S5_sistemas_almacenamiento_recuperacion.ipynb` | Notebook principal (26 celdas: 10 Markdown + 16 código). **Fuente de verdad de las cifras.** Trae outputs guardados de una ejecución real. |
| `EXPLICACION_sesion_05.md` | Guía de estudio de la sesión (notebook + diapositivas). Leer primero. |
| `README.md` | Configuración del entorno (`uv`, Python 3.12, `.env`). |
| `VALIDACION.md` | Validación del 16-09-2026: versiones fijadas, imágenes Docker, límites de verificación. |
| `requirements.txt` | Dependencias fijadas (jupyterlab, pandas, python-dotenv, langchain-core/openai/pinecone, pinecone 7.3.0). |
| `extras Docker con distintas BBDD Vectoriales/` | Tutoriales opcionales: `qdrant_local/`, `milvus_local/`, `weaviate_local/` (cada uno con `README.md`, `docker-compose.yml`, `example_*_langchain.py`, `requirements-extra.txt`). |
| `../pdfs/T5-S5 Sistemas de almacenamiento y recuperacion.pptx.pdf` | Diapositivas (37 págs.) de esta sesión. |

## Flujo del notebook

1. Config: `INDEX_NAME` (`s5-storage-retrieval`), `CLOUD/REGION`, `NAMESPACE=s5-policies-main`,
   `text-embedding-3-small` a 1536 dims (coseno); helper `remote_operation` (omite si faltan claves).
2. Corpus determinista de **128 documentos** (8 categorías × 4 países × 2 contratos × 2 versiones) con metadatos
   planos (`doc_id, country, status, employee_type, access_level, effective_day, version, tenant, …`).
3. `connect_pinecone` (SDK crea/valida índice) → `PineconeVectorStore` → `wait_for_records` (consistencia
   eventual) → ingesta con IDs explícitos (upsert).
4. Búsqueda sin/con filtro; catálogo de operadores (`$eq,$in,$gte,$or,$and`); post-filtro Python vs filtro integrado
   (1/6 vs 6/6 resultados).
5. CRUD sobre `crud-vacaciones-es`; reconexión sin ingesta; namespaces `s5-tenant-acme/orbit`; versiones
   `s5-policy-v1/v2` con ruta activa.

## Precauciones (coste y efectos remotos)

- **Ejecutar el notebook crea/usa recursos reales** en Pinecone y **consume OpenAI** (cada ingesta re-genera
  embeddings). No ejecutarlo, ni los scripts de `extras/`, sin que el usuario lo pida expresamente.
- El notebook **nunca borra un índice**; solo opera en namespaces `s5-*` dedicados. Mantener esa regla al editarlo.
- Nunca imprimir credenciales ni mensajes de error del proveedor.
- Los extras con Docker enlazan a `127.0.0.1`; `docker compose down -v` **borra datos**. Milvus pide ≥4 núcleos y 8 GB.

## Convenciones al editar

- Las guías `EXPLICACION_sesion_XX.md` de `clases/01…05` son la plantilla de estilo: título "Guía de estudio —
  Sesión N", cita inicial con enlaces al notebook/PDF/sesiones previas, índice con anclas, lenguaje sencillo,
  analogías cotidianas, tablas y código real, resumen final, "¿qué sigue?" y preguntas de repaso.
- Toda cifra citada debe contrastarse con los outputs del notebook; los scores de coseno no son probabilidades.
- Enlaces relativos con espacios codificados (`%20`); verificar que existen.

## Gotchas conocidos

- `VALIDACION.md` dice **28 celdas (13 md / 15 código)**; el notebook real tiene **26 (10 md / 16 código)**.
- `README.md` y los README de `extras/` piden `cp .env.example .env`, pero **no existe ningún `.env.example` en esta carpeta** (usa el de la raíz).
- `VALIDACION.md` indica que no se hicieron llamadas reales a OpenAI/Pinecone, pero el notebook contiene outputs
  de una ejecución con servicios reales (fue otra ejecución).
- Python: el README recomienda 3.12 (la sesión 4 exige 3.11); el `.venv` común es 3.11, que también cumple `langchain-pinecone` `<3.14`.
- Ese `.env` de la raíz y los nombres de índice/namespaces son compartidos: no reutilizar el índice para otro
  modelo de embeddings (dimensión/métrica se validan al conectar).

## Contexto del curso

Secuencia en `clases/`: 01 vectores → 02 sparse vs dense → 03 hybrid/reranking/ColBERT → 04 indexación
(HNSW/IVF/PQ) → **05 almacenamiento y recuperación (este directorio)** → 06 construcción y evaluación → 07 RAG.
Las diapositivas de todas las sesiones están en `clases/pdfs/` (T5-S1 … T5-S7).
