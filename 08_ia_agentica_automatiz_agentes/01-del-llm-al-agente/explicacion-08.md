# Explicación completa — Sesión 1: Del LLM al agente, anatomía y arquitectura

Este documento explica **todo** el contenido de la sesión 1 del Tema 8 (el PDF `Tema8_Sesion1_Del_LLM_al_agente.pdf` y el código de `../tema8-agentes/sesion1/` y `../tema8-agentes/comun/`) con un lenguaje sencillo, paso a paso, y sin dar nada por sabido. Todo lo que aquí se afirma viene del PDF de la sesión, de los PDFs de la raíz (`Tema8_Trabajo_previo_a_clase.pdf`, `Tema8_Deberes_y_lecturas.pdf`) o del código real. Cuando se usa un ejemplo propio para aclarar un concepto, se dice explícitamente que es un ejemplo ilustrativo.

---

## 0. Mapa del tema: seis sesiones, un mismo sistema

El Tema 8 no son seis temas sueltos: es **un único proyecto que crece**. En cada sesión se añade una capa al mismo agente:

| Sesión | Bloque | Qué se añade |
|---|---|---|
| 1 | Agente | Un agente desde cero (esta sesión) |
| 2 | Planificar | ReAct y patrones de planificación |
| 3 | Herramientas | LangGraph, APIs externas y MCP |
| 4 | Memoria | Contexto, memoria y estado |
| 5 | Equipos | Sistemas multiagente |
| 6 | Producción | Integración en la empresa |

### El caso conductor: Lumen Shop

Lumen Shop es una tienda online de cosmética **ficticia**, elegida porque tiene los problemas de cualquier e-commerce. El PDF la divide en cuatro áreas:

- **Catálogo y stock**: productos, precios y unidades disponibles.
- **Pedidos**: estado, importe y número de seguimiento.
- **Transportista**: una API externa *que a veces no responde*.
- **Clientes**: tickets de soporte, incidencias y reembolsos.

En el código, todo esto vive en `comun/tienda.py` como diccionarios fijos (en un sistema real serían llamadas a Shopify, al ERP o al CRM). Por ejemplo:

- Productos: `serum vitamina c` (24,90 €, 132 uds), `crema hidratante` (19,50 €, **0 uds**), `protector solar spf50` (15,90 €, **8 uds**), `contorno de ojos` (21 €, 47 uds).
- Clientes: `marta.lopez@email.com` (pedidos `ORD-10231` y `ORD-10544`) y `jorge.ruiz@email.com` (`ORD-10598`).
- Pedidos: `ORD-10544` está "en tránsito" con seguimiento `TRK-58873`.
- **`consultar_transportista` siempre falla** con `ConnectionError("Timeout: ...")`. Es deliberado: sirve para ver en clase qué hace un agente cuando una herramienta está caída.

---

## 1. Lo que ya sabíamos del Tema 6 (repaso)

La sesión arranca recordando tres conceptos del Tema 6 (`../../06_mcp/`), que ahora se van a construir "por dentro":

- **Agente**: el LLM decide qué pasos dar, con qué herramienta y cuándo ha terminado.
- **Tool calling**: el modelo *pide* una herramienta; el *código* la ejecuta y le devuelve el resultado. El modelo nunca ejecuta nada por sí mismo.
- **MCP**: un protocolo estándar para servir herramientas a cualquier agente (se retoma en la sesión 3).

---

## 2. ¿Agente o workflow? La distinción central de la sesión

Esta es la idea más importante de la sesión (y de la lectura recomendada, *Building effective agents* de Anthropic):

> En un **workflow** el código fija los pasos; en un **agente** los decide el LLM.

En un workflow el LLM se usa como una pieza más dentro de un guion que ha escrito un programador: "primero extrae esto, luego consulta aquello, luego redacta". En un agente, el programador da al LLM un objetivo y un conjunto de herramientas, y es el LLM quien decide, en cada vuelta, qué hacer.

### Los cinco patrones de workflow

El PDF presenta cinco patrones clásicos (los de la lectura de Anthropic), cada uno aterrizado en Lumen Shop:

