# Guía de estudio — Sesión 5: Sistemas de almacenamiento y recuperación (Vector Databases, filtros, CRUD y arquitectura)

> Esta guía explica, con lenguaje sencillo y muchos ejemplos, el contenido de
> [`S5_sistemas_almacenamiento_recuperacion.ipynb`](./S5_sistemas_almacenamiento_recuperacion.ipynb), de las
> diapositivas
> [`T5-S5 Sistemas de almacenamiento y recuperacion.pptx.pdf`](../pdfs/T5-S5%20Sistemas%20de%20almacenamiento%20y%20recuperacion.pptx.pdf)
> y del entorno descrito en [`README.md`](./README.md) y [`VALIDACION.md`](./VALIDACION.md).
>
> Es la continuación directa de las sesiones anteriores — si no las has leído, échales un vistazo primero:
> [sesión 1 (vectores)](../01-vectores/EXPLICACION_sesion_1.md),
> [sesión 2 (sparse vs dense)](../02-sistemas-recuper-info/EXPLICACION_sesion_02.md),
> [sesión 3 (hybrid, reranking, ColBERT)](../03-recuper-info-2/EXPLICACION_sesion_03.md) y
> [sesión 4 (indexación: HNSW, IVF, PQ)](../04-indexacion-busq-efic/EXPLICACION_sesion_04.md). En la sesión 4
> aprendimos a **buscar rápido** entre millones de vectores con un índice ANN. Aquí damos el salto que falta
> para llevar eso a un sistema real: **¿dónde viven los datos, cómo cambian, cómo se filtran y cómo se
> opera todo?**

## Índice

