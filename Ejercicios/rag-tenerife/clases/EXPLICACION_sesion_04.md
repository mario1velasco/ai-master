# Guía de estudio — Sesión 4: Indexación y búsqueda vectorial eficiente (Exact, HNSW, IVF, IVF-PQ)

> Esta guía explica, con lenguaje sencillo y muchos ejemplos, el contenido de
> [`indexacion_busqueda_vectorial_eficiente.ipynb`](./indexacion_busqueda_vectorial_eficiente.ipynb), de las
> diapositivas
> [`T5-S4 Sistemas de recuperación de la información, RAG y Langchain.pdf`](../pdfs/T5-S4%20Sistemas%20de%20recuperación%20de%20la%20información,%20RAG%20y%20Langchain.pdf)
> y del entorno descrito en [`README.md`](./README.md).
>
> Es la continuación directa de las tres sesiones anteriores — si no las has leído, échales un vistazo
> primero: [sesión 1 (vectores)](../01-vectores/EXPLICACION_sesion_1.md),
> [sesión 2 (sparse vs dense)](../02-sistemas-recuper-info/EXPLICACION_sesion_02.md) y
> [sesión 3 (hybrid, reranking, ColBERT)](../03-recuper-info-2/EXPLICACION_sesion_03.md). Allí aprendimos
> a **convertir texto en vectores** y a **compararlos** (coseno, producto escalar). Aquí respondemos a la
> pregunta que queda pendiente: **¿qué pasa cuando hay millones de vectores y no podemos compararlos todos
> con cada consulta?**

## Índice

