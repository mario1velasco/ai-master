# Guía de estudio — Sesión 3: Métodos modernos de recuperación (Hybrid, Reranking, Late Interaction, Multimodal)

> Esta guía explica, con lenguaje sencillo y muchos ejemplos, el contenido de
> [`metodos_modernos_recuperacion.ipynb`](./metodos_modernos_recuperacion.ipynb) y de las diapositivas
> [`T5-S3 Sistemas de recuperación de la información, RAG y Langchain.pdf`](./T5-S3%20Sistemas%20de%20recuperación%20de%20la%20información,%20RAG%20y%20Langchain.pdf).
> Es la continuación directa de las dos sesiones anteriores — si no las has leído, échales un vistazo
> primero: [sesión 1 (vectores)](../01-vectores/EXPLICACION_sesion_1.md) y
> [sesión 2 (sparse vs dense)](../../EXPLICACION_sesion_02.md). Allí vimos que existen dos grandes
> formas de representar texto (contar palabras exactas — *sparse* — o usar un modelo de IA que
> entiende significado — *dense*), y que ninguna de las dos gana siempre. Esta sesión responde a la
> pregunta natural que queda pendiente: **si ninguna gana siempre, ¿cómo las combinamos y cómo
> afinamos aún más el resultado final?**

## Índice

