# Guía de estudio — Sesión 2: Representación de la información (Sparse vs Dense)

> Esta guía explica, con lenguaje sencillo y muchos ejemplos, todo lo que aparece en el notebook
> [`sesion_02_sparse_vs_dense.ipynb`](./sesion_02_sparse_vs_dense.ipynb). Continúa directamente donde
> terminó la sesión 1 (si no la has leído, revisa primero
> [`clases/01-vectores/EXPLICACION_sesion_1.md`](./clases/01-vectores/EXPLICACION_sesion_1.md)):
> allí vimos cómo convertir texto en vectores muy simples (contando palabras) y cómo compararlos. Aquí
> profundizamos en **dos grandes familias de representaciones** y en un método clásico y muy usado en
> la práctica: **BM25**.

## Índice

1. [¿Qué significa "representar" información?](#1-qué-significa-representar-información)
2. [Dos estrategias: sparse y dense](#2-dos-estrategias-sparse-y-dense)
3. [Representaciones sparse: el vocabulario como sistema de coordenadas](#3-representaciones-sparse-el-vocabulario-como-sistema-de-coordenadas)
4. [Bag of Words (BoW): contar palabras](#4-bag-of-words-bow-contar-palabras)
5. [TF-IDF: no todas las palabras importan igual](#5-tf-idf-no-todas-las-palabras-importan-igual)
6. [BM25: la mejora que se usa en sistemas reales](#6-bm25-la-mejora-que-se-usa-en-sistemas-reales)
7. [Representaciones dense y el problema del "lexical gap"](#7-representaciones-dense-y-el-problema-del-lexical-gap)
8. [Qué es un embedding moderno](#8-qué-es-un-embedding-moderno)
9. [Cómo se entrena un embedding (intuición, sin fórmulas complicadas)](#9-cómo-se-entrena-un-embedding-intuición-sin-fórmulas-complicadas)
10. [Consulta y documento no siempre se tratan igual](#10-consulta-y-documento-no-siempre-se-tratan-igual)
11. [Probando embeddings de verdad con LangChain](#11-probando-embeddings-de-verdad-con-langchain)
12. [La comparación justa: mismo corpus, mismas consultas](#12-la-comparación-justa-mismo-corpus-mismas-consultas)
13. [Cómo medir quién gana de verdad: Recall@k](#13-cómo-medir-quién-gana-de-verdad-recallk)
14. [Resumen final](#14-resumen-final)
15. [¿Qué sigue después?](#15-qué-sigue-después)

---

## 1. ¿Qué significa "representar" información?

Un ordenador no entiende palabras ni significados directamente: solo entiende números. Por eso, antes
de poder comparar una consulta con un documento, hace falta **traducir** ambos a algo que se pueda
calcular: números, listas de números (vectores), o estructuras más complejas.

A esa traducción la llamamos **representación**. Formalmente es una función que recibe "el objeto
original" (un texto) y devuelve "un objeto computable" (por ejemplo, un vector).

**Idea clave de toda la sesión:** *representar siempre implica elegir qué conservar y qué
descartar*. No existe una representación perfecta que lo conserve absolutamente todo — sería tan
complicada como el texto original y no serviría para calcular nada rápido. Toda representación
introduce lo que el notebook llama un **sesgo inductivo**: hace que ciertas relaciones sean fáciles de
detectar, y otras casi imposibles.

### Ejemplo cotidiano: fichar a alguien para un trabajo

Cuando resumes a una persona en un CV de una página, estás "representando" a esa persona: conservas
estudios, experiencia y habilidades, pero descartas su personalidad, su forma de hablar, sus gestos...
Un CV es útil para comparar candidatos rápidamente (eficiencia), pero pierde matices (no captura todo
lo que esa persona es). Exactamente lo mismo pasa cuando convertimos un texto en un vector: ganamos
capacidad de cálculo y perdemos matices.

### El mismo texto se puede representar de muchas maneras

Por ejemplo, el texto "coche eléctrico con buena autonomía" se podría representar como:

- una secuencia de letras (c-o-c-h-e-...);
- una secuencia de palabras (tokens): `["coche", "eléctrico", "con", "buena", "autonomía"]`;
- un conjunto de palabras sin repetir;
- un vector de frecuencias de palabras (lo que veremos en la sección 4);
- un vector "denso" aprendido por un modelo de inteligencia artificial (secciones 7 en adelante);
- una lista de entidades (por ejemplo: "coche" = producto, "eléctrico" = característica).

**Cambiar la representación puede cambiar por completo qué documentos parecen "cercanos" entre sí.**
Esta es la idea central de toda la sesión.

### ¿Qué debería conservar una buena representación?

Depende totalmente de para qué la vayas a usar. Algunas propiedades deseables en un sistema de
búsqueda:

| Propiedad | Qué significa | Ejemplo |
|---|---|---|
| **Discriminación** | Separar bien lo relevante de lo irrelevante | Que un documento sobre coches no aparezca al buscar recetas de cocina |
| **Invariancias útiles** | Reconocer que decir lo mismo con otras palabras sigue siendo relevante | "portátil" y "ordenador" deberían poder tratarse como relacionados |
| **Precisión léxica** | No perder identificadores exactos | Un código de error como `ERR_CONNECTION_RESET` debe encontrarse tal cual |
| **Comparabilidad** | Poder calcular un número consulta-documento | Necesitamos poder decir "esto se parece un 80% a lo que buscas" |
| **Eficiencia** | Poder buscar rápido en millones de documentos | No sirve un sistema que tarde una hora por búsqueda |
| **Robustez** | Aguantar errores, ruido, otros idiomas | Que funcione aunque haya una errata |
| **Interpretabilidad** | Poder explicar por qué salió ese resultado | Poder decir "salió primero porque contiene la palabra X" |

**Pregunta del notebook:** si buscas jurisprudencia por número de sentencia (por ejemplo,
"STS 245/2023"), necesitas **precisión léxica exacta** — no sirve de nada que el sistema entienda
"sentencias parecidas en tema", necesitas ESA sentencia concreta. Pero si buscas preguntas
formuladas con palabras distintas pero el mismo significado, necesitas **invariancia a la
paráfrasis** — ahí la coincidencia exacta de palabras ya no basta. Como ves, **un único sistema puede
no servir bien para ambos casos a la vez**. Esta tensión es el hilo conductor de toda la sesión.

---

## 2. Dos estrategias: sparse y dense

Existen dos grandes familias de representación de texto, y toda la sesión gira en torno a compararlas.

### Sparse (dispersa)

Cada posición del vector corresponde a **algo explícito**, normalmente una palabra concreta del
vocabulario. La inmensa mayoría de las posiciones valen **cero** (de ahí el nombre "dispersa" o
"sparse" en inglés: hay muy pocos valores distintos de cero, dispersos entre muchos ceros).

**Ejemplo cotidiano:** imagina una hoja de asistencia con 200 nombres de alumnos, donde marcas con un
1 quién vino a clase hoy y dejas en 0 a todos los demás. Si a una clase concreta solo vinieron 15
alumnos, tendrás 15 unos y 185 ceros. Eso es "sparse": la mayoría de las casillas están vacías
(en cero), pero cada casilla tiene un significado claro y fijo (un nombre concreto).

### Dense (densa)

Cada posición del vector es un número **aprendido** por un modelo de inteligencia artificial, y casi
todas las posiciones tienen algún valor distinto de cero. Sin embargo, ya no puedes señalar una
posición y decir "esto es la palabra tal": el significado está repartido entre todas las posiciones a
la vez, de una forma que ni siquiera los propios ingenieros que crean el modelo pueden explicar
posición por posición.

**Ejemplo cotidiano:** piensa en cómo describirías el "estilo" de una canción usando solo 10 números
del 0 al 100 (por ejemplo, para un algoritmo de recomendación musical): "energía", "positividad",
"tempo"... Ningún número por sí solo dice "esta canción es de rock", pero la **combinación** de los 10
números sitúa la canción en una zona del "mapa musical" cerca de canciones parecidas. Eso es la
intuición de "dense": pocos números, todos con algún valor, y el significado emerge de la combinación,
no de una sola casilla.

### Tabla comparativa

| Propiedad | Sparse | Dense |
|---|---|---|
| Coordenadas | Términos explícitos del vocabulario | Dimensiones aprendidas, sin significado individual claro |
| Dimensión típica | Tamaño del vocabulario (puede ser enorme) | Fija por el modelo (ej. 1024) |
| Valores distintos de cero | Muy pocos | Casi todos |
| Señal principal | Coincidencia literal de palabras | Compatibilidad de significado aprendida |
| Punto fuerte | Identificadores y términos exactos | Paráfrasis y variación en cómo se dice algo |

**Importante:** esto no es una carrera entre "lo viejo" (sparse) y "lo nuevo y mejor" (dense). BM25
(un método sparse, sección 6) sigue usándose muchísimo en sistemas reales de búsqueda hoy en día,
porque resuelve problemas distintos a los que resuelven los embeddings densos.

---

## 3. Representaciones sparse: el vocabulario como sistema de coordenadas

Imagina que decides que tu "sistema de coordenadas" son estas 5 palabras, en este orden fijo:

$$V = [\text{autonomía}, \text{batería}, \text{coche}, \text{eléctrico}, \text{precio}]$$

Cada posición del vector significa siempre la misma palabra. El texto "coche eléctrico con buena
autonomía" se convierte en:

$$[1, 0, 1, 1, 0]$$

Lo que significa: contiene "autonomía" (1 vez), no contiene "batería" (0 veces), contiene "coche"
(1 vez), contiene "eléctrico" (1 vez), no contiene "precio" (0 veces). Nota que la palabra "con" y
"buena" ni siquiera aparecen en el vocabulario elegido, así que simplemente se ignoran.

### Tokenizar: partir el texto en palabras

Antes de contar palabras hace falta decidir **cómo separar el texto en palabras** (esto se llama
"tokenizar"):

```python
def tokenizar(texto):
    return re.findall(r"\b\w+\b", texto.lower(), flags=re.UNICODE)

tokenizar("Coche eléctrico con buena autonomía.")
# ['coche', 'eléctrico', 'con', 'buena', 'autonomía']
```

Este tokenizador simplemente pasa todo a minúsculas y separa por palabras, ignorando la puntuación.

### Decisiones "ocultas" que parecen triviales pero no lo son

Antes incluso de construir el primer vector, ya tomamos muchísimas decisiones silenciosas:

- ¿Tratamos "Coche" y "coche" como la misma palabra? (aquí sí, por el `.lower()`)
- ¿Qué hacemos con tildes, guiones, números o emojis?
- ¿"eléctrico" y "eléctricos" son la misma palabra? (con este tokenizador, **no** — son dos palabras
  distintas, porque el tokenizador no sabe de gramática)
- ¿Cómo separamos textos en idiomas que no usan espacios entre palabras (como el chino)?

**Ejemplo que ilustra la limitación:** si buscas "coche eléctrico" pero el documento dice "coches
eléctricos" (en plural), este tokenizador tan simple los trata como palabras completamente distintas,
aunque para una persona sea obvio que hablan de lo mismo. Solucionar esto (por ejemplo, quitando los
plurales antes de comparar) se llama normalización o lematización, y es una decisión de diseño más,
no algo automático ni "gratis".

> **Conclusión de esta sección:** la tokenización no es un paso de "limpieza" sin importancia. Es
> una decisión de diseño que afecta directamente a qué se puede encontrar y qué no.

---

## 4. Bag of Words (BoW): contar palabras

"Bag of Words" (bolsa de palabras) es la representación sparse más simple: cuenta cuántas veces
aparece cada palabra del vocabulario en el documento, **sin importar en qué orden aparecen**.

$$\operatorname{BoW}(d)_j = \text{número de veces que aparece la palabra } V_j \text{ en el documento } d$$

### Ejemplo paso a paso

```python
documentos_bow = [
    "coche eléctrico con buena autonomía",
    "precio del coche eléctrico",
    "batería con autonomía y batería de repuesto",
]
```

Primero se construye el vocabulario juntando todas las palabras distintas de los 3 documentos (en
orden alfabético, para que sea reproducible):

```
['autonomía', 'batería', 'buena', 'coche', 'con', 'de', 'del', 'eléctrico', 'precio', 'repuesto', 'y']
```

Son 11 palabras en total. Cada documento se convierte en un vector de 11 números (uno por cada
palabra del vocabulario, en ese orden):

```
[1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0]  <- "coche eléctrico con buena autonomía"
[0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0]  <- "precio del coche eléctrico"
[1, 2, 0, 0, 1, 1, 0, 0, 0, 1, 1]  <- "batería con autonomía y batería de repuesto"
```

Fíjate en el tercer documento: la palabra "batería" aparece **2 veces** ("batería... de repuesto" y
antes "autonomía y batería"), por eso su componente vale 2 en lugar de 1.

### Sparsity: por qué la mayoría son ceros

En este ejemplo diminuto, el 54.5% de las celdas de la matriz son cero. En una colección real, con
miles de documentos y un vocabulario de decenas de miles de palabras, cada documento individual solo
usa una fracción minúscula de todo el vocabulario posible, así que la matriz completa puede tener
más del 99% de sus valores en cero.

**¿Por qué es esto una ventaja, y no solo un detalle curioso?** Porque permite construir un
**índice invertido**: en vez de guardar, para cada documento, todas sus 50 000 posiciones (la mayoría
en cero, un desperdicio enorme de memoria), se guarda, para cada palabra, la lista de qué documentos
la contienen. Es la misma idea que el índice alfabético al final de un libro de texto: en vez de leer
el libro entero buscando una palabra, vas directamente a la página donde dice que aparece.

### Qué conserva y qué destruye BoW

**Conserva:** qué palabras aparecen y cuántas veces (identidad y frecuencia de términos).

**Destruye:** el orden en que aparecen las palabras, la gramática, la cercanía entre palabras.

**Ejemplo muy ilustrativo del notebook:**

- "el perro muerde al hombre"
- "el hombre muerde al perro"

Ambas frases tienen **exactamente el mismo vector BoW**, `[1, 1, 1, 1, 1]`, ¡aunque signifiquen cosas
completamente opuestas (quién muerde a quién)! Esto no significa que BoW sea "malo" — significa que
BoW es útil solo cuando lo que importa es **qué palabras aparecen**, no **cómo están organizadas**.
Para muchas búsquedas (por ejemplo, buscar documentos "sobre perros y mordeduras" en general) esto no
importa demasiado; para entender exactamente "quién le hizo qué a quién", sí importaría muchísimo.

---

## 5. TF-IDF: no todas las palabras importan igual

BoW tiene un problema evidente: palabras muy comunes como "el", "la", "de", "con" aparecen en casi
todos los documentos y no ayudan nada a distinguir de qué trata realmente un texto. TF-IDF corrige
esto dándole más peso a las palabras que son **raras en la colección** (y por tanto, más
"informativas" cuando aparecen).

### Los tres ingredientes

- **TF (Term Frequency, "frecuencia del término"):** cuántas veces aparece la palabra **en este
  documento concreto**. Evidencia local.
- **DF (Document Frequency, "frecuencia documental"):** en cuántos documentos **distintos** de toda
  la colección aparece esa palabra, al menos una vez.
- **IDF (Inverse Document Frequency, "frecuencia inversa de documento"):** el "valor" o "rareza" de
  una palabra a nivel global. Cuantos **menos** documentos la contienen, **más alto** es su IDF.

Fórmula usada en el notebook (con suavizado para evitar divisiones problemáticas):

$$\operatorname{idf}(t)=\log\left(\frac{N+1}{\operatorname{df}(t)+1}\right)+1$$

No hace falta memorizarla — lo importante es la idea: **palabra rara → IDF alto → pesa más**;
**palabra común → IDF bajo → pesa menos**.

### Ejemplo del notebook

Con este corpus de 4 documentos:

```python
corpus_tfidf = [
    "la batería del coche eléctrico mejora la autonomía",
    "el precio del coche eléctrico depende de la batería",
    "la autonomía real disminuye con el frío",
    "manual de mantenimiento del motor diésel",
]
```

Algunos resultados de IDF:

| Palabra | En cuántos documentos aparece (df) | IDF |
|---|---|---|
| "la" | 3 de 4 | 1.223 (bajo → es muy común, aporta poco) |
| "batería" | 2 de 4 | 1.511 |
| "precio" | 1 de 4 | 1.916 (alto → aparece en un solo documento, es más distintiva) |
| "frío" | 1 de 4 | 1.916 |

**Ejemplo cotidiano:** en un examen tipo test, si una palabra de la pregunta aparece en las 4 opciones
de respuesta, esa palabra no te ayuda a decidir cuál es la correcta (es como "la", "el", "de"). Pero
si una palabra aparece solo en una de las opciones, esa palabra sí es una pista fuerte y útil (como
"precio" o "frío" en la tabla de arriba).

### Calcular TF-IDF y buscar con él

$$\operatorname{tfidf}(t,d)=\operatorname{tf}(t,d)\cdot\operatorname{idf}(t)$$

Cada palabra de un documento se multiplica por su frecuencia local y por su IDF global. Después, para
comparar la consulta con cada documento, se usa la **similitud del coseno** (ya la vimos en la sesión
1: mide solo la dirección del vector, ignorando su tamaño total).

Buscando `"autonomía batería"` en el corpus anterior, el resultado es:

```
0.474  D1: la batería del coche eléctrico mejora la autonomía
0.235  D3: la autonomía real disminuye con el frío
0.229  D2: el precio del coche eléctrico depende de la batería
0.000  D4: manual de mantenimiento del motor diésel
```

Tiene sentido: D1 contiene ambas palabras de la consulta, y las demás solo comparten una o ninguna.

### Los límites de TF-IDF

1. **¿Por qué "autonomía" pesa más que "la"?** Porque "autonomía" aparece en menos documentos
   (mayor IDF), mientras que "la" aparece en casi todos (menor IDF).
2. **¿Puede TF-IDF encontrar una paráfrasis sin palabras compartidas?** No. Si la consulta y el
   documento no comparten ni una sola palabra, el resultado del producto escalar es exactamente cero,
   sin importar cuán relacionados estén en significado.
3. **¿Qué pasa si duplico todo el contenido de un documento (lo pego dos veces seguidas)?** El coseno
   ayuda un poco (porque normaliza la dirección del vector), pero TF-IDF básico no controla
   explícitamente que "repetir mucho una palabra" no debería multiplicar su importancia sin límite, ni
   corrige el hecho de que un documento más largo tiene más oportunidades de contener palabras de la
   consulta por pura casualidad.

Esta última limitación es exactamente el motivo por el que se inventó **BM25**.

---

## 6. BM25: la mejora que se usa en sistemas reales

BM25 es, hoy en día, uno de los algoritmos de búsqueda por palabras más usados en el mundo (lo usan
buscadores, tiendas online, sistemas de documentación, Elasticsearch, etc.). Toma la misma idea básica
de TF-IDF (contar palabras y ponderarlas por rareza), pero le añade **dos mejoras muy importantes**:

### Mejora 1 — Saturación de frecuencia

Si una palabra aparece 1 vez en un documento, es una señal fuerte de que el documento habla de eso.
Pero si aparece 20 veces, **no es 20 veces más relevante** que si apareciera 1 vez — hay un punto en
el que repetir más la palabra deja de aportar información nueva.

```python
Saturación para un documento de longitud media:
f= 0 -> factor=0.000
f= 1 -> factor=1.000
f= 2 -> factor=1.429
f= 3 -> factor=1.667
f= 5 -> factor=1.923
f=10 -> factor=2.174
f=20 -> factor=2.326
f=50 -> factor=2.427
```

Observa cómo el "factor" crece muchísimo al pasar de 0 a 1 repetición, pero apenas crece al pasar de
20 a 50 repeticiones. La curva se **aplana** — eso es "saturación". Con los parámetros usados
($k_1=1.5$), el factor nunca puede superar $k_1 + 1 = 2.5$, sin importar cuántas veces se repita la
palabra.

**Ejemplo cotidiano:** si un vendedor te dice una vez "este coche es muy fiable", te lo crees. Si te
lo repite 30 veces seguidas en la misma frase, no te lo crees 30 veces más — probablemente sospeches
que está intentando manipularte repitiendo la misma palabra. BM25 refleja matemáticamente esta
intuición: repetir aporta cada vez menos.

### Mejora 2 — Normalización por longitud

Tres apariciones de una palabra en un documento de 10 palabras es una señal muchísimo más fuerte que
tres apariciones en un documento de 10 000 palabras (donde es casi inevitable que aparezca por pura
casualidad estadística).

```python
Misma frecuencia (f=3), distinta longitud:
longitud= 50 -> factor=1.905
longitud=100 -> factor=1.667
longitud=200 -> factor=1.333
longitud=500 -> factor=0.833
```

Con exactamente las mismas 3 repeticiones, el "factor" de relevancia baja según el documento es más
largo. Esto evita que documentos muy largos "ganen" solo por tener más texto y, por tanto, más
oportunidades de contener palabras de la consulta.

**Ejemplo cotidiano:** si buscas "manzana" y un documento de una frase contiene la palabra "manzana"
tres veces, seguro que habla de manzanas. Si un libro entero de 500 páginas menciona "manzana" tres
veces en total, probablemente sea solo una mención de pasada, no el tema principal del libro.

### La fórmula completa (no hace falta memorizarla)

$$\operatorname{BM25}(q,d)=\sum_{t\in q}\operatorname{IDF}(t)\;\frac{f(t,d)(k_1+1)}{f(t,d)+k_1\left(1-b+b\frac{|d|}{\operatorname{avgdl}}\right)}$$

| Símbolo | Qué es | Analogía |
|---|---|---|
| $f(t,d)$ | Cuántas veces aparece la palabra en el documento | El "TF" de siempre |
| $|d|$ | Longitud del documento (en palabras) | — |
| $\operatorname{avgdl}$ | Longitud promedio de todos los documentos de la colección | El "documento típico" con el que se compara |
| $k_1$ | Qué tan rápido se satura la frecuencia (normalmente entre 1.2 y 2.0) | Cuánto "límite" le pones a repetir palabras |
| $b$ | Cuánto pesa la longitud del documento (0 = nada, 1 = al máximo) | El "perdón" que le das a documentos largos |
| $\operatorname{IDF}(t)$ | Qué tan rara/informativa es la palabra a nivel global | Igual que en TF-IDF |

**Experimento del notebook:** si pones `b=0`, la longitud del documento deja de importar por
completo (se apaga la Mejora 2). Si cambias `k1`, cambia qué tan rápido se "aplana" la curva de
saturación (se ajusta la Mejora 1). Estos parámetros no inventan información nueva: solo controlan
**cuánto peso** le das a señales que ya existen.

### BM25 en acción: buscando en un corpus real

El notebook arma un pequeño corpus de 9 documentos sobre temas variados (errores técnicos, autonomía
de portátiles, y pagos con tarjeta), y prueba 3 consultas distintas:

```python
consultas = {
    "exacta": "ERR_CONNECTION_RESET Python",
    "semantica": "cómo gastar menos batería en el portátil",
    "mixta": "cancelar cargo duplicado en tarjeta",
}
```

Resultado con BM25:

```
[EXACTA] 'ERR_CONNECTION_RESET Python'
1. D01  score=4.464  Solucionar ERR_CONNECTION_RESET en Python al realizar peticiones HTTP.
2. D02  score=0.000  ...

[SEMANTICA] 'cómo gastar menos batería en el portátil'
1. D05  score=4.778  Cómo calibrar la batería de un portátil...
2. D03  score=3.210  Guía de compra de una batería portátil externa...
(D04, que habla de "reducir consumo energético y prolongar la autonomía", NI SIQUIERA aparece bien posicionado)

[MIXTA] 'cancelar cargo duplicado en tarjeta'
1. D07  score=7.876  Cancelar un cargo duplicado en tarjeta...
2. D06  score=1.964  Pasos para reclamar al banco un cobro repetido...
```

**Fíjate en el caso "semántica":** el documento realmente ideal (D04: "reducir el consumo energético y
prolongar la autonomía del ordenador") comparte muy pocas palabras exactas con la consulta ("gastar
menos batería en el portátil" vs. "reducir consumo energético... autonomía... ordenador"). BM25, al
depender de coincidencias de palabras, no logra "ver" que ambas frases dicen básicamente lo mismo con
otras palabras. A esto se le llama el **lexical gap** ("brecha léxica"), y es la motivación de la
siguiente parte de la sesión.

### Un punto a favor de BM25: se puede explicar

BM25 permite descomponer el score palabra por palabra, algo que los embeddings densos (sección 8) no
permiten hacer con la misma claridad:

```
D07: Cancelar un cargo duplicado en tarjeta: formulario y plazos de la entidad.
  cancelar   -> 1.897
  cargo      -> 1.897
  duplicado  -> 1.897
  en         -> 0.799
  tarjeta    -> 1.386
  TOTAL      -> 7.876
```

Puedes ver exactamente qué palabra aportó cuánto al resultado final. Esto es muy valioso cuando
necesitas poder **justificar** por qué un sistema devolvió cierto resultado (por ejemplo, en un
contexto legal o de auditoría).

### ¿Cuándo BM25 es especialmente bueno?

- códigos de error, referencias de producto, DOI, matrículas de coche, números de sentencia legal;
- nombres propios y términos poco comunes;
- jerga especializada donde una sola palabra cambia completamente el sentido;
- cuando necesitas poder explicar por qué salió cada resultado;
- dominios donde no hay datos suficientes para entrenar un modelo de IA;
- como primer filtro rápido y barato antes de aplicar técnicas más sofisticadas.

---

## 7. Representaciones dense y el problema del "lexical gap"

Ya vimos el problema: la consulta *"cómo gastar menos batería en el portátil"* y el documento ideal
*"consejos para reducir el consumo energético y prolongar la autonomía del ordenador"* dicen
prácticamente lo mismo, pero casi no comparten ninguna palabra clave. "gastar menos" vs. "reducir
consumo", "portátil" vs. "ordenador" — para una persona son sinónimos evidentes; para un sistema que
solo cuenta palabras exactas (como BM25), son totalmente distintos.

A esta brecha entre "cómo lo dice la consulta" y "cómo lo dice el documento relevante" se le llama
**lexical gap** (brecha léxica).

Una solución posible sería construir diccionarios de sinónimos a mano, pero eso es enorme trabajo
manual y nunca cubre todos los casos. La alternativa moderna es entrenar un modelo de inteligencia
artificial que aprenda, a partir de muchísimos ejemplos, **qué frases significan cosas parecidas**,
sin que nadie le diga explícitamente la regla "portátil = ordenador".

**Ejemplo cotidiano:** imagina un traductor humano muy experimentado. No traduce palabra por palabra;
entiende el significado completo de una frase y lo reformula naturalmente en otro idioma. Los
embeddings intentan algo parecido: no comparan letra por letra, sino que "entienden" el sentido general
y lo colocan en un mapa donde las cosas parecidas quedan cerca.

---

## 8. Qué es un embedding moderno

Un **embedding** es el resultado de pasar un texto por un modelo de inteligencia artificial entrenado
específicamente para esto, que produce un **vector denso** (recordemos: pocas dimensiones, casi todas
con algún valor).

$$f_\theta(\text{texto}) \in \mathbb{R}^d$$

Donde $d$ es el número de dimensiones del vector (por ejemplo, 1024), y $\theta$ representa todos los
"parámetros aprendidos" del modelo durante su entrenamiento.

### Cuatro características clave de un embedding moderno

1. **Dense (denso):** casi todas las posiciones tienen algún valor (a diferencia de BoW o TF-IDF).
2. **Learned (aprendido):** las posiciones no fueron diseñadas a mano como "esta es la columna de la
   palabra coche" — surgen del proceso de entrenamiento.
3. **Geométrico:** lo importante no es leer los números individuales, sino las **relaciones**
   entre vectores (qué tan cerca o lejos están dos textos en ese "mapa" de muchas dimensiones).
4. **Depende de la tarea:** el "mapa" que aprende el modelo refleja los datos y objetivos con los que
   se entrenó — no es una especie de "significado universal y perfecto". Un modelo entrenado para
   buscar en español puede comportarse peor en portugués, por ejemplo.

**Muy importante:** con embeddings densos **no se puede** decir "la posición 417 del vector significa
autonomía de batería". La información sobre "autonomía" está repartida (distribuida) entre muchas
dimensiones a la vez, mezclada con información sobre otros mil matices más. Por eso, mirar los
números crudos de un embedding no sirve de nada por sí solo — solo sirve **compararlos entre ellos**
(por ejemplo, con la similitud del coseno que vimos en la sesión 1).

### Ejemplo real del notebook

Al codificar el documento "Solucionar ERR_CONNECTION_RESET en Python..." con el modelo
Qwen3-Embedding-0.6B, se obtiene un vector de **1024 números**, cuyas primeras 8 posiciones son:

```
[0.0349, 0.1001, -0.0078, -0.0476, 0.0623, -0.0132, -0.0413, -0.0078]
```

Estos números por sí solos no dicen nada legible a simple vista. Solo cobran sentido cuando los
comparamos (con coseno) contra el vector de una consulta.

---

## 9. Cómo se entrena un embedding (intuición, sin fórmulas complicadas)

No hace falta entender las matemáticas de entrenamiento para usar embeddings, pero ayuda tener la
intuición general de **por qué funcionan**.

Durante el entrenamiento, al modelo se le muestran muchísimos ejemplos de este tipo:

- una **consulta** ($q$),
- un **documento correcto** que sí responde a esa consulta (llamado positivo, $d^+$),
- varios **documentos incorrectos** que no responden a esa consulta (llamados negativos, $d^-$).

El modelo ajusta sus números internos para que, en el "mapa" que va construyendo:

- la consulta y el documento correcto queden **cerca**;
- la consulta y los documentos incorrectos queden **lejos**.

Repitiendo esto millones de veces con ejemplos distintos, el modelo aprende, poco a poco, **qué
relaciones generales debe reflejar la geometría del mapa** (por ejemplo, que "portátil" y "ordenador"
suelen usarse en contextos similares), sin que nadie le programe esa regla a mano.

**Ejemplo cotidiano:** es parecido a cómo un niño aprende qué animales son "parecidos" sin que nadie
le dé una definición formal de "mamífero". Ve muchos ejemplos (perro se parece a gato, pero no se
parece a un pez), y poco a poco construye mentalmente "categorías" de similitud, aunque no pueda
explicar con palabras exactas cuál es la regla que está usando.

> **Nota importante:** la calidad final del embedding depende muchísimo de la calidad de esos
> ejemplos de entrenamiento (los positivos y negativos). Un modelo entrenado con ejemplos de mala
> calidad aprenderá relaciones de mala calidad, por muy sofisticado que sea el algoritmo.

---

## 10. Consulta y documento no siempre se tratan igual

Algo curioso (y fácil de pasar por alto) es que muchos modelos de embeddings modernos **no tratan
igual una consulta que un documento**, aunque ambos pasen por el mismo modelo.

¿Por qué? Porque cumplen roles distintos: una consulta suele ser corta e incompleta y expresa una
**necesidad** de información ("¿cómo ahorro batería?"), mientras que un documento suele ser más largo
y aportar **contenido** (un texto completo con consejos). Muchos modelos añaden una pequeña
"instrucción" o "etiqueta" para indicarle al modelo qué rol está cumpliendo cada texto:

- **Qwen3-Embedding** y **multilingual-e5-large-instruct** recomiendan añadir una instrucción
  únicamente a la consulta, y dejar el documento tal cual.
- **Cohere** usa explícitamente dos modos distintos: `search_query` (para consultas) y
  `search_document` (para documentos).

### Ejemplo concreto del notebook con Qwen3

```python
INSTRUCCION = "Given a Spanish web search query, retrieve relevant passages that answer the query"

def preparar_query_qwen(consulta):
    return f"Instruct: {INSTRUCCION}\nQuery: {consulta}"
```

Antes de convertir la consulta del usuario en un vector, se le "envuelve" con esta instrucción
explicando la tarea. El documento, en cambio, se codifica directamente, sin ninguna envoltura.

**Ejemplo cotidiano:** piensa en un traductor que traduce distinto según el contexto: si le dicen
"esto es una pregunta de un cliente", adopta un tono; si le dicen "esto es la respuesta oficial de la
empresa", adopta otro tono. El modelo de embeddings hace algo parecido: interpreta el texto de forma
distinta según si sabe que es "una necesidad de búsqueda" o "un contenido que puede responder a esa
necesidad".

**Advertencia del notebook:** si usas la plantilla de consulta para codificar documentos, o al revés,
estás usando el modelo de una forma distinta a como fue entrenado y evaluado. El vector seguirá teniendo
la misma cantidad de números, pero la geometría (las distancias que importan) puede dejar de tener
sentido. Es como usar mal un instrumento: sigue produciendo un número, pero ese número ya no significa
lo que se supone que debería significar.

---

## 11. Probando embeddings de verdad con LangChain

El notebook usa **LangChain** como una capa común para hablar con distintos modelos de embeddings, ya
sean modelos que se ejecutan en tu propio ordenador (como Qwen3-Embedding) o servicios en la nube de
pago (OpenAI, Google, Cohere).

La ventaja de LangChain es que **todos los modelos comparten la misma interfaz**, con solo dos
funciones:

- `embed_documents(lista_de_textos)` → convierte una lista de documentos en una lista de vectores
  (esto se hace **una sola vez**, al construir el índice de búsqueda).
- `embed_query(consulta)` → convierte una única consulta en un vector (esto se hace **cada vez** que
  alguien busca algo).

```python
def buscar_con_langchain(modelo_embeddings, consulta, documentos, k=4):
    vectores_documentos = modelo_embeddings.embed_documents(documentos)
    vector_consulta = modelo_embeddings.embed_query(consulta)
    scores = [coseno(vector_consulta, vector_doc) for vector_doc in vectores_documentos]
    orden = sorted(range(len(scores)), key=lambda i: (-scores[i], i))[:k]
    return [(scores[i], i, documentos[i]) for i in orden]
```

Fíjate en algo muy importante: **esta función no tiene ningún `if` que pregunte "¿qué proveedor
es?"**. Sirve exactamente igual para el modelo local Qwen3, para OpenAI, para Google o para Cohere,
porque todos implementan la misma interfaz común de LangChain. Esto es una gran ventaja práctica:
puedes cambiar de proveedor de embeddings sin tener que reescribir la lógica de búsqueda.

### Modelos de embeddings mencionados en el notebook (a fecha de septiembre 2026)

| Modelo | Tipo | Idea pedagógica relevante |
|---|---|---|
| **Qwen3-Embedding-0.6B** | Abierto (se descarga y ejecuta local) | Multilingüe, admite instrucciones, hasta 1024 dimensiones — es el que se usa como práctica principal |
| **multilingual-e5-large-instruct** | Abierto | Multilingüe, instrucción solo en la consulta |
| **BGE-M3** | Abierto | Puede producir a la vez señales sparse, dense y "multi-vector" |
| **OpenAI text-embedding-3-large** | Servicio de pago (API) | Muy fuerte en inglés y otros idiomas |
| **Google gemini-embedding-001 / 2** | Servicio de pago (API) | Texto, y en su versión 2 también imágenes/audio/vídeo |
| **Cohere embed-v4.0** | Servicio de pago (API) | Separa explícitamente `search_query` y `search_document` |

No hace falta memorizar esta lista — los nombres y versiones concretas cambian con el tiempo. Lo
importante es el criterio para elegir: idioma/dominio de tu caso de uso, objetivo (buscar/recuperar),
longitud de los textos, dimensión del vector, coste, privacidad (¿tus datos salen a un servicio
externo o se quedan en tu ordenador?), y si el modelo distingue consulta/documento.

### Ejemplo real de resultados con distintos proveedores

Buscando `"cómo gastar menos batería en el portátil"` con tres proveedores distintos, los tres
consiguen situar en primer lugar el documento correcto (D04, sobre "reducir consumo energético y
prolongar la autonomía"), aunque con puntuaciones de coseno distintas:

```
OpenAI:  1. D04  cos=0.673
Google:  1. D04  cos=0.803
Cohere:  1. D04  cos=0.379
```

**Detalle importante:** los números de coseno **no se pueden comparar directamente entre distintos
modelos** — un 0.379 en Cohere no es "peor" que un 0.803 en Google, porque cada modelo tiene su propia
escala interna de similitud. Lo que sí es comparable es **el orden (ranking)** que produce cada uno.

---

## 12. La comparación justa: mismo corpus, mismas consultas

Para comparar de verdad BM25 (sparse) contra un embedding (dense), hay que evitar hacer trampa dándole
a cada uno un ejemplo que le beneficie. El notebook usa exactamente **el mismo corpus de 9 documentos**
y **las mismas 3 consultas** para ambos métodos:

| Caso | Consulta | Qué pone a prueba | Documento ideal |
|---|---|---|---|
| Exacta | `ERR_CONNECTION_RESET Python` | Identificador técnico exacto | D01 |
| Semántica | `cómo gastar menos batería en el portátil` | El "lexical gap" (mismo sentido, otras palabras) | D04 |
| Mixta | `cancelar cargo duplicado en tarjeta` | Mezcla de coincidencia exacta y paráfrasis | D07 y D06 |

Resultado comparativo (los primeros 4 resultados de cada método):

```
CASO       BM25 TOP-4                     DENSE TOP-4
---------------------------------------------------------------------------
exacta     D01, D02, D03, D04             D01, D02, D09, D07
semantica  D05, D03, D09, D01             D03, D05, D04, D07
mixta      D07, D06, D01, D09             D07, D06, D08, D09
```

### Interpretando cada caso

**Caso "exacta"** — donde BM25 debería ganar: `ERR_CONNECTION_RESET` es una cadena de texto muy poco
común y muy discriminativa. BM25 la encuentra directamente por coincidencia exacta y le da un peso muy
alto (por IDF elevado). El modelo dense también reconoce el tema general de "errores de red", pero como
generaliza más, puede colar documentos algo menos precisos entre los primeros puestos.

**Caso "semántica"** — donde dense debería ganar: la consulta habla de "gastar menos batería" y el
documento ideal (D04) habla de "reducir consumo energético" y "prolongar autonomía". BM25, al no
compartir esas palabras exactas, se distrae con documentos que sí mencionan literalmente "batería" y
"portátil" (D05, D03), aunque hablen de otra cosa (calibrar o comprar una batería, no ahorrarla). El
embedding dense, en cambio, sí logra reconocer que D04 responde al sentido real de la pregunta.

**Caso "mixta"** — resultado ambiguo/mezclado: D07 coincide casi literalmente con la consulta (gana
claramente con ambos métodos). D06 expresa una idea relacionada pero con otras palabras ("cobro
repetido", "reclamar", "devolución" en vez de "cancelar cargo duplicado"). Ambos métodos logran
recuperar D06 en sus primeros puestos, cada uno por razones distintas.

> **Advertencia útil:** los resultados exactos pueden variar según la versión del modelo, el hardware
> o cómo se preprocesan los textos. Esto no invalida el ejercicio — al contrario, es justo la razón por
> la que hace falta **medir de forma sistemática** en vez de fiarse de una sola prueba, que es
> exactamente el tema de la siguiente sección.

---

## 13. Cómo medir quién gana de verdad: Recall@k

Mirar unos pocos resultados "a ojo" puede engañarte fácilmente. Para comparar métodos de forma seria,
hace falta una métrica objetiva. El notebook usa **Recall@k** ("exhaustividad en los primeros k
resultados"), una de las métricas más simples e intuitivas que existen.

### ¿Qué es Recall@k?

Primero, para cada consulta, un humano decide de antemano cuáles son los documentos realmente
relevantes (esto se llama "juicio de relevancia"):

```python
relevantes = {
    "exacta": {"D01"},
    "semantica": {"D04"},
    "mixta": {"D06", "D07"},
}
```

Después, Recall@k mide: **de todos los documentos que deberían haber salido, ¿qué fracción
efectivamente salió entre los primeros k resultados?**

$$\text{Recall@k} = \frac{|\text{documentos relevantes recuperados en el top-k}|}{|\text{documentos relevantes totales}|}$$

**Ejemplo cotidiano:** imagina que hay 2 llaves correctas escondidas entre 20 llaveros, y solo puedes
probar 3 llaveros. Si de esos 3 aciertas 1 de las 2 llaves correctas, tu "recall" es 1/2 = 0.5 (50%).
Si aciertas las 2, tu recall es 2/2 = 1.0 (100%), perfecto.

### Resultado del notebook

```
exacta     Recall@3 BM25=1.00  Dense=1.00
semantica  Recall@3 BM25=0.00  Dense=1.00
mixta      Recall@3 BM25=1.00  Dense=1.00
```

Este resultado confirma numéricamente lo que ya intuíamos mirando las tablas: en la consulta
"semántica", BM25 obtiene un Recall de **0.00** — ¡ni siquiera logra meter el documento correcto (D04)
entre sus 3 primeros resultados! Mientras tanto, el embedding dense logra un Recall perfecto de 1.00 en
los tres casos.

### Por qué esto importa mucho, y una advertencia importante

Esta pequeña evaluación con solo 3 consultas es útil para **aprender el concepto**, pero el notebook
advierte explícitamente: **no hay que confundir una demo con evidencia real**. Para evaluar un sistema
de verdad en producción hacen falta:

- muchas más consultas, representativas de cómo preguntan de verdad los usuarios reales;
- evaluadores humanos consistentes que decidan qué es "relevante" (y acuerden entre ellos);
- varias métricas complementarias, no solo Recall@k — por ejemplo **MRR** (qué tan arriba aparece el
  primer resultado correcto) o **nDCG** (que además tiene en cuenta el orden de varios resultados
  relevantes, no solo si aparecieron o no).

### Preguntas de reflexión que plantea el notebook

1. ¿Qué palabras exactas explican por qué BM25 dio ese resultado? (Esto se puede consultar de forma
   directa, como vimos en la sección 6.)
2. ¿Qué relación de significado podría explicar el resultado del modelo dense? (Esto es más difícil de
   "leer" directamente — solo podemos inferirlo por el contexto.)
3. ¿El juicio de "qué es relevante" es único, o podría haber más de una intención razonable detrás de
   la misma consulta?
4. ¿Cambiaría la conclusión si en vez de 9 documentos hubiera un millón?
5. ¿Qué otra consulta usarías para intentar **refutar** tu propia hipótesis, en vez de solo buscar
   confirmarla?

---

## 14. Resumen final

1. **Representar** es siempre elegir qué conservar y qué descartar — no existe una representación
   perfecta y universal.
2. **Bag of Words (BoW)** cuenta palabras usando el vocabulario como sistema de coordenadas, pero
   descarta completamente el orden de las palabras.
3. **TF-IDF** mejora BoW dándole más peso a las palabras raras (informativas) y menos peso a las
   palabras muy comunes.
4. **BM25** mejora TF-IDF añadiendo saturación de frecuencia (repetir una palabra aporta cada vez
   menos) y normalización por longitud (documentos largos no ganan solo por ser largos).
5. Un **embedding** moderno es un vector denso cuya "geometría" (qué está cerca de qué) se aprende
   automáticamente a partir de muchísimos ejemplos, en vez de programarse a mano.
6. La **consulta** y el **documento** a veces requieren un tratamiento distinto (instrucciones,
   prefijos) aunque pasen por el mismo modelo.
7. **Sparse** (BM25, TF-IDF) es imbatible en coincidencias exactas de palabras; **dense** (embeddings)
   puede cerrar el "lexical gap" entendiendo paráfrasis y sinónimos.
8. Una comparación justa entre métodos exige usar **el mismo corpus y las mismas consultas** para
   ambos, y medir con una métrica objetiva (como Recall@k), no solo mirar resultados "a ojo".
9. Las puntuaciones (scores) de BM25 o de coseno **no son probabilidades** y no deben compararse
   alegremente entre consultas distintas o entre modelos distintos.
10. En sistemas reales, lo habitual **no es elegir uno u otro**, sino combinar ambas señales — esto se
    llama **hybrid retrieval** (recuperación híbrida), y suele ir seguido de un paso de
    **reranking** (reordenar los mejores candidatos con un modelo todavía más preciso, pero más
    lento).

---

## 15. ¿Qué sigue después?

La frase que resume toda la sesión es:

> **Misma consulta + mismo corpus + distinta representación = distinta señal de relevancia y,
> potencialmente, distinto ranking.**

Ni sparse ni dense "ganan" siempre:

- si necesitas exactitud terminológica y poder explicar el resultado → sparse (BM25) tiene ventaja;
- si necesitas capturar paráfrasis y distintas formas de decir lo mismo → dense (embeddings) tiene
  ventaja;
- la mayoría de las búsquedas reales de usuarios mezclan ambas necesidades a la vez.

Por eso, el siguiente paso natural (que se plantea como continuación de esta sesión) es:

- **Hybrid retrieval:** combinar los resultados de BM25 y de un embedding dense en un único sistema,
  para aprovechar lo mejor de ambos mundos.
- **Reranking:** una vez que tienes, por ejemplo, los 50 candidatos más prometedores (recuperados
  rápido con sparse y/o dense), pasarlos por un modelo más lento pero más preciso que los reordene
  con mucho más cuidado antes de mostrar el top final al usuario.

Esta combinación (recuperación rápida y aproximada + reordenación lenta y precisa al final) es,
en la práctica, cómo funcionan la mayoría de los sistemas de búsqueda y de RAG (Retrieval-Augmented
Generation) usados en producción hoy en día.