1. [El problema: de la búsqueda exacta al problema de escala](#1-el-problema-de-la-búsqueda-exacta-al-problema-de-escala)
2. [¿Necesitamos realmente el vecino exacto? (ANN)](#2-necesitamos-realmente-el-vecino-exacto-ann)
3. [Recall@k y el trade-off recall vs. latencia](#3-recallk-y-el-trade-off-recall-vs-latencia)
4. [Entorno y configuración del notebook](#4-entorno-y-configuración-del-notebook)
5. [El corpus real: AG News como `Document` de LangChain](#5-el-corpus-real-ag-news-como-document-de-langchain)
6. [Embeddings con Model2Vec](#6-embeddings-con-model2vec)
7. [Un mismo contrato LangChain para índices distintos](#7-un-mismo-contrato-langchain-para-índices-distintos)
8. [Baseline exacto: `IndexFlatIP`](#8-baseline-exacto-indexflatip)
9. [HNSW: navegar un grafo de vecinos](#9-hnsw-navegar-un-grafo-de-vecinos)
10. [IVF: dividir el espacio antes de buscar](#10-ivf-dividir-el-espacio-antes-de-buscar)
11. [Product Quantization e IVF-PQ: comprimir los vectores](#11-product-quantization-e-ivf-pq-comprimir-los-vectores)
12. [Recuperación idiomática con LangChain (`as_retriever`)](#12-recuperación-idiomática-con-langchain-as_retriever)
13. [Comparación final y decisiones de diseño](#13-comparación-final-y-decisiones-de-diseño)
14. [Resumen final](#14-resumen-final)
15. [¿Qué sigue después?](#15-qué-sigue-después)

---

## 1. El problema: de la búsqueda exacta al problema de escala

### Repaso: buscar el vecino más cercano

Dada una consulta representada por un vector **q**, queremos encontrar dentro de una colección los
elementos cuyo vector sea **más próximo** según una función de distancia o de similitud (justo lo que vimos
en la sesión 1):

$$NN(q)=\arg\min_{x\in X} d(q,x) \qquad\text{o bien}\qquad NN(q)=\arg\max_{x\in X} \operatorname{sim}(q,x)$$

- Si usamos una **distancia**, buscamos la menor.
- Si usamos una **similitud** (coseno, producto escalar), buscamos la mayor.

En recuperación de información casi nunca queremos *un único* vecino, sino los **k mejor posicionados**:
es el **Top-k Nearest Neighbors** (`k=10`, por ejemplo).

### Exact search: comparar contra todo

La estrategia más directa (la que usamos hasta ahora) es:

```
q  →  {x₁, x₂, …, x_N}  →  {s₁, s₂, …, s_N}  →  Top-k
      (todos los vectores)   (una puntuación por vector)
```

Calcular la similitud de la consulta con **cada** vector de la colección, ordenar y quedarse con los
mejores. Es lo que en el notebook hace `IndexFlatIP` ("Flat" = plano, sin estructura; "IP" = *inner
product*, producto escalar).

| Ventaja | Explicación |
|---|---|
| **Exactitud** | Garantiza encontrar los verdaderos vecinos más cercanos según la métrica elegida. |
| **Simplicidad** | No hace falta construir ninguna estructura de búsqueda adicional. |

| Inconveniente | Explicación |
|---|---|
| **Coste** | Cada consulta necesita evaluar **todos** los candidatos. |

Para una colección de **N** vectores de dimensión **d**, una búsqueda exhaustiva cuesta aproximadamente:

$$O(N \cdot d)$$

### El problema no es la fórmula: es cuántas veces la ejecutamos

Calcular la similitud entre dos vectores es barato. El problema aparece cuando hay que **repetir esa
operación millones (o miles de millones) de veces por cada consulta**. La diapositiva lo resume con una
tabla (número de componentes que hay que multiplicar por consulta):

| | 1.000 vectores | 1 millón de vectores | 1.000 millones de vectores |
|---|---|---|---|
| **768 dimensiones** | 768.000 | 768 millones | 768.000 millones |
| **1.536 dimensiones** | 1,5 millones | 1.536 millones | 1,5 billones |

**Ejemplo cotidiano:** imagina que buscas un libro en una biblioteca pequeña de 1.000 libros: puedes
mirarlos todos uno por uno en unos minutos. Con 1.000 millones de libros, "mirarlos todos" deja de ser una
opción, por muy rápido que seas comparando títulos. No hace falta un mejor "comparador": hace falta **no
tener que comparar con todos**.

> **Nota del notebook:** las instrucciones SIMD y las operaciones vectorizadas (lo que hace FAISS por
> dentro) reducen las *constantes* del cálculo, pero **no eliminan el crecimiento lineal** con N. Si
> duplicas el corpus, la búsqueda exacta tarda aproximadamente el doble.

---

## 2. ¿Necesitamos realmente el vecino exacto? (ANN)

En muchos sistemas de recuperación, encontrar siempre el vecino *matemáticamente óptimo* es menos
importante que **responder mucho más rápido con resultados prácticamente equivalentes**. Piensa en RAG:
si el 9.º y el 10.º documento intercambian posiciones, o si el 10.º es "casi igual de bueno" que el que
se ha perdido, el usuario ni lo nota.

| | Exact Search | Approximate Search (ANN) |
|---|---|---|
| **Qué hace** | Examina toda la colección | Explora solo una parte prometedora del espacio |
| **Ventaja** | Máxima exactitud | Respuesta mucho más rápida |
| **Inconveniente** | Mayor coste por consulta | Posibilidad de perder algún vecino real |

**ANN** significa *Approximate Nearest Neighbors* (vecinos más cercanos aproximados). Un algoritmo ANN
construye (o usa) una estructura que permite **descartar grandes regiones** de la colección y concentrar
la búsqueda en los candidatos con mayor probabilidad de estar cerca de la consulta.

> **Idea clave de la diapositiva:** *ANN no aproxima la similitud: aproxima la búsqueda de los vecinos.*
> Sobre los candidatos que sí se inspeccionan puedes seguir calculando coseno o producto escalar de forma
> exacta; lo que te ahorras es compararlos **con todos**.

### "Aproximado" no significa "aleatorio"

Los algoritmos ANN **no eligen candidatos al azar**. Utilizan una estructura construida a partir de la
geometría de los datos. El proceso siempre tiene tres pasos:

1. **Indexar:** analizar previamente la colección y construir una estructura auxiliar.
2. **Navegar:** usar esa estructura para dirigir la consulta hacia regiones prometedoras.
3. **Verificar:** comparar la consulta con un conjunto reducido de candidatos y quedarse con los mejores.

Es decir, **desplazamos parte del coste desde el momento de la consulta hacia una fase previa de
construcción del índice**:

> **Más trabajo offline → menos trabajo por consulta.**

**Ejemplo cotidiano:** es como ordenar una biblioteca por secciones antes de abrirla al público. Ordenar
lleva mucho trabajo (una sola vez, por la noche), pero después cada visitante encuentra su libro en
segundos sin recorrer todas las estanterías.

---

## 3. Recall@k y el trade-off recall vs. latencia

### ¿Cuánto perdemos al aproximar?

Podemos medirlo comparando los resultados del índice aproximado con los de la búsqueda exacta (que actúa
como "verdad de referencia"):

$$\operatorname{Recall@k}=\frac{|\operatorname{TopK}_{ANN}\cap \operatorname{TopK}_{Exact}|}{k}$$

Ejemplo de la diapositiva:

```
Exact Top-5:  A  B  C  D  E
ANN   Top-5:  A  B  C  E  F        →  Recall@5 = 4 / 5 = 0.8
```

El ANN encontró 4 de los 5 vecinos exactos (perdió D y colocó F en su lugar).

- `Recall@k = 1` → recuperamos **todos** los vecinos exactos del top-k.
- `Recall@k < 1` → alguno de los vecinos exactos **se ha perdido**.

```python
def recall_at_k(approximate_ids, exact_ids, k=TOP_K):
    return len(set(approximate_ids[:k]) & set(exact_ids[:k])) / k
```

Fíjate en que compara **conjuntos de identificadores**: no importa el orden dentro del top-k, solo *qué*
documentos aparecen.

⚠️ **Matiz importante que señala el notebook:** este Recall@k mide cuánto se parece el índice al ranking
**exacto de esos mismos embeddings**. No mide si los resultados son *semánticamente relevantes* para una
persona (eso dependería del modelo de embeddings y de juicios humanos, como vimos en la sesión 2). Un índice
ANN puede tener recall 1.0 y aun así devolver malos resultados si el embedding es malo.

### El trade-off fundamental

Los índices ANN suelen permitir **controlar cuánto esfuerzo dedicamos a cada búsqueda**:

- **Más exploración** → ↑ candidatos evaluados, ↑ latencia, ↑ Recall@k.
- **Menos exploración** → ↓ candidatos evaluados, ↓ latencia, ↓ Recall@k.

La curva de la diapositiva tiene forma de "codo": al principio, explorar un poco más sube mucho el recall;
después, cada mejora cuesta muchísimo más. Por eso **no buscamos maximizar Recall@k a cualquier precio**: el
objetivo práctico es encontrar un **punto de operación** con calidad suficiente dentro de los requisitos de
latencia y coste del sistema.

> **ANN es un problema de compromiso, no simplemente de velocidad.**

---

## 4. Entorno y configuración del notebook

El [`README.md`](./README.md) del directorio explica cómo montar un entorno autocontenido en Windows, macOS
y Linux. Lo esencial:

- **Python 3.11 obligatorio**: es la versión con paquetes precompilados compatibles de FAISS en los tres
  sistemas. La primera celda del notebook lo comprueba y lanza un error si el kernel usa otra versión.
- **No requiere claves de API, GPU ni PyTorch**: los embeddings se generan en local (sección 6).
- **`requirements.txt`** fija versiones (`faiss-cpu==1.12.0`, `model2vec==0.9.0`, `numpy==2.1.3`,
  `datasets==3.5.0`…) y acota LangChain (`langchain-core>=1.0,<2`, `langchain-community>=0.4,<1`) para
  evitar cambios de API.
- **`verificar_entorno.py`** importa las librerías clave y crea un pequeño `IndexHNSWFlat` como prueba de
  humo.
- **`INICIAR_LINUX.sh`** instala `uv`, descarga Python 3.11, crea `.venv`, instala dependencias, verifica el
  entorno y abre JupyterLab.
- Necesita unos **3 GB** libres (entorno + dataset + modelo + cachés) y conexión a Internet en la primera
  ejecución.

### Parámetros del notebook

```python
SEED = 42                 # reproducibilidad (muestreo y entrenamiento de PQ)
MAX_DOCUMENTS = 50_000    # tamaño del corpus (10_000 para probar rápido; hasta 120_000)
EMBEDDING_MODEL = "minishlab/potion-retrieval-32M"
TOP_K = 10                # k del Recall@k y de las búsquedas
BENCHMARK_REPETITIONS = 7 # cada benchmark se repite 7 veces y se toma la mediana
```

**¿Por qué `MAX_DOCUMENTS = 50_000`?** Porque es lo bastante grande para que las diferencias de latencia
sean visibles, y lo bastante pequeño para ejecutarse en un portátil. Cambiar el modelo, el número de
documentos o la semilla genera una caché de embeddings distinta.

---

## 5. El corpus real: AG News como `Document` de LangChain

En vez de un corpus de juguete, el notebook usa **AG News**: titulares y descripciones de noticias en
inglés de cuatro áreas — `World`, `Sports`, `Business` y `Sci/Tech`. Es un buen banco de pruebas porque:

- sus consultas son **fáciles de interpretar** (una noticia de deportes es claramente de deportes);
- tiene escala suficiente para que se note el trabajo que ahorra un índice ANN;
- se baraja con `seed=42` y se toman las primeras 50.000 noticias, así que es reproducible.

Cada noticia se convierte en un `Document` de LangChain:

```python
Document(
    id=str(row.Index),
    page_content=row.text,                                       # el texto que se convierte en embedding
    metadata={"corpus_id": row.Index, "category": row.category}, # identificador estable + categoría
)
```

**¿Por qué separar texto y metadatos?** El texto (`page_content`) es lo que se vectoriza; el
identificador y la categoría viajan al lado, sin alterar el índice. Así, más adelante, se pueden aplicar
**filtros**, **trazabilidad** ("¿de qué noticia salió este fragmento?") o conectar el índice a una cadena
RAG sin tocar nada de lo construido.

Resultado real: `Documentos: 50,000`, con ejemplos como *"Bangladesh paralysed by strikes…"* (World),
*"Desiring Stability Redskins coach Joe Gibbs…"* (Sports) o *"U2 pitches for Apple New iTunes ads…"*
(Sci/Tech).

---

## 6. Embeddings con Model2Vec

Los embeddings se generan con `Model2vecEmbeddings("minishlab/potion-retrieval-32M")`, la integración de
LangChain para **Model2Vec**. Es un modelo **estático**, optimizado para recuperación:

- produce vectores de **512 componentes**;
- **no necesita PyTorch, ONNX ni GPU**: codifica texto con operaciones ligeras sobre embeddings de tokens
  precalculados (por eso es mucho más rápido en CPU que un modelo tipo `sentence-transformers`);
- implementa el contrato `Embeddings` de LangChain (`embed_documents` y `embed_query`, que vimos en la
  sesión 2), así que se puede **sustituir por OpenAI, Google, Cohere…** cambiando solo el objeto
  `embedding_model` (recuerda ajustar la dimensión del índice a la del nuevo modelo).

### Normalización L2: coseno = producto escalar

```python
embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True).clip(min=1e-12)
```

Se normalizan todos los vectores a longitud 1. Como vimos en la sesión 1 (sección 8), con vectores
normalizados **la similitud coseno y el producto escalar dan el mismo orden**. Por eso todos los índices
del notebook pueden usar producto escalar (`METRIC_INNER_PRODUCT`), que es más barato de calcular.

### Caché en disco

Calcular 50.000 embeddings lleva tiempo, así que el notebook guarda la matriz en un `.npy` cuyo nombre
incluye un *hash* del modelo, el número de documentos y la semilla:

```python
cache_key = hashlib.sha256(f"{EMBEDDING_MODEL}|{len(documents)}|{SEED}".encode()).hexdigest()[:12]
```

Si algo cambia, el hash cambia y se recalcula; si no, se carga directamente (con `mmap_mode="r"`, sin
copiar todo a RAM de golpe). Resultado real:

```
Matriz: (50000, 512); float32: 97.7 MiB
```

**Comprobación de cabeza:** 50.000 × 512 × 4 bytes (un `float32` ocupa 4) = 102,4 millones de bytes ≈
97,7 MiB. Esa cifra será importante cuando comparemos tamaños de índice.

---

## 7. Un mismo contrato LangChain para índices distintos

Esta es la idea de ingeniería más importante del notebook. LangChain separa **tres piezas**:

1. el **modelo de embeddings** (convierte texto en vectores);
2. el **índice FAISS** (resuelve la búsqueda vectorial: aquí es donde cambiamos de algoritmo);
3. el **`Docstore`** (devuelve el `Document` completo y sus metadatos a partir de un identificador).

**FAISS** (*Facebook AI Similarity Search*) actúa como motor numérico interno; **LangChain** actúa como
interfaz común. Gracias a eso, la función siguiente envuelve **cualquier** índice FAISS ya poblado en el
mismo `VectorStore`:

```python
def as_langchain_vector_store(faiss_index):
    return FAISS(
        embedding_function=embedding_model,
        index=faiss_index,                 # ← lo único que cambia entre métodos
        docstore=shared_docstore,          # ← compartido por todos
        index_to_docstore_id=index_to_docstore_id.copy(),
        distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
    )
```

A partir de ahí, **todas las búsquedas** pasan por la misma llamada:

```python
def search_by_vector(vector_store, query_vector, k=TOP_K):
    results = vector_store.similarity_search_with_score_by_vector(query_vector.tolist(), k=k)
    ...
```

**Ejemplo cotidiano:** es como un enchufe estándar. Da igual si detrás tienes una central eléctrica de gas,
solar o nuclear: tu lámpara se conecta igual. Aquí, tu aplicación "se enchufa" siempre al mismo
`VectorStore`; detrás puede haber una búsqueda exacta, un grafo HNSW o un índice IVF-PQ.

### ¿Por qué se usan vectores de consulta precalculados?

Los benchmarks llaman a `..._by_vector` con los vectores de las consultas **ya calculados**, en lugar de
pasar el texto. Así el cronómetro mide **el índice**, no el tiempo del modelo de embeddings (que sería
idéntico para todos los métodos y ensuciaría la comparación).

### Utilidades de medición

| Función | Qué mide |
|---|---|
| `benchmark_store` | Ejecuta las 6 consultas `BENCHMARK_REPETITIONS=7` veces y devuelve la **mediana** de ms por consulta (más robusta que la media ante picos). Antes de medir se hace una búsqueda de calentamiento (`_ = search_by_vector(...)`). |
| `serialized_size_mib` | Tamaño del índice serializado (`faiss.serialize_index`), en MiB: la "huella de memoria" del índice. |
| `ranking_table` | Convierte ids y scores en una tabla legible con categoría y texto. |

---

## 8. Baseline exacto: `IndexFlatIP`

Antes de comparar métodos aproximados hace falta una **referencia**. `IndexFlatIP` almacena todos los
vectores tal cual y calcula el producto escalar de la consulta contra cada uno. No requiere entrenamiento
ni estructura auxiliar: es transparente y exacto. Es la "verdad" contra la que mediremos el recall.

### Las 6 consultas del notebook

```python
queries = [
    "diplomatic negotiations between countries after an armed conflict",   # World
    "a football team wins an international championship",                  # Sports
    "central bank interest rates and their effect on markets",             # Business
    "a new spacecraft mission explores another planet",                    # Sci/Tech
    "a technology company launches a new mobile device",                   # Sci/Tech
    "quarterly earnings and a corporate acquisition",                      # Business
]
```

Son consultas **semánticas** (no comparten palabras exactas con los titulares), justo el terreno de los
embeddings densos. Resultados reales del baseline:

| Consulta | Mejor resultado | Score |
|---|---|---|
| diplomatic negotiations… | *"Full Sudanese peace talks get off to a shaky s…"* (World) | 0.497 |
| a football team wins… | *"Wins Tough to Find The revamped ACC is one of…"* (Sports) | 0.495 |
| central bank interest rates… | *"ECB leaves interest rates unchanged…"* (Business) | 0.643 |

Los cinco primeros de cada consulta son de la categoría esperada: el modelo "entiende" el tema.

### Coste medido

```
method  median_ms_per_query  candidates_per_query
Exact            1.597                  50000
```

**1,6 ms por consulta puntuando los 50.000 documentos.** Parece poco, pero con 1 millón de documentos serían
del orden de 30 ms por consulta, y con cientos de millones ya sería inviable en un sistema interactivo. Y
recuerda: **es la referencia de calidad** (recall = 1.0 por definición) contra la que se miden los demás.

---

## 9. HNSW: navegar un grafo de vecinos

**HNSW** = *Hierarchical Navigable Small World* ("mundo pequeño navegable jerárquico").

### La idea: buscar navegando entre vecinos

HNSW organiza los vectores como un **grafo de proximidad**: cada elemento (nodo) se conecta con otros
vectores cercanos. En lugar de comparar la consulta con toda la colección:

1. **empezamos desde un punto de entrada**;
2. **nos movemos hacia vecinos cada vez más prometedores** (los más parecidos a la consulta);
3. **detenemos la exploración** cuando ya no encontramos mejores candidatos.

> La búsqueda se transforma de **escanear una colección** a **navegar por una red de vecinos**.

**Ejemplo cotidiano:** buscar a alguien en una fiesta preguntando "¿quién de aquí conoce a Marta?". Vas
saltando de persona en persona, siempre hacia quien está "más cerca" de Marta, sin hablar con los 500
invitados.

### "Small World": conexiones locales y saltos globales

Un grafo con solo conexiones muy locales necesitaría muchos pasos para cruzar el espacio. HNSW aprovecha
las redes de mundo pequeño (como las "seis grados de separación"):

- **Conexiones cortas** → exploran con precisión una región concreta.
- **Conexiones largas** → permiten grandes saltos entre regiones alejadas.

La combinación permite **alcanzar rápido una zona prometedora y después refinar localmente**.

### La jerarquía: capas

HNSW organiza el grafo en **múltiples capas**:

| Capa | Contenido | Para qué sirve |
|---|---|---|
| **Superiores** | Pocos nodos | Navegación rápida entre regiones alejadas |
| **Intermedias** | Mayor densidad | Refinamiento progresivo |
| **Base** | **Todos** los elementos | Búsqueda precisa entre vecinos cercanos |

```
Navegar rápido arriba  →  refinar progresivamente  →  buscar localmente abajo
```

La consulta "entra" por arriba, desciende usando en cada nivel el mejor candidato encontrado como punto de
partida del siguiente. El notebook lo llama búsqueda *coarse-to-fine* (de grueso a fino).

**Ejemplo cotidiano:** es como usar un mapa con zoom. Primero miras el mapa del país (pocos puntos, saltos
grandes), luego el de la provincia, luego el de la ciudad y por último el plano de la calle.

### HNSW no aparece gratis: hay que construir el grafo

Cada vector nuevo debe incorporarse al índice: se buscan vecinos candidatos, se seleccionan las conexiones
útiles y se inserta el nodo en las capas correspondientes. Además, el índice **guarda las conexiones**, así
que consume **más memoria** que almacenar solo los vectores.

> **HNSW intercambia memoria y coste de construcción por búsquedas extremadamente rápidas.**

### Los tres parámetros de HNSW

| Parámetro | Cuándo actúa | Qué controla | Efecto de subirlo |
|---|---|---|---|
| **`M`** | Construcción | Nº aproximado de conexiones por nodo | Más conectividad y memoria; normalmente mayor recall |
| **`efConstruction`** | Construcción | Candidatos explorados al insertar cada nodo | Mejor índice, pero construcción más costosa |
| **`efSearch`** | **Consulta** | Candidatos que mantiene la búsqueda | Mayor recall, pero mayor latencia |

`M` y `efConstruction` **condicionan el índice** (para cambiarlos hay que reconstruirlo); `efSearch` permite
**ajustar el trade-off en tiempo de consulta, sin reconstruir nada**.

### En el notebook

```python
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_VALUES = [10, 25, 50, 100, 200]

hnsw_index = faiss.IndexHNSWFlat(VECTOR_DIMENSION, HNSW_M, faiss.METRIC_INNER_PRODUCT)
hnsw_index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
hnsw_index.add(np.asarray(embeddings))
...
hnsw_index.hnsw.efSearch = max(ef_search, TOP_K)   # se cambia sin reconstruir
```

Fíjate en `max(ef_search, TOP_K)`: `efSearch` nunca debe ser menor que `k`, porque no se pueden devolver
10 resultados si solo se mantienen 5 candidatos.

### Resultados reales

| `efSearch` | Recall@10 | Latencia mediana (ms) | Aceleración vs. exact (1,597 ms) |
|---|---|---|---|
| 10 | 0.933 | 0.031 | ≈ 52× |
| 25 | 0.967 | 0.040 | ≈ 40× |
| **50** | **1.000** | **0.063** | **≈ 25×** |
| 100 | 1.000 | 0.156 | ≈ 10× |
| 200 | 1.000 | 0.275 | ≈ 6× |

Tamaño del índice: **104,5 MiB** (frente a 97,7 MiB del exacto: ~7 MiB extra de aristas del grafo).
Tiempo de construcción: **4,71 s**.

**Cómo leer la tabla:** con `efSearch=50` HNSW ya iguala el recall del exacto (1.000) siendo unas **25
veces más rápido**. Subir a 100 o 200 solo gasta latencia sin mejorar nada: es la parte plana de la curva
recall-latencia (sección 3). El "punto dulce" está en `efSearch≈50` para este corpus.

⚠️ FAISS no expone cuántos nodos visita HNSW por consulta, así que la columna `candidates_per_query`
queda vacía (`NaN`) para HNSW.

---

## 10. IVF: dividir el espacio antes de buscar

**IVF** = *Inverted File* (archivo invertido). Es un enfoque completamente distinto a HNSW: en vez de
navegar un grafo, **divide el espacio vectorial en regiones**.

### Cómo funciona

1. **Construir centroides.** Se agrupan los vectores con *clustering* (k-means) en `nlist` regiones, cada
   una representada por un **centroide** (su "centro"). Esto es el **entrenamiento** (`train`).
2. **Asignar cada vector a su región.** Cada vector se guarda en la **lista invertida** de su centroide más
   cercano: `C₁ → {x₂, x₇, x₁₄, …}`, `C₂ → {x₁, x₉, x₂₁, …}`…
3. **Buscar solo en las regiones más prometedoras.** Ante una consulta:
   - buscamos los **centroides más cercanos** a la consulta;
   - accedemos a **sus listas**;
   - comparamos **únicamente contra esos vectores**.

**Ejemplo cotidiano:** un supermercado organizado por pasillos (lácteos, limpieza, bebidas…). Si buscas
yogur no recorres los 30 pasillos: vas al de lácteos. Los centroides son los carteles de cada pasillo; las
listas invertidas, el contenido de cada uno.

### `nprobe`: cuántas regiones exploramos

La consulta no tiene por qué limitarse a una única región. **`nprobe`** es el número de centroides
(regiones) cercanos que visitamos:

| | `nprobe = 1` | `nprobe` intermedio | `nprobe` alto |
|---|---|---|---|
| Comparaciones | Muy pocas | Más candidatos | Muchas regiones |
| Latencia | Menor | Moderada | Mayor |
| Recall@k | Mayor riesgo de perder vecinos | Mejor | Cercano al exact search |

**¿Por qué se pierden vecinos?** Si la consulta cae **cerca de la frontera** entre dos regiones, sus
verdaderos vecinos pueden estar "al otro lado" y nunca los miramos. Con `nprobe` mayor miramos también las
regiones vecinas. **`nprobe` controla directamente el trade-off entre Recall@k y coste de búsqueda.**

### En el notebook

```python
N_LISTS = int(np.clip(round(np.sqrt(N_DOCUMENTS)), 64, 512))   # √50000 ≈ 224
IVF_NPROBE_VALUES = [1, 2, 4, 8, 16, 32, 64]

ivf_quantizer = faiss.IndexFlatIP(VECTOR_DIMENSION)             # busca el centroide más cercano
ivf_index = faiss.IndexIVFFlat(ivf_quantizer, VECTOR_DIMENSION, N_LISTS, faiss.METRIC_INNER_PRODUCT)
ivf_index.train(np.asarray(embeddings))   # aprende los centroides
ivf_index.add(np.asarray(embeddings))     # reparte los vectores en listas
```

- **`nlist = √N`** (acotado entre 64 y 512) es una regla práctica habitual: con `N=50.000` da **224
  listas** de unos 223 vectores de media.
- El "cuantizador grueso" (`ivf_quantizer`) es un índice exacto pequeño: solo compara la consulta con los
  224 centroides, no con los 50.000 vectores.
- `IndexIVFFlat` **conserva los vectores completos en `float32`**: la aproximación viene *solo* de qué
  listas se visitan, no de cómo se calcula la similitud dentro de ellas.

### Resultados reales

Listas: 224; construcción: **0,21 s**. Elementos por lista: media 223,2, **mínimo 22, máximo 717**
(las listas están **desequilibradas**: los datos no se reparten de forma uniforme).

| `nprobe` | Recall@10 | Latencia (ms) | Candidatos por consulta | % del corpus |
|---|---|---|---|---|
| 1 | 0.500 | 0.039 | 364 | 0,7 % |
| 2 | 0.817 | 0.045 | 697 | 1,4 % |
| 4 | 0.850 | 0.060 | 1.131 | 2,3 % |
| 8 | 0.900 | 0.095 | 2.147 | 4,3 % |
| 16 | 0.933 | 0.151 | 3.912 | 7,8 % |
| 32 | 0.983 | 0.268 | 7.492 | 15 % |
| **64** | **1.000** | **0.516** | **14.815** | **30 %** |

Tamaño: **98,5 MiB**.

**Cómo leer la tabla:**

- Con `nprobe=1` solo se puntúa el 0,7 % del corpus, pero el recall es un pobre 0.50: de cada 10 vecinos
  exactos, se pierden 5.
- Con `nprobe=64` (30 % del corpus) se alcanza recall 1.0, y aun así es ~3× más rápido que el exacto
  (0,516 vs. 1,597 ms).
- Si `nprobe` llegara a `nlist` (224) se visitarían todas las listas y estaríamos, en la práctica, haciendo
  búsqueda exacta más la sobrecarga del índice: el ahorro habría desaparecido.
- Comparando con HNSW: para recall 1.0, HNSW necesita 0,063 ms e IVF 0,516 ms. **En este corpus HNSW gana
  claramente**, a cambio de más tiempo de construcción (4,71 s vs. 0,21 s).

> **Aviso sobre el texto del notebook:** la celda explicativa de IVF dice que aumentar `nprobe` "mejora
> normalmente recall y latencia". Los datos muestran que mejora el **recall** pero **empeora la latencia**
> (0,039 → 0,516 ms). Es un pequeño descuido de redacción; el trade-off real es el que refleja la tabla.

---

## 11. Product Quantization e IVF-PQ: comprimir los vectores

### El problema que resuelve PQ

HNSW e IVF ayudan a **buscar** menos, pero ambos siguen guardando los vectores completos. En colecciones muy
grandes el coste **no está solo en buscar: también en almacenar**. 1.000 millones de vectores de 512
dimensiones en `float32` son ~2 TB de RAM.

**Product Quantization (PQ)** comprime cada vector:

1. **Divide** los `d` componentes del vector en `m` **subvectores** (aquí, 512 componentes → 16 trozos de 32).
2. Para cada subespacio, **aprende un *codebook*** (un "diccionario") de 256 centroides representativos
   (con `nbits=8` hay 2⁸ = 256 posibles).
3. Sustituye cada subvector por el **identificador** (0-255, ocupa **1 byte**) del centroide del codebook
   más parecido.

```
Vector original:   512 valores float32  = 2.048 bytes
Vector cuantizado: 16 códigos de 1 byte =    16 bytes     (128× más pequeño)
```

**Ejemplo cotidiano:** es como describir un color de pintura. En vez de dar los tres valores RGB con
decimales exactos, dices "el número 137 de mi catálogo de 256 colores". Ocupas mucho menos, pero pierdes
precisión: el color real puede ser algo distinto del de catálogo.

| Ventaja | Explicación |
|---|---|
| **Menos memoria** | Podemos almacenar colecciones mucho mayores. |
| **Comparaciones más rápidas** | Parte del cálculo se hace sobre representaciones comprimidas. |
| **Pérdida de precisión** | La representación **deja de ser exacta**. |

### Cómo se puntúa: *asymmetric distance computation*

La **consulta permanece sin comprimir**. FAISS precalcula, una vez por consulta, tablas con la distancia
entre cada subvector de la consulta y cada centroide del codebook. Puntuar un vector comprimido se reduce a
**buscar 16 valores en tablas y sumarlos**: muy rápido, sin operar con `float32`.

### IVF-PQ: dos aproximaciones combinadas

> **IVF reduce *dónde* buscamos. PQ reduce *cuánto ocupa* y *cuánto cuesta comparar* cada vector.**

`IndexIVFPQ` combina ambas: IVF decide qué listas visitar y PQ aproxima los vectores de esas listas. Por
eso acumula **dos fuentes de error**: las listas no visitadas *y* el error de cuantización.

```python
PQ_M = 16          # subvectores; 512 % 16 == 0 (el notebook lo comprueba)
PQ_NBITS = 8       # 1 byte por código
PQ_TRAIN_SIZE = min(30_000, N_DOCUMENTS)   # PQ se entrena con una muestra aleatoria

ivfpq_index = faiss.IndexIVFPQ(pq_quantizer, VECTOR_DIMENSION, N_LISTS, PQ_M, PQ_NBITS,
                               faiss.METRIC_INNER_PRODUCT)
ivfpq_index.train(np.asarray(embeddings)[pq_training_ids])
ivfpq_index.add(np.asarray(embeddings))
```

Requisito: **`d` debe ser divisible entre `m`** (512 / 16 = 32 componentes por subvector).

### Resultado: el ahorro de memoria

| Representación | Tamaño |
|---|---|
| `IndexFlatIP` | **97,66 MiB** |
| `IndexIVFPQ` | **2,08 MiB** |

Es una reducción de **~47×**. (No llega a 128× porque además del código de 16 bytes por documento, el
índice guarda los 224 centroides, los codebooks y los identificadores.) Tiempo de construcción: **2,48 s**
(entrenar los codebooks tiene su coste).

### Resultado: el recall (¡atención!)

| `nprobe` | Recall@10 | Latencia (ms) | Candidatos |
|---|---|---|---|
| 4 | 0.333 | 0.040 | 1.212 |
| 16 | 0.333 | 0.058 | 4.247 |
| 64 | 0.333 | 0.102 | 15.217 |

**Observación clave:** el recall se queda **congelado en 0.333** aunque subamos `nprobe` de 4 a 64 (y se
visiten 12× más candidatos). Con IVF a secas, más `nprobe` sí mejoraba el recall hasta 1.0. ¿Qué ha
cambiado? Que ahora **el cuello de botella no son las listas visitadas, sino el error de cuantización**:
al comprimir cada vector a 16 bytes, el ranking *dentro* de las listas ya no coincide con el exacto, y no
importa cuántas listas más se miren.

**Ejemplo cotidiano:** si tu fotocopiadora saca copias borrosas, buscar en más cajones no te ayuda a
distinguir las fotos: el problema está en la calidad de la copia, no en dónde buscas.

### Inspección cualitativa

Recall mide coincidencia de **identificadores**, pero documentos casi equivalentes pueden intercambiar
posiciones. Para la consulta *"a new spacecraft mission explores another planet"* (`efSearch=50`,
`nprobe=16`):

- **Exact, HNSW e IVF** devuelven **exactamente los mismos 5 documentos** con los mismos scores (0.633,
  0.591, 0.584, 0.574, 0.567): *Mars Reconnaissance Orbiter*, *Mars Life Evidence*, *Mars Odyssey*…
- **IVF-PQ** devuelve documentos **también del tema espacial** (Cassini, Saturno, Marte…) pero en otro
  orden y con **scores distintos** (0.569, 0.566…): son scores *aproximados*, calculados con los códigos
  comprimidos.

Lectura: IVF-PQ tiene recall bajo (0.33) pero **los resultados siguen siendo temáticamente razonables**.
Para muchas aplicaciones eso puede bastar; para otras (donde necesitas exactamente los mejores), no. Una
práctica habitual es recuperar más candidatos con IVF-PQ y **reordenarlos con vectores completos o con un
reranker** (sesión 3).

> **Aviso sobre el texto del notebook:** la celda explicativa de PQ habla de "384 dimensiones" y `m=12`
> (12 bytes por documento), pero el código real usa **512 dimensiones y `m=16`** (16 bytes). Los números
> correctos son los de esta guía.

---

## 12. Recuperación idiomática con LangChain (`as_retriever`)

Los benchmarks anteriores usan la variante *por vector* para excluir del cronómetro la codificación de la
consulta. En una aplicación real, el acceso parte del **texto**. LangChain lo resuelve con
`as_retriever()`, que convierte cualquier `VectorStore` en un `Runnable`:

```python
ivf_index.nprobe = 16
retriever = ivf_store.as_retriever(search_kwargs={"k": 5})
retrieved_documents = retriever.invoke("a new spacecraft mission explores another planet")
```

Devuelve `Document`s completos (texto + `category` + `corpus_id`): *Red Planet Bound: Mars Reconnaissance
Orbiter…*, *NASA Extends Mars Odyssey Orbiter Mission…*, etc. — todos `Sci/Tech`.

**Por qué importa:** ese mismo `retriever` se conecta tal cual a una **cadena RAG**, a herramientas o a
agentes. Cambiar de HNSW a IVF-PQ es cambiar el índice FAISS de detrás; **el resto de la aplicación no se
entera**. Este es el hilo que enlaza esta sesión con las de RAG (sesión 7).

---

## 13. Comparación final y decisiones de diseño

### Tabla cualitativa (diapositiva)

| | **Exact Search** | **HNSW** | **IVF** |
|---|---|---|---|
| **Estrategia** | Examinar todos los vectores | Navegar un grafo | Explorar regiones |
| **Recall** | Exacto | Muy alto, configurable | Configurable |
| **Latencia a gran escala** | Alta | Muy baja | Baja |
| **Memoria adicional** | Baja | Alta | Moderada |
| **Construcción del índice** | Mínima | Costosa | Requiere *clustering* |
| **Actualizaciones** | Simples | Posibles, con coste | Dependen de la implementación |

*(Los valores son relativos y dependen del tamaño del corpus, la dimensionalidad, el hardware y la
configuración.)* **La estructura que acelera la búsqueda también introduce nuevos costes.**

### Tabla cuantitativa (notebook, 50.000 docs × 512 dims)

Puntos de operación representativos de cada método:

| Método | Configuración | Recall@10 | Latencia (ms) | Tamaño (MiB) | Construcción (s) |
|---|---|---|---|---|---|
| Exact | `IndexFlatIP` | 1.000 | 1.597 | 97,7 | 0 |
| HNSW | `efSearch=50` | 1.000 | 0.063 | 104,5 | 4,71 |
| IVF | `nprobe=64` | 1.000 | 0.516 | 98,5 | 0,21 |
| IVF | `nprobe=16` | 0.933 | 0.151 | 98,5 | 0,21 |
| IVF-PQ | `nprobe=16, m=16` | 0.333 | 0.058 | **2,1** | 2,48 |

Y el notebook dibuja la gráfica **Recall@10 frente a latencia** (una curva por método): los métodos buenos
son los que quedan **arriba a la izquierda** (alto recall, baja latencia). Cada fila es un **punto de
operación**; HNSW cambia `efSearch`, IVF e IVF-PQ cambian `nprobe`.

**Lecturas honestas de estos números:**

- Ningún método "gana" en todo: HNSW es el más rápido con recall 1.0, pero es el que más memoria y
  construcción pide; IVF-PQ es imbatible en memoria pero pierde recall; el exacto es el único con calidad
  garantizada y sin construcción.
- Con solo 50.000 vectores el exacto tarda 1,6 ms: **el ahorro absoluto es pequeño**. La ventaja de ANN
  crece con N (el coste exacto crece linealmente; el de HNSW/IVF, mucho más despacio). Con un corpus de
  50.000 documentos y pocas consultas, un `IndexFlatIP` sigue siendo una opción perfectamente razonable.
- La latencia corresponde al `VectorStore` de LangChain y **excluye** el cálculo del embedding de la
  consulta. Las cifras dependen del hardware, corpus, modelo y bibliotecas: **la relación entre los
  puntos es más informativa que un valor aislado**.

### Elegir el índice a partir del problema

La diapositiva propone **no empezar por "¿cuál es el mejor índice?"**, sino por estas cinco preguntas:

| Pregunta | Por qué importa |
|---|---|
| **¿Cuántos vectores tenemos?** | Miles no plantean el mismo problema que cientos de millones. |
| **¿Qué latencia necesitamos?** | Procesamiento *offline* y búsqueda interactiva tienen requisitos distintos. |
| **¿Cuánto recall podemos sacrificar?** | Algunas aplicaciones toleran aproximación; otras necesitan resultados casi exactos. |
| **¿Cuánta memoria tenemos?** | HNSW compra velocidad con más memoria; PQ puede reducir drásticamente el almacenamiento. |
| **¿Cómo cambia la colección?** | Índices estáticos y colecciones con inserciones frecuentes tienen necesidades diferentes. |

$$\text{Dataset} + \text{hardware} + \text{SLA} + \text{calidad requerida} \;\rightarrow\; \text{configuración del índice}$$

### Decisiones de diseño (celda final del notebook)

- **Escala y tasa de consultas:** `IndexFlatIP` es simple y exacto, pero crece linealmente.
- **SLA de latencia:** HNSW suele ofrecer latencia baja y alto recall; IVF expresa el presupuesto mediante
  listas y candidatos.
- **Recall objetivo:** debe medirse con consultas representativas y un baseline exacto.
- **Memoria:** HNSW añade aristas; IVFFlat conserva vectores; IVFPQ reduce la huella a cambio de error de
  cuantización.
- **Construcción y actualización:** HNSW inserta nodos; IVF y PQ requieren **entrenamiento** y pueden
  necesitar **reentrenamiento** si la distribución de los datos cambia.
- **Abstracción:** LangChain mantiene estable la interfaz y el tipo `Document`; FAISS conserva el control
  fino del índice.
- **Operación:** filtros, borrados, persistencia, concurrencia y aceleración por GPU pueden pesar más que
  el algoritmo a la hora de elegir.

> **No existe un índice universalmente mejor.** Una evaluación sólida fija restricciones, mide una familia
> de configuraciones y elige un punto de la **frontera recall–latencia–memoria** que satisfaga al sistema.
> Y la decisión debe validarse **empíricamente con benchmarks sobre tus propios datos**.

---

## 14. Resumen final

1. **La búsqueda exacta** compara la consulta con todos los vectores: es exacta y simple, pero cuesta
   $O(Nd)$ y crece linealmente con el corpus. El problema no es la fórmula, sino cuántas veces se ejecuta.
2. **ANN** no aproxima la similitud, aproxima **la búsqueda de vecinos**: evita comparar con todos los
   vectores usando una estructura construida a partir de la geometría de los datos.
3. **Más trabajo offline (construir el índice) → menos trabajo por consulta.**
4. **Recall@k** mide qué fracción del top-k exacto recupera el índice aproximado. Mide fidelidad al ranking
   exacto, **no** relevancia semántica.
5. **HNSW** navega un grafo jerárquico (capas superiores: saltos largos; capa base: detalle). Parámetros:
   `M` y `efConstruction` (construcción), `efSearch` (consulta). Muy rápido y con alto recall, a cambio de
   **memoria y coste de construcción**.
6. **IVF** divide el espacio en `nlist` regiones con centroides y solo visita `nprobe` de ellas. `nprobe`
   controla el trade-off recall–latencia.
7. **PQ** comprime cada vector en pocos códigos (aquí 2.048 → 16 bytes por documento; índice 97,7 → 2,1
   MiB), a cambio de **perder exactitud**. **IVF-PQ** combina ambos: IVF decide *dónde* buscar, PQ reduce
   *cuánto ocupa* cada vector.
8. Con IVF-PQ el recall puede quedar limitado por la **cuantización**, no por `nprobe`: en el notebook se
   estanca en 0.333 aunque se visiten 12× más candidatos.
9. **LangChain** mantiene el mismo contrato (`VectorStore`, `Retriever`, `Document`) mientras FAISS cambia
   de algoritmo por debajo.
10. **No hay un índice universalmente mejor.** La elección depende de: nº de vectores, latencia, recall
    aceptable, memoria disponible y cómo cambia la colección — y se valida con benchmarks propios.

---

## 15. ¿Qué sigue después?

La frase que resume la sesión es:

> **Más trabajo al construir el índice → menos trabajo por consulta, a cambio de un pequeño (y medible)
> sacrificio de recall.**

Hasta ahora hemos trabajado con FAISS **en memoria, dentro de un notebook**. En un sistema real aparecen
preguntas nuevas: dónde se **almacenan** los vectores y los metadatos, cómo se **persisten y actualizan**,
cómo se aplican **filtros**, cómo se **escala** con varios nodos… Eso es lo que abordan las siguientes
sesiones del tema (almacenamiento y recuperación en la sesión 5, construcción y evaluación de sistemas en la
6 y RAG en la 7). La arquitectura de la cadena no cambia:

```
representar → indexar → recuperar (ANN) → refinar (hybrid, rerank) → generar (RAG)
```

Y en este punto ya tienes las piezas del "recuperar" que hace que todo lo demás funcione a escala.

### Preguntas para repasar

1. ¿Por qué un `IndexFlatIP` ya no es viable con mil millones de vectores, aunque calcular un producto
   escalar sea barato? ¿Qué añaden SIMD y las operaciones vectorizadas, y qué no pueden arreglar?
2. Si un índice ANN tiene Recall@10 = 1.0, ¿significa que los resultados son relevantes para el usuario?
   ¿Por qué sí o por qué no?
3. En HNSW, ¿qué parámetros hay que fijar al construir el índice y cuál se puede cambiar en cada consulta?
   ¿Qué ventaja práctica tiene eso?
4. En IVF, ¿por qué con `nprobe=1` se pierden vecinos? ¿Qué le pasa al recall y a la latencia al subirlo?
5. ¿Por qué el recall de IVF-PQ no mejora al subir `nprobe` de 4 a 64, mientras que el de IVF sí?
6. Tienes 20 millones de vectores y solo 4 GB de RAM para el índice. ¿Qué combinación considerarías?
   ¿Y con 5.000 vectores y una consulta cada minuto?
7. ¿Qué información necesitas antes de poder afirmar que "HNSW es mejor que IVF" para tu proyecto?
8. Si llega una tanda de documentos con un tema completamente nuevo, ¿qué índices podrían degradarse y por
   qué (piensa en el entrenamiento de centroides y codebooks)?
