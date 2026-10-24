# CLAUDE.md — Repositorio del Tema 5: Sistemas de recuperación de la información, RAG y LangChain

Este archivo se carga en cada conversación. Léelo entero antes de responder; después abre la guía o el `CLAUDE.md` de la
carpeta concreta sobre la que trate la pregunta. **Objetivo final del usuario: hacer la práctica de `practica/` con tu
ayuda** (sección 6 de este archivo contiene todo el contexto necesario). Todo el material está en **español**: responde en
español.

## 1. Qué es este repositorio

Material y trabajo de un **máster de EBIS Business Techschool (Automatización con IA Agéntica)**, asignatura *Tema 5:
Sistemas de recuperación de la información, RAG y LangChain*. Contiene:

- **7 sesiones** (`clases/01…07`) con notebooks, código y diapositivas (`clases/pdfs/T5-S1…S7`).
- **La práctica final** (`practica/`): un asistente turístico RAG sobre una guía PDF de Tenerife.
- Para cada sesión hay una **guía de estudio** (`EXPLICACION_sesion_XX.md`, lenguaje sencillo, analogías, cifras reales
  del notebook, preguntas de repaso) y un **`CLAUDE.md`** (mapa de archivos, cómo ejecutar, costes, gotchas).

## 2. Mapa del repositorio

```
05_rag_langchain/
├── CLAUDE.md                ← este archivo
├── requirements.txt         ← dependencias del .venv común (Python 3.11, sin paquetes pesados)
├── requirements-optional.txt← torch, transformers, sentence-transformers, google-genai, beir (no instalados)
├── .env / .env.example      ← claves (el .env NO se lee ni se imprime; está en .gitignore)
├── .gitignore  scripts/lab.sh  .venv/
├── clases/
│   ├── 01-vectores/                 EXPLICACION_sesion_1.md  (notebook)
│   ├── 02-sistemas-recuper-info/    EXPLICACION_sesion_02.md (sparse vs dense, BM25, embeddings)
│   ├── 03-recuper-info-2/           EXPLICACION_sesion_03.md (hybrid, RRF, reranking, ColBERT, multimodal)
│   ├── 04-indexacion-busq-efic/     EXPLICACION_sesion_04.md + CLAUDE.md (FAISS: exact, HNSW, IVF, IVF-PQ)
│   ├── 05-sist-almac-recuperc-AWS/  EXPLICACION_sesion_05.md + CLAUDE.md (Pinecone, filtros, CRUD, namespaces)
│   ├── 06-Const-evaluacion/         EXPLICACION_sesion_06.md + CLAUDE.md + src/retrieval_lab/CLAUDE.md (TREC-COVID)
│   ├── 07-RAG/                      EXPLICACION_sesion_07.md + CLAUDE.md + app/ + src/{umbra,retrieval_lab}/CLAUDE.md
│   └── pdfs/                        diapositivas T5-S1 … T5-S7
└── practica/
    ├── [Tema 5] … RAG y Langchain.pdf   ← ENUNCIADO Y RÚBRICA (3 págs.)
    └── "Recursos "/                     ← ¡nombre con ESPACIO FINAL! (siempre entre comillas)
        rag_tenerife.ipynb  utilidades.py  preguntas.csv  TENERIFE.pdf  README.md  requirements.txt
```

Guías: [01](clases/01-vectores/EXPLICACION_sesion_1.md) ·
[02](clases/02-sistemas-recuper-info/EXPLICACION_sesion_02.md) ·
[03](clases/03-recuper-info-2/EXPLICACION_sesion_03.md) ·
[04](clases/04-indexacion-busq-efic/EXPLICACION_sesion_04.md) ·
[05](clases/05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md) ·
[06](clases/06-Const-evaluacion/EXPLICACION_sesion_06.md) ·
[07](clases/07-RAG/EXPLICACION_sesion_07.md). Las sesiones 01–03 no tienen `CLAUDE.md` propio.

## 3. Qué se aprende: el hilo del tema

```
representar → indexar → almacenar → recuperar → evaluar → generar con evidencia (RAG)
   S1–S3        S4          S5         S3, S6      S6              S7
```