1. [Del índice vectorial a un sistema de almacenamiento](#1-del-índice-vectorial-a-un-sistema-de-almacenamiento)
2. [Un vector rara vez viaja solo: el registro](#2-un-vector-rara-vez-viaja-solo-el-registro)
3. [Relevancia vs. elegibilidad: metadatos y filtros](#3-relevancia-vs-elegibilidad-metadatos-y-filtros)
4. [Entorno y configuración del notebook](#4-entorno-y-configuración-del-notebook)
5. [El corpus del notebook y su contrato de metadatos](#5-el-corpus-del-notebook-y-su-contrato-de-metadatos)
6. [Conectar con Pinecone desde LangChain e ingerir](#6-conectar-con-pinecone-desde-langchain-e-ingerir)
7. [Recuperación semántica con filtros (resultados reales)](#7-recuperación-semántica-con-filtros-resultados-reales)
8. [Filtrar antes o después de buscar](#8-filtrar-antes-o-después-de-buscar)
9. [CRUD: crear, reemplazar, actualizar y borrar](#9-crud-crear-reemplazar-actualizar-y-borrar)
10. [Persistencia y reconexión](#10-persistencia-y-reconexión)
11. [Namespaces y separación entre organizaciones](#11-namespaces-y-separación-entre-organizaciones)
12. [Versiones de colección y migración de embeddings](#12-versiones-de-colección-y-migración-de-embeddings)
13. [Producción: mucho más que Recall@k y latencia](#13-producción-mucho-más-que-recallk-y-latencia)
14. [El ecosistema: pgvector, Vector Databases y despliegue](#14-el-ecosistema-pgvector-vector-databases-y-despliegue)
15. [Diseñar y elegir una arquitectura de recuperación](#15-diseñar-y-elegir-una-arquitectura-de-recuperación)
16. [Material adicional: Qdrant, Milvus y Weaviate con Docker](#16-material-adicional-qdrant-milvus-y-weaviate-con-docker)
17. [Resumen final](#17-resumen-final)
18. [¿Qué sigue después?](#18-qué-sigue-después)

---

## 1. Del índice vectorial a un sistema de almacenamiento

HNSW, IVF o cualquier otro índice ANN resuelven **una pregunta muy concreta**:

> ¿Cómo encontrar rápidamente los vectores más próximos a una query?

Pero una aplicación real necesita responder otras cuatro preguntas que ningún algoritmo ANN contesta:

| # | Pregunta | Detalle |
|---|---|---|
| 1 | **¿Dónde viven los datos?** | Los vectores y documentos deben sobrevivir al proceso que ejecuta la búsqueda. |
| 2 | **¿Cómo cambian?** | Necesitamos insertar, actualizar y eliminar información. |
| 3 | **¿Cómo describimos cada vector?** | IDs, metadatos, permisos, fechas, categorías, versiones… |
| 4 | **¿Cómo operamos el sistema?** | Concurrencia, escalado, backups, disponibilidad, monitorización… |

La diapositiva lo dibuja como capas concéntricas: en el centro está el **ANN**, alrededor el
**almacenamiento**, luego **datos + metadatos**, luego **CRUD** (Create, Read, Update, Delete) y por fuera la
**operación**.

> **El índice optimiza la búsqueda. La base de datos gestiona el ciclo de vida de la información.**

### ¿Por qué no quedarnos con un índice local?

En la sesión 4 el índice FAISS vivía **dentro del proceso** de un notebook: se construía, se consultaba y
desaparecía al cerrar Python. Para un prototipo con pocos documentos está bien. Pero a medida que crece:

| Problema | Por qué aparece |
|---|---|
| **Capacidad** | Vectores, índice y estructuras auxiliares pueden ocupar decenas o cientos de GB. |
| **Persistencia** | Reiniciar un proceso no debería implicar reconstruir todo el estado (¡generar embeddings cuesta tiempo y dinero!). |
| **Concurrencia** | Varias aplicaciones y usuarios necesitan consultar **y modificar** los mismos datos. |
| **Escalabilidad** | Almacenamiento y procesamiento pueden necesitar distribuirse entre varias máquinas. |

> **El problema deja de ser solamente algorítmico y pasa a ser también un problema de sistemas.**

**Ejemplo cotidiano:** un índice ANN es como el sistema de catalogación de una biblioteca (encuentra el libro
rápido). Una *Vector Database* es la biblioteca entera: el edificio donde se guardan los libros (persistencia),
el carné de socio y los permisos (seguridad), el mostrador para dar de alta o retirar libros (CRUD), los
horarios y el personal de guardia (operación). Sin catálogo no encuentras nada; pero el catálogo por sí solo no
es una biblioteca.

### Índice vectorial vs. Vector Database

| | **Índice vectorial** | **Vector Database** |
|---|---|---|
| **Qué es** | Estructura especializada para acelerar la búsqueda de vecinos más cercanos. | Sistema de almacenamiento y recuperación que incorpora uno o varios índices como parte de una infraestructura mayor. |
| **Incluye** | vectores · estructura ANN · parámetros de búsqueda | persistencia · CRUD · metadatos · filtrado · concurrencia · seguridad · replicación · backups |

> **Una Vector Database utiliza índices vectoriales; no los sustituye conceptualmente.**

El notebook lo resume igual: las garantías concretas (durabilidad, consistencia, concurrencia…) **dependen del
producto y de su configuración**. Incluso con un servicio gestionado como Pinecone, que se encarga de la
infraestructura, tu código sigue necesitando diseñar el **modelo de registro** y el **ciclo de vida de los
datos**.

---

## 2. Un vector rara vez viaja solo: el registro

En una aplicación real no almacenamos únicamente una coordenada en $\mathbb{R}^d$. La unidad de
almacenamiento es un **registro**:

```
record = { id, embedding, content, metadata }
```

| Campo | Ejemplo | Para qué sirve |
|---|---|---|
| **Identidad** (`id`) | `document_id = "DOC-8291"` | Mantiene la identidad del registro a lo largo de los cambios; permite upsert y borrado. |
| **Representación** (`embedding`) | `[0.17, -0.42, …, 0.08]` | Permite **buscar por similitud**. |
| **Contenido** (`content`) | fragmento de texto, imagen, producto, evento… | Permite **interpretar** el resultado (lo que se enseña al usuario o se pasa al LLM). |
| **Metadatos** (`metadata`) | idioma, categoría, fecha, usuario, permisos, fuente… | Deciden **qué información puede o debe recuperarse**. |

> **El embedding permite buscar por similitud. Los demás campos permiten decidir qué información puede o
> debe recuperarse.**

Este es exactamente el papel de LangChain en el notebook: convierte el contenido en embeddings y ofrece una
interfaz de `VectorStore`, mientras que **Pinecone almacena y consulta los registros**.

---

## 3. Relevancia vs. elegibilidad: metadatos y filtros

### La relevancia semántica no es suficiente

Un documento puede ser **extremadamente similar** a la consulta y, aun así, **no ser un resultado válido**.
Ejemplo de la diapositiva: la consulta *"política de vacaciones para empleados"* encuentra cuatro
políticas casi idénticas:

| Política | País | Estado | Tipo |
|---|---|---|---|
| Política de vacaciones | España | vigente | interno ✅ |
| Política de vacaciones | México | vigente | interno ❌ |
| Política de vacaciones | España | **2022** (antigua) | interno ❌ |
| Política de vacaciones | España | vigente | **externo** ❌ |

Solo la primera cumple `country = "ES"`, `status = "active"` y `employee_type = "internal"`. Las cuatro son
muy parecidas *semánticamente*; solo una es **aplicable**.

> **La similitud determina relevancia. Los filtros determinan elegibilidad.**

**Ejemplo cotidiano:** buscas "restaurante italiano bueno" y el buscador te devuelve uno excelente… en otra
ciudad, o cerrado definitivamente. Es "relevante" pero no "elegible". Necesitas filtrar por ciudad y por
"abierto ahora".

### Metadata filtering: combinar estructura y similitud

Una búsqueda vectorial puede incorporar condiciones estructuradas junto a la similitud:

```
similar_to(query_embedding)
  AND language = "es"
  AND category = "legal"
  AND date >= "2026-01-01"
  AND access_level IN ["public", "internal"]
```

Los metadatos pueden ser de tres tipos:

| Tipo | Ejemplos |
|---|---|
| **Propiedades del contenido** | idioma · categoría · autor · fecha · producto |
| **Contexto operacional** | tenant · región · versión · fuente |
| **Reglas de negocio** | disponibilidad · estado · precio · permisos |

> **Los metadatos convierten una búsqueda genérica por similitud en una consulta adaptada al dominio.**

### ¿Filtrar antes o después de buscar?

| | **Pre-filtering** | **Post-filtering** |
|---|---|---|
| **Orden** | FILTER → D′ reducido → ANN → Top-k | ANN → candidatos → FILTER → ¿Top-k? |
| **Ventaja** | El índice evita candidatos inválidos. | Arquitectura sencilla. |
| **Problema** | El filtro debe integrarse eficientemente con la búsqueda. | Podemos recuperar *k* candidatos y **terminar con muchos menos resultados válidos**. |

En sistemas reales pueden usarse estrategias pre-filter, post-filter o **híbridas/iterativas**. (En la sección
8 lo veremos con datos reales.)

### Los metadatos también necesitan ser buscables

Añadir metadatos **no garantiza** que filtrarlos sea eficiente. Imagina 100 millones de vectores y la consulta
`country = "ES"`, `category = "support"`, Top-10 semántico. Hay que resolver dos cosas:

1. **¿Qué elementos cumplen el filtro?** → resolverlo rápido puede requerir **índices específicos sobre
   atributos estructurados** (`country`, `category`, `status`…).
2. **¿Cuáles son los más próximos?** → lo resuelve el índice vectorial.

Ambos mecanismos deben **cooperar**: un sistema moderno mantiene simultáneamente índices vectoriales **e**
índices sobre atributos estructurados.

### Separar datos lógicamente: colección, namespace y metadatos

Muchos sistemas mantienen información de múltiples clientes, aplicaciones, versiones o dominios en una misma
infraestructura. Hay tres niveles de segmentación:

| Nivel | Qué es |
|---|---|
| **Colección / índice** | Gran unidad física o lógica de almacenamiento. |
| **Namespace / partición / tenant** | Segmentación de conjuntos de datos dentro del sistema. |
| **Metadata** | Restricciones más finas aplicadas a registros individuales. |

Una jerarquía típica: `company_42 → notion → legal → internal`. Una buena estrategia de segmentación mejora
**aislamiento, seguridad, mantenimiento y rendimiento**.

---

## 4. Entorno y configuración del notebook

### Qué usa el notebook

- **Pinecone** (base de datos vectorial gestionada, *serverless*) como almacén.
- **OpenAI** `text-embedding-3-small` como modelo de embeddings, configurado con **1536 dimensiones** y el
  índice con métrica **coseno**.
- **LangChain** (`langchain-core`, `langchain-openai`, `langchain-pinecone`) como capa común.
- **No necesita Docker** (los tutoriales con Docker son material aparte, sección 16).

> ℹ️ El directorio se llama "…AWS", pero el notebook **no usa servicios de AWS directamente**: Pinecone
> serverless se crea por defecto en la nube `aws`, región `us-east-1` (`PINECONE_CLOUD` y `PINECONE_REGION`
> son configurables), y es lo único que tiene que ver con AWS.

### Variables de entorno (`.env`)

| Variable | Obligatoria | Para qué |
|---|---|---|
| `OPENAI_API_KEY` | Sí | Embeddings (con facturación habilitada). |
| `PINECONE_API_KEY` | Sí | Crear/consultar el índice. |
| `PINECONE_INDEX_NAME` | No | Por defecto `s5-storage-retrieval`; 1–45 caracteres en minúscula, números o guiones, con extremos alfanuméricos. |
| `PINECONE_CLOUD` / `PINECONE_REGION` | No | Ubicación admitida por tu plan (por defecto `aws` / `us-east-1`). |

**Nunca compartas ni publiques el `.env`.** Ojo: el `README.md` indica `cp .env.example .env`, pero en el
directorio **no existe `.env.example`**; hay que crear el `.env` a mano.

### Versiones y entorno Python

`requirements.txt` fija una combinación verificada el 16-09-2026 (`jupyterlab==4.6.3`, `pandas==3.0.5`,
`langchain-core==1.6.3`, `langchain-openai==1.6.2`, `langchain-pinecone==0.2.13`, `pinecone==7.3.0`, …). El
SDK de Pinecone se fija en 7.3.0 porque `langchain-pinecone 0.2.13` declara `pinecone[asyncio]>=6.0.0,<8.0.0`,
y se recomienda **Python 3.12** porque esa integración tiene un límite `<3.14`.

En este repositorio se reutiliza el **`.venv` de la raíz del proyecto** para todas las sesiones (ver
[`CLAUDE.md`](./CLAUDE.md)), en lugar de crear uno por carpeta como sugiere el README.

### `remote_operation`: fallar con elegancia

Las operaciones remotas cuestan dinero y pueden fallar. El notebook envuelve cada una en:

```python
def remote_operation(label, operation, default=None):
    if missing_keys:
        print(f"{label}: omitido. Configura {', '.join(missing_keys)} en .env ...")
        return default
    try:
        return operation()
    except Exception as error:
        print(f"{label}: no completado ({type(error).__name__}). Comprueba claves, permisos, cuota, red ...")
        return default
```

- Si falta una clave, **el corpus y las tablas conceptuales siguen disponibles** y las operaciones remotas se
  omiten.
- Un error remoto se comunica **sin imprimir credenciales ni el mensaje del proveedor**.
- **No hay sustitución silenciosa por embeddings ficticios**: mejor que falle claro a que dé resultados
  falsos sin avisar.

### Cuidado con el consumo

Las operaciones remotas usan OpenAI y Pinecone y **pueden generar consumo**. Repetir una ingesta con los mismos
IDs **no duplica registros**, pero **vuelve a generar embeddings** (y a cobrarlos). El notebook usa namespaces
con prefijo `s5-` como espacios dedicados a estos ejemplos, y **nunca elimina un índice completo**.

---

## 5. El corpus del notebook y su contrato de metadatos

Se usa un corpus **ficticio** de documentación empresarial (sus cifras son reglas inventadas, no normativa
laboral). La carga es pequeña a propósito: permite **observar cambios y filtros** sin entrar a evaluar escala
ANN.

### 128 documentos generados de forma determinista

```
8 políticas × 4 países × 2 tipos de contrato × 2 versiones = 128 documentos
```

- **Categorías (8):** vacaciones, teletrabajo, gastos, seguridad, compras, onboarding, datos, formación.
- **Países (4):** ES, MX, FR, DE.
- **Tipo de contrato (2):** `internal`, `contractor`.
- **Versión (2):** v1 (2025, `archived`) y v2 (2026, `active`).

Las versiones históricas **comparten gran parte del vocabulario** con las vigentes, y eso es deliberado: hace
que una búsqueda semántica pueda encontrar una política **plausible pero inaplicable**.

### El contrato de metadatos

```python
metadata = {
    "doc_id": doc_id, "language": "es", "country": country,
    "category": category, "date": effective_date.isoformat(),
    "effective_day": effective_date.toordinal(), "employee_type": employee_type,
    "access_level": "restricted" if category in ("seguridad", "datos") else "standard",
    "source": f"intranet://acme/{country.lower()}/{category}",
    "version": version, "status": "active" if version == 2 else "archived",
    "tenant": "acme", "embedding_model": EMBEDDING_MODEL,
}
```

Decisiones de diseño que merece la pena notar:

- **Metadatos planos:** solo strings y números, sin nulos ni estructuras anidadas (los almacenes vectoriales
  suelen restringir los tipos permitidos).
- **`date` y `effective_day`:** la misma fecha en dos formas. `date` (texto ISO) es para lectura humana;
  `effective_day` (ordinal entero, `date.toordinal()`) es para **filtros de rango** (`$gte`), que necesitan
  números.
- **`employee_type`, `status`, `country`, `access_level` son atributos distintos**, no un único "tipo".
- **`source`** identifica el origen; **`version`** la versión del contenido; **`tenant`** la organización;
  **`embedding_model`** permite **auditar** con qué modelo se generó cada vector.
- **Cada documento es una unidad recuperable completa.** Si fragmentáramos textos largos (*chunking*),
  necesitaríamos un ID por fragmento y conservar un identificador del documento padre; aquí no hace falta.
- Comprobaciones con `assert`: 128 documentos, 128 IDs únicos y que ningún metadato se llame `text` (ese
  nombre está reservado por el adaptador de Pinecone).

Distribución: cada combinación país × tipo × estado tiene **8 documentos** (las 8 categorías), es decir, **8
documentos son elegibles** para "España · personal interno · vigente".

---

## 6. Conectar con Pinecone desde LangChain e ingerir

### Dos herramientas con responsabilidades distintas

`OpenAIEmbeddings` implementa la interfaz de embeddings de LangChain, y `PineconeVectorStore.add_documents`
genera los vectores y hace *upsert*. Pero **la creación y descripción del índice** las hace el **SDK de
Pinecone**, no LangChain, porque `VectorStore` **no es una abstracción de administración de
infraestructura**.

```python
def connect_pinecone():
    client = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    if not client.has_index(INDEX_NAME):
        client.create_index(name=INDEX_NAME, dimension=DIMENSION, metric="cosine",
                            spec=ServerlessSpec(cloud=CLOUD, region=REGION))
    # ... espera (máx. 90 s) a que el índice esté listo y comprueba dimensión y métrica ...
    model = OpenAIEmbeddings(model=EMBEDDING_MODEL, dimensions=DIMENSION, max_retries=2)
    connected_index = client.Index(host=description.host)
    store = PineconeVectorStore(index=connected_index, embedding=model,
                                namespace=NAMESPACE, text_key="text")
    return client, connected_index, model, store
```

Puntos importantes:

- **Se reutiliza el índice por nombre** y **se comprueban dimensión y métrica** antes de usarlo. Si no
  coinciden, se aborta con un mensaje claro (no se sobrescribe nada).
- **Dos modelos con la misma dimensión no son compatibles por ello:** que ambos produzcan 1536 números no
  significa que sus espacios vectoriales se parezcan. El índice debe **dedicarse a un modelo concreto**; por
  eso cada registro guarda `embedding_model` en sus metadatos.
- **`text_key="text"`:** el contenido del documento se guarda como metadato `text` (por eso ese nombre está
  reservado).
- La espera de disponibilidad tiene **límite** (90 s) y lanza `TimeoutError` si se supera.

### Consistencia eventual: confirmar ≠ visible

Las escrituras de Pinecone son **eventualmente consistentes**: que el `upsert` responda "OK" **no garantiza**
que el dato sea visible inmediatamente en un `fetch` o en una búsqueda.

**Ejemplo cotidiano:** es como enviar un paquete por mensajería: el resguardo dice "enviado", pero el
destinatario todavía no lo tiene en la mano. Si asumes que ya está, la siguiente acción falla.

Por eso el notebook **no usa un `time.sleep` fijo** (adivinar cuánto esperar). En su lugar, `wait_for_records`:

1. hace `fetch` de los IDs esperados (o ausentes, tras un borrado) en lotes de 100;
2. comprueba que el **contenido y todos los metadatos** coinciden;
3. hace además una **consulta vectorial** con un embedding de prueba y verifica que los registros aparecen;
4. reintenta cada 2 s hasta un `timeout` de 45 s; si no se confirma, lanza `TimeoutError` (sin afirmar nada
   que no haya leído).

### Ingesta idempotente

```python
vector_store.add_documents(documents=deepcopy(documents), ids=document_ids, batch_size=32)
wait_for_records(NAMESPACE, documents)
```

Al pasar **IDs explícitos**, la operación es un *upsert*: si ejecutas la celda dos veces, los 128 registros
se **reemplazan** en vez de duplicarse (aunque se vuelven a generar los embeddings y se vuelve a pagar por
ello). Resultado real: **`128 registros visibles. IDs explícitos: upsert reproducible.`**

---

## 7. Recuperación semántica con filtros (resultados reales)

Una consulta busca cercanía entre el embedding de la pregunta y los embeddings almacenados. El *score*
devuelto es la **similitud coseno del backend**: **no es una probabilidad** de que el contenido sea correcto
ni es comparable sin más con el de otro proveedor.

La consulta es deliberadamente ambigua:

```python
query = "¿Cuál es la política de vacaciones para empleados?"
```

No especifica país, contrato ni vigencia, así que es razonable que recupere variantes históricas o de otro
país.

### Sin filtro: relevantes pero no todos válidos

Las 4 primeras (`similarity_search`, sin score) son, en orden: **México v2**, **México v1**, **España v2** y
**España v1**, todas de "personal interno". Con score (`k=6`, sin filtro):

| Pos. | Score | Documento |
|---|---|---|
| 1 | 0.762113 | México · interno · v2 |
| 2 | 0.761841 | México · interno · v1 |
| **3** | **0.761427** | **España · interno · v2 (el único elegible)** |
| 4 | 0.760342 | España · interno · v1 |
| 5 | 0.745528 | … |
| 6 | 0.744735 | … |

Los scores 1–4 se diferencian en **una milésima**: la búsqueda semántica **no distingue** bien entre países ni
versiones (el texto es casi idéntico). El documento correcto está en 3.ª posición.

### Con filtro: solo lo elegible

```python
eligible_filter = {
    "$and": [
        {"country": {"$eq": "ES"}},
        {"status": {"$eq": "active"}},
        {"employee_type": {"$eq": "internal"}},
    ]
}
filtered = vector_store.similarity_search_with_score(query, k=6, filter=eligible_filter)
```

| Pos. | Score | Qué es |
|---|---|---|
| 1 | 0.761427 | Vacaciones ES interno v2 ✅ |
| 2 | 0.530394 | Teletrabajo ES interno v2 |
| 3 | 0.430681 | Onboarding ES interno v2 |
| 4 | 0.417420 | Gastos ES interno v2 |
| 5 | 0.398829 | Formación ES interno v2 |
| 6 | 0.369389 | Datos ES interno v2 |

Dos lecturas importantes:

1. **El filtro define qué registros pueden entrar; la similitud solo ordena ese conjunto.** El primer
   resultado es el mismo documento (0.761427), pero ya está en 1.ª posición y no mezclado con inaplicables.
2. **Solo hay 8 documentos elegibles en todo el corpus**, así que al pedir `k=6` el sistema tiene que rellenar
   con políticas de *otros temas* (teletrabajo, onboarding, gastos, formación, datos…). Los scores caen de
   0.76 a 0.37: **son resultados válidos pero mucho menos relevantes**. Un `k` alto con un filtro muy
   restrictivo produce "relleno". En RAG esto importa: pasarías contexto poco útil al LLM.

### Catálogo de operadores de filtro (sintaxis Pinecone)

El notebook muestra cuatro filtros distintos:

| Ejemplo | Filtro | Operadores |
|---|---|---|
| países y vigencia | `country ∈ {ES, MX}` y `status = active` | `$in`, `$eq`, `$and` |
| fecha y categoría | `effective_day ≥ 2026-01-01` y `category = vacaciones` | `$gte`, `$eq`, `$and` |
| categorías alternativas | `status = active` y (`category = teletrabajo` o `seguridad`) | `$or`, `$and` |
| acceso estándar | `access_level = standard` y `country = ES` | `$eq`, `$and` |

Cada base de datos tiene **su propia sintaxis** de filtros (la de Qdrant o Weaviate es distinta, sección 16):
LangChain unifica el `VectorStore`, pero **no traduce los filtros**.

### Filtro por permisos: ¡cuidado!

Un filtro por `access_level` **solo es una condición de consulta**. En una aplicación real debe construirse
**a partir de una identidad autorizada y verificada** por el servidor, **nunca** aceptando permisos
arbitrarios enviados por el usuario. De lo contrario cualquiera escribiría `access_level = restricted`.

---

## 8. Filtrar antes o después de buscar

El notebook compara con datos reales las dos estrategias de la sección 3:

- **Post-filtro en Python:** pide 12 candidatos sin filtro y **después** se queda con los que cumplen las tres
  condiciones.
- **Filtro integrado en la base:** el filtro viaja **dentro** de la consulta.

```python
candidates = vector_store.similarity_search_with_score(query, k=12)
manual_results = [(doc, score) for doc, score in candidates if is_eligible(doc)][:desired_k]
integrated_results = vector_store.similarity_search_with_score(query, k=desired_k, filter=eligible_filter)
```

### Resultado real

| Método | Candidatos recibidos | Resultados | k deseado | Elegibles en el corpus |
|---|---|---|---|---|
| post-filtro Python | 12 | **1** | 6 | 8 |
| filtro en base | 6 | **6** | 6 | 8 |

El post-filtro trajo 12 candidatos y **solo 1** era elegible (los demás serían de otros países, versiones
antiguas o colaboradores externos: son las variantes que la consulta no distingue). Había 8 elegibles en el corpus, pero **no estaban entre los 12 primeros** por
similitud. Además, transfirió 11 candidatos inservibles al cliente.

**Ejemplo cotidiano:** pides "los 6 mejores restaurantes de Madrid" pero tu buscador solo mira los 12 mejores
del mundo y luego tira los que no son de Madrid: te quedas con 1. El filtro integrado equivale a buscar
**dentro de Madrid** desde el principio.

### Matices honestos (los que señala el propio notebook)

- **Aumentar el Top-k reduce el riesgo del post-filtro, pero no lo elimina** con un límite finito.
- **No se presupone el algoritmo interno de Pinecone:** aquí solo se observa su *contrato* de filtrado
  integrado en la consulta. Cómo lo consigue (pre-filtro, filtrado durante el recorrido del índice, etc.)
  afecta al rendimiento y al recall, pero no se puede asegurar desde fuera.
- **La búsqueda integrada tampoco garantiza completar `k`** si hay pocos registros elegibles (por eso la tabla
  incluye "elegibles en corpus": distingue *falta de candidatos* de *falta de documentos*).
- La comparación depende del ranking real: el notebook **no fuerza artificialmente** el déficit.

---

## 9. CRUD: crear, reemplazar, actualizar y borrar

Las cuatro operaciones básicas, con sus particularidades en LangChain + Pinecone:

| Operación | Cómo | Notas |
|---|---|---|
| **Crear** | `add_documents(..., ids=[...])` con un ID nuevo | Añade un registro. |
| **Reemplazar contenido** | `add_documents` con un ID **existente** (upsert) | Reemplaza **vector y metadatos**; se **recalcula el embedding**. No existe un `update_document` en LangChain. |
| **Actualizar solo metadatos** | `index.update(id=..., set_metadata={...})` (SDK de Pinecone) | **No recalcula el vector**; *añade o cambia* los campos indicados, **no reemplaza** todo el diccionario. |
| **Borrar** | `vector_store.delete(ids=[...])` | Se verifica con `fetch`. |

### El experimento del notebook (registro temporal `crud-vacaciones-es`)

1. **Crear** *"Procedimiento de vacaciones urgentes en España: registrar la ausencia … antes de las 09:00…"*
   (versión 1). Se busca con `filter={"doc_id": {"$eq": crud_id}}` → score **0.579256**.
2. **Reemplazar contenido y actualizar metadatos:** se hace upsert del texto nuevo (*"antes de las 10:00 y
   adjuntar la aprobación…"*, versión 2), y después `index.update(... set_metadata={"access_level":
   "restricted", "reviewed_by": "people_ops"})`. Resultado: score **0.575936**, `access_level = restricted`,
   `version = 2`, y aparece el campo nuevo `reviewed_by = people_ops`.
3. **Borrar:** `presente en fetch = False` en el namespace `s5-policies-main`.

Observaciones:

- Entre cada paso se llama a `wait_for_records`: **cada lectura comprueba la visibilidad del cambio**
  (consistencia eventual).
- El borrado se verifica con `fetch`; una **consulta inmediatamente posterior podría seguir viendo** el
  registro (eventual).
- Cambiar solo metadatos (p. ej. marcar un documento como `archived`) **es barato** porque no hay que volver
  a llamar al modelo de embeddings; cambiar el **contenido** exige re-embedding.
- La secuencia es **repetible**: solo opera sobre su ID explícito, dentro del namespace dedicado.

---

## 10. Persistencia y reconexión

El objeto `PineconeVectorStore` **no es el lugar donde viven los registros**: contiene un cliente, la
configuración del embedding y un namespace. Los datos viven **en el servicio remoto**. Por eso:

- Reiniciar Python **no borra** el índice.
- Una **segunda instancia** puede recuperar los registros **sin volver a llamar a `add_documents`**.

```python
new_client = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
host = new_client.describe_index(INDEX_NAME).host
reopened_store = PineconeVectorStore(index=new_client.Index(host=host), embedding=embeddings,
                                     namespace=NAMESPACE, text_key="text")
reopened_store.similarity_search_with_score(query, k=1, filter={"doc_id": {"$eq": "vacaciones-es-internal-v2"}})
```

Resultado real: la nueva instancia devuelve el mismo documento, con el mismo score **0.761427**, sin ninguna
ingesta. (La consulta usa un `doc_id` para que el resultado no dependa de la ordenación de documentos
similares.)

> **El índice deja de ser un objeto temporal del proceso y pasa a formar parte del estado del sistema.**

La diapositiva lista lo que hay que persistir: **vectores**, **contenido y metadatos**, **estructuras de
indexación** y **configuración y estado**. Reiniciar una aplicación, sustituir un nodo o desplegar una nueva
versión **no debería obligarnos a reconstruir toda la colección desde cero**. La permanencia real depende del
recurso remoto, de su política de retención y de las operaciones de borrado; las credenciales deben pertenecer
al proyecto que contiene el índice.

---

## 11. Namespaces y separación entre organizaciones

Un **namespace** *particiona lógicamente* los registros de un índice y **acota las consultas** a esa partición.
Los **mismos IDs pueden coexistir** en namespaces distintos. Dentro de un namespace, los metadatos permiten
restricciones más finas (país, departamento, estado).

El notebook crea dos espacios pequeños con políticas parecidas y reglas distintas:

| Namespace | Documento 1 (score) | Documento 2 (score) |
|---|---|---|
| `s5-tenant-acme` | *"Las vacaciones se aprueban en **PeopleHub** con **15 días** de antelación."* (0.575) | *"En acme, las incidencias del portal…"* (0.259) |
| `s5-tenant-orbit` | *"Las vacaciones se aprueban en **OrbitDesk** con **7 días** de antelación."* (0.565) | *"En orbit, las incidencias del portal…"* (0.244) |

Ambos usan los **mismos IDs** (`tenant-policy-1`, `tenant-policy-2`) y la **misma pregunta** ("¿Cómo solicito
vacaciones?"), pero **cada consulta solo ve su propio namespace**: acme nunca obtiene la política de orbit. El
notebook lo comprueba con un `assert` sobre el campo `tenant`.

Detalles importantes:

- El campo `tenant` se conserva en los metadatos **para auditoría**; **no es lo que produce el aislamiento**
  (lo produce el namespace).
- **La separación lógica no reemplaza la autenticación ni la autorización.** Un servicio con acceso al índice
  debe seleccionar el namespace **según la identidad verificada**; no basta con permitir que el cliente envíe
  un nombre de namespace arbitrario (si no, cualquiera pediría el del vecino).

**Ejemplo cotidiano:** los namespaces son como las habitaciones de un hotel: cada huésped ve su habitación y
las cerraduras separan a unos de otros, pero si la recepción entrega la llave a quien la pide sin comprobar su
identidad, las cerraduras no sirven de nada.

---

## 12. Versiones de colección y migración de embeddings

### Por qué versionar

En producción la colección **no es estática**: llegan `INSERT`, `UPDATE` y `DELETE` continuamente, y cada
uno toca varias piezas a la vez (almacenamiento, índice vectorial, índices de metadatos, cachés, réplicas).

> **La frescura del retrieval depende de cuánto tarda una modificación en convertirse en *searchable*.**

Además, **documento, embedding e índice evolucionan juntos**: si cambia el contenido usado para construir un
embedding, su vector puede dejar de describir correctamente el documento. Preguntas que surgen: ¿qué ocurre
durante la reindexación? ¿cómo evitamos mezclar versiones? ¿podemos reconstruir sin interrumpir las búsquedas?
¿cómo migramos a un nuevo modelo de embeddings?

> **Cambiar de embedding model es también una migración de datos.**

### Versionar permite separar construcción y *serving*

Un nuevo modelo de embeddings, una nueva estrategia de *chunking* o una nueva configuración de índice pueden
exigir reconstruir buena parte del sistema. El patrón de la diapositiva:

```
Queries → routing → Versión A (embeddings + índice) ┐
                  → Versión B (embeddings + índice) ┴→ Métricas
```

Esto habilita **migraciones, benchmarking, canary releases, experimentos A/B y rollback**. Ojo: una base
vectorial *facilita* estas operaciones, pero **el experimento A/B sigue siendo una decisión de arquitectura de
la aplicación** (Pinecone no distribuye tráfico ni evalúa experimentos automáticamente).

### En el notebook

Se separan `s5-policy-v1` y `s5-policy-v2`, cada uno con un documento `urgent-policy` (misma ID, distinto
contenido: límite a las **09:00** frente a las **10:00**):

| Namespace | Score | Contenido |
|---|---|---|
| `s5-policy-v1` | 0.7037 | "…registrar la solicitud antes de las 09:00…" |
| `s5-policy-v2` | 0.7074 | "…registrar la solicitud antes de las 10:00…" |

Un parámetro de la aplicación decide qué versión se consulta (`active_collection_version = 2`); la ruta activa
devuelve la política de las 10:00. Si la versión configurada no estuviera disponible, el notebook **no cambia
automáticamente a otra**: prefiere avisar antes que servir datos de la versión equivocada.

### Procedimiento de migración a otro modelo de embeddings

1. **Recalcular** embeddings de documentos **y de queries** con el nuevo modelo.
2. **Construir** la nueva versión sin tocar la anterior (nuevo namespace o, si cambia la dimensión, **otro
   índice**).
3. **Verificar** calidad y filtros.
4. **Cambiar el enrutamiento**, conservando una **ruta de rollback**.
5. **Limpiar** la versión anterior *después* de validar.

Mezclar modelos en una misma partición puede invalidar la similitud, incluso si la dimensión coincide.

### Dos "versiones" que no hay que confundir

| | `metadata.version` | Namespace `s5-policy-vN` |
|---|---|---|
| **Qué versiona** | Un **registro** (una política concreta). | Una **entrega coherente de todo el corpus**. |
| **Problema que resuelve** | ¿Cuál es la versión vigente de esta política? | ¿Con qué conjunto de embeddings/índice respondo ahora? |

---

## 13. Producción: mucho más que Recall@k y latencia

> **La búsqueda rápida no sirve si el sistema no está disponible.**

Cuando el retrieval forma parte de una aplicación real aparecen requisitos que **no pertenecen al algoritmo
ANN**:

| Requisito | Qué implica |
|---|---|
| **Disponibilidad** | Réplicas y tolerancia a fallos. |
| **Durabilidad** | Almacenamiento persistente y recuperación. |
| **Seguridad** | Autenticación, autorización y aislamiento. |
| **Observabilidad** | Latencia, *throughput*, errores, memoria, recall. |
| **Escalado** | Distribuir datos y consultas. |

> **Producción exige optimizar algo más que Recall@k y latencia.**

### Escalar no significa solo añadir más vectores

Dos sistemas con 100 millones de vectores pueden necesitar arquitecturas completamente diferentes, porque la
escala tiene **cinco dimensiones**:

| Dimensión | Significa |
|---|---|
| **Data scale** | Más registros y embeddings. |
| **Query scale** | Más consultas por segundo. |
| **Update scale** | Más inserts, updates y deletes. |
| **Tenant scale** | Más clientes y aislamiento. |
| **Model scale** | Nuevas representaciones y migraciones. |

---

## 14. El ecosistema: pgvector, Vector Databases y despliegue

### Varias formas de almacenar vectores

Todas pueden resolver *nearest-neighbor search*; **no todas resuelven el mismo problema operacional**. La
diapositiva las sitúa en dos ejes (de "librería embebida" a "servicio persistente" y de "generalista" a
"especializado en retrieval"):

| Familia | Ejemplos | Características |
|---|---|---|
| **Librería de índices** | FAISS, hnswlib | Embebida en tu proceso. Es lo que usamos en la sesión 4. |
| **DB general + vectores** | PostgreSQL + pgvector | Los vectores como una columna más. |
| **Search engine vectorial** | Elasticsearch, OpenSearch | Motor de búsqueda que añade vectores. |
| **Vector DB especializada** | Pinecone, Qdrant, Milvus, Weaviate | Servicio persistente diseñado para retrieval. |

### PostgreSQL + pgvector: cuando los vectores son parte del dato

`pgvector` añade **tipos y operaciones de similitud vectorial dentro de PostgreSQL**. Una tabla `documents`
tiene columnas `id`, `content`, `embedding`, `category_id`, `user_id`, `created_at`… y ofrece a la vez:

- **SQL**: `JOIN`, `WHERE`, transacciones.
- **Vector similarity**.
- Búsqueda **exacta, HNSW o IVFFlat** (los mismos algoritmos de la sesión 4).

> **La búsqueda vectorial se integra dentro del modelo relacional existente, en lugar de introducir
> necesariamente un sistema independiente.**

**Tiene mucho sentido cuando:**

- los **datos ya están en PostgreSQL** (evitas duplicar información y añadir otra infraestructura);
- el retrieval está **ligado al modelo relacional** (joins, permisos, usuarios, productos, transacciones);
- la **escala vectorial es manejable** (latencia y *throughput* caben en la arquitectura PostgreSQL);
- la **consistencia es especialmente importante** (datos estructurados y embeddings en el mismo sistema
  transaccional).

> **Introducir una Vector Database independiente puede añadir complejidad antes de aportar beneficio.**

### ¿Cuándo cobra ventaja una Vector Database especializada?

Cuando conviene separar dos mundos conectados por **sincronización**:

```
SYSTEM OF RECORD (usuarios, pedidos, productos, transacciones)
        ⇄ sincronización ⇄
RETRIEVAL SYSTEM (embeddings, ANN/quantization, metadata filtering, sparse + dense)
```

Razones para separar el *workload* vectorial:

- **Retrieval es carga central:** muchos embeddings y búsquedas concurrentes.
- **Escalado independiente:** perfiles de carga distintos.
- **Corpus muy grande:** *sharding*, réplicas y distribución.
- **Capacidades específicas:** filtros avanzados, multi-vector, sparse + dense, cuantización.

### Tabla comparativa

| Atributo | PostgreSQL + pgvector | Vector Database especializada |
|---|---|---|
| **Modelo principal** | Relacional | Retrieval / vectorial |
| **SQL / joins** | Nativo | Limitado o diferente |
| **Transacciones complejas** | Fortaleza natural | No suele ser el objetivo principal |
| **Vector search** | Integrada | Función central |
| **Escalado del retrieval** | Unido a la arquitectura DB | Puede escalarse independientemente |
| **Operación** | Aprovecha PostgreSQL existente | Nueva infraestructura o servicio |
| **Mejor encaje** | Vector como parte del dominio | Retrieval como *workload* principal |

> **La frontera no es absoluta. La elección debe partir del *workload*, no de la etiqueta "Vector Database".**

### ¿Quién opera la infraestructura?

Self-hosted y managed forman un **continuo**: cambia **quién asume la complejidad operacional**.

```
Local/Docker → VM propia → Kubernetes propio → Managed cloud → Fully managed
```

| Extremo | Qué implica | Ejemplos |
|---|---|---|
| **Self-hosted** | Tú gestionas infraestructura, versiones, red, escalado, seguridad, backups y monitorización. | Milvus / Qdrant *self-hosted* |
| **Managed cloud** | El proveedor gestiona provisioning, mantenimiento, disponibilidad, escalado y actualizaciones. | Qdrant Cloud, Zilliz Cloud |
| **Fully managed** | Casi toda la complejidad operacional la asume el proveedor. | **Pinecone** (la opción del notebook) |

> **La tecnología de búsqueda puede ser similar; lo que cambia es quién asume la complejidad operacional.**

Una misma tecnología ofrece varios modos de despliegue: **Qdrant** (local/Docker, *self-hosted*, *managed
cloud*) y **Milvus** (*standalone*, *distributed*, Zilliz Cloud). Por eso **"¿qué base de datos utilizamos?" y
"¿cómo la desplegamos?" son dos preguntas distintas**, cuyas respuestas dependen de: quién lo mantiene, dónde
se almacenan los datos, cómo escala, qué SLA necesitamos y qué restricciones de red o *compliance* existen.

---

## 15. Diseñar y elegir una arquitectura de recuperación

### De un documento a una colección *searchable*

```
Fuente → Extracción → Chunking → Embeddings → Vector Database
          (a lo largo del camino se guardan: contenido, IDs, metadatos, permisos, versión)
```

Se producen a la vez una **representación vectorial para recuperar** y un **registro estructurado para
gestionar**. Como dice la diapositiva: **la calidad del sistema empieza mucho antes de ejecutar la primera
query.**

### De una query a un resultado recuperado

```
Query → Embedding → Metadata/access filters → ANN Search → Top-k candidates → Reranking → Resultados
                                               ↑ sparse retrieval    ↑ business rules   ↑ personalization
```

Enlaza con la sesión 3 (sparse + dense, reranking). La idea: **la Vector Database ocupa una posición central,
pero el retrieval sigue siendo un *pipeline*, no una única llamada a `similarity_search()`.**

### `VectorStore`: una interfaz común sobre sistemas diferentes

LangChain ofrece una interfaz relativamente homogénea:

```python
vector_store.add_documents(...)
vector_store.similarity_search(...)
vector_store.similarity_search_with_score(...)
```

sobre PostgreSQL + pgvector, Pinecone, Qdrant, Milvus, Weaviate… Pero **no hace equivalentes las bases de
datos subyacentes**: siguen siendo distintos los índices, el filtrado, la consistencia, el escalado, los
costes, el ANN y las operaciones (¡ya vimos que los filtros tienen sintaxis propia y que la consistencia
eventual de Pinecone obligó a escribir `wait_for_records`!).

> **Una abstracción simplifica el código cliente; no elimina la arquitectura del sistema.**

### El patrón de consulta debe influir en el diseño

No basta con preguntar cuántos vectores tendremos: hay que saber **cómo serán las queries**.

| Patrón de consulta | Qué domina |
|---|---|
| "cualquier documento parecido" | Domina la **búsqueda vectorial**. |
| "documentos parecidos **del usuario X**" | Filtro **altamente selectivo**. |
| "productos parecidos en España, categoría Y, precio < 100 €" | **Varios filtros** estructurados. |
| "corpus global con permisos por documento" | **El filtrado forma parte de la seguridad.** |

### La arquitectura nace de las restricciones

Se evalúan cinco frentes y de ahí salen las opciones:

| Frente | Pregunta |
|---|---|
| **Modelo de datos** | ¿Relaciones y transacciones o retrieval? |
| **Escala** | ¿Vectores, queries y actualizaciones? |
| **Query patterns** | ¿Filtros, permisos, búsquedas híbridas? |
| **Operación** | ¿Operar infraestructura o consumir un servicio? |
| **No funcionales** | Latencia, disponibilidad, seguridad, residencia de datos, coste. |

Opciones resultantes: **relacional + vector**, **Vector DB dedicada**, **self-hosted distribuida** o **managed
service**. Y siempre: **evaluación → benchmark → decisión**.

> **Elegir una Vector Database no debería ser el punto de partida. Debería ser una consecuencia del diseño.**

### Del índice al sistema de recuperación

Las capas anidadas de la última diapositiva de contenido:

```
Retrieval System ⊃ Vector Store / Database ⊃ Vector Index ⊃ Embedding
Representar → Indexar → Almacenar → Recuperar → Evaluar
```

> Un sistema de *retrieval* se diseña para encontrar la información correcta, para el usuario correcto, bajo
> las restricciones correctas y con un coste operacional aceptable.

---

## 16. Material adicional: Qdrant, Milvus y Weaviate con Docker

La carpeta [`extras Docker con distintas BBDD Vectoriales/`](./extras%20Docker%20con%20distintas%20BBDD%20Vectoriales/)
contiene tutoriales **opcionales, para hacer fuera de la sesión**. Cada subcarpeta es autocontenida (su propio
entorno y despliegue) y **no forma parte del flujo del notebook principal**. Recomendación del propio material:
**ejecutar un tutorial cada vez** para simplificar recursos y puertos.

**Docker en dos líneas:** ejecuta servicios empaquetados en *contenedores*; **Compose** lee un
`docker-compose.yml` y coordina su arranque; un **volumen** conserva los datos aunque se detenga el
contenedor. No hace falta Kubernetes ni crear imágenes.

| Subcarpeta | Servicio | Imagen fijada | Particularidades |
|---|---|---|---|
| `qdrant_local/` | **Qdrant** | `qdrant/qdrant:v1.19.1` | REST en `6333`, gRPC en `6334`, volumen `qdrant_data`. Filtros de *payload*. |
| `milvus_local/` | **Milvus standalone** | `milvusdb/milvus:v3.0.1` | Con **etcd y MinIO** (Compose oficial). Necesita más recursos: al menos **4 núcleos y 8 GB de RAM** para Docker. Oferta gestionada: **Zilliz Cloud**. |
| `weaviate_local/` | **Weaviate** | `cr.weaviate.io/semitechnologies/weaviate:1.39.5` | Autenticación por clave y embeddings externos. |

Puntos comunes:

- Los puertos se enlazan a `127.0.0.1` (**solo acceso desde la propia máquina**; nunca los expongas
  públicamente, no hay autenticación en el ejemplo de Qdrant).
- Los scripts (`example_*_langchain.py`) usan **LangChain + `OpenAIEmbeddings`** (1536 dims, coseno): **la base
  de datos es local, pero los embeddings se envían a OpenAI** (consumo de API).
- El corpus es ficticio: por ejemplo, en Qdrant se ingieren 3 políticas de vacaciones (ES activa, MX activa, ES
  archivada) y se comparan búsquedas **con y sin filtro**.
- **Qdrant en LangChain** guarda los atributos dentro de `metadata` en el *payload*, por eso el filtro usa
  `metadata.country` en lugar de `country`. Los IDs son **UUID deterministas** (`uuid5`), así que repetir la
  ejecución hace *upsert*. Además, la colección se crea con `size=1536` y `distance=COSINE`.
- `docker compose down` conserva el volumen; **`docker compose down -v` borra los datos** de ese despliegue.
- Como en el resto de la sesión, los tutoriales piden `cp .env.example .env`, pero ese fichero de ejemplo
  **no existe** en el repositorio.

**Valor didáctico:** el mismo problema (ingerir 3 documentos, buscar con/sin filtro) resuelto con tres
productos diferentes ilustra de forma práctica la frase de la sección 15: la interfaz de LangChain se parece,
pero **el filtro, la consistencia y el despliegue son propios de cada sistema**.

---

## 17. Resumen final

1. **Un índice vectorial es una estructura de búsqueda, no un sistema completo de datos.** Una Vector Database
   la envuelve con persistencia, CRUD, metadatos, filtrado, concurrencia, seguridad y operación.
2. La unidad de almacenamiento es el **registro `{id, embedding, content, metadata}`**: el embedding busca, el
   contenido se interpreta, los metadatos deciden la elegibilidad y el ID mantiene la identidad.
3. **La similitud determina relevancia; los filtros determinan elegibilidad.** Metadatos y filtros forman parte
   del retrieval real, no son un extra.
4. **Filtrar dentro de la consulta** (pre-filter/integrado) evita el problema del **post-filtro**, que en el
   notebook devolvió **1 de 6** resultados aunque existían 8 elegibles. Con filtros muy restrictivos, un `k`
   grande produce relleno de baja relevancia (scores de 0.76 a 0.37).
5. **Las escrituras pueden ser eventualmente consistentes:** confirmar un `upsert` no implica que sea visible;
   hay que **verificar** (`wait_for_records`) en vez de dormir un tiempo fijo.
6. **CRUD con IDs estables:** el upsert con el mismo ID reemplaza vector y metadatos (re-embedding); actualizar
   solo metadatos no recalcula el vector; el borrado se verifica.
7. **Persistencia:** el `VectorStore` es un *cliente*; los datos viven en el servicio. Una nueva instancia
   recupera todo sin volver a ingerir.
8. **Namespaces** separan lógicamente datos (tenants, versiones), pero **no sustituyen a la autenticación y
   autorización**.
9. **Cambiar de modelo de embeddings es una migración de datos:** recalcular, construir la nueva versión al
   lado, verificar, enrutar con *rollback* y limpiar después. El A/B es responsabilidad de la aplicación.
10. **Producción exige más que Recall@k y latencia:** disponibilidad, durabilidad, seguridad, observabilidad y
    escalado (en cinco dimensiones: datos, queries, updates, tenants, modelos).
11. **pgvector y las Vector Databases especializadas tienen "centros de gravedad" distintos:** pgvector cuando
    el vector es parte de un dominio relacional; una Vector DB cuando el retrieval es el *workload* principal.
    Y **"qué base de datos" y "cómo la desplegamos" son decisiones distintas.**
12. **La arquitectura debe elegirse desde requisitos y *benchmarks*,** no desde la etiqueta de un producto. Un
    `VectorStore` común de LangChain simplifica el código, pero **no elimina la arquitectura del sistema**.

---

## 18. ¿Qué sigue después?

La frase que resume la sesión es:

> **El índice optimiza la búsqueda. La base de datos gestiona el ciclo de vida de la información.**

La secuencia del tema avanza así: en las sesiones 1–3 aprendimos a **representar y comparar**; en la 4, a
**indexar para buscar rápido**; en ésta, a **almacenar, filtrar, actualizar y operar**. Falta responder:
**¿cómo sabemos que el sistema recupera lo correcto?** Eso es la siguiente sesión (**construcción y evaluación
de sistemas de recuperación**, carpeta [`06-Const-evaluacion`](../06-Const-evaluacion/)), y después la de
**Retrieval Augmented Generation** ([`07-RAG`](../07-RAG/)), donde los fragmentos recuperados se entregan a un
modelo de lenguaje.

```
representar → indexar → almacenar → recuperar → evaluar → generar (RAG)
```

### Preguntas para repasar

1. ¿Qué cuatro preguntas no contesta un índice ANN y sí una Vector Database? Ponle un ejemplo a cada una.
2. ¿Por qué un documento muy similar a la consulta puede no ser un resultado válido? ¿Quién decide la
   elegibilidad, la similitud o los filtros?
3. En el notebook, el post-filtro sobre un Top-12 devolvió 1 resultado de 6 deseados, aunque había 8 elegibles.
   ¿Por qué? ¿Bastaría con subir `k`? ¿Qué garantías no da tampoco el filtro integrado?
4. Al pedir `k=6` con un filtro que solo admite 8 documentos, los scores bajan de 0.76 a 0.37. ¿Qué implica
   eso para un sistema RAG que pasa esos 6 fragmentos a un LLM?
5. ¿Por qué el notebook usa `wait_for_records` en lugar de `time.sleep(5)`? ¿Qué es la consistencia eventual?
6. ¿Qué diferencia hay entre reemplazar el contenido de un registro y actualizar solo sus metadatos? ¿Cuál es
   más caro y por qué?
7. Un namespace por cliente aísla los datos… ¿es suficiente para la seguridad de un SaaS multi-cliente? ¿Qué
   más hace falta?
8. Quieres pasar de `text-embedding-3-small` (1536 dims) a otro modelo también de 1536 dims. ¿Puedes escribir
   los nuevos vectores en el mismo namespace? ¿Qué pasos seguirías?
9. Tu aplicación ya usa PostgreSQL con 2 millones de filas y necesita búsqueda semántica sobre una columna de
   texto, con permisos por usuario. ¿Partirías de pgvector o de una Vector DB dedicada? ¿Qué cambiaría con
   500 millones de vectores y 5.000 consultas por segundo?
10. ¿Por qué "¿qué base de datos usamos?" y "¿cómo la desplegamos?" son preguntas distintas? Da un ejemplo
    con Qdrant o Milvus.