| Patrón | Qué es | En Lumen Shop |
|---|---|---|
| **Encadenamiento** (*prompt chaining*) | La salida de una llamada al LLM es la entrada de la siguiente, en orden fijo. | Extraer email → buscar pedidos → redactar respuesta. |
| **Enrutado** (*routing*) | Un primer paso clasifica la entrada y la manda a un camino especializado. | ¿Es una reclamación, una consulta o una devolución? |
| **Paralelización** | Varias llamadas a la vez sobre la misma entrada, y se combinan resultados. | Revisar tono, datos y política a la vez. |
| **Orquestador-trabajadores** | Un LLM reparte subtareas a otros y junta el resultado. | Preparar la campaña de rebajas. |
| **Evaluador-optimizador** | Un LLM genera y otro evalúa, en bucle, hasta que se aprueba. | Ficha de producto revisada hasta aprobarse. |

Mensaje del PDF: **muchos problemas se resuelven con uno de estos patrones, sin necesidad de agente.**

---

## 3. El bucle agéntico

Un agente, en el fondo, es un bucle con tres fases:

1. **Observar**: el mensaje del usuario + todo el contexto acumulado.
2. **Razonar**: ¿qué necesito? ¿he terminado?
3. **Actuar**: llamar a una herramienta. El **resultado vuelve al contexto** y se repite.

Y el bucle tiene que parar. El PDF da cuatro **condiciones de parada**:

- **Respuesta final**: el modelo ya no pide herramientas.
- **Límite de pasos**: el código corta tras N vueltas.
- **Presupuesto agotado**: tokens o dinero.
- **Error irrecuperable**.

Importante: las dos primeras las pone **el código**, no el modelo. Un agente sin límite de pasos puede quedarse dando vueltas para siempre.

### El bucle en una traza real

El PDF muestra la salida real de `agente_minimo.py` ante «Quiero 10 sérums y 10 protectores, ¿hay suficientes?»:

```
[Paso 1] consultar_stock("serum vitamina c")      → {"stock": 132, ...}
[Paso 1] consultar_stock("protector solar spf50") → {"stock": 8, ...}
✅ Respuesta final (paso 2, 1.180 tokens)
Hay sérums de sobra, pero solo quedan 8 protectores. ¿Te envío esos 8?
```

Tres cosas a observar:
1. **Dos herramientas en el mismo paso**: lo decide el modelo (llamadas en paralelo).
2. **Los resultados vuelven al contexto** y en el paso 2 el modelo ya puede responder.
3. **Nadie programó la comparación "10 frente a 8"**: el modelo la hace solo. Esta es la gracia de un agente.

---

## 4. El código: `sesion1/agente_minimo.py`, línea a línea

El fichero tiene cuatro piezas, que el PDF numera:

### 4.1 Instrucciones (el *system prompt*)

```python
INSTRUCCIONES = (
    "Eres el agente de atención al cliente de Lumen Shop, una tienda online de cosmética. "
    "Usa las herramientas para consultar datos; nunca inventes stock, pedidos ni clientes. "
    "Responde en español, de forma breve y amable."
)
```

Define rol, objetivo y límites. La frase «nunca inventes stock, pedidos ni clientes» es protagonista de una demo (ver §5).

### 4.2 Herramientas: lo que el modelo *ve* y lo que el código *ejecuta*

Cada herramienta existe por duplicado:

- En **`HERRAMIENTAS`**: un esquema JSON (nombre, descripción, parámetros). Es **lo único que ve el modelo**. Por eso la descripción importa tanto: es lo que el modelo lee para decidir si usarla.
- En **`FUNCIONES`**: un diccionario `nombre → función Python real` (`tienda.consultar_stock`, `tienda.buscar_cliente`, `tienda.consultar_transportista`). Es lo que se ejecuta de verdad.

El modelo nunca toca `FUNCIONES`; solo devuelve "quiero llamar a `consultar_stock` con `{"producto": "..."}`" y el código hace el resto.

### 4.3 `ejecutar_herramienta`: ejecutar y devolver el error al modelo