| Sesión | Idea central | Conceptos y cifras clave |
|---|---|---|
| **1 · Vectores** | Un texto se vuelve una lista de números que se pueden comparar. | Vector = lista ordenada; dimensión; magnitud y normalización; distancias (euclídea, Manhattan, Minkowski, Chebyshev); **la métrica y la escala cambian el resultado**; producto escalar vs **coseno** (normalizar + producto escalar = coseno); mini buscador: tokenizar → vocabulario → BoW → coseno → ranking top-k. |
| **2 · Sparse vs Dense** | Representar es elegir qué conservar. | BoW → TF-IDF → **BM25** (`k1` saturación, `b` longitud; 1.2/0.75); **lexical gap**; embedding = vector denso y aprendido; consulta y documento a veces con prefijos distintos; interfaz LangChain `embed_documents`/`embed_query`; **Recall@k**; sparse gana en identificadores exactos, dense en paráfrasis. |
| **3 · Métodos modernos** | Ningún retriever ve toda la relevancia. | **Hybrid**; los scores no son comparables → *score fusion* (min-max + `alpha`) o **RRF** (`1/(60+posición)`); *retrieve-then-rerank*; bi-encoder vs cross-encoder; ColBERT (MaxSim); multimodal. |
| **4 · Indexación** | La búsqueda exacta cuesta O(N·d). | **ANN** aproxima *la búsqueda*, no la similitud; Recall@k del ANN; **HNSW** (`M`, `efConstruction`, `efSearch`), **IVF** (`nlist`, `nprobe`), **PQ**; FAISS con LangChain (`VectorStore`); 50 000 docs: exact 1,6 ms, HNSW ef=50 recall 1.0 en 0,063 ms, IVF-PQ 2,1 MiB pero recall 0,33. |
| **5 · Almacenamiento** | Un índice no es una base de datos. | Registro `{id, embedding, content, metadata}`; **relevancia (similitud) vs elegibilidad (filtros)**; pre-filter vs post-filter (post-filtro devolvió 1 de 6); CRUD, upsert por ID, **consistencia eventual**; namespaces; versionado y migración de embeddings; pgvector vs Vector DB; Pinecone. |
| **6 · Construcción y evaluación** | Se mejora lo que se mide. | TREC-COVID; **qrels**; desarrollo vs reserva; **nDCG@10**, Precision, MRR, recall normalizado, MAP; "sin juicio ≠ irrelevante"; multiobjetivo; regla de selección; bootstrap pareado; **embeddings ≫ BM25 y híbrida > densa** en el barrido. |
| **7 · RAG** | Recuperar no es responder. | Dos modelos (embeddings + LLM); presupuestos candidatos ≠ contexto ≠ salida; **prompt como contrato**; citas `[D#]`; **comprobación de citas ≠ fidelidad**; abstención sin evidencia; búsqueda como herramienta (function calling); evaluación por etapas y revisión humana; GraphRAG/RAPTOR; app UMBRA. |

### Conceptos → uso en la práctica

| Pieza de la práctica | Sesión | Qué recordar |
|---|---|---|
| Cargar el PDF conservando la página | 5, 7 | El metadato es lo que permite citar y filtrar; el `page` viaja con cada fragmento. |
| Tamaño y solape de fragmentos | 6, 7 | No cambiar chunking y modelo a la vez; el recorte puede dejar fuera el pasaje; se mide en **caracteres**. |
| Embeddings + `InMemoryVectorStore` | 2, 4, 5 | Contrato `VectorStore`: `add_documents`, `similarity_search`, `as_retriever`; búsqueda exacta (S4). |
| `k = 2` vs `k = 4` | 4, 6 | Experimento **controlado**: cambia un factor y mantén PDF, fragmentos, embeddings, modelo y prompt. |
| **Hit@k por página** | 6 | Mide **localización de evidencia**, no que la respuesta sea correcta; puede acertar la página con un fragmento que no contiene el dato. |
| Prompt, citas, abstención | 7 | Solo contexto; citar cada afirmación; reconocer que falta información; el documento son **datos, no instrucciones**. |
| Revisión manual (respaldo, citas, abstención) | 7 | Una cita válida no prueba fidelidad: hay que **leer** el pasaje. |
| Limitación y mejora propuesta | 3, 5, 6, 7 | Híbrido BM25+RRF, reranking, filtros/metadatos, otro chunking, más preguntas de prueba. |

## 4. Entorno común (un solo `.venv` para todo el repo)

