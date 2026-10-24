# Paso 5 · Lectura: *Building effective agents* (Anthropic)

> **Artículo:** [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — Anthropic, diciembre de 2024.
> **Tiempo:** unos 20 minutos.
> **En qué fijarte (según el curso):** los cinco patrones de workflow, cuándo **no** usar agentes y el diseño de herramientas.

Esta guía te acompaña en la lectura: resume cada parte del artículo con palabras sencillas y la conecta con lo que has hecho en la sesión 1 (Lumen Shop, `agente_minimo.py`, `workflow_equivalente.py`). Léela antes o al lado del artículo, no en su lugar.

---

## 1. La idea principal en una frase

> Los equipos que mejor construyen con LLMs **no usan frameworks complicados**: usan **patrones simples que se combinan**.

Anthropic lo dice tras trabajar con decenas de equipos. El consejo de fondo es el mismo que la regla práctica de clase: **la solución más simple que funcione**. Empieza con una sola llamada al modelo bien hecha; añade complejidad solo cuando demuestres que mejora el resultado.

---

## 2. Workflows frente a agentes

El artículo agrupa todo bajo el nombre de **sistemas agénticos**, pero distingue dos tipos:

| | Workflow | Agente |
|---|---|---|
| ¿Quién decide los pasos? | **El código**, con rutas fijas | **El LLM**, de forma dinámica |
| Ventaja | Predecible y consistente | Flexible, resuelve lo imprevisto |
| Cuándo | Tareas bien definidas | Problemas abiertos, pasos imposibles de prever |

👉 En la sesión 1 lo viste en vivo: `workflow_equivalente.py` es un workflow (siempre extrae email → consulta → redacta) y `agente_minimo.py` es un agente (el modelo elige qué herramienta y cuántas veces).

---

## 3. Cuándo usar (y cuándo no) un sistema agéntico

Este es uno de los tres puntos que el curso te pide mirar con atención.

- Los sistemas agénticos **cambian latencia y coste por mejor rendimiento**. Cada vuelta del bucle es otra llamada al modelo.
- Muchas veces **basta con una sola llamada al LLM** con buenos ejemplos y contexto (o con recuperación de información, RAG).
- **Workflow** si la tarea está bien definida; **agente** si necesitas flexibilidad y que el modelo decida a escala.

👉 Conecta con la tabla de «Cuándo NO usar un agente» de la clase: proceso predecible, error muy caro, latencia crítica, auditoría estricta.

### Sobre los frameworks

El artículo menciona frameworks (como LangGraph, que verás en la sesión 3) y avisa:
- Ayudan a empezar rápido, pero **esconden** los prompts y las respuestas, y eso complica depurar.
- Tientan a añadir complejidad que no hace falta.
- Recomendación: **empieza llamando a la API directamente**; muchos patrones caben en unas pocas líneas. Si usas un framework, entiende lo que hace por debajo.

👉 Por eso la sesión 1 construye el agente "a mano" en ~80 líneas antes de pasar a LangGraph.

---

## 4. El bloque básico: el LLM aumentado

Todo se construye sobre un **LLM aumentado**: un modelo al que se le añaden

- **Recuperación** (buscar información),
- **Herramientas** (actuar y consultar sistemas),
- **Memoria** (recordar información).

Lo importante es adaptar esas capacidades a tu caso y darle al modelo una **interfaz bien documentada**. (Menciona MCP como una forma de conectar herramientas, lo que viste en el Tema 6.)

👉 En `agente_minimo.py`, el LLM aumentado es el modelo + `HERRAMIENTAS` (y la memoria se limita a la lista `mensajes`).

---

## 5. Los cinco patrones de workflow ⭐

El otro punto clave que pide el curso. Para cada uno: qué es, cuándo usarlo y el ejemplo de Lumen Shop que viste en clase.

### 5.1 Encadenamiento (*prompt chaining*)
- **Qué es:** dividir la tarea en pasos fijos; la salida de una llamada es la entrada de la siguiente. Se pueden añadir comprobaciones en código entre pasos (*gates*).
- **Cuándo:** la tarea se divide limpiamente en subtareas fijas. Cambias velocidad por precisión: cada llamada es más fácil.
- **Lumen Shop:** extraer email → buscar pedidos → redactar. Es justo `workflow_equivalente.py`.

### 5.2 Enrutado (*routing*)
- **Qué es:** un primer paso **clasifica** la entrada y la manda a un proceso especializado.
- **Cuándo:** hay categorías claras que se tratan mejor por separado. También sirve para mandar preguntas fáciles a un modelo barato y difíciles a uno potente.
- **Lumen Shop:** ¿es una reclamación, una consulta o una devolución?

### 5.3 Paralelización
- **Qué es:** varias llamadas a la vez y se juntan los resultados. Dos variantes:
  - *Sectioning*: trocear la tarea en partes independientes.
  - *Voting*: repetir la misma tarea varias veces y votar.
- **Cuándo:** para ganar velocidad, o para tener más seguridad mirando algo desde varios ángulos.
- **Lumen Shop:** revisar tono, datos y política a la vez.

### 5.4 Orquestador-trabajadores
- **Qué es:** un LLM central **reparte subtareas dinámicamente** a otros LLMs y combina sus resultados.
- **Cuándo:** no sabes de antemano qué subtareas habrá. La diferencia con la paralelización es que aquí las subtareas no están fijadas: las decide el orquestador.
- **Lumen Shop:** preparar la campaña de rebajas. (Lo verás en la sesión 5, multiagente.)

### 5.5 Evaluador-optimizador
- **Qué es:** un LLM genera y otro **evalúa y da feedback**, en bucle, hasta que se aprueba.
- **Cuándo:** hay criterios claros de evaluación y las iteraciones mejoran de verdad el resultado (como un escritor que revisa su texto).
- **Lumen Shop:** ficha de producto revisada hasta aprobarse. (En la sesión 2 harás algo parecido con el "crítico" de `reflexion.py`.)

---

## 6. Agentes

Cuando ningún patrón fijo encaja, llegan los agentes:

- Arrancan con una orden o una conversación con el humano; luego **planifican y actúan solos**.
- En cada paso necesitan **información real del entorno** (resultados de herramientas) para saber si avanzan.
- Pueden pararse a pedir ayuda al humano en puntos clave.
- Terminan al completar la tarea, pero es habitual poner **condiciones de parada**, como un máximo de iteraciones.
- Por dentro suelen ser simplemente **un LLM usando herramientas en un bucle**. Por eso el diseño de las herramientas es crucial.

**Riesgos:** más coste y **errores que se acumulan**. Recomiendan probar mucho en entornos aislados (*sandbox*) y poner protecciones.

👉 Todo esto es `agente_minimo.py`: bucle, resultados que vuelven al contexto, `max_iteraciones` como condición de parada. Y el «≈ 60 % de acierto en 10 pasos» de clase es el "los errores se acumulan" del artículo. Tu reto del Paso 3 (detectar bucles) es una de esas "protecciones".

---

## 7. Tres principios para construir agentes

El artículo cierra con tres reglas:

1. **Simplicidad**: mantén el diseño del agente lo más simple posible.
2. **Transparencia**: que se vean los pasos de planificación del agente. (Como los `[Paso N] 🔧 …` que imprime `agente_minimo.py`.)
3. **Buena interfaz agente-ordenador (ACI)**: documenta y prueba las herramientas con el mismo cuidado que una interfaz para humanos.

---

## 8. Apéndice: diseñar bien las herramientas ⭐

El tercer punto que pide el curso (y el tema de la sesión 3). Anthropic propone tratar las herramientas como una **interfaz para el modelo** (ACI), igual que diseñas interfaces para personas (HCI):

- **Ponte en el lugar del modelo:** ¿es obvio cómo usar la herramienta leyendo solo su descripción y parámetros? Si no, tampoco lo será para el modelo.
- **Escribe descripciones como para un compañero junior:** con ejemplos de uso, casos límite, formato esperado y diferencias con otras herramientas parecidas.
- **Elige formatos fáciles para el modelo:** cercanos a lo que ha visto en internet; evita que tenga que contar líneas o escapar texto.
- **Prueba cómo la usa el modelo:** lanza muchos ejemplos, mira los errores y ajusta.
- **Haz difícil equivocarse (*poka-yoke*):** cambia los parámetros para que el error sea casi imposible. Su ejemplo: exigir rutas absolutas en vez de relativas acabó con un error frecuente.

Una anécdota del artículo: al construir su agente de programación, **dedicaron más tiempo a mejorar las herramientas que el prompt general**.

### 👉 Aplícalo ya a Lumen Shop

¿Recuerdas lo que pasó en el Paso 0? El modelo llamó a `consultar_stock("proteccion solar")`, recibió un error y concluyó que no había stock (había 8). Con lo que dice el apéndice:

- La descripción de `consultar_stock` dice «Devuelve precio y unidades disponibles de un producto del catálogo». No dice que el nombre tiene que ser **exacto**, ni cuáles son los nombres válidos.
- Una descripción mejor, o aceptar nombres aproximados (*poka-yoke*), habría evitado el fallo.

Y en el Paso 2, cuando escribas la `description` de `consultar_pedido`, piensa: ¿sabrá el modelo, solo leyéndola, que el número tiene la forma `ORD-12345`?

---

## 9. Para comprobar que lo has entendido

Intenta responder sin mirar:

1. ¿Cuál es la diferencia entre un workflow y un agente, según el artículo?
2. ¿Qué diferencia hay entre *paralelización* y *orquestador-trabajadores*?
3. Nombra dos situaciones en las que **no** usarías un agente.
4. ¿Por qué Anthropic recomienda empezar sin frameworks?
5. ¿Qué es la ACI y por qué importa tanto en un agente?
6. Volviendo a los deberes: ¿pondrías el **agente** o el **workflow** en producción para responder «¿cómo van mis pedidos?»? Usa argumentos del artículo.

<details>
<summary>Ver respuestas orientativas</summary>

1. En el workflow el código fija los pasos; en el agente el LLM decide los pasos y las herramientas de forma dinámica.
2. En la paralelización las subtareas están definidas de antemano; en orquestador-trabajadores las decide el LLM orquestador según la entrada.
3. Proceso predecible, error muy caro sin supervisión, latencia crítica, auditoría estricta (o cuando basta una sola llamada bien hecha).
4. Porque los frameworks esconden prompts y respuestas, dificultan depurar y empujan a añadir complejidad innecesaria; muchos patrones caben en pocas líneas.
5. La interfaz agente-ordenador: cómo están descritas y diseñadas las herramientas. El modelo solo "ve" su descripción y parámetros, así que una herramienta mal diseñada provoca errores aunque el modelo sea bueno.
6. Orientación (es tu opinión la que cuenta): es una tarea predecible con pasos conocidos, así que el workflow es más barato, consistente y auditable. El agente solo compensaría si quieres que la misma entrada resuelva también preguntas imprevistas.
</details>
