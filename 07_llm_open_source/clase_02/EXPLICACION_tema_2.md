# Guía de estudio — Tema 7, Sesión 2: DropLab Analyst con datos, voz y documentos

> Esta guía explica, con lenguaje sencillo y ejemplos del caso, todo lo que hay en `clase_02/`: las
> [diapositivas](./Diapositivas%20Tema%207%20-%20Sesi%C3%B3n%202.pdf) (68 páginas), los scripts de
> [`practica/sesion_2/`](./DropLab_sesion_2/practica/sesion_2/), los documentos y la llamada de
> [`data/`](./DropLab_sesion_2/data/), el [enunciado de los ejercicios](./Enunciado%20-%20Ejercicios%20propuestos.pdf),
> los [enlaces](./Enlaces_sesion_2.pdf) y el [test](./Test%20-%20sesi%C3%B3n%202.pdf).
> Sigue a la [guía de la sesión 1](../clase_01/EXPLICACION_tema_1.md): conviene tenerla leída.

## Índice

1. [La idea de la sesión en una frase](#1-la-idea-de-la-sesión-en-una-frase)
2. [Dónde lo dejamos y qué cambia hoy](#2-dónde-lo-dejamos-y-qué-cambia-hoy)
3. [Bloque I · La capa semántica: el negocio, escrito una vez en código](#3-bloque-i--la-capa-semántica-el-negocio-escrito-una-vez-en-código)
4. [Bloque I · El verificador de cifras](#4-bloque-i--el-verificador-de-cifras)
5. [Bloque I · Para elegir, mide: el examen](#5-bloque-i--para-elegir-mide-el-examen)
6. [Bloque I · La nota, el coste y el modelo «de expertos»](#6-bloque-i--la-nota-el-coste-y-el-modelo-de-expertos)
7. [Bloque II · Qué es un audio y qué ve Whisper](#7-bloque-ii--qué-es-un-audio-y-qué-ve-whisper)
8. [Bloque II · Transcribir la llamada y dónde se equivoca](#8-bloque-ii--transcribir-la-llamada-y-dónde-se-equivoca)
9. [Bloque III · Diez fuentes, una historia y cuatro trampas](#9-bloque-iii--diez-fuentes-una-historia-y-cuatro-trampas)
10. [Bloque III · Preparar las fuentes: trocear y poner ficha](#10-bloque-iii--preparar-las-fuentes-trocear-y-poner-ficha)
11. [Bloque III · Buscar bien: embeddings, palabras e híbrida](#11-bloque-iii--buscar-bien-embeddings-palabras-e-híbrida)
12. [Bloque III · Responder con fuentes y verificar](#12-bloque-iii--responder-con-fuentes-y-verificar)
13. [Todo junto: el analista](#13-todo-junto-el-analista)
14. [Los ejercicios, explicados](#14-los-ejercicios-explicados)
15. [Enlaces y test](#15-enlaces-y-test)
16. [Mapa de los scripts y cómo ejecutarlos](#16-mapa-de-los-scripts-y-cómo-ejecutarlos)
17. [Resumen final](#17-resumen-final)
18. [¿Qué sigue?](#18-qué-sigue)

---

## 1. La idea de la sesión en una frase

> **Los datos dicen *cuánto* y *qué*; la voz y los documentos ayudan con el *porqué*. Y todo, con fuentes.**

La regla de oro de la sesión 1 sigue en pie (*el código calcula, el modelo redacta, tú verificas*). Hoy se
le añaden tres cosas:

| Bloque | Tema | Pregunta guía |
|---|---|---|
| **I** | Datos con garantías | El SQL libre respondía a todo y fallaba sin avisar: ¿cómo lo hacemos bien? |
| **II** | La voz | ¿Qué se dijo en una llamada y cuánto nos podemos fiar del texto? |
| **III** | Preguntar a los documentos | ¿Qué dicen los documentos y la llamada, y **dónde** lo dicen? |

Al final se juntan las tres piezas en un **analista** que responde con cifras de los datos y hechos de los
documentos, cada uno con su cita.

Todo se hizo en clase en la **NVIDIA Jetson** (64 GB) con Ollama. El modelo principal ya no es el 4B de la
sesión 1, sino **`qwen3:30b-a3b-instruct`** (unos 18 GB cargado). En un portátil normal no cabe: en los
ejercicios se usa el 4B y se mide la diferencia.

---

## 2. Dónde lo dejamos y qué cambia hoy

En la sesión 1 vimos tres formas de dar los datos al modelo (diapositiva 3):

| Script (sesión 1) | Quién calcula | Qué se puede preguntar | Resultado |
|---|---|---|---|
| `04_conectar_ollama.py` (el modelo redacta) | Nuestro código, antes de preguntar | Solo lo calculado antes | ✓ Fiable ✗ Limitado |
| `07_herramienta_funcion.py` (función fija) | Nuestro código (la función) | Lo que cabe en la función | ✓ Fiable ✗ Limitado |
| `08_herramienta_sql.py` (SQL libre) | El modelo, escribiendo SQL | Cualquier cosa | ✓ Libre ✗ **Falla sin dar error** |

El objetivo de hoy es tener **las dos cosas a la vez: libertad para preguntar y fiabilidad en la respuesta**.

Y al final de la sesión 1 quedó una pregunta abierta: **«¿qué cambió el 30 de marzo?»**. Los datos dicen que
Malasaña mantiene sus 120 pedidos, pero cada pedido lleva menos unidades. Hoy aparecen la llamada y los
documentos que lo explican (spoiler: terminó una campaña de regalo, el **Pack 4**).

---

## 3. Bloque I · La capa semántica: el negocio, escrito una vez en código

### 3.1 Por qué fallaba el SQL libre

Con las tablas crudas, incluso un modelo de 30B se equivoca. La diapositiva 5 resume cinco fallos reales, todos
**sin ningún mensaje de error**:

| # | Trampa | Qué hizo el modelo | Dio | Real |
|---|---|---|---|---|
| 1 | ¿Dónde acaba el periodo A? | Tomó todo marzo (incluye el 30 y 31, que son de B) | 42.332,73 € | 40.000 |
| 2 | Unir tablas multiplica filas | Unió ventas con calendario: cada venta, 28 veces | 1.962.800 € | 40.000 |
| 3 | Un abono cuenta en su fecha | Restó los abonos por la fecha de la venta | 39.817,63 € | 40.000 |
| 4 | Contar el pedido entero | Miró cada línea (`cantidad ≥ 4`), no el pedido | 0 pedidos | 108 |
| 5 | Un pedido no es un cliente | Contó pedidos como personas | 120 clientes | no existe |

> «Nada de esto se ve mirando las columnas. Con reglas en el prompt, el modelo puede leerlas… **e ignorarlas**.»

### 3.2 Seis palancas, probadas una a una

Antes de elegir, se probaron seis ideas con un examen de 13 preguntas (diapositiva 6, modelo de 30B):

| Palanca | Qué cambia | Resultado |
|---|---|---|
| Un modelo más grande | Del 4B al 30B, mismo prompt | 8 → 8 ✗ no mejora |
| El diccionario de la empresa | El documento oficial, en el prompt | 8 → 9 ≈ poco |
| Ejemplos resueltos | Tres preguntas con su SQL | 12 frente a 13 ≈ no ayuda |
| Razonar antes de responder | `gpt-oss:20b`, tablas crudas | 12, pero 78 s por pregunta |
| **Capa semántica** | **Vistas con el negocio dentro** | **8 → 13 ✓ la palanca grande** |
| Verificador en el código | Revisa las cifras de la respuesta | Caza cifras inventadas ✓ |

### 3.3 Qué es la capa semántica

Una **vista** es una tabla virtual: una consulta guardada con nombre. La idea es esconder los CSV y
enseñarle al modelo **vistas que ya traen dentro las reglas del negocio**. El modelo ya no tiene que *saber*
el negocio: solo tiene que **traducir la pregunta**.

**Analogía:** en vez de darle a un becario las facturas sueltas y un manual de 20 páginas sobre cómo sumarlas,
le das un Excel con una columna «ventas netas» ya calculada y revisada. Solo tiene que filtrar y sumar.

En [`02_capa_semantica.py`](./DropLab_sesion_2/practica/sesion_2/02_capa_semantica.py) los 6 CSV se cargan en
un esquema aparte llamado `crudo`, y en el esquema principal se crean estas vistas:

| Vista | Una fila = | Para qué |
|---|---|---|
| `resumen_diario` | una tienda en un día | Pedidos, unidades, ventas, abonos y **ventas netas** ya calculadas |
| `pedidos` | una compra | La cesta: líneas, unidades e importe de cada pedido |
| `ventas_lineas` | una línea | Cada línea con su periodo, tienda y producto ya pegados |
| `abonos` | un reembolso | Periodo por **fecha del abono**; tienda heredada de la venta |
| `movimientos` | una venta o un abono | Ventas (+) y abonos (−) juntos, por producto |
| `disponibilidad` | un intervalo de stock | Stock con producto y horas (solo 8 SKU) |
| `tiendas`, `catalogo` | tienda / SKU | Nombres y catálogo |

Así se escribe una regla **una sola vez**. Por ejemplo, la trampa 3 (el abono cuenta en su fecha) queda
resuelta dentro de la vista `abonos`:

```sql
-- De 02_capa_semantica.py (vista abonos, recortada)
CREATE VIEW abonos AS
SELECT a.reembolso_id, a.linea_id, a.fecha_reconocimiento,
       CASE WHEN a.fecha_reconocimiento BETWEEN DATE '2026-03-02' AND DATE '2026-03-29' THEN 'A'
            WHEN a.fecha_reconocimiento BETWEEN DATE '2026-03-30' AND DATE '2026-04-26' THEN 'B' END AS periodo,
       v.local_id, v.tienda, ...
FROM crudo.reembolsos a JOIN ventas_lineas v USING (linea_id);
```

Y `resumen_diario` **agrega antes de unir** (sumar ventas por día, sumar abonos por día, y solo entonces
juntarlos), así que la trampa del JOIN que duplica no puede aparecer.

### 3.4 Lo mismo que falló en la sesión 1, ahora en una consulta

La diapositiva 8 lo compara:

```sql
-- Sesión 1 · tablas crudas + reglas: dos consultas, 42.332,73 € y sin periodo B ✗
SELECT SUM(v.importe_linea) FROM ventas v
WHERE v.fecha_venta >= '2026-03-02' AND v.fecha_venta < '2026-04-01'   -- todo marzo
  AND v.local_id = 'MAD-MAL'

-- Hoy · capa semántica: una consulta, 40.000 € y 26.000 € ✓
SELECT periodo, SUM(ventas_netas)
FROM resumen_diario
WHERE tienda = 'Malasaña'
GROUP BY periodo
```

«Sin JOIN y sin fechas que equivocar: lo difícil se escribió una vez, en las vistas, y se comprobó contra el 03.»

### 3.5 Los comentarios: avisos de negocio que el modelo sí lee

Cada vista y cada columna lleva un **comentario** (`COMMENT ON VIEW` / `COMMENT ON COLUMN` de DuckDB). El
esquema que recibe el modelo **se genera automáticamente** (nadie lo escribe a mano) e incluye esos
comentarios. Algunos ejemplos:

```python
# De 02_capa_semantica.py (diccionario COMENTARIOS, recortado)
"pedidos": ("Una fila por pedido (compra completa). ... Un pedido NO es un cliente.", {...
    "importe_antes_reembolsos": "EUR del pedido; NO descuenta abonos"}),
"disponibilidad": ("Stock observado por intervalos. SOLO 8 SKU de Street One; un producto sin filas no se "
                   "observa (no es stock cero).", {...}),
```

Además el prompt lleva una **GUÍA** (qué vista usar para cada tipo de pregunta, cómo hacer porcentajes dentro
del SQL) y una lista de **datos que no existen**:

```text
Datos que NO existen (si los piden, dilo y explica qué dato sí hay):
clientes (no hay cliente_id: un pedido no es una persona), visitas o tráfico, hora de la venta, costes y margen,
campaña aplicada a cada pedido, regalos entregados, demanda no atendida.
```

Ojo con un detalle que el propio script aclara: los CSV crudos **siguen ahí** (en `crudo`) y la barrera SQL
no los bloquea; simplemente no se incluyen en el esquema que se le enseña al modelo. Esconder no es prohibir.

### 3.6 Se comprueba antes de usarla

Una capa semántica con un error sería peor que nada (todos los resultados saldrían mal *con seguridad*). Por
eso `02_capa_semantica.py --comprobar` compara las vistas con las cifras del script 03 de la sesión 1. Lo he
ejecutado y las 7 comprobaciones salen en verde:

| Comprobación | Resultado |
|---|---|
| Neto de Malasaña, A y B | 40.000 / 26.000 € |
| Neto de la empresa, A y B | 96.000 / 81.000 € (desde `resumen_diario` y desde `movimientos`) |
| Cesta de Malasaña | 120 / 120 pedidos · 467 / 304 unidades |
| Pedidos de 4+ unidades en Malasaña | **108 → 7** |
| Abonos de `HIST-JOIN-001` en A | 2 abonos, 30 € |
| Stock sin unidades en Malasaña | 8 intervalos, 4 SKU, 48 horas-SKU |

### 3.7 Dónde vive el conocimiento del negocio

| Forma | Dónde está el negocio | Qué se puede preguntar | Fiabilidad |
|---|---|---|---|
| 04 · El modelo redacta | En el código (el 03) | Solo lo previsto | Máxima |
| 07 · Función fija | En el código (la función) | Lo que cabe en la función | Alta |
| 08 · SQL libre | **En el prompt (reglas)** | Cualquier cosa | Baja (~60 %) |
| **Capa semántica** | **En el código (las vistas)** | **Cualquier cosa** | **Alta (~90 %)** |

> **El negocio vuelve al código… sin quitarle al modelo la libertad de preguntar.**

---

## 4. Bloque I · El verificador de cifras

La segunda pieza está en [`01_preguntar_datos.py`](./DropLab_sesion_2/practica/sesion_2/01_preguntar_datos.py).
Es el SQL libre de la sesión 1 con las mismas barreras (solo `SELECT`, una sentencia, sin archivos, 50 filas)
más un **revisor automático**: cuando el modelo escribe su respuesta, el código busca cada número y comprueba
que aparece en algún resultado de SQL (o en la pregunta, o en las fechas de los periodos).

```python
# De 01_preguntar_datos.py
def cifras_sin_respaldo(respuesta: str, fuentes: list[str]) -> list[float]:
    """Cifras de la respuesta que no aparecen en ningún resultado de SQL (ni en la pregunta ni en los periodos)."""
    permitidos = [n for t in fuentes for n in numeros(t)]
    return sorted({n for n in numeros(respuesta) if not any(abs(n - p) <= 0.011 for p in permitidos)})
```

Si encuentra cifras sin respaldo, **le devuelve la respuesta al modelo una vez** («estas cifras no aparecen en
tus consultas; si son un cálculo, hazlo dentro del SQL»). Si en el segundo intento siguen, no lo esconde:
muestra un **AVISO**. La función `numeros()` entiende los dos formatos (40.000,00 y 40,000.00).

### Lo que caza y lo que no (diapositiva 17)

| ✓ Lo caza | ✗ No lo caza |
|---|---|
| «El ticket medio de Goya fue **25.858 €**». Ese número no sale de ningún SQL (era 258,33 €). El código se lo devuelve al modelo para que lo corrija. | «¿Cuántas líneas tuvo Goya en B?» → «**307 líneas**». Ese SQL hizo `SUM(cantidad)`: son **unidades**. Las líneas son 240. El número *sí* sale del SQL, así que el verificador lo da por bueno. |

Es el mismo problema que el «8 SKU» de la sesión 1: **comprobar que una cifra existe no basta; hay que
comprobar a qué se refiere**. Por eso el script enseña siempre el SQL: **se lee el SQL**.

### Las tres piezas, juntas (diapositiva 9)

1. **Capa semántica:** el negocio, escrito una vez en código.
2. **Un modelo capaz:** `qwen3:30b-a3b`, que entiende la pregunta y, por ser «de expertos», va rápido.
3. **Un verificador:** el código revisa que cada cifra salga de un resultado de SQL.

Y lo de siempre: el modelo **escribe** el SQL, nuestro código lo **ejecuta** con barreras… y el SQL **se enseña**.

---

## 5. Bloque I · Para elegir, mide: el examen

«Parece que va bien» no sirve para elegir un modelo ni una forma de darle los datos. Hace falta un **examen**
(diapositiva 12):

```
1 Preguntas          → 2 Respuesta correcta     → 3 El modelo responde     → 4 El código pone nota
  variadas, escritas    calculada a mano con       con su herramienta,        ¿están todas las cifras?
  por nosotros (y       SQL revisado y             como en el trabajo         ¿dice que no a lo
  alguna imposible)     contrastada con el 03      de verdad                  imposible?
```

- **Lo caro es el paso 2.** Sin respuestas correctas no hay nota; sin nota, se elige por impresión.
- **Temperatura 0 y repeticiones.** Un modelo fiable acierta *siempre*, no a veces.

### 5.1 Cómo es una pregunta del examen

Están en [`examen/`](./DropLab_sesion_2/practica/sesion_2/examen/), en JSON. Cada una dice qué pone a prueba y
qué cifras debe contener la respuesta. Las imposibles llevan `debe_negar`:

```json
{"id": "P11", "tipo": "agregar por pedido y luego contar",
 "pregunta": "¿Cuántos pedidos de Malasaña tuvieron 4 o más unidades en el periodo A y cuántos en el periodo B?",
 "esperado": {"pedidos4_A": 108, "pedidos4_B": 7}}

{"id": "P13", "tipo": "imposible (dato que no existe)",
 "pregunta": "¿Cuántos clientes distintos compraron en Malasaña en el periodo B?", "debe_negar": true}
```

[`04_examen.py`](./DropLab_sesion_2/practica/sesion_2/04_examen.py) corrige así: acierta si la respuesta
contiene **todas** las cifras esperadas (±0,01); en las imposibles, si contiene una negación («no hay», «no
existe», «no es posible»…). Es una corrección automática y algo generosa: no comprueba que cada cifra esté en
su sitio.

La diapositiva 13 muestra cómo se calculó a mano la respuesta de P01: ventas por fecha de venta (42.000 €),
abonos por fecha de reconocimiento con la tienda de la venta (2.000 €) → **40.000 €**, que coincide con el 03.

### 5.2 Tres exámenes, para no hacernos trampas

| Examen | Preguntas | Para qué |
|---|---|---|
| `bateria.json` | 13 (P01–P13) | **Diseñar**: con ella se probó cada idea y se mejoró la capa |
| `validacion.json` | 10 (V01–V10) | **Comprobar**: preguntas nuevas; ¿la mejora vale para otras preguntas? |
| `prueba_final.json` | 10 (T01–T10) | **Decidir**: escritas antes de la versión definitiva, el examen limpio |

**Analogía:** es como estudiar con los ejercicios del libro y examinarse con otros nuevos. Si solo miras la
batería, te engañas: la capa se diseñó mirándola y puede estar «ajustada» a esas 13 preguntas.

Cada examen incluye una pregunta imposible: P13 (clientes), V09 (margen) y T08 (visitas). Y el modo
`--rapido` usa solo 5 preguntas de la batería: P01 (neto), P06 (un día), P08 (producto), P11 (cesta) y P13
(imposible).

---

## 6. Bloque I · La nota, el coste y el modelo «de expertos»

### 6.1 De 58 % a 91 % (diapositiva 16)

Aciertos en las 33 preguntas (batería + validación + prueba final):

| Configuración | Aciertos | Tiempo por pregunta |
|---|---|---|
| 30B · tablas crudas (el 08) | 58 % | ~15 s |
| 4B · tablas crudas (el 08) | 61 % | ~18 s |
| 4B · capa semántica + verificador | 67 % | ~12 s |
| **30B · capa semántica + verificador** | **91 %** | **~15 s** |
| `gpt-oss:20b` razonando · capa semántica | 97 % | ~30 s |

> La palanca grande es **cómo le damos los datos**. Se elige el **30B con la capa**: 91 % a unos 15 s.

### 6.2 Hacen falta las dos cosas (diapositiva 18)

|  | Tablas crudas + reglas | Capa semántica |
|---|---|---|
| **4B** | 61 % | 67 % — *se pierde: une vistas sin necesidad y suma unidades cuando se piden pedidos* |
| **30B de expertos** | 58 % | **91 %** — *entiende la pregunta y va tan rápido como el 4B* |

> «La capa le quita al modelo **el negocio**; el modelo tiene que poner **la comprensión**.»

Fíjate: con tablas crudas el 30B **no** es mejor que el 4B (58 % frente a 61 %). Un modelo grande no arregla
unos datos mal presentados. Y la capa sola tampoco basta si el modelo no entiende bien la pregunta.

### 6.3 Lo que cuestan (diapositiva 19)

| Modelo | Memoria cargado | Velocidad al escribir |
|---|---|---|
| `qwen3:4b-instruct` | 3,2 GB | 7,3 tokens/s |
| `qwen3:30b-a3b-instruct-2507-q4_K_M` | **18,0 GB** | **8,5 tokens/s** |

En disco: 2,5 GB el 4B y 18 GB el 30B (en la sesión 1, el 8B: 5,6 GB y ~5 tokens/s). **El de 30B ocupa casi
seis veces más… y escribe más rápido que el 4B.** ¿Cómo puede ser?

### 6.4 El modelo «de expertos» (MoE, diapositiva 20)

| Modelo denso (`qwen3:4b`, `qwen3:8b`) | Modelo de expertos (`qwen3:30b-a3b`) |
|---|---|
| **Todo trabaja en cada palabra.** 4B: 4.000 millones de parámetros, todos activos. | **En cada palabra trabajan unos pocos expertos.** 30.000 millones en memoria; unos 3.000 millones activos (8 de 128 expertos). |

Cómo leer el nombre: **`30b`** = parámetros en total · **`a3b`** = activos por palabra («*active 3B*»).

> **La memoria la marca el total; la velocidad, los activos.** Cabe en el Jetson y va rápido; en un portátil
> de 16 GB no cabe.

**Analogía:** un hospital con 128 especialistas en plantilla (hay que pagar a todos: memoria), pero a cada
paciente lo atienden solo 8 (por eso va rápido).

### 6.5 Qué elegimos, y para qué (diapositivas 21 y 22)

| Forma | Acierto | Qué se puede preguntar | Coste | Para qué |
|---|---|---|---|---|
| 07 · Función fija | 67 % (y no inventa) | Lo que cabe en la función | 4B · 3,9 GB | **Las preguntas de siempre** |
| 08 · SQL libre, tablas crudas | ~60 % | Cualquier cosa | 4B o 30B | Nada sin revisar |
| **Capa semántica + 30B + verificador** | **91 %** | **Cualquier cosa** | 18 GB · ~15 s | **Explorar los datos** |

> Preguntas frecuentes, **función fija**. Explorar, **capa semántica + verificador**. Y siempre, **leer el SQL**.

Las cuatro frases para dirección se actualizan con lo nuevo:

| | Contenido |
|---|---|
| **1 · Hechos** | Malasaña pasa de 40.000 a 26.000 € netos: −14.000 €, no 20.000. |
| **2 · Interpretación** | Mantiene 120 pedidos, pero baja de 3,89 a 2,53 unidades por pedido. |
| **3 · Hipótesis** | Los pedidos de 4 o más unidades caen de **108 a 7**. Algo cambió el 30 de marzo. |
| **4 · Límites** | No hay visitas, campañas aplicadas ni demanda no atendida. |

Un dato que ayuda a verlo (lo saca `03_metricas_basicas.py --reparto`): en Malasaña los pedidos de 2 unidades
pasan de **1 a 63**, los de 3 de **11 a 50** y los de 4 de **108 a 7**. Las compras grandes se convierten en
compras pequeñas.

**Tres ideas del bloque I:** el negocio, en el código · para elegir, mide · más grande no es la solución.

---

## 7. Bloque II · Qué es un audio y qué ve Whisper

### 7.1 La llamada

El 7 de abril, **Álex** (Operaciones, central) llama a **Dani** (tienda de Malasaña). Archivo:
[`data/audio/`](./DropLab_sesion_2/data/audio/).

| Dato | Valor |
|---|---|
| Duración | 113 s de conversación |
| Canales | 2: uno por persona (izquierdo = Álex, derecho = Dani) |
| Turnos | 13 en este montaje |
| Muestreo | 16.000 números por segundo y canal |

Queremos saber **qué se dijo, quién lo dijo y cuándo**, y contrastarlo con los datos. Hay dos archivos:
`llamada_0704_dos_canales.wav` (estéreo, un canal por persona) y `llamada_0704_escucha_mono.wav` (la mezcla,
para escucharla).

### 7.2 Un audio es una lista de números

[`06_ver_audio.py`](./DropLab_sesion_2/practica/sesion_2/06_ver_audio.py) lo enseña sin ningún modelo (solo
numpy y matplotlib). Lo he ejecutado:

| | Valor |
|---|---|
| Números por segundo y canal | 16.000 (16 kHz: suficiente para la voz) |
| Cada número | 16 bits: de −32.768 a 32.767 |
| Números en toda la llamada | 1.813.437 por canal × 2 = **3,6 millones** |
| Peso en disco, sin comprimir | **7,3 MB** |

Cada número dice cuánto se mueve la membrana del micrófono en ese instante. Con la vista `zoom` se ve: 2 s de
palabras → 0,1 s de vibración de la voz → 5 ms = **80 números**, uno detrás de otro.

### 7.3 El espectrograma: qué frecuencias suenan

La voz mezcla muchas frecuencias a la vez. El **espectrograma** es una imagen: **eje horizontal** = tiempo,
**eje vertical** = frecuencia (grave abajo, agudo arriba) y **color** = energía en cada banda. Cada voz deja
su «huella».

### 7.4 Lo que entra en Whisper: la imagen log-mel

Whisper no recibe el sonido, recibe **números que describen el sonido**:

| | Valor | Por qué |
|---|---|---|
| Trozo | **30 s** | Whisper procesa el audio en ventanas de 30 segundos |
| Filas | **128 bandas mel** | Más detalle en graves, como el oído humano |
| Columnas | **3.000** | Una cada 10 ms: 100 por segundo |

Los mismos parámetros están al principio del script:

```python
# De 06_ver_audio.py
SR = 16_000          # muestras por segundo
N_FFT = 400          # ventana de 25 ms
HOP = 160            # un paso cada 10 ms → 100 columnas por segundo
N_MELS = 128         # bandas de frecuencia (large-v3 y turbo; los modelos antiguos usan 80)
TROZO = 30           # Whisper procesa el audio en trozos de 30 segundos
```

### 7.5 Quién habla cuándo, sin IA

Como cada persona está en su canal, basta medir la **energía** de cada canal en ventanas de 20 ms: si pasa de
**−40 dB**, hay voz. Uniendo pausas cortas salen los **13 turnos** (vista `turnos`).

> **Whisper no sabe quién habla.** Lo sabemos porque el canal ya está asignado; no es un sistema general de
> «diarización» (separar voces de una grabación mezclada). Por eso, **grabar bien vale más que un modelo más grande**.

### 7.6 Whisper por dentro (diapositiva 31)

```
Audio 30 s → Matriz log-mel 128 × 3.000 → Codificador → Decodificador → Texto
                                           (procesa       (escribe token     (con tiempos y
                                            rasgos)        a token)           probabilidad)
```

El decodificador escribe tokens como un LLM, empezando por unos tokens de control:

```text
<|startoftranscript|> <|es|> <|transcribe|> <|0.00|> Hola, Malasaña. Soy Álex, de Operaciones. <|9.40|> …
```

Esos tokens le dicen el idioma, si transcribir o traducir al inglés, los tiempos y «aquí no hay voz».
**Escribe como un LLM… así que también puede inventar.**

### 7.7 Cómo se entrenó (diapositiva 32)

| Año | Versión | Qué cambió |
|---|---|---|
| 2022 | Whisper | 680.000 h de audio con su transcripción, de internet. 96 idiomas además del inglés |
| 2022 | large-v2 | Los mismos datos, más entrenamiento |
| 2023 | large-v3 | 1 M de horas + 4 M etiquetadas automáticamente por large-v2. 128 bandas mel |
| 2024 | turbo | large-v3 con el decodificador recortado de 32 a 4 capas: casi igual y mucho más rápido |

- **Supervisión débil:** transcripciones de internet que nadie revisó una a una. La fuerza está en la escala.
- **Abierto (licencia MIT):** pesos y código descargables; corre en local y los datos no salen del equipo.

---

## 8. Bloque II · Transcribir la llamada y dónde se equivoca

### 8.1 Elegir modelo y motor

| Modelo | Parámetros | Descarga | En el Jetson (GPU) | Lo que vimos |
|---|---|---|---|---|
| tiny · base | 39 M · 74 M | 75 · 140 MB | — | Para pruebas rápidas |
| small | 244 M | 0,5 GB | 36 s | «PAK4», «Danny» |
| medium | 769 M | 1,5 GB | — | — |
| **turbo** | **809 M** | **1,6 GB** | **32 s (mezcla) · 45 s (canales)** | **Equilibrio de velocidad y calidad** |
| large-v3 | 1.550 M | 2,9 GB | 95 s (canales) | Más grande; también puede inventar y fallar |

> Se elige **el más pequeño que haga bien la tarea**, igual que con los LLM.

Tres motores para la misma llamada (diapositiva 34; la llamada dura 113 s):

| Motor | Tiempo | Nota |
|---|---|---|
| faster-whisper · small · CPU | **207 s** (más lento que la llamada) | `pip` y listo; en el Jetson solo CPU. Bueno para portátiles |
| openai-whisper · small · GPU | 36 s | |
| **openai-whisper · turbo · GPU** | **32 s** | PyTorch + `pip`. Da probabilidad por palabra. **El que usamos** |
| openai-whisper · large-v3 · GPU (canales) | 95 s | |
| whisper.cpp · turbo · GPU | 22 s | El «primo» de llama.cpp; el más rápido, pero hay que compilarlo (25 min) |

**La GPU lo cambia todo.** Y un detalle importante: **Ollama no ejecuta Whisper**; para la voz hace falta otro
motor. Otros modelos de la familia: **distil-whisper** (un alumno pequeño que imita al grande: destilación),
**Parakeet / Canary** (NVIDIA, voz a texto) y **Piper / Kokoro** (el camino de vuelta: texto a voz).

### 8.2 Cómo transcribe el script

[`07_transcribir.py`](./DropLab_sesion_2/practica/sesion_2/07_transcribir.py) transcribe **cada canal por
separado** y une los trozos por su hora de inicio. Así se sabe quién dice cada cosa sin ningún modelo extra.
Las opciones importantes:

```python
# De 07_transcribir.py (recortado)
DUDOSA = 0.70            # por debajo de esta probabilidad, la palabra se marca
PISTA = ("Llamada de DropLab entre Álex, de Operaciones, y Dani, de la tienda de Malasaña. "
         "Pack 4, tote bag, Street One.")

opciones = dict(language="es", word_timestamps=True, condition_on_previous_text=False, ...,
                initial_prompt=PISTA if pista else None)
if solo_voz:   # Whisper solo decodifica los tramos con voz que detecta la energía (con 0,2 s de margen)
    opciones["clip_timestamps"] = clip
```

Guarda un JSON por prueba en [`transcripciones/`](./DropLab_sesion_2/practica/sesion_2/transcripciones/). Ya
vienen cinco hechas en el Jetson: `turbo_mono`, `turbo_canales`, `turbo_canales_solo-voz`,
`turbo_canales_pista` y `large-v3_canales_solo-voz`. La que se usa en el RAG es **`turbo_canales_solo-voz`**.

### 8.3 Una frase ambigua: «ya nos» o «ya no se» (diapositiva 37)

| Mezcla mono · turbo | Canal central · turbo |
|---|---|
| «Desde el 30 ya **nos** entregaba la tote bag» | «Desde el 30 ya **no se** entregaba la tote bag» |
| p(«nos») = 0,626 · dudosa | p(«no») = 0,655 · dudosa |

Las dos salidas son dudosas y significan cosas opuestas. En ese momento habla Álex y Dani está en silencio, así
que la mezcla no «tapa» nada. Conclusión prudente: **la diferencia no prueba que separar los canales causara
el cambio**. Con un solo ejemplo no se puede sacar una regla.

### 8.4 La probabilidad por palabra: una alerta, no un veredicto (diapositiva 38)

Whisper da una probabilidad a cada palabra. Las de menos de 0,70 se marcan para revisar:

| Palabra | p | Qué era |
|---|---|---|
| se iba | 0,48 · 0,65 | «siguió» |
| nos | 0,63 | «no se» |
| tote | 0,58 | correcta, pero dudosa |
| pack | 0,07 | escrita por la pista, no oída |

> **No es infalible:** también hay errores con probabilidad alta. Se verifica igual. La probabilidad sirve para
> decidir **qué tramos escuchar primero**.

### 8.5 Whisper escribe incluso cuando apenas hay voz (diapositiva 39)

Con large-v3, en el canal de Dani, segundo 10,4: **«¿Qué pasa?»**. Ahí solo hay una respiración. El
decodificador, que escribe como un LLM, completa con algo que «suena» a llamada: es una **alucinación**. Con
`--solo-voz` (Whisper solo escucha los tramos con energía) **desaparece**.

Un clásico en español: «*Subtítulos realizados por la comunidad de Amara.org*». Sale de los subtítulos con los
que se entrenó y aparece en audios en silencio o con música.

### 8.6 Más grande no siempre acierta más (diapositiva 40)

| En nuestras pruebas | small · canales | turbo · solo voz | large-v3 · solo voz |
|---|---|---|---|
| «Pack 4» | PAK4 | **Pack 4** | PAC-4 |
| La tienda … abierta | se abierta | **siguió abierta** | seguía abierta |
| Frase espuria en silencio | — | — | — (con solo voz) |

Es una comparación **cualitativa**: modelo y preparación producen hipótesis distintas. No se puede calcular el
**WER** (tasa de error por palabra) sin una transcripción humana de referencia.

### 8.7 Cómo reducir errores sin reentrenar (diapositiva 41)

| # | Técnica | Qué hace | En este caso |
|---|---|---|---|
| 1 | Un canal por persona | Conserva hablante/pista; ayuda ante solapamiento | Este ejemplo no prueba causalidad |
| 2 | Solo voz (umbral de energía) | Recorta actividad baja; puede cortar voz débil | «¿Qué pasa?» desaparece |
| 3 | Pista de contexto | Sugiere vocabulario; no cambia audio ni pesos | «PAK4» → «pack 4»; revisar |
| 4 | Elegir modelo | Calidad frente a tiempo | turbo: el equilibrio |
| 5 | **Contrastar con datos** | Detecta errores semánticos | Caja / calendario / stock |

«La pista orienta el vocabulario, no corrige la señal»: en `turbo_canales_pista` la palabra «Pack» sale con
p = 0,185, señal de que la escribió la pista y no el oído.

### 8.8 Y si no basta: adaptar Whisper (diapositiva 42)

Si la empresa tuviera, por ejemplo, 1.000 llamadas reales:

1. **Preparar:** audio + texto **revisado por humanos**; acordar formato de importes, nombres y dudas.
2. **Separar:** entrenamiento / validación / test **por llamada o hablante** (nunca trozos de la misma llamada
   en los dos lados); el test, intacto.
3. **Ajustar:** desde Whisper, con **LoRA** (congela la base y aprende pequeños adaptadores: menos memoria, no
   menos necesidad de validar).
4. **Evaluar:** WER + errores críticos en llamadas humanas no vistas; comparar base y adaptado.

```
WER = (sustituciones + borrados + inserciones) / palabras
```

### 8.9 Del audio al dato: la transcripción es una fuente más (diapositiva 43)

| Lo que dice la llamada | Dónde se comprueba | |
|---|---|---|
| Día 6: sin Street One negro y arena, 41 y 42, de 10 a 16 h | `disponibilidad.csv`: 4 SKU, 10:00–16:00 | ✓ coincide |
| El calendario aprobado terminaba el 29; el borrador decía 31 | Documentos: calendario y propuesta | → bloque III |
| «Avería del vehículo» | Informe de logística (PDF) | → bloque III |
| Regalo por 4 o más unidades en el mismo pedido | `ventas.csv`: 108 → 7 pedidos de 4+ | ✓ coincide |
| «No tengo un número de visitas» | No existe en ningún dato | límite |

> **La transcripción es una fuente más:** se cita con quién y cuándo… y se contrasta.

**Tres ideas del bloque II:** Whisper procesa rasgos del audio y escribe como un LLM (y puede inventar) ·
preparar la entrada puede ayudar más que aumentar el modelo · el texto es una fuente: se cita y se contrasta.

---

## 9. Bloque III · Diez fuentes, una historia y cuatro trampas

### 9.1 El modelo no ha leído nuestros documentos (diapositiva 46)

| Pegarlo todo en el prompt | Buscar y luego responder (**RAG**) |
|---|---|
| Nuestro corpus: ~6.000 palabras (~9.000 tokens): cabría | Solo los 5 fragmentos relevantes: ~2.000 tokens |
| Con mil documentos, no cabe: **el contexto es memoria** (sesión 1) | Escala a miles de documentos |
| El modelo se pierde entre lo que no importa | Cada fragmento llega con su ficha: documento, página, fecha y estado |
| Difícil saber de dónde sale cada frase | Cada afirmación, con su cita comprobable |

> **RAG** = *Retrieval-Augmented Generation*: buscar primero, responder después… **citando**.

Es la misma idea del Tema 5, ahora **todo en local**: embeddings y modelo en Ollama, índice en un archivo DuckDB.

### 9.2 Las diez fuentes (diapositiva 47)

Están en [`data/documentos/`](./DropLab_sesion_2/data/documentos/) (6 Markdown y 3 PDF) más la llamada:

| Grupo | Fuente | Estado | Qué dice |
|---|---|---|---|
| **Decidido** | Calendario aprobado (`calendario_comercial_aprobado.md`) | aprobado | Pack 4: del 02/03 al **29/03** |
| | Propuesta Pack 4 (`propuesta_pack4_borrador.md`) | **sustituido** | Proponía hasta el 31/03. Ya no manda |
| **Ocurrido** | Diario de tienda (`diario_operaciones_abril.md`) | registro | Cartel fuera el 30/03; roturas 6 y 16/04 |
| | Informe de logística (`informe_logistica_abril.pdf`) | emitido | Avería el 6/04; reposición a las 16:00 |
| | La llamada del 07/04 (Whisper turbo, solo voz) | automática | «Terminaba el 29», el día 6, sin visitas |
| **Previsto** | Aviso de obras (`aviso_obras.md`) | recibido | Obras programadas del 01/04 al 20/04 |
| **Reglas** | Diccionario de datos (`diccionario_datos.md`) | vigente | Cada columna, y qué datos no existen |
| | Política de reembolsos (`politica_reembolsos.md`) | vigente | Un abono cuenta el día que se reconoce |
| | Manual de datos (`manual_datos_y_criterios.pdf`) | vigente | Métricas y reglas; pág. 7: la ficha |

Y el **expediente comercial y de operaciones** (PDF de 8 páginas): el encargo, **copias** de 6 documentos y lo
pendiente (pág. 1 encargo · 2 calendario · 3 diario · 4 logística · 5 stock · 6 obras · 7 borrador · 8 pendientes).

> **Programado no es ocurrido.** El aviso dice cuándo estaba previsto; nada confirma que las obras empezaran ese día.

### 9.3 La historia en fechas (diapositiva 48)

| Fecha | Qué pasa | Tipo |
|---|---|---|
| 27/02 | Borrador del Pack 4: «hasta el 31/03» | escrito (luego sustituido) |
| 01/03 | Calendario aprobado: Pack 4 del 02/03 al 29/03 | decidido |
| 25/03 | Llega el aviso de obras | recibido |
| **30/03** | **Se retira el cartel del Pack 4** (empieza el periodo B) | ocurrido |
| 01/04 → 20/04 | Obras programadas | **previsto** (no consta que empezaran ni que acabaran) |
| 06/04 y 16/04 | Sin Street One 41–42 de 10 a 16 h | ocurrido |
| 07/04 | La llamada (habla del día 6) | ocurrido |
| 27/04 | Expediente e informes | escrito |

«Cuándo se **escribe**, qué se **planifica** y qué **pasa**: tres fechas que no son intercambiables.»

### 9.4 Cuatro trampas escondidas en las fuentes (diapositiva 49)

| # | Trampa | Ejemplo | Defensa |
|---|---|---|---|
| 1 | **Dos versiones casi iguales** | Borrador «hasta el 31/03» · aprobado «hasta el 29/03». Para la búsqueda son casi el mismo texto | La ficha dice cuál está sustituido |
| 2 | **Fechas con significados distintos** | 25/03 recibido · 01/04 programado · 20/04 previsto. Ninguna dice que las obras empezaran | Conservar el significado de cada fecha |
| 3 | **Lo mismo, en dos sitios** | El expediente copia 6 documentos (Markdown y PDF) | Un hecho repetido **no son dos pruebas**: citar la fuente, no sumar copias |
| 4 | **Una fuente escrita por una máquina** | La llamada: «nos» / «no se» en salidas distintas | Estado «transcripción automática»; escuchar y contrastar |

> Y lo que **no está** (visitas, regalos entregados, margen): la respuesta correcta es «**no consta**».

---

## 10. Bloque III · Preparar las fuentes: trocear y poner ficha

El RAG tiene cuatro pasos, todo en el equipo (diapositiva 50):

| Paso | Script | Qué hace |
|---|---|---|
| 1 · Trocear y etiquetar | `10_corpus.py` | 10 fuentes → **51 fragmentos** con su ficha |
| 2 · Índice vectorial | `11_indice.py` | Cada fragmento → **1.024 números** (bge-m3), guardados en DuckDB |
| 3 · Buscar | `12_buscar.py` | La pregunta → los 5 fragmentos más relevantes |
| 4 · Responder y verificar | `13_preguntar_documentos.py` | Solo con esos fragmentos, citando `[F#]` |

Las fuentes son una **lista explícita** (la carpeta `data/documentos/` y la llamada) y **nunca la carpeta del
profesor** (`docente/`, con las respuestas, no se recorre).

### 10.1 Cada fuente se corta por su estructura natural (diapositiva 54)

| Formato | Archivos → fragmentos | Un fragmento = |
|---|---|---|
| Markdown | 6 → 21 | **una sección** (`## …`); la cabecera va a la ficha |
| PDF | 3 → 17 | **una página** (se quitan logotipo, pie y n.º de página; se unen las frases que el PDF cortó) |
| Llamada | 13 turnos → 13 | **dos turnos seguidos, con solape**: cada respuesta llega con su pregunta |

He ejecutado [`10_corpus.py`](./DropLab_sesion_2/practica/sesion_2/10_corpus.py) y salen exactamente esos 51
fragmentos. Si una sección o página pasa de **320 palabras** (`MAX_PALABRAS`), se empaqueta por líneas, sin
partir una línea a la mitad. «Usamos los delimitadores que reconocemos en estas fuentes; revisamos los cortes,
**no es una regla universal**.»

### 10.2 La ficha de cada fragmento (diapositivas 53 y 55)

El propio manual (pág. 7) lo exige: «*Todo fragmento utilizado en un informe debe conservar el documento de
origen, sección o página, fecha, responsable y estado documental.*» Así queda la ficha del borrador
(`10_corpus.py --ver 36`):

```json
"cita":            "propuesta_pack4_borrador.md · Propuesta"
"titulo":          "Propuesta de campaña Pack 4"
"codigo":          "CAM-2026-03-DRAFT"
"fecha":           "27/02/2026"
"responsable":     "equipo comercial"
"estado_documento": "borrador"
"estado":          "sustituido"
"sustituido_por":  "CAM-2026-03-FINAL"
"texto": "Tienda: MAD-MAL. Inicio propuesto: 02/03/2026. Último día propuesto: 31/03/2026. …"
```

Algunos datos los **pone el documento** (título, código, fecha, responsable salen de su cabecera) y otros los
**deduce el código** (`sustituido_por`, y por tanto el estado «sustituido»). `--ver N` enseña de dónde sale
cada campo y marca en amarillo lo deducido.

### 10.3 La cabecera de contexto

El texto que se convierte en vector no es solo el fragmento: lleva delante una línea con su ficha. Así el
fragmento **se entiende aunque llegue solo** (una sección llamada «Pack 4: ejecución», sin más, no diría de qué
documento ni de qué versión viene):

```python
# De 10_corpus.py, función construir()
f["texto_indexado"] = (f"{f['titulo']} ({f['codigo']}, {f['estado']}, {f['fecha']})"
                       + (f" · {f['seccion']}" if f["seccion"] else "") + f"\n{f['texto']}")
```

Ejemplo del fragmento #3: `Calendario comercial aprobado (CAM-2026-03-FINAL, aprobado, 01/03/2026) · Pack 4: ejecución`
y debajo el texto. Es la misma idea que la «recuperación contextual» de Anthropic (enlace 13), solo que allí la
frase la escribe un LLM y aquí la construye el código con la ficha.

### 10.4 «Sustituido»: una regla literal en Python

El calendario aprobado dice literalmente «*Este calendario sustituye a CAM-2026-03-DRAFT*». El código busca esa
frase con una expresión regular y marca como **sustituido** todo fragmento con ese código (también las copias del
borrador dentro del expediente):

```python
# De 10_corpus.py, función construir()
for m in re.finditer(r"sustituye a ([A-Z0-9-]+)", f["texto"], re.IGNORECASE):
    sustituciones[m[1]] = {"por": f["codigo"], "evidencia": f["cita"], "mencion": m[0]}
```

Es una inferencia **por regla, para este caso**, no una validación general de versiones. Y lo importante:
**el embedding no la decide**. La decide el código.

---

## 11. Bloque III · Buscar bien: embeddings, palabras e híbrida

### 11.1 Embeddings: el significado convertido en números (diapositiva 56)

Un modelo de **embeddings** lee un texto y devuelve una lista de números (un **vector**) que resume su
significado. Textos que dicen cosas parecidas dan vectores cercanos, aunque no compartan palabras. Se usa
**bge-m3** (multilingüe, textos de hasta 8.192 tokens, 1.024 números por texto) a través de Ollama.

La cercanía se mide con la **similitud coseno** (1 = mismo significado):

| Par | Similitud (bge-m3) |
|---|---|
| «avería del vehículo» ↔ «el camión se estropeó» | **0,67** — sin una palabra en común, y cerca |
| «tote bag» ↔ «bolsa de regalo» | **0,67** |
| «tote bag» ↔ «HIST-JOIN-001» | 0,39 (textos sin relación rondan 0,3–0,4, no 0) |

**El problema:** el borrador y el aprobado dicen casi lo mismo, así que **quedan juntos** en el mapa de
vectores. La similitud no los distingue.

[`11_indice.py`](./DropLab_sesion_2/practica/sesion_2/11_indice.py) guarda los 51 vectores en una tabla de
DuckDB, **con la ficha en columnas al lado del vector**. Para unas decenas o miles de fragmentos no hace falta
una base de datos vectorial especial: DuckDB compara la pregunta con todos los vectores en milisegundos con la
función `list_cosine_similarity`. Un detalle: cada modelo de embeddings espera un «prefijo» propio para
preguntas y documentos (por ejemplo `search_query:` en nomic); están en el diccionario `PREFIJOS` del script.

### 11.2 Tres formas de buscar (diapositiva 57)

| | **Semántica** | **Palabras (BM25)** | **Híbrida** |
|---|---|---|---|
| Cómo | Por significado (embeddings) | Por palabras clave, como un buscador clásico | Las dos, unidas por su posición (RRF) |
| ✓ | Entiende «vigencia» ≈ «último día» | Clava «HIST-JOIN-001», «DL-0604-MAL» | Lo mejor de las dos |
| ✗ | Puede perder códigos raros | No entiende sinónimos | Un poco más lenta |

«Con *¿hasta cuándo duró el Pack 4?* falla la de palabras; con *HIST-JOIN-001*, la semántica duda.»

**BM25** puntúa un fragmento por las palabras de la pregunta que contiene, dando más peso a las palabras raras
(aparecen en pocos fragmentos) y sin premiar que un fragmento sea muy largo. Antes quita palabras vacías («de»,
«el», «qué»…) y tildes.

**RRF** (*Reciprocal Rank Fusion*) junta las dos listas usando **la posición**, no la puntuación (las dos
puntuaciones están en escalas distintas y no se pueden sumar):

```python
# De 12_buscar.py
def hibrida(self, pregunta: str, k: int = K, rrf: int = 60) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion: suma 1/(60 + posición) de cada lista. No mezcla puntuaciones distintas."""
    puntos = Counter()
    for lista in (self.semantica(pregunta, 20), self.palabras(pregunta, 20)):
        for pos, (i, _) in enumerate(lista):
            puntos[i] += 1 / (rrf + pos + 1)
    return puntos.most_common(k)
```

Un fragmento que sale bien en las dos listas suma dos veces y sube.

### 11.3 La trampa de las versiones: lo más parecido es el borrador (diapositiva 58)

Búsqueda híbrida de «¿Hasta qué día estuvo vigente el Pack 4?»:

| # | Fragmento | Estado |
|---|---|---|
| 1 | expediente · pág. 7 · Propuesta inicial | **sustituido** · 31/03 |
| 2 | borrador.md · Pendientes | **sustituido** |
| 3 | expediente · pág. 2 · Calendario aprobado | aprobado · 29/03 |
| 4 | borrador.md · Propuesta | **sustituido** · 31/03 |
| 5 | calendario aprobado.md · Pack 4: ejecución | aprobado |
| + | calendario aprobado.md · Campañas | **añadido: el vigente** |

Tres defensas:

1. **Estado en la ficha:** «sustituido por CAM-2026-03-FINAL».
2. **El código añade el vigente:** si sale un sustituido, trae el documento que lo sustituye (si no estaba ya).
3. **Una regla para el modelo:** manda el aprobado; el borrador, solo como antecedente.

> **La similitud no sabe qué documento manda. Los metadatos, sí.**

### 11.4 Medido: ¿encuentra la fuente correcta? (diapositiva 60)

[`14_evaluar_rag.py`](./DropLab_sesion_2/practica/sesion_2/14_evaluar_rag.py) usa
[`examen_rag.json`](./DropLab_sesion_2/practica/sesion_2/examen/examen_rag.json): 16 preguntas (R01–R16), cada
una con las **fuentes esperadas** (por ejemplo `expediente_comercial_y_operaciones.pdf#2`, archivo y página) y
los **hechos** que debe contener la respuesta. La parte de recuperación **no usa el LLM** (es rápida): mira si
la fuente esperada está entre los *k* primeros.

¿Está la fuente esperada entre los 3 primeros? (16 preguntas)

| Modelo de embeddings | Semántica | Palabras | Híbrida |
|---|---|---|---|
| **bge-m3** | **16/16** | 14/16 | **16/16** |
| qwen3-embedding:0.6b | 16/16 | 14/16 | 16/16 |
| embeddinggemma | 13/16 | 14/16 | 15/16 |
| nomic-embed-text | 13/16 | 14/16 | 15/16 |

- **Solo palabras: 14/16.** Falla «vigencia del Pack 4» y la pregunta sobre la llamada.
- **nomic: 13/16.** Pensado para inglés: peor en español.
- **La híbrida rescata a los modelos flojos.** Se elige **bge-m3 híbrida**.

El script también calcula el **MRR** (*Mean Reciprocal Rank*): la media de 1/posición de la primera fuente
correcta (1 si sale la primera, 0,5 si sale la segunda, 0,33 si la tercera…; 0 si no sale). Premia que la buena
salga **arriba**, no solo que salga.

### 11.5 Las mismas piezas, en la nube (diapositiva 51)

| Pieza | En el Jetson (hoy) | En Azure (lo equivalente) |
|---|---|---|
| Archivos | `data/documentos/` | Blob Storage o Data Lake |
| Trocear y etiquetar | `10_corpus.py` (pymupdf + reglas) | Function o skillset (+ Document Intelligence si hay escaneados) |
| Embeddings | bge-m3 en Ollama | Azure OpenAI `text-embedding-3` |
| Índice | DuckDB (un archivo: ficha + vector) | Azure AI Search (campos filtrables + vector) |
| Buscar | `12_buscar.py` híbrida (RRF) | AI Search, consulta híbrida + filtros |
| Responder | qwen3 30B en Ollama | Azure OpenAI GPT, con las citas |

**La ficha va con el vector** (en AI Search: filtrar `estado = vigente`). MongoDB, Cosmos DB o PostgreSQL
(pgvector) también guardan vectores: lo importante es **vector + ficha + filtros**. Y «nada sale de DropLab»
(manual, pág. 8): en la nube, suscripción propia, red privada, región UE. Es **cumplimiento, no solo técnica**.

---

## 12. Bloque III · Responder con fuentes y verificar

### 12.1 Cómo responde (13_preguntar_documentos.py)

[`13_preguntar_documentos.py`](./DropLab_sesion_2/practica/sesion_2/13_preguntar_documentos.py) busca (híbrida,
k = 5), numera los fragmentos `[F1]…[F5]` con su documento, página o sección, fecha y **estado**, y le pide al
modelo que responda **solo** con ellos. Las reglas del *system prompt*, resumidas:

```text
- Cada afirmación lleva detrás la cita del fragmento del que sale, por ejemplo [F2]. Sin cita, no se afirma.
- Si los fragmentos no contienen la respuesta, di «No consta en los documentos» y qué información faltaría.
- Si dos fragmentos se contradicen, manda el de estado aprobado o vigente. Un borrador o documento SUSTITUIDO
  solo se menciona como antecedente, diciendo que fue sustituido.
- Respeta el significado de cada fecha: recepción de un aviso, inicio programado, fin previsto y fecha
  efectiva son cosas distintas. Lo previsto no prueba que ocurriera.
- La llamada es una transcripción automática: puede tener errores. Úsala como testimonio, no como dato oficial.
- No calcules cifras nuevas ni afirmes causas que los fragmentos no digan.
```

Una respuesta real (diapositiva 61):

> «El Pack 4 estuvo vigente desde el 02/03/2026 hasta el 29/03/2026, ambos incluidos **[F3]**. A partir del
> 30/03/2026 se retiró el regalo **[F3]**. Esta vigencia fue aprobada y comunicada el 01/03/2026 **[F3]**. La
> propuesta inicial que indicaba hasta el 31/03/2026 fue sustituida **[F1]**.»

La **lista de fuentes la construye el código** a partir de las citas, no el modelo: [F3] = calendario aprobado
(expediente, pág. 2, aprobado, 01/03/2026) y [F1] = propuesta inicial (expediente, pág. 7, sustituido, 27/02/2026).

### 12.2 El código revisa al modelo (diapositiva 62)

| Comprobación | Ejemplo de aviso |
|---|---|
| **Las citas existen** | Si cita [F9] y solo hay 6 fragmentos, avisa |
| **Cada frase lleva cita** | «Sin cita, no se afirma» (salvo «no consta») |
| **Cada cifra está en su fuente** | Si dice «30/03/2026» y [F1] no lo contiene, avisa |
| **Un borrador no es lo vigente** | Si cita un sustituido sin decir que es borrador, avisa |

Es el mismo verificador del bloque I, ahora para **fuentes**: una cifra sin respaldo, **avisa**.

### 12.3 Lo que la verificación no ve: la cita es real, el significado no (diapositiva 63)

| Pregunta | Lo que respondió | Por qué está mal |
|---|---|---|
| «¿Cuándo **empezaron** las obras?» | «…el inicio efectivo fue el 1 de abril [F2]» | La fuente dice «inicio **programado**» y que no hay confirmación de la ejecución. La pregunta lo daba por hecho |
| «¿Quién llamó a la tienda y para qué?» | «…se realizó el mismo día que el aviso de obras fue recibido [F1][F5]» | El aviso se recibió el 25/03 y la llamada es del 07/04. Inventa una relación entre fuentes, **con cita** |

> Como el «8 SKU» y las «307 líneas»: **comprobar que una cita existe no basta; hay que leerla.**

### 12.4 Medido: la nota de las respuestas (diapositiva 64)

`14_evaluar_rag.py --parte respuesta` pregunta de verdad las 16 preguntas y puntúa tres cosas:

| Modelo | Hechos correctos | Cita la fuente esperada | Verificación limpia | Por pregunta |
|---|---|---|---|---|
| **qwen3:30b-a3b-instruct** | **16/16** | **16/16** | **16/16** | 24 s |
| qwen3:4b-instruct | 16/16 | 15/16 | 10/16 | 35 s |

- **La imposible, bien:** «¿Cuántas tote bags se entregaron?» → «No consta en los documentos. Faltaría el
  registro de regalos…».
- **Pero la nota no lo ve todo:** el examen mira hechos y fuentes; los errores de significado de la 12.3 pasaron.

> Bien buscado y bien citado, el modelo acierta. **Y aun así, una persona lee las fuentes.**

---

## 13. Todo junto: el analista

[`15_analista.py`](./DropLab_sesion_2/practica/sesion_2/15_analista.py) junta toda la sesión. El modelo tiene
**dos herramientas** y decide cuál usar:

| Herramienta | Qué hace | Cita |
|---|---|---|
| `consultar_datos(consulta)` | SQL sobre la capa semántica (bloque I): cifras exactas | `[S1]`, `[S2]`… |
| `buscar_documentos(pregunta)` | El RAG (bloque III, incluida la llamada del bloque II): fragmentos con fuente, fecha y estado | `[D1]`, `[D2]`… |

El código numera consultas y fragmentos, construye la lista de fuentes y verifica que cada número de la
respuesta aparece en alguna consulta o fragmento.

### 13.1 Sin consultar, se lo inventa todo… y el código lo para (diapositiva 65)

La primera vez que se probó, el modelo respondió **sin usar ninguna herramienta**: «…las ventas netas bajaron
un 23 % [S1]… los abonos aumentaron un 45 % [S3]. El 28 de marzo se registró un error en el sistema de precios
que afectó a 12 productos… [D1]». Ni el error de precios ni esas cifras existen, y cita [S1] y [D1] sin haber
hecho ninguna consulta. El código detectó **0 fuentes** consultadas y **6 cifras sin respaldo** (12, 15, 23, 28,
31, 45). Desde entonces el script **no acepta una respuesta sin consultar antes las dos herramientas**:

```python
# De 15_analista.py (recortado)
if not llamadas and (not consultas or not fragmentos) and ronda < 6:
    # Respondió sin consultar: el código no lo acepta y se lo devuelve (sin herramientas, inventa).
    falta = "consultar_datos" if not consultas else "buscar_documentos"
    messages.append({"role": "user", "content": f"No respondas todavía: usa antes la herramienta {falta}. "
                     "Toda cifra debe salir de consultar_datos y todo hecho de buscar_documentos."})
    continue
```

> Sin herramientas, el modelo **escribe como un analista… de memoria**. Por eso las fuentes las pone **el código**.

### 13.2 La respuesta final (diapositiva 66)

Ante «¿Qué cambió en Malasaña a partir del 30 de marzo?», el modelo pidió una consulta SQL (ventas y abonos por
tienda y periodo) y una búsqueda de documentos («¿Qué cambios se implementaron en Malasaña a partir del 30 de
marzo?»), y respondió separando **cifras clave**, **hechos documentados**, **hipótesis** y **qué falta**:
ventas 42.000 → 28.000 €, unidades 467 → 304, netas 40.000 → 26.000 €, abonos estables en 2.000 € [S1]; el 30
de marzo se retiró el cartel del Pack 4 [D1][D2]; hipótesis: la retirada del regalo y la falta de stock podrían
explicar la caída [D1][D4]; falta tráfico, consultas sin compra y demanda no atendida.

**Ojo** (lo marca la diapositiva): **no consultó los pedidos de 4+ unidades (108 → 7), la cifra más
reveladora**. Pasar la verificación no significa haber hecho las preguntas importantes.

> **Datos** para el cuánto (bloque I), **voz** y **documentos** para el porqué (bloques II y III).

### 13.3 Qué hace bueno a un RAG (diapositiva 67)

| ✓ | Qué |
|---|---|
| Fuentes permitidas | Una lista explícita. Nunca la carpeta del profesor |
| Trocear por estructura | Sección, página o turno; nunca a mitad de frase |
| Una ficha por fragmento | Documento, página, fecha y estado (vigente o sustituido) |
| Búsqueda híbrida | Significado y palabras clave; *k* pequeño (3–5) |
| Citas y fuentes por código | El modelo escribe `[F#]`; el código construye la lista |
| Verificar y examinar | Cifras contra fuentes; un examen con la fuente esperada |
| Todo en local | Embeddings, índice y modelo: los datos no salen |

**Tres ideas del bloque III:** un RAG busca primero y responde después, citando · la similitud no sabe qué
documento manda (los metadatos y el código, sí) · una cita real no garantiza un significado real.

---

## 14. Los ejercicios, explicados

Documento: [`Enunciado - Ejercicios propuestos.pdf`](./Enunciado%20-%20Ejercicios%20propuestos.pdf). Cuatro
ejercicios, unas **dos horas y media**. Igual que en la sesión 1, el profesor no da todos los comandos: cada
script explica al principio para qué sirve y todos tienen `--help`. Si te atascas **más de media hora**, escríbele.

> Esta guía explica *qué se pide y cómo pensarlo*; no resuelve los ejercicios por ti.

**Sobre el modelo:** en clase, `qwen3:30b-a3b-instruct` (~18 GB cargado). En un portátil no cabe: usa
`qwen3:4b-instruct` o el que elegiste en la sesión 1 (`--modelo` en los scripts de datos, `--llm` en los de
documentos). «Que vuestro modelo saque peor nota que el del Jetson no es un fallo vuestro: es justo lo que quiero
que midáis.»

⚠️ **El anexo no viene:** el enunciado habla de un anexo con los resultados del Jetson y la respuesta del
analista, pero el PDF solo tiene 3 páginas. Los números de referencia del Jetson están en las diapositivas
(examen rápido: 2/5 en modo clase y 5/5 con la capa, diapositiva 11) y la respuesta del analista, en la
diapositiva 66 (sección 13.2 de esta guía).

### Ejercicio 1 · El SQL libre, con y sin capa semántica (~40 min)

| Lo que hay que conseguir | Cómo pensarlo |
|---|---|
| **Comprobar la capa antes de usarla** | El script 02 tiene una opción que compara las vistas con el 03. Si algo no sale en verde, no sigas. |
| **Ver lo que ve el modelo** | Saca el *system prompt* completo y busca **tres avisos de negocio** dentro de los comentarios (sección 3.5: qué columna no descuenta abonos, qué no es un cliente…). |
| **La misma pregunta, dos modos** | Neto de Malasaña en A y B con el script 01, en modo clase y con la capa. Copia el SQL de cada uno. Si no sale 40.000 / 26.000 €, busca la línea culpable con la tabla de la sección 3.1. |
| **El examen rápido** | El script 04 en los dos modos con tu modelo (unos minutos). |
| **Tres preguntas tuyas** | Que no estén en ningún examen (el 04 te deja verlos sin modelo) y **una imposible** (piensa en lo que no existe). **Antes** de preguntar al modelo, calcula tú la respuesta con tu propio SQL sobre las vistas (el 02 te deja ejecutarlo con las mismas barreras). |

**Qué entregar:** tu modelo y tiempo medio por pregunta; el examen rápido en los dos modos (aciertos y qué
pregunta falla) frente al Jetson; el SQL de Malasaña en los dos modos y, si falla, la línea culpable; tus tres
preguntas (respuesta correcta, lo que dijo el modelo y, si falla, el **tipo de error** con la clasificación de la
sesión 1). Pregúntate: **¿lo habría cazado el verificador?** Recuerda qué comprueba exactamente (sección 4: que
el número *exista* en un resultado, no que signifique lo pedido). Y **una mejora de la capa**: una vista, columna
o comentario que añadirías para que tu modelo no repita el fallo.

### Ejercicio 2 · Transcribid la llamada y auditadla (~40 min)

| Lo que hay que conseguir | Pistas |
|---|---|
| **Escucharla primero** | La versión mono (menos de 2 minutos). Apunta: hasta qué día dice Álex que duró el Pack 4, qué pasó el día 6 y a qué horas, y qué dice Dani de las visitas. Es tu **referencia humana**. |
| **Instalar Whisper** (`openai-whisper`) en el entorno | Antes, PyTorch para tu sistema desde su web: sin GPU NVIDIA, la versión **CPU** (la de por defecto puede bajar varios GB que no necesitas). Archivo: `requirements_audio.txt`. |
| **Transcribir por canales** con `small`, y con `turbo` si aguanta tu equipo | Apunta cuánto tarda frente a los 113 s de la llamada. En CPU puede tardar varios minutos. |
| **Cinco palabras dudosas** | El script marca las de p < 0,70. Ve a ese segundo (el visor del 08 deja hacer clic en cada palabra) y escucha: ¿acertó? Busca también algún error con probabilidad alta. |
| **Comparar dos transcripciones** | La tuya con la del Jetson, small con turbo, o con y sin `--solo-voz`. Elige una frase que cambie y explica qué cambió **en la entrada**. Prudencia: un solo ejemplo no prueba una causa (sección 8.3). |
| **Del audio al dato** | Tres cosas que se dicen en la llamada, comprobadas en otra fuente: datos (tu SQL sobre las vistas) o documentos (sección 8.9). |

Si en media hora no consigues instalarlo, usa las transcripciones del Jetson que vienen en `transcripciones/`
y dilo en la entrega.

⚠️ **Problema del zip (comprobado):** en modo canales, `07_transcribir.py` lee `data/audio/llamada_0704_central.wav`
y `llamada_0704_tienda.wav`, que **no vienen en el zip** (solo están `dos_canales` y `escucha_mono`). Sin
ellos, el modo por defecto falla. Se crean separando los dos canales del estéreo (con `ffmpeg`; lo he probado y
el módulo `wave` de Python los lee bien):

```bash
cd ~/ebis/07_llm_open_source/clase_02/DropLab_sesion_2/data/audio
ffmpeg -i llamada_0704_dos_canales.wav -af "pan=mono|c0=c0" llamada_0704_central.wav   # izquierdo = Álex
ffmpeg -i llamada_0704_dos_canales.wav -af "pan=mono|c0=c1" llamada_0704_tienda.wav    # derecho = Dani
```

(Con `channelsplit` en vez de `pan`, `ffmpeg` escribe una cabecera WAV extendida que `wave` no sabe leer.)

**Qué entregar:** equipo, modelo de Whisper y tiempos (o «usé las del Jetson» y por qué); una **tabla de cinco
palabras dudosas** (palabra, probabilidad, lo que se oye, si acertó); la comparación de dos transcripciones con
una explicación prudente; las tres comprobaciones (qué se dice, dónde se comprueba, si coincide); y **una frase**:
si esta transcripción entrara en un informe para dirección, ¿cómo la presentarías? (No es un acta revisada por nadie.)

### Ejercicio 3 · Montad el RAG y cambiad una decisión (~50 min)

«Cómo se trocea, qué ficha lleva cada fragmento y cómo se busca son decisiones del científico de datos, no del
modelo. **Sin medir, es solo una opinión.**»

| Lo que hay que conseguir | Pistas |
|---|---|
| **El RAG funcionando** | `ollama pull bge-m3`, el corpus (con la transcripción del Jetson salen 51 fragmentos) y el índice. Son los scripts **10 y 11, y el orden importa**. |
| **Mirar cómo se trocea** un PDF y la llamada | El 10 enseña una fuente antes y después. Elige un fragmento del expediente y explica de dónde sale cada dato de su ficha: **¿lo pone el documento o lo deduce el código?** (sección 10.2) |
| **La línea base** | Examen de recuperación del 14 con **k = 3 y k = 1**: aciertos y **MRR** de las tres búsquedas. Es rápido: no usa el LLM. |
| **Cambiar UNA decisión** y repetir | (a) quitar la cabecera de contexto del texto que se indexa; (b) trocear mucho más pequeño bajando el límite de palabras; (c) otro modelo de embeddings (p. ej. `nomic-embed-text`). Para (a) y (b) hay que tocar el 10 (ya viste en las secciones 10.1 y 10.3 qué controla el límite y cómo se construye el texto indexado). Después, **rehacer corpus e índice**. |
| **Preguntar a los documentos** con tu modelo (13) | La pregunta del Pack 4, una tuya y una imposible. Abre las fuentes citadas y léelas: ¿dicen lo mismo que la respuesta? |
| **Deshacer el cambio** | Y volver a crear corpus e índice antes del ejercicio 4. |

**Qué entregar:** la ficha de tu fragmento explicada; una **tabla antes/después** (aciertos y MRR por búsqueda,
con k = 3 y k = 1, y qué preguntas cambian); tu conclusión en 2–3 frases («si mejora una cosa y empeora otra,
contadlo tal cual: eso es lo interesante»); y las tres respuestas con sus citas, indicando si la fuente dice
exactamente lo mismo. Si encuentras **una cita real con un significado distinto**, señálala (sección 12.3).

Ten en cuenta: el examen de recuperación solo usa los índices que existan (si no has creado el de
`nomic-embed-text`, lo omite y lo dice). Para la opción (c), además de `ollama pull`, hay que crear su índice con
`11_indice.py --modelo …`; el 10 no cambia.

### Ejercicio 4 · Cinco frases para dirección (~20 min)

Parte de la respuesta que escribió el analista (script 15) en el Jetson. Como el anexo no viene en el PDF, está
en la **diapositiva 66** (sección 13.2). Pasó la verificación del código: todas sus cifras salen de una
consulta y todas sus citas existen.

| Lo que hay que hacer | Cómo pensarlo |
|---|---|
| **Auditarla frase a frase** | ¿Qué es un **hecho**, qué es **testimonio** (la llamada, el diario) y qué es **hipótesis**? ¿Alguna afirmación sin fuente que la respalde? ¿Qué dato importante no consultó? |
| **Tus cinco frases para dirección** | La hipótesis que priorizas, las cifras con la consulta que las da, las fuentes (documento y página o sección; la llamada, como testimonio) y el dato que pedirías para confirmarla. **Sin afirmar causas que los datos no prueban.** |
| Opcional | Ejecutar el analista con tu modelo y comparar con el del Jetson. |

**Método práctico:** usa la tabla de tipos de error de la sesión 1 (cifra inventada, cifra real con significado
falso, afirmación ajena como dato, causa no demostrada, interpretación contradicha) y añade dos preguntas nuevas
de esta sesión: *¿esta fuente es un documento vigente o un borrador?* y *¿esta fecha es prevista o confirmada?*

---

## 15. Enlaces y test

### Enlaces ([`Enlaces_sesion_2.pdf`](./Enlaces_sesion_2.pdf), revisados el 13/10/2026)

| # | Para | Enlace | Qué saber hacer |
|---|---|---|---|
| 1 | Ej. 1 | Vistas y comentarios en DuckDB (`create_view`, `comment_on`) | Leer una vista del 02 y escribir otra con su comentario |
| 2 | Ej. 1 | DuckDB desde Python (DB-API) | Ejecutar tu consulta; pasar valores como **parámetros**, no pegados en el texto |
| 3 | Ej. 1 | Capa semántica de **dbt** | Por qué definir una métrica una vez en código es mejor que explicarla en cada prompt |
| 4 | Ej. 1 | Modelos de expertos (blog MoE de Hugging Face) y ficha de `Qwen3-30B-A3B-Instruct-2507` | Parámetros totales frente a activos; qué cuesta memoria y qué cuesta tiempo |
| 5 | Ej. 2 | Repositorio de Whisper (MIT) | Instalarlo y elegir un modelo que tu equipo pueda mover |
| 6 | Ej. 2 | Instalar PyTorch (selector) | Instalar la versión adecuada antes que Whisper (CPU si no hay GPU NVIDIA) |
| 7 | Ej. 2 | Curso de audio de Hugging Face (cap. 1) | Explicar qué recibe Whisper: no el sonido, sino números |
| 8 | Ej. 3 | Embeddings en Ollama, `bge-m3` (Ollama y Hugging Face) | Pedir el vector de un texto y saber cuántos números tiene (con Ollama, solo el vector denso) |
| 9 | Ej. 3 | Funciones de listas de DuckDB (`list_cosine_similarity`) | Entender qué devuelve |
| 10 | Ej. 3 | PyMuPDF | Sacar el texto de una página y ver por qué hay que limpiarlo (si es escaneado, haría falta OCR) |
| 11 | Ej. 3 | BM25 (Wikipedia) y artículo original de RRF (2009) | Explicar por qué RRF usa la **posición** y no la puntuación |
| 12 | Extra | Artículo que bautizó el RAG (Lewis y otros, 2020) | Situar de dónde viene el término |
| 13 | Extra | Recuperación contextual (Anthropic) | Relacionarlo con el experimento (a) del ejercicio 3 |
| 14 | Extra | Clasificación MTEB de embeddings | Filtrar por idioma y tamaño; una buena nota general no garantiza el mejor para tus documentos |
| 15 | Extra | Artículo de Whisper (Radford y otros, 2022) | Contar en dos frases cómo se entrenó |
| 16 | Extra | Ajustar Whisper (blog), PEFT y artículo de LoRA | Qué hace falta antes de ajustar: transcripciones revisadas, separar por llamada y medir el WER |

### Test ([`Test - sesión 2.pdf`](./Test%20-%20sesi%C3%B3n%202.pdf))

15 preguntas para hacer **al final y sin apuntes**. Esta tabla dice qué sección de la guía tiene lo necesario
para razonar cada una (sin dar la respuesta):

| # | Tema | Sección |
|---|---|---|
| 1 | Qué es exactamente la capa semántica | 3.3 |
| 2 | Por qué el 30B dio 39.817,63 € con tablas crudas sin ningún error | 3.1 |
| 3 | Qué error **no** puede detectar el verificador | 4 |
| 4 | Por qué tres exámenes y no solo la batería | 5.2 |
| 5 | Cómo el 30B va casi igual de rápido que el 4B | 6.4 |
| 6 | Qué afirmación sobre Whisper es correcta | 7.6 y 8.1 |
| 7 | «¿Qué pasa?» en un tramo casi en silencio | 8.5 |
| 8 | Para qué sirve la probabilidad por palabra | 8.4 |
| 9 | Por qué sabemos quién dice cada frase | 7.5 |
| 10 | Plan correcto para adaptar Whisper con 1.000 llamadas | 8.8 |
| 11 | Para qué sirve la cabecera de cada fragmento | 10.3 |
| 12 | Quién decide que el borrador está sustituido | 10.4 y 11.3 |
| 13 | Buscar «HIST-JOIN-001»: semántica, BM25 e híbrida | 11.2 |
| 14 | La fuente sale entre las 3 primeras, pero la frase dice «inicio efectivo» | 12.3 |
| 15 | El analista respondió sin herramientas: qué lo detectó y qué se cambió | 13.1 |

---

## 16. Mapa de los scripts y cómo ejecutarlos

### 16.1 Mapa

| Script | Qué hace | Necesita | Conceptos |
|---|---|---|---|
| `sesion_2/01_preguntar_datos.py` | SQL libre en modo `clase` (tablas crudas + reglas) o `capa` (vistas + verificador) | Ollama | Capa semántica, verificador |
| `sesion_2/02_capa_semantica.py` | Lo que ve el modelo y lo que no; `--comprobar`, `--sql`, `--prompt` | Nada | Vistas con el negocio dentro |
| `sesion_2/04_examen.py` | Examen con respuestas calculadas a mano y nota | Ollama (salvo `--ver`) | Medir para elegir |
| `sesion_2/06_ver_audio.py` | Datos, onda, zoom, espectrograma, log-mel y turnos | Nada (numpy, matplotlib) | Un audio son números |
| `sesion_2/07_transcribir.py` | Transcribe la llamada con Whisper; marca palabras dudosas | PyTorch + openai-whisper (y los WAV por canal, ver 14) | Whisper, alucinaciones |
| `sesion_2/08_ver_transcripcion.py` | Página web con la llamada como chat; clic = escuchar | Nada | Auditar la transcripción |
| `sesion_2/09_panel_en_directo.py` | Panel en el navegador: onda, quién habla, espectrograma, log-mel y texto sincronizados | Nada (servidor local) | Todo el bloque II a la vez |
| `sesion_2/10_corpus.py` | Trocea y etiqueta las 10 fuentes → `rag/corpus.jsonl` | Nada (pymupdf) | Trocear por estructura, ficha |
| `sesion_2/corpus_html.py` | Lo usa `10_corpus.py --html` (no se ejecuta solo) | — | — |
| `sesion_2/11_indice.py` | Vectores con Ollama → `rag/indice_<modelo>.duckdb` | Ollama + modelo de embeddings | Embeddings, similitud coseno |
| `sesion_2/12_buscar.py` | Búsqueda semántica, por palabras o híbrida | Ollama + embeddings (en los tres modos) | BM25, RRF, versiones |
| `sesion_2/13_preguntar_documentos.py` | Responde con fragmentos citados y verifica | Ollama | Citas, verificación |
| `sesion_2/14_evaluar_rag.py` | Examen de recuperación (sin LLM) o de respuestas | Ollama | Hit@k, MRR |
| `sesion_2/15_analista.py` | Datos + documentos en una respuesta | Ollama | Todo junto |
| `sesion_1/03_metricas_basicas.py` | La fuente de verdad de la sesión 1; ahora con `--reparto` | Nada | El código calcula |
| `sesion_1/07_herramienta_funcion.py`, `08_herramienta_sql.py` | Los de la sesión 1 (el 01 y el 02 los importan) | Ollama | Función fija, SQL libre |

**Citados pero ausentes en el zip** (no los inventes): `03_monitor_recursos.py` (práctica 2, monitor de RAM/GPU),
`sesion_1/04_conectar_ollama.py` (está en [`clase_01/Ejercicios/practica/`](../clase_01/Ejercicios/practica/)), los
`docs/sesion_2/…` que citan los comentarios de los scripts y la carpeta `experimentos/` (los scripts 09 y 10 la
usan solo como respaldo si no hay transcripciones; aquí sí las hay).

### 16.2 Preparar el entorno (una sola vez)

Hay **un único `.venv` en la raíz del tema**, compartido por todas las clases. El `requirements.txt` de la raíz
ya incluye el de esta sesión (añade `numpy`, `matplotlib` y `pymupdf` a lo de la sesión 1):

```bash
cd ~/ebis/07_llm_open_source
source .venv/bin/activate
pip install -r requirements.txt
```

Modelos de Ollama: `qwen3:4b-instruct` (ya lo tienes) y **`bge-m3`** para el RAG (`ollama pull bge-m3`). El de
clase, `qwen3:30b-a3b-instruct-2507-q4_K_M`, ocupa ~18 GB: **no cabe en un portátil de 16 GB**. Por eso, en
cada script que llama al modelo, pasa `--modelo qwen3:4b-instruct` (scripts 01 y 04) o `--llm qwen3:4b-instruct`
(13, 14 y 15). Si no, intentarán usar el 30B y fallarán.

**Whisper** (solo ejercicio 2) se instala aparte, encima de lo anterior: primero PyTorch para tu sistema, luego
`pip install -r clase_02/DropLab_sesion_2/requirements_audio.txt`. Pesa GB: hazlo solo si vas a transcribir.

### 16.3 Desde dónde se lanzan

Todas las órdenes se lanzan **desde la carpeta `DropLab_sesion_2`** (la que contiene `data/` y `practica/`):

```bash
cd ~/ebis/07_llm_open_source/clase_02/DropLab_sesion_2
```

Cualquier script acepta `-h`. Los archivos que generan (`rag/`, `figuras_audio/`, `panel/`, HTML de
transcripciones) quedan dentro de `practica/sesion_2/`.

### 16.4 Bloque I · datos

**`02_capa_semantica.py`** — sin modelo.

| Opción | Para qué |
|---|---|
| *(ninguna)* | Lo que el modelo NO ve (los 6 CSV en `crudo`) y lo que SÍ ve (vistas con comentarios) + la guía |
| `--comprobar` | Compara las vistas con las cifras del 03 (7 comprobaciones) |
| `--sql "SELECT …"` | Ejecutas **tú** una consulta sobre las vistas, con las mismas barreras |
| `--prompt` | El *system prompt* completo que recibe el modelo (~1.250 palabras) |

```bash
python practica/sesion_2/02_capa_semantica.py
python practica/sesion_2/02_capa_semantica.py --comprobar
python practica/sesion_2/02_capa_semantica.py --sql "SELECT periodo, SUM(ventas_netas) FROM resumen_diario WHERE tienda = 'Malasaña' GROUP BY periodo"
python practica/sesion_2/02_capa_semantica.py --prompt
```

**`01_preguntar_datos.py`** — necesita Ollama.

| Opción | Por defecto | Para qué |
|---|---|---|
| `--modo {capa,clase}` | `capa` | `clase` = tablas crudas + reglas, como el 08 (4 rondas y sin verificador) |
| `-q`, `--question "…"` | neto de Malasaña en A y B | Otra pregunta |
| `--modelo NOMBRE` | `qwen3:30b-a3b-instruct-2507-q4_K_M` | Otro modelo (en portátil: `qwen3:4b-instruct`) |
| `--sin-verificar` | (verifica) | Quitar la revisión de cifras |

```bash
python practica/sesion_2/01_preguntar_datos.py --modo clase --modelo qwen3:4b-instruct
python practica/sesion_2/01_preguntar_datos.py --modelo qwen3:4b-instruct
python practica/sesion_2/01_preguntar_datos.py --modelo qwen3:4b-instruct -q "¿Qué ventas se hicieron en las tres tiendas el 25 de abril?"
```

Imprime lo que recibe el modelo, cada SQL con su resultado, la revisión del código, la respuesta y el tiempo
(con los segundos de carga y los tokens de entrada).

**`04_examen.py`** — necesita Ollama salvo con `--ver`.

| Opción | Por defecto | Para qué |
|---|---|---|
| `--ver` | — | Preguntas y respuestas correctas, sin modelo |
| `--examen {bateria,validacion,final}` | `bateria` | Qué examen |
| `--modo {clase,capa}` | `capa` | Tablas crudas o capa semántica (+ verificador) |
| `--rapido` | — | Solo P01, P06, P08, P11 y P13 |
| `--preguntas P01 P07` | — | Solo esas |
| `--modelo NOMBRE` | el 30B | Otro modelo |

```bash
python practica/sesion_2/04_examen.py --ver
python practica/sesion_2/04_examen.py --ver --examen final
python practica/sesion_2/04_examen.py --modo clase --rapido --modelo qwen3:4b-instruct
python practica/sesion_2/04_examen.py --modo capa  --rapido --modelo qwen3:4b-instruct
```

Termina con «NOTA: x de n (…) · s por pregunta» (el tiempo descuenta la carga del modelo).

**`sesion_1/03_metricas_basicas.py --reparto`** añade cuántos pedidos de Malasaña tienen 2, 3 o 4 unidades en A y B.

### 16.5 Bloque II · voz

**`06_ver_audio.py`** — sin modelo. Vista (primer argumento): `datos`, `onda`, `zoom`, `espectrograma`, `mel`,
`turnos` o `todo` (por defecto).

| Opción | Para qué |
|---|---|
| `--inicio S` | Segundo de inicio para `zoom` y `mel` |
| `--guardar` | Guardar además cada figura en PNG (`figuras_audio/`) |
| `--sin-ventana` | No abrir ventanas (por SSH): solo guardar |
| `--archivo RUTA` | Otro WAV (debe ser de 16 kHz) |

```bash
python practica/sesion_2/06_ver_audio.py datos
python practica/sesion_2/06_ver_audio.py zoom --inicio 1.0
python practica/sesion_2/06_ver_audio.py mel
python practica/sesion_2/06_ver_audio.py turnos
```

**`07_transcribir.py`** — necesita PyTorch + Whisper (y, en modo canales, los dos WAV de la sección 14).

| Opción | Por defecto | Para qué |
|---|---|---|
| `--modelo` | `turbo` | `tiny`, `base`, `small`, `medium`, `turbo`, `large-v3` |
| `--modo {canales,mono}` | `canales` | Cada canal por separado (sabemos quién habla) o la mezcla |
| `--solo-voz` | — | Solo los tramos con energía de voz |
| `--pista` | — | Darle el vocabulario del negocio (`initial_prompt`) |

```bash
python practica/sesion_2/07_transcribir.py --modelo small
python practica/sesion_2/07_transcribir.py --modo mono
python practica/sesion_2/07_transcribir.py --modelo small --solo-voz
```

Guarda `transcripciones/<modelo>_<modo>[_solo-voz][_pista].json` (ojo: **sobrescribe** el del Jetson si coincide
el nombre; cópialo antes si quieres compararlos).

**`08_ver_transcripcion.py`** — sin modelo. Argumento opcional: el JSON (por defecto, el más reciente). `--abrir`
lo abre en el navegador. Escribe un `.html` junto al JSON.

```bash
python practica/sesion_2/08_ver_transcripcion.py transcripciones/turbo_canales_solo-voz.json --abrir
```

**`09_panel_en_directo.py`** — sin modelo. Levanta un servidor solo en tu equipo (`127.0.0.1:8765`, o el
siguiente libre) y abre el panel. Opciones: `--transcripcion RUTA`, `--puerto N`, `--sin-abrir`. Teclas: espacio
= reproducir/pausa, ← → = 5 s. Para terminar, `Ctrl + C`.

```bash
python practica/sesion_2/09_panel_en_directo.py --transcripcion practica/sesion_2/transcripciones/turbo_canales_solo-voz.json
```

### 16.6 Bloque III · documentos

Orden obligatorio la primera vez: **10 → 11 → (12, 13, 14, 15)**. Si cambias el 10, rehaz el 11.

**`10_corpus.py`** — sin modelo. Siempre reescribe `rag/corpus.jsonl`.

| Opción | Para qué |
|---|---|
| *(ninguna)* | El mapa: fuentes y fragmentos (un ■ por fragmento, del color de su estado) |
| `--trocear FUENTE` (+ `--todo`) | Cómo se corta una fuente, antes y después (vale parte del nombre: `calendario`, `expediente`, `llamada`…) |
| `--ver N` | La ficha completa del fragmento N y de dónde sale cada dato |
| `--lista` | Todos los fragmentos, una línea cada uno |
| `--html` (+ `--abrir`) | Todo el corpus en el navegador, original y fragmentos lado a lado |
| `--llamada ARCHIVO.json` | Usar otra transcripción (por defecto `turbo_canales_solo-voz.json`) |

```bash
python practica/sesion_2/10_corpus.py
python practica/sesion_2/10_corpus.py --trocear calendario
python practica/sesion_2/10_corpus.py --trocear expediente
python practica/sesion_2/10_corpus.py --ver 36
python practica/sesion_2/10_corpus.py --html --abrir
```

**`11_indice.py`** — necesita Ollama y el modelo de embeddings.

| Opción | Por defecto | Para qué |
|---|---|---|
| *(ninguna)* | — | Crea `rag/indice_bge-m3.duckdb` (51 × 1.024 números) |
| `--modelo NOMBRE` | `bge-m3` | Otro modelo (crea su propio índice) |
| `--ver "texto"` | — | El vector de un texto, en números y colores |
| `--comparar ["a" "b" …]` | ejemplo preparado | ¿Qué textos quedan cerca? |

```bash
ollama pull bge-m3
python practica/sesion_2/11_indice.py
python practica/sesion_2/11_indice.py --comparar
python practica/sesion_2/11_indice.py --comparar "tote bag" "bolsa de regalo" "avería del vehículo"
```

**`12_buscar.py`** — necesita Ollama (incluso en modo `palabras`, porque siempre calcula también la lista semántica
para enseñar el puesto de cada fragmento).

| Opción | Por defecto | Para qué |
|---|---|---|
| `"pregunta"` | — | Obligatoria |
| `--modo {semantica,palabras,hibrida}` | `hibrida` | Cómo buscar |
| `-k N` | 5 | Cuántos fragmentos |
| `--explicar` | — | Las dos listas y cómo se combinan (RRF) |
| `--sin-vigentes` | — | No añadir el documento que sustituye a un borrador |
| `--corto` | — | Solo el ranking |
| `--modelo` | `bge-m3` | Índice de otro modelo de embeddings |

```bash
python practica/sesion_2/12_buscar.py "¿Hasta qué día estuvo vigente el Pack 4?" --explicar
python practica/sesion_2/12_buscar.py "HIST-JOIN-001" --modo palabras
python practica/sesion_2/12_buscar.py "¿Hasta qué día estuvo vigente el Pack 4?" --sin-vigentes
```

**`13_preguntar_documentos.py`** — necesita Ollama. Opciones: `"pregunta"`, `-k`, `--modo`, `--llm` (por defecto
el 30B), `--modelo` (embeddings), `--sin-reglas` (prompt mínimo, sin reglas de versiones ni fechas).

```bash
python practica/sesion_2/13_preguntar_documentos.py "¿Hasta qué día estuvo vigente el Pack 4?" --llm qwen3:4b-instruct
python practica/sesion_2/13_preguntar_documentos.py "¿Cuándo empezaron las obras?" --llm qwen3:4b-instruct
```

Enseña: lo que encontró el buscador (citado o no), la respuesta con cada cita del color del estado de su fuente,
la tabla de fuentes (la pone el código) y la verificación.

**`14_evaluar_rag.py`** — necesita Ollama.

| Opción | Por defecto | Para qué |
|---|---|---|
| `--parte {recuperacion,respuesta}` | `recuperacion` | Sin LLM (¿sale la fuente?) o con LLM (¿responde y cita bien?) |
| `-k N` | 5 | Cuántos fragmentos mira |
| `--llm` | el 30B | Modelo que responde (parte respuesta) |
| `--modelo`, `--modo` | `bge-m3`, `hibrida` | Embeddings y búsqueda (parte respuesta) |
| `--guardar ARCHIVO.json` | — | Guardar el detalle |

```bash
python practica/sesion_2/14_evaluar_rag.py -k 3
python practica/sesion_2/14_evaluar_rag.py -k 1
python practica/sesion_2/14_evaluar_rag.py --parte respuesta --llm qwen3:4b-instruct
```

La recuperación recorre `bge-m3`, `qwen3-embedding:0.6b`, `embeddinggemma` y `nomic-embed-text` y **omite los
que no tengan índice**.

**`15_analista.py`** — necesita Ollama. Opciones: `-q "…"`, `--llm`, `--guardar ARCHIVO.json`.

```bash
python practica/sesion_2/15_analista.py --llm qwen3:4b-instruct
python practica/sesion_2/15_analista.py --llm qwen3:4b-instruct -q "¿La rotura de stock del 6 de abril explica la caída de Malasaña?"
```

> **Datos en otra carpeta:** como en la sesión 1, los scripts de datos aceptan la variable `DROPLAB_DATOS`.

---

## 17. Resumen final

1. **Datos con garantías:** el negocio se escribe **una vez en código** (vistas con comentarios, comprobadas
   contra el 03). El modelo solo traduce la pregunta. Con el 30B pasa de 58 % a **91 %**.
2. **Verificador:** caza cifras inventadas, pero no cifras reales con significado falso (307 «líneas»). Por eso
   se enseña y se lee el SQL.
3. **Medir:** un examen con respuestas calculadas a mano, tres conjuntos (diseñar, comprobar, decidir), una
   pregunta imposible y temperatura 0.
4. **Coste:** un modelo de expertos ocupa por el total (18 GB) y va a la velocidad de los activos (3B). Más
   grande no es la solución sin datos bien presentados.
5. **Voz:** un audio son números; Whisper recibe una imagen log-mel de 30 s y escribe como un LLM, así que
   puede inventar. Un canal por persona, solo voz y contrastar con datos ayudan más que un modelo mayor.
6. **Documentos:** RAG local = trocear por estructura + ficha por fragmento + búsqueda híbrida (bge-m3 + BM25 +
   RRF) + citas que pone el código + verificación. La similitud no sabe qué versión manda: los metadatos sí.
7. **Todo junto:** cifras de los datos `[S#]` y hechos de los documentos `[D#]`. Sin herramientas, el modelo
   escribe de memoria; el código no lo acepta.

### Ideas para recordar siempre

- **El negocio, en el código; no en el prompt.**
- **Para elegir, mide** (y con preguntas que no usaste para diseñar).
- **La memoria la marca el total de parámetros; la velocidad, los activos.**
- **Una transcripción es una fuente más:** quién, cuándo, con qué probabilidad… y se contrasta.
- **Programado no es ocurrido. Un borrador no es lo vigente. Un hecho repetido no son dos pruebas.**
- **La similitud no sabe qué documento manda.**
- **Una cifra que existe o una cita que existe no garantizan un significado real: hay que leerlas.**

---

## 18. ¿Qué sigue?

Las diapositivas cierran con «*Datos, voz y documentos, en local y con fuentes: el analista de DropLab,
completo*». En la sesión 1 se anunció que en la sesión 3 llegarían **tickets e imágenes**; el material ya está en
[`clase_03/`](../clase_03/), pero lo veremos con su propia guía.

### Preguntas para repasar

1. ¿Por qué el 30B con tablas crudas (58 %) no es mejor que el 4B (61 %), y con la capa semántica sí (91 % frente a 67 %)?
2. La capa semántica esconde los CSV en `crudo`, pero la barrera SQL no los bloquea. ¿Qué diferencia hay entre esconder y prohibir?
3. Pon un ejemplo de error que el verificador del bloque I caza y otro que no. ¿Qué tienen en común el «8 SKU», las «307 líneas» y el «inicio efectivo»?
4. ¿Por qué hacen falta tres exámenes y qué pasaría si solo miraras la batería?
5. `qwen3:30b-a3b`: ¿qué significan `30b` y `a3b`, y cuál de los dos decide la memoria y cuál la velocidad?
6. ¿Por qué Whisper puede escribir «¿Qué pasa?» donde no hay voz, y qué opción del script lo evitó?
7. ¿Cómo usarías la probabilidad por palabra si tuvieras que revisar 100 llamadas?
8. ¿Por qué el borrador del Pack 4 sale primero en la búsqueda y qué tres defensas lo corrigen?
9. ¿Por qué RRF combina posiciones y no puntuaciones?
10. ¿Qué dato importante no consultó el analista y por qué la verificación no podía detectarlo?
