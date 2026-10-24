# Guía de estudio — Sesión 6: Construcción y evaluación de sistemas de recuperación (TREC-COVID, métricas y experimentos)

> Esta guía explica, con lenguaje sencillo y muchos ejemplos, el contenido de
> [`01_retrieval_system_evaluation.ipynb`](./01_retrieval_system_evaluation.ipynb), de las diapositivas
> [`T5-S6 Sistemas de almacenamiento y recuperacion.pdf`](../pdfs/T5-S6%20Sistemas%20de%20almacenamiento%20y%20recuperacion.pdf)
> (el nombre del fichero es engañoso: su contenido es "construcción y evaluación de sistemas de
> recuperación"), del código de [`src/retrieval_lab/`](./src/README.md) y del entorno descrito en
> [`README.md`](./README.md).
>
> Es la continuación directa de las sesiones anteriores — si no las has leído, échales un vistazo primero:
> [sesión 1 (vectores)](../01-vectores/EXPLICACION_sesion_1.md),
> [sesión 2 (sparse vs dense)](../02-sistemas-recuper-info/EXPLICACION_sesion_02.md),
> [sesión 3 (hybrid, reranking, ColBERT)](../03-recuper-info-2/EXPLICACION_sesion_03.md),
> [sesión 4 (indexación: HNSW, IVF, PQ)](../04-indexacion-busq-efic/EXPLICACION_sesion_04.md) y
> [sesión 5 (almacenamiento, filtros, CRUD)](../05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md). Hasta
> ahora estudiamos **las piezas por separado**. Aquí las juntamos en un caso real y respondemos a la pregunta
> que las une: **¿cómo sabemos, con datos y no "a ojo", qué configuración es mejor?**

## Índice

1. [Del prototipo al sistema real](#1-del-prototipo-al-sistema-real)
2. [El caso real: TREC-COVID](#2-el-caso-real-trec-covid)
3. [La decisión que queremos tomar (y qué significa "offline")](#3-la-decisión-que-queremos-tomar-y-qué-significa-offline)
4. [El contrato de evaluación: desarrollo, reserva final y relevancia](#4-el-contrato-de-evaluación-desarrollo-reserva-final-y-relevancia)
5. [Las métricas de recuperación](#5-las-métricas-de-recuperación)
6. [Retrieval es una optimización multiobjetivo](#6-retrieval-es-una-optimización-multiobjetivo)
7. [Qué se almacena en Pinecone y por qué](#7-qué-se-almacena-en-pinecone-y-por-qué)
8. [Preparación: BM25, embeddings y caché](#8-preparación-bm25-embeddings-y-caché)
9. [Primer resultado: BM25 como referencia](#9-primer-resultado-bm25-como-referencia)
10. [El barrido de experimentos (resultados reales)](#10-el-barrido-de-experimentos-resultados-reales)
11. [Búsqueda híbrida y Reciprocal Rank Fusion](#11-búsqueda-híbrida-y-reciprocal-rank-fusion)
12. [Elegir sin perseguir la última milésima](#12-elegir-sin-perseguir-la-última-milésima)
13. [Leer un error antes de culpar al modelo](#13-leer-un-error-antes-de-culpar-al-modelo)
14. [La reserva final: ¿la mejora se sostiene?](#14-la-reserva-final-la-mejora-se-sostiene)
15. [Qué falta antes de producción](#15-qué-falta-antes-de-producción)
16. [Arquitectura del laboratorio (`src/retrieval_lab/`)](#16-arquitectura-del-laboratorio-srcretrieval_lab)
17. [Resumen final](#17-resumen-final)
18. [¿Qué sigue después?](#18-qué-sigue-después)

---

## 1. Del prototipo al sistema real

Hasta ahora hemos estudiado por separado las piezas fundamentales de un sistema de recuperación. En un
sistema real **todas esas decisiones están conectadas** y hay que tomarlas sobre un caso concreto. La
diapositiva las agrupa en cuatro familias:

| # | Decisión | Preguntas típicas |
|---|---|---|
| 1 | **Representación** | ¿Qué modelo de embeddings? ¿Qué dimensionalidad? ¿Documento completo o *chunks*? |
| 2 | **Retrieval** | ¿Sparse, Dense o Hybrid? ¿Exact Search o ANN? ¿Necesitamos *reranking*? |
| 3 | **Arquitectura** | ¿Índice local o Vector Database? ¿Qué coste de memoria y latencia podemos asumir? |
| 4 | **Evaluación** | ¿Qué significa que el sistema sea "mejor"? ¿Con qué datos y métricas lo demostramos? |

El pipeline completo, como lo dibuja la diapositiva "Diseñar el pipeline significa tomar decisiones":

```
Representación          Candidate Retrieval     Search                  Ranking
(modelo, dimensión,  →  (sparse / dense /    →  (exact / ANN /       →  (retriever only /
 documento vs chunks,    hybrid)                 HNSW + parámetros)      cross-encoder rerank)
 chunk size, overlap)
```

Cada decisión tiene un coste. **Representar mejor también cuesta más**:

| Decisión | Efecto |
|---|---|
| **Modelo** | Modelos distintos producen geometrías y señales de relevancia distintas. |
| **Dimensionalidad** | Más dimensiones → más almacenamiento y más coste de comparación. |
| **Granularidad** | Documento completo vs. múltiples *chunks*. |
| **Número de vectores** | El *chunking* puede multiplicar considerablemente el tamaño del índice. |

**Ejemplo cotidiano:** montar una cocina de restaurante. Puedes elegir mejores ingredientes (modelo), platos
más elaborados (dimensiones), una carta enorme (chunks) o más cocineros (infraestructura). Todo mejora la
comida, pero todo cuesta, y solo sabrás qué combinación merece la pena si **mides** cuántos clientes
salen contentos y cuánto tardan en servirse.

---

## 2. El caso real: TREC-COVID

Se usa **TREC-COVID**, un *benchmark* de *Information Retrieval* construido sobre literatura científica
biomédica (distribuido por la librería **BEIR**). Tiene tres piezas con funciones distintas:

| Pieza | Qué es | En este benchmark |
|---|---|---|
| **Corpus** | Documentos con un ID estable, título y texto. | **171.332** artículos científicos. |
| **Queries** | Necesidades de información expresadas como consultas reales. | **50** consultas (p. ej. *"what is the origin of COVID-19"*). |
| **Qrels** | Para cada consulta, qué documentos fueron juzgados relevantes y **con qué grado**. | **66.336** juicios. |

La frase clave de la diapositiva:

> **Ya no tenemos que decidir "a ojo" si un resultado parece bueno. Tenemos *ground truth*.**

Detalles importantes del notebook:

- El buscador **solo utiliza corpus y consulta**. Los qrels se consultan **después** para evaluar. **No se
  guardan como metadatos en Pinecone ni se usan para fabricar embeddings** (sería hacer trampa).
- **La unidad recuperada es un documento** (título + texto). Así se comparan directamente los IDs devueltos
  con los qrels, sin tener que decidir cómo puntuar fragmentos.
- Una consulta puede tener **centenares** de documentos relevantes (en desarrollo, de media **486** por
  consulta; mínimo 111, máximo 867). No es un conjunto de preguntas con una única respuesta correcta.
- Los datos se leen de `data/trec-covid/` (se descargan si faltan) y los artefactos generados van a
  `artifacts/pinecone_v1/`.

---

## 3. La decisión que queremos tomar (y qué significa "offline")

Buscar literatura científica no es solo encontrar textos parecidos a una pregunta: el sistema debe recuperar
documentos **útiles**, **ordenarlos bien** y hacerlo con un **coste y latencia asumibles**. Un resultado puede
compartir muchas palabras con la pregunta y no responderla; otro puede aportar evidencia pertinente con
**vocabulario distinto** (el "lexical gap" de la sesión 2). Por eso hay que comparar contra juicios de
relevancia, no elegir "por la reputación del modelo".

La pregunta operativa del notebook es:

> **¿Qué configuración devuelve los mejores diez documentos para este conjunto de consultas, sin exceder
> nuestro presupuesto de latencia?**

El "diez" expresa la parte visible del ranking que nos importa; no impone cuántos candidatos recupera cada
componente antes de construirlo.

### "Offline" no significa "sin Internet"

**Evaluación offline** = usar consultas y relevancias **ya recogidas**, sin repartir tráfico entre usuarios
reales. En cada experimento se envían **las mismas consultas** a distintas configuraciones de Pinecone y se
contrastan los IDs devueltos con **los mismos juicios**. Sigue necesitando Internet y servicios externos
(OpenAI, Pinecone). Un **A/B online** posterior mediría comportamiento real de usuarios; aquí medimos
**calidad de recuperación**.

### El recorrido en cuatro momentos

1. Entender los documentos y fijar qué contará como respuesta relevante.
2. Construir una referencia léxica (BM25) en Pinecone y comprobar resultados concretos.
3. Cambiar modelo, dimensión, profundidad y combinación de señales, **manteniendo lo demás controlado**.
4. **Elegir en desarrollo, congelar la elección y comprobarla en una reserva final.**

---

## 4. El contrato de evaluación: desarrollo, reserva final y relevancia

### Dos conjuntos de consultas

La diapositiva lo resume así: `Corpus + Queries + Qrels → Evaluation`, y distingue dos usos de los datos:

| Conjunto | Para qué | En el notebook |
|---|---|---|
| **Development set** | Comparar configuraciones y ajustar decisiones. | **30** consultas |
| **Evaluation set** (reserva final / *holdout*) | Estimar el rendimiento final. | **20** consultas |

La separación es **reproducible** (semilla 42) y **aproximadamente estratificada** por número de documentos
relevantes: se agrupan las consultas en cinco tramos según su cantidad de relevantes y se reparte cada tramo
entre los dos conjuntos, para que no acaben todas las preguntas "fáciles" (o "difíciles") en el mismo grupo.
Los IDs de cada conjunto y la huella de los qrels se guardan en disco.

> **Regla de oro:** en desarrollo puedes observar fallos, comparar y elegir. En la reserva final **solo
> evalúas lo ya elegido**. Si miras sus resultados y vuelves a ajustar, deja de ser independiente. Mantener
> una semilla fija **no corrige** esa contaminación.

**Ejemplo cotidiano:** es como preparar un examen con un simulacro. El simulacro sirve para practicar y
corregir errores; el examen real solo sirve para saber cuánto sabes. Si el día del examen ves las preguntas y
luego estudias esas mismas, la nota ya no mide nada.

### Relevancia binaria vs. graduada

| Tipo | Significado | Cómo se usa aquí |
|---|---|---|
| **Binaria** | Relevante / no relevante. | Relevante = **grado > 0** (Precision, Recall, MRR, MAP). |
| **Graduada** | Distintos niveles de utilidad para una misma consulta. | **nDCG** conserva el grado original y usa **ganancia lineal**: un grado 2 aporta el doble que un grado 1 (antes del descuento por posición). |

Distribución real de juicios en desarrollo:

| Grado | Juicios |
|---|---|
| −1 | 1 |
| 0 (no relevante) | 25.132 |
| 1 (relevante) | 6.160 |
| 2 (muy relevante) | 8.426 |

(El único −1 se trata como ganancia cero: `max(0, grado)`.)

### "Sin juicio" no es lo mismo que "irrelevante"

Los qrels son **incompletos**: nadie juzgó todos los documentos para todas las consultas. Un documento sin
juicio recibe **ganancia cero** en el cálculo, **pero eso no demuestra que sea irrelevante**. Por eso el
código registra también la **fracción juzgada entre los diez primeros** (`Fracción juzgada@10`): si es baja,
las métricas pueden estar subestimando al sistema.

---

## 5. Las métricas de recuperación

### ANN Recall no es Retrieval Recall

La diapositiva insiste en distinguir dos "recall" que ya vimos por separado:

| | **ANN Recall@k** (sesión 4) | **Retrieved Recall@k** (esta sesión) |
|---|---|---|
| **Compara** | Resultados del índice aproximado vs. búsqueda exacta. | Resultados recuperados vs. **qrels**. |
| **Pregunta** | ¿Cuántos de los *vecinos exactos* consigue recuperar el índice ANN? | ¿Cuántos de los documentos *realmente relevantes* consigue recuperar el sistema? |

Un índice puede tener ANN Recall 1.0 y aun así recuperar mal si el embedding no captura la relevancia.

### No existe una única métrica

| Métrica | Pregunta que responde | Cómo se calcula (código de `evaluation/metrics.py`) |
|---|---|---|
| **Precision@10** | De los resultados recuperados, ¿cuántos son relevantes? | Relevantes en las 10 primeras posiciones / 10. |
| **Recall normalizado@k** | ¿Qué fracción de lo *recuperable con este k* hemos conseguido? | Relevantes entre los primeros k / **`min(k, relevantes conocidos)`**. |
| **MRR@10** | ¿En qué posición aparece el primer relevante? | 1/posición del primero; 0 si no aparece en las 10 primeras. |
| **nDCG@10** (**primaria**) | ¿Colocamos los documentos más relevantes en las primeras posiciones? | Ganancia descontada por posición / ganancia del orden ideal. |
| **MAP@k** | ¿Se recuperan relevantes de forma consistente a lo largo del ranking? | Media entre consultas de AP@k; AP suma precisiones en cada posición relevante y divide por **todos** los relevantes conocidos. |

La **medida primaria será nDCG@10**. Precision y MRR ayudan a interpretarla; el recall normalizado mide cuánto
aprovechamos el presupuesto de recuperación. Ninguna mide por sí sola la calidad de un sistema de
generación de respuestas.

### Por qué "recall normalizado"

Aquí **k es el máximo de documentos que pedimos**, mientras que las métricas terminadas en @10 evalúan las
diez primeras posiciones. Como una consulta puede tener 800 relevantes, un recall estándar con k=100 nunca
pasaría de 0,125. El recall normalizado divide entre `min(k, relevantes)`:

- k=100 y 400 relevantes: encontrar 100 → **1,0**.
- k=100 y 78 relevantes: encontrar los 78 → **1,0**; encontrar 39 → **0,5**.
- Sin relevantes conocidos → 0.

Cuando hay al menos k relevantes **coincide con Precision@k**; cuando hay menos, coincide con el recall
estándar. Ojo: normalizar **no hace equivalentes** los presupuestos k=20, 50 y 100 ni garantiza que la
métrica suba al ampliar k.

### Ejemplo numérico (reducido a k=5)

Una consulta con **3 relevantes conocidos** (grados 2, 1 y 1). El sistema devuelve 5 documentos: el 1.º
(grado 2), el 2.º no relevante, el 3.º (grado 1), el 4.º y 5.º no relevantes.

| Métrica | Cálculo | Resultado |
|---|---|---|
| Precision@5 | 2 relevantes / 5 | **0,40** |
| Recall normalizado@5 | 2 / min(5, 3) | **0,667** |
| MRR | primer relevante en posición 1 → 1/1 | **1,0** |
| AP@5 | (1/1 + 2/3) / 3 relevantes | **0,556** |
| nDCG@5 | DCG = 2/log₂2 + 1/log₂4 = 2,5; ideal = 2 + 1/log₂3 + 1/log₂4 ≈ 3,131 | **0,798** |

Fíjate en que **AP divide por todos los relevantes** (3), no por `min(k, relevantes)`: esa convención
importa cuando se compara con otras herramientas.

### Comprobaciones de seguridad del código

`evaluate_ranking` lanza error si el ranking tiene **documentos duplicados** o si **excede la profundidad**
declarada: un ranking mal formado no debe producir una métrica bonita en silencio.

---

## 6. Retrieval es una optimización multiobjetivo

Mejorar el sistema implica optimizar **varias propiedades que compiten entre sí**:

| Familia | Ejemplos |
|---|---|
| **Calidad** | Recall@100, nDCG@10… |
| **Rendimiento** | Latencia p50 / p95. |
| **Recursos** | Memoria, tamaño del índice. |
| **Complejidad** | Número de componentes, operación y mantenimiento. |

> **El mayor nDCG no implica automáticamente la mejor arquitectura. La mejor configuración es la que
> satisface las restricciones del sistema.**

### Cada cambio es un experimento medible

Cada configuración se registra como una fila (*run*):

| Run | Representación | Retrieval | Índice | Reranker |
|---|---|---|---|---|
| 001 | – | BM25 | – | – |
| 002 | E5 | Dense | Exact | – |
| 003 | E5 | Dense | HNSW | – |
| 004 | E5 | Hybrid | HNSW | – |
| 005 | E5 | Hybrid | HNSW | Cross-Encoder |

(Tabla de la diapositiva: cada experimento modifica **una** decisión y mide sus consecuencias, y se lleva un
registro de todos.) Sobre cada una se miden Recall@100, nDCG@10, latencia p95, memoria/tamaño del índice…

### El ciclo de mejora

```
Baseline → Hipótesis → Experimento → Evaluación → Análisis de errores → Nueva hipótesis → (Baseline…)
```

La hipótesis debe responder: **¿qué esperamos mejorar? ¿cómo sabremos si ocurrió? ¿qué coste estamos
dispuestos a aceptar?** Es el método científico aplicado a la ingeniería de búsqueda.

---

## 7. Qué se almacena en Pinecone y por qué

El objeto del experimento es una **búsqueda sobre una base vectorial gestionada**. El portátil solo prepara
representaciones, envía consultas, fusiona listas y calcula métricas. **No hay un índice HNSW, IVF o BM25
local sirviendo de sustituto de Pinecone**: la matriz local de embeddings es solo una **caché** para no pagar
ni calcular de nuevo.

Consecuencia importante: **no podemos barrer libremente `ef_search`, `M`, `nprobe` o *product quantization***
como hicimos con FAISS en la sesión 4. Aquí comparamos los controles que expone la aplicación: **modelo,
dimensiones, profundidad y estrategia de recuperación**. No hay un "mejor HNSW de Pinecone" que se pueda
inferir de estas tablas.

### Estructura en Pinecone

| Elemento | Detalle |
|---|---|
| **Un índice por dimensión** | Pinecone fija la dimensión al crear el índice: `{prefijo}-d256`, `-d512`, `-d768` (métrica coseno). |
| **Un índice *sparse*** | `{prefijo}-sparse` (producto escalar) para los pesos BM25. |
| **Un *namespace* por modelo** | Nombre `{modelo}-{huella}`. Si se activa Qwen, sus vectores quedan separados de los de OpenAI aunque tengan la misma dimensión (espacios distintos). |
| **Metadatos por registro** | ID, título, extracto, modelo y firma. **No la relevancia.** |
| **Protección** | Los índices se crean con `deletion_protection="enabled"`; el código **nunca borra**. |

La **huella** incluida en el namespace evita reutilizar silenciosamente otro corpus o preprocesamiento (es el
mismo principio de "un índice dedicado a un modelo" de la sesión 5).

### Dimensionar antes de cargar

Cada matriz densa ocupa aproximadamente **N × d × 4 bytes** (float32). Con 171.332 documentos:

| Modelo | Dimensiones | Vectores | Tamaño bruto |
|---|---|---|---|
| openai-large | 256 | 171.332 | 0,16 GiB |
| openai-large | 512 | 171.332 | 0,33 GiB |
| openai-large | 768 | 171.332 | 0,49 GiB |
| **Total** | 3 representaciones | **513.996** | **0,98 GiB** |

No son documentos nuevos, sino **tres versiones del mismo corpus**. Es un mínimo de datos numéricos, no el
almacenamiento facturado (faltan índices internos, metadatos, etc.).

⚠️ El recorrido completo **puede superar las cuotas de un plan gratuito**: el notebook no inventa una
estimación en euros; hay que revisar en tu cuenta número de índices, namespaces, almacenamiento y uso.

Inventario de configuraciones (por defecto, solo OpenAI): **3 representaciones densas, 18 configuraciones
densas/híbridas + 1 referencia léxica = 19 configuraciones**, 3 índices densos distintos y 1 sparse. Con
Qwen (`include_qwen=True`) serían 37.

---

## 8. Preparación: BM25, embeddings y caché

### El texto común

La unidad es título + texto, con un **límite común de 6.000 bytes UTF-8** al principio del texto (`prepare_text`).
No es un tamaño óptimo, sino una decisión conservadora: evita que cada proveedor recorte una cantidad
distinta. **Bytes no son tokens.** Resultado real: solo **104 documentos (0,06 %)** superan ese límite (media
1.121 bytes; percentil 95 = 2.324; máximo 122.591).

> **No cambiamos simultáneamente *chunking* y modelo:** si lo hiciéramos, una diferencia de calidad no
> tendría una explicación clara. Las conclusiones quedan condicionadas a esta representación común.

### BM25 como pesos *sparse*

Se calculan **localmente** los pesos BM25 (`SparseBM25`) y se cargan en Pinecone como vectores dispersos con
producto escalar; Pinecone hace la recuperación. Parámetros de la sesión 2 (`k1=1.2`, `b=0.75`) sin optimizar.
Tokenización: minúsculas, lista fija de palabras vacías en inglés y términos de ≥ 2 caracteres. Se ajusta con
todo el corpus **sin usar qrels**. La consulta se codifica con pesos 1,0 por término.

### Embeddings de OpenAI y Qwen (opcional)

| Modelo | Descripción |
|---|---|
| **OpenAI `text-embedding-3-large`** | Propósito general; admite reducción de dimensión. Se miden **256, 512 y 768**. |
| **Qwen `Qwen3-Embedding-0.6B`** *(opcional)* | Alternativa local (hasta 1024 dims); se elige 0.6B para contener memoria/cómputo. `include_qwen=True` añade 256/512/768 y puede descargar pesos. |

Las dos son **hipótesis, no ganadores**: se prueban, no se dan por buenas. Cada modelo recibe **sus propias
instrucciones de recuperación** (recuerda la sesión 2: consulta y documento no siempre se tratan igual), pero
el contenido documental subyacente es el mismo.

### Reducir dimensiones sin volver a facturar el corpus (Matryoshka)

Estos modelos admiten representaciones **Matryoshka**: los primeros componentes del vector son una
representación válida de menor dimensión. Se guarda **una sola matriz** por modelo y tipo de entrada; para
cada índice se conserva el **prefijo** de la dimensión elegida y se **vuelve a normalizar a longitud 1**
(`unit_vectors`). **No es PCA, no es cuantización y no es válido para cualquier modelo.**

Ojo: esto ahorra repetir llamadas del corpus, pero **no demuestra que baje el coste de inferencia**: lo que
cambia es la representación almacenada y buscada.

### Caché reanudable

`EmbeddingCache` guarda matrices `.npy`, un manifiesto (modelo, IDs y su orden, texto, formato, dimensión
original, normalización) y un fichero de progreso por lotes. Si se corta la ejecución, se recuperan los lotes
terminados (aunque acabaran fuera de orden) y se calculan los pendientes. En la ejecución guardada:
*"171.332 embeddings de documento y 50 de consulta recuperados de caché"*.

**Caché no significa cero llamadas:** `prepare_dense()` hace una prevalidación pequeña (2 documentos y 1
consulta por proveedor) y comprueba los índices **antes** de generar masivamente, para que un fallo de acceso
o capacidad aparezca pronto. Las consultas a Pinecone siguen siendo remotas y **no se cachean** (reejecutar
vuelve a consultar y consume lecturas).

### Integridad de la carga

La escritura no es instantánea (consistencia eventual, sesión 5): el helper espera el recuento esperado y
comprueba **tres registros remotos** contra su representación local. Es una comprobación de integridad
**parcial**, no una demostración de que todo esté correcto. Si vence la espera, **no se evalúa una carga
incompleta**. Reejecutar es seguro: el `upsert` es idempotente.

Resultado real: los cuatro namespaces (`bm25`, `openai-large` 256/512/768) muestran **171.332 vectores
visibles** cada uno.

---

## 9. Primer resultado: BM25 como referencia

Antes de añadir complejidad hay que saber **qué resuelve una señal léxica**. Se envían las 30 consultas de
desarrollo (hasta 50 documentos cada una) y se miden 2 repeticiones tras un calentamiento excluido:

| Configuración | nDCG@10 | Precision@10 | MRR@10 | Recall normalizado@50 | MAP@50 | p95 (ms) | RU/consulta |
|---|---|---|---|---|---|---|---|
| `bm25-d0-lexica-k50` | **0,60** | 0,64 | 0,83 | 0,55 | 0,05 | 227,9 | 1,00 |

- La **latencia** se mide desde tu equipo e incluye red, cliente y servicio (no es el tiempo interno del
  índice); en BM25 incluye codificar la consulta léxica. No se extrapola a otra región ni a concurrencia alta.
- **RU** = *read units* de Pinecone (unidades de lectura consumidas).
- Un score BM25 alto expresa compatibilidad con esa función, **no una probabilidad**; no se puede comparar un
  BM25 de 8 con un coseno de 0,7.

### Tres consultas reales, leídas a mano

El notebook inspecciona las tres primeras consultas de desarrollo para **leer** antes de medir:

| Consulta | Lo que se observa en el top-5 de BM25 |
|---|---|
| *"what is the origin of COVID-19"* | Los cinco primeros son relevantes (grados 1–2): títulos con "origin". BM25 luce en coincidencias explícitas. |
| *"has social distancing had an impact on slowing the spread of COVID-19?"* | Cuatro de cinco relevantes (grado 2); la 4.ª posición es de grado **0** (habla de distanciamiento pero no responde). |
| *"what are the guidelines for triaging patients infected with coronavirus?"* | **Ningún** resultado relevante (todos grado 0): documentos sobre pandemia/COVID en general, sin las pautas de triaje. |

Lección: la misma referencia léxica funciona muy bien en una consulta con términos distintivos y falla por
completo en otra donde solo comparte vocabulario genérico ("COVID", "pandemic").

---

## 10. El barrido de experimentos (resultados reales)

Ahora se mantienen corpus y consultas y **se cambia cómo se representa el significado**. Se cruzan modelo,
dimensión, estrategia y profundidad:

```
1 modelo × 3 dimensiones (256/512/768) × 2 estrategias (densa, híbrida) × 3 profundidades (20/50/100) = 18
+ 1 referencia BM25 (k=50)                                                                           = 19
```

Todas usan **las mismas 30 consultas y los mismos qrels**. El orden de consultas y configuraciones **se
aleatoriza** dentro del barrido para que no se mida siempre una alternativa durante un periodo de red más
lento. Fueron **1.080 evaluaciones** (30 consultas × 18 configuraciones × 2 repeticiones) en ≈ 3 min 35 s.

### Tabla real (desarrollo, ordenada por nDCG@10)

| Configuración | nDCG@10 | Precision@10 | MRR@10 |
|---|---|---|---|
| `d768-híbrida-k100` | **0,80** | 0,86 | 0,98 |
| `d512-híbrida-k100` | 0,80 | 0,85 | 1,00 |
| `d256-híbrida-k100` | 0,79 | 0,85 | 1,00 |
| `d768-híbrida-k50` | 0,78 | 0,83 | 0,98 |
| `d512-híbrida-k50` | 0,78 | 0,81 | 1,00 |
| `d256-híbrida-k50` | 0,77 | 0,81 | 1,00 |
| `d768-densa-k20/50/100` | 0,76 | 0,81 | 0,92 |
| `d512-densa-k20/50/100` | 0,75 | 0,79 | 0,95 |
| `d768-híbrida-k20` | 0,74 | 0,78 | 0,94 |
| `d512-híbrida-k20` | 0,74 | 0,77 | 0,96 |
| `d256-híbrida-k20` | 0,73 | 0,76 | 1,00 |
| `d256-densa-k20/50/100` | 0,73 | 0,76 | 0,93 |
| `bm25-d0-lexica-k50` | **0,60** | 0,64 | 0,83 |

(Para la mejor fila: Recall normalizado@100 = 0,60; MAP = 0,11; p95 ≈ 318 ms; 2,0 RU por consulta —el doble
que BM25 porque la híbrida hace dos búsquedas—.)

### Cómo leer la tabla (con cautela)

- **Todas las variantes de embeddings superan claramente a BM25** en este corpus (0,73–0,80 frente a 0,60).
  Recuerda la sesión 2: el *lexical gap* pesa mucho en literatura científica con vocabulario variado.
- **La híbrida supera a la densa** cuando hay suficientes candidatos (k=50 o 100): 0,77–0,80 frente a
  0,73–0,76 (p. ej. 768 dims: 0,80 frente a 0,76). Con **k=20 la híbrida no ayuda** (0,73–0,74; incluso queda
  un poco por debajo de la densa en 768 y 512 dims): con pocos candidatos por rama la fusión tiene poco material.
- **La dimensión importa poco:** de 256 a 768 dimensiones el nDCG@10 sube entre 0,01 (híbrida k=50/100) y
  0,03 (densa). Reducir de 768 a 256 ahorra un 67 % de almacenamiento a cambio de 1–3 puntos de calidad:
  exactamente el tipo de *trade-off* que hay que decidir con una regla explícita (sección 12).
- **En la densa, la profundidad no cambia nDCG@10:** k=20, 50 y 100 dan el mismo valor. Es lógico: nDCG@10
  solo mira las 10 primeras posiciones y las 10 primeras de un top-100 son las de un top-20.
- Son **diferencias observadas en desarrollo con 30 consultas**: aún no sabemos si son estables. Para eso
  existe la reserva final (sección 14).

### Las cuatro comparaciones controladas

Para atribuir cada diferencia a **un** cambio, el notebook hace comparaciones donde solo varía un factor:

| Efecto | Qué varía | Se mantiene |
|---|---|---|
| **Modelo** | OpenAI vs. Qwen (solo si está habilitado) | 768 dims, densa, k=50 |
| **Dimensión** | 256 / 512 / 768 | Mismo modelo, estrategia y profundidad |
| **Combinar señales** | Densa vs. híbrida | Mismo modelo, dimensión y profundidad por rama |
| **Profundidad** | 20 / 50 / 100 | Misma configuración |

Con solo OpenAI **no hay comparación entre modelos**. Estas comparaciones describen efectos **bajo esas
condiciones**, no causalidad universal: modelo y dimensión pueden interactuar (un modelo puede tolerar mejor
la reducción que otro), por eso se conserva el cruce completo.

### Dos latencias que no se deben mezclar

- **En el barrido**, el embedding de cada consulta está **precalculado**: el p95 mide búsqueda + fusión, **no
  incluye llamada nueva al proveedor de embeddings**.
- **En la reserva final** sí se pide el embedding **en vivo** (ruta completa).

No se mezclan bajo la misma etiqueta.

---

## 11. Búsqueda híbrida y Reciprocal Rank Fusion

La **búsqueda densa** devuelve documentos cercanos en el espacio del modelo; la **léxica**, documentos con
términos coincidentes ponderados por BM25. La **híbrida** pide *k* candidatos a cada rama, elimina duplicados
al combinar IDs y devuelve como máximo *k* documentos. La fusión usa **RRF** (sesión 3):

$$\operatorname{RRF}(d)=\sum_{r} \frac{1}{60+\operatorname{posición}_r(d)}$$

```python
def reciprocal_rank_fusion(rankings, limit, constant=60):
    scores = {}
    for ranking in rankings:
        for position, (doc_id, _) in enumerate(ranking, 1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (constant + position)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
```

- Un documento en 3.er lugar en **ambas** listas recibe `1/63 + 1/63 ≈ 0,0317`; uno que aparece 1.º en **una
  sola** recibe `1/61 ≈ 0,0164`. RRF **premia el acuerdo** sin sumar scores de escalas distintas.
- **El 60 es una constante fijada, no un óptimo demostrado** (y no es "otro nombre para k").
- El desempate final es por ID, para que el resultado sea determinista.

Puntos de honestidad sobre el coste:

- **Igual k por rama no significa igual trabajo:** con k=50 la híbrida puede examinar hasta **100 IDs
  distintos** antes de devolver 50. El registro conserva el tamaño de esa unión (`candidate_union`) y las
  unidades de lectura (RU) de Pinecone. La calidad se compara **con el coste observado**.
- Las dos consultas se ejecutan **secuencialmente**: la latencia híbrida incluye ambas búsquedas más la
  fusión. Paralelizarlas sería otro cambio de ingeniería que habría que volver a medir.
- **No hay reranker** escondido: "ranking final" es el orden denso o el orden RRF, no un cross-encoder.
- Aumentar k **no crea documentos ni cambia el namespace**; cambia la petición. En cambio, cambiar modelo o
  dimensión exige seleccionar otra representación.

---

## 12. Elegir sin perseguir la última milésima

Una mejora pequeña de calidad puede exigir duplicar almacenamiento o hacer una segunda búsqueda. La elección
debe **expresar prioridades**, no esconderlas tras una puntuación agregada arbitraria. La regla se fija **al
comienzo**, antes de mirar resultados:

```
1. Descartar configuraciones con p95 de búsqueda > 1.500 ms      (presupuesto de latencia)
2. Conservar las que estén a ≤ 0,01 de nDCG@10 de la mejor       (tolerancia de calidad)
3. Entre ellas, elegir la de menos bytes brutos de representación
4. Después, la de menor latencia
```

```python
eligible = frame[frame["p95 (ms)"] <= config.latency_budget_ms]
best = eligible["nDCG@10"].max()
shortlist = eligible[eligible["nDCG@10"] >= best - config.quality_tolerance]
chosen = shortlist.sort_values(["Vectores brutos (GiB)", "p95 (ms)", "Experimento"]).iloc[0]
```

Matices:

- **La tolerancia 0,01 no es un intervalo estadístico:** es una **preferencia operativa declarada**.
- Los bytes incluyen la representación *sparse* si la estrategia la necesita en producción (híbrida), pero
  **no** las configuraciones descartadas: no se penaliza a un candidato por guardar otros modelos para
  investigarlos. Tampoco se mide la memoria interna de Pinecone.
- **Si ninguna configuración cumple el presupuesto, el código no inventa un ganador**: lanza un error
  ("No hay ganador viable"). Y **si la seleccionada es la propia referencia densa, también es un resultado
  válido**: añadir complejidad no es una obligación.
- El recall normalizado se mantiene visible como contrapartida, pero sus valores a k=20 y k=100 corresponden
  a presupuestos distintos y no significan la misma cobertura.

### Congelar la decisión

La elección sigue siendo **provisional** (se hizo con desarrollo y con latencia sin embedding en vivo). Antes
de abrir la reserva final, `freeze_decision` guarda en `frozen_decision.json`: referencia, candidato,
consultas de desarrollo y reserva, huellas del corpus, configuración completa y ubicación remota (índices y
namespaces). **Si ya existe una decisión distinta, se bloquea su sustitución:**

> "Ya hay otra decisión congelada. No reutilice la reserva final para retocar el ganador; use otro
> directorio de artefactos y declare la nueva evaluación como exploratoria."

Es una barrera técnica contra la tentación de ajustar después de ver la reserva.

---

## 13. Leer un error antes de culpar al modelo

Tras elegir, se revisan **dos casos de desarrollo**: la **mayor regresión** y la **mayor mejora** de nDCG@10 del
candidato frente a la referencia. Son casos **extremos escogidos a propósito** para diagnosticar, no una
muestra representativa. Cada uno muestra A y B junto a los juicios reales.

Antes de concluir "el modelo es peor", hay que comprobar **qué cambió**:

- ¿Se **perdió** un documento relevante?
- ¿Descendió **varias posiciones**?
- ¿Aparecieron documentos **sin juzgar** (que no necesariamente son malos)?

Las tres situaciones bajan una métrica, pero significan cosas distintas. Además:

- Compara el contenido con la **intención** de la pregunta: una coincidencia superficial (enfermedad + órgano)
  no garantiza que el documento estudie la relación pedida. Busca entidades poco frecuentes, negaciones y
  vocabulario especializado.
- Son **hipótesis** que deben respaldarse leyendo el documento, no etiquetas que el código infiera de un score.
- El extracto es corto a propósito: consulta `corpus[document_id]["text"]` y contrasta cuánto quedó dentro de
  los 6.000 bytes. **Si el pasaje pertinente quedó fuera del límite, un modelo más grande no puede recuperar
  información que no recibió.**
- **No se corrige el pipeline con casos de la reserva.** Para una nueva investigación (otro modelo, *chunking*,
  reranker, fusión ponderada) hay que formular una hipótesis y disponer de validación independiente: los 50
  temas no son una fuente infinita de confirmaciones.

---

## 14. La reserva final: ¿la mejora se sostiene?

Se evalúan **solo las configuraciones ya elegidas** —la referencia densa, BM25 y el candidato congelado (si dos
coinciden, se ejecuta una vez)— sobre las **20 consultas no usadas** para elegir, con `fresh_embedding=True`:
el embedding de la consulta se pide **en vivo** al proveedor.

```python
final_results = run_experiments(lab, finalists, holdout_ids, qrels, config,
                                split="holdout", fresh_embedding=True)
```

- La latencia incluye ahora **representación de consulta + red + búsqueda + fusión**: es la más parecida a
  producción (con servicio "caliente"; los pesos locales de Qwen ya están cargados).
- La **calidad** se calcula sobre la **primera respuesta** de cada consulta; las repeticiones sirven para medir
  tiempos y **no** cuentan como observaciones estadísticas nuevas. **Tener 40 tiempos de 20 consultas no
  equivale a 40 necesidades de información independientes.**

### Bootstrap pareado

`final_report` calcula, para cada consulta de la reserva, la **diferencia de nDCG@10 (candidato − referencia)**
y remuestrea **pares de resultados de las mismas consultas** (3.000 réplicas) para obtener un **intervalo
bootstrap del 95 %** de la diferencia media:

```python
delta = (b - a).to_numpy()                        # una diferencia por consulta
samples = delta[rng.integers(0, len(delta), (3000, len(delta)))].mean(axis=1)
IC95 = (np.quantile(samples, .025), np.quantile(samples, .975))
```

**Se mantienen los pares** porque unas preguntas son más difíciles que otras *para ambos sistemas*.

| Resultado del IC95 | Interpretación (del código) |
|---|---|
| Todo por **encima de 0** | "La reserva aporta evidencia de mejora media de nDCG@10 para B en este conjunto." |
| Todo por **debajo de 0** | "B empeora nDCG@10 en la reserva; no se recomienda sustituir A basándose en desarrollo." |
| **Contiene 0** | "La diferencia no es concluyente con estas consultas: el intervalo incluye cero." |
| Candidato = referencia | "La selección conserva la referencia; no existe una mejora A/B que afirmar." |

Un intervalo que contiene cero **no demuestra equivalencia**: con veinte consultas puede faltar precisión.
Tampoco se convierte una mejora estadística diminuta en ventaja de negocio: hay que contrastar magnitud,
fallos concretos, latencia y coste. Y **si la latencia completa incumple el presupuesto, la selección de
búsqueda no basta para aprobar el pipeline**.

Los ficheros exportados (`frozen_decision.json`, `final_report.json`, rankings por ID, métricas por consulta,
tiempos individuales, versiones instaladas, referencias a namespaces) permiten **auditar** la conclusión.

> ⚠️ **Nota sobre este notebook:** las salidas guardadas en el fichero llegan solo hasta el **barrido de
> desarrollo**. Las celdas de las comparaciones controladas, la selección del candidato, el análisis de
> errores, la reserva final y el informe **no tienen salida guardada** en este notebook. El resultado se conoce
> por la [sesión 7](../07-RAG/EXPLICACION_sesion_07.md), que lo hereda: la configuración congelada fue **OpenAI,
> 256 dimensiones, híbrida, 100 candidatos por rama**, y la reserva final dio **nDCG@10 ≈ 0,791 para el
> candidato frente a ≈ 0,773 para la referencia**, con un **intervalo de la diferencia que incluía el cero**
> (mejora observada, sin evidencia estadística concluyente). Para ver las tablas completas hay que ejecutar esas
> celdas (con costes reales).

---

## 15. Qué falta antes de producción

El informe final sustenta la decisión de **esa ejecución**; el notebook no declara un ganador fijo. Conviene
distinguir tres afirmaciones que **no son intercambiables**:

1. "Esta configuración obtiene mayor nDCG."
2. "La diferencia se sostiene en la reserva."
3. "El pipeline completo cumple el presupuesto."

### Límites de la conclusión

La recomendación queda limitada a **TREC-COVID, sus consultas, sus juicios incompletos, el recorte documental
elegido y este entorno de acceso a Pinecone**. No demuestra calidad de respuestas RAG, factualidad de un
generador ni satisfacción de usuarios reales. Añadir reranking o generación exigiría medir las etapas nuevas
y no atribuirles resultados de este experimento.

### Para trasladarlo a una aplicación

- **Conservar el contrato de representación:** modelo, dimensión, instrucciones, normalización y
  preprocesamiento. Cambiar de embedding obliga a reconstruir la colección y a usar la **misma versión en las
  consultas** (¡la migración de la sesión 5!).
- **Almacenamiento, RU y latencia son señales distintas.** La factura depende de condiciones comerciales y del
  uso total, incluidos preparación, escrituras, almacenamiento mantenido y llamadas a embeddings. **Las RU
  ausentes se guardan como "dato no disponible", no como coste cero**, y la preparación se paga aunque luego se
  descarte una configuración.
- **A/B online:** habría que definir asignación de tráfico, una métrica de éxito de uso y salvaguardas de
  latencia, errores y coste.
- **Vigilar:** cambios en el vocabulario de consultas, distribución de scores, búsquedas vacías y documentos
  sin cubrir. Las puntuaciones **no son probabilidades calibradas** y cambian al sustituir el modelo: no se
  heredan umbrales sin revalidarlos.

### Cierre de recursos y continuidad

- Los índices tienen **protección contra borrado** y el notebook **no elimina** recursos, namespaces ni
  cachés al terminar. **Los recursos que quedan activos pueden seguir generando costes**: contrasta el
  inventario con la decisión congelada en la consola de Pinecone y decide qué conservar.
- Si se interrumpe la generación de embeddings, la caché recupera los lotes hechos. Si se interrumpe una
  carga, la reejecución reenvía IDs de forma idempotente (no duplica; puede repetir escrituras).
- **Un timeout o un error de autenticación no debe convertirse en una fila de métricas a cero.** Un
  experimento *fallido* no es un experimento *con baja calidad*.

---

## 16. Arquitectura del laboratorio (`src/retrieval_lab/`)

El código repetitivo vive en un paquete organizado **por dominio** (no por tipo de archivo); el notebook
concentra decisiones e interpretaciones y llama a este paquete. Se describe con detalle en
[`src/README.md`](./src/README.md) y en [`src/retrieval_lab/CLAUDE.md`](./src/retrieval_lab/CLAUDE.md).

| Subpaquete | Responsabilidad |
|---|---|
| `configuration/` | `ExperimentConfig` (parámetros validados), modelos (`ModelSpec`), carga explícita del `.env`. |
| `data/` | Lectura y validación de TREC-COVID; preparación común del texto. |
| `representations/` | Adaptadores de embeddings (OpenAI, Gemini, Qwen), caché reanudable, prefijo Matryoshka + normalización, BM25. |
| `storage/` | Índices, namespaces, subidas, verificación, inventario y consultas en Pinecone. |
| `retrieval/` | Preparación remota; recuperación léxica, densa e híbrida; fusión RRF; `RetrievalLab` (fachada). |
| `evaluation/` | Diseño experimental (brazos, *split*), métricas, bootstrap, ejecución y selección/congelado. |
| `reporting/` | Tablas, gráficos, ejemplos y conclusiones para el notebook. |
| `infrastructure/` | Huellas y escritura atómica, concurrencia acotada, cuotas (RPM/TPM) y reintentos. |

Ideas de diseño que conviene fijar:

- **Un experimento es un `Arm(modelo, dimensión, estrategia, profundidad)`** con un nombre determinista
  (`openai-large-d768-hibrida-k100`), lo que hace las tablas legibles y las mediciones reproducibles.
- **Separar motivos de cambio:** `metrics.py` define las fórmulas, `runner.py` ejecuta y agrega,
  `selection.py` aplica los criterios y congela la decisión. Métricas, estadística, ejecución y selección
  **no dependen de Jupyter ni de matplotlib**.
- **Huellas (`fingerprint`) por todas partes:** cachés, namespaces y carpetas de resultados se identifican por
  el contenido (SHA-256 de un JSON canónico). Si cambian textos, modelo o protocolo, cambia la huella y
  **no se reutiliza en silencio** algo incompatible.
- **Robustez operativa:** reintentos con *backoff* y respeto de `Retry-After`, límites de cuota configurables,
  cancelación cooperativa de hilos y escritura atómica de JSON.

---

## 17. Resumen final

1. Un sistema de recuperación real **conecta decisiones** de representación, retrieval, arquitectura y
   evaluación; ninguna se optimiza por separado.
2. **TREC-COVID** aporta *ground truth* (corpus + queries + qrels): dejamos de juzgar "a ojo". Los qrels solo
   se usan para evaluar, **nunca** para construir el índice.
3. **Offline** no significa sin Internet ni sin coste: significa consultas y juicios ya recogidos, no tráfico
   real. No sustituye a un A/B online.
4. Se separan **desarrollo (30)** y **reserva final (20)**. Tocar la reserva para ajustar la contamina;
   la semilla fija no lo arregla.
5. **"Sin juicio" ≠ "irrelevante".** Hay que registrar la fracción juzgada.
6. No hay una métrica única: **nDCG@10** (primaria), Precision@10, MRR@10, **Recall normalizado@k**
   (`min(k, relevantes)`) y MAP@k, cada una con su pregunta. **ANN Recall ≠ Retrieval Recall.**
7. Retrieval es **multiobjetivo** (calidad, latencia, recursos, complejidad): la mejor configuración es la
   que satisface las restricciones, no la de mayor nDCG.
8. Con Pinecone gestionado no se barren `ef_search`/`nprobe`; se comparan **modelo, dimensión, profundidad y
   estrategia**. Un índice por dimensión, un índice sparse y namespaces con huella.
9. En el barrido real: **embeddings ≫ BM25** (0,73–0,80 frente a 0,60 de nDCG@10), la **híbrida supera a la
   densa con k ≥ 50**, y **256 dimensiones cuestan solo 1–3 puntos** de nDCG@10 frente a 768 con un 67 % menos de bytes.
10. **RRF** (`1/(60+posición)`) combina rankings sin calibrar scores; igual k por rama **no** es igual trabajo
    (la unión puede duplicar los candidatos).
11. La elección sigue una **regla predefinida** (latencia → tolerancia de calidad → menos bytes → menos
    latencia) y se **congela** antes de abrir la reserva.
12. La reserva se evalúa con **embedding en vivo** y un **bootstrap pareado** del IC95 de la diferencia de
    nDCG@10; si el intervalo contiene cero, **no hay conclusión**, y eso tampoco es equivalencia.
13. Un error hay que **leerlo** antes de culpar al modelo: quizá el pasaje relevante quedó fuera del recorte.
14. Antes de producción: contrato de representación, coste real (RU/facturación), A/B online, monitorización
    y gestión de recursos remotos (que no se borran solos).

---

## 18. ¿Qué sigue después?

La frase que resume la sesión es:

> **Evaluar antes de optimizar: cada cambio es un experimento medible, con una hipótesis, una métrica y un
> coste declarados de antemano.**

El hilo del tema hasta aquí: sesiones 1–3, **representar y comparar**; sesión 4, **indexar para buscar
rápido**; sesión 5, **almacenar, filtrar y operar**; sesión 6, **construir y evaluar el sistema completo**.
Falta la pieza final, que es la que el usuario percibe: usar los fragmentos recuperados para que un modelo de
lenguaje **genere una respuesta**. Eso es la sesión 7, **Retrieval-Augmented Generation**
([`07-RAG`](../07-RAG/)), donde lo aprendido aquí se convierte en la base de medir, además del retrieval, la
calidad de la respuesta generada.

```
representar → indexar → almacenar → recuperar → evaluar → generar (RAG)
```

### Lecturas adicionales de esta carpeta

En [`Lecturas adicionales/`](./Lecturas%20adicionales/) hay cinco artículos sobre bases de datos vectoriales:
*Survey of Vector Database Management Systems* (Pan, Wang & Li), *Vector Database Management Systems:
Fundamental Concepts, Use-Cases, and Current Challenges* (Taipalus), *Milvus: A Purpose-Built Vector Data
Management System* (Wang et al.), *FreshDiskANN* (Singh et al., índices con actualizaciones en streaming) y
*Filtered-DiskANN* (Gollapudi et al., búsqueda con filtros), que profundizan en los temas de las sesiones 5 y 6.

### Preguntas para repasar

1. ¿Por qué el ANN Recall de la sesión 4 no es lo mismo que el Recall@k de esta sesión? ¿Puede un índice tener
   ANN Recall 1.0 y mala calidad de recuperación?
2. ¿Por qué se reservan 20 consultas que no se usan para elegir? ¿Qué pasaría si, tras ver los resultados de la
   reserva, cambiaras el modelo elegido?
3. Una consulta tiene 800 documentos relevantes y pides k=100. ¿Qué vale el recall normalizado si encuentras 60?
   ¿Y el recall estándar? ¿Por qué se prefiere el primero aquí?
4. Calcula Precision@5, MRR y AP@5 de un ranking con relevantes en las posiciones 2 y 4 y 3 relevantes
   conocidos.
5. ¿Qué significa que un documento "no tiene juicio"? ¿Cómo puede sesgar la evaluación y qué métrica ayuda a
   detectarlo?
6. En la tabla de resultados, `d256-híbrida-k100` obtiene 0,79 de nDCG@10 frente a 0,80 de `d768-híbrida-k100`
   con un 67 % menos de almacenamiento denso. Con la regla del notebook (tolerancia 0,01), ¿puede entrar en la
   lista de candidatos? ¿Y `d256-densa`? ¿Qué cambiaría si la tolerancia fuera 0,05?
7. ¿Por qué con k=20 la híbrida no mejora a la densa (incluso la iguala o empeora), y con k=50 o 100 sí? ¿Y por qué en la densa cambiar k no
   modifica nDCG@10?
8. La latencia del barrido y la de la reserva final no son comparables. ¿Qué incluye cada una y por qué
   importa?
9. El bootstrap da un IC95 de la diferencia de nDCG@10 igual a [−0,02; +0,06]. ¿Qué concluyes? ¿Puedes decir
   que las dos configuraciones son equivalentes?
10. Un colega propone cambiar a la vez el modelo de embeddings y el tamaño de los *chunks* "para ahorrar
    tiempo". ¿Qué problema de interpretación tiene esa propuesta?
11. ¿Qué información necesitarías, además del nDCG, antes de llevar la configuración ganadora a producción?