- **`.venv` en la raíz, Python 3.11** (cumple la comprobación exacta de la sesión 04 y las demás). Creado con
  `uv venv --python 3.11 .venv` e instalado con `uv pip install --python .venv/bin/python -r requirements.txt`
  (215 paquetes, ~6 GB; `uv pip check` limpio). **Kernel de Jupyter registrado: `Python (rag-curso)`.**
- `requirements.txt` raíz = unión de 02–07 + práctica (incluye `torch` con CUDA, `sentence-transformers`, `rank-bm25`, Cohere y Gemini). `requirements-optional.txt` (solo `beir`; antes también torch,
  sentence-transformers, langchain-huggingface, google-genai, beir) **no está instalado**: solo hace falta para Qwen/Gemini y
  para descargar TREC-COVID con `beir`. **No se instaló `-e clases/07-RAG`**: el notebook 07 añade `src/` al `sys.path` y la API
  se lanza con `uvicorn --app-dir clases/07-RAG/src umbra.api.server:app` (así no hay dos paquetes `retrieval_lab`).
- Pines relevantes: `langchain-core==1.6.3`, `langchain-openai==1.6.2`, `pinecone==7.3.0`, `faiss-cpu==1.12.0`,
  `model2vec==0.9.0`, `numpy==2.1.3`, `pandas` resuelto a 3.0.x (04 pedía 2.2.3 y 05 3.0.5; no se ha ejecutado el notebook 04 con 3.x).
- Usar **sin activar**: `.venv/bin/python …`, `uv pip install --python .venv/bin/python …`.
  Para abrir Jupyter con las claves: `scripts/lab.sh [carpeta]` (exporta el `.env` raíz al proceso **sin imprimirlo**; los
  notebooks usan `load_dotenv(override=False)`/`setdefault`, así que respetan lo ya exportado). Para la práctica:
  `scripts/lab.sh "practica/Recursos "`.
- **`.env` raíz** (OPENAI, GOOGLE, COHERE, PINECONE…): **nunca leerlo, imprimirlo ni copiarlo**. `.env.example` (raíz)
  lista solo nombres. Está en `.gitignore` y **fuera del índice de git**; sigue en el historial local (3 commits, sin remoto):
  si el repo se comparte, hay que **rotar las claves**.
- `.gitignore`: ignora `.venv`, `.env*` (salvo `.env.example`), `__pycache__`, `*.zip`, `node_modules`, y datos/cachés generados
  con **rutas ancladas** (`/clases/06-…/data/`, `/clases/06-…/artifacts/`, `/clases/07-RAG/data/`, `/clases/07-RAG/artifacts/`,
  `/clases/04-…/cache_vector_search/`, `/practica/**/data/`). **No** usar patrones sueltos como `data/` (ignorarían los paquetes
  `src/*/data/`). `clases/07-RAG/app/dist/` **sí** se versiona. `resultados.json` y `revision.csv` de la práctica **sí**.

## 5. Reglas de trabajo para Claude

1. **Español**, sencillo; las cifras se contrastan con los notebooks/guías (fuente de verdad), no de memoria.
2. Antes de responder sobre una sesión, **lee su guía `EXPLICACION_sesion_XX.md`** y su `CLAUDE.md`.
3. **No ejecutar nada que llame a OpenAI, Pinecone o cualquier API de pago** (notebooks de 05–07, `RAGService`, la práctica
   con `RUN`) **sin petición expresa**; avisa del coste antes. Las sesiones 05–07 crean recursos reales en Pinecone.
4. **Nunca leer, imprimir ni commitear el `.env`.** No pegar claves en celdas ni salidas.
5. **No hacer commits, `push`, ni reescribir historial** salvo petición. Añadir los trailers de atribución configurados cuando
   se pidan commits. No borrar recursos remotos.
6. **Rutas con espacios:** `practica/Recursos ` termina en espacio → siempre entre comillas (`"practica/Recursos /x"`).
7. `clases/07-RAG/src/retrieval_lab` es una **copia** de `clases/06-Const-evaluacion/src/retrieval_lab`: no editar una esperando
   que cambie la otra.
8. Convención de las guías: título "Guía de estudio — Sesión N", enlaces a notebook/PDF/sesiones previas, índice con anclas,
   analogías cotidianas, tablas y código real, resumen, "¿qué sigue?" y preguntas de repaso.
9. Al editar notebooks: no guardar claves ni salidas con datos privados; no ejecutar "todo" en los de 05–07
   (el notebook 07 se guardó con `RUN_LIVE = True` y `RUN_EXTRAS = True`).

