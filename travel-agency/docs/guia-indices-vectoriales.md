# Guía — Índices vectoriales: Flat, HNSW, IVF e IVF-PQ (y cuál usar en Travel Agency)

> Guía de estudio para entender **cómo se buscan los vecinos más cercanos** cuando un RAG tiene muchos
> documentos, y para justificar la decisión de índice del RAG de [`PROYECTO.md`](../PROYECTO.md).
>
> Complementa la [sesión 4 del tema 5](../../05_rag_langchain/clases/04-indexacion-busq-efic/EXPLICACION_sesion_04.md)
> (Exact, HNSW, IVF, IVF-PQ). El código usa los mismos nombres que su notebook
> (`faiss.IndexFlatIP`, `IndexHNSWFlat`, `IndexIVFFlat`, `IndexIVFPQ`).

## Índice

1. [El problema de partida](#1-el-problema-de-partida)
2. [Búsqueda exacta vs ANN](#2-búsqueda-exacta-vs-ann)
3. [Flat: comparar con todo](#3-flat-comparar-con-todo)
4. [IVF: buscar solo en los barrios cercanos](#4-ivf-buscar-solo-en-los-barrios-cercanos)
5. [HNSW: un grafo con autopistas](#5-hnsw-un-grafo-con-autopistas)
6. [PQ e IVF-PQ: comprimir los vectores](#6-pq-e-ivf-pq-comprimir-los-vectores)
7. [Comparación y por qué cada uno gana en su terreno](#7-comparación-y-por-qué-cada-uno-gana-en-su-terreno)
8. [FAISS "a pelo": qué significa y qué le falta](#8-faiss-a-pelo-qué-significa-y-qué-le-falta)
9. [La opción sencilla: FAISS `IndexFlatIP` (paso a paso)](#9-la-opción-sencilla-faiss-indexflatip-paso-a-paso)
10. [Aplicación a Travel Agency](#10-aplicación-a-travel-agency)
11. [Glosario](#11-glosario)

---

## 1. El problema de partida

En un RAG, cada trozo de documento (**chunk**) se convierte en un **vector** (embedding): una lista de
números, por ejemplo 1.024 con `bge-m3`. La pregunta del usuario también se convierte en un vector. Buscar
"los pasajes que hablan de lo mismo que la pregunta" es buscar **los vectores más parecidos** al de la
pregunta: los **k vecinos más cercanos** (*k-nearest neighbors*, k-NN).

```
"¿Qué indemnización hay por 4 h de retraso?"  ──embedding──►  q = [0.12, -0.03, …, 0.40]   (1.024 números)

Colección:  chunk 1 → x₁ = [ … ]
            chunk 2 → x₂ = [ … ]
            …
            chunk N → x_N = [ … ]

Objetivo:   los k chunks cuyo xᵢ se parece más a q  (k = 5, 10, 50…)
```

"Parecerse" se mide con una **similitud**: normalmente el **coseno** o el **producto escalar** (*inner
product*, IP). Si los vectores están **normalizados** (longitud 1), los dos dan exactamente lo mismo.

La pregunta de esta guía es: **¿cómo encontrar esos k vecinos sin tardar una eternidad cuando N es enorme?**
Y la respuesta depende, sobre todo, de **cuánto vale N**.

---

## 2. Búsqueda exacta vs ANN

### Búsqueda exacta

Comparar `q` con **todos** los vectores, ordenar y quedarse con los k mejores. Siempre acierta, pero el
trabajo crece en línea recta con N: el doble de documentos, el doble de tiempo.

### ANN (*Approximate Nearest Neighbors*)

**ANN = vecinos más cercanos aproximados.** En lugar de mirar todo, se construye de antemano una
**estructura** (un índice) que permite mirar **solo una parte prometedora** de la colección. A cambio,
**a veces se escapa algún vecino verdadero**.

**Ejemplo cotidiano:** buscas el bar más cercano en una ciudad.

- **Exacto:** mides la distancia a *todos* los bares de la ciudad y eliges el menor. Infalible y lentísimo.
- **ANN:** miras solo los bares de tu barrio y de los barrios de al lado. Casi siempre aciertas; muy de vez
  en cuando el más cercano estaba justo al otro lado del límite de un barrio que no miraste.

### Cómo se mide "cuánto se escapa": recall@k

$$\text{recall@k} = \frac{\text{nº de vecinos verdaderos que el ANN encontró en su top-k}}{k}$$

Ejemplo: la búsqueda exacta dice que el top-10 es `{3, 8, 15, 21, 40, 52, 77, 90, 101, 130}`. El ANN
devuelve `{3, 8, 15, 21, 40, 52, 77, 90, 101, 999}`. Ha acertado 9 de 10 → **recall@10 = 0,9**.

Todos los índices ANN tienen **una perilla** que mueve el equilibrio:

```
   más rápido  ◄──────────── perilla ────────────►  más preciso
   recall 0,80                                     recall 0,99
   0,2 ms                                          2 ms
```

En HNSW la perilla se llama `efSearch`; en IVF, `nprobe`. Las veremos enseguida.

### ¿Por qué en un RAG se tolera perder algún vecino?

- El LLM recibe 3–10 pasajes. Si el 9.º y el 10.º cambian por otros casi igual de buenos, la respuesta
  apenas cambia.
- Con **búsqueda híbrida** (BM25 + denso) y **reranker**, lo que importa es que el pasaje bueno esté
  entre los ~50 candidatos; el orden fino lo decide el reranker.

Pero ojo: **si N es pequeño, no hay nada que ganar** aproximando. Eso es lo que justifica la tabla de la
regla práctica.

---

## 3. Flat: comparar con todo

### Qué es

**Flat** ("plano") = **sin estructura**. Los vectores se guardan tal cual, uno detrás de otro, y cada
consulta se compara con todos. En FAISS:

| Índice | Similitud | Cuándo |
|---|---|---|
| `IndexFlatIP` | Producto escalar (*Inner Product*): **mayor = más parecido** | Vectores normalizados → equivale a coseno. Lo que usa el máster |
| `IndexFlatL2` | Distancia euclídea al cuadrado: **menor = más parecido** | Es el que usa LangChain por defecto |

> Con vectores normalizados, L2 y coseno ordenan **igual**: $\|a-b\|^2 = 2 - 2\cos(a,b)$. Solo cambia el
> número que ves como "score" (y su sentido: en L2 menos es mejor).

### Cómo funciona, con un ejemplo de juguete

Vectores de 2 dimensiones (normalizados) y una consulta:

| Chunk | Vector | `q · x` con `q = [0.8, 0.6]` |
|---|---|---|
| A | [1.0, 0.0] | 0.80 |
| B | [0.6, 0.8] | 0.96 |
| C | [0.0, 1.0] | 0.60 |
| D | [-0.6, 0.8] | 0.00 |

Top-2 = **B (0,96), A (0,80)**. Eso es todo: multiplicar, sumar, ordenar. FAISS lo hace con
instrucciones vectorizadas (SIMD/BLAS), muy rápido, pero **sigue mirando las N filas**.

### Cuánto cuesta

- **Memoria:** `N × d × 4 bytes` (cada número es un `float32` de 4 bytes).
- **Tiempo:** proporcional a `N × d`. En la práctica, con una consulta suelta, el límite es **leer toda esa
  memoria**: el tiempo crece casi exactamente igual que el tamaño del índice.

Con `d = 1024` (bge-m3), **órdenes de magnitud** en una CPU normal:

| N (chunks) | Memoria Flat | Tiempo aprox. por consulta |
|---|---|---|
| 10.000 | 40 MB | ~1–2 ms |
| 50.000 | 200 MB | ~5–20 ms |
| 1.000.000 | 4 GB | ~200–500 ms |
| 10.000.000 | 41 GB | segundos |
| 1.000.000.000 | 4 TB | no cabe en RAM |

> Estas cifras dependen mucho del hardware: mídelo con tu máquina (el notebook de la sesión 4 tiene un
> `benchmark_store` que sirve tal cual).

### Ventajas e inconvenientes

| ✅ Ventajas | ❌ Inconvenientes |
|---|---|
| **Recall 100 %**: es la referencia con la que se mide a los demás | Lento cuando N es muy grande |
| Nada que entrenar ni ajustar (cero parámetros) | Ocupa todo: 4 bytes por número |
| Añadir y **borrar** vectores es trivial | |
| **Filtrar** es trivial y exacto: comparas solo con los permitidos | |
| Se construye al instante | |

**Idea clave:** Flat no es "el índice malo". Es **el correcto mientras te lo puedas permitir**. Los demás
existen solo porque, a partir de cierto N, Flat se vuelve demasiado lento o no cabe en memoria.

---

## 4. IVF: buscar solo en los barrios cercanos

### Qué es

**IVF = Inverted File** (fichero invertido). La idea: **dividir el espacio en zonas** y, al buscar,
**mirar solo las zonas más cercanas** a la consulta.

### Cómo se construye

1. **Entrenar:** se aplica **k-means** a los vectores para encontrar `nlist` **centroides** (el "centro"
   de cada zona). Por ejemplo, `nlist = 200`.
2. **Repartir:** cada vector se guarda en la **lista** de su centroide más cercano. Quedan 200 listas, cada
   una con los vectores de "su barrio".

### Cómo se busca

1. Comparar `q` con los **200 centroides** (barato: son solo 200).
2. Elegir los `nprobe` centroides más cercanos (por ejemplo, `nprobe = 8`).
3. Hacer búsqueda exacta **solo dentro de esas 8 listas**.

### Ejemplo con números

N = 1.000.000 vectores, `nlist = 1.000` → unas 1.000 vectores por lista.

| `nprobe` | Comparaciones por consulta | Fracción del total | Recall típico |
|---|---|---|---|
| 1 | 1.000 centroides + ~1.000 vectores | 0,2 % | bajo (≈ 0,4–0,6) |
| 8 | 1.000 + ~8.000 | 0,9 % | medio-alto (≈ 0,85–0,9) |
| 64 | 1.000 + ~64.000 | 6,5 % | alto (≈ 0,97–0,99) |
| 1.000 | todo | 100 % | 1,0 (= Flat, pero más lento) |

Con `nprobe = 8` haces **unas 100 veces menos trabajo** que Flat.

### Por qué se pierden vecinos: el problema de la frontera

**Ejemplo cotidiano:** una biblioteca ordenada por secciones (Historia, Viajes, Derecho…). Si buscas un
libro sobre "derecho aéreo de los pasajeros", vas a Derecho. Pero puede que el mejor libro esté
catalogado en Viajes. Si solo miras **una** sección (`nprobe = 1`), te lo pierdes. Si miras las 3 más
cercanas (`nprobe = 3`), probablemente lo encuentras.

En vectores igual: un punto puede estar cerca de `q` pero **justo al otro lado de la frontera** entre dos
zonas. Por eso `nprobe > 1`.

```
       zona A        │       zona B
                     │
          · ·    q ● │ ★  ← vecino real de q, pero cae en la zona B
        ·   ·        │   ·
                     │
   nprobe=1: solo mira A → pierde ★
   nprobe=2: mira A y B  → encuentra ★
```

### Parámetros

| Parámetro | Qué es | Regla práctica |
|---|---|---|
| `nlist` | Nº de zonas (centroides) | Entre `√N` y `16·√N`. El notebook usa `≈ √N` entre 64 y 512 |
| `nprobe` | Zonas que se miran al buscar | **La perilla**: subir hasta lograr el recall que necesitas |

### Ventajas e inconvenientes

| ✅ Ventajas | ❌ Inconvenientes |
|---|---|
| Mucho más rápido que Flat con N grande | Hay que **entrenar** (k-means) con datos representativos |
| Casi no ocupa más memoria que Flat | Si los datos cambian mucho, los centroides se quedan viejos → reentrenar |
| Permite borrar vectores | Con N pequeño las zonas son tan pequeñas que no compensa |
| Es la base para comprimir con PQ (sección 6) | A igual velocidad suele tener **menos recall** que HNSW |

---

## 5. HNSW: un grafo con autopistas

### Qué es

**HNSW = Hierarchical Navigable Small World** (mundo pequeño navegable jerárquico). Es un **grafo**: cada
vector es un nodo conectado con unos cuantos vecinos parecidos. Para buscar, **saltas de vecino en
vecino** acercándote cada vez más a la consulta.

### La idea del "mundo pequeño"

**Ejemplo cotidiano:** "seis grados de separación". Si quieres hacer llegar una carta a un desconocido de
otro país, se la das al conocido tuyo que "más se parezca" al destinatario, y él a su conocido más
parecido… En pocos saltos llega. No hace falta conocer a todo el mundo, solo a unos cuantos bien elegidos.

### La parte "jerárquica": las autopistas

Saltar de vecino en vecino desde un punto cualquiera puede requerir muchos pasos. HNSW lo arregla con
**varias capas**, como una red de carreteras:

```
Capa 2 (autopistas):    ●───────────────────●───────────────●        pocos nodos, enlaces largos
                        │                                   │
Capa 1 (nacionales):    ●─────●─────────●───●─────●─────────●        más nodos
                        │     │         │   │     │         │
Capa 0 (calles):        ●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●        TODOS los nodos, enlaces cortos
```

- La **capa 0** tiene **todos** los vectores.
- Cada capa superior tiene una **fracción aleatoria** de los de abajo (cada vez menos).
- **Buscar:** entras por arriba, avanzas por la autopista hasta el nodo más cercano a `q`, bajas de capa,
  sigues afinando por las nacionales y terminas en las calles de la capa 0.

Es como ir de Madrid a una calle de Sevilla: autovía hasta Sevilla, avenidas hasta el barrio, calles hasta
el portal. Nunca recorres "todas las calles de España".

### Ejemplo de búsqueda paso a paso

Buscamos el vecino de `q` (en una capa, simplificado):

1. Empiezas en el nodo **E** (punto de entrada). Similitud con `q`: 0,30.
2. Miras los vecinos de E: F (0,45), G (0,20). El mejor es **F** → saltas a F.
3. Vecinos de F: H (0,70), E (0,30). Saltas a **H**.
4. Vecinos de H: I (0,82), F. Saltas a **I**.
5. Vecinos de I: J (0,79), H (0,70). Ninguno mejora 0,82 → **paras**: I es el resultado.

Has mirado unos 8 nodos en lugar de N. El riesgo: que exista un nodo de 0,95 al que no se llega por ese
camino (un **mínimo local**). Para reducirlo, HNSW no sigue un solo camino sino que mantiene una **lista de
`efSearch` candidatos** a la vez: cuanto mayor, más caminos explora.

### Parámetros

| Parámetro | Cuándo actúa | Qué hace | Valores típicos |
|---|---|---|---|
| `M` | Construcción | Nº de enlaces por nodo. Más enlaces = mejor recall, más memoria | 16–64 (el notebook usa 16) |
| `efConstruction` | Construcción | Lo exhaustivo que es al crear el grafo. Más = mejor grafo, construcción más lenta | 100–400 (el notebook usa 200) |
| `efSearch` | Búsqueda | **La perilla**: candidatos explorados. Debe ser ≥ k | 32–256 |

### Ventajas e inconvenientes

| ✅ Ventajas | ❌ Inconvenientes |
|---|---|
| **El mejor equilibrio recall/velocidad** en la mayoría de pruebas: ~1 ms con recall 0,95–0,99 en millones de vectores | **Más memoria** que Flat: los vectores completos + los enlaces (≈ `2·M·4` bytes extra por vector en la capa 0) |
| **No hay que entrenar**: se pueden ir añadiendo vectores | Construir es lento con millones de vectores |
| El tiempo de búsqueda crece muy despacio con N (≈ logarítmico) | En FAISS **no se pueden borrar** vectores (hay que reconstruir) |
| | Con **filtros muy restrictivos** el grafo se "rompe": los caminos pasan por nodos prohibidos y el recall cae |

---

## 6. PQ e IVF-PQ: comprimir los vectores

IVF y HNSW resuelven el **tiempo**. Pero si tienes 1.000 millones de vectores de 1.024 dimensiones, el
problema es otro: **4 TB no caben en RAM**. Ahí entra la compresión.

### PQ (*Product Quantization*): la idea

**Ejemplo cotidiano: las imágenes GIF.** Una foto tiene millones de colores posibles (3 bytes por píxel).
Un GIF elige una **paleta de 256 colores** y guarda cada píxel como **el número del color más parecido de
la paleta** (1 byte). La imagen se ve casi igual y ocupa un tercio.

PQ hace lo mismo con los vectores, pero por **trozos**:

1. **Cortar** cada vector de `d` dimensiones en `m` sub-vectores. Ej.: `d = 1024`, `m = 64` → 64 trozos
   de 16 números.
2. **Entrenar una paleta** (k-means con 256 centroides) **para cada trozo**.
3. **Codificar:** cada trozo se sustituye por **el número (0–255) de su centroide más cercano** → 1 byte.

```
Vector original (1.024 float32 = 4.096 bytes):
[0.12, -0.40, …, 0.33 | 0.05, 0.71, …, -0.2 | … | 0.9, 0.1, …, 0.0]
 └──── trozo 1 ────┘   └──── trozo 2 ────┘       └──── trozo 64 ──┘
          ▼                     ▼                         ▼
       paleta 1              paleta 2                  paleta 64
          ▼                     ▼                         ▼
Código PQ:  [ 17,   203,   …,   88 ]          → 64 bytes   (64 veces más pequeño)
```

### Ejemplo de juguete

Vector de 4 dimensiones, `m = 2` trozos de 2 números, paletas de 4 entradas (2 bits):

| | Paleta del trozo 1 | Paleta del trozo 2 |
|---|---|---|
| 0 | [0.0, 0.0] | [0.0, 1.0] |
| 1 | [1.0, 0.0] | [1.0, 1.0] |
| 2 | [0.0, 1.0] | [0.5, 0.5] |
| 3 | [1.0, 1.0] | [1.0, 0.0] |

Vector `x = [0.9, 0.1, 0.6, 0.4]`:

- Trozo 1 `[0.9, 0.1]` → el más parecido es `[1.0, 0.0]` → **1**
- Trozo 2 `[0.6, 0.4]` → el más parecido es `[0.5, 0.5]` → **2**

Se guarda `x ≈ [1, 2]`. Al buscar, `x` "vale" `[1.0, 0.0, 0.5, 0.5]`: parecido, pero **no idéntico**.
Esa diferencia es el **error de cuantización**: las similitudes son aproximadas y el orden de los
resultados se desordena un poco.

### Por qué el producto de paletas es tan potente

Con 64 trozos y 256 entradas por paleta, el número de "vectores representables" es $256^{64}$ (un número
astronómico), pero solo guardas 64 paletas pequeñas. Eso es lo de *Product* en el nombre.

### IVF-PQ: las dos ideas juntas

- **IVF** decide **dónde mirar** (solo `nprobe` zonas) → menos tiempo.
- **PQ** decide **cómo guardar** cada vector (unos bytes) → menos memoria.

Para 1.000 millones de vectores de 1.024 dimensiones:

| Índice | Bytes por vector | Total |
|---|---|---|
| Flat | 4.096 | ~4 TB |
| HNSW (M=32) | ~4.096 + 256 | ~4,3 TB |
| **IVF-PQ** (m=64) | ~64 + 8 (id) | **~72 GB** |

Pasas de "imposible" a "un servidor grande". Ese es el **único** motivo de peso para usar IVF-PQ.

### El truco para recuperar precisión: re-ranking con vectores exactos

Como PQ desordena un poco el top, se suele pedir más resultados (p. ej. 100) con IVF-PQ y **reordenarlos
con los vectores originales** (que pueden estar en disco). FAISS lo ofrece con `IndexRefineFlat`. Es la
misma filosofía que el reranker del RAG: **etapa barata y aproximada → etapa cara y precisa sobre pocos**.

### Ventajas e inconvenientes

| ✅ Ventajas | ❌ Inconvenientes |
|---|---|
| Memoria **10–100 veces menor** | **Pierde precisión** (recall más bajo que HNSW o IVFFlat) |
| Escala a miles de millones de vectores | Hay que **entrenar** IVF **y** PQ, con muchos datos (PQ con 8 bits quiere ≳ 10.000 vectores de entrenamiento) |
| Muy rápido (compara bytes, no floats) | Más parámetros que ajustar: `nlist`, `nprobe`, `m`, `nbits` |
| | `d` tiene que ser divisible por `m` |

---

## 7. Comparación y por qué cada uno gana en su terreno

### Tabla resumen

| | Flat | IVF | HNSW | IVF-PQ |
|---|---|---|---|---|
| **Recall** | 100 % | alto (según `nprobe`) | muy alto (según `efSearch`) | medio-alto |
| **Velocidad con N grande** | lenta | rápida | **muy rápida** | muy rápida |
| **Memoria** | 4·d bytes/vector | ≈ Flat | Flat + enlaces | **unos pocos bytes/vector** |
| **¿Entrenar?** | no | sí (k-means) | no | sí (k-means + PQ) |
| **Construcción** | instantánea | rápida | lenta | media |
| **Borrar vectores (FAISS)** | sí | sí | **no** | sí |
| **Filtrar por metadatos** | trivial y exacto | razonable | delicado si el filtro es estricto | razonable |
| **Parámetros** | ninguno | `nlist`, `nprobe` | `M`, `efConstruction`, `efSearch` | `nlist`, `nprobe`, `m`, `nbits` |

### La regla práctica, justificada

| Nº de vectores | Índice | Por qué |
|---|---|---|
| **< ~1 millón** | **Flat** | Cabe en RAM (≤ 4 GB a 1.024 dims) y tarda milisegundos o, como mucho, unas décimas. **Recall perfecto, cero parámetros, filtros exactos.** No hay nada que ganar aproximando |
| **1 – ~50 millones** (si cabe en RAM) | **HNSW** | Flat ya tarda segundos; HNSW responde en ~1 ms con recall ≈ 0,98. La memoria extra de los enlaces es asumible |
| **Muchos millones o poca RAM** | **IVF / IVF-PQ** | Los vectores completos no caben (o cuestan demasiado). IVF-PQ comprime 50–100× y acepta perder algo de recall, que se recupera con re-ranking |

Las fronteras son **orientativas**: dependen de la dimensión (con 384 dims, Flat aguanta ~3 veces más que
con 1.024), del hardware y de tu **presupuesto de latencia**.

### El argumento que más pesa en un RAG: la latencia del LLM

En un RAG, el LLM tarda **segundos** en generar la respuesta (más aún en local con Ollama). Que la búsqueda
tarde 10 ms (Flat) o 1 ms (HNSW) **no lo nota nadie**. Optimizar el índice solo tiene sentido cuando la
búsqueda empieza a pesar en el tiempo total, y eso no pasa hasta tener muchos cientos de miles de chunks.

### Árbol de decisión

```
¿Cuántos chunks vas a indexar?
│
├─ < ~1 M ─────────────────────────────► Flat  (IndexFlatIP)
│
└─ ≥ ~1 M
   │
   ├─ ¿Caben los vectores completos en RAM (N × d × 4 bytes + margen)?
   │   │
   │   ├─ Sí ──► ¿Necesitas borrar o filtrar mucho?
   │   │          ├─ No ──► HNSW
   │   │          └─ Sí ──► HNSW en una base vectorial con filtrado (Qdrant, Milvus…) o IVF
   │   │
   │   └─ No ──► IVF-PQ (+ re-ranking con vectores exactos)
```

---

## 8. FAISS "a pelo": qué significa y qué le falta

### Qué es FAISS

[FAISS](https://github.com/facebookresearch/faiss) es una **librería** de Meta para buscar vectores. Hace
**una cosa** y la hace muy bien: dado un vector, devolver los **números de fila** (ids enteros) de los más
parecidos. Implementa todos los índices de esta guía.

"FAISS **a pelo**" quiere decir usar la librería **directamente**, sin una base de datos vectorial
alrededor. Hay tres niveles:

| Nivel | Ejemplo | Qué guarda |
|---|---|---|
| **FAISS a pelo** | `faiss.IndexFlatIP` | Solo vectores y su posición (0, 1, 2…). Ni texto, ni metadatos |
| **Wrapper de LangChain** | `langchain_community.vectorstores.FAISS` | Lo anterior + un diccionario Python con el texto y los metadatos de cada `Document` |
| **Base de datos vectorial** | Qdrant, Milvus, Weaviate, pgvector, Elasticsearch | Vectores + metadatos + filtros dentro del índice + altas/bajas/cambios + persistencia + (a menudo) búsqueda híbrida |

### Lo que le falta a FAISS a pelo

1. **Metadatos y texto.** FAISS devuelve "filas 17, 203 y 88". Tú tienes que mantener aparte qué chunk
   es cada fila. El wrapper de LangChain lo hace con un `docstore` en memoria (en el notebook:
   `InMemoryDocstore` + `index_to_docstore_id`).
2. **Filtros por metadatos.** Este es el problema más serio (ver abajo).
3. **Borrados y actualizaciones.** HNSW en FAISS no permite borrar. Si cambias una política de la empresa,
   hay que reconstruir el índice.
4. **Persistencia.** Guardas y cargas ficheros a mano (`faiss.write_index`, `FAISS.save_local`).
5. **BM25.** FAISS **solo guarda y busca vectores densos**, que le da ya hechos el modelo de embeddings
   (bge-m3). Esa rama densa es imprescindible y va en FAISS. Lo que le falta es la otra rama de la
   búsqueda híbrida, la **léxica (BM25)**, que hay que montar con otra herramienta (p. ej. `rank_bm25`):

   ```
   pregunta ─┬─► bge-m3 → vector denso → FAISS        (significado)
             └─► palabras → BM25                       (términos exactos: "261/2004", "artículo 7")
                       └──► RRF ─► reranker ─► LLM
   ```

   Las bases vectoriales como Qdrant guardan en el mismo sitio el vector denso y uno disperso, y hacen la
   fusión RRF. bge-m3 puede generar los dos tipos.

### El problema de los filtros, con un ejemplo de Travel Agency

Cada documento de `empresa/` lleva metadatos `vigente_desde` y `publico` (cliente / interno). Queremos:
*"busca solo entre lo que puede ver un cliente y está vigente"*.

Hay dos formas de filtrar:

| Estrategia | Cómo | Riesgo |
|---|---|---|
| **Post-filtro** | Buscar los `fetch_k` más parecidos **en todo el corpus** y después tirar los que no cumplen | Si casi nada del top cumple el filtro, te quedas **sin resultados** |
| **Pre-filtro** | Buscar **solo entre los que cumplen** el filtro | Con Flat es exacto. Con HNSW, si el filtro deja pocos nodos, el grafo pierde caminos |

El wrapper `FAISS` de LangChain hace **post-filtro**: con `filter=...` pide `fetch_k` resultados (20 por
defecto) y filtra en Python.

**Ejemplo concreto:**

- Corpus de 50.000 chunks. Solo **500** (1 %) son de `empresa/`.
- Pregunta: *"¿En cuántos días me devolvéis el dinero si cancelo?"*
- Los 20 chunks más parecidos son casi todos del **Reglamento 261/2004** y de la **Directiva 2015/2302**,
  que hablan mucho de reembolsos. De `empresa/`, quizá uno o ninguno.
- Filtro `ambito = empresa` → **0–1 resultados**. El agente se abstiene ("no encuentro la información")
  aunque la política de cancelación de Viajes Nimbo **sí dice** "7 días".

Soluciones:

- Subir `fetch_k` (200, 1.000…): funciona, pero es un parche.
- **Pre-filtrar con Flat**: FAISS permite pasar un `IDSelector` con los ids permitidos, y con Flat el
  resultado es **exacto** (solo compara con los 500 permitidos).
- Usar **índices separados** por ámbito (uno para `empresa/`, otro para leyes…).
- Usar una **base vectorial con filtrado integrado** (Qdrant aplica el filtro mientras recorre su HNSW y
  lo compensa cuando el filtro es muy estricto).

Con HNSW o IVF en FAISS a pelo, el filtrado es justo donde más fácil es equivocarse. Con Flat, no.

---

## 9. La opción sencilla: FAISS `IndexFlatIP` (paso a paso)

### 9.1 Con FAISS directamente

```python
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

chunks = [
    "El reembolso se realiza en un plazo máximo de 7 días naturales.",
    "Reglamento (CE) 261/2004, artículo 7: derecho a compensación...",
    "Para viajar a EE. UU. se necesita autorización ESTA.",
]

model = SentenceTransformer("BAAI/bge-m3")

# 1) Embeddings normalizados → el producto escalar es el coseno
embeddings = model.encode(chunks, normalize_embeddings=True).astype(np.float32)
d = embeddings.shape[1]                     # 1024

# 2) Índice exacto por producto escalar
index = faiss.IndexFlatIP(d)
index.add(embeddings)                       # sin train(): Flat no se entrena

# 3) Búsqueda
q = model.encode(["¿Cuánto tardan en devolverme el dinero?"], normalize_embeddings=True)
scores, ids = index.search(q.astype(np.float32), k=2)
for score, i in zip(scores[0], ids[0]):
    print(f"{score:.3f}  {chunks[i]}")
```

Puntos importantes:

- **Normalizar** siempre (al indexar **y** al consultar). Si no, `IndexFlatIP` premia los vectores
  "largos" y deja de ser coseno.
- `index.search` devuelve **posiciones**: `chunks[i]` es responsabilidad tuya (FAISS a pelo).

### 9.2 Pre-filtro exacto con `IDSelector`

```python
publico_cliente = np.array([0, 2], dtype=np.int64)       # ids de los chunks que puede ver un cliente
params = faiss.SearchParameters(sel=faiss.IDSelectorBatch(publico_cliente))
scores, ids = index.search(q.astype(np.float32), k=2, params=params)
```

Con `IndexFlatIP`, esto compara **solo** con los permitidos: resultado exacto, sin el problema de `fetch_k`.

### 9.3 Con el wrapper de LangChain (como en el notebook)

```python
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True},
)

# Con MAX_INNER_PRODUCT, LangChain crea un IndexFlatIP por debajo
vector_store = FAISS.from_documents(
    documents,                              # list[Document] con page_content + metadata
    embedding_model,
    distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
)

retriever = vector_store.as_retriever(search_kwargs={"k": 50})
vector_store.save_local("rag/index")        # persistencia a mano
```

Este `retriever` es la rama **densa** del pipeline híbrido. Se combina con un retriever BM25 mediante
`EnsembleRetriever` (que fusiona con **RRF**) y el resultado pasa por el **reranker**:

```
pregunta ─┬─► BM25 (top-50) ──────────┐
          └─► FAISS IndexFlatIP (top-50)┴─► RRF ─► top-20 ─► reranker ─► top-5 ─► LLM
```

---

## 10. Aplicación a Travel Agency

### Tamaño estimado del corpus

| Fuente | Chunks aprox. (~500 tokens) |
|---|---|
| Leyes UE y BOE | 1.000 – 2.000 |
| Yellow Book (CDC) | 4.000 – 6.000 |
| tabiji (8.799 registros) | 10.000 – 25.000 |
| BAAI IndustryCorpus (subconjunto) | lo que se decida (p. ej. 10.000) |
| Documentos de Viajes Nimbo | ~500 |
| **Total** | **~30.000 – 50.000** |

### Decisión propuesta

**Índice denso: `IndexFlatIP` (búsqueda exacta).**

- **Memoria:** 50.000 × 1.024 × 4 B ≈ **200 MB**. Cabe de sobra.
- **Latencia:** del orden de **10 ms** por consulta, frente a **segundos** del LLM local. Irrelevante.
- **Recall 100 %:** si un pasaje no llega al LLM, no es culpa del índice. Simplifica la evaluación.
- **Filtros exactos** por `vigente_desde`, `publico` y `ambito` con `IDSelector` o índices separados.
- **Cero parámetros** y construcción instantánea: reindexar al cambiar un documento cuesta segundos.

**Lo que sí aporta calidad** es lo de alrededor: búsqueda **híbrida con BM25** (leyes llenas de
"261/2004", "artículo 7"), **RRF** y **reranker** (`BAAI/bge-reranker-v2-m3`).

### Cuándo revisar la decisión

| Señal | Cambio |
|---|---|
| N > ~1 millón (p. ej. meter el BAAI IndustryCorpus completo) | HNSW (o Qdrant, que usa HNSW con filtrado integrado) |
| Los vectores ya no caben en la RAM disponible | IVF-PQ + re-ranking con vectores exactos |
| Hacen falta muchos filtros, altas/bajas frecuentes o búsqueda híbrida nativa | Qdrant en local, independientemente de N |

Para el ADR: *"Flat porque N ≈ 50.000 < 1 M; revisar si N > 1 M o si los filtros/actualizaciones lo
piden"*.

---

## 11. Glosario

| Término | Significado |
|---|---|
| **Embedding / vector** | Lista de números que representa el significado de un texto |
| **k-NN** | Los k vecinos más cercanos (más parecidos) a una consulta |
| **ANN** | *Approximate Nearest Neighbors*: buscar vecinos mirando solo parte de la colección, aceptando algún fallo |
| **Recall@k** | Fracción de los k vecinos verdaderos que el índice encuentra |
| **Flat** | Índice sin estructura: compara con todos. Exacto |
| **IP / L2** | Producto escalar (mayor = más parecido) / distancia euclídea (menor = más parecido) |
| **Normalizar** | Escalar el vector a longitud 1; así IP = coseno |
| **IVF** | *Inverted File*: divide el espacio en `nlist` zonas (k-means) y busca en las `nprobe` más cercanas |
| **Centroide** | El "centro" de una zona, calculado con k-means |
| **HNSW** | Grafo de vecinos en varias capas; se busca saltando de nodo en nodo |
| **`M`, `efConstruction`, `efSearch`** | Enlaces por nodo / esfuerzo al construir / esfuerzo al buscar (HNSW) |
| **PQ** | *Product Quantization*: trocea el vector y guarda cada trozo como el índice de una paleta de 256 → bytes en vez de floats |
| **IVF-PQ** | IVF para elegir dónde mirar + PQ para comprimir lo guardado |
| **Pre-filtro / post-filtro** | Filtrar por metadatos antes de buscar / después de buscar |
| **FAISS a pelo** | Usar la librería FAISS directamente, sin base de datos vectorial alrededor |
| **Base de datos vectorial** | Sistema (Qdrant, Milvus, pgvector…) que añade metadatos, filtros, CRUD y persistencia a la búsqueda de vectores |