```python
try:
    resultado = funciones[nombre](**json.loads(argumentos or "{}"))
except Exception as e:  # el error vuelve al modelo para que decida qué hacer
    resultado = {"error": f"{type(e).__name__}: {e}"}
return json.dumps(resultado, ensure_ascii=False)
```

Detalle clave: si la herramienta falla (como el transportista), **el programa no se rompe**: el error se convierte en texto y se le devuelve al modelo, que decide qué hacer (reintentar, disculparse, pedir otro dato...).

### 4.4 El bucle `ejecutar_agente`

Simplificado (versión del PDF):

```python
for paso in range(max_iteraciones):
    respuesta = llm(mensajes, tools=HERRAMIENTAS)
    if not respuesta.tool_calls:
        return respuesta.content          # ha terminado
    for llamada in respuesta.tool_calls:
        resultado = ejecutar(llamada)
        mensajes.append(resultado)         # vuelve al contexto
```

En el código real:
- `mensajes` empieza con el `system` (instrucciones) y el `user` (pregunta).
- En cada paso se llama a `cliente.chat.completions.create(model=MODELO, messages=mensajes, tools=herramientas)` y se suman los tokens consumidos.
- Si el modelo pide herramientas, se añade su mensaje `assistant` con los `tool_calls` y, por cada llamada, un mensaje `role: "tool"` con el `tool_call_id` y el resultado.
- Si se agota `max_iteraciones` (8 por defecto, configurable con `--max-iter`), devuelve «No he podido completar la consulta. Te paso con un compañero del equipo.» — es decir, **escala a un humano** en vez de inventar.

### 4.5 La conexión con el modelo: `comun/llm.py`

`crear_cliente()` devuelve un cliente `OpenAI(base_url=..., api_key=...)` configurado desde `.env`. Por defecto apunta a **Ollama local** (`http://localhost:11434/v1`, modelo `qwen2.5:7b`). Como Ollama y muchos proveedores en la nube hablan la misma API compatible con OpenAI, cambiar de modelo es **editar `.env`, no el código**.

### Cómo probarlo

Desde `tema8-agentes/`:

```bash
python -m sesion1.agente_minimo "¿Hay stock de crema hidratante?"
python -m sesion1.agente_minimo "Soy marta.lopez@email.com, ¿qué pedidos tengo?"
python -m sesion1.agente_minimo "Quiero 10 sérums de vitamina C y 10 protectores solares, ¿hay suficientes?"
```

Qué observar (según el PDF): quién decide llamar a cada herramienta, cuántos pasos da y por qué, y que nadie programó la comparación.

---

## 5. Demo: el poder de una frase

Experimento en directo:

- **Con la instrucción** «Nunca inventes stock, pedidos ni clientes», a la pregunta «¿tenéis champú?» el agente consulta el catálogo y responde que no existe (la herramienta devuelve `error` + lista de `productos_disponibles`).
- **Sin la instrucción** (se borra esa frase), con la misma pregunta, **con frecuencia se inventa un precio o una respuesta**.

Conclusión del PDF: *el comportamiento varía entre modelos: las instrucciones importan.* Una sola frase en el prompt cambia si el agente alucina o no.

---

## 6. Actividad: ¿agente, workflow o ninguno?

El PDF propone seis casos para clasificar (sin dar la solución en las diapositivas):

1. Responder «¿dónde está mi pedido?»
2. Clasificar las facturas que llegan al buzón
3. Investigar a un competidor y resumir su oferta
4. Resolver incidencias de IT de primer nivel
5. Traducir 2.000 fichas de producto
6. Gestionar la devolución de un pedido dañado

*Orientación ilustrativa (no viene en el PDF, aplicando sus criterios):* lo que tiene pasos conocidos y repetitivos (1, 2, 5) encaja mejor en un workflow; lo abierto, donde no se sabe de antemano qué habrá que consultar (3, 4), encaja en un agente; y lo que implica dinero (6) probablemente pide agente o workflow **con aprobación humana**.

---

## 7. Los componentes de un agente

