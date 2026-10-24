# Guía de estudio — Tema 7, Sesión 1: DropLab Analyst, un LLM local que explica un problema de negocio sin inventar

> Esta guía explica, con lenguaje sencillo y muchos ejemplos, todo lo que hay en `clase_01/`: las
> [diapositivas](./Diapositivas%20Tema%207%20-%20Sesi%C3%B3n%201.pdf) (58 páginas), los scripts de
> [`practica/`](./DropLab_sesion_1/DropLab_sesion_1/practica/), el material del
> [ejercicio 3](./DropLab_sesion_1/DropLab_sesion_1/ejercicio_3/) y los
> [deberes, enlaces y test](./Ejercicios%20propuestos/Deberes_Enlaces_Test/Deberes_Enlaces_Test/).
> No hace falta saber de IA: si entiendes qué es una tabla y una suma, puedes seguirla.

## Índice

1. [La idea de la sesión en una frase](#1-la-idea-de-la-sesión-en-una-frase)
2. [El caso DropLab y el correo de las 09:15](#2-el-caso-droplab-y-el-correo-de-las-0915)
3. [Los seis archivos de datos y sus trampas](#3-los-seis-archivos-de-datos-y-sus-trampas)
4. [Qué es un LLM (repaso mínimo)](#4-qué-es-un-llm-repaso-mínimo)
5. [Nube o local, Hugging Face y Ollama](#5-nube-o-local-hugging-face-y-ollama)
6. [Elegir modelo: nombre, cuantización, variante y contexto](#6-elegir-modelo-nombre-cuantización-variante-y-contexto)
7. [Las cifras primero: el código calcula](#7-las-cifras-primero-el-código-calcula)
8. [El modelo redacta: la escalera de cuatro pruebas](#8-el-modelo-redacta-la-escalera-de-cuatro-pruebas)
9. [Herramientas: función fija frente a SQL libre](#9-herramientas-función-fija-frente-a-sql-libre)
10. [Comparar modelos, coste y las cuatro frases para dirección](#10-comparar-modelos-coste-y-las-cuatro-frases-para-dirección)
11. [Los deberes, explicados](#11-los-deberes-explicados)
12. [Mapa de los scripts y cómo ejecutarlos](#12-mapa-de-los-scripts-y-cómo-ejecutarlos)
13. [Resumen final](#13-resumen-final)
14. [¿Qué sigue en la sesión 2?](#14-qué-sigue-en-la-sesión-2)

---

## 1. La idea de la sesión en una frase

> **El código calcula, el modelo redacta y tú verificas.**

Es la "regla de oro de todo el curso". Un LLM (modelo de lenguaje) escribe muy bien y calcula mal, y
lo peor es que **suena igual de seguro cuando acierta que cuando falla**. Toda la sesión consiste en
construir, paso a paso, una forma de usar un modelo en tu propio ordenador para que **no invente
nada**: los números los saca un programa, el modelo solo los convierte en texto claro, y una persona
comprueba el resultado.

**Ejemplo cotidiano:** un contable (el código) hace las cuentas con calculadora; un redactor (el
LLM) escribe el informe con esas cuentas; el director financiero (tú) lee el informe y comprueba que
cada cifra está bien y *se refiere a lo que dice*. Si dejas que el redactor haga también las cuentas
"de cabeza", tarde o temprano se equivocará sin darse cuenta.

La sesión tiene cinco bloques:

| Bloque | Tema | Pregunta guía |
|---|---|---|
| **I** | El caso DropLab | ¿Qué ha pasado con las ventas de Malasaña? |
| **II** | LLM locales | ¿Puede ayudarnos un modelo sin sacar los datos de la empresa? |
| **III** | Las cifras | ¿Cuánto han caído realmente las ventas y qué ha cambiado? |
| **IV** | El modelo en acción | ¿Cómo hacemos que el modelo redacte sin inventar? |
| **V** | Comparar y cerrar | ¿Qué modelo y qué herramienta elegir, y qué entregamos? |

Todo se hizo en clase en una **NVIDIA Jetson Orin de 64 GB** con **Ollama** y el modelo
**`qwen3:4b-instruct`**. En los deberes lo repites en tu propio equipo.

---

## 2. El caso DropLab y el correo de las 09:15

**DropLab** es una marca ficticia de *streetwear* con:

- **3 tiendas:** Malasaña y Goya (Madrid) y Eixample (Barcelona).
- **7 modelos y 48 productos:** 5 zapatillas (Street One, Pulse Runner, Metro Court, Night Shift y
  Cloud Step, de 95 a 130 €), una sudadera (Core Hoodie, 65 €) y una camiseta (Daily Tee, 32 €). Cada
  modelo existe en 2 colores y varias tallas; **cada combinación modelo-color-talla es un SKU**
  (40 SKU de zapatillas = 5 × 2 × 4 tallas, y 8 de ropa = 2 × 2 × 2 tallas).
- **2 periodos:** cuatro semanas de marzo (**periodo A**, 2–29 marzo) frente a cuatro de abril
  (**periodo B**, 30 marzo–26 abril). Los dos empiezan en lunes y duran 28 días: se compara *lo mismo
  con lo mismo*.

El **lunes 27 de abril, 09:15**, llega un correo de Dirección Comercial
([`encargo_direccion.txt`](./DropLab_sesion_1/DropLab_sesion_1/DropLab/encargo_direccion.txt)) con
tres elementos:

| Elemento | Qué dice | Cómo hay que tratarlo |
|---|---|---|
| **Una cifra** | «Las ventas netas han caído 20.000 €» (se la han *trasladado*). | Es una **hipótesis por comprobar**, no un dato. |
| **Tres sospechosos** | Devoluciones, obras frente al local e incidencias de reposición. | Por ahora son **opiniones**. |
| **Una condición** | Analizarlo en nuestros equipos, **sin enviar datos fuera**. | Obliga a usar un **LLM local**. |

Las tres preguntas del correo y cómo las responderá el curso:

| Pregunta | Cómo se responde | Cuándo |
|---|---|---|
| ¿Cuánto han caído realmente las ventas? | El código calcula el neto; el LLM lo redacta y comprobamos que no invente. | **Hoy** |
| ¿Qué ha cambiado en las compras? | El código cuenta pedidos, líneas y unidades; el LLM pide esos cálculos con herramientas. | **Hoy** |
| ¿Qué explicación respaldan los datos y qué nos falta? | Cruzar las cifras con documentos, tickets e imágenes y listar lo que falta. | Sesiones 2 y 3 |

Y dos condiciones que **marcan el diseño**: *«con cifras y fuentes»* (cada número lo calcula el
código y se puede rastrear hasta su archivo) y *«sin enviar datos fuera de DropLab»* (el modelo corre
en nuestro equipo).

> **Idea clave:** una cifra que te llega por correo, por un compañero o por un modelo es una
> **hipótesis hasta que la compruebas con los datos**.

---

## 3. Los seis archivos de datos y sus trampas

Los datos están en [`DropLab/datos/`](./DropLab_sesion_1/DropLab_sesion_1/DropLab/datos/) y las
reglas de cálculo en
[`diccionario_datos.md`](./DropLab_sesion_1/DropLab_sesion_1/DropLab/documentos/diccionario_datos.md).
**Lo primero en cualquier análisis es saber qué representa una fila** en cada archivo:

| Archivo | 1 fila = | Filas | Clave | Para qué sirve |
|---|---|---|---|---|
| `locales.csv` | una tienda | 3 | `local_id` | Traduce `MAD-MAL` → Malasaña, Madrid. |
| `referencias.csv` | un producto (SKU) | 48 | `sku` | Modelo, color, categoría, talla y `precio_lista`. |
| `calendario.csv` | una tienda en un día | 168 | fecha + `local_id` | Qué días comparamos (56 días × 3 tiendas). Todas abren 10:00–20:00. |
| `ventas.csv` | una **línea** de un pedido | 1.441 | `linea_id` | Lo que se vendió. |
| `reembolsos.csv` | un abono sobre una venta | 62 | `reembolso_id` | Dinero devuelto. |
| `disponibilidad.csv` | un SKU en un tramo horario | 1.352 | local + sku + inicio | Stock observado (¡solo de 8 SKU!). |

Los **códigos** (`local_id`, `sku`, `linea_id`) son el pegamento que conecta los archivos.

### 3.1 `ventas.csv`: línea, pedido y unidades no son lo mismo

Cada fila es una **línea**; un **pedido** puede tener varias. Se cuentan así:

| Quiero contar… | Cómo |
|---|---|
| **Pedidos** (compras) | `pedido_id` **distintos** |
| **Líneas** (renglones) | **filas** |
| **Unidades** | **suma** de la columna `cantidad` |

Ejemplo de la diapositiva: el pedido `A-MAD-MAL-ORD-0006` (8 de marzo, Malasaña) tiene 2 líneas (2×
Core Hoodie lila L = 115,03 € y 2× Street One negro 42 = 168,13 €): **1 compra, 2 líneas, 4
unidades, 283,16 €**. Cuidado: `A-MAD-MAL-0014` es una *línea* y `A-MAD-MAL-ORD-0014` es *otro pedido*;
se parecen pero no tienen nada que ver. Usa siempre el identificador completo y su columna.

El importe de una línea ya lleva el descuento restado:

```
importe_linea = cantidad × precio_unitario − descuento_linea     →   2 × 95,00 − 21,87 = 168,13 €
```

Otros detalles: hay 1.441 filas = 720 en A + 720 en B + **una venta antigua de febrero**
(`HIST-JOIN-001`); `fecha_venta` tiene día pero **no hora**; y `precio_lista` **no es el coste**, así
que no se puede calcular margen ni beneficio.

### 3.2 `reembolsos.csv`: el abono cuenta el día en que se reconoce

- No tiene `local_id`: la tienda se obtiene de la **venta original** con `linea_id`.
- **Un abono se asigna al periodo de `fecha_reconocimiento`, no al de la venta.** `REF-0031` abona el
  1 de abril una venta del 16 de marzo: la venta va en A y el abono en B.
- `unidades = 0` también existe: es un **ajuste comercial** (dinero devuelto sin devolución física).

### 3.3 La trampa del JOIN que duplica

La venta `HIST-JOIN-001` (100 €, febrero) tiene **dos abonos** (10 € y 20 €). Si unes ventas con
reembolsos directamente por `linea_id`, la venta sale **dos veces** (una por abono) y al sumar
`importe_linea` obtienes **200 €** en vez de 100 €.

```
Mal :  ventas ⨝ reembolsos  →  2 filas  →  SUM(importe_linea) = 200 €   ✗
Bien:  1) sumar abonos por línea (10 + 20 = 30)  2) después unir  →  100 − 30 = 70 €   ✓
```

**Regla:** *antes de unir dos tablas, agrega la que tiene varias filas por cada fila de la otra.*
**Analogía:** si en el ticket de un restaurante hay un plato y dos propinas, y pegas ambas listas
fila a fila, el plato aparece dos veces y la cuenta sale inflada.

### 3.4 `disponibilidad.csv`: sin fila no es stock cero

Cada fila es un tramo de horas (`inicio` incluido, `fin` excluido, con desfase horario `+01:00` /
`+02:00`). Solo se observan **8 SKU, todos de Street One** (2 colores × 4 tallas, en las 3 tiendas).
**Un SKU ausente significa que *no lo medimos***, no que haya cero stock. Además no es un libro de
almacén: no cuadra entradas ni ventas.

### 3.5 Lo que NO está en los datos

No hay `cliente_id` (un pedido no es una persona), visitas o tráfico, hora de venta, costes y margen,
campañas aplicadas ni demanda no atendida. **«Un dato ausente no es un cero: si hace falta, se pide;
no se inventa.»**

---

## 4. Qué es un LLM (repaso mínimo)

Un LLM es **un autocompletado gigante**: dado un texto, puntúa cada palabra posible como
continuación y elige una, y repite palabra a palabra hasta terminar.

```
Las ventas de abril han ___   →   bajado 62 %  ·  subido 24 %  ·  sido 9 %  ·  …
```

| Término | Qué es | En clase |
|---|---|---|
| **Token** | Un trozo de texto; una palabra ocupa uno o varios. | — |
| **Parámetros** | Lo que el modelo aprendió al entrenar. | ~4.000 millones (4B). |
| **Contexto** | Todo lo que tiene delante a la vez: instrucciones, datos y su propia respuesta. | La petición usa ≈ 1.600 tokens. |

### Un LLM predice palabras; no calcula

Prueba en directo: `ollama run qwen3:4b-instruct "Responde solo: 17*23"`. Lo preguntaron **cinco
veces** y las cinco contestó **401**, con total seguridad. La respuesta correcta es **391**. Suena
seguro, es falso y no avisa. **Por eso las cifras las calcula el código, nunca el modelo.**

Tampoco conoce DropLab: si le preguntas cuánto cayeron las ventas de Malasaña entre marzo y abril de
2026, no sabe nada de la empresa (y cree que estamos en 2024). Un modelo no puede leer los CSV solo
porque estén en la misma carpeta: necesita **recibir los datos** o **acceso mediante una integración**
(pregunta 4 del test).

---

## 5. Nube o local, Hugging Face y Ollama

### 5.1 Nube frente a local

| | **En la nube** (ChatGPT, Claude, Gemini) | **En local** (Llama, Qwen, Gemma…) |
|---|---|---|
| Modelos | Cerrados: solo por Internet | Abiertos: se descargan y corren en tu equipo |
| ✓ | Los más potentes; nada que instalar | Los datos **no salen del equipo**; sin coste por uso; funciona sin red |
| ✗ | Tus datos viajan a otra empresa; pago por uso y siempre con Internet | Modelos más pequeños; necesitas memoria y, mejor, GPU |

**DropLab elige local** porque son datos de negocio que no deben salir de la empresa.
⚠️ Ojo (pregunta 8 del test): usar Ollama **no garantiza** que sea local. Ollama también permite
modelos "en la nube" (*cloud*); si eliges uno, los datos viajan. Hay que comprobar el **destino de
inferencia** y los servicios conectados; escribir en el prompt «que no salgan los datos» no cambia
nada.

### 5.2 Hugging Face es el almacén; Ollama, el reproductor

```
Hugging Face  →  modelos listos (GGUF)  →  Ollama  →  pregunta/respuesta  →  Tu aplicación
(el «GitHub» de      (>1 millón)           descarga una vez, carga en         le pregunta por HTTP
 los modelos)                              memoria y responde                 a localhost:11434
```

- **Hugging Face** (huggingface.co): ahí se publican los modelos. En la **ficha** del modelo mira:
  quién lo publica (Qwen/Alibaba), cuántas descargas, parámetros y precisión (4B, BF16), **licencia**
  (apache-2.0 permite uso en empresa, también para vender) y etiquetas (Text Generation…). La
  **licencia completa manda sobre la etiqueta** (pregunta 7 del test): revisa siempre las condiciones
  de uso comercial del modelo concreto, no la cifra de descargas ni la etiqueta «local».
- **Ollama**: descarga el modelo y lo sirve en `http://localhost:11434`. Tu código le habla como a
  cualquier API. **Ollama ejecuta y gestiona modelos; el LLM genera respuestas** (pregunta 3 del test).
- Alternativas: **LM Studio** (como Ollama, con ventanas), **llama.cpp** (el motor sobre el que nació
  Ollama) y **vLLM** (servir a muchos usuarios en servidores).

Comandos de la práctica 2: `ollama list`, `ollama pull qwen3:4b-instruct`, `ollama run …`,
`ollama show …` (4.0B parámetros, Q4_K_M, ventana de 262.144 tokens), `ollama ps` (columnas `SIZE` y
`CONTEXT`) y `ollama stop …` (libera memoria).

### 5.3 Los modelos abiertos más conocidos

| Familia | Quién | Tamaños | Nota |
|---|---|---|---|
| **Llama** | Meta (EE. UU.) | 1B, 3B, 8B, 70B | Pionero. Lo usamos como modelo pequeño. |
| **Qwen** | Alibaba (China) | 0,6B, 4B, 8B, 32B | Multilingüe, muy bueno en español. **El nuestro.** |
| **Gemma** | Google (EE. UU.) | 1B, 4B, 12B, 27B | Ligero; los medianos también ven imágenes. |
| **Mistral** | Mistral AI (Francia) | 7B, 24B | El referente europeo. |
| **DeepSeek** | DeepSeek (China) | 1,5B, 8B, 70B | Famoso por razonar paso a paso (R1). |
| **gpt-oss** | OpenAI (EE. UU.) | 20B, 120B | Primer modelo abierto de OpenAI desde GPT-2. |

El panorama cambia cada pocos meses.

---

## 6. Elegir modelo: nombre, cuantización, variante y contexto

### 6.1 Cómo leer el nombre de un modelo

```
qwen3    :4b          -instruct         -q4_K_M
FAMILIA   TAMAÑO       VARIANTE          COMPRESIÓN
Qwen v3   4.000 M      responde directo  pesos en ≈ 4 bits
          parámetros   (otras: thinking, vision…)
```

**Regla rápida:** más parámetros = más capaz, pero también más lento y con más memoria. Se elige **el
más pequeño que haga bien la tarea**.

### 6.2 Cuantizar = comprimir para que quepa

Es como bajar la resolución de una foto: pesa la tercera parte y se sigue reconociendo.

| El mismo `qwen3:4b` guardado en… | Pesa | Cabe en… (orientativo) |
|---|---|---|
| 16 bits (original) | ≈ 8 GB | Portátil de 8 GB: modelos de 1B a 4B |
| 8 bits | ≈ 4,4 GB | Portátil de 16 GB o GPU de 8 GB: hasta ~8B |
| **4 bits (Ollama)** | **2,5 GB** | Jetson Orin 64 GB: 8B con holgura, hasta ~30B |

**Cuenta de la servilleta** (pregunta 5 del test): 4.000 millones de parámetros × 4 bits = 16.000
millones de bits = 2.000 millones de bytes = **2 GB** solo de pesos. Pero ejecutar el modelo necesita
**memoria adicional** (sobre todo el contexto), así que 2 GB no bastan para todo el proceso.

### 6.3 Elegir bien la variante: de >3 minutos a 2 segundos

| `qwen3:4b` (piensa antes de responder) | `qwen3:4b-instruct` (responde directo) |
|---|---|
| > 180 s: genera más de 1.200 tokens de razonamiento oculto | **2 s**: mismo tamaño (2,5 GB), ideal para redactar sobre cifras ya calculadas |

Antes de usar un modelo, comprueba qué hace: en `/api/show`, el campo `thinking`. En los scripts se
envía `"think": False`.

### 6.4 Lo que más memoria gasta no es el modelo: es el contexto

El **contexto** es la "memoria de trabajo" de la conversación y **Ollama la reserva entera al cargar
el modelo, se use o no**. Si no la fijas, la elige según la memoria libre (262.144 tokens con ≥ 48
GB; 32.768 entre 24 y 48 GB).

| | En disco | Por defecto (≥ 48 GB libres) | Por defecto (24–48 GB) | **`num_ctx = 4.096`** |
|---|---|---|---|---|
| Memoria | 2,5 GB | **42 GB** | 7,5 GB | **3,2 GB** |

Nuestra petición usa ≈ 1.600 tokens, así que **fijamos `num_ctx = 4096`** (en los scripts
`NUM_CTX`; en los de herramientas, 8192). Consecuencia (pregunta 6 del test): al aumentar mucho el
contexto, *aunque el modelo y su cuantización no cambien*, **puede aumentar la memoria de ejecución y
el tiempo de procesamiento**; los parámetros del modelo no cambian.

### 6.5 Todo ocurre en el equipo

```
Nuestro código (Python, pandas) → Ollama (localhost:11434) → Modelo (qwen3:4b-instruct)
```

Internet solo se usa **una vez, para descargar el modelo**. En clase desconectaron la red y el modelo
siguió respondiendo.

---

## 7. Las cifras primero: el código calcula

[`03_metricas_basicas.py`](./DropLab_sesion_1/DropLab_sesion_1/practica/03_metricas_basicas.py) calcula
todo "en un segundo y sin errores". (Las cifras de abajo las he verificado ejecutando el script.)

### 7.1 Reglas de negocio que implementa

- Una **venta** se asigna al periodo por `fecha_venta`.
- Un **abono** se asigna por `fecha_reconocimiento` (no por la fecha de la venta).
- Los abonos se **agregan por `linea_id` antes** de cruzarlos con ventas (evita el doble conteo).
- **Ventas netas = ventas antes de reembolsos − reembolsos reconocidos en el periodo.**
- Los importes se suman en **céntimos (enteros)**: con decimales en coma flotante, 1.441 sumas
  acumulan error (RBQL dio `42000.00000000003`, y un modelo llegó a escribir 50.999,99 €).

### 7.2 Resultados

**Total empresa:** neto **96.000 € → 81.000 €** (**−15.000 €, −15,6 %**).

| Tienda | Neto A | Neto B | Variación |
|---|---|---|---|
| **Malasaña** | 40.000 € | 26.000 € | **−14.000 € (−35 %)** |
| Goya | 32.000 € | 30.000 € | −2.000 € (−6 %) |
| Eixample | 24.000 € | 25.000 € | +1.000 € (+4 %) |

**Malasaña explica el 93 % de la caída** (14.000 / 15.000). Esto dice *dónde* cae la venta, todavía no
*por qué*.

### 7.3 ¿Cuadra el −20.000 € del correo?

No cuadra con ninguna métrica: Malasaña bruto −14.000 €, Malasaña neto −14.000 €, DropLab neto total
−15.000 €. **El correo decía 20.000; los datos dicen 14.000.**

### 7.4 Los tres sospechosos

| Sospechoso | Qué dicen los datos | Veredicto |
|---|---|---|
| **Devoluciones** | Abonos en Malasaña: **2.000 € en A y 2.000 € en B**. Explican **0 €** de la caída de 14.000 €. | No es la causa. |
| **Cambio en las compras** | Pedidos: 120 → 120. Unidades: 467 → 304 (−35 %). Unidades/pedido: 3,89 → 2,53. Ticket medio: 350 → 233,33 € (−33 %). El precio de lista medio no cambia. | **Mismas compras, menos artículos en cada una.** No es un efecto de precios. |
| **Reposición / stock** | 8 intervalos sin stock en Malasaña = 48 horas-SKU, pero solo **12 horas de reloj** (el 4 % del horario de B). | Una **pista**, no una causa. |

Detalles que conviene entender bien:

- **La trampa del porcentaje.** Los abonos pasan de **4,76 % a 7,14 %** de las ventas antes de
  reembolsos, pero los euros no cambian (2.000 €). El porcentaje sube porque **baja el denominador**
  (42.000 → 28.000 €). Di siempre *sobre qué* se calcula un porcentaje.
- **Horas-SKU frente a horas de reloj.** Cuatro SKU (Street One negro y arena, tallas 41 y 42) × 6 h
  (10:00–16:00) × 2 días (6 y 16 de abril) = **48 horas-SKU**; pero como coinciden a la vez, el reloj
  solo marca **12 horas**. Son dos formas distintas de medir lo mismo (suma de duraciones por variante
  frente a unión de intervalos).
- **Coincidir en el tiempo no es causar**, y 12 horas en 4 SKU no explican por sí solas un mes de
  caída en todo el catálogo. Además, como `fecha_venta` no tiene hora, **no se pueden cruzar ventas
  con las horas sin stock**.
- **Un pedido no es una persona.** Sin visitas ni clientes no sabemos si entró menos gente.

---

## 8. El modelo redacta: la escalera de cuatro pruebas

[`04_conectar_ollama.py`](./DropLab_sesion_1/DropLab_sesion_1/practica/04_conectar_ollama.py) hace
**la misma pregunta** («¿Cuánto han caído realmente las ventas netas de Malasaña y qué ha cambiado en
las compras?») con el **mismo modelo**, cambiando **una sola cosa cada vez**: qué contexto recibe. El
modelo **nunca ve un CSV**: como mucho recibe un JSON pequeño con cifras ya calculadas.

```
Datos (6 CSV) → Cálculo (pandas) → Hechos (JSON pequeño) → Redacción (el modelo) → Informe
                03_metricas        construir_evidencia()    04_conectar_ollama      hechos y borrador, por separado
```

| Prueba | Orden | Qué recibe el modelo |
|---|---|---|
| 1 | `--modo sin-datos --sin-reglas` | Solo la pregunta y un papel. |
| 2 | `--modo correo --sin-reglas` | + el correo (con sus 20.000 €). |
| 3 | `--modo hechos --sin-reglas` | + los hechos calculados. |
| 4 | *(por defecto)* | + las **reglas** en el system prompt. |

### 8.1 Qué pasó (resultados de clase)

| | 1 · Solo la pregunta | 2 · + el correo | 3 · + los hechos |
|---|---|---|---|
| **Sin reglas** | ✗ Inventa la cifra («15 %») y la causa («clientes nuevos»). | ✗ Repite el correo como si fuera un dato («cayeron 20.000 € según registros de exportación»). | ≈ Cifras bien (14.000 €, 35 %), **causas inventadas** («mayor incidencia de calidad» por el 7,14 %). |
| **Con reglas** | ✓ «No se puede determinar…» (admite que no lo sabe). | ✓ No da por buena la cifra: «no se ofrecen fuentes para verificar el correo». | ✓ Cifras correctas (14.000 €, 467 → 304, 350 → 233,33 €). |

Conclusión: **sin hechos inventa; con hechos pero sin reglas, atribuye causas; con hechos y reglas,
redacta bien.**

### 8.2 El system prompt de la prueba 4 (las "reglas")

Dice, en resumen: usa **exclusivamente** las cifras del bloque «hechos» y no las recalcules; si falta
el dato, **dilo**; una cifra del correo es una **afirmación por comprobar** (compárala y da la
calculada); distingue empresa de tienda; **no afirmes causas** (el stock es una pista); responde en
español en ≤ 6 frases.

### 8.3 Si le falta un dato lo dice; si lo tiene no exagera

Pregunta: «¿Fue por falta de stock disponible?». **Sin el dato de stock** (`--sin-stock`): «no se
puede confirmar… no se proporcionan datos sobre disponibilidad». **Con el dato**: lo sitúa en Street
One, tallas 41 y 42, dos fechas, y añade «no se puede afirmar que la falta de stock sea la causa
directa».

### 8.4 Pero también se equivoca, y no avisa

En la prueba 4 el modelo escribió «la disponibilidad de stock cero afectó a **8 SKU**». El 8 *existe*
en los hechos (son los 8 intervalos y los 8 SKU observados), pero los SKU sin stock son **4**. El
revisor automático (sección `[REVISIÓN]` del script) **no lo detecta**: *el número existe, el
significado no*.

> **Comprobar que una cifra existe no basta: hay que comprobar a qué se refiere.**

### 8.5 El revisor automático y sus límites

`cifras_no_respaldadas()` busca en el borrador los números que **no aparecen** en los hechos (ignora
enteros pequeños y años; admite formatos `40.000` o `3,89`). Es **una ayuda, no un veredicto**: no
detecta cifras reales con significado falso, ni causas inventadas sin números, ni una cifra del
correo citada correctamente.

El script imprime al final los datos de la ejecución para anotarlos: modelo, temperatura (0,2),
`num_ctx`, tiempo total, segundos de carga, tokens de entrada y salida y **tokens por segundo**.

---

## 9. Herramientas: función fija frente a SQL libre

En vez de pasarle los hechos ya hechos, podemos dejar que **el modelo pida los cálculos**. Es el
*tool calling* (llamada a herramientas):

```
Ronda 1: el modelo NO escribe texto: pide una herramienta (tool_call) con argumentos
         ↓ nuestro código VALIDA la llamada, la EJECUTA y le devuelve el resultado (JSON)
Ronda 2: el modelo recibe todo lo anterior + resultado → ahora sí escribe la respuesta
```

Dos puntos clave:

- **El modelo propone; tu código ejecuta** (pregunta 10 del test). El modelo no ejecuta nada por sí
  mismo, y Ollama no modifica tus CSV.
- **El modelo no ve tu código, solo la descripción** de la herramienta (nombre, para qué sirve y
  parámetros). Por eso la `description` es lo más importante.

### 9.1 Función fija — [`07_herramienta_funcion.py`](./DropLab_sesion_1/DropLab_sesion_1/practica/07_herramienta_funcion.py)

`resumen_comercial(local_id, desde, hasta)` es código escrito y probado: calcula ventas, abonos,
neto, pedidos, líneas, unidades y ticket para **una tienda y un rango de fechas** (válida para
cualquier tienda/fechas; no contiene respuestas del caso). El modelo solo elige **cuándo** llamarla y
**con qué argumentos**: pide dos llamadas (una por periodo) y responde «de 40.000 € a 26.000 €; 120
pedidos en ambos».

- ✓ **Fiable:** el cálculo está escrito y probado antes.
- ✗ **Limitada:** solo responde lo que la función cubre.
- Devuelve errores legibles (tienda desconocida, fechas no válidas, `desde` > `hasta`).
- El bucle `conversar_con_herramientas()` limita las **rondas** (en la última obliga a responder en
  texto), detecta si el modelo **escribió la llamada como texto** en vez de usar `tool_calls` y
  captura errores de argumentos.

### 9.2 SQL libre — [`08_herramienta_sql.py`](./DropLab_sesion_1/DropLab_sesion_1/practica/08_herramienta_sql.py)

Aquí el modelo **escribe el SQL** y nuestro código lo ejecuta en **DuckDB** (carga los 6 CSV en una
base en memoria). Responde a preguntas que nadie previó, pero **puede escribir un SQL que se ejecuta
sin error y calcula otra cosa**.

El código aporta: el **esquema generado automáticamente** (tablas, columnas, tipos y valores de
ejemplo; `--solo-esquema`), el **contexto** (periodos, tiendas) y las **reglas de cálculo**
(`--sin-reglas` las quita), y si el SQL falla **el error vuelve al modelo** para que lo corrija.

**Barreras en el código, no en el prompt:**

| Intento | Resultado |
|---|---|
| `DELETE FROM ventas` | ✗ bloqueado: solo `SELECT` |
| `SELECT * FROM read_csv_auto('/etc/passwd')` | ✗ bloqueado: sin acceso a archivos (`enable_external_access = false`) |
| `SELECT 1; SELECT 2` | ✗ bloqueado: una sola sentencia |
| Resultados enormes | recortados a 50 filas |

> Una instrucción en el prompt («no borres nada») es una petición; una barrera en el código es una
> garantía.

### 9.3 Cómo falla el SQL libre (sin dar error)

Pregunta: ventas netas de Malasaña en A y B. Valor real: **40.000 / 26.000 €**.

| Configuración | Resultado | Qué pasó |
|---|---|---|
| 4B **con reglas** | 42.332,73 € (y olvida B) | Toma «marzo» como periodo A: mete el 30 y 31 de marzo, que son de B. |
| 4B **sin reglas** | **1.962.800 €** | JOIN ventas–calendario por tienda: cada venta × 28 días. DuckDB no da error. |
| 8B **con reglas** | 40.030 / 26.212 € | Fechas bien, pero solo cuenta abonos de ventas *del mismo periodo*. «Casi acierta… y falla.» |

Esto conecta con la pregunta 11 del test: un filtro `fecha_venta >= '2026-03-02' AND fecha_venta <
'2026-04-01'` se ejecuta sin error pero **incluye el 30 y 31 de marzo** (que son del periodo B); el
resultado está mal aunque no haya mensaje. Y no es cosa solo de modelos pequeños: el 8B también falla.

---

## 10. Comparar modelos, coste y las cuatro frases para dirección

### 10.1 No acierta el modelo más grande, sino la mejor herramienta

Se midió el % de campos correctos en tres preguntas (Q01 neto, Q02 cesta, Q03 `HIST-JOIN-001`), con 2
repeticiones, para tres modelos y tres formas de acceder a los datos:

| Modelo | Función fija | SQL libre + reglas | SQL libre sin reglas | Coste |
|---|---|---|---|---|
| `llama3.2:1b` | 0 % | 0 % | 0 % | 1,3 GB en disco · 1,7 GB cargado · 9 s/pregunta |
| `qwen3:4b-instruct` | **67 %** | 7 % | 11 % | 2,5 GB · 3,9 GB cargado · 25 s/pregunta |
| `qwen3:8b` | **67 %** | 0 % | 11 % | 5,2 GB · 6,3 GB cargado · 39 s/pregunta |

Lectura: duplicar el tamaño (4B → 8B) **no mejora nada** con función fija (67 % en ambos) y cuesta
más memoria (3,9 → 6,3 GB cargado) y más tiempo (25 → 39 s por pregunta). La función fija acierta lo que cubre y **no inventa lo que no
cubre (Q03)**; el SQL libre queda entre 0 % y 11 % con cualquier modelo. Con solo 3 preguntas y 2
repeticiones, las diferencias entre 0 %, 7 % y 11 % **no son concluyentes**: lo que sí se ve es la
distancia con el 67 %. Los modelos de 1B no sirven: no saben usar herramientas.

**Comparación justa** (pregunta 12 del test): probar un modelo recién cargado y otro ya en memoria,
con preguntas distintas y solo el tiempo total, **no sirve para elegir**. Hacen falta **tareas
comunes, calidad verificable y condiciones comparables**.

### 10.2 El coste, en directo (práctica 6, opcional)

`05_monitor_recursos.py` muestra RAM, GPU y CPU en vivo. Al cargar `qwen3:4b-instruct` la RAM sube
~3 GB y al escribir se dispara la GPU (~8 tokens/s). Con `qwen3:8b`, ~6 GB más y más lento
(~5 tokens/s). Pregunta para reflexionar: ¿escribe mejor el grande? (Ya vimos que no calcula mejor.)

### 10.3 Cuatro frases para dirección

La mejor respuesta no es la más rotunda, sino **la más exacta, trazable y honesta**:

| | Contenido |
|---|---|
| **1 · Hechos** | Malasaña pasa de 40.000 a 26.000 € netos: **−14.000 €, no 20.000**. |
| **2 · Interpretación** | Mantiene 120 pedidos, pero baja de 3,89 a 2,53 unidades por pedido. |
| **3 · Hipótesis** | Los abonos no cambian; 12 horas sin stock son una pista menor. Falta saber **qué cambió el 30 de marzo**. |
| **4 · Límites** | No hay visitas, campañas aplicadas ni demanda no atendida. |

---

## 11. Los deberes, explicados

Documento: [`Deberes_sesion_1.pdf`](./Ejercicios%20propuestos/Deberes_Enlaces_Test/Deberes_Enlaces_Test/Deberes_sesion_1.pdf).
Tres ejercicios, unas **dos horas**. El profesor no da los comandos; si te atascas **más de media
hora** con lo mismo, escríbele. **Entrega:** un único documento (Word o PDF) con lo pedido en cada
ejercicio, más `herramientas.py` y los `resultados_*.json`; **sin la carpeta `.venv`**.

> Esta guía explica *qué se pide y cómo pensarlo*; no resuelve los deberes por ti.

### Ejercicio 1 · Monta tu laboratorio (~45 min + descarga)

| Lo que hay que conseguir | Pistas |
|---|---|
| Conocer tu equipo: RAM, disco libre, GPU | Cada sistema lo muestra distinto; búscalo. |
| Elegir un modelo y justificarlo | En clase `qwen3:4b-instruct` (2,5 GB). Con 8 GB de RAM puede ir justo: prueba uno más pequeño (en el aula funcionó `llama3.2:3b`). **Los de 1B no valen**: no saben usar herramientas. |
| Entorno virtual (Python ≥ 3.10) en `DropLab_sesion_1` con `requirements.txt` | `pandas>=2.2,<3`, `duckdb>=1.1,<2`, `rich>=13.7,<14`, `requests>=2.31,<3`. |
| Ollama instalado y modelo descargado | Empieza pronto: la descarga tarda. |
| Repetir lo de clase | Scripts 01, 02 y 03; las dos preguntas del bloque II (17 × 23 y Malasaña); pruebas 1 y 4 del script 04 (`--help`). |

**Qué debe aparecer en la entrega:** tu equipo y modelo (con una frase de por qué); ventas netas de
DropLab y de Malasaña en A y B según el script 03; qué respondió el modelo a 17 × 23 y la línea de
`ollama ps` **explicada con tus palabras** (sobre todo `SIZE` y `CONTEXT`); tiempo y tokens/s de las
pruebas 1 y 4 comparados con el Jetson (≈ 25 s y 8 tokens/s); **una frase de la prueba 4 que no se
pueda respaldar con los hechos y por qué**; y **qué te ha fallado por el camino y cómo lo arreglaste**
(«esto me interesa mucho»).

### Ejercicio 2 · ¿Lo enviarías a dirección? (~20 min, sin instalar nada)

- **Calentamiento:** busca el pedido `B-BCN-EIX-ORD-0013` en `ventas.csv`: líneas, unidades, importe
  total, periodo y si tiene reembolso. *Pista del enunciado:* piensa **por qué columna** lo buscas en
  `reembolsos.csv` (¿qué clave tiene esa tabla?).
- **Lo importante:** el anexo del PDF trae los **hechos de Malasaña** (la única fuente de verdad) y
  **cuatro borradores reales** (A, B, C y D) escritos por el modelo en el Jetson. Para cada uno decide
  si lo enviarías **tal cual, con cambios o no**, y marca cada frase problemática con su tipo de error:

| Tipo | Nombre | Pregunta para detectarlo |
|---|---|---|
| **1** | Cifra inventada | ¿El número aparece en los hechos? |
| **2** | Cifra real, significado falso | El número existe, pero ¿se refiere a eso? (ejemplo de clase: «8 SKU» cuando eran 4). |
| **3** | Afirmación ajena como dato | ¿Da por buena una cifra u opinión de otra persona (el correo)? |
| **4** | Causa no demostrada | ¿Hay un «porque / se debe a» que los datos no prueban? |
| **5** | Interpretación contradicha | Las cifras están bien, pero ¿la conclusión choca con los hechos? |

- **Para terminar:** coge el borrador que mejor se pueda salvar y corrígelo con **los mínimos cambios
  posibles, como mucho en cuatro frases**. Pista: *una cifra correcta no basta, mira a qué se refiere.*

**Método práctico:** subraya cada número y busca su origen en los hechos; después comprueba *a qué
se refiere* (periodo, tienda, métrica, porcentaje sobre qué); por último busca verbos causales
(«debido a», «se debe», «afectó directamente», «estructural») y compara con la sección «No hay datos
de…» del anexo.

### Ejercicio 3 · Construye una herramienta (~60 min, Python + Ollama)

Archivo: [`ejercicio_3/herramientas.py`](./DropLab_sesion_1/DropLab_sesion_1/ejercicio_3/herramientas.py)
(solo Python 3.9+, **sin librerías**; usa `csv`, `Decimal` y `urllib`). Ya trae una herramienta
hecha (`ventas_netas`) y el bucle que la conecta con el modelo. **Te toca:**

1. **TODO 1 · `cesta(local_id, desde, hasta)`**: pedidos, líneas, unidades, unidades por pedido,
   ticket medio y **pedidos con 4 o más unidades**. Las pistas están en el código: valida como
   `ventas_netas`, filtra por tienda y fechas, `cantidad` es texto (usa `int()`), suma las unidades
   por pedido con un diccionario `{pedido_id: unidades}`, usa `Decimal` y `euros()` para el ticket.
   Borra el `raise NotImplementedError`.
2. **TODO 2 · describirla en `TOOLS`** copiando el bloque de `ventas_netas`. **Lo importante es la
   `description`**: es lo único que lee el modelo. Explica qué devuelve cada métrica y cuándo
   conviene llamarla.

**Comprobar sin modelo:** `python herramientas.py probar` ejecuta 6 pruebas con resultado conocido
(2 de `ventas_netas`, 3 de `cesta` y una con tienda inexistente que debe devolver `error`).
Ejecutar una a mano: `python herramientas.py calcular cesta MAD-MAL 2026-03-02 2026-03-29`.

**Con modelo:** `preguntar "…"` y `bateria` (6 preguntas; la 6 —«¿cuántas personas visitaron la
tienda de Malasaña en abril?»— **no se puede responder**). Se guarda `resultados_<etiqueta>.json`.
Revisa cada pregunta con **tres comprobaciones**: ¿eligió la **herramienta** buena? ¿con la tienda y
las **fechas** correctas (**argumentos**)? ¿lo que **responde** coincide con lo que devolvió tu
código?

**Experimentos (elige uno y compara con la batería normal):**

| Orden | Qué cambia | Qué vigilar |
|---|---|---|
| `bateria --descripciones-pobres` | Descripciones casi vacías y sin `enum` | ¿Usa la herramienta equivocada o responde una pregunta imposible? |
| `bateria --sin-contexto` | No se le dice qué fechas son A y B | ¿Se inventa fechas en las que no hay datos? |
| `bateria --modelo llama3.2:3b` | Otro modelo | ¿Mantiene el nivel? |

Con ellos aparece la idea central: **errores que no dan ningún mensaje de error**. En las trazas de
clase ([`trazas_jetson.md`](./DropLab_sesion_1/DropLab_sesion_1/ejercicio_3/trazas_jetson.md), del
03/10/2026) puedes verlos: con descripciones pobres, la pregunta imposible de las visitas se
"responde" con la herramienta de pedidos y dice que «110 personas realizaron pedidos» (un pedido no es
una persona); sin contexto el modelo consulta **2023 y 2024** y la función devuelve ceros sin
quejarse; y `llama3.2:3b` contesta a la pregunta de las visitas con «23.667 visitantes», que es en
realidad un importe en euros. *(Si tu equipo no puede con el modelo, haz los dos primeros ejercicios
y usa estas trazas para el resto; díselo al profesor en la entrega.)*

**El hallazgo:** calcula los **pedidos de 4 o más unidades** de las tres tiendas en A y en B. ¿Qué
tipo de compra desaparece, y dónde? ¿Qué dato pedirías a la empresa para entender por qué? Escribe
una **recomendación para dirección de 4–5 frases, con cifras y sin inventar causas**. (Es el hilo que
abre la sesión 2: *¿qué cambió el 30 de marzo?*)

**Reto opcional:** con `--sin-contexto`, haz que `cesta()` **devuelva un error que explique qué fechas
existen** cuando se le pidan fechas sin datos. ¿Se corrige solo el modelo?

### Extras: enlaces y test

- [`Enlaces_sesion_1.pdf`](./Ejercicios%20propuestos/Deberes_Enlaces_Test/Deberes_Enlaces_Test/Enlaces_sesion_1.pdf)
  (revisados el 6/10/2026): 13 enlaces ordenados por momento de uso. Instalar Ollama
  (`ollama.com/download`, `docs.ollama.com/quickstart`), Ollama por sistema y GPU, entornos virtuales
  de Python, elegir modelo (`ollama.com/library/qwen3`), fichas y licencias en Hugging Face,
  comandos (`docs.ollama.com/cli`), Rainbow CSV para VS Code, API de Ollama, *tool calling*, FAQ y,
  como extra, longitud de contexto, **salidas estructuradas** («que el formato sea correcto no
  demuestra que el contenido sea verdadero») y documentación de pandas y DuckDB.
- [`Test_sesion_1.pdf`](./Ejercicios%20propuestos/Deberes_Enlaces_Test/Deberes_Enlaces_Test/Test_sesion_1.pdf):
  12 preguntas para hacer **al final y sin apuntes**. Cubren, en este orden: contar pedidos/líneas/
  unidades (1), el JOIN que duplica (2), qué hace Ollama frente al LLM (3), que el modelo no ve los
  CSV (4), memoria de los pesos (5), efecto del contexto (6), licencias (7), nube vs local (8),
  validar JSON frente a validar cifras (9), quién ejecuta la herramienta (10), SQL que corre sin error
  pero mal (11) y cómo comparar modelos de forma justa (12). Las secciones 3 a 10 de esta guía
  contienen lo necesario para razonar cada una.

---

## 12. Mapa de los scripts y cómo ejecutarlos

### 12.1 Mapa

| Script | Qué hace | Necesita Ollama | Conceptos |
|---|---|---|---|
| `01_inspeccionar_datos.py` | Filas, columnas, tipos, nulos y primeras filas de cada CSV. | No | Mirar antes de asumir. |
| `02_auditoria_integridad.py` | Claves únicas, referencias sin huérfanos, calendario completo y demostración del doble conteo (200 € frente a 100 €). | No | Integridad, JOIN que duplica. |
| `03_metricas_basicas.py` | Ventas, abonos, neto por total y tienda; cesta; resumen de stock. En céntimos. | No | El código calcula. |
| `04_conectar_ollama.py` | Escalera de 4 pruebas; imprime lo que recibe el modelo, los hechos, el borrador, la revisión y la ejecución. | **Sí** | El modelo redacta. |
| `05_monitor_recursos.py` / `06_flujo_visual.py` | Se citan en las diapositivas (monitor de RAM/GPU/CPU y flujo visual), **pero no están en el zip** de `clase_01`. | — | Coste; flujo de datos. |
| `07_herramienta_funcion.py` | Tool calling con `resumen_comercial()`; define `conversar_con_herramientas()`. | **Sí** | Función fija. |
| `08_herramienta_sql.py` | SQL libre en DuckDB con barreras; `--solo-esquema`, `--sin-reglas`, `--sql`. | **Sí** (excepto `--solo-esquema` / `--sql`) | SQL libre. |
| `09_comparativa_modelos.py` | Se menciona en un comentario de 08 (la comparativa de 3 modelos), **tampoco está en el zip**. | — | Comparar modelos. |
| `ejercicio_3/herramientas.py` | Ejercicio 3, autónomo y sin librerías. | Solo `bateria` / `preguntar` | Tu propia herramienta. |

Los scripts buscan la carpeta de datos con la variable `DROPLAB_DATOS`, o `data/datos`, o
`DropLab/datos`, en la carpeta del script y hacia arriba. Un truco útil para comprobar en clase el SQL
del modelo: `python practica/08_herramienta_sql.py --sql "SELECT COUNT(*) FROM ventas"` (misma
seguridad, sin modelo).

### 12.2 Preparar el entorno (una sola vez)

Hay **un único `.venv` en la raíz del repo**, compartido por todas las clases. El `requirements.txt` de
la raíz incluye el de esta sesión (`pandas`, `duckdb`, `rich`, `requests`).

```bash
cd ~/ebis/07_llm_open_source
python3 -m venv .venv                 # solo si no existe
source .venv/bin/activate             # en cada terminal nueva (verás "(.venv)" en el prompt)
pip install -r requirements.txt
```

Para los scripts que usan el modelo, además: Ollama abierto (`ollama list` debe responder) y el modelo
descargado (`ollama pull qwen3:4b-instruct`, unos GB). Los scripts sin modelo funcionan sin Ollama.

> Si no quieres activar el entorno, cambia `python` por la ruta completa:
> `~/ebis/07_llm_open_source/.venv/bin/python practica/03_metricas_basicas.py`.

### 12.3 `practica/`, script a script

Todas las órdenes se lanzan **desde la carpeta que contiene `practica/`**:

```bash
cd ~/ebis/07_llm_open_source/clase_01/DropLab_sesion_1/DropLab_sesion_1
```

Cualquier script acepta `-h` para ver sus opciones (`python practica/04_conectar_ollama.py -h`).

**`01_inspeccionar_datos.py`** — sin opciones, sin modelo.

```bash
python practica/01_inspeccionar_datos.py
```

Recorre los 6 CSV y enseña filas, columnas, tipos, nulos y las 3 primeras filas de cada uno.

**`02_auditoria_integridad.py`** — sin opciones, sin modelo.

```bash
python practica/02_auditoria_integridad.py
```

Imprime `[OK]`/`[FALLO]` por cada comprobación y termina con la trampa del JOIN (200 € en vez de 100 €).

**`03_metricas_basicas.py`** — sin opciones (solo `-h`), sin modelo.

```bash
python practica/03_metricas_basicas.py
```

Es la **fuente de verdad** del caso: total de la empresa, neto por tienda, cesta, Malasaña en detalle
(40.000 → 26.000 €) y disponibilidad. Los scripts 04, 07 y 08 lo importan.

**`04_conectar_ollama.py`** — necesita Ollama.

| Opción | Por defecto | Para qué |
|---|---|---|
| `--modo {sin-datos,correo,hechos}` | `hechos` | Qué contexto recibe el modelo (la escalera de la sección 8). |
| `--sin-reglas` | (reglas activadas) | System prompt mínimo, sin reglas de verificación. |
| `--sin-stock` | (con stock) | Quita la disponibilidad de los hechos. |
| `-q`, `--question "…"` | la pregunta de Malasaña | Hacer otra pregunta. |
| `--modelo NOMBRE` | `qwen3:4b-instruct` | Probar otro modelo descargado. |
| `--temperatura N` | `0.2` | Más alto = más variado. |
| `--num-ctx N` | `4096` | Tamaño de la ventana de contexto (más = más memoria). |
| `--seed N` | (ninguna) | Repetir exactamente la misma respuesta. |

```bash
python practica/04_conectar_ollama.py --modo sin-datos --sin-reglas   # prueba 1
python practica/04_conectar_ollama.py --modo correo --sin-reglas      # prueba 2
python practica/04_conectar_ollama.py --modo hechos --sin-reglas      # prueba 3
python practica/04_conectar_ollama.py                                 # prueba 4 (con reglas)
python practica/04_conectar_ollama.py -q "¿Fue por falta de stock?" --sin-stock
python practica/04_conectar_ollama.py --modelo llama3.2:1b --temperatura 0.8 --seed 42
```

**`07_herramienta_funcion.py`** — necesita Ollama salvo con `--solo-explicita`.

| Opción | Por defecto | Para qué |
|---|---|---|
| `--solo-explicita` | (llama al modelo) | Solo el paso 0: llamamos nosotros a `resumen_comercial()`; sin modelo. |
| `-q`, `--question "…"` | Malasaña, A frente a B | Otra pregunta. |
| `--modelo NOMBRE` | `qwen3:4b-instruct` | Otro modelo. |

```bash
python practica/07_herramienta_funcion.py --solo-explicita    # sin modelo: ver la función a mano
python practica/07_herramienta_funcion.py                     # paso 0 + rondas de tool calling
python practica/07_herramienta_funcion.py -q "¿Cómo le fue a Eixample en el periodo B?"
python practica/07_herramienta_funcion.py --modelo llama3.2:1b
```

**`08_herramienta_sql.py`** — necesita Ollama salvo con `--solo-esquema` o `--sql`.

| Opción | Por defecto | Para qué |
|---|---|---|
| `--solo-esquema` | — | Muestra el esquema automático y prueba las 3 barreras (DELETE, leer archivo, dos sentencias). Sin modelo. |
| `--sql "SELECT …"` | — | Ejecutas **tú** una consulta con las mismas barreras. Sin modelo. |
| `--sin-reglas` | (con reglas) | Quita las reglas de cálculo del prompt (deja periodos y tiendas). |
| `-q`, `--question "…"` | neto de Malasaña A y B | Otra pregunta. |
| `--modelo NOMBRE` | `qwen3:4b-instruct` | Otro modelo. |

```bash
python practica/08_herramienta_sql.py --solo-esquema
python practica/08_herramienta_sql.py --sql "SELECT COUNT(*) FROM ventas"
python practica/08_herramienta_sql.py                  # el modelo escribe el SQL
python practica/08_herramienta_sql.py --sin-reglas     # ¿cae en la trampa del JOIN?
python practica/08_herramienta_sql.py --modelo qwen3:8b -q "¿Qué tienda vendió más unidades en B?"
```

Al final imprime, para comparar, lo que calcula `03_metricas_basicas.py`.

> **Datos en otra carpeta:** todos aceptan la variable `DROPLAB_DATOS`, por ejemplo
> `DROPLAB_DATOS=/ruta/a/datos python practica/03_metricas_basicas.py`.

### 12.4 `ejercicio_3/herramientas.py`

Se lanza **desde su propia carpeta** (ahí guarda los `resultados_*.json`). No necesita librerías, pero
con el `.venv` activado funciona igual.

```bash
cd ~/ebis/07_llm_open_source/clase_01/DropLab_sesion_1/DropLab_sesion_1/ejercicio_3
```

Funciona por **órdenes** (la primera palabra tras el nombre del archivo):

| Orden | Modelo | Qué hace |
|---|---|---|
| `probar` | No | 6 pruebas con resultado conocido. Hasta completar `cesta()` verás «2 de 6» y 4 `[PENDIENTE]`. |
| `calcular HERRAMIENTA TIENDA DESDE HASTA` | No | Ejecutas tú una herramienta (`ventas_netas` o `cesta`). |
| `preguntar "…"` | Sí | Una pregunta; muestra qué herramienta pide el modelo y qué devuelve tu código. |
| `bateria` | Sí | Las 6 preguntas del ejercicio; guarda `resultados_<etiqueta>.json`. |

Opciones de `preguntar` y `bateria`:

| Opción | Para qué |
|---|---|
| `--modelo NOMBRE` | Otro modelo (por defecto `qwen3:4b-instruct`); se añade a la etiqueta del JSON. |
| `--sin-contexto` | Experimento 2: no se le dice qué fechas son A y B. |
| `--descripciones-pobres` | Experimento 1: descripciones casi vacías y sin `enum`. |
| `--solo 3,4,5` | (solo `bateria`) Ejecutar únicamente esas preguntas. |

```bash
python herramientas.py probar
python herramientas.py calcular ventas_netas MAD-MAL 2026-03-02 2026-03-29
python herramientas.py calcular cesta MAD-MAL 2026-03-02 2026-03-29   # cuando hayas hecho el TODO 1
python herramientas.py preguntar "¿Cuántos pedidos hizo Goya en el periodo B?"
python herramientas.py bateria
python herramientas.py bateria --solo 4
python herramientas.py bateria --descripciones-pobres
python herramientas.py bateria --sin-contexto
python herramientas.py bateria --modelo llama3.2:3b
```

Orden de trabajo recomendado: `probar` → completar `cesta()` hasta «6 de 6» → `calcular cesta …` →
completar el TODO 2 → `bateria` → un experimento. Sin el TODO 2 el modelo no sabe que `cesta` existe
y las preguntas de pedidos las responderá mal o sin herramienta.

---

## 13. Resumen final

1. **Problema:** una cifra por comprobar (−20.000 €), tres sospechosos y la condición de no sacar los
   datos fuera.
2. **Datos:** seis archivos conectados por códigos; saber qué es una fila en cada uno; cuidado con
   contar mal, con el JOIN que duplica, con el abono que cuenta por fecha de reconocimiento y con lo
   que no está en los datos.
3. **LLM local:** un autocompletado que no calcula; Ollama lo ejecuta en tu equipo; cuantizar reduce
   el peso; **el contexto es lo que más memoria gasta**.
4. **Cifras:** el código calcula (pandas, en céntimos): −15.000 € en total, −14.000 € (−35 %) en
   Malasaña, devoluciones iguales, mismas compras con menos unidades, 12 h sin stock como pista.
5. **Redacción:** sin hechos inventa; con hechos y sin reglas atribuye causas; con hechos y reglas
   redacta bien, pero aun así puede dar una cifra real con significado falso.
6. **Herramientas:** la función fija es fiable y limitada; el SQL libre es flexible y falla sin
   avisar; las barreras van en el código, no en el prompt.
7. **Decisión:** no acierta el modelo más grande, sino la mejor herramienta. La respuesta ideal es
   exacta, trazable y honesta.

### Ideas para recordar siempre

- **El código calcula, el modelo redacta y tú verificas.**
- **Local es control:** los datos no salen del equipo y no hay coste por uso (pero comprueba que el
  modelo *de verdad* es local).
- **Una cifra que te llega es una hipótesis hasta que la compruebas.**
- **Que una cifra exista en los hechos no prueba que se refiera a lo que dice el modelo.**
- **Un error sin mensaje de error es el más peligroso** (SQL con 1.962.800 €, fechas de 2023, 23.667
  «visitantes»).
- **Coincidir en el tiempo no es causar.** Un dato ausente no es un cero.
- **Validar la estructura (JSON, SQL sin error) no es validar el contenido.**

---

## 14. ¿Qué sigue en la sesión 2?

La sesión termina con una pregunta abierta: **«¿Qué cambió el 30 de marzo?»**. Con los CSV hemos
respondido *cuánto* y *dónde*, pero no *por qué*. En la sesión 2 **llegan los documentos internos**
(más tickets e imágenes en la 3), y con ellos las preguntas de siempre: cómo darle al modelo la
información correcta sin pegar todo en el prompt (la ventana de contexto es limitada y cara) y cómo
exigir **fuentes**. Es el mismo problema que ya conoces del Tema 5 (recuperación + generación con
evidencia), ahora con un LLM abierto y local como motor.

### Preguntas para repasar antes de la próxima sesión

1. ¿Por qué el modelo respondió 401 a «17*23» cinco veces seguidas y qué implica para el diseño de
   DropLab Analyst?
2. En Malasaña, los abonos suben del 4,76 % al 7,14 % pero valen 2.000 € en ambos periodos. ¿Qué
   explicación das y qué has de decir siempre al citar un porcentaje?
3. ¿Cuál es la diferencia entre 48 horas-SKU y 12 horas de reloj? ¿Por qué ninguna de las dos prueba
   que el stock causara la caída?
4. La prueba 3 sin reglas acertó las cifras pero inventó causas. ¿Qué regla del *system prompt* lo
   evita y por qué no es una garantía absoluta?
5. ¿Qué diferencia hay entre «el SQL se ejecutó sin error» y «el SQL es correcto»? Pon un ejemplo del
   caso.
6. ¿Por qué se pone la barrera «solo SELECT» en el código y no en el prompt?
7. Un modelo de 4B con 4 bits ocupa unos 2 GB de pesos. ¿Por qué `ollama ps` puede mostrar 3,9 GB, o
   42 GB si no fijas `num_ctx`?
8. ¿Qué dato pedirías a la empresa para entender por qué desaparecen los pedidos de 4 o más unidades?