## 6. LA PRÁCTICA FINAL — "Un asistente turístico con RAG" (Tenerife)

> **Trabajo por pasos:** la práctica se hace en 12 mini-tareas ejecutables y testeadas. Guía: [`practica/README.md`](practica/README.md)
> (pasos y estado), [`practica/Agent.md`](practica/Agent.md) (cómo trabajar, testear y dónde mirar en `clases/`) y `practica/docs/paso-NN-*.md`.
> Estado: **pasos 0–5 hechos** (`practica/verificar.sh 5`, sin red ni coste); pasos 6–11 preparados, falta ejecutar en vivo.
> **API de la práctica:** clave corporativa de EBIS en `practica/Recursos /.env` (ignorado; **nunca imprimirla ni copiarla**),
> modelo obligatorio **`gpt-5-nano`** (sin `temperature=0`), presupuesto limitado y sin bucles. Lanzar con `scripts/practica.sh`
> (no con `scripts/lab.sh`, que exporta la clave personal). No ejecutar celdas de API sin petición expresa.

Fuentes: enunciado `practica/[Tema 5] … RAG y Langchain.pdf` (3 págs.) y `practica/Recursos /` (notebook, utilidades, README, CSV,
PDF). **Trabajar en `practica/Recursos /`.**

### 6.1 Enunciado (resumen fiel)

- **Negocio:** especialista en automatización con IA en *Tenerife a tu Ritmo* (empresa ficticia). El equipo de atención responde
  consultas repetidas sobre lugares, rutas y gastronomía con una **guía PDF**; hace falta un **prototipo verificable** y una
  **recomendación sobre sus límites**. No hay reservas, tarifas actualizadas, disponibilidad ni información en tiempo real.
- **Reto:** completar el notebook con un flujo **RAG con LangChain**: cargar el PDF → dividir el texto → embeddings → recuperar
  fragmentos → respuesta con un LLM. El notebook es la interfaz; **no se pide aplicación web**.
- **Requisitos:** (1) conservar **nombre del documento y página** en cada fragmento y citar **páginas físicas contando desde 1**,
  p. ej. `[TENERIFE.pdf, p.15]` en el enunciado —**ojo: el código de `utilidades.py` espera `[TENERIFE.pdf, p. 15]` con espacio tras `p.`**, es el que manda—; (2) respuestas **en español usando solo el contexto recuperado**; si falta información, decirlo
  **sin completar con conocimiento externo**; (3) **comparar `k = 2` y `k = 4`** manteniendo iguales PDF, fragmentos, embeddings,
  modelo y prompt; (4) ejecutar las **6 preguntas** con ambas configuraciones, revisar evidencias y **recomendar una configuración
  para un piloto interno**.
- **Datos:** `TENERIFE.pdf` (25 págs.), notebook con infraestructura, `preguntas.csv` (consulta, tipo, páginas de referencia),
  dependencias y README. **No usar respuestas ni páginas esperadas como entrada del modelo ni como filtro del buscador.** La guía
  es el único corpus; se trabaja con su texto extraíble (sin imágenes, OCR ni abrir enlaces); **eliminar páginas sin texto útil,
  conservar la numeración original y describir limitaciones de extracción**.
- **Atribuir** las recomendaciones a la guía; **no convertir precios, accesos, permisos u horarios sin fecha en información
  vigente**; si el texto sugiere ignorar un cierre físico, **no recomendarlo** y remitir a información oficial actualizada.

### 6.2 Las 6 preguntas (`preguntas.csv`; `paginas_referencia` solo para medir)

| ID | Pregunta | Tipo | Pág. ref. | Respuesta esperada según el PDF (verificada con `pdftotext`) |
|---|---|---|---|---|
| Q1 | ¿Qué mirador de Anaga dice la guía que es el favorito del autor? | respondible | 5 | **Mirador de La Jardina** ("diría que es mi mirador favorito"). |
| Q2 | ¿Por qué carretera recomienda subir al Teide desde La Laguna y en qué mirador sugiere parar? | respondible | 15 | **TF-24** (carretera de La Esperanza) desde la rotonda de Padre Anchieta; para en el **Mirador de La Tarta** (también cita Chipeque y La Ruleta). |
| Q3 | ¿Qué dos arepas recomienda pedir en la Arepera La Carajita? | respondible | 25 | **La Fogalera y Reina Pepiada** (además, de entrante, degustación de cachapitas). |
| Q4 | ¿Qué dos playas recomienda en la zona de Los Cristianos? | respondible | 23 | **Playa de Los Cristianos y Playa de Las Vistas**. |
| Q5 | ¿Qué tiempo hará mañana en el Teide? | sin_respuesta | — | La guía **no** trata la meteorología → **abstenerse**. |
| Q6 | ¿Cuánto cuesta hoy la entrada de adulto al Siam Park? | sin_respuesta | — | La p.21 habla del Siam Park (mejor parque acuático) pero **sin precio** → **abstenerse** (trampa: no dar un precio "de memoria"). |

