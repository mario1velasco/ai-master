# Guía de estudio — Tema 7, Sesión 3: el Asistente DropLab, de punta a punta

> Esta guía explica, con lenguaje sencillo y ejemplos del caso, todo lo que hay en `clase_03/`: las
> [diapositivas](./Diapositivas%20Tema%207%20-%20Sesion%203.pdf) (64 páginas), el código de
> [`DropLab_sesion_3/`](./DropLab_sesion_3/) (sobre todo [`practica/sesion_3/`](./DropLab_sesion_3/practica/sesion_3/)),
> la [guía de integración](./guia_integracion.html) del profesor, la
> [guía del alumno](./DropLab_sesion_3/alumnos/sesion_3/guia_alumno.md), el [reto](./DropLab_sesion_3/alumnos/sesion_3/reto.md),
> el [enunciado de la entrega final](./Enunciado%20-%20ejercicios%20propuestos.pdf), los
> [enlaces](./Enlaces_sesion_3.pdf) y el [test](./Test%20-%20sesi%C3%B3n%203.pdf).
> Sigue a las guías de la [sesión 1](../clase_01/EXPLICACION_tema_1.md) y la [sesión 2](../clase_02/EXPLICACION_tema_2.md).

## Índice

1. [La idea de la sesión en una frase](#1-la-idea-de-la-sesión-en-una-frase)
2. [El plan de hoy y la clave del test de la sesión 2](#2-el-plan-de-hoy-y-la-clave-del-test-de-la-sesión-2)
3. [Bloque I · Terminar el RAG (repaso)](#3-bloque-i--terminar-el-rag-repaso)
4. [Bloque II · Leer una imagen: cuatro tareas distintas](#4-bloque-ii--leer-una-imagen-cuatro-tareas-distintas)
5. [Bloque II · Práctica 1: leer y comprobar un ticket](#5-bloque-ii--práctica-1-leer-y-comprobar-un-ticket)
6. [Bloque II · El segundo encargo: los PDF de junio](#6-bloque-ii--el-segundo-encargo-los-pdf-de-junio)
7. [Bloque II · Práctica 2: cuatro formas de leer una página](#7-bloque-ii--práctica-2-cuatro-formas-de-leer-una-página)
8. [Bloque III · La arquitectura: quién es quién](#8-bloque-iii--la-arquitectura-quién-es-quién)
9. [Bloque III · La API: un contrato y errores con nombre](#9-bloque-iii--la-api-un-contrato-y-errores-con-nombre)
10. [Bloque III · El flujo con LangGraph](#10-bloque-iii--el-flujo-con-langgraph)
11. [Bloque III · Open WebUI y la Pipe](#11-bloque-iii--open-webui-y-la-pipe)
12. [Bloque IV · El asistente, en directo](#12-bloque-iv--el-asistente-en-directo)
13. [Extras: medir por piezas y una respuesta convincente y falsa](#13-extras-medir-por-piezas-y-una-respuesta-convincente-y-falsa)
14. [Cierre: hacia producción y lo que nos llevamos](#14-cierre-hacia-producción-y-lo-que-nos-llevamos)
15. [La entrega final, explicada](#15-la-entrega-final-explicada)
16. [Enlaces y test](#16-enlaces-y-test)
17. [Mapa de los scripts y cómo ejecutarlos](#17-mapa-de-los-scripts-y-cómo-ejecutarlos)
18. [Resumen final](#18-resumen-final)

---

## 1. La idea de la sesión en una frase

> **Un modelo lee y redacta; el código calcula, comprueba y dice lo que no se sabe.**

Es la regla de oro de la sesión 1 (*el código calcula, el modelo redacta, tú verificas*) llevada al final del
camino. Hoy el modelo además **lee** cosas que no son texto (un ticket fotografiado, un PDF escaneado, un
gráfico), y todas las piezas de las tres sesiones se juntan en un **asistente que se usa desde el navegador**:

```
Escribes una pregunta  →  Una API la recibe  →  Un flujo decide     →  El código comprueba    →  El modelo redacta
y adjuntas un ticket      (FastAPI, Jetson)     imagen · cifras ·      caja, versiones,          citando
                                                documentos             lecturas                  [S#] [D#] [V#]
```

Es la última sesión del tema. Lo importante no es entender cada línea del código (ya está hecho), sino saber
**qué pieza hace qué** y **quién decide cada paso: el modelo o el código**.

---

## 2. El plan de hoy y la clave del test de la sesión 2

| Bloque | Tema | Prácticas |
|---|---|---|
| **I** | Terminar el RAG: trocear, buscar, versiones y citas | 5 y 6 (las que quedaron de la sesión 2) |
| **II** | Leer lo que no es texto: un ticket y los PDF de junio | 1 y 2 |
| **III** | Del script al asistente: API, Open WebUI y LangGraph | 3 |
| **IV** | El asistente en directo: preguntas difíciles de punta a punta | En directo, juntos |

En el Jetson se usan dos modelos: **`qwen3:30b-a3b-instruct-2507-q4_K_M`** para el texto (planificar y redactar)
y **`qwen3-vl:8b-instruct`** para las imágenes. En un portátil de 16 GB: `qwen3:4b-instruct` y
`qwen3-vl:4b-instruct` (las variantes *instruct*: la otra razona antes de contestar y tarda minutos).

### La clave del test de la sesión 2 (diapositivas 4 y 18)

El profesor dio las respuestas al empezar. Las dejo aquí porque cierran la [guía de la sesión 2](../clase_02/EXPLICACION_tema_2.md):

| # | La idea | Resp. |
|---|---|---|
| 1 | Capa semántica: vistas en código que ya resuelven periodos, abonos y tiendas | B |
| 2 | El abono va al periodo de su fecha de reconocimiento, no al de la venta | C |
| 3 | El verificador no ve «307 líneas» si 307 aparece en un resultado (eran unidades) | D |
| 4 | Batería para diseñar; validación y prueba final para medir sin hacerse trampas | A |
| 5 | MoE: ~3B parámetros activos por token, pero los 30B en memoria | B |
| 6 | Whisper: log-mel, codificador y decodificador que escribe tokens como un LLM | C |
| 7 | Con poca señal, el decodificador completa algo plausible: alucinación | A |
| 8 | La probabilidad por palabra prioriza qué escuchar; no certifica | B |
| 9 | Quién habla: un canal por interlocutor, no reconocimiento de voz | D |
| 10 | Ajuste fino: revisar etiquetas, separar por llamada y medir el WER antes y después | D |
| 11 | La cabecera (título, código, estado, fecha) se indexa para que el fragmento se entienda solo | A |
| 12 | **El borrador lo marca una regla del código («sustituye a…»), no los embeddings ni el LLM** | C |
| 13 | BM25 clava códigos; la semántica, sinónimos. La híbrida (RRF) combina posiciones | A |
| 14 | **Cita real, significado falso: la búsqueda acertó, falló la redacción. Hay que leer la fuente** | B |
| 15 | Sin consultar, cifras inventadas: lo cazó el código. Ahora no acepta respuestas sin consultar | D |

> «La 12 y la 14 son las dos ideas clave del bloque: las versiones las decide el código, y hay que leer la fuente.»

---

## 3. Bloque I · Terminar el RAG (repaso)

El bloque III de la sesión 2 (el RAG local) no dio tiempo en clase y se terminó aquí con las **mismas
diapositivas y los mismos scripts** (`practica/sesion_2/10` a `15`). Está explicado en detalle en las secciones
9 a 13 de la [guía de la sesión 2](../clase_02/EXPLICACION_tema_2.md#9-bloque-iii--diez-fuentes-una-historia-y-cuatro-trampas).
En resumen:

| Paso | Script | Qué hace |
|---|---|---|
| 1 · Trocear y etiquetar | `10_corpus.py` | 10 fuentes → **51 fragmentos**, cada uno con su **ficha** (documento, página, fecha, estado) |
| 2 · Índice vectorial | `11_indice.py` | Cada fragmento → 1.024 números (bge-m3), guardados en DuckDB |
| 3 · Buscar | `12_buscar.py` | Híbrida (significado + palabras, unidas por RRF); si sale un borrador, añade el vigente |
| 4 · Responder y verificar | `13_preguntar_documentos.py` | Solo con esos fragmentos, citando `[F#]`; el código revisa las citas |

**Tres ideas para llevar (diapositiva 19):**

1. **Trocear y etiquetar es trabajo del código.** La ficha viaja con cada fragmento.
2. **Lo más parecido no es lo vigente.** Las versiones las resuelve una regla del código, no los embeddings.
3. **Citar no es demostrar.** El código comprueba que las citas y las cifras existen; el significado, una persona.

Novedad respecto al zip de la sesión 2: `DropLab_sesion_3` ya trae los índices creados (`practica/sesion_2/rag/` y
el ampliado de `practica/sesion_3/rag/`), y `11_indice.py` y `12_buscar.py` aceptan otra ruta de índice para
poder usar el ampliado con los PDF de junio (sección 7.6).

---

## 4. Bloque II · Leer una imagen: cuatro tareas distintas

### 4.1 «Leer una imagen» no es una sola cosa (diapositiva 21)

| Tarea | Qué hace | Ejemplo con el ticket |
|---|---|---|
| **OCR** · reconocer texto | Caracteres, sin saber qué significan | «TOTAL 231,99 EUR» |
| **VLM** · interpretar y responder | Entiende la imagen… y puede inventar con aplomo | «Es un justificante de 2 artículos por 231,99 €» |
| **Extracción** · devolver campos definidos | Campos con tipo: el código ya puede usarlos | `{"total_impreso": 231.99, …}` |
| **Verificación** · contrastar con otras fuentes | La hace **el código**, con los registros | caja: 211,99 → no coincide |

> **El modelo lee y propone; el código comprueba. Un VLM no es un notario.**

**VLM** = *Vision-Language Model*: un modelo de lenguaje que además recibe imágenes.

### 4.2 Para un ordenador, una imagen es una tabla de números (diapositiva 22)

Igual que en la sesión 2 un audio era una lista de números, una imagen es una **tabla de píxeles**: cada punto,
un número de 0 (negro) a 255 (blanco); en color, tres (rojo, verde y azul). El ticket son unos **4,8 millones de
números**. Una red aprende sola a reconocer bordes → trazos → letras → palabras y objetos. Hoy se usan
*transformers*: la imagen se corta en **parches** y cada parche se trata como una palabra (ViT, 2020).

### 4.3 Por dentro de un VLM: unos ojos, un traductor y un LLM (diapositiva 23)

```
Imagen        →  Parches          →  Codificador de visión  →  Proyector              →  LLM (36 capas)
724 × 1024 px    16 × 16 px          transformer de 27 capas:   2 × 2 parches → 1 token   tokens de imagen + texto
(la reduce       (como «palabras»    cada parche mira a todos   = el «idioma» del LLM     → escribe, token a token
 el código)       de imagen)
```

Lo que esto explica:

| Consecuencia | Ejemplo |
|---|---|
| **Más píxeles, más tokens** | El ticket original (1060 × 1500) ≈ 1.580 tokens. Reducido a 1024 px de lado ≈ 1.080 tokens y la mitad de tiempo, con el mismo resultado. Por eso el código reduce la imagen (`MAX_LADO_IMAGEN = 1024` en `asistente/config.py`). |
| **Ve trozos, no letras** | Una etiqueta pequeña o solapada cae en uno o dos tokens: el 4B lee **95** donde pone **96**. |
| **Escribe como un LLM** | Lo más probable, no lo comprobado: si no lo ve claro, completa… con aplomo. |

> **Un VLM es un LLM al que le han puesto ojos: lee y propone; no es un notario.**

---

## 5. Bloque II · Práctica 1: leer y comprobar un ticket

[`01_ver_imagen.py`](./DropLab_sesion_3/practica/sesion_3/01_ver_imagen.py) hace seis pasos y deja claro quién
hace cada uno:

| # | Paso | Quién |
|---|---|---|
| 1 | Pregunta libre: el VLM describe la imagen en prosa | modelo |
| 2 | Extracción: el mismo VLM, obligado a usar un esquema JSON | modelo |
| 3 | Validación: ¿es JSON?, ¿están los campos?, ¿tienen su tipo? (Pydantic) | código |
| 4 | Consulta: el pedido en caja, con SQL con parámetros | código |
| 5 | Comparación campo a campo, y del ticket consigo mismo | código |
| 6 | Veredicto: coincide · discrepancia · lectura dudosa · no verificable | código |

### 5.1 El esquema lo escribimos nosotros; Pydantic comprueba la forma (diapositiva 25)

```python
# De asistente/vision.py (recortado, como en la diapositiva)
class LineaTicket(BaseModel):
    sku: str | None              # None = no se lee
    cantidad: int | None
    importe: float | None

class Ticket(BaseModel):
    pedido_id: str | None
    fecha: date | None           # 2026-04-31 no pasa
    lineas: list[LineaTicket]
    total_impreso: float | None  # el impreso, aunque no cuadre
    campos_ilegibles: list[str]
    legibilidad_declarada: Literal["buena", "regular", "mala"]   # opinión, no probabilidad
```

| Lo que comprueba | Lo que NO comprueba | Lo que permite |
|---|---|---|
| ¿Es JSON? ¿Están los campos? ¿Tienen su tipo? ¿La fecha existe? | Que el pedido sea ese, que el total sea correcto o que la imagen diga eso | `null` y `campos_ilegibles`: decir «no lo leo» en vez de inventar |

> **Pydantic garantiza la forma. El contenido se comprueba después.**

### 5.2 Cómo obliga «format» a escribir JSON, y por qué no basta (diapositiva 26)

A Ollama se le puede pasar el esquema en el parámetro `format`. Mientras el modelo escribe, en cada paso solo
puede elegir tokens que mantengan el JSON válido. Ejemplo ilustrativo: tras `"total_impreso": ` el modelo propone
`231` (0,71), `211` (0,12), `"` (0,09), `Tot` (0,05), `}` (0,03). El esquema **prohíbe** `"`, `Tot` y `}` (romperían
el JSON), pero **231 y 211 son los dos «válidos»**: entre los números posibles, elige el modelo.

| Lo que garantiza | Lo que NO garantiza |
|---|---|
| La forma: llaves, comillas, campos y tipos. Siempre JSON válido | El valor. 231 o 211, ambos «válidos» |

Pedir JSON **en el prompt** es una petición; obligarlo **con un esquema** es una barrera (como el «solo SELECT» de
la sesión 1). Pero ni así se garantiza que el contenido sea verdad.

### 5.3 JSON válido no es contenido correcto: el ticket muy borroso (diapositiva 27)

[`02_validar.py`](./DropLab_sesion_3/practica/sesion_3/02_validar.py) (sin modelo, instantáneo) valida tres
extracciones. Lo he ejecutado:

| Ejemplo | Pydantic | El código |
|---|---|---|
| **A** · lo que leyó el VLM del ticket de abril | ✓ pasa | El ticket no cuadra consigo mismo: diferencia de 20,00 € |
| **B** · mal formado (importe en letra, fecha 2026-04-31, legibilidad «95 %») | ✗ 5 errores | — |
| **C** · bien formado… e **inventado** (el ticket muy borroso, real) | ✓ pasa | Pedido, fecha y líneas con formato imposible; no cuadra consigo mismo |

El caso C, campo a campo:

| Campo | En la imagen (real) | Lo que leyó |
|---|---|---|
| pedido_id | B-MAD-MAL-ORD-0005 | **8-MAD-MAL-000-0005** |
| fecha | 2026-04-04 | **2020-04-04** |
| línea 1 · importe | 117,27 | **126,13** |
| línea 2 · SKU | …_AZUL_40 | **…_AZUL_41** |
| legibilidad | — | **«buena»** |

Veredicto del código: **LECTURA DUDOSA** (repetir la foto o revisar a mano). Y el modelo dijo «buena»:
**su opinión no es una probabilidad**. (Las imágenes borrosas son **sintéticas**, hechas para practicar, y están
en `practica/sesion_3/imagenes_sinteticas/`.)

### 5.4 Comprobar con código: el ticket de abril, campo a campo (diapositiva 28)

`01_ver_imagen.py ticket_abril.png --guardada` (salida real del Jetson, sin modelo):

| Comprobación | En el ticket | Registro / cálculo | |
|---|---|---|---|
| Línea 1: cantidad × precio − descuento | 117,27 € | 117,27 € | ✓ |
| Línea 2: cantidad × precio − descuento | 94,72 € | 94,72 € | ✓ |
| **Total impreso = suma de sus líneas** | **231,99 €** | **211,99 €** | ✗ |
| Pedido | B-MAD-MAL-ORD-0005 | B-MAD-MAL-ORD-0005 | ✓ |
| Fecha | 2026-04-04 | 2026-04-04 | ✓ |
| Tienda | MAD-MAL | MAD-MAL | ✓ |
| **Total: impreso frente a caja** | **231,99 €** | **211,99 €** | ✗ |

**Veredicto: DISCREPANCIA de 20,00 €.** Coincide todo… menos el total impreso: 20 € más que sus líneas y que
caja. **El código lo dice; no dice por qué.** El veredicto y su explicación los escribe el código, no el modelo:

```python
# De asistente/vision.py, función _veredicto() (recortado)
if formato:                      # valores imposibles (pedido, fecha, línea…)
    veredicto = "lectura_dudosa"
elif n["no_coincide"]:
    veredicto = "discrepancia"
...
"discrepancia": "Hay {no_coincide} discrepancia(s) entre la imagen y los registros. Una discrepancia pide "
                "revisión: no indica por sí sola la causa ni un responsable.",
```

Detalle que añade el código: ese pedido tiene después **2 abonos** (12 y 13 de abril) que suman 211,99 €, y el
código avisa de que **no explican la diferencia del total** (se calculan sobre el importe de caja, no sobre el
impreso). El ticket de marzo (`ticket_marzo.png`), en cambio, **coincide** en las 11 comprobaciones.

> **Una discrepancia pide revisión: no demuestra fraude ni dice quién se equivocó.**

La misma lógica vale para las otras dos imágenes del caso: la **hoja de recuento** (`recuento_stock_0604.png`) se
compara con `disponibilidad.csv` en el mismo momento, y el **albarán** (`albaran_0604.png`) dice lo **previsto**,
que nunca se suma como recibido.

---

## 6. Bloque II · El segundo encargo: los PDF de junio

### 6.1 El encargo (diapositiva 29)

> «Necesito el cierre de junio: qué llegó, qué no y cuánto costó.»

Solo hay dos PDF, en [`data/documentos_junio/`](./DropLab_sesion_3/data/documentos_junio/). Los datos de ventas
acaban el 26/04, así que **de junio solo hay documentos**:

| Documento | Qué tiene | Por qué es difícil |
|---|---|---|
| **Informe de reposición** (`01_DropLab_informe_reposicion_junio.pdf`, LOG-2026-06 v1.1, aprobado) | 8 págs. digitales: tabla T1 de recepciones (sigue en la pág. siguiente), gráfico **G1** de líneas completas, decisiones, un **anexo con el borrador v0.9**, y la tabla T2 de expediciones | Tablas sin rejilla que saltan de página; un gráfico que es una **imagen**; un borrador dentro del documento aprobado |
| **Expediente escaneado** (`02_DropLab_expediente_escaneado.pdf`) | 3 págs. que son **solo imagen**: albarán A-0617-04, parte de incidencia INC-0617-02 y rectificación RC-0620-01 | No hay texto que extraer: hay que leer la imagen |

### 6.2 Antes: el lector de la sesión 2 con estos PDF (diapositiva 31)

`08_leer_documentos.py --antes` pasa los PDF por las reglas de `10_corpus.py` (pensadas para los PDF de abril):

| Qué | Lo que sale | Por qué |
|---|---|---|
| Código | «Uso interno» | Toma la primera línea con dos «\|»: aquí es el **pie** de página |
| Estado | «sin estado» (8 págs.) | El borrador v0.9 del anexo queda igual que el aprobado |
| Versiones | «sustituye a LOG-2026-06» | v0.9 y v1.1 tienen el **mismo código**: la versión no está en la clave |
| Gráfico G1 | no existe | Es una imagen: sus 12 porcentajes no están en el texto del PDF |
| Tabla T2 | fila huérfana en la pág. 8 | «tarde. La firma…» es el final de ENT-06-012, que empieza en la pág. 7 |
| Escaneado | `IndexError`: 0 palabras en la página | No hay texto que extraer |

> **Las reglas de un lector valen para un formato. Formato nuevo → reglas nuevas, y medirlas.**

---

## 7. Bloque II · Práctica 2: cuatro formas de leer una página

### 7.1 Medidas en el Jetson (diapositiva 32)

| Forma | Herramienta | Escaneado | Informe | Tablas | Gráfico | Confianza |
|---|---|---|---|---|---|---|
| Texto del PDF | pymupdf (CPU) | **nada** | 0,0 s | celda a celda | no | — |
| OCR clásico | PP-OCRv6 · GPU | 1,8 s | 2,0 s | **no: líneas sueltas** | rótulos sueltos | por línea (media 0,995) |
| Parser de documentos | PaddleOCR-VL-1.6 · GPU | 23,8 s | 34,1 s | **sí** | **sí: 12/12** | no |
| VLM general | qwen3-vl:8b · Ollama | 31,3 s* | 33,6 s* | sí | **se lo salta** | no |

Segundos por página con el modelo cargado (carga: ~10 s el OCR, 5–13 s PaddleOCR-VL). \* Una sola página. Sin GPU,
el mismo OCR: ~40 s/página.

> **Rápido y con confianza *o* con estructura. Y ninguno dice si ha leído *bien*: eso se comprueba.**

### 7.2 Por dentro: lo que PaddleOCR hace solo (diapositiva 33)

| Lector | Paso 1 | Paso 2 | Salida |
|---|---|---|---|
| **OCR clásico · PP-OCRv6** (~2 s/pág.; no sabe qué es una tabla) | Detector: una caja por línea | Reconocedor: caracteres, uno a uno | Líneas + confianza |
| **Parser · PaddleOCR-VL-1.6** (~25–35 s/pág.; el gráfico, como tabla de valores) | Maquetación: bloques (título, tabla, gráfico, pie…) | Un VLM de **0,9 B** lee cada bloque | Markdown; tablas en HTML |

Antes de llamarlo decidimos nosotros: página → imagen (150 ppp, con PyMuPDF); motor «transformers» (PyTorch +
CUDA) para que vaya en la GPU; gráficos activados (por defecto se quedan como imagen); conservar cabecera y pie
(por defecto los quita, y el pie lleva el código).

**Por qué va en la GPU del Jetson** (`requirements_ocr.txt` y pregunta 7 del test): el paquete PaddlePaddle para ARM
solo usa la CPU (~40 s por página, y en modo 30 W ni arranca). Desde PaddleOCR 3.5 los modelos pueden ejecutarse
con **PyTorch** (motor «transformers»), que en el Jetson sí usa la GPU: ~2 s el OCR.

### 7.3 La misma página: lo que devuelve cada lector (diapositiva 34)

El parte de incidencia escaneado (pág. 2), una tabla de cajas revisadas:

```text
PP-OCRv6 · salida cruda (confianza, línea)      PaddleOCR-VL · su tabla, en filas
1,00  Caja                                       | Caja | Pares revisados | Conformes | Cuarentena | Observación |
1,00  Pares revisados                            | 1 | 6 | 6 | 0 | Sin incidencia |
1,00  Conformes                                  | 2 | 6 | 6 | 0 | Sin incidencia |
1,00  Cuarentena                                 | 3 | 6 | 6 | 0 | Sin incidencia |
1,00  Observación                                | 4 | 6 | 0 | 6 | Humedad / embalaje |
1,00  1                                          | TOTAL | 24 | 18 | 6 | Revisión completa |
1,00  6
1,00  6   …
```

- **OCR: líneas sueltas.** Cada carácter, bien. Pero ¿qué columna es cada «6»? La tabla se ha perdido.
- **Parser: una tabla.** «Caja 4: 6 revisados, 0 conformes, 6 en cuarentena». Qué documento es, no lo sabe.

### 7.4 El gráfico: sus 12 valores solo están en la imagen (diapositiva 35)

G1 son 12 porcentajes (3 tiendas × 4 semanas). Malasaña cae al **68 %** la semana del 08 al 14 de junio.

| Lector | Qué entra | Aciertos |
|---|---|---|
| PaddleOCR-VL-1.6 | la página entera | 12/12 |
| qwen3-vl:8b | el gráfico recortado | 12/12 |
| qwen3-vl:4b | el gráfico recortado | 11/12 (lee **95** donde pone 96, siempre igual y sin dudar) |
| qwen3-vl:8b | la página entera | **0/12** (no lo transcribe: pone un enlace a una imagen que no existe) |

> **Leído no es comprobado:** la ficha marca esas cifras como **SIN COMPROBAR**.

### 7.5 Qué hace PaddleOCR solo y qué hacemos nosotros (diapositivas 36 y 37)

| 1 · Nosotros, antes | 2 · PaddleOCR, solo | 3 · Nuestro código, después | 4 · Negocio valida |
|---|---|---|---|
| Elegir lector, página → imagen, activar gráficos, conservar pie | Líneas con confianza (OCR) o bloques con tablas HTML (parser), **página a página** | Limpiar (HTML → filas; el pie, aparte), reglas (código + versión, estado, «sustituye a», fila partida), comprobar cifras con el texto del PDF, ficha + «sin revisar» | ¿«APROBADO» en la pág. 1 vale para todo? ¿Esas dos filas son la misma entrada? ¿Qué se acepta sin revisar? |

> **PaddleOCR lee. Limpiar, poner la ficha y comprobar es nuestro código; que esas reglas sean ciertas, lo valida negocio.**

Dos reglas nuestras, en [`asistente/lectura.py`](./DropLab_sesion_3/practica/sesion_3/asistente/lectura.py):

- **Tabla partida.** PaddleOCR-VL lee página a página, así que la cola de una fila que sigue en la página siguiente
  sale como una fila **sin registro**. Regla: *una fila sin registro al principio de una página es la cola de la
  última fila de la anterior: se pega ahí*. La da el propio informe en su nota (1): «Las casillas vacías en una
  continuación pertenecen a la misma observación iniciada en la página anterior».
- **Versiones.** La versión entra en la **clave**: `LOG-2026-06 v1.1` (aprobado, págs. 1–5 y 7–8) y
  `LOG-2026-06 v0.9` (**sustituido**, pág. 6, el anexo), porque la pág. 1 dice «sustituye a LOG-2026-06 v0.9».

```python
# De asistente/lectura.py
SUSTITUYE = re.compile(r"sustituye a (?P<codigo>[A-Z]{3}-\d{4}-\d{2}) (?P<version>v\d+\.\d+)", re.I)
```

Compárala con la regla de la sesión 2 (`sustituye a ([A-Z0-9-]+)`): solo miraba el código, y aquí los dos documentos
tienen el mismo. Es la pregunta 12 del test.

### 7.6 Después: cada página, con su ficha y cómo se leyó (diapositiva 38)

[`09_indice_junio.py`](./DropLab_sesion_3/practica/sesion_3/09_indice_junio.py) crea el **índice ampliado**: los 51
fragmentos de la sesión 2 (mismos id) + **11 páginas de junio** = **62 fragmentos**. Cada página lleva un campo
nuevo, **`lectura`**: con qué se leyó, «sin revisar», y cuántas cifras se pudieron comprobar con el texto del PDF.

| id | Documento · pág. | Código | Estado | Lectura (PaddleOCR-VL, sin revisar) |
|---|---|---|---|---|
| 51–55, 57–58 | informe · 1–5, 7–8 | LOG-2026-06 v1.1 | aprobado | valores = texto del PDF (pág. 4: 14 valores **solo en la imagen**) |
| **56** | informe · 6 (anexo) | **LOG-2026-06 v0.9** | **sustituido → v1.1** | 18/18 valores = texto del PDF |
| 59 | escaneado · 1 | A-0617-04 | registro | escaneada: **SIN COMPROBAR** |
| 60 | escaneado · 2 | INC-0617-02 | abierta (pendiente) | escaneada: **SIN COMPROBAR** |
| 61 | escaneado · 3 | RC-0620-01 | aprobado | escaneada: **SIN COMPROBAR** |

`09_indice_junio.py --ver 56` enseña de dónde sale cada campo de la ficha del anexo (lo he ejecutado): el código y el
estado salen de la línea de la propia página «LOG-2026-06 v0.9 | 01/07/2026 | BORRADOR», y el código lo convierte en
**SUSTITUIDO** por la frase de la pág. 1; el responsable no lo dice la página, se toma el de la pág. 1.

Cuidado con dos cosas:

- Una cifra que coincide con el texto del PDF dice que **se leyó igual que lo que hay escrito**, no que lo escrito
  sea verdad.
- En el escaneado no hay texto con el que comparar: **nada se puede comprobar automáticamente**.

**Tres ideas del bloque II:** un modelo lee, el código comprueba (ticket frente a caja; cifras leídas frente al texto
del PDF) · PaddleOCR lee, la ficha y las reglas son nuestras (y negocio las valida) · lo que no se ha podido
comprobar, se dice («leído por PaddleOCR-VL, sin revisar» viaja en la ficha hasta la respuesta).

---

## 8. Bloque III · La arquitectura: quién es quién

### 8.1 El viaje de una pregunta (diapositiva 41)

```
Navegador  →  Open WebUI   →  Pipe               →  API FastAPI        →  Flujo LangGraph
pregunta      Docker :3000    «DropLab Analista»    :8000 · contrato       planificar → … →
+ imagen      la interfaz     adaptador             OpenAPI                redactar → verificar
                                                                              │
                         ┌──────────────────────┬────────────────────────┬────┴─────────────────┐
                         ▼                      ▼                        ▼                      ▼
                       visión                 cifras                 documentos              redactar
                       vision.py → Ollama     datos.py → DuckDB      documentos.py → DuckDB  Ollama
                       qwen3-vl:8b-instruct   capa semántica         + bge-m3 (Ollama)       qwen3:30b-a3b
```

> **Open WebUI es la interfaz; Ollama ejecuta modelos; DuckDB guarda datos e índice; FastAPI expone operaciones;
> LangGraph organiza el proceso.**

La idea central de la [guía de integración](./guia_integracion.html) del profesor: **no hay nada nuevo por dentro**.
Son las funciones de Python de las sesiones 1 y 2 (incluso se importan tal cual, en `asistente/sesion2.py`). Lo
nuevo son tres piezas que las conectan: **LangGraph** las ejecuta en orden, **FastAPI** las pone detrás de una
dirección web y **Open WebUI** es la ventana. Y desde la terminal, `05_flujo.py` entra directamente en el flujo,
sin API ni Open WebUI: por eso todo se puede probar en la terminal.

**Docker y la red:** Open WebUI corre en un contenedor con `--network=host`, para que «127.0.0.1» dentro del
contenedor sea el Jetson (y vea Ollama y la API). Sin eso, sería el propio contenedor y no vería nada.

### 8.2 Cinco palabras, con DropLab (diapositiva 42)

| Palabra | Qué es | En DropLab |
|---|---|---|
| **Backend** | El programa que procesa las peticiones | La API (FastAPI) y el flujo, en el Jetson |
| **API** | La forma acordada de pedirle operaciones | HTTP + JSON en `http://<jetson>:8000` |
| **Endpoint** | Una dirección para una operación concreta | `POST /tickets/comprobar` · `GET /salud` |
| **Petición / respuesta** | Lo que entra y lo que sale | `{pregunta, imagen_base64}` → `{respuesta, evidencias, errores}` |
| **OpenAPI** | La descripción del contrato, legible por máquinas | `/openapi.json` · `/docs` (con «Try it out») |

> **Un contrato claro permite cambiar la interfaz (o el modelo) sin tocar lo demás.**

### 8.3 Todo lo que se puede cambiar, en un sitio

[`asistente/config.py`](./DropLab_sesion_3/practica/sesion_3/asistente/config.py) reúne modelos y direcciones, y
se cambian con **variables de entorno**, sin tocar el código:

```python
# De asistente/config.py
OLLAMA_URL = os.environ.get("DROPLAB_OLLAMA", "http://127.0.0.1:11434").rstrip("/")
MODELO_TEXTO = os.environ.get("DROPLAB_MODELO_TEXTO", "qwen3:30b-a3b-instruct-2507-q4_K_M")
MODELO_VISION = os.environ.get("DROPLAB_MODELO_VISION", "qwen3-vl:8b-instruct")
API_URL = os.environ.get("DROPLAB_API", "http://127.0.0.1:8000").rstrip("/")
```

Un detalle medido que también vive ahí: **un solo `num_ctx` por modelo** (`CTX_TEXTO = 12288`). Si una llamada pide
otro tamaño de contexto, Ollama **recarga el modelo**: planificar con 2.048 y redactar con 12.288 costaba ~25 s de
recarga en cada pregunta.

Todas las llamadas a modelos pasan por una sola función, `chat()` de
[`asistente/ollama.py`](./DropLab_sesion_3/practica/sesion_3/asistente/ollama.py): la petición a `/api/chat` de la
sesión 1, con `format` (esquema JSON) opcional, que devuelve tokens y tiempos y, si algo falla, un
**`ErrorComponente`** con código y pieza (`OLLAMA_NO_DISPONIBLE`, `MODELO_NO_INSTALADO`…). Ese error llega tal cual
hasta el navegador.

---

## 9. Bloque III · La API: un contrato y errores con nombre

[`asistente/api.py`](./DropLab_sesion_3/practica/sesion_3/asistente/api.py), arrancada con `03_api.py`
(diapositiva 44):

| Método y dirección | Qué hace | ¿Modelo? | Tiempo |
|---|---|---|---|
| `GET /salud` | Estado de Ollama, índice, datos y modelos | no | < 1 s |
| `POST /documentos/buscar` | Fragmentos del RAG (sesión 2 + junio) | solo embeddings | < 1 s |
| `POST /datos/consulta` | Una consulta **fija** con parámetros validados | no | < 1 s |
| `POST /tickets/comprobar` | Imagen (multipart) → extraer, validar, consultar, comparar | VLM | ~11–25 s |
| `POST /analizar` | Pregunta (+ imagen) → el flujo completo | VLM + texto | ~8–30 s |
| `POST /analizar/stream` | Igual, enviando cada paso al terminar | VLM + texto | igual |

Cada operación son dos o tres líneas que llaman a funciones que ya existían. Lo que entra lo define una clase
Pydantic (el **contrato**), y FastAPI rechaza solo lo que no lo cumple:

```python
# De asistente/api.py
class PeticionBuscar(BaseModel):
    model_config = ConfigDict(extra="forbid")          # un campo que no existe es un error, no se ignora
    pregunta: str = Field(min_length=3, examples=["¿Qué semana de junio tuvo el peor porcentaje…?"])
    k: int = Field(5, ge=1, le=10)
    modo: Literal["semantica", "palabras", "hibrida"] = "hibrida"

@app.post("/documentos/buscar", response_model=RespuestaBuscar, summary="Buscar en los documentos (RAG: sesión 2 + PDF de junio)")
def buscar_documentos(p: PeticionBuscar):
    t0 = time.time()
    frags = documentos.buscar(p.pregunta, k=p.k, modo=p.modo)
    return {"fragmentos": frags, "segundos": round(time.time() - t0, 2), "errores": []}
```

`/docs` lo genera FastAPI a partir de este código (pregunta 5 del test): operaciones, campos y ejemplos, con «Try it
out» para probarlas. Los errores tienen **siempre la misma forma** `{codigo, componente, mensaje}`: **4xx** si la
petición está mal, **503** si falla una pieza (Ollama, el índice…).

### Un error que se explica: la inyección de SQL

```bash
python practica/sesion_3/04_cliente_api.py consulta --pedido "1; DROP TABLE ventas"
```
```json
{"errores": [{"codigo": "PARAMETRO_NO_VALIDO", "componente": "datos",
              "mensaje": "Formato de pedido no válido: '1; DROP TABLE ventas'"}]}      ← HTTP 422
```

La base no se toca, por dos barreras **en el código** (pregunta 6 del test): el SQL lo escribimos nosotros y el valor
va aparte, como **parámetro** (el `?`), nunca pegado dentro del texto de la consulta; y antes se comprueba su
formato con una expresión regular:

```python
# De asistente/datos.py, función pedido()
if not PEDIDO_RE.fullmatch(pedido_id):
    raise ErrorComponente("PARAMETRO_NO_VALIDO", "datos", f"Formato de pedido no válido: {pedido_id!r}")
lineas = _ejecutar("pedido", f"Líneas del pedido {pedido_id} en caja", """
    SELECT linea_id, ... FROM ventas_lineas WHERE pedido_id = ? ORDER BY linea_id""", [pedido_id])
```

Las consultas fijas de [`asistente/datos.py`](./DropLab_sesion_3/practica/sesion_3/asistente/datos.py) son cuatro:
`pedido`, `resumen_tienda` (cifras clave por periodo, **con la diferencia B − A calculada en el SQL**),
`disponibilidad_en` y `roturas_dia`. Para lo que no cabe en ellas queda el SQL del modelo de la sesión 2 (capa
semántica + barreras + verificador).

---

## 10. Bloque III · El flujo con LangGraph

### 10.1 LangChain, LangGraph y tres palabras (diapositiva 45)

| | Qué es | Hoy |
|---|---|---|
| **LangChain** | Componentes e integraciones: clientes de modelos, cargadores, divisores, recuperadores | No: ya tenemos los nuestros (sesión 2) |
| **LangGraph** | Organiza un proceso: pasos, transiciones y estado | Sí: el flujo del asistente |

| Palabra | Qué es | Ejemplo |
|---|---|---|
| **Nodo** | Una función del proceso | `leer_imagen(estado)` → lo que cambia |
| **Estado** | Lo que el proceso conserva entre nodos | pregunta, imagen, consultas, fragmentos… |
| **Enrutamiento** | Elegir el siguiente paso | `enrutar(estado)` → «consultar_datos» |

> **Un grafo con estado es un diagrama que se ejecuta: se puede dibujar, seguir y medir.**

### 10.2 Siete nodos y dos decisiones (diapositiva 46)

```
planificar ──► (enrutar) ──► leer_imagen ─────┐
  modelo         ▲  │        VLM+Pydantic+caja │   cada tarea vuelve a «enrutar»,
  propone,       │  ├──► consultar_datos ──────┤   que elige la siguiente pendiente
  código valida  │  │     SQL con parámetros   │
                 │  └──► buscar_documentos ────┤
                 └─────── RAG sesión 2+junio ──┘
                    │
                    └──► contrastar ──► redactar ──► verificar ──► FIN
                         (código)       (modelo:      (código)  │
                                        [S#][D#][V#])  ▲        │
                                                       └────────┘ 1 reintento si falla
```

`05_flujo.py --dibujar` saca el mismo grafo en Mermaid (lo he ejecutado): flechas continuas = siempre; discontinuas
= las elige una función de enrutamiento. Montarlo con LangGraph es poco código:

```python
# De asistente/flujo.py
def construir():
    g = StateGraph(Estado)
    for nombre, f in (("planificar", planificar), ("leer_imagen", leer_imagen), ("consultar_datos", consultar_datos),
                      ("buscar_documentos", buscar_documentos), ("contrastar", contrastar), ("redactar", redactar),
                      ("verificar", verificar)):
        g.add_node(nombre, f)
    destinos = ["leer_imagen", "consultar_datos", "buscar_documentos", "contrastar"]
    g.add_edge(START, "planificar")
    g.add_conditional_edges("planificar", enrutar, destinos)
    for n in ("leer_imagen", "consultar_datos", "buscar_documentos"):
        g.add_conditional_edges(n, enrutar, destinos)
    g.add_edge("contrastar", "redactar")
    g.add_edge("redactar", "verificar")
    g.add_conditional_edges("verificar", tras_verificar, ["redactar", END])
    return g.compile()
```

`enrutar` **no es un modelo**: es una función de cinco líneas que devuelve la siguiente tarea pendiente del plan, en
orden fijo (imagen → cifras → documentos), y «contrastar» cuando no queda ninguna.

### 10.3 El plan: el modelo solo marca casillas

```python
# De asistente/flujo.py
class Plan(BaseModel):
    """Lo que el modelo puede proponer. Cualquier otra cosa no pasa la validación."""
    tareas: list[Literal["imagen", "cifras", "documentos"]] = Field(description="Qué hace falta para responder")
    tienda: Literal["MAD-MAL", "MAD-GOY", "BCN-EIX"] | None = Field(None, description="Tienda de la que se pregunta")
    consulta: Literal["resumen_tienda", "pedido", "sql_libre", "ninguna"] = Field("ninguna", ...)
    motivo: str = Field("", description="Una frase corta (15 palabras como mucho): por qué")
```

Diferencia con la sesión 1: allí el modelo tenía un menú de herramientas (*tools*) y decidía cuándo llamarlas. Aquí
**solo marca casillas** en un plan con opciones cerradas (`Literal`), y es **el código** quien llama a cada función,
en orden. Menos libertad para el modelo, más control. Además el código **corrige** el plan (pregunta 9 del test):
si hay imagen, se lee aunque el plan no lo diga; si la pregunta trae un número de pedido, se consulta; si es de
**junio**, nada de cifras de ventas (los datos acaban el 26/04: solo documentos); y si el plan no pasa la
validación, se usan **reglas** de palabras clave (`plan_por_reglas`).

### 10.4 Quién decide qué: el modelo propone, el código dispone (diapositiva 47)

| Paso | Modelo | Código |
|---|---|---|
| Planificar | Propone tareas, tienda y tipo de consulta (JSON con esquema) | Valida con Pydantic; corrige (imagen, pedido, junio → sin SQL); si falla, reglas |
| Leer la imagen | VLM: extrae campos con esquema | Valida, comprueba formato y cuentas, consulta caja, decide el veredicto |
| Cifras | — (o SQL del modelo, solo SELECT y sobre la capa semántica) | Consultas fijas con parámetros; las diferencias, en SQL |
| Documentos | bge-m3: la pregunta → vector | Búsqueda híbrida; versiones (S2) y versión en la clave (junio) |
| Contrastar | — | Versiones, fuentes automáticas (Whisper, PaddleOCR-VL), ticket ↔ Pack 4, límites |
| Redactar | Escribe con `[S#] [D#] [V#]` | Numera las evidencias y fija los apartados |
| Verificar | — | Citas, cifras, versiones, culpa y causa; 1 reintento |

> **Libertad para el modelo donde aporta (entender, leer, redactar); garantías del código en el resto.**

### 10.5 Contrastar: el código compara fuentes antes de redactar (diapositiva 48)

| Comprobación | Fuente | Ejemplo |
|---|---|---|
| **Versiones** | documentos | Expediente pág. 7 SUSTITUIDO por CAM-2026-03-FINAL: solo antecedente |
| **Fuentes automáticas** | documentos | La llamada es Whisper: testimonio. Los PDF de junio, PaddleOCR-VL: «sin revisar» |
| **Ticket ↔ Pack 4** | imagen + documentos | 04/04 · 2 unidades → no elegible. 16/03 · 4 unidades → elegible (el regalo, no consta) |
| **Límites** | la pregunta | Coincidir en el tiempo no prueba una causa. Faltan visitas, regalos entregados, demanda |

> **El modelo recibe las comprobaciones ya hechas: las repite, no las decide.**

### 10.6 Redactar y verificar

El código numera las evidencias (`S#` consultas, `D#` documentos, `V#` la imagen) y le pide al modelo unos apartados
fijos (**Respuesta**, **Cifras**, **Documentos y llamada**, **Imagen**, **Límites**). Después,
`verificar()` revisa la redacción **con reglas de Python, sin IA**:

- que cada cita `[S#] [D#] [V#]` exista;
- que cada cifra esté en **alguna** evidencia (el mismo `cifras_sin_respaldo()` de la sesión 2);
- que si cita un documento sustituido, diga que es un borrador;
- que no atribuya **culpa o fraude** ni afirme una **causa** sin presentarla como hipótesis (expresiones regulares
  que ignoran las frases negadas: «no demuestra fraude» está bien).

Si falla en lo grave (cifras o citas), **un reintento**; después, fin con avisos. Ojo a la limitación (pregunta 15 del
test y mejora (b) del ejercicio 4): comprueba que la cifra esté en **alguna** evidencia, **no en la que se cita**.

### 10.7 La traza: lo que hizo el sistema, con tiempos (diapositiva 49)

`05_flujo.py --caso combinada --guardada` (salida real del Jetson, sin modelos; la he ejecutado):

| Nodo | Herramienta | Detalle | s |
|---|---|---|---|
| planificar | plan por modelo | imagen → cifras → documentos | 1,1 |
| leer_imagen | VLM + Pydantic + SQL | ticket · qwen3-vl:8b-instruct · JSON válido · discrepancia · lectura reutilizada | 0,1 |
| consultar_datos | DuckDB · capa semántica | `resumen_tienda(MAD-MAL)` | 0,0 |
| buscar_documentos | RAG · bge-m3 · índice ampliado | 1 búsqueda → 5 fragmentos | 0,0 |
| contrastar | código | 3 comprobaciones · 2 límites | 0,0 |
| redactar | qwen3:30b-a3b | 3.759 tokens de entrada · 509 de salida · 33,5 tok/s | 19,7 |
| verificar | código | limpia | 0,0 |

21 s en total. Casi todo el tiempo es **redactar**. («Lectura reutilizada»: la misma imagen ya se había leído y se
reutiliza por su huella sha256.)

> **La traza es lo que se puede auditar:** pasos, herramientas, fuentes y tiempos; **no** el «razonamiento» del modelo.

### 10.8 Sin framework: el mismo proceso con un bucle

[`asistente/flujo_simple.py`](./DropLab_sesion_3/practica/sesion_3/asistente/flujo_simple.py) hace lo mismo con un
`while` y unos `if` (`05_flujo.py --sin-framework`) y da el mismo resultado. ¿Qué aporta entonces LangGraph
(pregunta 10 del test)? Pasos y conexiones **declarados** que se pueden dibujar, un estado con tipos que mezcla solo
la traza y los errores, el progreso paso a paso y, si el proceso crece, **pausas para aprobación humana**, reanudar
a medias o ejecutar en paralelo. Para siete pasos, las dos versiones son igual de válidas.

**Tres ideas del bloque III:** la lógica no se mueve, la API y la interfaz traducen (el mismo código en la terminal, en
`/docs` y en Open WebUI) · el modelo propone, el código valida y comprueba · la traza es lo que se puede auditar.

---

## 11. Bloque III · Open WebUI y la Pipe

**Open WebUI** es una interfaz de chat que no sabe nada de DropLab. Una **Pipe** es una clase de Python que Open WebUI
trata como un «modelo» más del selector («DropLab Analista»): cuando escribes, Open WebUI la llama. La nuestra,
[`openwebui/droplab_pipe.py`](./DropLab_sesion_3/practica/sesion_3/openwebui/droplab_pipe.py), **no calcula, no busca
y no llama a Ollama**: saca la pregunta y la imagen, llama a `POST /analizar/stream` y convierte la respuesta en
Markdown (con desplegables de comprobaciones, fuentes y traza). Es la pregunta 8 del test.

Tres detalles que explica el código:

- Usa **`httpx` asíncrono**: con una llamada que bloquea (`requests`), Open WebUI se quedaba congelado para todos los
  usuarios mientras esperaba.
- La imagen llega dentro del último mensaje como `data:image/png;base64,…` (lo comprobaron con una «sonda»,
  `openwebui/sonda_pipe.py`).
- Si la API no responde, devuelve un error con nombre: **`API_NO_DISPONIBLE`** (extra de clase: Ctrl+C en la API y
  preguntar).

Open WebUI va en Docker (`openwebui/arrancar_openwebui.sh`) con `WEBUI_AUTH=False` (sin usuarios: **solo para el aula**)
y **sin RAG propio**: no se le suben documentos, así no hay un segundo RAG que trocee distinto o se salte la regla de
versiones. La Pipe se instala con `openwebui/instalar_pipe.py`. Su licencia no es MIT: BSD-3 con una cláusula de marca.

> **La interfaz, lo más fina posible.** Si mañana se cambia Open WebUI por Teams, Slack o una web propia, solo cambia
> este adaptador.

---

## 12. Bloque IV · El asistente, en directo

### 12.1 Siete preguntas difíciles, y dónde está la trampa (diapositiva 52)

| # | Tipo | Pregunta | La trampa | Caso en `05_flujo.py` |
|---|---|---|---|---|
| 1 | Versiones | ¿Hasta qué día estuvo vigente el Pack 4 en Malasaña? | Lo más parecido es el borrador: decía 31/03 | `documental` |
| 2 | Un ticket | ¿Qué demuestra este ticket? Compáralo con caja. (+ `ticket_abril.png`) | Se lee perfecto… y no cuadra con caja | `visual` |
| 3 | Una causa | ¿La rotura de stock del 6 de abril es la causa de la caída de Malasaña? | Pide una causa que los datos no prueban | `causal` |
| 4 | Junio · gráfico | ¿Qué semana de junio tuvo el peor % de líneas completas en Malasaña? ¿Fue por la caja húmeda del albarán A-0617-04? | El dato está en una imagen, y la caja llegó después | `junio_grafico` |
| 5 | Junio · escaneado | ¿Cuántos pares del albarán A-0617-04 se aceptaron al final y qué pasó con el resto? | Solo imagen: nadie lo ha leído a mano | `junio_escaneado` |
| 6 | Lo que no consta | ¿Cuántas tote bags se entregaron en marzo y cuántas ventas se perdieron por las obras? | Invita a inventar dos cifras | `insuficiente` |
| 7 | Una errata | ¿La campaña de junio aumentó las ventas de Street One? | En junio no hay ninguna campaña | `extra_campana` |

Antes de lanzar cada una, entre todos: **¿qué debería contestar y en qué documento, consulta o imagen estará?**
Después se lanza en Open WebUI (8–30 s), se abre lo que hay debajo (comprobaciones, fuentes, traza) y se lee la
fuente citada.

### 12.2 Cómo leer una respuesta: cuatro preguntas (diapositiva 54)

| Pregunta | Qué mirar | Ejemplo (pregunta 4) |
|---|---|---|
| **¿Es correcta?** | ¿Las cifras y fechas son las de la fuente vigente, no las del borrador? | 68 %, semana 08–14 |
| **¿La respaldan las fuentes?** | Abrid la cita: ¿dice exactamente eso? ¿Viene a cuento? | [D2] = informe, pág. 4 |
| **¿Dice lo que no sabe?** | ¿Separa hecho de hipótesis? ¿Evita causas y culpas sin pruebas? | «coincidir no prueba la causa» |
| **¿Se ve qué hizo?** | ¿Qué consultó, qué leyó y cómo («sin revisar»)? ¿Cuánto tardó? | «PaddleOCR-VL, sin revisar» |

> **Si las cuatro son sí, la firmaríamos. Si alguna es no, se dice antes de mandarla.**

La pregunta 4 (diapositiva 55) muestra cómo debe razonarse: la peor semana fue la 08–14 con un 68 % [D2]; la caja
húmeda se registró el 18/06, **después** de esa semana, así que no la explica; y además el gráfico describe
incidencias, no prueba causas (es la pregunta 14 del test).

### 12.3 Lo que comprueba el código y lo que miráis vosotros (diapositiva 56)

| Lo comprueba el código, siempre | Lo tenéis que mirar vosotros |
|---|---|
| ✓ Que cada cita `[S#] [D#] [V#]` existe | ? Que la cita dice exactamente eso |
| ✓ Que cada cifra está en alguna evidencia | ? Que la cita viene a cuento |
| ✓ Que un borrador no pasa por vigente | ? Que la página con el dato llegó a la búsqueda |
| ✓ Que no afirma culpas ni causas sin decirlo | ? Que la cifra es de la fila correcta |
| ✓ Que avisa de lo leído por OCR o por Whisper | ? Que la conclusión tiene sentido para el negocio |

> **«Verificación limpia» = ha pasado nuestras reglas. Que sea verdad, lo dice quien abre la fuente.**

---

## 13. Extras: medir por piezas y una respuesta convincente y falsa

### 13.1 Una respuesta convincente… y falsa: ¿qué pieza ha fallado? (diapositiva 61)

Caso `extra_falla`: «¿Cuántos pares de STREET_ONE_ARENA_41 aceptó Goya en junio y cuándo llegó la última entrega?»

| Lo que dijo el asistente (verificación limpia) | Lo que dicen los PDF |
|---|---|
| «MAD-GOY aceptó **60** pares de STREET_ONE_ARENA_41 en junio. La última entrega llegó el 30/06/2026.» | **40** pares: T1 sigue en la pág. 3 (MAD-GOY · ARENA_41 · 40/40/40). Última entrega: ENT-06-012, 30/06 a las 18:20: la fila partida entre la pág. 7 y la 8 |

| Pieza | Diagnóstico |
|---|---|
| **Recuperación · aquí** | La pág. 3 no está entre los 8 primeros fragmentos. Llega la pág. 2 |
| Redacción · hereda | Coge la fila más parecida que sí tiene: NEGRO_41 |
| Verificación · no lo ve | El 60 existe en las evidencias (en otra fila): limpia |

> **La tabla partida, otra vez: si la página que tiene el dato no llega, el modelo rellena.**

Es el punto de partida de la mejora (a) del ejercicio 4 de la entrega.

### 13.2 Una errata del documento: «la campaña» de junio (diapositiva 62)

La pág. 4 del informe dice: «…Una mejora de la curva tampoco acredita que **la campaña** incrementara las ventas»,
pero **en junio no hay campaña**. El asistente respondió bien: «No se puede afirmar que la campaña de junio aumentó las
ventas de Street One. No hay datos de ventas de junio en las evidencias…».

> **Los documentos también se equivocan: una fuente es una evidencia, no la verdad.**

### 13.3 Medido: el asistente, pieza a pieza (diapositiva 63)

[`06_evaluar.py`](./DropLab_sesion_3/practica/sesion_3/06_evaluar.py) usa
[`examen/examen_sesion_3.json`](./DropLab_sesion_3/practica/sesion_3/examen/examen_sesion_3.json), con una parte por
pieza, para que un fallo diga **dónde** está:

| Pieza | Qué mide | 30B + VL 8B | 4B + VL 4B | Tiempo por prueba |
|---|---|---|---|---|
| Lectura visual | Campos extraídos frente a la imagen (L1–L6) | 6/6 imágenes | 6/6 | 56,2 s |
| Recuperación | Fuente esperada entre los 5 primeros, sin modelo de texto (B1–B6) | 6/6 preguntas | 6/6 | 0,1 s |
| Consulta y cálculo | Consultas fijas frente a la cifra a mano (C1–C4) | 11/11 cifras | 11/11 | 0,5 s |
| Interpretación | Hechos que debe tener y lo que NO debe afirmar (R1–R7) | 7/7 preguntas | **6/7** | 57,2 s |
| Integración | Errores con nombre: API caída, Ollama caído, imagen mala… | 10/10 pruebas | 10/10 | 0,3 s |

> **Si una pieza falla con todos los modelos, el problema no es el modelo: es el dato, el índice o el código.**

(Pregunta 13 del test: si falla la recuperación, se revisa el índice, el troceado, los embeddings o la búsqueda; esa
parte no usa el modelo de texto.)

### 13.4 Dos configuraciones locales (diapositiva 64)

[`07_comparar.py`](./DropLab_sesion_3/practica/sesion_3/07_comparar.py) (resultados guardados, lo he ejecutado):

| Medida | A · Jetson (30B + VL 8B) | B · Portátil (4B + VL 4B) |
|---|---|---|
| Imágenes reales bien leídas | 4/4 · 38/38 campos | 4/4 · 38/38 campos |
| Imagen ilegible (sintética) | detectada · lectura_dudosa | detectada · JSON no válido |
| Respuestas correctas · verificación limpia | 7/7 · 7/7 | **6/7** · 7/7 |
| s por imagen · s por pregunta (cargado) | 56 s · 57 s | 50 s · 46 s |
| Carga (una vez): texto · visión | 19 s · 10 s | 6 s · 7 s |
| Memoria: texto + visión | 19,8 + 6,5 GB | 4,5 + 4,2 GB |

- **Casi empatan: el código hace lo difícil.** Cifras, comparaciones y un plan con opciones cerradas. Con SQL libre
  (sesión 2) la distancia era 91 % frente a 67 %.
- **Leer desempata.** B omite el 108 → 7 en la combinada y dice que la tienda «abrió después» (siguió abierta).
  Ningún verificador lo ve.

---

## 14. Cierre: hacia producción y lo que nos llevamos

### 14.1 Para usarlo de verdad (diapositiva 58 y guía de integración)

| Tema | Qué falta | Una forma de empezar |
|---|---|---|
| **Calidad medida** | Un banco de preguntas reales con respuesta revisada, que crezca con el uso | Ampliar `practica/sesion_3/examen/` y pasar `06_evaluar.py` antes de cada cambio |
| **Verificar mejor** | Hoy una cifra vale si está en *alguna* evidencia; debería estar en la que se cita | Cambiar `verificar()` en `flujo.py` y medirlo con las salidas guardadas |
| **Revisión humana** | Lo «sin revisar» (OCR, Whisper) debería pasar por una persona antes de decidir | Una cola de revisión: la ficha pasa a «revisado por…», con quién y cuándo |
| **Documentos al día** | Hoy se cargan a mano | Una carpeta vigilada que lea, ponga ficha e indexe; versiones desde el gestor documental |
| **Seguridad** | Open WebUI sin usuarios (`WEBUI_AUTH=False`) | Usuarios y permisos; cada uno ve solo lo suyo; la API, con autenticación |
| **Registro** | La traza se ve, pero no se guarda | Guardar cada pregunta, traza, fuentes y quién la hizo (JSONL) |
| **Operación** | Ollama atiende de una en una; si cae, nadie se entera | Cola de peticiones, alertas, tiempos medidos |
| **Despliegue** | Se arranca a mano en una terminal | Contenedores con versiones fijas, configuración fuera del código, pruebas automáticas |
| **Modelos** | Elegidos con pocas pruebas | Repetir `07_comparar.py` con vuestras preguntas; revisar la licencia |

> **Las piezas ya están. Llevarlo a producción es medir, proteger y operar.**

### 14.2 Lo que nos llevamos de las tres sesiones (diapositiva 59)

1. **El código calcula; el modelo lee, entiende y redacta.** La regla de oro de la sesión 1 sigue igual con voz,
   documentos e imágenes.
2. **El negocio, los metadatos y las comprobaciones, en el código.** Capa semántica, fichas con versión,
   verificadores y contrastes.
3. **Leer no es comprobar; citar no es demostrar.** Lo que no se ha podido comprobar, se dice: «sin revisar», «no consta».
4. **Todo en local: los datos no salen de DropLab.** Un Jetson, modelos de pesos abiertos, PaddleOCR y una interfaz web.

### 14.3 La receta para vuestra propia integración (guía de integración)

1. Funciones que hacen una cosa y se prueban solas, sin modelo.
2. Una función para hablar con el modelo, con tiempos y errores con nombre.
3. Esquemas Pydantic para todo lo que entra y sale de un modelo.
4. El proceso: primero funciones y un bucle; LangGraph cuando crezca.
5. Comprobaciones en código después del modelo; lo que no se puede comprobar, se dice.
6. Una API con FastAPI que solo valida y llama a vuestras funciones (`/docs` sale gratis).
7. Una interfaz como adaptador fino de la API.
8. Medir por piezas: así sabéis **dónde** falla, no solo **si** falla.

---

## 15. La entrega final, explicada

Documento: [`Enunciado - ejercicios propuestos.pdf`](./Enunciado%20-%20ejercicios%20propuestos.pdf) (las diapositivas y
la guía del alumno lo llaman `Deberes_sesion_3.docx`). **Una sola entrega, individual**, que junta los ejercicios 3 y
4 de la sesión 2 (los del RAG) y los de la sesión 3: cuatro ejercicios (~3 horas) y un quinto opcional. Como siempre,
el profesor no da los comandos; el punto de partida es [`guia_alumno.md`](./DropLab_sesion_3/alumnos/sesion_3/guia_alumno.md),
el principio de cada script y su `--help`. Pide abrir **una vez** la [guía de integración](./guia_integracion.html)
(~10 minutos).

> Esta guía explica *qué se pide y cómo pensarlo*; no resuelve la entrega por ti.

### Antes de empezar: tres avisos prácticos (comprobados)

1. **La carpeta `DropLab_sesion_3` está en solo lectura** (los directorios, no los archivos). Lo he comprobado: no
   se puede crear ningún archivo nuevo. Fallarán `11_indice.py` (borra y recrea el índice), `09_indice_junio.py`
   (crea el índice ampliado), `01_ver_imagen.py` en directo (guarda la lectura en `salidas_guardadas/cache_vision/`)
   y cualquier índice de otro modelo de embeddings. Antes de los ejercicios 1 y 4 hay que dar permiso de escritura:
   ```bash
   chmod -R u+w ~/ebis/07_llm_open_source/clase_03/DropLab_sesion_3
   ```
   Lo que funciona con `--guardada` o solo lee (02, 05, 06, 07, 08 `--comparar`, 09 `--ver`) va bien sin tocar nada.
2. **Modelos:** el enunciado dice cómo elegirlos. Scripts de la sesión 2 (13, 14 y 15): `--llm qwen3:4b-instruct`.
   Scripts de la sesión 3: variables de entorno
   `export DROPLAB_MODELO_TEXTO=qwen3:4b-instruct DROPLAB_MODELO_VISION=qwen3-vl:4b-instruct`. Siempre hace falta
   `bge-m3`. Con 8 GB o menos, los scripts 01, 05 y 08 de la sesión 3 tienen `--guardada`.
3. **PaddleOCR no hace falta** (`requirements_ocr.txt` es opcional y va en otro entorno): las lecturas de junio hechas
   en el Jetson ya vienen guardadas.

### Ejercicio 1 · Montad el RAG y cambiad una decisión (~50 min)

Es **el ejercicio 3 de la sesión 2**, explicado en la sección 14 de su
[guía](../clase_02/EXPLICACION_tema_2.md#ejercicio-3--montad-el-rag-y-cambiad-una-decisión-50-min): RAG funcionando
(10 → 11), mirar cómo se trocea un PDF y la llamada, línea base con `14_evaluar_rag.py` (k = 3 y k = 1, aciertos y
MRR), cambiar **una** decisión (cabecera, tamaño de trozo u otro modelo de embeddings) y medir, preguntar con el 13
(Pack 4, una tuya y una imposible) y leer las fuentes citadas.

Novedad: al deshacer el cambio y rehacer corpus e índice, hay que pasar también **`09_indice_junio.py`**, que copia ese
corpus en el índice ampliado que usa el asistente (si no, el asistente seguiría con el corpus cambiado).

**Qué entregar:** la ficha de tu fragmento explicada; la tabla antes/después; tu conclusión en 2–3 frases; y las tres
respuestas con sus citas, diciendo si la fuente dice exactamente lo mismo.

### Ejercicio 2 · Cinco frases para dirección (~20 min)

Es **el ejercicio 4 de la sesión 2** ([guía 2, sección 14](../clase_02/EXPLICACION_tema_2.md#ejercicio-4--cinco-frases-para-dirección-20-min)).
El enunciado remite a un **«anexo B»** con la respuesta del analista (`15_analista.py`) en el Jetson, pero **no viene
en el PDF**: esa respuesta está en la diapositiva 66 de la sesión 2 (sección 13.2 de su guía). Auditarla frase a frase
(hecho, testimonio, hipótesis; qué dato importante no consultó) y escribir tus cinco frases: hipótesis priorizada,
cifras con su consulta, fuentes (documento y página; la llamada, como testimonio) y el dato que pedirías. Sin afirmar
causas que los datos no prueban.

### Ejercicio 3 · El reto Malasaña, la versión que firmaríais (~50 min)

La pregunta ([`reto.md`](./DropLab_sesion_3/alumnos/sesion_3/reto.md), parte 2):

> **¿Qué cambió en las ventas de Malasaña entre marzo y abril, qué aportan los documentos y la llamada, y qué
> demuestra este ticket (`data/imagenes/ticket_abril.png`)?**

Una página con [`plantilla_reto.md`](./DropLab_sesion_3/alumnos/sesion_3/plantilla_reto.md). La respuesta del asistente
está guardada (`05_flujo.py --caso combinada --guardada`); se puede repetir en directo con `05_flujo.py`, la API u
Open WebUI. **El asistente es una herramienta: la respuesta la firmas tú.** Si dice algo que no puedes comprobar, no
lo entregues como hecho.

| Lo que tiene que tener | Cómo pensarlo |
|---|---|
| **Cifras reproducibles** | Cada una con la consulta que la da: `POST /datos/consulta` de la API, o tu SQL sobre las vistas (`02_capa_semantica.py --sql`) |
| **Documentos y llamada** | Documento, página o sección, estado y fecha; la **versión vigente**; la llamada, como testimonio (y su minuto) |
| **El ticket** | Qué se lee, qué dice caja, el veredicto del código… y **lo que no demuestra** (sección 5.4) |
| **Contradicciones y pendiente** | Lo que no cuadra y lo que faltaría para saberlo |
| **Recomendación proporcionada** | Que no vaya más allá de la evidencia |
| **Traza** | Qué preguntaste y qué fuentes abriste, para que otra persona pueda repetirlo |

Y al lado, **qué frases de la respuesta del asistente cambiaste y por qué**. Úsalas con las cuatro preguntas de la
sección 12.2 y con la tabla de tipos de error de la sesión 1.

**Cómo se valora (40 puntos, `reto.md`):**

| Criterio | 10 puntos | 5 puntos | 0 puntos |
|---|---|---|---|
| **Corrección** | Cifras correctas que salen de una consulta repetible | Correctas sin consulta, o una cifra con otro significado | Inventadas o de memoria |
| **Fuentes** | Cada afirmación con su evidencia; versión vigente; la llamada como testimonio | Fuentes generales o alguna afirmación sin fuente | Sin fuentes, o un borrador como vigente |
| **Límites** | Distingue hecho, hipótesis y lo que no consta; no afirma causas ni culpas | Menciona límites pero alguna frase va más allá | Afirma la causa de la caída o habla de fraude |
| **Trazabilidad** | Otra persona podría repetirlo | Traza incompleta | Sin traza |

No puntúa la velocidad, el ordenador, el modelo ni lo larga que sea.

### Ejercicio 4 · El cierre de junio (~50 min)

Segundo encargo: los dos PDF de junio (sección 6). En clase se leyeron con PaddleOCR y se indexaron con una ficha que
dice «sin revisar». **Ahora toca revisar.**

**Cuatro preguntas de junio** (cada una es un caso de `05_flujo.py`):

| Caso | Pregunta |
|---|---|
| `junio_tabla` | ¿Cuántos pares de STREET_ONE_NEGRO_41 aceptó Malasaña en junio? El borrador decía 72. |
| `junio_grafico` | ¿Qué semana de junio tuvo el peor porcentaje de líneas completas en Malasaña? ¿Fue por la caja húmeda del albarán A-0617-04? |
| `junio_escaneado` | ¿Cuántos pares del albarán A-0617-04 se aceptaron al final y qué pasó con el resto? |
| `junio_trampa` | Tras la reposición de junio, ¿faltan 18 pares en las tiendas? ¿Cuánto costó la incidencia descontando los 240 euros del transportista? |

Para cada una: **primero tu respuesta leyendo los PDF** (`data/documentos_junio/`), con página; **después la del
asistente** (`05_flujo.py --caso <caso> --guardada`) leída con las cuatro preguntas de clase (sí, a medias o no).
«Ojo: alguna de las cuatro tiene un error.» Pistas para leer los PDF sin que te los resuelva:

- Distingue **solicitado**, **expedido** y **aceptado**: son conceptos distintos, y el informe explica qué se puede
  sumar y qué no.
- Una **reclamación** no es un **abono cobrado**: mira qué dice el informe sobre los 240 €.
- Comprueba siempre qué versión cita la respuesta: el anexo de la pág. 6 es el **borrador sustituido**.
- En el gráfico, mira **la fecha** de la semana y **la fecha** del incidente.

**Una lectura, contra el original:** elige una página del escaneado y compara la lectura del OCR y la de PaddleOCR-VL
(`08_leer_documentos.py --leer escaneado N --con ocr` y `--con vl`, con `--guardada`) con la imagen del PDF. ¿Algún
error? ¿Qué línea del OCR tiene la confianza más baja y por qué crees que es?

**Una mejora, medida** (elige una):

- **(a)** El caso `extra_falla` falla porque la pág. 3 no llega a la búsqueda (sección 13.1). Añade esa pregunta como
  prueba de recuperación en `practica/sesion_3/examen/examen_sesion_3.json` (fuente esperada
  `01_DropLab_informe_reposicion_junio.pdf#3`), comprueba que falla (`06_evaluar.py --parte recuperacion`, sin LLM),
  propón un arreglo (por ejemplo, repetir la cabecera de la tabla en las páginas de continuación, en
  `asistente/lectura.py`, y rehacer el índice con el 09) y mide antes y después. Necesita la carpeta con permiso de
  escritura.
- **(b)** El verificador acepta una cifra si está en **alguna** evidencia, aunque no en la que se cita (sección 10.6).
  Propón el cambio en `verificar()` de `asistente/flujo.py` y aplícalo a las respuestas guardadas
  (`salidas_guardadas/flujo/`): ¿cuáles marcaría? ¿Marca alguna correcta? (Ese «falso positivo» es lo interesante.)
- **(c)** Otra tuya, con su forma de medirla.

**Qué entregar:** una tabla con las preguntas (tu respuesta y fuente, la del asistente, las cuatro preguntas y, si no
coinciden, quién se equivocó y dónde: lectura, búsqueda, cálculo o redacción); la página revisada (errores o ninguno,
y la línea de menor confianza); tu mejora (el trozo de JSON o código) con el resultado antes y después. «Sed críticos:
¿mide de verdad lo que queréis?»

### Ejercicio 5 (opcional) · Hacia producción (~45 min)

Elegir uno de los temas de la sección 14.1 y escribir media página: qué problema concreto tendría DropLab hoy (con un
ejemplo visto en clase), qué cambiarías y en qué archivo, y **cómo sabrías que ha funcionado**. Si te animas, hazlo en
pequeño: guardar cada pregunta con su respuesta, fuentes y tiempos en JSONL desde `/analizar` de `asistente/api.py`;
exigir una clave en una cabecera (FastAPI, seguridad); o pasar `06_evaluar.py` antes y después de un cambio.

---

## 16. Enlaces y test

### Enlaces ([`Enlaces_sesion_3.pdf`](./Enlaces_sesion_3.pdf), revisados el 19/10/2026)

| # | Para | Enlace | Qué saber hacer |
|---|---|---|---|
| 1 | Ej. 1–2 | Embeddings en Ollama y `bge-m3` | Crear el índice y probar otro modelo de embeddings |
| 2 | Ej. 1–2 | BM25 y el artículo de RRF | Por qué la híbrida combina posiciones y no puntuaciones |
| 3 | Ej. 1–2 | Listas en DuckDB y recuperación contextual (Anthropic) | Qué se pierde al quitar la cabecera |
| 4 | Ej. 3 | Imágenes con Ollama y las variantes de `qwen3-vl` | Descargar un VLM que quepa y preguntarle por una imagen |
| 5 | Ej. 3 | Salidas estructuradas de Ollama (`format`) | Distinguir pedir JSON en el prompt de obligarlo con un esquema |
| 6 | Ej. 3 | Pydantic (validación y JSON Schema) | Leer el modelo `Ticket` y saber qué rechazaría |
| 7 | Ej. 3 | Ficha de `Qwen3-VL-8B-Instruct` | Encontrar la licencia del VLM que uses |
| 8 | Ej. 3 | Tutorial de FastAPI y manejo de errores | Leer una operación de `api.py`: qué entra, qué sale y qué errores da |
| 9 | Ej. 3 | Qué es OpenAPI | Por qué un contrato legible por máquinas sirve a otros programas |
| 10 | Ej. 3 | Códigos de estado HTTP (MDN) | Distinguir «la petición está mal» (4xx) de «falla una pieza» (5xx) |
| 11 | Ej. 3 | `requests` y `httpx` | Un POST con JSON; por qué la Pipe usa `httpx` asíncrono |
| 12 | Ej. 3 | OWASP: prevención de inyección SQL | Por qué «1; DROP TABLE ventas» no hace nada |
| 13 | Ej. 4 | PaddleOCR y su OCR (PP-OCRv6) | Qué devuelve un OCR y qué no |
| 14 | Ej. 4 | PaddleOCR-VL y el motor de inferencia | Por qué en el Jetson va en la GPU sin PaddlePaddle |
| 15 | Ej. 4 | PyMuPDF | Comprobar si un PDF tiene texto o es solo imagen |
| 16 | Ej. 5 | Seguridad en FastAPI | Que la API rechace (401) una petición sin clave |
| 17 | Ej. 5 | FastAPI en Docker y Docker Compose | Qué se gana frente a arrancar cada pieza a mano |
| 18 | Ej. 5 | Usuarios y permisos en Open WebUI | Qué cambiar para que cada persona vea solo lo suyo |
| 19 | Ej. 5 | `logging` de Python y JSON Lines | Guardar cada pregunta con su traza y contarlas con una consulta |
| 20–23 | Por dentro | VLM (blog y ViT), Qwen3-VL, PaddleOCR-VL (ficha y artículo), bge-m3 y el RAG original | Por qué más píxeles cuestan más tokens; parser frente a OCR; qué añade nuestro RAG |
| 24–25 | Open WebUI | Docker y su red; Open WebUI, sus Pipes y su licencia | Instalar la Pipe; qué hace ella y qué hace la API |
| 26–27 | El flujo | LangGraph (estado, nodos, aristas); memoria y contexto en Ollama (`keep_alive`, `num_ctx`) | Señalar en el grafo el estado, un nodo y el enrutamiento; por qué la primera pregunta tarda más |
| 28–30 | Opcional | La API como herramienta de Open WebUI; la API de chat de Ollama; licencias (Apache 2.0) | Pipe que siempre llama frente a modelo que decide si llama; pesos abiertos frente a licencia abierta |

### Test ([`Test - sesión 3.pdf`](./Test%20-%20sesi%C3%B3n%203.pdf))

15 preguntas para hacer **al final y sin apuntes**. Qué sección de la guía tiene lo necesario para razonar cada una
(sin dar la respuesta):

| # | Tema | Sección |
|---|---|---|
| 1 | Quién escribe el veredicto «discrepancia» del ticket | 5.4 |
| 2 | El JSON del ticket muy borroso que Pydantic acepta | 5.3 |
| 3 | Qué se puede afirmar de 231,99 € frente a 211,99 € | 5.4 |
| 4 | Qué le falta al OCR para servir a un RAG | 7.3 |
| 5 | Qué es la página `/docs` | 9 |
| 6 | «1; DROP TABLE ventas» en `/datos/consulta` | 9 |
| 7 | Por qué el OCR pasó de ~40 s a ~2 s por página en el Jetson | 7.2 |
| 8 | Dónde está la lógica cuando se usa «DropLab Analista» | 11 |
| 9 | Qué hace el código con el plan del modelo | 10.3 |
| 10 | Qué aporta LangGraph si un `while` da lo mismo | 10.8 |
| 11 | Qué dice la ficha de la pág. 4 (gráfico G1) | 7.4 y 7.6 |
| 12 | El borrador v0.9 con el mismo código que el aprobado | 7.5 |
| 13 | Qué revisar si falla una pregunta de recuperación | 13.3 |
| 14 | El valle del 68 % y la caja húmeda del 17/06 | 12.2 |
| 15 | «66 pares… [D4]» y el verificador no avisa | 10.6 |

---

## 17. Mapa de los scripts y cómo ejecutarlos

### 17.1 Qué hay en `DropLab_sesion_3`

Es **autocontenido**: datos, documentos (también los de junio), imágenes, audio, los scripts de las tres sesiones
(`practica/sesion_1`, `sesion_2` y `sesion_3`), los índices ya creados, las lecturas de junio hechas en el Jetson y las
salidas guardadas. Cambios respecto al zip de la sesión 2: `sesion_1` trae también 01, 02 y 04; `11_indice.py` y
`12_buscar.py` aceptan otro corpus y otra ruta de índice (para el ampliado). Siguen sin venir los WAV por canal que
pide `07_transcribir.py` (ver la guía de la sesión 2, sección 14).

| Carpeta | Qué hay |
|---|---|
| `data/datos/`, `data/documentos/`, `data/audio/` | Lo de las sesiones 1 y 2 |
| `data/imagenes/` | `ticket_marzo.png`, `ticket_abril.png`, `recuento_stock_0604.png`, `albaran_0604.png` |
| `data/documentos_junio/` | Los dos PDF de junio |
| `practica/sesion_3/asistente/` | El paquete del asistente (la lógica; los scripts solo la llaman) |
| `practica/sesion_3/openwebui/` | Arrancar Open WebUI, la Pipe, su instalador y la sonda |
| `practica/sesion_3/rag/` | Corpus e índice **ampliados** (62 fragmentos) |
| `practica/sesion_3/salidas_guardadas/` | Salidas reales del Jetson: `vision/`, `flujo/`, `documentos/` (lecturas de junio) y `cache_vision/` |
| `practica/sesion_3/examen/` | `examen_sesion_3.json` (lectura, recuperación, cálculo y respuesta) |
| `practica/sesion_3/imagenes_sinteticas/` | Ticket borroso y muy borroso (sintéticos) |
| `experimentos/sesion_3/` | Mediciones de `06_evaluar.py` y `07_comparar.py` |
| `alumnos/sesion_3/` | Guía del alumno, reto, plantilla y guía de integración |

### 17.2 El paquete `asistente/`

| Módulo | Qué hace |
|---|---|
| `config.py` | Rutas, URLs, modelos (variables `DROPLAB_*`), `num_ctx` fijo, tamaño máximo de imagen |
| `ollama.py` | `chat()` a `/api/chat` con `format` opcional, tiempos y `ErrorComponente` |
| `sesion2.py` | Importa tal cual la capa semántica, el SQL del modelo y el RAG de la sesión 2 |
| `datos.py` | Consultas fijas con parámetros (`pedido`, `resumen_tienda`, `disponibilidad_en`, `roturas_dia`) y el SQL del modelo |
| `documentos.py` | El RAG de la sesión 2 sobre el índice ampliado (o el de la sesión 2 con `DROPLAB_INDICE=sesion2`) |
| `vision.py` | Esquemas `Ticket`, `Recuento`, `Albaran`; preparar, clasificar, extraer, validar, comprobar y veredicto |
| `lectura.py` | Limpiar la lectura de PaddleOCR-VL, comprobar cifras con la capa de texto, unir la fila partida, ficha de cada página |
| `flujo.py` | El grafo de LangGraph: `Plan`, `Estado`, los 7 nodos, `enrutar`, `verificar` |
| `flujo_simple.py` | El mismo proceso con un bucle de Python |
| `api.py` | La API FastAPI (seis operaciones y el formato de error) |

### 17.3 Preparar el entorno

Hay un único `.venv` en la raíz del tema. Su `requirements.txt` ya incluye los de esta sesión (FastAPI, uvicorn,
python-multipart, Pydantic, LangGraph, httpx y Pillow):

```bash
cd ~/ebis/07_llm_open_source
source .venv/bin/activate
pip install -r requirements.txt
```

Modelos de Ollama para este portátil (16 GB): `qwen3:4b-instruct` (ya está), **`qwen3-vl:4b-instruct`** y **`bge-m3`**
(`ollama pull …`; varios GB). Y para los scripts de la sesión 3:

```bash
export DROPLAB_MODELO_TEXTO=qwen3:4b-instruct DROPLAB_MODELO_VISION=qwen3-vl:4b-instruct
```

Todas las órdenes se lanzan **desde `DropLab_sesion_3`**, y la primera comprobación es `00_comprobar_entorno.py`:

```bash
cd ~/ebis/07_llm_open_source/clase_03/DropLab_sesion_3
python practica/sesion_3/00_comprobar_entorno.py          # todo en verde (o casi); --calentar carga los modelos
```

Recuerda el aviso de la sección 15: para crear índices o leer imágenes en directo, antes `chmod -R u+w` sobre la carpeta.
Open WebUI (Docker) y PaddleOCR (`.venv-ocr`) son opcionales.

### 17.4 Los scripts de `practica/sesion_3/`

| Script | Qué hace | Necesita | Opciones |
|---|---|---|---|
| `00_comprobar_entorno.py` | Hardware, librerías, Ollama y modelos, índices, lecturas, API, Open WebUI, salidas guardadas | Nada | `--calentar` |
| `01_ver_imagen.py [imagen]` | Los 6 pasos con una imagen (por defecto `ticket_marzo.png`) | VLM (salvo `--guardada`) | `--tipo`, `--modelo`, `--sin-libre`, `--sin-esquema`, `--guardada` |
| `02_validar.py` | Esquema y validación con tres ejemplos | Nada | `--esquema` |
| `03_api.py` | Arranca la API en `0.0.0.0:8000` (`/docs`, `/salud`) | Ollama para las operaciones con modelo | `--puerto`, `--host` |
| `04_cliente_api.py OPERACIÓN [texto]` | Habla con la API: `salud`, `buscar`, `consulta`, `ticket`, `analizar` | La API en marcha | `--api`, `--pedido`, `--tienda`, `--imagen` |
| `05_flujo.py [pregunta]` | El flujo completo, paso a paso | Ollama (salvo `--guardada`/`--dibujar`) | `--caso`, `--imagen`, `--reglas`, `--sin-framework`, `--modelo-texto`, `--modelo-vision`, `--dibujar`, `--guardada`, `--guardar` |
| `06_evaluar.py` | Examen por piezas (por defecto, resultados guardados) | Según la parte | `--parte {lectura,recuperacion,calculo,respuesta,integracion}`, `--todo`, `--texto`, `--vision`, `--guardar` |
| `07_comparar.py` | Dos configuraciones de modelos (por defecto, guardado) | Ollama con `--medir` (~1 h) | `--medir`, `--solo {A,B}`, `--recalificar` |
| `08_leer_documentos.py` | Las cuatro formas de leer los PDF de junio | Nada con `--guardada`; PaddleOCR en directo | `--antes`, `--leer DOC PAG`, `--con {texto,ocr,vl,vlm}`, `--guardada`, `--comparar`, `--capas DOC PAG` (+ `--solo-modelo`/`--solo-reglas`), `--grafico`, `--modelo`, `--guardar` |
| `09_indice_junio.py` | Corpus e índice ampliados (62 fragmentos) | bge-m3 (salvo `--ver`/`--sin-indice`) | `--ver N`, `--buscar "…"`, `-k`, `--sin-indice` |
| `guardar_salidas.py` | Regenera las salidas guardadas (antes de clase) | Ollama | `--solo {vision,flujo}` |

### 17.5 Órdenes de ejemplo

```bash
# Bloque II · imágenes
python practica/sesion_3/01_ver_imagen.py ticket_abril.png --guardada
python practica/sesion_3/01_ver_imagen.py ticket_abril_muy_borroso.png --guardada
python practica/sesion_3/02_validar.py
python practica/sesion_3/01_ver_imagen.py ticket_abril.png --sin-libre        # en directo (VLM)

# Bloque II · PDF de junio
python practica/sesion_3/08_leer_documentos.py                                # qué hay en cada página
python practica/sesion_3/08_leer_documentos.py --antes
python practica/sesion_3/08_leer_documentos.py --leer escaneado 2 --con ocr --guardada
python practica/sesion_3/08_leer_documentos.py --leer informe 4 --con vl --guardada
python practica/sesion_3/08_leer_documentos.py --capas informe 8 --guardada --solo-reglas
python practica/sesion_3/08_leer_documentos.py --comparar
python practica/sesion_3/09_indice_junio.py --ver 56
python practica/sesion_3/09_indice_junio.py --buscar "¿Cuántos pares aceptó MAD-MAL de NEGRO_41 en junio?"

# Bloque III · API y flujo
python practica/sesion_3/03_api.py                                            # en otra terminal; luego /docs
python practica/sesion_3/04_cliente_api.py consulta --pedido "1; DROP TABLE ventas"
python practica/sesion_3/05_flujo.py --dibujar
python practica/sesion_3/05_flujo.py --caso combinada --guardada
python practica/sesion_3/05_flujo.py --caso documental --sin-framework
python practica/sesion_3/05_flujo.py --caso numerica --reglas

# Extras
python practica/sesion_3/05_flujo.py --caso extra_falla --guardada
python practica/sesion_3/06_evaluar.py --parte integracion
python practica/sesion_3/07_comparar.py
```

Casos de `05_flujo.py --caso`: `documental`, `numerica`, `visual`, `combinada`, `insuficiente`, `causal`,
`junio_tabla`, `junio_grafico`, `junio_escaneado`, `junio_trampa`, `extra_falla` y `extra_campana`. Todos tienen salida
guardada en `salidas_guardadas/flujo/`.

Open WebUI (opcional, Docker): `bash practica/sesion_3/openwebui/arrancar_openwebui.sh` y
`python practica/sesion_3/openwebui/instalar_pipe.py`; luego `http://127.0.0.1:3000`, modelo «DropLab Analista».

---

## 18. Resumen final

1. **Imágenes:** un VLM lee y propone; un esquema Pydantic fija la **forma** (con `format`, siempre JSON válido); el
   **código** comprueba el contenido (formato posible, coherencia del ticket consigo mismo, caja) y escribe el
   veredicto. El ticket de abril se lee bien y no cuadra: discrepancia de 20 €, sin causa ni culpable.
2. **Documentos difíciles:** texto del PDF, OCR, parser y VLM general leen distinto; ninguno dice si ha leído bien.
   PaddleOCR lee; las reglas (pie, versión en la clave, fila partida) y la ficha «sin revisar» son nuestras, y negocio
   las valida. Índice ampliado: 62 fragmentos.
3. **Asistente:** Open WebUI (ventana) → Pipe (adaptador) → API FastAPI (contrato) → flujo LangGraph (7 nodos) →
   herramientas (visión, cifras, documentos) → Ollama. El modelo planifica con opciones cerradas y redacta; el código
   valida, enruta, contrasta y verifica.
4. **Medir:** por piezas, para saber dónde falla. Con el código haciendo lo difícil, el 4B casi empata con el 30B;
   **leer** desempata.
5. **Producción:** medir, proteger y operar.

### Ideas para recordar siempre

- **Un VLM no es un notario.** Su «legibilidad» es una opinión, no una probabilidad.
- **JSON válido no es contenido correcto.** Pydantic garantiza la forma; el contenido, el código y las personas.
- **Leído no es comprobado.** Lo que no se ha podido comprobar, se dice: «sin revisar».
- **Una discrepancia pide revisión,** no demuestra fraude.
- **El modelo propone; el código dispone.** Opciones cerradas, rutas fijas y contrastes antes de redactar.
- **La traza es lo que se puede auditar,** no el «razonamiento» del modelo.
- **Si la página con el dato no llega, el modelo rellena.** Y el verificador puede no verlo.
- **Una fuente es una evidencia, no la verdad.**

### Preguntas para repasar

1. ¿Qué diferencia hay entre OCR, VLM, extracción y verificación? ¿Quién hace cada una en el asistente?
2. ¿Por qué `format` con un esquema garantiza JSON válido pero no el total correcto del ticket?
3. ¿Por qué el ticket muy borroso da «lectura dudosa» y no «discrepancia»?
4. ¿Por qué el VLM de 4B lee 95 donde pone 96? ¿Qué tiene que ver con los parches?
5. ¿Qué devuelve un OCR y qué devuelve un parser de documentos? ¿Cuál sirve mejor a un RAG y por qué?
6. ¿Por qué la regla «sustituye a» de la sesión 2 no sirve para el informe de junio y cómo se arregla?
7. ¿Qué significa «sin revisar» en la ficha y por qué en el escaneado no se puede comprobar ninguna cifra?
8. ¿Qué hace la Pipe y qué hace la API? ¿Qué cambiaría si sustituyéramos Open WebUI por otra interfaz?
9. En el flujo, ¿qué decide el modelo y qué decide el código? Pon un ejemplo de corrección del plan.
10. ¿Por qué `extra_falla` pasa la verificación siendo falsa? ¿Qué pieza falló y cómo lo medirías?
