# Guía de estudio — Tema 7, Sesión 1, Ejercicio 3: `herramientas.py`, tu propia herramienta para el modelo

> Esta guía explica, línea a línea y con lenguaje sencillo, el archivo
> [`herramientas.py`](./herramientas.py): qué hace cada bloque, por qué está escrito así, cómo se
> ejecuta y cómo leer los resultados que deja en `resultados_*.json`. Complementa la sección 11 de la
> [guía de la sesión 1](../../EXPLICACION_tema_1.md#ejercicio-3--construye-una-herramienta-60-min-python--ollama)
> y se apoya en las [trazas del aula](./trazas_jetson.md).
> Las cifras que aparecen aquí las he comprobado ejecutando el propio script.

## Índice

1. [La idea del ejercicio en una frase](#1-la-idea-del-ejercicio-en-una-frase)
2. [El archivo de un vistazo](#2-el-archivo-de-un-vistazo)
3. [Bloque 1 · Datos: leer, validar y redondear](#3-bloque-1--datos-leer-validar-y-redondear)
4. [Bloque 2 · Las herramientas: `ventas_netas` y `cesta`](#4-bloque-2--las-herramientas-ventas_netas-y-cesta)
5. [Bloque 3 · Describir las herramientas al modelo (`TOOLS`)](#5-bloque-3--describir-las-herramientas-al-modelo-tools)
6. [Bloque 4 · Comprobar sin modelo (`probar`)](#6-bloque-4--comprobar-sin-modelo-probar)
7. [Bloque 5 · El bucle de *tool calling*](#7-bloque-5--el-bucle-de-tool-calling)
8. [La batería, los experimentos y el JSON de resultados](#8-la-batería-los-experimentos-y-el-json-de-resultados)
9. [Lo que dicen tus ejecuciones](#9-lo-que-dicen-tus-ejecuciones)
10. [El hallazgo y el reto opcional](#10-el-hallazgo-y-el-reto-opcional)
11. [Cómo ejecutarlo](#11-cómo-ejecutarlo)
12. [Resumen final](#12-resumen-final)

---

## 1. La idea del ejercicio en una frase

> **Tú escribes la función que calcula; el modelo solo decide cuándo llamarla y con qué argumentos.**

Es la regla de oro del curso aplicada a herramientas: **el código calcula, el modelo redacta, tú
verificas**. El modelo **nunca ve los CSV ni tu código**: solo ve el *nombre* y la *descripción* de
cada herramienta. Si la descripción es buena, pide la herramienta correcta; si es mala, se equivoca
**sin dar ningún mensaje de error**.

**Ejemplo cotidiano:** el modelo es un recepcionista que no sabe hacer cuentas, pero tiene una lista
de departamentos con un cartel que dice qué hace cada uno. Si el cartel de «Contabilidad» dice solo
«Departamento», mandará a la gente al sitio equivocado. Tu trabajo es (1) que el departamento haga
bien las cuentas y (2) que su cartel sea claro.

El archivo traía dos tareas (`TODO`), que en tu versión ya están hechas:

| Tarea | Qué es | Dónde |
|---|---|---|
| **TODO 1** | La función `cesta()`: cómo son las compras de una tienda entre dos fechas. | [herramientas.py:122-149](./herramientas.py#L122-L149) |
| **TODO 2** | Su descripción en `TOOLS`, para que el modelo sepa que existe y cuándo usarla. | [herramientas.py:178-189](./herramientas.py#L178-L189) |

---

## 2. El archivo de un vistazo

Solo usa la **biblioteca estándar de Python** (sin `pandas` ni `requests`): `csv` para leer, `Decimal`
para el dinero y `urllib` para hablar con Ollama. Funciona con Python 3.9+.

| Bloque | Líneas | Qué hace | ¿Se toca? |
|---|---|---|---|
| Cabecera | 1–40 | Documentación, *imports* y tres constantes: URL de Ollama, modelo y tiendas. | No |
| **1 · Datos** | 42–86 | Encontrar y leer los CSV, validar argumentos, redondear euros. | No |
| **2 · Herramientas** | 89–149 | `ventas_netas()` (hecha) y `cesta()` (**TODO 1**). | **Sí** |
| **3 · Descripción** | 153–193 | `PARAMETROS`, `TOOLS` (**TODO 2**) y `EJECUTORES`. | **Sí** |
| **4 · Comprobación** | 196–240 | Seis pruebas con resultado conocido (`probar`). | No |
| **5 · Bucle** | 243–361 | Contexto, instrucciones, batería, experimentos y el bucle con Ollama. | No |
| `main()` | 364–397 | Lee la orden de la terminal (`probar`, `calcular`, `preguntar`, `bateria`). | No |

Las tres constantes de arriba ([herramientas.py:37-39](./herramientas.py#L37-L39)):

```python
OLLAMA_URL = "http://localhost:11434/api/chat"   # Ollama en tu propio equipo
MODELO = "qwen3:4b-instruct"                     # el modelo de clase
TIENDAS = {"MAD-MAL": "Malasaña", "MAD-GOY": "Goya", "BCN-EIX": "Eixample"}
```

---

## 3. Bloque 1 · Datos: leer, validar y redondear

### 3.1 `buscar_datos()`: dónde están los CSV

Busca la carpeta que contiene `ventas.csv`, en este orden:

1. La variable de entorno `DROPLAB_DATOS`, si existe.
2. `DropLab/datos` o `data/datos` en la carpeta actual, y luego en la del script **y en todas las de
   arriba**.

Por eso funciona aunque `DropLab/` esté un nivel más arriba (aquí está en
[`../DropLab/datos/`](../DropLab/datos/)). Si no lo encuentra, termina con un mensaje claro en vez de
un error raro.

### 3.2 `tabla(nombre)`: leer cada CSV una sola vez

```python
_TABLAS: dict[str, list[dict]] = {}

def tabla(nombre):
    if nombre not in _TABLAS:
        ... _TABLAS[nombre] = list(csv.DictReader(f))
    return _TABLAS[nombre]
```

- `csv.DictReader` convierte cada fila en un diccionario: `{"linea_id": "A-MAD-MAL-0001", "cantidad": "2", …}`.
- **Ojo: todo llega como texto.** `"2"` no es `2`; por eso luego hace falta `int()` o `Decimal()`.
- `_TABLAS` es una **caché**: la primera vez lee el archivo; las siguientes devuelve lo que ya tiene en
  memoria. Durante una batería el modelo puede llamar a las herramientas muchas veces y no se relee
  el disco cada vez.

### 3.3 `validar(local_id, desde, hasta)`: la barrera en el código

Devuelve un **mensaje de error** si algo está mal, o `None` si todo está bien:

| Comprobación | Ejemplo que falla | Mensaje |
|---|---|---|
| ¿La tienda existe? | `MAD-XXX` | `local_id desconocido: MAD-XXX. Válidos: MAD-MAL, MAD-GOY, BCN-EIX` |
| ¿Las fechas son `YYYY-MM-DD`? | `"marzo"` | `Fechas no válidas. Usa el formato YYYY-MM-DD.` |
| ¿`desde` ≤ `hasta`? | `2026-04-01` → `2026-03-01` | `'desde' es posterior a 'hasta'.` |

Las herramientas **no lanzan excepciones**: devuelven `{"error": "…"}`. Así el error **vuelve al
modelo como texto** y puede corregirse en la siguiente ronda, en vez de romper el programa. Es la idea
de la sesión: *las barreras van en el código, no en el prompt*.

⚠️ Lo que `validar` **no** comprueba: que las fechas caigan dentro de los datos. Pedir 2023 es
perfectamente «válido» y devuelve ceros. Ese hueco es justo lo que explota el experimento
`--sin-contexto` (sección 9.2) y lo que propone arreglar el reto opcional (sección 10.2).

### 3.4 `euros(valor)`: redondear dinero bien

```python
def euros(valor: Decimal) -> float:
    return float(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
```

- Los importes se suman con **`Decimal`** (decimales exactos), no con `float`. Con `float`, sumar 1.441
  importes acumula error (`42000.00000000003`); con `Decimal` no.
- `quantize(Decimal("0.01"))` deja **2 decimales**, y `ROUND_HALF_UP` redondea «como en el colegio»
  (0,005 → 0,01). El `round()` de Python usa otro criterio (al par) y puede dar un céntimo distinto.
- Solo al final se convierte a `float`, porque JSON no entiende `Decimal`.

---

## 4. Bloque 2 · Las herramientas: `ventas_netas` y `cesta`

Las dos tienen **la misma firma**: `(local_id, desde, hasta)`, ambas fechas **incluidas**. Esto
importa: el modelo solo tiene que aprender un tipo de argumentos.

Un detalle útil de las dos: comparan fechas **como texto** (`desde <= v["fecha_venta"] <= hasta`).
Funciona porque el formato `YYYY-MM-DD` ordena alfabéticamente igual que cronológicamente
(`"2026-03-29" < "2026-03-30"`). Con `29/03/2026` no funcionaría.

### 4.1 `ventas_netas()` (ya hecha)

Aplica las reglas de negocio de la sesión ([herramientas.py:94-119](./herramientas.py#L94-L119)):

1. **Ventas antes de reembolsos (`bruto`):** suma `importe_linea` de las filas de esa tienda cuya
   `fecha_venta` está en el rango.
2. **Reembolsos:** `reembolsos.csv` **no tiene `local_id`**, así que primero construye un
   diccionario `tienda_de_linea = {linea_id: local_id}` con todas las ventas y, con él, averigua la
   tienda de cada abono. El abono cuenta si su **`fecha_reconocimiento`** está en el rango (no la de
   la venta).
3. **Neto = bruto − abonos.**

Fíjate en que **no hace un JOIN**: usa un diccionario de búsqueda. Cada abono busca su tienda, pero
ninguna venta se duplica. Así evita la trampa del JOIN que duplica (`HIST-JOIN-001`, 200 € en vez de
100 €).

```
$ python herramientas.py calcular ventas_netas BCN-EIX 2026-03-02 2026-03-29
ventas_antes_reembolsos_eur 25000.0 · reembolsos_reconocidos_eur 1000.0 · ventas_netas_eur 24000.0
```

### 4.2 `cesta()` (TODO 1)

Responde a «¿cómo son las compras?», contando bien **pedido ≠ línea ≠ unidades**
([herramientas.py:122-149](./herramientas.py#L122-L149)):

```python
filas = [v for v in tabla("ventas")
         if v["local_id"] == local_id and desde <= v["fecha_venta"] <= hasta]
unidades_de_pedido = defaultdict(int)          # {pedido_id: unidades de ese pedido}
for v in filas:
    unidades_de_pedido[v["pedido_id"]] += int(v["cantidad"])
```

Paso a paso:

| Paso | Código | Qué consigue |
|---|---|---|
| 1 | `validar(...)` | Igual que `ventas_netas`: error legible si algo está mal. |
| 2 | `filas = [...]` | Las **líneas** de esa tienda en esas fechas. |
| 3 | `defaultdict(int)` | Un diccionario que empieza en 0 para cualquier clave nueva: no hace falta comprobar si el pedido ya estaba. |
| 4 | `+= int(v["cantidad"])` | Suma las unidades **por pedido**. `int()` porque el CSV da texto. |

Y de ese diccionario salen todas las métricas:

| Métrica | Cómo se calcula | Por qué así |
|---|---|---|
| `pedidos` | `len(unidades_de_pedido)` | Cada `pedido_id` es una clave: cuenta pedidos **distintos**. |
| `lineas` | `len(filas)` | Una fila = una línea. |
| `unidades` | `sum(unidades_de_pedido.values())` | Suma de `cantidad`. |
| `unidades_por_pedido` | `round(unidades / pedidos, 2)` | Tamaño medio de la cesta. |
| `ticket_medio_eur` | `euros(importe / pedidos)` | Importe **antes de reembolsos** entre pedidos, con `Decimal`. |
| `pedidos_4_o_mas_unidades` | `sum(1 for u in … if u >= 4)` | Cuenta los pedidos «grandes». Solo se puede saber **después** de agrupar por pedido. |

Dos protecciones pequeñas pero importantes: `if pedidos else 0` evita **dividir entre cero** si no hay
ventas en ese rango, y el resultado incluye `local_id`, `desde` y `hasta`, de modo que en la traza
siempre se ve **a qué se refiere cada cifra**.

**Ejemplo para entender el paso 4:** el pedido `A-MAD-MAL-ORD-0006` tiene 2 líneas de 2 unidades.
Tras el bucle, `unidades_de_pedido["A-MAD-MAL-ORD-0006"] == 4`: cuenta como **1 pedido**, **2 líneas**,
**4 unidades** y **sí** entra en `pedidos_4_o_mas_unidades`. Si contaras líneas con `cantidad >= 4`,
no saldría nunca (ninguna línea tiene 4).

---

## 5. Bloque 3 · Describir las herramientas al modelo (`TOOLS`)

### 5.1 `PARAMETROS`: un esquema JSON compartido

```python
"local_id": {"type": "string", "enum": ["MAD-MAL", "MAD-GOY", "BCN-EIX"],
             "description": "MAD-MAL = Malasaña, MAD-GOY = Goya, BCN-EIX = Eixample"},
"desde":    {"type": "string", "description": "Primer día incluido, formato YYYY-MM-DD"},
"hasta":    {"type": "string", "description": "Último día incluido, formato YYYY-MM-DD"},
"required": ["local_id", "desde", "hasta"]
```

- **`enum`** limita los valores posibles: el modelo ve que solo hay tres tiendas y cómo se llaman.
- Las descripciones de `desde`/`hasta` dicen **«incluido»** y el **formato**: evitan que el modelo
  pida «marzo» o un rango que se deja el último día.
- Se reutiliza para las dos herramientas porque tienen la misma firma.

### 5.2 `TOOLS`: lo único que lee el modelo

Cada herramienta es un bloque con `name`, `description` y `parameters`. La descripción de `cesta`
(TODO 2) hace tres cosas, y las tres importan:

| Qué dice | Ejemplo en tu texto | Para qué sirve |
|---|---|---|
| **Qué devuelve** | «número de pedidos, líneas, unidades, unidades por pedido, ticket medio…» | Que el modelo sepa que la respuesta está ahí. |
| **Cómo se define** cada cifra dudosa | «ticket medio en euros (importe antes de reembolsos / pedidos)» | Que no la confunda con otra (neto, por línea…). |
| **Cuándo usarla y cuándo no** | «…para ventas netas o reembolsos usa `ventas_netas`. Para comparar periodos, llámala una vez por periodo.» | Que elija bien entre dos herramientas parecidas y pida A y B por separado. |

> El modelo **no ve tu función**: si la descripción no menciona «pedidos de 4 o más unidades», no
> sabe que puedes calcularlos.

### 5.3 `EJECUTORES`: del nombre a la función

```python
EJECUTORES = {"ventas_netas": ventas_netas, "cesta": cesta}
```

Cuando el modelo pide `"cesta"`, el código busca aquí qué función de Python ejecutar. Es también una
**lista blanca**: si el modelo inventa una herramienta (`"visitas"`), no existe en el diccionario y se
devuelve un error. Al añadir una herramienta nueva hay que tocar **tres sitios**: la función, `TOOLS`
y `EJECUTORES`.

---

## 6. Bloque 4 · Comprobar sin modelo (`probar`)

`PRUEBAS` es una lista de casos con **resultado conocido** (calculado de antemano). `probar()`
ejecuta cada uno y compara clave a clave:

| Prueba | Qué comprueba |
|---|---|
| `ventas_netas` · Eixample · A | 25.000 − 1.000 = 24.000 € |
| `ventas_netas` · Goya · 9–15 mar | Un rango corto que no es un periodo: 7.610,33 − 341,38 = 7.268,95 € |
| `cesta` · Goya · A | 120 pedidos, 240 líneas, 390 unidades, 3,25 u/pedido, 275 €, **44** pedidos ≥ 4 |
| `cesta` · Eixample · B | 120 pedidos, 295 unidades, 2,46 u/pedido, 216,67 €, **5** pedidos ≥ 4 |
| `cesta` · Goya · 9–15 mar | 29 pedidos, 94 unidades, 262,43 € (comprueba que filtras bien las fechas) |
| `cesta` · tienda inexistente | Debe devolver una clave `error` |

Si la función aún tiene `raise NotImplementedError`, la prueba sale como `[PENDIENTE]` en vez de
romperse. Tu versión da:

```
6 de 6 pruebas superadas.
```

**Por qué es importante:** comprueba el cálculo **antes** de meter al modelo. Si una cifra sale mal
en la batería, ya sabes que el fallo está en el modelo (herramienta o argumentos equivocados), no en
tu función.

---

## 7. Bloque 5 · El bucle de *tool calling*

### 7.1 Lo que recibe el modelo

**`CONTEXTO`** traduce el lenguaje del negocio a datos: «Periodo A: del 2026-03-02 al 2026-03-29.
Periodo B: del 2026-03-30 al 2026-04-26» y los códigos de tienda. Sin esto, «periodo A» no significa
nada para el modelo.

**`INSTRUCCIONES`** (el *system prompt*): eres el analista de DropLab; **usa las herramientas para
cualquier cifra**; no calcules ni inventes; compara periodos pidiéndolos por separado; **si ninguna
herramienta sirve, dilo y no estimes**; responde en español en ≤ 5 frases citando las cifras.

### 7.2 `preguntar()`: la conversación por rondas

Es **el corazón del ejercicio** ([herramientas.py:306-339](./herramientas.py#L306-L339)). Hace de
intermediario entre el modelo y tus funciones: le pasa la pregunta, ejecuta lo que pida, le devuelve
los resultados y repite hasta que el modelo contesta con texto.

**Preparación** (antes del bucle):

```python
sistema = INSTRUCCIONES.format(contexto="" if sin_contexto else CONTEXTO)   # experimento 2
tools = herramientas_pobres(TOOLS) if pobres else TOOLS                      # experimento 1
messages = [{"role": "system", "content": sistema}, {"role": "user", "content": pregunta}]
```

Los dos experimentos se activan **aquí**: solo cambian lo que *ve* el modelo, nunca tus funciones.

#### El payload: lo que se envía a Ollama en cada ronda

```python
payload = {"model": modelo, "messages": messages, "stream": False, "think": False,
           "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 600}}
if ronda < max_rondas:
    payload["tools"] = tools
```

| Campo | Valor | Qué significa y por qué |
|---|---|---|
| `model` | `qwen3:4b-instruct` (o `--modelo`) | Qué modelo de Ollama responde. |
| `messages` | La conversación **entera** hasta ahora | El modelo **no tiene memoria** entre llamadas: en cada ronda hay que reenviarle todo (instrucciones, pregunta, llamadas anteriores y sus resultados). |
| `tools` | `TOOLS` (o la versión pobre) | El «menú» de herramientas. **No se envía en la última ronda.** |
| `stream` | `False` | Recibe la respuesta entera de una vez, no palabra a palabra. |
| `think` | `False` | Sin razonamiento oculto: de minutos a segundos (sección 6.3 de la guía de la sesión). |
| `options.temperature` | `0` | Siempre la palabra más probable: mismas preguntas → mismas llamadas. Necesario para comparar experimentos. |
| `options.num_ctx` | `8192` | Tamaño de la ventana de contexto. Más grande que en el script 04 (4.096) porque aquí entran las descripciones de `TOOLS` y los resultados de cada ronda. Más = más memoria. |
| `options.num_predict` | `600` | Máximo de tokens que puede escribir en cada ronda (evita respuestas interminables). |

#### Cómo crece `messages` ronda a ronda (pregunta 4 de la batería)

```
Ronda 0 → se envían:  [system] instrucciones + contexto
                      [user]   ¿Cuántos pedidos de 4 o más unidades hubo en Malasaña en A y en B?
          el modelo devuelve tool_calls (sin texto):
                      cesta(MAD-MAL, 2026-03-02, 2026-03-29) y cesta(MAD-MAL, 2026-03-30, 2026-04-26)
          tu código añade:
                      [assistant] tool_calls = esas dos llamadas
                      [tool] {"pedidos": 120, …, "pedidos_4_o_mas_unidades": 108}   tool_name = cesta
                      [tool] {"pedidos": 120, …, "pedidos_4_o_mas_unidades": 7}     tool_name = cesta

Ronda 1 → se envían los 5 mensajes anteriores
          el modelo ya no pide nada: devuelve texto → RESPUESTA
          «En el periodo A … hubo 108 pedidos de 4 o más unidades … En el periodo B … hubo 7.»
```

Tres detalles del código:

- Hay que añadir **primero el mensaje `assistant` con sus `tool_calls`** y después un mensaje
  `tool` por cada resultado. Así el modelo ve «yo pedí esto → me devolvieron esto».
- El resultado se envía como **texto JSON** (`json.dumps(…, ensure_ascii=False)`, para que las tildes
  no salgan como `ñ`). El modelo lee texto, no diccionarios de Python.
- Un modelo puede pedir **varias herramientas en la misma ronda** (aquí, A y B a la vez); el `for ll
  in llamadas` las ejecuta todas antes de volver a preguntarle.

#### El final: cuándo y cómo se para

| Situación | Qué pasa |
|---|---|
| El modelo responde **sin `tool_calls`** | Su `content` es la respuesta; `break`. |
| Llega la **ronda 5** (`max_rondas`) | Se envía **sin `tools`**: el modelo no puede pedir nada más y está obligado a escribir. |

Ese límite es una **barrera en el código**: un modelo confundido podría pedir herramientas para
siempre. Por eso el bucle es `range(max_rondas + 1)`: 5 rondas con herramientas + 1 final sin ellas.

#### La traza y lo que devuelve

Cada llamada se guarda en `traza` (`herramienta`, `argumentos`, `resultado`) y, si `mostrar=True`, se
imprime:

```
  → el modelo pide  cesta({"local_id": "MAD-GOY", "desde": "2026-03-30", "hasta": "2026-04-26"})
    tu código da    {"pedidos": 120, "unidades": 307, "unidades_por_pedido": 2.56, ...}
RESPUESTA (12.7 s): En el periodo B, Goya registró 120 pedidos, con un promedio de 2.56 unidades por pedido.
```

Si el modelo no usó ninguna herramienta, lo avisa: `(el modelo no ha usado ninguna herramienta)`.
Es una señal de alarma si la pregunta necesitaba cifras, y la respuesta correcta en la pregunta 6.

La función devuelve `{"pregunta", "llamadas", "respuesta", "segundos"}`, que es exactamente lo que
`bateria()` guarda en el JSON. **Esa traza es la que te permite verificar**: qué pidió el modelo, qué
le devolvió tu código y si lo que escribe coincide.

### 7.3 `ejecutar()`: el modelo propone, tu código ejecuta

```python
def ejecutar(nombre, argumentos):
    if isinstance(argumentos, str):                    # 1. ¿llegan como texto? → convertir
        try:
            argumentos = json.loads(argumentos)
        except json.JSONDecodeError:
            return {"error": "Los argumentos no son un JSON válido."}
    if nombre not in EJECUTORES:                       # 2. ¿existe la herramienta?
        return {"error": f"No existe la herramienta {nombre}."}
    try:
        return EJECUTORES[nombre](**argumentos)        # 3. ejecutar de verdad
    except NotImplementedError:
        return {"error": f"La herramienta {nombre} todavía no está implementada."}
    except TypeError as exc:
        return {"error": f"Argumentos incorrectos: {exc}"}
```

Es la **única puerta** entre lo que escribe el modelo y tu código. El modelo solo genera texto con
forma de llamada (`{"name": "cesta", "arguments": {...}}`); quien la ejecuta es esta función. Por eso
la pregunta 10 del test: *el modelo propone, tu código ejecuta*.

Paso a paso:

1. **Argumentos como texto.** Ollama suele dar los argumentos como diccionario, pero otros modelos o
   servidores los dan como texto JSON (`'{"local_id": "MAD-MAL", ...}'`). Se aceptan los dos.
2. **Lista blanca.** Solo se ejecuta lo que está en `EJECUTORES`. Si el modelo inventa
   `visitas(...)`, no se ejecuta nada.
3. **`**argumentos`** desempaqueta el diccionario: `cesta(**{"local_id": "MAD-MAL", "desde": …})` es lo
   mismo que `cesta(local_id="MAD-MAL", desde=…)`. Si el modelo se deja un argumento o inventa otro
   (`tienda=...`), Python lanza `TypeError` y se convierte en un mensaje.

| Lo que hace el modelo | Lo que vuelve al modelo |
|---|---|
| Argumentos con JSON roto | `Los argumentos no son un JSON válido.` |
| Pide una herramienta que no existe | `No existe la herramienta visitas.` |
| Pide una función aún sin hacer | `La herramienta cesta todavía no está implementada.` |
| Se deja `hasta` o usa `tienda` en vez de `local_id` | `Argumentos incorrectos: cesta() missing 1 required positional argument: 'hasta'` |
| Tienda o fechas mal (lo detecta `validar`) | `local_id desconocido: …` / `Fechas no válidas…` |

**Por qué nunca lanza la excepción hacia fuera:** si `ejecutar()` rompiera el programa, la batería se
pararía. Al devolver `{"error": …}`, el error **entra en la conversación** como un mensaje `tool` más, y
en la ronda siguiente el modelo puede leerlo y **corregir su llamada**. Es lo mismo que hace el script
08 cuando devuelve al modelo el error del SQL.

⚠️ Lo que **no** puede detectar: una llamada bien formada pero con un significado equivocado (2023 en
vez de 2026, `cesta` para contar personas). Eso no es un error de Python, y por eso hay que leer la
traza.

### 7.4 `llamar_ollama()`: hablar con Ollama sin librerías

Hace un `POST` a `localhost:11434/api/chat` con `urllib` y traduce los dos fallos típicos a mensajes
útiles: **HTTP error** → «¿Has descargado el modelo? Prueba: `ollama pull …`»; **no conecta** → «¿Está
abierto? Prueba: `ollama list`». El `timeout` es de 600 s porque la primera llamada incluye cargar el
modelo en memoria.

---

## 8. La batería, los experimentos y el JSON de resultados

### 8.1 Las seis preguntas (`BATERIA`)

| # | Pregunta | Qué pone a prueba | Herramienta y argumentos esperados |
|---|---|---|---|
| 1 | Ventas netas de Eixample en A y en B | Elegir `ventas_netas` y pedir dos periodos | `ventas_netas` × 2 (A y B) |
| 2 | Pedidos de Goya en B y unidades medias | Elegir `cesta`, un solo periodo | `cesta` B |
| 3 | Qué ha cambiado en las compras de Malasaña | Pregunta abierta: ¿sabe que «compras» es `cesta`? | `cesta` × 2 |
| 4 | Pedidos de 4 o más unidades en Malasaña, A y B | Usar la métrica nueva | `cesta` × 2 |
| 5 | Netas de Malasaña del 6 al 12 de abril | Fechas que **no** son un periodo | `ventas_netas` 2026-04-06 → 2026-04-12 |
| 6 | ¿Cuántas personas visitaron Malasaña en abril? | **Pregunta imposible**: no hay datos de visitas | Ninguna; decir que no se puede |

### 8.2 Los tres experimentos

| Opción | Qué cambia en el código | Qué vigilar |
|---|---|---|
| `--descripciones-pobres` | `herramientas_pobres()` copia `TOOLS` y deja todas las descripciones en «Herramienta de datos.», quitando también las de los parámetros y el `enum`. | ¿Elige la herramienta equivocada? ¿«Responde» la pregunta 6? |
| `--sin-contexto` | `INSTRUCCIONES` se rellena con `contexto=""`: el modelo no sabe qué fechas son A y B. | ¿Inventa fechas? ¿Pregunta? |
| `--modelo llama3.2:3b` | Otro modelo, mismas herramientas. | ¿Mantiene el nivel? |

`copy.deepcopy` es necesario en `herramientas_pobres()`: sin él, al vaciar las descripciones se
modificaría también el `TOOLS` original (los diccionarios se comparten por referencia).

### 8.3 El JSON que se guarda

`bateria()` construye una **etiqueta** con el experimento y la usa para el nombre del archivo:

| Orden | Archivo |
|---|---|
| `bateria` | `resultados_base.json` |
| `bateria --sin-contexto` | `resultados_base_sin_contexto.json` |
| `bateria --descripciones-pobres` | `resultados_base_descripciones_pobres.json` |
| `bateria --modelo llama3.2:3b` | `resultados_base_llama3.2-3b.json` (los `:` y `/` se cambian por `-`) |

Cada resultado guarda `id`, `pregunta`, `llamadas` (la traza completa), `respuesta` y `segundos`. Al
final imprime un **resumen** de una línea por pregunta con las herramientas y fechas usadas, para ver
de un vistazo si los argumentos tienen sentido.

⚠️ Con `--solo 3,4` el archivo se **sobrescribe** solo con esas preguntas.

---

## 9. Lo que dicen tus ejecuciones

Revisa cada respuesta con **tres comprobaciones**: ¿eligió la **herramienta** buena? ¿con la tienda
y las **fechas** correctas? ¿lo que **responde** coincide con lo que devolvió tu código?

### 9.1 Base ([`resultados_base.json`](./resultados_base.json))

| # | Herramienta(s) y fechas | Respuesta | Tiempo | ¿Bien? |
|---|---|---|---|---|
| 1 | `ventas_netas` A y B | 24.000 € y 25.000 € | 37,3 s | ✓ |
| 2 | `cesta` B | 120 pedidos, 2,56 u/pedido | 12,7 s | ✓ |
| 3 | `cesta` A y B | 120 = 120 pedidos; 467 → 304 unidades; 3,89 → 2,53 u/pedido; 350 → 233,33 €; ≥ 4 u: 108 → 7 | 29,9 s | ✓ |
| 4 | `cesta` A y B | 108 y 7 pedidos de ≥ 4 unidades | 25,5 s | ✓ |
| 5 | `ventas_netas` 2026-04-06 → 2026-04-12 | 5.302,37 € | 13,0 s | ✓ |
| 6 | ninguna | «No puedo determinar… no hay datos sobre visitantes» | 7,0 s | ✓ |

Seis de seis: con buenas descripciones y contexto, el modelo elige bien, pide los periodos por
separado y copia las cifras sin tocarlas. La pregunta 1 tarda más porque incluye **cargar el modelo**
en memoria.

### 9.2 Sin contexto ([`resultados_base_sin_contexto.json`](./resultados_base_sin_contexto.json))

| # | Qué pidió | Qué respondió | Tipo de fallo |
|---|---|---|---|
| 1 | `ventas_netas` **ene–mar 2023** y **abr–jun 2023** | «0,00 euros» en los dos | **Error silencioso**: fechas inventadas; la función devuelve ceros sin quejarse. |
| 2 | `cesta` **abril 2023** | «Goya no registró ningún pedido» | Igual: un cero que parece un dato. |
| 3 | nada | Pide las fechas de A y B | ✓ Honesto: reconoce que le falta información. |
| 4 | `cesta` **todo 2023** y **todo 2024** | «0 pedidos de 4 o más unidades» | Error silencioso. |
| 5 | `ventas_netas` 2026-04-06 → 2026-04-12 | 5.302,37 € | ✓ La pregunta ya traía las fechas. |
| 6 | nada | «No hay herramienta para visitantes» | ✓ |

La lección: **un dato ausente no es un cero**. La herramienta respondió «0» a una pregunta sobre
fechas en las que no hay datos, y el modelo lo convirtió en una frase rotunda («no registró ningún
pedido»). Ninguna parte del sistema dio un error. Lo mismo vio el profesor en el Jetson (ver
[trazas_jetson.md](./trazas_jetson.md#experimento-2--sin-contexto)).

Para los otros dos experimentos, las trazas del aula muestran: con **descripciones pobres** la
pregunta 6 se «responde» con la herramienta de pedidos («110 personas realizaron pedidos»: un pedido
no es una persona); con **`llama3.2:3b`** aparecen «23.667 visitantes», que en realidad es un importe
en euros. *Cifra real, significado falso.*

---

## 10. El hallazgo y el reto opcional

> Esta parte es tuya: la guía te dice cómo obtener los datos y qué pensar, no la conclusión.

### 10.1 El hallazgo: pedidos de 4 o más unidades

Obtén la cifra de las tres tiendas en A y en B **sin modelo**, con tu propia herramienta:

```bash
python herramientas.py calcular cesta MAD-MAL 2026-03-02 2026-03-29
python herramientas.py calcular cesta MAD-MAL 2026-03-30 2026-04-26
# … y lo mismo con MAD-GOY y BCN-EIX
```

| Tienda | Pedidos ≥ 4 u. en A | Pedidos ≥ 4 u. en B |
|---|---|---|
| Malasaña | 108 (de tu batería) | 7 (de tu batería) |
| Goya | 44 (de `probar`) | … |
| Eixample | … | 5 (de `probar`) |

Preguntas para guiar la redacción: ¿qué tipo de compra desaparece y en qué tienda sobre todo? ¿pasa
algo parecido en las otras, o en menor medida? Recuerda que los **pedidos totales no cambian** (120 en
todas). ¿Qué dato pedirías a la empresa para entender **por qué** (algo que cambiase el 30 de marzo:
una promoción, un cambio de política, una tarifa…)? La recomendación para dirección: **4–5 frases,
con cifras y sin afirmar causas** que los datos no prueban.

### 10.2 Reto opcional: que la herramienta avise cuando no hay datos

El problema de la sección 9.2 está en que `validar()` acepta cualquier fecha bien escrita. Pistas
para resolverlo (sin modificar los CSV):

- Calcula la **primera y última `fecha_venta`** que existen (o usa las de `calendario.csv`).
- Si el rango pedido no se solapa con ellas, devuelve un `{"error": …}` que **diga qué fechas
  existen**, por ejemplo con el formato de los demás mensajes de `validar`.
- Cuidado con la venta antigua de febrero (`HIST-JOIN-001`): ¿cuenta como «hay datos» en febrero?
- Después repite `bateria --sin-contexto` y compara: ¿el modelo **se corrige solo** al leer el error
  en la siguiente ronda? Mira en la traza si hace una segunda llamada con fechas de 2026.

---

## 11. Cómo ejecutarlo

Desde **esta carpeta** (aquí se guardan los `resultados_*.json`). No necesita librerías, pero con el
`.venv` de la raíz activado funciona igual.

```bash
cd ~/ebis/07_llm_open_source/clase_01/Ejercicios/ejercicio_3
source ../../../.venv/bin/activate        # opcional
```

| Orden | Modelo | Qué hace |
|---|---|---|
| `probar` | No | Las 6 pruebas con resultado conocido. |
| `calcular HERRAMIENTA TIENDA DESDE HASTA` | No | Ejecutas tú una herramienta (`ventas_netas` o `cesta`). |
| `preguntar "…"` | Sí | Una pregunta; muestra qué pide el modelo y qué devuelve tu código. |
| `bateria` | Sí | Las 6 preguntas; guarda `resultados_<etiqueta>.json`. |

Opciones de `preguntar` y `bateria`: `--modelo NOMBRE`, `--sin-contexto`, `--descripciones-pobres` y,
solo en `bateria`, `--solo 3,4,5`.

```bash
python herramientas.py probar
python herramientas.py calcular cesta MAD-MAL 2026-03-02 2026-03-29
python herramientas.py preguntar "¿Cuántos pedidos hizo Goya en el periodo B?"
python herramientas.py bateria
python herramientas.py bateria --solo 4
python herramientas.py bateria --descripciones-pobres
python herramientas.py bateria --sin-contexto
python herramientas.py bateria --modelo llama3.2:3b
```

Para las órdenes con modelo: Ollama abierto (`ollama list` debe responder) y el modelo descargado.
Si los datos están en otro sitio: `DROPLAB_DATOS=/ruta/a/datos python herramientas.py probar`.

**Orden de trabajo recomendado:** `probar` → completar `cesta()` hasta «6 de 6» → `calcular cesta …`
→ completar `TOOLS` → `bateria` → un experimento → el hallazgo.

---

## 12. Resumen final

1. **Una herramienta = una función normal de Python** que valida sus argumentos y devuelve un
   diccionario (o `{"error": …}`).
2. **Contar bien:** pedidos = `pedido_id` distintos, líneas = filas, unidades = suma de `cantidad`;
   «pedidos de 4 o más unidades» exige agrupar por pedido primero.
3. **Dinero con `Decimal`** y redondeo explícito; fechas `YYYY-MM-DD` para poder compararlas como
   texto.
4. **La descripción es lo único que ve el modelo:** qué devuelve, cómo se define y cuándo usarla (y
   cuándo usar otra).
5. **Probar sin modelo primero** (`probar`, `calcular`): así separas fallos de cálculo de fallos del
   modelo.
6. **El bucle** limita rondas, ejecuta solo herramientas de la lista y devuelve los errores al modelo.
7. **Los errores peligrosos no dan error:** fechas de 2023 que devuelven ceros, pedidos contados como
   personas, euros leídos como visitantes.

### Preguntas para repasar

1. ¿Por qué `pedidos_4_o_mas_unidades` no se puede calcular mirando cada línea por separado?
2. ¿Qué ventaja tiene devolver `{"error": …}` en vez de lanzar una excepción?
3. ¿Por qué `ventas_netas` usa un diccionario `tienda_de_linea` en vez de unir ventas y reembolsos?
4. En el experimento sin contexto, ¿quién falla: la función, el modelo o el diseño? ¿Dónde pondrías
   la barrera?
5. Si añadieras una herramienta `stock(local_id, desde, hasta)`, ¿qué tres sitios del archivo
   tendrías que tocar y qué diría su descripción sobre los SKU que **no** se miden?