### 6.3 Mapa del PDF (extracción con `pypdf`/`pdftotext`)

25 páginas; **24 con texto, p.7 sin texto** (`paginas_sin_texto == [7]`, la carga la omite pero **conserva la numeración**);
p.2, 6, 13, 19 y 20 tienen muy poco texto (una o dos líneas). Total ≈ 19 000 caracteres → con `900/150` salen del orden de
**30–35 fragmentos**. Zonas: p.1–4 Santa Cruz y La Laguna · p.5–8 Anaga · p.9–11 Orotava/Puerto de la Cruz · p.12–14 Isla Baja
(Icod, Garachico, Punta de Teno) · p.15–16 Teide · p.17–21 sur (playas, beach clubs, Siam Park) · p.22 Masca · p.23 El Médano,
La Tejita, Los Cristianos · p.24–25 "Otras vainas" (dónde comer). Las guías enlazan a vídeos/ubicaciones (`[ubicación]`) que **no**
se abren. El tono es coloquial y lleno de "creo que", "actualmente lo desconozco" (**incertidumbre**: conservarla).

### 6.4 Qué medir (y cómo lo calcula `utilidades.py`)

| Métrica | Casos | Quién la calcula |
|---|---|---|
| **Hit@k por página** | Q1–Q4 (media de 4) | Automática: `hit_pagina(paginas_recuperadas, paginas_referencia)`; **no aplica a Q5–Q6** (`None` → `NA`). Es **localización de evidencia, no corrección**. |
| **Respaldo** | Q1–Q4 | **Manual** (0/1): respuesta **completa** y sostenida por el contexto. |
| **Citas** | Q1–Q4 | **Manual** (0/1): cada afirmación turística tiene una cita que **realmente la apoya** en una página recuperada. |
| **Abstención** | Q5–Q6 | **Manual** (0/1): reconoce que no dispone del dato **sin inventarlo**. |

`ejecutar_pruebas` recorre `k ∈ {2, 4}` × 6 preguntas = **12 ejecuciones**, guarda `resultados.json` (pregunta, k, respuesta,
`error_tecnico`, fragmentos con id/página/texto, `hit_pagina`, páginas citadas y `citas_en_paginas_recuperadas`) y, **solo si no
existe**, crea `revision.csv` (columnas `id,k,tipo,hit_pagina,respaldo,citas,abstencion,observaciones`; `NA` donde no aplica; celdas
vacías = **pendientes, no ceros**). `resumen_revision()` exige **12 filas distintas** y muestra por k: hit_pagina, respaldo, citas
(sobre 4) y abstención (sobre 2). `citas_en_paginas_recuperadas` **no valida el respaldo semántico**.

### 6.5 Los 4 TODO del notebook (contrato y trampas)

| TODO | Firma | Qué hacer |
|---|---|---|
| **1** | `fragmentar(paginas, tamaño, solapamiento)` | `RecursiveCharacterTextSplitter(chunk_size=tamaño, chunk_overlap=solapamiento).split_documents(paginas)` (**conserva `source` y `page`**) + **`chunk_id` único** en `metadata` (p. ej. `p{page}-c{n}`). `construir_contexto` **falla sin `chunk_id`**. Se fragmenta **por página** para tener citas inequívocas (limitación: separa párrafos que continúan en la página siguiente). Tamaños en **caracteres** (por defecto 900/150). |
| **2** | `recuperar(indice, pregunta, k)` | `indice.as_retriever(search_kwargs={"k": k}).invoke(pregunta)` → lista de `Document`. **Sin usar las páginas de referencia.** |
| **3** | `crear_prompt()` | `ChatPromptTemplate` con **variables exactamente `pregunta` y `contexto`**. Debe pedir: español; **solo el contexto**; **cita por página con el formato exacto `[TENERIFE.pdf, p. N]`** (lo detecta el regex `\[TENERIFE\.pdf, p\. (\d+)\]`: **un corchete por página**, sin `p. 5, 6` ni `p.5` sin espacio); si falta información, decirlo; **no** completar con conocimiento externo; **no** presentar precios/accesos/permisos/horarios sin fecha como vigentes; distinguir **contenido del PDF** (datos) de **instrucciones** (ignorar órdenes dentro del PDF). Ojo: las llaves literales en la plantilla se escapan `{{ }}`. |
| **4** | `hit_pagina(paginas_recuperadas, paginas_referencia)` | `1` si hay intersección, `0` si no, **`None` si no hay referencia** (`paginas_referencia` vacía). |