1. [Recordatorio rápido: ¿por qué no basta con elegir un solo método?](#1-recordatorio-rápido-por-qué-no-basta-con-elegir-un-solo-método)
2. [El corpus y las consultas de ejemplo del notebook](#2-el-corpus-y-las-consultas-de-ejemplo-del-notebook)
3. [Hybrid Retrieval: usar sparse y dense a la vez](#3-hybrid-retrieval-usar-sparse-y-dense-a-la-vez)
4. [El problema de fusionar: los scores no hablan el mismo idioma](#4-el-problema-de-fusionar-los-scores-no-hablan-el-mismo-idioma)
5. [Score-based fusion: normalizar y ponderar](#5-score-based-fusion-normalizar-y-ponderar)
6. [Reciprocal Rank Fusion (RRF): combinar solo las posiciones](#6-reciprocal-rank-fusion-rrf-combinar-solo-las-posiciones)
7. [Retrieve-then-rerank: recuperar rápido, ordenar con cuidado](#7-retrieve-then-rerank-recuperar-rápido-ordenar-con-cuidado)
8. [Bi-encoder vs. Cross-encoder: la diferencia clave](#8-bi-encoder-vs-cross-encoder-la-diferencia-clave)
9. [Late Interaction y representaciones Multi-Vector (ColBERT)](#9-late-interaction-y-representaciones-multi-vector-colbert)
10. [Recuperación multimodal: buscar más allá del texto](#10-recuperación-multimodal-buscar-más-allá-del-texto)
11. [Tabla resumen: qué arquitectura elegir](#11-tabla-resumen-qué-arquitectura-elegir)
12. [Resumen final](#12-resumen-final)

---

## 1. Recordatorio rápido: ¿por qué no basta con elegir un solo método?

En la sesión 2 vimos que:

- **Sparse (BM25)** cuenta coincidencias exactas de palabras. Es genial para identificadores, códigos
  y nombres propios, pero no entiende sinónimos ni paráfrasis.
- **Dense (embeddings)** convierte el texto en un vector "aprendido" que captura significado. Es genial
  para reconocer que "coche" y "automóvil" hablan de lo mismo, pero puede perder precisión con
  identificadores exactos o texto muy técnico.

La diapositiva titulada **"Ningún retriever ve toda la relevancia"** resume la idea central de esta
sesión con una imagen muy clara: sparse y dense, ante la misma consulta, **señalan documentos
distintos** dentro de la misma colección. No es que uno sea "mejor" — es que cada uno detecta una
señal diferente, y cada uno puede encontrar información relevante que el otro se salta por completo.

**Ejemplo cotidiano:** imagina que buscas un restaurante preguntando a dos amigos distintos. Uno
conoce la ciudad de memoria calle por calle (como BM25: preciso con nombres y direcciones exactas).
El otro no conoce los nombres de las calles, pero tiene un gusto culinario muy parecido al tuyo (como
dense: entiende "qué tipo de comida te gustaría" aunque no sepa el nombre exacto del sitio). Preguntar
solo a uno de los dos te hace perder la mitad de las buenas recomendaciones. Lo lógico es
**preguntar a ambos y combinar sus respuestas**.

Otra diapositiva, **"Los errores tampoco son los mismos"**, lo remata con dos ejemplos muy concretos:

- **Sparse puede perder:** si la consulta es *"reducir el consumo de energía del portátil"* y el
  documento relevante dice *"cómo prolongar la autonomía del ordenador"*, casi no hay solapamiento de
  palabras — BM25 puede fallar aquí completamente.
- **Dense puede perder:** si la consulta es un código exacto como `"ORA-12541"` (un error concreto de
  Oracle) o una referencia de producto como `"XJ-17"`, un embedding puede acercarse a documentos
  "parecidos en tema" en vez de encontrar la coincidencia exacta que realmente importa.

> **Conclusión de esta sección:** el problema deja de ser "¿cuál de los dos elijo?" y pasa a ser
> **"¿cómo combino ambas señales?"**. Esa es exactamente la primera mitad de esta sesión (Hybrid
> Retrieval), y después veremos cómo refinar aún más el resultado con reranking y otras técnicas.

---

## 2. El corpus y las consultas de ejemplo del notebook

El notebook usa una pequeña colección de 10 documentos que mezclan varios temas de esta propia sesión
(sparse, dense, fusión, reranking, ColBERT, multimodal) más dos documentos "trampa" sobre coches
eléctricos, pensados específicamente para poner a prueba sparse vs. dense:

| id | texto |
|---|---|
| D01 | BM25 pondera la frecuencia de términos y la longitud del documento. |
| D02 | Los embeddings densos representan el significado semántico en vectores. |
| D03 | La búsqueda híbrida combina señales léxicas y semánticas. |
| D04 | Reciprocal Rank Fusion combina rankings sin calibrar sus puntuaciones. |
| D05 | Un cross-encoder evalúa conjuntamente una consulta y un documento. |
| D06 | ColBERT conserva un vector por token y aplica interacción tardía MaxSim. |
| D07 | La búsqueda multimodal relaciona texto, imágenes, audio y vídeo. |
| D08 | El índice invertido permite recuperar rápidamente documentos por palabras. |
| D09 | El modelo de vehículo ZX-81 tiene autonomía eléctrica de 420 kilómetros. |
| D10 | Un automóvil eléctrico puede recorrer largas distancias sin emisiones locales. |

Y estas 4 consultas de prueba:

```python
queries = {
    "Q1": "cómo combinar coincidencia exacta y significado",
    "Q2": "coche eléctrico con gran autonomía",
    "Q3": "especificaciones ZX-81",
    "Q4": "comparar cada token de la consulta con tokens del documento",
}
```

Fíjate en el diseño deliberado de estas consultas:

- **Q1** apunta conceptualmente a D03 (búsqueda híbrida) — pone a prueba si el sistema entiende la
  propia idea de "combinar señales".
- **Q2** es la consulta "trampa del lexical gap": usa la palabra **"coche"**, mientras que D10 usa
  **"automóvil"** (sinónimo, sin coincidencia literal) y D09 usa **"vehículo... ZX-81"** (contiene el
  identificador exacto, pero no la palabra "coche"). Es una prueba perfecta para comparar sparse y
  dense sobre el mismo par de documentos.
- **Q3** es una consulta puramente de identificador (`"ZX-81"`) — el terreno favorito de BM25.
- **Q4** describe literalmente, con otras palabras, el mecanismo de ColBERT (sección 9) — apunta a
  D06.

Con este mismo corpus y estas mismas 4 consultas se prueban **todos** los métodos del resto de la
sesión, para que la comparación sea siempre justa (misma idea que en la sesión 2: nunca cambiar de
ejemplo a mitad de comparación).

---

## 3. Hybrid Retrieval: usar sparse y dense a la vez

### La idea básica

Un sistema **híbrido** no elige entre BM25 o embeddings: ejecuta **los dos** sobre la misma consulta,
y luego combina ambos resultados en un único ranking final. La diapositiva **"De elegir un retriever a
combinar señales"** lo resume así:

> Si sparse y dense aportan evidencia complementaria, la pregunta deja de ser **"¿cuál utilizamos?"**
> y pasa a ser **"¿cómo combinamos sus resultados?"**

### BM25 en el notebook (señal sparse)

```python
from rank_bm25 import BM25Okapi

tokenized_corpus = [tokenize(doc.page_content) for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

def rank_bm25(query):
    scores = bm25.get_scores(tokenize(query))
    ...
```

Esto es exactamente el BM25 que ya vimos en la sesión 2 (frecuencia de términos + rareza global +
normalización por longitud), pero usando la librería `rank_bm25` en vez de implementarlo a mano.

### Embeddings en el notebook (señal dense)

```python
if USE_OPENAI:
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
else:
    local_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```

El notebook detecta automáticamente si tienes configurada una clave de OpenAI. Si no la tienes, usa un
modelo local y gratuito (`paraphrase-multilingual-MiniLM-L12-v2`), que se descarga la primera vez que
lo ejecutas. Ambos casos calculan, para cada documento, un vector normalizado (de longitud 1 — como
vimos en la sesión 1), y comparan con la consulta usando el producto escalar, que —al estar todo
normalizado— equivale exactamente a la similitud del coseno.

### Qué esperar al comparar ambos en las 4 consultas

Aunque los números exactos dependen del modelo de embeddings que uses (varían un poco entre OpenAI y
el modelo local), el **patrón cualitativo** que vas a observar al ejecutar el notebook es:

- **Q1** ("cómo combinar coincidencia exacta y significado"): dense debería acercarse mucho a D03
  ("La búsqueda híbrida combina señales léxicas y semánticas"), porque entiende el significado general
  de la frase aunque las palabras no coincidan exactamente. Sparse puede acertar también si comparte
  alguna palabra clave (por ejemplo "combina"), pero de forma menos robusta.
- **Q2** ("coche eléctrico con gran autonomía"): aquí es donde se ve mejor el contraste. **BM25** debería
  favorecer fuertemente a **D09** (contiene "eléctrica" y "autonomía" literalmente) por encima de D10
  (que ni siquiera dice "coche", dice "automóvil"). **Dense**, en cambio, debería reconocer que D10
  ("automóvil eléctrico... sin emisiones") es semánticamente muy cercano a "coche eléctrico", aunque no
  comparta la palabra "coche" ni "autonomía" literalmente, y quizás sitúe D09 y D10 con puntuaciones
  parecidas entre sí.
- **Q3** ("especificaciones ZX-81"): BM25 debería clavar D09 en primer lugar sin ninguna duda —
  "ZX-81" es un identificador rarísimo, con IDF altísimo (recuerda la sesión 2). Dense también puede
  encontrarlo, pero por una razón distinta (reconoce el contexto de "modelo de vehículo... kilómetros"),
  no por el código en sí, que para un modelo de lenguaje es solo una secuencia de caracteres poco
  común.
- **Q4** ("comparar cada token de la consulta con tokens del documento"): esta consulta describe, con
  otras palabras, exactamente lo que hace ColBERT (sección 9). Dense debería reconocer esa relación
  conceptual y acercarse a D06, mientras que BM25 probablemente falle si no comparte palabras exactas
  con "ColBERT conserva un vector por token y aplica interacción tardía MaxSim".

> Al ejecutar el notebook verás los números concretos en tu máquina — no los reproducimos aquí porque
> varían ligeramente según qué backend de embeddings (OpenAI o local) esté activo. Lo importante es el
> patrón: **cada método brilla en casos distintos**, tal como predice la sección 1.

---

## 4. El problema de fusionar: los scores no hablan el mismo idioma

Ahora que tenemos dos rankings (uno de BM25, otro de embeddings), la tentación obvia sería sumar
directamente sus puntuaciones. **Esto es un error**, y la diapositiva **"Los scores no hablan
necesariamente el mismo idioma"** lo explica con un ejemplo perfecto:

| | BM25 | Dense (coseno) |
|---|---|---|
| Documento A | 12.7 | 0.71 |
| Documento B | 8.4 | 0.83 |

- **BM25 no tiene un límite fijo**: sus puntuaciones pueden ser 5, 12, 50... dependiendo del corpus, de
  la consulta y de cuántos términos raros contenga.
- **La similitud coseno siempre está entre -1 y 1** (normalmente entre 0 y 1 para texto).

Si sumas directamente `12.7 + 0.71 = 13.41` para A y `8.4 + 0.83 = 9.23` para B, el resultado está
completamente dominado por el número de BM25 — el coseno apenas influye, porque su escala es
minúscula en comparación. **Eso no es "fusionar dos señales", es dejar que una aplaste a la otra por
pura casualidad de escala** — exactamente el mismo problema que vimos con las unidades de "edad" e
"ingresos" en la sesión 1.

**Ejemplo cotidiano:** es como intentar promediar la nota de un examen sobre 10 puntos con la nota de
otro examen sobre 1000 puntos, sumándolas directamente sin convertir ambas a la misma escala. El
examen sobre 1000 puntos "ganaría" siempre, sin que eso signifique que sea más importante.

La diapositiva propone **dos alternativas** para resolver esto:

1. **Score-Based Fusion:** normalizar los números a una escala común antes de combinarlos (sección 5).
2. **Rank-Based Fusion:** ignorar los números por completo y usar solo **la posición** de cada
   documento en cada ranking (sección 6).

---

## 5. Score-based fusion: normalizar y ponderar

### El paso de normalización: min-max

Antes de combinar, convertimos los scores de cada método a una escala común, típicamente entre 0 y 1,
usando **normalización min-max**:

```python
def minmax_normalize(values):
    values = np.asarray(values, dtype=float)
    value_range = values.max() - values.min()
    if np.isclose(value_range, 0):
        return np.zeros_like(values)
    return (values - values.min()) / value_range
```

La fórmula es sencilla: al valor más bajo de la lista le asignamos 0, al valor más alto le asignamos 1,
y todos los demás quedan proporcionalmente en medio.

**Ejemplo cotidiano:** si en un examen las notas van de 3 a 9 sobre 10, y "reescalas" para que la nota
más baja de la clase sea un 0 y la más alta un 10, un compañero que sacó un 6 (justo en medio del
rango original) pasaría a tener aproximadamente un 5 en la escala reescalada. Es literalmente estirar
o encoger la regla para que el rango de valores encaje siempre entre 0 y 1, sin importar la escala
original.

### La fórmula de fusión con peso `alpha`

$$s_{hybrid}(d)=\alpha \cdot \hat{s}_{sparse}(d) + (1-\alpha) \cdot \hat{s}_{dense}(d)$$

Donde $\hat{s}$ significa "el score ya normalizado entre 0 y 1". El parámetro **`alpha`** (entre 0 y 1)
controla cuánto peso le das a cada señal:

- `alpha = 1.0` → confías completamente en BM25 (sparse), ignoras dense por completo.
- `alpha = 0.0` → confías completamente en el embedding (dense), ignoras BM25 por completo.
- `alpha = 0.5` → les das el mismo peso a ambos.

```python
def score_fusion(query, alpha=0.5):
    ...
    fused["sparse_norm"] = minmax_normalize(fused["score_sparse"])
    fused["dense_norm"] = minmax_normalize(fused["score_dense"])
    fused["score_fusion"] = alpha * fused["sparse_norm"] + (1 - alpha) * fused["dense_norm"]
    ...
```

El notebook prueba la consulta Q1 con tres valores de `alpha` (0.2, 0.5 y 0.8) y muestra cómo **el
ranking final cambia según cuánto peso le des a cada señal** — el mismo fenómeno que vimos en la
sesión 1 con la elección de métrica, y en la sesión 2 con el reescalado de unidades: **la decisión de
ponderación no es neutral, cambia el resultado**.

**Ejemplo cotidiano:** es como decidir cuánto pesan las notas de teoría frente a las notas de
prácticas en la nota final de una asignatura. Si `alpha=0.8` le das mucho peso a la teoría, un alumno
fuerte en teoría pero flojo en prácticas quedará mejor situado que con `alpha=0.2`. Ninguna ponderación
es "la correcta" en abstracto — depende de qué te importa medir.

### Ventajas y problemas de score-based fusion

**Ventaja:** conserva información sobre "cuánta ventaja" tenía un documento sobre otro dentro de cada
ranking (no solo su posición, sino su intensidad relativa).

**Problema:** es sensible a valores extremos. Si en una consulta concreta BM25 solo tiene un documento
con score muy alto y el resto en cero, la normalización min-max puede distorsionar mucho la escala.
También es inestable cuando todos los scores de un método están casi empatados entre sí (la
normalización "estira" diferencias diminutas y sin significado real hasta parecer importantes).

---

## 6. Reciprocal Rank Fusion (RRF): combinar solo las posiciones

### La idea: ignorar los números, quedarnos solo con el orden

RRF resuelve el problema de "los scores no hablan el mismo idioma" de una forma radicalmente simple:
**tira los números originales a la basura y se queda solo con la posición (el puesto) que ocupa cada
documento en cada ranking.**

$$RRF(d) = \sum_{r \in R} \frac{1}{k + rank_r(d)}$$

- $rank_r(d)$ es la posición del documento $d$ en el ranking $r$ (1º, 2º, 3º...).
- $k$ es una constante (normalmente 60) que "suaviza" la diferencia entre posiciones cercanas, para
  que pasar del puesto 1 al puesto 2 no sea un cambio brutal en el score final.

### Ejemplo del notebook, calculado paso a paso

```
Documento A: Sparse → puesto #1, Dense → puesto #4
Documento B: Sparse → puesto #8, Dense → puesto #1
```

Con $k=60$:

$$RRF(A) = \frac{1}{60+1} + \frac{1}{60+4} = \frac{1}{61} + \frac{1}{64} \approx 0{,}0164 + 0{,}0156 = 0{,}032$$

$$RRF(B) = \frac{1}{60+8} + \frac{1}{60+1} = \frac{1}{68} + \frac{1}{61} \approx 0{,}0147 + 0{,}0164 = 0{,}031$$

**Resultado: A gana por muy poco (0.032 frente a 0.031)**, aunque en el ranking sparse A era claramente
primero y B estaba bastante rezagado (puesto 8), mientras que en dense pasa justo lo contrario. RRF
"premia" a los documentos que quedan **razonablemente bien en ambos rankings**, más que a los que son
"campeones absolutos" en solo uno de los dos.

```python
def reciprocal_rank_fusion(rankings, k=60):
    fused_scores = defaultdict(float)
    for ranking in rankings:
        for position, document_id in enumerate(ranking, start=1):
            fused_scores[document_id] += 1 / (k + position)
    return sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)
```

**Ejemplo cotidiano:** imagina un concurso con dos jurados que puntúan con escalas totalmente distintas
(uno pone notas del 0 al 5, otro del 0 al 1000). En vez de intentar convertir ambas escalas a algo
comparable (que sería como el score-based fusion de la sección 5), simplemente le preguntas a cada
jurado **"¿en qué puesto (1º, 2º, 3º...) pondrías a cada concursante?"**, y combinas esos puestos.
Así ya no importa que un jurado use una escala de notas completamente distinta al otro.

### ¿Por qué RRF es tan popular en sistemas reales?

- **Es robusto ante scores incompatibles**: no necesitas normalizar nada, ni preocuparte de que un
  método use una escala rarísima — solo necesitas la lista ordenada de resultados de cada método.
- **Es simple de implementar** y no tiene casi ningún parámetro que ajustar (solo `k`, que rara vez
  hace falta cambiar).
- **A cambio, pierde información**: descarta por completo "cuánta ventaja" tenía un documento sobre
  otro dentro de un mismo ranking. Un documento que ganó por muchísimo en BM25 cuenta exactamente
  igual que uno que ganó por muy poco, siempre que ambos queden en el puesto 1.

El notebook compara, para las 4 consultas, el ranking de "score fusion" (sección 5) contra el de RRF, y
verás que en la práctica suelen coincidir bastante en los primeros puestos, aunque no siempre de forma
idéntica — cada método tiene su propia forma de resolver los empates y casi-empates.

---

## 7. Retrieve-then-rerank: recuperar rápido, ordenar con cuidado

### La idea general

Hasta ahora hemos hablado de cómo **recuperar** un conjunto de candidatos (usando sparse, dense, o una
combinación). Pero recuperar rápido sobre millones de documentos y **ordenar con muchísima precisión**
son dos objetivos que suelen chocar entre sí: los métodos más precisos son también los más lentos, y
no se pueden aplicar a un corpus entero.

La solución habitual, ilustrada en la diapositiva **"Retrieve first, Rerank second"**, es una
arquitectura en dos etapas:

```
1.000.000 documentos → RETRIEVER (rápido) → top 50 candidatos → RERANKER (preciso) → top 5 finales
```

1. **Retrieve (recuperar):** un método barato y muy rápido (sparse, dense o híbrido) reduce el corpus
   completo (por ejemplo, un millón de documentos) a un puñado de candidatos razonables (por ejemplo,
   50). El objetivo aquí es **no dejar fuera nada relevante** (maximizar lo que en la sesión 2 llamamos
   *recall*), aunque el orden entre esos 50 no sea perfecto todavía.
2. **Rerank (reordenar):** un modelo mucho más lento pero mucho más preciso examina solo esos 50
   candidatos (nunca el corpus entero) y decide el orden final definitivo, quedándonos por ejemplo con
   los 5 mejores.

**Ejemplo cotidiano:** es exactamente cómo funciona un proceso de selección de personal con muchos
candidatos. Primero hay un filtro rápido y automático (por ejemplo, descartar CVs que no cumplen unos
requisitos mínimos) que reduce 1000 candidaturas a 50. Después, un proceso mucho más costoso y
detallado (entrevistas personales) decide, entre esos 50, quiénes son los 5 finalistas. Sería
absurdo (e inviable en tiempo) entrevistar personalmente a las 1000 candidaturas iniciales.

La diapositiva señala explícitamente qué modelos se usan típicamente en cada etapa: para *retrieve*,
BM25 (sparse), OpenAI/Qwen (dense) o combinaciones híbridas; para *rerank*, modelos especializados como
`Cohere rerank-v4.0`, `Qwen3-Reranker` o `BAAI bge-reranker-v2-m3`.

> **Punto importante:** el reranker **nunca puede "rescatar" documentos que el retriever ya descartó**.
> Solo puede mejorar el **orden** dentro del conjunto que ya se recuperó. Si el retriever inicial se
> equivocó y dejó fuera el documento realmente relevante, el reranker jamás lo va a poder recuperar,
> por muy bueno que sea — simplemente nunca llega a verlo.

---

## 8. Bi-encoder vs. Cross-encoder: la diferencia clave

Para entender por qué el reranker es más lento pero más preciso, hay que entender la diferencia entre
dos arquitecturas de modelos, explicada muy claramente en la diapositiva **"Bi-Encoder vs
Cross-Encoder"**.

### Bi-encoder (lo que hemos usado hasta ahora para "dense")

$$q \to e_q \qquad d \to e_d \qquad score(q,d) = sim(e_q, e_d)$$

La consulta y el documento se convierten en vectores **por separado**, sin que uno "vea" al otro
durante ese proceso. Solo al final se comparan esos dos vectores ya terminados (con coseno, por
ejemplo). Esto es justo lo que hace `embed_documents` / `embed_query` de LangChain: puedes calcular
todos los vectores de los documentos **una sola vez, por adelantado**, guardarlos en un índice, y para
cada nueva consulta solo necesitas calcular un vector más y compararlo. Muy rápido.

### Cross-encoder (lo que se usa típicamente para el reranker)

$$[q, d] \to \text{Modelo} \to score$$

Aquí la consulta y el documento se meten **juntos, a la vez**, dentro del mismo modelo, que produce
directamente un único número de relevancia para esa pareja concreta. El modelo puede fijarse en cómo
interactúan palabras concretas de la consulta con palabras concretas del documento, algo que el
bi-encoder no puede hacer (porque para cuando compara los vectores, ya "olvidó" los detalles finos de
cada texto por separado, todo quedó comprimido en un solo vector).

**El coste:** como la consulta y el documento se procesan juntos, **no se puede precalcular nada por
adelantado**. Cada vez que quieres puntuar un documento nuevo contra una consulta, tienes que volver a
ejecutar el modelo entero para esa pareja específica. Si tuvieras un millón de documentos, necesitarías
un millón de pasadas del modelo por cada búsqueda — completamente inviable. Por eso el cross-encoder
**solo se usa sobre un conjunto pequeño ya filtrado** (los 50 candidatos de la sección 7), nunca sobre
el corpus completo.

### Ejemplo muy claro de la diapositiva "¿Por qué un Cross-Encoder puede ordenar mejor?"

Consulta: *"¿La cancelación de un vuelo da derecho a compensación?"*

- **Documento A:** *"Compensaciones por cancelación y retrasos de vuelos según condiciones
  aplicables."*
- **Documento B:** *"Cómo cancelar voluntariamente una reserva de vuelo."*

Ambos documentos comparten muchísimo vocabulario con la consulta ("cancelación", "vuelo"), así que un
bi-encoder podría puntuarlos de forma parecida, sin distinguir bien cuál responde realmente a la
pregunta. Pero solo el **Documento A** responde a la intención real de la consulta (trata sobre
compensaciones), mientras que el Documento B habla de otra cosa completamente distinta (cómo cancelar
tú mismo una reserva, no sobre compensaciones que te deben a ti). Un cross-encoder, al poder analizar
**la interacción conjunta** entre la consulta completa y el documento completo, tiene mucha más
capacidad de distinguir estos matices finos que un simple parecido superficial de vocabulario.

### Ejemplo real del notebook

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
pairs = [(rerank_query, text) for text in candidates["texto"]]
candidates["score_reranker"] = reranker.predict(pairs)
```

El notebook toma los 6 mejores candidatos obtenidos por RRF para la consulta Q4 ("comparar cada token
de la consulta con tokens del documento"), y los pasa por un cross-encoder para obtener un
`score_reranker` a cada pareja `(consulta, documento)`. Después compara **la posición inicial** (la
que traían de RRF) contra **la posición tras el reranking**, para ver si el orden cambió. Es de
esperar que el reranker suba considerablemente la posición de D06 ("ColBERT conserva un vector por
token y aplica interacción tardía MaxSim"), porque describe casi literalmente lo que pregunta la
consulta Q4, aunque el solapamiento de palabras exactas sea limitado.

### Tabla comparativa de arquitecturas (de la diapositiva del notebook)

| Arquitectura | Representación documental | ¿Se puede precalcular? | Interacción | Coste online |
|---|---|---|---|---|
| **Bi-encoder** | Un solo vector | Sí | Coseno / producto escalar | Bajo |
| **Late interaction** (sección 9) | Varios vectores | Sí | MaxSim | Medio |
| **Cross-encoder** | Depende de la consulta (no se puede fijar de antemano) | No | Atención conjunta | Alto |

---

## 9. Late Interaction y representaciones Multi-Vector (ColBERT)

### El problema que resuelve: ¿y si comprimir todo en un solo vector pierde demasiado detalle?

La diapositiva **"¿Qué perdemos al comprimir un texto en un solo vector?"** lo plantea muy bien: un
bi-encoder obliga al modelo a resumir absolutamente todo el documento —términos, entidades, temas,
relaciones, matices— en **un único punto** dentro de un espacio de muchas dimensiones. Dos textos
pueden parecer "globalmente parecidos" en ese único vector y, aun así, diferir mucho en **qué partes
concretas** son relevantes para una consulta específica.

**Ejemplo cotidiano:** resumir un libro entero de 300 páginas en una sola frase de "de qué trata" es
muy útil para clasificarlo rápidamente en una biblioteca, pero pierde muchísimo detalle: si buscas
específicamente "el capítulo donde el protagonista viaja a Japón", ese resumen de una frase no te sirve
de nada, aunque el libro sí contenga esa información en algún punto interno.

### La solución de ColBERT: guardar un vector por cada palabra (token), no uno solo por documento

En vez de comprimir todo el documento en un único vector, ColBERT guarda **un vector por cada token
del texto** (una palabra, aproximadamente). Un documento de 50 palabras tendría 50 vectores en vez de
1. Lo mismo para la consulta.

```
Single-Vector:  documento → un solo vector
Multi-Vector:   documento → {vector_1, vector_2, ..., vector_m}   (uno por token)
```

### La regla MaxSim: cómo comparar dos conjuntos de vectores

$$score(q,d) = \sum_i \max_j sim(q_i, d_j)$$

En palabras: para **cada** vector de la consulta, buscas cuál es el vector del documento que más se
le parece (el "máximo"), te quedas con ese mejor emparejamiento, y luego **sumas** todos esos mejores
emparejamientos para obtener el score final.

**Ejemplo cotidiano:** imagina que estás emparejando ingredientes de una receta con lo que hay en tu
nevera. Para cada ingrediente de la receta (cada "token de la consulta"), buscas el sustituto más
parecido disponible en tu nevera (el "mejor match" en el documento), y sumas qué tan bien encajaron
todos los sustitutos encontrados. No te importa si tu nevera tiene además cosas que la receta no pide
—solo importa lo mejor que encontraste para cada ingrediente que sí necesitas.

### Ejemplo completo del notebook, calculado paso a paso

La consulta tiene 2 tokens: `["coche", "eléctrico"]`, representados (de forma simplificada, con
vectores de juguete de solo 3 números) como:

```python
query_vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]   # "coche"     # "eléctrico"
```

Se comparan contra dos documentos, cada uno con sus propios vectores por token:

**Documento D_A** (tokens: "automóvil", "batería", "ciudad"):

```
automóvil = [0.95, 0.05, 0.00]
batería   = [0.05, 0.96, 0.00]
ciudad    = [0.10, 0.05, 0.85]
```

**Documento D_B** (tokens: "coche", "gasolina", "carretera"):

```
coche      = [0.98, 0.02, 0.00]
gasolina   = [0.10, 0.05, 0.90]
carretera  = [0.20, 0.05, 0.80]
```

Calculando la similitud coseno (sección 8 de la sesión 1) entre cada token de la consulta y cada token
de cada documento, y quedándonos con el máximo de cada fila:

**Para D_A:**
- El token "coche" de la consulta encuentra su mejor coincidencia en "automóvil" → similitud ≈ **0.999**
  (son prácticamente el mismo vector, es decir, el modelo "sabe" que coche y automóvil son sinónimos).
- El token "eléctrico" de la consulta encuentra su mejor coincidencia en "batería" → similitud ≈
  **0.999** (el modelo asocia fuertemente "eléctrico" con "batería").
- **Score MaxSim(D_A) = 0.999 + 0.999 ≈ 2.00**

**Para D_B:**
- El token "coche" de la consulta encuentra su mejor coincidencia en "coche" → similitud ≈ **0.9998**
  (¡coincidencia casi exacta, literalmente la misma palabra!).
- El token "eléctrico" de la consulta busca su mejor coincidencia entre "gasolina" y "carretera", y no
  encuentra nada realmente parecido → mejor similitud ≈ **0.06** (muy baja: "eléctrico" no tiene
  relación fuerte con ninguno de esos dos tokens).
- **Score MaxSim(D_B) = 0.9998 + 0.06 ≈ 1.06**

**Resultado: D_A gana claramente (≈2.00 frente a ≈1.06)**, ¡aunque D_B contenga literalmente la
palabra "coche" y D_A ni siquiera la mencione! Esto ilustra perfectamente el valor de MaxSim: **cada
token de la consulta puede encontrar su propia mejor coincidencia, de forma independiente**, en vez de
depender de un único resumen global del documento. D_A gana porque, aunque no comparte la palabra
"coche" literalmente, **sí cubre bien ambos conceptos de la consulta** (coche→automóvil,
eléctrico→batería), mientras que D_B solo cubre bien uno de los dos.

### ColBERT: un punto intermedio entre bi-encoder y cross-encoder

La diapositiva **"ColBERT: entre Bi-Encoder y Cross-Encoder"** lo resume con una idea muy útil:

- **Más interacción → mayor capacidad de modelar relevancia** (como el cross-encoder).
- **Más independencia → mayor capacidad de precomputación e indexación** (como el bi-encoder).

ColBERT logra un equilibrio: **sigue pudiendo precalcular los vectores de los documentos por
adelantado** (como un bi-encoder, porque documento y consulta se codifican por separado), pero la
interacción ocurre **después**, comparando token a token con MaxSim (más parecido en riqueza a un
cross-encoder, aunque sin llegar a su nivel de interacción total). Por eso su coste computacional
online es "medio": más caro que un bi-encoder simple, pero mucho más barato que ejecutar un
cross-encoder sobre cada documento.

---

## 10. Recuperación multimodal: buscar más allá del texto

### La idea: un espacio compartido para distintos tipos de contenido

Todo lo visto hasta ahora compara texto contra texto. Pero la misma lógica geométrica (vectores,
similitud coseno) se puede extender a **imágenes, audio y vídeo**, si entrenamos codificadores para
cada modalidad que produzcan vectores dentro de **un mismo espacio compatible**.

$$\text{texto} \to e_{txt} \qquad \text{imagen} \to e_{im} \qquad \text{audio} \to e_{au} \qquad \text{vídeo} \to e_{vid}$$

**Importante:** esta compatibilidad **no surge por arte de magia** de tener vectores del mismo tamaño.
Surge porque el modelo se entrena específicamente (mediante *aprendizaje contrastivo*, la misma
intuición de "acercar positivos, alejar negativos" que vimos en la sesión 2) para que, por ejemplo,
una foto de un perro y la frase "un perro corriendo" terminen cerca la una de la otra en ese espacio
compartido, aunque procedan de mundos completamente distintos (píxeles vs. letras).

**Ejemplo cotidiano:** es como si tradujeras tanto un texto en español como uno en japonés a un
"idioma universal" común (por ejemplo, el significado puro, sin palabras). Una vez traducidos ambos a
ese idioma común, puedes comparar directamente si dicen lo mismo, aunque el idioma original de cada uno
fuera completamente distinto. Los codificadores multimodales hacen algo parecido: traducen imagen,
audio, vídeo y texto a un mismo "idioma numérico" común.

### Cross-modal retrieval: la consulta y el resultado pueden ser de tipos distintos

Una vez que existe ese espacio compartido, se abren búsquedas que antes no tenían sentido:

- **Texto → Imagen:** escribes *"perro corriendo por la playa"* y el sistema te devuelve fotos.
- **Imagen → Texto:** subes la foto de un producto y el sistema te devuelve su ficha técnica en texto.
- **Audio → Vídeo/Texto:** subes un fragmento de sonido y el sistema encuentra vídeos o documentos
  relacionados.

### Ejemplo completo del notebook, calculado paso a paso

El notebook usa vectores "de juguete" de 4 dimensiones, donde cada dimensión representa
conceptualmente un rasgo compartido (naturaleza, ciudad, sonido, movimiento) — no son píxeles ni ondas
reales, solo sirven para ilustrar el mecanismo:

```python
M1 (imagen, "bosque con un río"):              [0.95, 0.05, 0.00, 0.20]
M2 (audio, "agua fluyendo y aves"):            [0.82, 0.00, 0.65, 0.10]
M3 (vídeo, "tráfico en una avenida"):          [0.05, 0.90, 0.55, 0.85]
M4 (texto, "sendero tranquilo en la naturaleza"): [0.90, 0.05, 0.05, 0.25]

consulta de texto: "sendero tranquilo en la naturaleza" → [0.92, 0.02, 0.20, 0.15]
```

Calculando la similitud coseno entre la consulta y cada elemento (normalizando todos los vectores
primero, igual que en la sesión 1), el resultado ordenado de mayor a menor similitud es:

```
1. M4 (texto, "sendero tranquilo en la naturaleza")   → similitud ≈ 0.981
2. M1 (imagen, "bosque con un río")                    → similitud ≈ 0.977
3. M2 (audio, "agua fluyendo y aves")                  → similitud ≈ 0.897
4. M3 (vídeo, "tráfico en una avenida")                → similitud ≈ 0.233
```

Tiene mucho sentido: la consulta y M4 son casi el mismo concepto en texto (por eso quedan casi
empatados en primer lugar), la imagen del bosque (M1) es la siguiente más cercana en significado, el
audio de agua y aves (M2) comparte "naturaleza" pero añade un componente de sonido que la consulta no
pedía, y el vídeo de tráfico urbano (M3) es prácticamente lo opuesto en significado — por eso su
similitud cae en picado. **La comparación deja de ser "texto contra texto" y pasa a ser "significado
representado contra significado representado"**, tal como dice literalmente la diapositiva
correspondiente.

---

## 11. Tabla resumen: qué arquitectura elegir

Esta tabla, adaptada de la última diapositiva de contenido y de la última celda del notebook, resume
todas las opciones vistas en esta sesión:

| Método | Eficiencia de búsqueda | ¿Se puede precalcular el documento? | Interacción consulta-documento | Interpretabilidad | Coste típico |
|---|---|---|---|---|---|
| **Sparse / BM25** | Muy alta | Sí (índice invertido) | Coincidencia de términos | Alta | Bajo |
| **Dense / bi-encoder** | Alta (con índice vectorial) | Sí, un solo vector | Similitud global | Media-baja | Bajo-medio |
| **Hybrid** | Alta | Sí, dos índices | Fusión de señales | Media | Medio |
| **Reranking / cross-encoder** | Baja sobre todo el corpus; viable solo sobre un top-k pequeño | No | Atención conjunta | Media | Alto |
| **Late interaction (ColBERT)** | Media-alta | Sí, varios vectores | MaxSim local | Media | Medio-alto |
| **Multimodal** | Depende del índice y los codificadores | Habitualmente sí | Similitud en espacio alineado | Baja-media | Variable |

Y la arquitectura habitual en un sistema real de producción combina varias de estas etapas en cascada,
tal como resume la última diapositiva **"La idea general no cambia"**:

```
REPRESENTAR → COMPARAR → RECUPERAR → REFINAR
```

- **Representar:** convertir información heterogénea (texto, código, imágenes...) en estructuras
  matemáticas compatibles (vectores).
- **Comparar:** aplicar una medida de similitud o relevancia (coseno, BM25...).
- **Recuperar:** seleccionar candidatos de forma eficiente sobre todo el corpus (sparse, dense o
  híbrido).
- **Refinar:** fusionar señales, reordenar (reranking) o aplicar interacción más rica (ColBERT) cuando
  realmente compensa el coste extra, ya sobre un conjunto pequeño de candidatos.

Una receta muy habitual combina: **recuperación híbrida** para maximizar cobertura, **RRF** cuando las
escalas de los scores son incompatibles, y un **cross-encoder** sobre unos pocos candidatos finales
para maximizar la precisión del orden. **Late interaction** ofrece un punto intermedio útil cuando
necesitas más matiz que un bi-encoder simple pero no puedes permitirte el coste de un cross-encoder
sobre muchos candidatos.

---

## 12. Resumen final

1. **Ningún método de recuperación "ve" toda la relevancia por sí solo**: sparse y dense cometen
   errores distintos, en casos distintos (sección 1).
2. **Hybrid retrieval** ejecuta sparse y dense sobre la misma consulta y combina ambos resultados, en
   vez de forzar una elección entre uno u otro (sección 3).
3. **Los scores de métodos distintos no son directamente comparables** — sumarlos sin más deja que la
   escala, no la relevancia real, decida el resultado (sección 4).
4. **Score-based fusion** normaliza los scores a una escala común (0-1) y los combina con un peso
   ajustable `alpha`; conserva matiz pero es sensible a valores extremos (sección 5).
5. **Reciprocal Rank Fusion (RRF)** ignora los scores originales y combina solo las posiciones —
   robusto ante escalas incompatibles, aunque pierde matiz sobre "cuánta ventaja" tenía cada documento
   (sección 6).
6. **Retrieve-then-rerank** separa el problema en dos etapas: recuperar rápido y con amplia cobertura
   (recall), y después reordenar con precisión solo un conjunto pequeño de candidatos (sección 7).
7. **Bi-encoder vs. cross-encoder:** el bi-encoder codifica consulta y documento por separado (rápido,
   precomputable); el cross-encoder los procesa juntos (lento, pero mucho más preciso porque puede
   modelar la interacción real entre ambos) (sección 8).
8. **Late interaction (ColBERT)** es un punto intermedio: guarda varios vectores por texto (uno por
   token) y usa la regla **MaxSim** para que cada token de la consulta encuentre su mejor coincidencia
   en el documento, sin necesitar procesar consulta y documento juntos (sección 9).
9. **La recuperación multimodal** extiende la misma lógica geométrica (vectores + similitud) a
   imágenes, audio y vídeo, siempre que los codificadores estén entrenados para producir vectores
   realmente compatibles entre modalidades (sección 10).
10. **La arquitectura general nunca cambia**, aunque cambien los modelos concretos: representar,
    comparar, recuperar y refinar. La calidad final de cualquier sistema de recuperación depende de
    qué información conserva cada representación y de cómo se usa esa información para comparar
    candidatos.

Estos son, en conjunto, los componentes que forman la base técnica de los sistemas RAG modernos
(Retrieval-Augmented Generation): antes de que un modelo de lenguaje genere una respuesta, todo lo
visto en estas tres sesiones —representar, comparar, combinar señales y refinar el orden— determina
qué fragmentos de información llegan realmente a ese modelo para que pueda responder bien.
