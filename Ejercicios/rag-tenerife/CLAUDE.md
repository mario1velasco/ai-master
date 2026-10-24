# CLAUDE.md — Proyecto rag-tenerife

Ejercicio de curso: construir un RAG mínimo sobre la guía turística `TENERIFE.pdf` con LangChain + OpenAI. El usuario hará preguntas para que se le explique cómo resolver la tarea; no completar código sin que lo pida.

## Contenido

- `rag_tenerife_final.ipynb` — notebook de la tarea. Hay **4 TODO** por completar:
  1. `fragmentar(paginas, tamaño, solapamiento)` — `RecursiveCharacterTextSplitter` por página, conservando metadatos y añadiendo `chunk_id` único.
  2. `recuperar(indice, pregunta, k)` — retriever con `k` sobre el `InMemoryVectorStore`; devuelve `Document`s.
  3. `crear_prompt()` — `ChatPromptTemplate` con variables `pregunta` y `contexto`: español, citas `[TENERIFE.pdf, p. N]`, límite documental, abstención, separar contenido del PDF de instrucciones.
  4. `hit_pagina(recuperadas, referencia)` — 1 si hay intersección, 0 si no, `None` si no aplica (preguntas sin respuesta).
- `utilidades.py` — infraestructura ya hecha (no tocar): `cargar_paginas`, `leer_preguntas`, `construir_contexto`, `ejecutar_pruebas` (6 preguntas × k=2 y k=4 = 12 ejecuciones → `resultados.json` + `revision.csv`), `resumen_revision`.
- `preguntas.csv` — 6 preguntas: Q1–Q4 `respondible` (con página de referencia), Q5–Q6 `sin_respuesta` (tiempo de mañana, precio hoy del Siam Park → el sistema debe abstenerse).
- `TENERIFE.pdf` — la guía (el notebook espera `data/TENERIFE.pdf`; falta crear esa carpeta/copiar el PDF).
- `README.md` — preparación del entorno (venv, `requirements.txt`, `.env` con `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL` por defecto `gpt-4.1-mini`, `OPENAI_EMBEDDING_MODEL` `text-embedding-3-small`), ejecución y entrega (ZIP).
- `clases/EXPLICACION_sesion_*.md` — apuntes de teoría (ver índice abajo) como material de apoyo.

## Índice de apuntes (`clases/`) — dónde buscar

- `sesion_1` — Vectores desde cero: operaciones, magnitud/normalización, distancias (euclídea, etc.), producto escalar y coseno, mini buscador (scoring, ranking, top-k).
- `sesion_02` — Representación: sparse (BoW, TF-IDF, BM25) vs dense (embeddings), lexical gap, embeddings con LangChain, Recall@k.
- `sesion_03` — Recuperación moderna: híbrida (score fusion, RRF), retrieve-then-rerank, bi-encoder vs cross-encoder, ColBERT/multi-vector, multimodal.
- `sesion_04` — Índices vectoriales eficientes: exacto (Flat), HNSW, IVF, IVF-PQ, ANN, trade-off recall/latencia, `as_retriever`.
- `sesion_05` — Vector DBs (Pinecone): registros y metadatos, filtros, CRUD, persistencia, namespaces, versiones, pgvector/Qdrant/Milvus/Weaviate.
- `sesion_06` — Evaluación de retrieval (TREC-COVID): métricas, barrido de experimentos, híbrido+RRF, análisis de errores, reserva final.
- `sesion_07` — **RAG** (la más relevante para esta tarea): flujo pregunta→contexto→respuesta, presupuestos de candidatos/contexto, prompt como contrato (instrucciones, evidencia, citas), búsqueda como herramienta, evaluación por etapas, GraphRAG/RAPTOR, seguridad y límites.

## Parámetros del notebook

`CHUNK_SIZE=900` (caracteres), `CHUNK_OVERLAP=150`, temperatura 0, índice en memoria.

## Flujo de la tarea

Completar los 4 TODO → ejecutar con kernel limpio → revisar manualmente `revision.csv` (0/1/NA: hit_pagina, respaldo, citas, abstencion) leyendo los fragmentos en `resultados.json` → `resumen_revision()` → escribir en la sección 7 un análisis de 300–500 palabras (decisiones de chunking/recuperación, tabla de 4 métricas por k, un caso concreto, configuración recomendada, límite y mejora) con cifras reales.

## Reglas

- La página de referencia nunca se pasa al buscador ni al modelo; solo se usa después para Hit@k.
- No guardar claves en el notebook; no entregar `.env`, `.venv` ni cachés.
- No presentar resultados antiguos como si fueran de la nueva configuración.
