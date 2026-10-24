# Guía de estudio — Sesión 1: De los vectores a un mini sistema de *retrieval*

> Esta guía explica, con lenguaje sencillo y muchos ejemplos, todo lo que aparece en el notebook
> [`sesion_1_vectores_y_retrieval.ipynb`](./sesion_1_vectores_y_retrieval.ipynb). No hace falta saber
> matemáticas avanzadas: si sabes sumar, restar y multiplicar, puedes seguir toda la sesión.

## Índice

1. [¿Qué problema estamos resolviendo?](#1-qué-problema-estamos-resolviendo)
2. [¿Qué es un vector? (explicado desde cero)](#2-qué-es-un-vector-explicado-desde-cero)
3. [Operaciones básicas con vectores](#3-operaciones-básicas-con-vectores)
4. [Magnitud (el "tamaño" de un vector) y normalización](#4-magnitud-el-tamaño-de-un-vector-y-normalización)
5. [Distancias: ¿qué tan lejos están dos vectores?](#5-distancias-qué-tan-lejos-están-dos-vectores)
6. [La métrica que elijas puede cambiar el resultado](#6-la-métrica-que-elijas-puede-cambiar-el-resultado)
7. [El efecto de la escala (por qué hay que tener cuidado con las unidades)](#7-el-efecto-de-la-escala)
8. [Similitud: producto escalar y coseno](#8-similitud-producto-escalar-y-coseno)
9. [Construyendo un mini buscador (scoring, ranking, top-k)](#9-construyendo-un-mini-buscador-scoring-ranking-top-k)
10. [Resumen final](#10-resumen-final)
11. [¿Qué sigue en la sesión 2?](#11-qué-sigue-en-la-sesión-2)

---

## 1. ¿Qué problema estamos resolviendo?

Piensa en cualquier buscador: Google, el buscador de una tienda online, o el buscador de canciones de
Spotify. Todos hacen lo mismo en el fondo:

1. Tú escribes algo (una **consulta** o *query*), por ejemplo `"zapatillas rojas de correr"`.
2. El sistema tiene una gran colección de cosas (productos, documentos, canciones).
3. El sistema decide **qué tan relevante** es cada cosa de la colección respecto a tu consulta
   (esto se llama **scoring**, es decir, "puntuar").
4. Ordena todo de mayor a menor puntuación (esto se llama **ranking**).
5. Te muestra solo los mejores resultados, por ejemplo los primeros 10 (esto se llama **top-k**,
   donde `k` es el número de resultados que quieres, por ejemplo `k=10`).

En forma de esquema:

```
consulta  →  puntuar cada candidato  →  ordenar  →  quedarte con los mejores k
```

Este mismo esquema es el corazón de un sistema **RAG** (Retrieval-Augmented Generation, "generación
aumentada con recuperación"), que es como ChatGPT o un asistente busca fragmentos de texto relevantes
antes de responderte.

### El primer intento (muy simple): buscar la palabra literal

El notebook empieza con el ejemplo más ingenuo posible: mirar si la palabra de la consulta aparece
**tal cual** dentro del texto.

```python
documentos = [
    "Introducción a los sistemas de recuperación de información",
    "Representaciones vectoriales de texto",
    "Generación aumentada mediante recuperación o RAG",
    "Fundamentos de bases de datos relacionales",
]

consulta = "recuperación"

coincidencias = [d for d in documentos if consulta.lower() in d.lower()]
```

Esto encuentra las frases que contienen literalmente la palabra "recuperación". Funciona, pero tiene
un problema grande: **no entiende el significado**. Si buscaras `"recuperar"` (sin la "ción") o
`"búsqueda"` (que significa casi lo mismo), este sistema no encontraría nada, aunque para una persona
esas palabras estén claramente relacionadas.

**Ejemplo cotidiano:** imagina una biblioteca donde el bibliotecario solo te ayuda si dices el título
exacto de un libro, letra por letra. Si te equivocas en una tilde, no te ayuda. Eso es justo la
limitación de la búsqueda literal.

La gran pregunta que resuelve el resto de la sesión es:

> **¿Cómo convertimos texto (o cualquier otra cosa) en números que se puedan comparar
> matemáticamente, para que el ordenador pueda decidir qué tan "parecidas" son dos cosas?**

La respuesta: convirtiendo cada elemento en un **vector**.

---

## 2. ¿Qué es un vector? (explicado desde cero)

Un vector es, sencillamente, **una lista ordenada de números**. Nada más misterioso que eso.

```python
vector = [3, 1, 0]
```

Cada número de la lista se llama **componente**, y **la posición importa**. El primer número siempre
significa lo mismo, el segundo siempre significa otra cosa, etc.

### Ejemplo de la vida real: una ficha de personaje de videojuego

Imagina que describes a un personaje con tres números: `(vida, fuerza, velocidad)`.

- Personaje A: `(100, 20, 5)` → mucha vida, fuerza media, poca velocidad.
- Personaje B: `(50, 10, 15)` → poca vida, poca fuerza, mucha velocidad.

Aquí la **posición 1 siempre es "vida"**, la **posición 2 siempre es "fuerza"**, etc. Si mezclaras el
orden, los números dejarían de tener sentido. Eso es exactamente lo que pasa con los vectores: no
puedes comparar el vector de un personaje de videojuego con el vector de un documento de texto, porque
cada posición significa algo distinto en cada espacio.

### El ejemplo del notebook: representar documentos por frecuencia de palabras

En el notebook se usan 3 características para describir documentos:

1. cuántas veces aparece la palabra "recuperación",
2. cuántas veces aparece la palabra "vector",
3. cuántas veces aparece "base de datos".

```python
caracteristicas = ("recuperación", "vector", "base de datos")

documento_a = [3, 1, 0]   # menciona mucho "recuperación", algo "vector", nada de "base de datos"
documento_b = [0, 1, 4]   # no menciona "recuperación", algo "vector", mucho "base de datos"
```

Es decir: el **Documento A** probablemente habla de sistemas de recuperación, y el **Documento B**
probablemente habla de bases de datos. Todavía no comparamos nada, solo hemos "traducido" el texto a
números.

### Dimensionalidad: cuántos números tiene el vector

El número de componentes de un vector se llama su **dimensión** (o dimensionalidad).

- `(2, 5)` tiene 2 dimensiones.
- `(2, 5, 1)` tiene 3 dimensiones.
- Un vector de frecuencias de palabras en un texto largo puede tener miles de dimensiones (una por
  cada palabra distinta del vocabulario).

**Regla de oro:** solo puedes comparar dos vectores si tienen la **misma dimensión** y **el mismo
significado en cada posición**. Que tengan la misma longitud no es suficiente: un vector
`(edad, altura)` y un vector `(precio, stock)` tienen ambos 2 componentes, pero comparar uno con otro
no tiene ningún sentido, porque describen cosas distintas.

```python
def misma_dimension(a, b):
    return len(a) == len(b)

misma_dimension([1, 2, 3], [4, 5, 6])   # True  → se pueden comparar
misma_dimension([1, 2], [1, 2, 3])       # False → no se pueden comparar
```

### Interpretación geométrica: un vector es también un punto en el espacio

Otra forma de pensar en un vector es como **una flecha que sale del origen (el punto 0,0) y llega
hasta un punto**.

- En 1 dimensión: es simplemente un punto sobre una recta numérica.
- En 2 dimensiones, `(3, 2)` es un punto: avanzas 3 pasos a la derecha y 2 pasos hacia arriba.
- En 3 dimensiones, `(3, 2, 5)` sería lo mismo pero añadiendo "profundidad".
- En más dimensiones ya no podemos dibujarlo, pero la idea de "dirección" y "distancia" se mantiene
  igual matemáticamente.

El notebook dibuja esto con una flecha desde `(0,0)` hasta `(3,2)`. Es literalmente lo mismo que
señalar un punto en un mapa dando "3 calles al este y 2 al norte".

---

## 3. Operaciones básicas con vectores

Las operaciones con vectores se hacen **componente a componente**, es decir, sumas el primer número
con el primer número, el segundo con el segundo, y así sucesivamente.

### Suma

```python
a = [2, 1]
b = [1, 3]
sumar(a, b)  # [3, 4]   →  (2+1, 1+3)
```

**Ejemplo cotidiano:** si el lunes vendiste `[5 camisetas, 2 pantalones]` y el martes vendiste
`[3 camisetas, 4 pantalones]`, el total de dos días es `[8 camisetas, 6 pantalones]`. Eso es una suma
de vectores.

### Resta

```python
restar(a, b)  # [1, -2]   →  (2-1, 1-3)
```

**Ejemplo:** si tenías `[100€, 50 dulces]` y gastaste `[30€, 20 dulces]`, te queda
`[70€, 30 dulces]`. Es una resta de vectores.

### Multiplicación por un número (escalar)

Multiplicar un vector por un número (llamado "escalar" porque cambia la "escala", el tamaño) multiplica
**cada componente** por ese número.

```python
escalar(2, [2, 1])   # [4, 2]    → el doble en cada dirección
escalar(-1, [2, 1])  # [-2, -1]  → apunta exactamente en dirección contraria
```

**Ejemplo cotidiano:** si una receta para 1 persona necesita `[2 huevos, 200g harina]`, para 4
personas necesitas `escalar(4, [2, 200]) = [8 huevos, 800g harina]`.

Multiplicar por un número negativo **invierte la dirección** de la flecha (apunta hacia el lado
opuesto), pero mantiene la misma "línea".

### Por qué esto importa para el buscador

Estas operaciones son los ladrillos con los que se construyen cosas más complejas, como calcular
distancias y similitudes (secciones 5 y 8). Sin suma, resta y multiplicación por escalar no podríamos
definir ninguna de las fórmulas siguientes.

---

## 4. Magnitud (el "tamaño" de un vector) y normalización

### Magnitud = qué tan "largo" es el vector

La **magnitud** (o norma) de un vector mide su longitud, como si fuera la distancia en línea recta
desde el origen hasta el punto que representa. Se calcula así:

$$\|\mathbf{x}\|_2=\sqrt{x_1^2+x_2^2+\cdots+x_n^2}$$

En palabras: eleva cada número al cuadrado, súmalos todos, y saca la raíz cuadrada del resultado.
Es literalmente el **teorema de Pitágoras**, generalizado a más de 2 dimensiones.

```python
magnitud([3, 4])   # 5.0     porque sqrt(3² + 4²) = sqrt(9+16) = sqrt(25) = 5
```

**Ejemplo cotidiano:** si caminas 3 cuadras al este y 4 cuadras al norte, la distancia en línea recta
(como vuela un pájaro) desde tu punto de partida es de 5 cuadras. Ese "5" es la magnitud del vector
`(3, 4)`.

### Normalización = quedarte solo con la dirección, sin el tamaño

**Normalizar** un vector significa dividir cada componente entre la magnitud, de forma que el vector
resultante tenga siempre longitud 1, pero **apunte exactamente en la misma dirección**.

```python
normalizar([3, 4])   # [0.6, 0.8]
magnitud([0.6, 0.8])  # 1.0
```

**Ejemplo cotidiano:** imagina una flecha de brújula. No importa si dibujas la flecha de 1 cm o de
10 cm, ambas te dicen "el norte está por allí". Normalizar es como forzar a que la flecha siempre mida
lo mismo (una unidad), quedándonos solo con la información de "hacia dónde apunta", ignorando "qué tan
larga era originalmente".

⚠️ **Caso especial:** el vector `[0, 0]` (el vector cero) no se puede normalizar, porque no apunta
hacia ninguna dirección — y dividir entre magnitud 0 no está definido matemáticamente (sería dividir
entre cero). El notebook lanza un error explícito en este caso, en lugar de dar un resultado
incorrecto en silencio.

**¿Por qué importa esto para un buscador?** Porque a veces queremos comparar documentos ignorando su
longitud (un documento largo no debería "ganar" solo por tener más palabras repetidas). Volveremos a
esto en la sección 8, con la similitud del coseno.

---

## 5. Distancias: ¿qué tan lejos están dos vectores?

Una **distancia** es un número que dice qué tan separados están dos puntos. Cuanto **menor** sea la
distancia, más "parecidos" o "cercanos" son. Hay varias formas de medir esta separación, y cada una
tiene su propia lógica.

### Distancia euclídea (la distancia "normal", en línea recta)

$$d_2(\mathbf{a},\mathbf{b})=\sqrt{\sum_i |a_i-b_i|^2}$$

Es la misma idea que la magnitud, pero aplicada a la diferencia entre dos vectores en vez de a un solo
vector. Es literalmente "la distancia que recorrería un pájaro volando en línea recta" entre dos
puntos.

```python
distancia_euclidea([1, 2], [4, 6])  # 5.0
```

### Distancia Manhattan (la distancia "en cuadrícula", como caminar por calles)

$$d_1(\mathbf{a},\mathbf{b})=\sum_i |a_i-b_i|$$

Suma las diferencias absolutas en cada dirección, sin tomar raíz cuadrada. Se llama así porque en una
ciudad con calles en cuadrícula (como Manhattan, en Nueva York), no puedes caminar en diagonal
atravesando edificios: tienes que caminar primero unas cuadras en una dirección y luego otras cuadras
en la otra dirección.

```python
distancia_manhattan([1, 2], [4, 6])  # 7.0   →  |1-4| + |2-6| = 3 + 4 = 7
```

**Ejemplo cotidiano:** si tu oficina está a 3 cuadras al este y 4 cuadras al norte de tu casa, un
pájaro volaría 5 cuadras (euclídea), pero tú caminando por las calles recorrerías 7 cuadras
(Manhattan).

### Distancia de Minkowski (la fórmula general que las incluye a todas)

$$d_p(\mathbf{a},\mathbf{b})=\left(\sum_i |a_i-b_i|^p\right)^{1/p}$$

Es una fórmula "genérica" con un parámetro `p` que puedes ajustar:

- si `p = 1` → obtienes la distancia Manhattan;
- si `p = 2` → obtienes la distancia euclídea;
- puedes usar cualquier otro valor de `p ≥ 1` para obtener variantes intermedias o más extremas.

```python
distancia_minkowski([1, 2], [4, 6], p=3)  # 4.4979...
```

No necesitas memorizar esta fórmula: solo entiende que euclídea y Manhattan son **casos particulares**
de una misma idea general.

### Distancia de Chebyshev (solo importa el peor salto)

$$d_\infty(\mathbf{a},\mathbf{b})=\max_i |a_i-b_i|$$

Aquí no sumamos nada: simplemente miramos **cuál es la mayor diferencia** entre todas las
componentes, e ignoramos el resto.

```python
distancia_chebyshev([1, 2], [4, 6])  # 4   → el máximo entre |1-4|=3 y |2-6|=4
```

**Ejemplo cotidiano:** en el juego de ajedrez, el rey puede moverse una casilla en cualquier
dirección (incluida la diagonal). El número mínimo de movimientos que necesita el rey para llegar de
una casilla a otra es exactamente la distancia de Chebyshev entre ambas casillas.

### Propiedades que toda distancia "de verdad" debe cumplir

El notebook comprueba 4 reglas básicas que cualquier distancia razonable debe cumplir siempre:

1. **Nunca es negativa**: `d(a,b) ≥ 0`.
2. **Solo es cero si son el mismo punto**: `d(a,b) = 0` únicamente cuando `a = b`.
3. **Es simétrica**: la distancia de A a B es la misma que de B a A → `d(a,b) = d(b,a)`.
4. **Desigualdad triangular**: ir directo de A a C nunca es más largo que pasar por un punto
   intermedio B → `d(a,c) ≤ d(a,b) + d(b,c)`.

**Ejemplo cotidiano de la desigualdad triangular:** ir caminando directo de tu casa al cine nunca
puede ser más largo que ir primero a la casa de un amigo y luego al cine. El camino directo siempre es,
como mucho, igual de largo (o más corto) que cualquier desvío.

---

## 6. La métrica que elijas puede cambiar el resultado

Este es uno de los puntos más importantes de la sesión: **no existe una única forma "correcta" de
medir qué tan cerca están dos cosas**. La métrica que elijas puede cambiar completamente el resultado.

### Ejemplo del notebook

Consulta `q = (0, 0)`. Dos candidatos:

- Candidato A: `(3, 0)`
- Candidato B: `(2, 2)`

| Métrica    | Distancia a A | Distancia a B | ¿Quién gana (menor distancia)? |
|------------|---------------|----------------|----------------------------------|
| Euclídea   | 3.0           | 2.83           | **B** |
| Manhattan  | 3.0           | 4.0            | **A** |
| Chebyshev  | 3             | 2              | **B** |

¡El "vecino más cercano" cambia dependiendo de qué fórmula uses! Esto no es un error: cada métrica
representa una noción distinta de "cercanía", y ninguna es universalmente mejor. Depende del problema
que estés resolviendo.

**Ejemplo cotidiano:** si buscas el restaurante "más cercano" en línea recta (como vuela un pájaro),
puede que en la práctica esté al otro lado de un río sin puentes cerca, y en la vida real tardes mucho
más en llegar que a otro restaurante que en línea recta parecía "más lejos". La distancia euclídea y la
distancia "real caminando" (más parecida a Manhattan) pueden dar respuestas distintas.

---

## 7. El efecto de la escala

Otro punto crucial: si una característica usa números mucho más grandes que otra, **puede dominar la
comparación aunque en realidad no sea más importante**.

### Ejemplo del notebook: personas descritas como `(edad, ingresos)`

```python
consulta = [40, 30_000]   # 40 años, 30 000€ de ingresos

candidatos = {
    "A": [41, 60_000],   # edad muy parecida (41 vs 40), ingresos muy distintos
    "B": [60, 31_000],   # edad muy distinta (60 vs 40), ingresos casi iguales
}
```

Sin hacer nada especial, la distancia euclídea da:

- A: distancia ≈ 30 000 (dominada casi enteramente por la diferencia de ingresos)
- B: distancia ≈ 1 000

**Ganador: B.** Pero espera... A tiene casi la misma edad que la consulta (41 vs 40), y B tiene una
edad mucho más distinta (60 vs 40). El problema es que los ingresos se miden en **decenas de miles**, y
la edad se mide en **decenas**, así que una pequeña diferencia de ingresos (30 000€) pesa muchísimo más
que una gran diferencia de edad (20 años), simplemente por la escala de las unidades, no porque
realmente sea "más importante".

### La solución: reescalar

Si dividimos cada característica entre un rango de referencia (por ejemplo, 40 años y 80 000€),
ambas quedan en una escala comparable, entre 0 y 1 aproximadamente:

```python
escalas = [40, 80_000]
# consulta reescalada, candidatos reescalados...
```

Después de reescalar, el resultado se invierte: **ahora gana A**, porque su edad es mucho más
parecida y, en la escala común, eso pesa lo que debería pesar.

**Ejemplo cotidiano:** imagina que comparas casas por `(número de habitaciones, precio en euros)`. El
precio (cientos de miles) va a aplastar completamente a las habitaciones (números de un dígito) si no
reescalas. Es como comparar peras (unidades pequeñas) con toneladas (unidades enormes) sin convertir
ambas al mismo sistema.

> **Idea clave:** reescalar no es "neutral". Al elegir cómo reescalar, tú **decides** cuánto peso le
> das a cada característica. No hay una única forma correcta; depende de qué te importa realmente medir.

---

## 8. Similitud: producto escalar y coseno

Hasta ahora hemos hablado de **distancias** (menor = más parecido). Ahora vemos **similitudes**
(mayor = más parecido), que es el enfoque más común en sistemas de búsqueda de texto.

### Producto escalar (o producto punto)

$$\mathbf{a}\cdot\mathbf{b}=\sum_i a_i b_i$$

Multiplicas cada componente por su pareja y sumas todo.

```python
producto_escalar([1, 0], [2, 0])    # 2   → misma dirección, resultado positivo
producto_escalar([1, 0], [0, 3])    # 0   → direcciones perpendiculares ("ortogonales")
producto_escalar([1, 0], [-2, 0])   # -2  → direcciones opuestas
```

- **Positivo** → los vectores apuntan más o menos en la misma dirección (ángulo menor a 90°).
- **Cero** → son perpendiculares entre sí (no comparten ninguna dirección en común).
- **Negativo** → apuntan en direcciones opuestas.

El problema del producto escalar es que **mezcla dos cosas a la vez**: qué tan alineados están los
vectores (dirección) y qué tan "grandes" son (magnitud). Esto puede ser confuso:

```python
consulta = [1, 1]
documento_corto = [1, 1]     # producto = 2.0
documento_largo = [10, 10]   # producto = 20.0  ← ¡mucho más alto, pero apunta exactamente igual!
```

El documento largo obtiene una puntuación 10 veces mayor solo porque sus números son más grandes
(por ejemplo, porque el documento tiene más palabras repetidas), **no** porque hable de algo más
relevante.

**Ejemplo cotidiano:** imagina comparar dos reseñas de un restaurante: una dice "bueno, bueno" y la
otra dice "bueno" 20 veces seguidas. El producto escalar diría que la segunda reseña es "20 veces más
relevante" simplemente por ser repetitiva, no porque diga algo distinto o mejor.

### Similitud del coseno: solo mirar la dirección, ignorando el tamaño

$$\cos(\mathbf{a},\mathbf{b})=\frac{\mathbf{a}\cdot\mathbf{b}}{\|\mathbf{a}\|\|\mathbf{b}\|}$$

La similitud del coseno es el producto escalar, **pero dividido entre las magnitudes de ambos
vectores**. Esto "cancela" el efecto del tamaño y deja solo el efecto de la dirección (el ángulo entre
ellos).

```python
similitud_coseno([1, 1], [1, 1])     # 1.0   → misma dirección exacta
similitud_coseno([1, 1], [10, 10])   # 1.0   → ¡también 1.0! misma dirección, distinto tamaño
similitud_coseno([1, 1], [1, 0])     # 0.707 → direcciones algo distintas
```

Con el coseno, el documento corto y el documento largo del ejemplo anterior obtienen **la misma
puntuación (1.0)**, porque apuntan exactamente en la misma dirección — el coseno ignora
completamente cuántas veces se repite cada palabra en total, y se centra solo en la "proporción" o
"perfil" del documento.

El valor del coseno siempre está entre **-1 y 1** (o entre 0 y 1 si los números nunca son negativos,
como en conteos de palabras):

- **1** → misma dirección exacta (máxima similitud).
- **0** → direcciones perpendiculares (nada en común).
- **-1** → direcciones exactamente opuestas.

**Ejemplo cotidiano:** el coseno es como comparar la "receta" de dos platos en vez de la cantidad
total de comida. Una pizza pequeña y una pizza grande con exactamente los mismos ingredientes en las
mismas proporciones son "la misma receta" (coseno = 1), aunque una pese mucho más que la otra en
gramos totales (producto escalar muy distinto).

### Un truco útil: normalizar + producto escalar = coseno

Si normalizas ambos vectores primero (sección 4), su magnitud pasa a ser 1, y entonces el simple
producto escalar entre ellos **ya es exactamente igual** a la similitud del coseno:

```python
similitud_coseno(a, b) == producto_escalar(normalizar(a), normalizar(b))  # True
```

Esto es muy práctico en sistemas reales: puedes normalizar toda tu colección de documentos **una sola
vez**, y luego, para cada nueva consulta, solo necesitas hacer productos escalares (que son rápidos de
calcular), en lugar de recalcular divisiones por magnitud cada vez.

### Producto escalar vs. coseno: pueden dar rankings distintos

```python
q = [1, 1]
candidatos = {"A": [1, 0], "B": [3, 3], "C": [10, 0]}
```

| Candidato | Producto escalar | Ranking por producto | Coseno | Ranking por coseno |
|-----------|-------------------|------------------------|--------|----------------------|
| A         | 1                 | 3º                     | 0.707  | 2º (empatado) |
| B         | 6                 | 2º                     | 1.0    | 1º |
| C         | 10                | 1º                     | 0.707  | 2º (empatado) |

Con producto escalar gana C (porque tiene números muy grandes), pero con coseno gana B (porque
apunta exactamente igual que la consulta), mientras que A y C quedan empatados (misma dirección entre
sí, aunque de distinto tamaño). Esto confirma otra vez la lección de la sección 6: **la elección de
métrica cambia el resultado**, así que hay que elegirla a propósito, no por accidente.

---

## 9. Construyendo un mini buscador (scoring, ranking, top-k)

Con todo lo anterior, el notebook arma un buscador de texto completo, usando solo Python estándar
(sin librerías de inteligencia artificial). Los pasos son:

### Paso 1 — Tokenizar: partir el texto en palabras

```python
def tokenizar(texto):
    return re.findall(r"\b\w+\b", texto.lower(), flags=re.UNICODE)
```

Convierte, por ejemplo, `"La Recuperación de Información"` en
`["la", "recuperación", "de", "información"]` (todo en minúsculas, separado en palabras individuales).

### Paso 2 — Construir el vocabulario: la lista de todas las palabras posibles

```python
vocabulario = construir_vocabulario(coleccion)
```

Es la lista (ordenada, sin repetir) de **todas** las palabras distintas que aparecen en toda la
colección de documentos. Esta lista define las "posiciones" del vector: la posición 1 siempre
corresponde a la misma palabra, la posición 2 a otra palabra, etc. — igual que en el ejemplo de
`(vida, fuerza, velocidad)` de la sección 2.

En el ejemplo del notebook, con 6 documentos, el vocabulario tiene 46 palabras distintas, así que cada
documento se representará como **un vector de 46 números**.

### Paso 3 — Vectorizar: contar cuántas veces aparece cada palabra

```python
def vectorizar_frecuencias(texto, vocabulario):
    conteos = Counter(tokenizar(texto))
    return [conteos[termino] for termino in vocabulario]
```

Por cada palabra del vocabulario, cuenta cuántas veces aparece en el texto. El resultado es un vector
larguísimo, lleno sobre todo de ceros (porque cada documento solo usa unas pocas palabras del
vocabulario completo), con algunos números mayores que cero en las posiciones de las palabras que sí
aparecen.

**Ejemplo concreto:**

> Texto: *"Los vectores permiten comparar documentos mediante distancias y similitudes."*
>
> Componentes distintas de cero: `{comparar: 1, distancias: 1, documentos: 1, los: 1, mediante: 1,
> permiten: 1, similitudes: 1, vectores: 1, y: 1}`
>
> Todas las demás de las 46 posiciones del vector valen 0.

### Paso 4 — Vectorizar la consulta en el mismo espacio

La consulta del usuario se convierte en un vector usando **exactamente el mismo vocabulario** que los
documentos. Esto es fundamental: la consulta y los documentos tienen que "hablar el mismo idioma
numérico" para poder compararse (recuerda la regla de oro de la sección 2).

### Paso 5 — Puntuar (scoring): calcular el coseno entre la consulta y cada documento

Por cada documento de la colección, se calcula la similitud del coseno entre su vector y el vector de
la consulta. Cuanto más alto el número, más "parecido" es el documento a lo que se preguntó.

### Paso 6 — Ordenar (ranking) y quedarse con los mejores (top-k)

```python
def recuperar(consulta, documentos, vocabulario, vectores_documentos, k=3):
    ...
    ranking = sorted(resultados, key=lambda r: (-r["score"], r["indice"]))
    return ranking[:k]
```

Se ordenan todos los documentos de mayor a menor puntuación, y se devuelven solo los primeros `k`
(por ejemplo, los 3 mejores). Fíjate que el criterio de orden usa **dos claves**: primero el score
(de mayor a menor, por eso el signo negativo), y si hay empate, el índice original del documento — así
el resultado siempre es el mismo, sin sorpresas aleatorias.

### Ejemplo completo, paso a paso

```python
consulta = "comparar documentos con vectores"
```

Resultado:

```
1. score=0.577  → "Los vectores permiten comparar documentos mediante distancias y similitudes."
2. score=0.192  → "El ranking ordena documentos según su puntuación de relevancia."
3. score=0.183  → "La recuperación de información busca documentos relevantes para una consulta."
```

Tiene sentido: el primer resultado comparte las palabras "comparar", "documentos" y "vectores"
directamente con la consulta, por eso tiene el score más alto.

### El límite de este sistema: solo entiende palabras exactas

```python
consulta_fuera_vocabulario = "hallar pasajes parecidos"
```

Ninguna de esas tres palabras aparece en la colección de documentos, así que el vector de la consulta
es **el vector cero** `[0, 0, 0, ...]`. Como el coseno no está definido cuando la magnitud es cero
(sería dividir entre cero), el sistema responde honestamente: *"La consulta no contiene términos
conocidos por el sistema."* — en vez de inventar una respuesta incorrecta.

Esto pasa aunque, para una persona, `"hallar pasajes parecidos"` esté claramente relacionado con
"recuperación de información". El sistema, tal como está construido, **no entiende sinónimos ni
significado**, solo coincidencias exactas de palabras. Esta limitación es exactamente el motivo por el
que existen técnicas más avanzadas (los llamados *embeddings* o representaciones "densas"), que verás
en la sesión 2.

---

## 10. Resumen final

La sesión completa recorre esta cadena de ideas, de principio a fin:

1. **Problema:** dada una consulta, encontrar lo más relevante dentro de una colección.
2. **Representación:** convertir texto (o cualquier otra cosa) en vectores de números.
3. **Geometría:** entender qué significan la dimensión, la dirección y la magnitud de un vector.
4. **Operaciones:** sumar, restar, multiplicar por un número y normalizar vectores.
5. **Comparación:** medir cercanía con distancias (menor = mejor) o similitudes (mayor = mejor).
6. **Decisiones importantes:** la métrica elegida y la escala de las unidades cambian el resultado —
   no hay una única forma "correcta", hay que elegir a propósito.
7. **Retrieval real:** puntuar todos los candidatos, ordenarlos, y devolver solo los mejores k.

### Ideas para recordar siempre

- Un vector solo tiene sentido si sabes **qué representa cada posición**.
- "Más cercano" **depende** de qué métrica y qué escala uses — no es un hecho absoluto.
- El producto escalar mezcla **dirección** y **tamaño**; el coseno se queda solo con la
  **dirección**.
- El coseno es matemáticamente lo mismo que el producto escalar de los vectores ya normalizados.
- Un sistema puede estar matemáticamente bien construido y aun así dar malos resultados, si la forma
  de representar la información (el "vector") es demasiado simple para capturar el significado real.

---

## 11. ¿Qué sigue en la sesión 2?

Los vectores de frecuencias de palabras usados aquí se llaman **representaciones dispersas**
(*sparse*, en inglés): tienen muchísimas dimensiones, y casi todos los valores son cero. Su ventaja es
que son fáciles de interpretar (cada posición es literalmente una palabra), pero su gran defecto es que
**no entienden significado**: "recuperar" y "recuperación" son dos posiciones totalmente distintas
para este sistema, aunque signifiquen casi lo mismo.

En la próxima sesión se comparará esto con **representaciones densas** (*dense*), donde:

- hay muchas menos dimensiones (por ejemplo, cientos, en vez de decenas de miles),
- los números ya no corresponden a una palabra concreta y no se pueden "leer" directamente,
- pero son capaces de capturar relaciones de significado, para que textos parecidos en sentido (aunque
  usen palabras distintas) queden matemáticamente cerca.

La arquitectura general del sistema **no cambiará**:

```
texto  →  vector  →  comparación  →  ranking  →  top-k
```

Lo único que cambiará —y con un impacto muy grande en la calidad de los resultados— es **cómo se
construye ese vector**. Ese salto (de contar palabras a usar *embeddings*) es la base de cómo funcionan
los sistemas RAG modernos.

### Preguntas para repasar antes de la próxima sesión

1. ¿Por qué dos textos que no comparten ninguna palabra obtienen coseno cero (o "no definido") en el
   sistema de esta sesión?
2. ¿En qué situación usarías una distancia y en cuál usarías una similitud?
3. ¿Qué información se pierde exactamente cuando normalizas un vector?
4. ¿Qué partes del mini buscador de la sección 9 seguirían funcionando igual si sustituyéramos los
   conteos de palabras por *embeddings* densos? ¿Cuáles habría que cambiar?