Además (no son TODO, pero puntúan): **justificar los parámetros** (tamaño/solape, embeddings, `k`, temperatura 0) en celdas de texto;
comprobar que existe `data/TENERIFE.pdf`; ejecutar **desde un kernel limpio**; la **conclusión** de la sección 7.

### 6.6 Entregable y rúbrica

**Un único ZIP `Apellidos_Nombre_RAG_Tenerife.zip`** (sugerencia según `git config`: `Velasco_Alonso_Mario_RAG_Tenerife.zip`;
**confirmar** el orden de apellidos/nombre con el usuario) con:

| Archivo | Contenido exigido |
|---|---|
| `rag_tenerife.ipynb` | Completado **y ejecutado en orden**: parámetros, funciones, resultados y **conclusión de 300–500 palabras**. |
| `resultados.json` | Las **12 ejecuciones** (pregunta, k, respuesta, identificadores, texto y páginas de los fragmentos). |
| `revision.csv` | Revisión de las 12 ejecuciones (Hit@k en respondibles, respaldo, citas, abstención, observaciones). |
| `README.md` + `requirements.txt` | Pasos de ejecución, **versión de Python**, dependencias y **nombres** de variables de entorno; incluir `preguntas.csv` y `utilidades.py` (y cualquier módulo añadido). |

**No incluir** claves, `.env`, entornos virtuales ni cachés (tampoco `data/TENERIFE.pdf`: el corrector aporta el suyo). Se admite otro
proveedor/almacén vectorial si se mantiene el flujo con LangChain y se documenta.

| Criterio | Peso | Cómo se cubre |
|---|---|---|
| Preparación documental | **15 %** | Carga con páginas físicas, p.7 omitida y documentada, `chunk_id`+metadatos, limitaciones de extracción. |
| Recuperación de información | **20 %** | Retriever correcto sin fuga de referencias; comparación `k=2`/`k=4` controlada; `hit_pagina` correcto. |
| Respuestas respaldadas por evidencia | **30 %** | Prompt sólido; citas con el formato exacto; abstención en Q5–Q6; sin conocimiento externo. |
| Evaluación y toma de decisiones | **25 %** | `revision.csv` honesta (0/1/NA), tabla con cifras por k, caso concreto, recomendación y mejora justificadas. |
| Reproducibilidad | **10 %** | README/requirements/versión de Python, sin claves, ejecución desde kernel limpio. |

**No puntúa:** memoria multiturno, meteorología, *function calling*, agentes, despliegue ni interfaz gráfica. **No se exige** que
`k=4` supere a `k=2` ni una puntuación perfecta: las 6 preguntas son un **diagnóstico pequeño, no una validación general**.

### 6.7 Estado actual de la carpeta y desajustes conocidos

- **Falta `data/TENERIFE.pdf`**: el notebook usa `PDF = Path("data/TENERIFE.pdf")` y el README lo exige, pero el PDF está junto al
  notebook. Solución sin duplicar en git: `mkdir -p "practica/Recursos /data" && cp "practica/Recursos /TENERIFE.pdf" "practica/Recursos /data/"`
  (`/practica/**/data/` está ignorado). **No cambiar la ruta del notebook**: el corrector la usa.
- El README cita `.env.example`, que **no existe** en esa carpeta (el `.env.example` de la raíz sirve de referencia). La práctica solo
  necesita `OPENAI_API_KEY`; opcionales `OPENAI_CHAT_MODEL` (`gpt-4.1-mini`) y `OPENAI_EMBEDDING_MODEL` (`text-embedding-3-small`).
