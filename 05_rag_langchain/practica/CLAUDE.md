# Agent.md — Cómo trabajar en `practica/`

Léelo antes de tocar nada en esta carpeta. Complementa [`../CLAUDE.md`](../CLAUDE.md) (sección 6 = enunciado, rúbrica y
mapa del PDF) y [`README.md`](./README.md) (pasos y estado).

## 1. Cómo está organizada la carpeta

```
practica/
├── [Tema 5] … RAG y Langchain.pdf   enunciado y rúbrica (3 págs.). No se edita.
├── README.md  Agent.md              guía de pasos / este documento
├── docs/paso-00…11-*.md             un documento por paso: qué se hizo, cómo ejecutarlo, en qué clase nos fijamos
├── tests/                           unittest sin red: ayudas.py (extrae código del notebook), simulacion.py, test_paso_NN_*.py
├── herramientas/                    validar_resultados, preparar_revision, validar_conclusion, empaquetar (pasos 8–11)
├── verificar.sh                     `practica/verificar.sh N` = tests de los pasos 0..N
└── Recursos /                       ← el ENTREGABLE. ¡El nombre termina en ESPACIO: siempre entre comillas!
    ├── rag_tenerife.ipynb           notebook a completar (fuente de verdad del código entregado)
    ├── utilidades.py                infraestructura suministrada (NO se modifica)
    ├── preguntas.csv  TENERIFE.pdf  datos suministrados (NO se modifican)
    ├── README.md  requirements.txt  los de la entrega (se actualizan en el paso 11)
    ├── .env  data/TENERIFE.pdf      locales; ignorados por git y fuera del ZIP
    └── resultados.json  revision.csv   se generan en los pasos 8 y 9
```

## 2. Cómo vamos a realizar las tareas

1. **Un paso cada vez**, en el orden del README. Cada paso es un cambio pequeño que deja **todo ejecutable**.
2. **El notebook es la fuente de verdad**: las 4 funciones (`fragmentar`, `recuperar`, `crear_prompt`, `hit_pagina`) viven
   **en sus celdas** (etiquetas de celda: `fragmentar`, `recuperar`, `crear_prompt`, `hit_pagina`, `api_setup`, `index`, `run`, `summary`).
   No se mueven a módulos externos ni se toca `utilidades.py`, `preguntas.csv` ni `TENERIFE.pdf`.
3. **Se edita el JSON del notebook** conservando `id`, `metadata`/etiquetas y el formato (`indent=1`, `ensure_ascii=False`);
   las celdas de API **no se ejecutan ni guardan salidas** hasta los pasos en vivo. Nunca se guardan claves en celdas o salidas.
4. Al terminar un paso: `practica/verificar.sh N` en verde → escribir/actualizar `docs/paso-NN-*.md` (qué hicimos, cómo ejecutarlo,
   **clase en la que nos fijamos**, celdas tocadas) → marcar el README → proponer el commit (no hacerlo sin que se pida).
5. **Reglas de seguridad y coste** (obligatorias):
   - La clave de EBIS solo vive en `Recursos /.env`. **Nunca** se imprime, se copia a otro fichero ni se escribe en docs/tests/README.
   - Modelo de chat **`gpt-5-nano`** (regla del sandbox). Sin bucles; `max_retries=1`; `timeout=60`.
   - **No ejecutar celdas de API ni pruebas en vivo sin que el usuario lo pida** y avisando del coste (~33 embeddings + 12 generaciones).
   - Arrancar Jupyter con `scripts/practica.sh` (no con `scripts/lab.sh`, que exporta la clave personal del `.env` raíz).
6. **La revisión manual (`revision.csv`) es del usuario.** El asistente prepara la información (`herramientas/preparar_revision.py`)
   pero no rellena los 0/1 por él, y la conclusión se redacta **solo con cifras reales** de `resumen_revision()`.

## 3. Cómo se testea