| Componente | Qué es |
|---|---|
| **Modelo** | Razona y decide. Determina la calidad, el coste y la latencia. |
| **Instrucciones** | Rol, objetivos y límites: lo que debe y lo que no debe hacer. |
| **Herramientas** | "Las manos": consultar sistemas y actuar sobre ellos. |
| **Memoria y estado** | Lo que sabe de esta conversación y de las anteriores (sesión 4). |
| **Orquestador** | El bucle de control: cuándo seguir, cuándo parar, qué permitir. |

En `agente_minimo.py`: el modelo es `MODELO` (vía `crear_cliente`), las instrucciones `INSTRUCCIONES`, las herramientas `HERRAMIENTAS`+`FUNCIONES`, la memoria es solo la lista `mensajes` de esta conversación, y el orquestador es el `for` con `max_iteraciones`.

---

## 8. Niveles de autonomía

De menos a más autonomía (y, según el PDF, **más autonomía = más riesgo**):

1. **Sugiere**: el agente propone; el humano decide y ejecuta.
2. **Ejecuta con aprobación**: el humano aprueba cada acción sensible.
3. **Autónomo supervisado**: actúa solo; el humano revisa después.
4. **Autónomo**: sin intervención humana.

La mayoría de agentes en empresa hoy están en los **niveles 2 y 3**.

---

## 9. Los errores se multiplican

Si cada paso acierta el 95 % de las veces, una tarea de 10 pasos acierta:

```
0,95 × 0,95 × … (10 veces) ≈ 0,60  →  ≈ 60 %
```

Por eso:
- Cada paso extra es una oportunidad de fallo.
- **La fiabilidad es el problema central de los agentes.**
- Menos pasos y mejores herramientas suben el acierto.

---

## 10. Cuándo NO usar un agente

| Situación | Por qué no |
|---|---|
| **Proceso predecible** | Si los pasos se conocen de antemano, un workflow es más fiable y barato. |
| **Error muy caro** | Pagos, contratos o datos sensibles sin supervisión humana. |
| **Latencia crítica** | Cada vuelta del bucle es una llamada al modelo. |
| **Auditoría estricta** | Si cada decisión debe ser explicable y repetible. |

Regla práctica del PDF: **la solución más simple que funcione.**

---

## 11. El código: `sesion1/workflow_equivalente.py`

La misma necesidad («¿cómo van mis pedidos?») resuelta como **workflow de encadenamiento**. Aquí el código decide los pasos y el modelo solo hace dos tareas concretas:

1. **El modelo extrae un dato**: se le pide «Extrae el email del mensaje. Responde solo con el email o con NINGUNO.». Si responde `NINGUNO`, el código contesta pidiendo el email.
2. **El código consulta los sistemas, siempre igual**: `tienda.buscar_cliente(email)` y luego `tienda.obtener_pedido(p)` para cada pedido. Si el cliente no existe, el código responde directamente.
3. **El modelo redacta** una respuesta breve usando *solo* esos datos.

Siempre son **dos llamadas al modelo, siempre en el mismo orden**. Más predecible, más barato y más fácil de auditar... pero **solo sabe resolver esta tarea**: si le preguntas por stock, no sabe.

```bash
python -m sesion1.workflow_equivalente "Hola, soy marta.lopez@email.com, ¿cómo van mis pedidos?"
```

Qué observar según el PDF: el workflow da siempre el mismo número de pasos; el agente, un número variable; y qué pasa si se pregunta otra cosa a cada uno.

---

## 12. Demo: romper el agente

```bash
python -m sesion1.agente_minimo --max-iter 20 "¿Dónde está mi envío TRK-58873? Insiste hasta que funcione."
python -m sesion1.agente_minimo "¿Dónde está mi envío TRK-58873?"
```

Como `consultar_transportista` siempre lanza un timeout, el agente recibe el error una y otra vez. Con «insiste» en el mensaje, tiende a reintentar hasta agotar el límite, gastando tokens en cada vuelta. Al quitar «insiste», suele rendirse antes y explicar el problema. Qué observar: cuántas veces reintenta, cuántos tokens gasta y qué cambia al quitar la palabra.