- El README pide crear un `.venv` local: **no hacerlo**; se usa el `.venv` común (mismas versiones: `langchain-core==1.6.3`,
  `langchain-openai==1.6.2`, `langchain-text-splitters==1.1.2`, `pypdf`). La entrega **sí** lleva el `requirements.txt` propio de la
  práctica e indicará Python 3.11.
- Verificado sin red: `cargar_paginas` → `{'paginas_pdf': 25, 'paginas_con_texto': 24, 'paginas_sin_texto': [7]}`; `leer_preguntas` OK.
- `resultados.json` y `revision.csv` **no existen todavía** (los crea `ejecutar_pruebas`). `revision.csv` **se conserva** si ya existe:
  si se repite la ejecución, **guardar copia y revisar de nuevo** las 12 filas.

### 6.8 Plan de ejecución paso a paso

1. Preparar `data/` (6.7) y abrir con `scripts/lab.sh "practica/Recursos "`; kernel **Python (rag-curso)**.
2. Inspeccionar la carga (celda 2): páginas con/sin texto; describir la limitación de extracción (p.7, páginas casi vacías, sin
   imágenes/enlaces).
3. Completar **TODO 1–4** y justificar parámetros (900/150 caracteres: las páginas son cortas —la mayoría < 1 400 caracteres—, así
   que cada página da 1–4 fragmentos; el solape protege frases en el corte).
4. Celda 10–11 (**llama a la API de embeddings**, coste ≈ céntimos): crear el índice **una sola vez** y reutilizarlo en la comparación.
5. Celda 13 (**12 generaciones**, ≈ céntimos con `gpt-4.1-mini`): revisar `error_tecnico` (un fallo técnico **no** es una abstención).
6. **Revisar a mano** las 12 respuestas leyendo también el texto de `fragmentos` en `resultados.json` (una página esperada puede haberse
   recuperado con un fragmento **sin** el dato): rellenar `revision.csv` (0/1/NA) y ejecutar `resumen_revision()`.
7. Redactar la **conclusión (300–500 palabras)** en la celda final.
8. Empaquetar el ZIP con los archivos de 6.6 (sin `.env`, `.venv`, cachés ni `data/`).

### 6.9 Esquema de la conclusión (300–500 palabras, con cifras reales)

1. **Decisiones:** tamaño y solape de fragmentos (por página, caracteres), embeddings (`text-embedding-3-small`), recuperación (exacta,
   `k`), y **cómo se impide responder sin evidencia** (prompt de solo-contexto + abstención + revisión).
2. **Tabla con las 4 métricas por k** (Hit@k, respaldo, citas, abstención) y comparación de `k=2` vs `k=4`.
3. **Un caso concreto** de acierto, fallo o ausencia de mejora (citando pregunta, k, páginas y fragmento).
4. **Configuración recomendada** para el piloto interno y **una limitación** (p. ej. solo 6 preguntas, fragmentación por página, texto
   coloquial con datos "sin fecha", sin vigencia de precios) con **una mejora** ligada a un fallo observado o a una carencia del
   conjunto de pruebas (híbrido BM25+RRF, reranking, más preguntas/juicios, chunking por secciones, filtros por zona).

### 6.10 Errores comunes a evitar

Usar `paginas_referencia` en el prompt o en el retriever · citar con otro formato (`p.15`, `[p. 15]`, `p. 5, 6`) · olvidar `chunk_id` ·
tratar un `error_tecnico` como abstención correcta · dejar celdas vacías creyendo que valen 0 · presentar resultados de una ejecución
anterior tras cambiar la configuración · pegar la clave en el notebook · añadir agentes/UI (no puntúa) · afirmar que `k=4` es mejor sin
cifras · confundir Hit@k con "respuesta correcta".

## 7. Decisiones pendientes y gotchas globales

- **Nombre del ZIP:** confirmar apellidos/nombre con el usuario (git: *Mario Velasco Alonso*).
- **Claves en el historial de git:** el `.env` estuvo versionado (3 commits). Sin remoto no se han subido; rotar si se comparte.
- El notebook 04 exige Python 3.11 (el `.venv` común lo es). El resto de guías/`CLAUDE.md` describen sus particularidades.
- Las carpetas 05/06/07 **no se pueden ejecutar de extremo a extremo** en este checkout (faltan `data/`, `artifacts/`, Pinecone
  activo y `SESSION06_DIR`); ver sus `CLAUDE.md`.
- Los desajustes README↔notebook de cada sesión están anotados en su `CLAUDE.md` (sección "Gotchas").