- **Sin red y sin coste** (`practica/verificar.sh [N]`, usa el `.venv` común y borra `OPENAI_API_KEY` del entorno):
  - `tests/ayudas.py` **extrae del notebook** los imports/constantes y las funciones por nombre (con `ast`) y las ejecuta:
    se prueba exactamente lo que se entrega.
  - Embeddings falsos (`DeterministicFakeEmbedding`) y LLM falso (`FakeListChatModel`) → `tests/simulacion.py` corre el flujo
    real de `utilidades.ejecutar_pruebas` (12 ejecuciones) en un directorio temporal.
  - Los pasos 8–11 se prueban contra esa simulación: `validar_resultados`, `preparar_revision`/`validar_revision`,
    `validar_conclusion` (300–500 palabras, tabla por k, caso, recomendación, limitación y mejora) y `empaquetar` (ZIP solo con
    los 7 archivos, sin `.env`/`data`/cachés, sin claves `sk-…`).
- **En vivo (opcional, con permiso):** celdas `api_setup`, `index` y `run`; después `validar_resultados` sobre el `resultados.json` real.
- Comprobaciones finales: `grep -R "sk-" practica` sin resultados; `git check-ignore -v "practica/Recursos /.env"`.

## 4. Dónde buscar en `clases/` para cada tarea

| Tarea | Qué mirar | Ruta |
|---|---|---|
| Cargar el PDF, registro con metadatos (`source`, `page`) | Guía S5 §2 (registro `{id, embedding, content, metadata}`) y S6 §8 (recorte del texto) | `clases/05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md`, `clases/06-Const-evaluacion/EXPLICACION_sesion_06.md` |
| `hit_pagina` (Hit@k) | Métricas puras y "localización ≠ corrección" | `clases/06-Const-evaluacion/src/retrieval_lab/evaluation/metrics.py`; guía S6 §5; S2 §13 (`recall_a_k`) |
| `fragmentar` (chunking) | Presupuestos de contexto, "no cambiar chunking y modelo a la vez" | guía S7 §4, S6 §8; `clases/07-RAG/src/umbra/generation/context.py` (`pack_context`). *El splitter en sí no se usa en clase* |
| `recuperar` (`as_retriever`) | Contrato `VectorStore`, `as_retriever` | `clases/04-indexacion-busq-efic/indexacion_busqueda_vectorial_eficiente.ipynb` (`as_retriever`), guía S4 §7 y §12; S5 §7 (`similarity_search`) |
| `crear_prompt` (citas, abstención, datos ≠ instrucciones) | `SYSTEM_PROMPT`, `citation_warnings`, prompt injection | `clases/07-RAG/src/umbra/generation/prompts.py` y `context.py`; guía S7 §5 y §12 |
| Embeddings y proveedor (OpenAI/local) | Interfaz `embed_documents`/`embed_query` | `clases/02-sistemas-recuper-info/sesion_02_sparse_vs_dense.ipynb` (`buscar_con_langchain`); guía S2 §11 |
| Modelo generativo y dos modelos | Embeddings vs LLM | guía S7 §1; `clases/07-RAG/src/umbra/generation/client.py` |
| Índice en memoria (búsqueda exacta) | Baseline exacto | guía S4 §8; `clases/04-…/…ipynb` (`IndexFlatIP`) |
| Ejecutar las 12 pruebas y leer costes | Comparación de modos, latencias, tokens | guía S7 §9; `clases/07-RAG/src/umbra/evaluation/comparison.py` |
| Revisión manual | Revisión por afirmación, "cita válida ≠ fidelidad", "sin juicio ≠ irrelevante" | guía S7 §8; S6 §4 |
| Conclusión y mejora propuesta | Límites de una conclusión; hybrid/RRF/reranking | guía S6 §14–15; S3 §6 (RRF) y S3 (reranking); S7 §16 |
| Reproducibilidad y entrega | Huellas, artefactos, checklist | guía S6 §16; `../CLAUDE.md` §6.6 |

## 5. Errores comunes (no repetir)

Pasar `paginas_referencia` al prompt o al retriever · citar como `p.15` o `p. 5, 6` (el regex exige `[TENERIFE.pdf, p. 15]`) ·
olvidar `chunk_id` · contar un `error_tecnico` como abstención · dejar celdas vacías creyendo que valen 0 ·
mostrar resultados de una ejecución anterior con otra configuración · pegar la clave en el notebook · añadir agentes/UI (no puntúa) ·
afirmar que `k=4` es mejor sin cifras · confundir Hit@k con «respuesta correcta».