Lección: **el límite de pasos del código es lo único que garantiza que el agente pare.**

### Resumen: workflow frente a agente

| Workflow | Agente |
|---|---|
| Pasos fijos y predecibles | Pasos decididos por el modelo |
| Coste conocido | Coste variable |
| Fácil de auditar | Resuelve lo imprevisto |
| Solo resuelve lo previsto | Necesita límites en el código |

Lo habitual: **lo predecible a workflows, lo abierto a un agente.**

---

## 13. Actividad: ¿qué ha fallado?

Cuatro trazas reales para diagnosticar. Pista del PDF: *¿modelo, instrucciones, herramienta o bucle?*

1. Llama 20 veces a la misma API caída hasta agotar el límite.
2. Responde un precio sin haber consultado el catálogo.
3. Llama a `buscar_cliente` con el nombre en lugar del email.
4. Termina sin responder a la segunda pregunta del cliente.

*Diagnóstico ilustrativo (no viene en el PDF):* (1) bucle/orquestador — falta detectar reintentos repetidos (es justo el reto de los deberes); (2) instrucciones — falta o no se respeta «nunca inventes»; (3) herramienta — la descripción/esquema no deja claro que el parámetro es un email; (4) modelo o instrucciones — no se le pide que compruebe que ha respondido a todo.

---

## 14. Caso real: Klarna

- **2024 · El anuncio**: su asistente de IA gestiona dos tercios de los chats de atención al cliente en su primer mes.
- **La promesa**: resolución más rápida y el trabajo equivalente a cientos de agentes humanos.
- **2025 · El ajuste**: vuelve a reforzar la atención humana: la calidad importaba más que el coste.
- **La lección**: automatizar lo predecible y dejar a las personas lo que requiere criterio.

### Dónde encaja un agente en un e-commerce

Cuatro usos que se construirán en las próximas sesiones:
- **Soporte de primer nivel**: estado de pedidos, stock, cambios de dirección.
- **Incidencias logísticas**: retrasos y envíos perdidos, cruzando transportista y pedido.
- **Catálogo**: fichas, traducciones y atributos, con revisión humana.
- **Reembolsos**: propuesta automática, aprobación humana.

---

## 15. Deberes y lectura (para la sesión 2)

No evaluables; se comentan al inicio de la sesión 2. Punto de partida: `sesion1/agente_minimo.py`.

**Nivel base · Añade una herramienta.** El agente no puede consultar un pedido por su número. Crea `consultar_pedido` usando `tienda.obtener_pedido` (ya existe). Pista: una entrada en `HERRAMIENTAS` (lo que ve el modelo) y otra en `FUNCIONES` (lo que se ejecuta); **el bucle no cambia**. Prueba: «¿En qué estado está el pedido ORD-10544?» (debería responder "en tránsito").

**Reto · Detecta bucles.** Si una herramienta se llama más de dos veces con los mismos argumentos, el agente debe dejar de intentarlo y explicar al cliente qué ocurre. Pista: **no hace falta tocar el bucle** (*ilustrativo:* se puede hacer dentro de la función que ejecuta herramientas o envolviendo las funciones, devolviendo al modelo un error que le diga que deje de reintentar).

**Para pensar:** ¿pondrías en producción el agente o el workflow para responder «¿cómo van mis pedidos?», y por qué?

**Lectura:** *Building effective agents* (Anthropic, diciembre 2024) — https://www.anthropic.com/engineering/building-effective-agents. Fíjate en: los cinco patrones de workflow, cuándo no usar agentes y el diseño de herramientas (se ve en la sesión 3).

**Antes de la sesión 1** (según `Tema8_Trabajo_previo_a_clase.pdf`, ≈ 50 min): instalar el entorno con `GUIA_INSTALACION.md` (Python ≥ 3.10, entorno virtual, dependencias, Ollama con `qwen2.5:7b`), comprobar con `python comprobar_entorno.py` hasta ver «Todo listo para el Tema 8», y leer el artículo de Anthropic. Opcional: descargar `nomic-embed-text` para la sesión 4.
