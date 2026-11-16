# Humano en el bucle: un equipo de agentes que delega en una persona

Explicación sencilla del material complementario «Un equipo de agentes que delega en una persona». Se construye a partir del PDF (`Demo_humano_en_el_bucle.pdf`, 5 diapositivas), del `README.md` y del código de `humano-en-el-bucle/`. Los ejemplos propios van marcados como *ilustrativos*. Los resultados «en mi máquina» son de ejecutar las cuatro demos con `qwen3:4b-instruct` en local (16-11-2026): el material usa `qwen2.5:7b`, así que con otro modelo saldrán otros resultados.

Es material del **Tema 8** (sistemas multiagente), pero encaja con la sesión 2 del Tema 9: es el paso **«derivar a una persona»** que veíamos en los guardarraíles y en el caso Air Canada, hecho de verdad.

---

## 0. La idea en una frase

> **Una persona forma parte del equipo de agentes.** Cuando los agentes llegan a algo que no pueden o no deben hacer solos, **le delegan una tarea, se paran sin perder nada** y, cuando ella termina, **el mismo equipo sigue** donde lo dejó, con lo que ella ha aportado.

Hasta ahora, «pasar a una persona» era el **final** del proceso: el agente escala y ahí acaba. Aquí no: la persona hace su parte y el trabajo **vuelve** a los agentes.

### Dónde encaja

| Ya lo habíamos visto | Lo nuevo aquí |
|---|---|
| Tema 8, sesión 5: un equipo de agentes con un **supervisor** que decide quién trabaja | Uno de los miembros del equipo **es una persona** |
| Tema 8, sesión 6: los patrones de humano en el bucle (aprobar, editar, revisar, escalar) | El equipo **espera horas o días** a la persona y luego **retoma** el trabajo solo |
| Tema 9, sesión 2: «por encima del límite, una persona»; «ante dudas sobre dinero, derivar» | Cómo se hace eso sin que el equipo pierda lo que llevaba hecho |

### ¿Se usa esto en empresa?

El README lo dice claro: **todavía es poco habitual**. Lo normal es derivar a una persona por email o teléfono y que el proceso acabe ahí. Pero en startups y pymes, donde una sola persona supervisa mucho trabajo automatizado, que los agentes esperen su decisión y sigan solos ahorra mucho tiempo. La demo combina las dos cosas: la persona recibe un **email** (simulado) con el enlace a su **bandeja**.

---

## 1. El caso: Faro Digital

**Faro Digital** es una agencia de marketing para pymes (inventada). Su equipo prepara campañas de publicidad para los clientes.

### 1.1 El equipo

| Miembro | Qué hace |
|---|---|
| **Supervisor** | Decide quién trabaja ahora (como en la sesión 5 del Tema 8). Es un modelo de lenguaje |
| **Estratega** | Prepara el **plan de medios**: en qué canales anunciarse y cuánto gastar en cada uno. Usa herramientas: ficha del cliente, tarifas y alcance estimado |
| **Persona** | **Laura Méndez, responsable de cuenta.** No es un agente: es una persona de verdad. Aprueba los planes de más de 1.000 € y consigue del cliente los datos que faltan |
| **Redactor** | Escribe los anuncios **solo con los datos confirmados** |

> **Todos vuelven al supervisor, también la persona.**

```
encargo ─► supervisor ─┬─► estratega ──┐
              ▲        ├─► redactor ───┤
              │        ├─► persona ────┤   ⏸️ aquí el equipo se para hasta que ella responde
              │        └─► entregar ─► propuesta final
              └────────────────────────┘
```

### 1.2 Las dos tareas que se le delegan a la persona

| Tipo | Cuándo | Qué puede hacer ella |
|---|---|---|
| **Decidir** | El plan supera los **1.000 €** que el equipo puede gastar sin permiso | Aprobarlo, aprobar **otro presupuesto máximo** o **rechazarlo** con un comentario |
| **Aportar datos** | Falta algo que **solo sabe el cliente** (precio, fechas, fotos…) | Confirmarlo con el cliente y escribirlo. Puede dejar alguno sin responder |

La primera es una **decisión** (dinero). La segunda es **información** que ningún agente puede averiguar con sus herramientas: hay que llamar al cliente.

### 1.3 Los clientes de la demo

| Cliente | Encargo | Presupuesto | Qué le pasará |
|---|---|---|---|
| **Obrador Espiga** (panadería, Valencia) | Lanzar su primer roscón de Reyes sin gluten | Unos 1.500 € | Necesita **aprobación** y **datos** (precio, fecha de reservas, fotos) |
| **Taller Radios** (bicicletas, Bilbao) | Llenar la agenda de revisiones en enero | 600 € | No pasa del límite: **solo datos** (descuento y fechas) |

---

## 2. Las dos piezas que hacen falta

### 2.1 Pararse sin perder nada

Para que el equipo pueda esperar a una persona **horas o días**, dos cosas:

1. **Un punto de pausa.** Cuando le toca a la persona, el equipo se detiene (en LangGraph, con `interrupt()`). El programa puede **terminar** del todo.
2. **Un sitio donde guardar el trabajo.** Todo lo que lleva hecho el equipo (el plan, la aprobación, los datos, quién ha hecho qué) se guarda en una base de datos (`datos/faro.sqlite`) después de **cada paso**. A cada una de esas fotos del estado se le llama *checkpoint*.

Cuando la persona responde, se carga el estado guardado **de ese encargo** y el mismo equipo sigue justo donde se quedó. Cada encargo (`ENC-001`, `ENC-002`…) tiene su propio estado: así no se mezclan.

El nodo de la persona, en esencia (`faro/equipo.py`):

```python
def persona(estado):
    tarea = preparar_tarea(estado)    # lo que verá la persona en su bandeja
    respuesta = interrupt(tarea)      # ⏸️ aquí se detiene y se guarda el estado
    ...                               # al reanudar, interrupt() devuelve la respuesta
```

### 2.2 Reglas que el supervisor no se puede saltar

El supervisor es un modelo: **propone** quién trabaja. Pero antes de hacerle caso, el código aplica unas reglas (`aplicar_reglas`):

| Regla | Qué impide |
|---|---|
| Un plan de **más de 1.000 €** necesita aprobación | Entregar un plan caro sin que nadie lo vea |
| Si la persona **rechaza** o aprueba **menos dinero**, el estratega rehace el plan | Seguir adelante con un plan que no está aprobado |
| **No se redacta sin los datos** del cliente | Anuncios con precios o fechas inventados |
| Si el plan ya está hecho y nadie ha pedido cambios, **no se rehace** | Que el equipo dé vueltas gastando tokens |
| Dos rechazos → **se cierra el encargo** sin campaña | Discutir con la persona para siempre |
| Más de 24 pasos → se entrega | Bucles infinitos entre agentes |

Si el supervisor propone otra cosa, la regla lo corrige y queda apuntado: «→ persona (proponía estratega; regla: el plan supera 1.000 € y tiene que aprobarlo una persona)».

> **Los agentes deciden; las reglas importantes, en código.**

Es la misma idea de la sesión 2 del Tema 9: **lo que no debe pasar se impide en el código, no se pide en el prompt**. El prompt del supervisor también dice que Laura aprueba lo de más de 1.000 €, pero lo que lo garantiza es el `if`.

---

## 3. Demo 1: delegar y esperar (`01_delegar.py`)

Encarga la campaña de Obrador Espiga. El equipo trabaja hasta que necesita a Laura, le **manda un email** (simulado, en la carpeta `buzon/`) y **el programa termina**.

En mi máquina:

```
🧭 supervisor: → estratega: Debo preparar o rehacer el plan de medios y el presupuesto…
📊 estratega: Plan v1: instagram_ads 600 €, google_ads_local 600 €, tiktok_ads 300 € · total 1.500 €
🧭 supervisor: → persona (proponía estratega; regla: el plan supera 1.000 € y tiene que aprobarlo una persona)
⏸️  El equipo espera a Laura Méndez: Aprobar el plan v1 (1.500 €)
```

Lo que se ve:

- **El supervisor quería volver a llamar al estratega**, y la regla lo corrigió: el plan pasa de 1.000 € y tiene que verlo una persona. Sin la regla, el modelo pequeño habría seguido rehaciendo el plan.
- **El programa termina, pero el trabajo no se pierde**: el plan v1 está guardado y Laura tiene un email:

```
Para: laura@farodigital.test
Asunto: [Faro] Aprobar el plan v1 (1.500 €) · ENC-001

El plan supera los 1.000 € que el equipo puede decidir solo. Apruébalo, apruébalo con otro
presupuesto máximo o recházalo con un comentario para el estratega.

Respóndela en la bandeja: http://127.0.0.1:8000/encargo/ENC-001
```

---

## 4. Demo 2: la bandeja de la persona (`02_bandeja.py`)

Una página web local (<http://127.0.0.1:8000>) donde Laura ve las tareas que le ha dejado el equipo y las completa. Al responder, **el mismo equipo continúa en segundo plano**, y en la terminal se ve lo que hace. La página se actualiza sola mientras el equipo trabaja.

### 4.1 En mi máquina: Obrador Espiga de principio a fin

**1. Laura aprueba otro presupuesto**: «Aprobar con otro presupuesto máximo», 1.200 €, comentario «El cliente no quiere pasar de 1.200 €».

```
🙋 Laura Méndez: aprueba un máximo de 1.200 €. El cliente no quiere pasar de 1.200 €
🧭 supervisor: → estratega: El plan v1 debe modificarse para respetar el límite de 1.200 €…
📊 estratega: Plan v2: instagram_ads 600 €, google_ads_local 500 €, tiktok_ads 100 € · total 1.200 €
🧭 supervisor: → persona (proponía estratega; regla: el plan ya está hecho y nadie ha pedido cambios)
⏸️  El equipo espera a Laura Méndez: Confirmar con el cliente los datos que faltan
```

El equipo rehizo el plan **sin pasar de 1.200 €**. Como ya está aprobado, ahora no pide aprobación: pide los **datos**. Otra vez el supervisor quería al estratega y la regla lo corrigió.

**2. Laura aporta los datos**: precio 24,50 €, reservas desde el 1 de diciembre, y deja **vacío** el enlace a las fotos.

```
🙋 Laura Méndez: aporta 2 de 3 datos del cliente
🧭 supervisor: → redactor (proponía estratega; regla: el plan ya está hecho y nadie ha pedido cambios)
✍️  redactor: Textos escritos para 3 canales
🧭 supervisor: → entregar: plan y textos listos
📦 entregar: Propuesta terminada
✅ Encargo terminado. Propuesta en entregas/ENC-001.md
```

**3. La propuesta** (`entregas/ENC-001.md`) lleva el plan, quién lo aprobó y con qué máximo, los datos confirmados (las fotos, «(sin confirmar)») y los textos. Un anuncio:

> **Google Ads Local** · Reserva tu roscón de Reyes sin gluten de Obrador Espiga – Desde el 1 de diciembre. Precio: 24,50 €. Reserva antes del 5 de enero. 📞 Llama al 960 000 111 o visita obradorespiga.test para más info.

Usa **solo** lo que confirmó Laura (precio y fecha) y el contacto real del cliente. No menciona las fotos ni deja huecos como «[enlace a las fotos]».

### 4.2 Lo que se aprende

- **La regla corrigió al supervisor tres veces** en este encargo. Las tres, el modelo quería volver al estratega. Si el orden lo decidiera solo el modelo, el equipo daría vueltas.
- **El dato que falta no se inventa.** Laura dejó vacías las fotos y el redactor no las nombra. El README cuenta que con `qwen2.5:7b` el redactor dejaba huecos de relleno («Visítanos en [enlace a la página de Instagram]»): ahora recibe el contacto real del cliente, se le pide que quite los huecos y, si insiste, **el código los borra**. Lo que llega al cliente no depende de que el modelo obedezca.
- **Hay una cosa que ninguna regla mira**: el plan v2 pone **100 € en TikTok**, y el mínimo de ese canal es **200 €**. El estratega se lo saltó y el código no lo comprueba (solo mira que el canal exista). Una regla más que podría ir en código.

### 4.3 Lo que muestran las diapositivas

En la ejecución del curso (con `qwen2.5:7b`) pasó algo distinto: **Laura aprobó 1.200 € y el estratega propuso un plan v2 de 1.600 €**. La regla lo detectó y **volvió a preguntarle**. Funciona, pero molesta a la persona por un error del agente. Por eso el código actual (marcado con 🐞 en `faro/equipo.py`) **suma los importes él mismo** y, si se pasan del máximo aprobado, le pide al estratega que corrija (hasta dos veces) **antes** de molestar a nadie. En mi máquina el plan v2 salió justo en 1.200 €.

### 4.4 Taller Radios: sin aprobación

Lo creé desde la bandeja. En mi máquina:

```
📊 estratega: Plan v1: instagram_ads 300 €, facebook_ads 200 €, google_ads_local 150 € · total 650 €
🧭 supervisor: → persona (proponía estratega; regla: el plan ya está hecho y nadie ha pedido cambios)
⏸️  El equipo espera a Laura Méndez: Confirmar con el cliente los datos que faltan
```

Como no pasa de 1.000 €, **no pide aprobación**: solo los datos (descuento del 20 % y fechas del 8 al 31 de enero). Después redacta y entrega con «Aprobación: no hacía falta».

Pero fíjate: el cliente dijo **600 €** y el plan es de **650 €**. Ninguna regla compara el plan con el presupuesto del cliente: solo con el límite de 1.000 €. Es justo lo que plantea el ejercicio 1 (sección 7).

---

## 5. Demo 3: qué ha pasado por dentro (`03_historial.py`)

Saca de los estados guardados la **línea temporal** de un encargo: quién ha trabajado, cuánto ha tardado y cuánto ha esperado el equipo a la persona.

`python 03_historial.py ENC-001 --checkpoints`, en mi máquina (recortado):

```
  19:23:11  +    49 s  🤖 estratega: Plan v1: … · total 1.500 €
  19:23:30  +    10 s  🙋 Laura Méndez: aprueba un máximo de 1.200 €…
  19:24:42  +    61 s  🤖 estratega: Plan v2: … · total 1.200 €
  19:25:07  +    14 s  🙋 Laura Méndez: aporta 2 de 3 datos del cliente
  19:25:53  +    37 s  🤖 redactor: Textos escritos para 3 canales

⏱️  Trabajo de los agentes: 187 s · Espera a la persona: 24 s
🔢 Tokens por agente: {'supervisor': 2316, 'redactor': 868, 'estratega': 7784} · total 10968

💾 14 estados guardados:
  [ 4] siguiente: persona    ⏸️ esperando a la persona
  [ 8] siguiente: persona    ⏸️ esperando a la persona
```

Lo que se ve:

- **Cada paso queda guardado** (14 estados), y en dos de ellos el equipo estaba **parado esperando a Laura**. Desde cualquiera de esos estados se podría reanudar.
- **El estratega es el que más gasta** (unos 7.800 de 11.000 tokens): es el que usa herramientas y lo hizo dos veces.
- **La espera a la persona sale muy baja (24 s)** porque yo respondí al momento. En la vida real serían **horas**: lo normal es que la espera humana sea, con mucho, la mayor parte del tiempo total. Es lo que pide medir el ejercicio 4.

---

## 6. Demo 4: ¿y si la persona no responde? (`04_plazos.py`)

Un equipo que espera a una persona **puede quedarse parado días**. Este script es lo que en una empresa se ejecutaría **cada hora** (una tarea programada) con dos plazos:

| Tiempo esperando | Qué hace |
|---|---|
| Más de **4 horas** | Un **recordatorio** a la persona (solo uno) |
| Más de **24 horas** | **Escala** la tarea a **Carmen Ibáñez, directora de cuentas**, y le manda un email |

Para no esperar horas de verdad, `--dentro-de` simula que ha pasado ese tiempo. Dejé un segundo encargo (ENC-002) sin responder. En mi máquina:

```
--dentro-de 0   ENC-002 · Laura Méndez · esperando 0.0 h    ✔️  Dentro de plazo
--dentro-de 5   ENC-002 · Laura Méndez · esperando 5.0 h    🔔 Recordatorio enviado a Laura Méndez
--dentro-de 6   ENC-002 · Laura Méndez · esperando 6.0 h    ✔️  Dentro de plazo
--dentro-de 26  ENC-002 · Laura Méndez · esperando 26.0 h   ⬆️  Escalada a Carmen Ibáñez
--dentro-de 27  ENC-002 · Carmen Ibáñez · esperando 27.0 h  ✔️  Dentro de plazo
```

Y en el buzón, tres emails: el aviso a Laura, el recordatorio («La tarea sigue pendiente y el equipo de agentes está parado esperándote») y el de Carmen («Te llega porque la persona asignada no ha respondido a tiempo»).

> **Tras 26 horas simuladas, la tarea pasa a Carmen con el estado intacto.**

Lo importante: **escalar no rehace nada**. El plan v1, el historial y todo lo demás siguen ahí; solo cambia **quién** tiene que responder. En la bandeja, la tarea aparece ahora «para Carmen Ibáñez (Directora de cuentas)».

**Un detalle que vi al probarlo**: después de escalar, a las 27 h sale «dentro de plazo». A Carmen no se le manda recordatorio ni se escala a nadie más. Si Carmen tampoco responde, el encargo se queda parado para siempre. En una empresa habría que decidir qué pasa entonces.

### 6.1 Carmen rechaza el plan

Para cerrar el ciclo, respondí como Carmen **rechazando** el plan con un comentario: «Nada de TikTok: el público del roscón son familias». En mi máquina:

```
🙋 Carmen Ibáñez: rechaza el plan. Nada de TikTok: el público del roscón son familias
🧭 supervisor: → estratega: Debo rehacer el plan de medios considerando que el cliente rechazó TikTok…
📊 estratega: Plan v2: instagram_ads 600 €, google_ads_local 600 € · total 1.200 €
🧭 supervisor: → persona (proponía estratega; regla: el plan supera 1.000 € y tiene que aprobarlo una persona)
⏸️  El equipo espera a Carmen Ibáñez: Aprobar el plan v2 (1.200 €)
```

- El estratega **tuvo en cuenta el comentario**: quitó TikTok.
- Como sigue pasando de 1.000 €, **vuelve a pedir aprobación**… y se la pide **a Carmen**, no a Laura: la tarea sigue con quien la tenía.

---

## 7. Tres ideas para llevarse

1. **El estado tiene que poder esperar.** Sin un sitio donde guardar el trabajo (el *checkpointer*), la pausa no funciona: la persona tarda horas o días y el programa no puede estar abierto todo ese tiempo.
2. **Antes de la pausa no debe haber efectos.** Al reanudar, el paso de la persona **se ejecuta otra vez desde el principio**. Si el email a Laura se mandara dentro de ese paso, le llegaría **dos veces**. Por eso el email se envía **fuera** del equipo (`faro/flujo.py`), cuando el equipo ya se ha parado. Lo mismo valdría para cobrar, reembolsar o cualquier cosa que no se deba repetir.
3. **Los agentes deciden; las reglas importantes, en código.** El supervisor elige el orden, pero no puede entregar un plan sin aprobación ni redactar sin datos. En mi máquina, en ENC-001 la regla corrigió 3 de las 5 decisiones que tomó el modelo.

---

## 8. Ejercicios propuestos

Del README. Pistas (*ilustrativas*), sin resolverlos del todo:

| # | Ejercicio | Pista |
|---|---|---|
| 1 | **Otro límite**: `LIMITE_AUTONOMIA` a 500 € (`faro/agencia.py`) y lanzar Taller Radios. ¿Qué cambia? | Con mi plan de 650 €, ahora **sí** pediría aprobación: un paso más para Laura antes de los datos. Bajar el límite da más control y más trabajo a la persona |
| 2 | **Una tercera tarea**: «revisar textos» antes de entregar, para aprobar o corregir lo del redactor | Es el patrón **revisar/editar** de la sesión 6 del Tema 8. Toca tres sitios: qué ve la persona (`preparar_tarea`), qué hace con su respuesta (`persona`) y una regla que no deje entregar sin revisión (`aplicar_reglas`) |
| 3 | **Rechazar** un plan con un comentario y verlo en la demo 3. ¿Y si se rechaza dos veces? | Lo de un rechazo está en la sección 6.1. Con dos, la regla de los rechazos **cierra el encargo**: «Cerrado sin campaña: el plan se rechazó dos veces» |
| 4 | **Coste de la espera**: con `03_historial.py`, qué parte del tiempo es espera humana. ¿Cómo hacer que la persona tarde menos? | En mi prueba, 24 s de espera frente a 187 s de agentes, porque respondí al momento. Ideas: que la tarea llegue con todo lo necesario para decidir, pedir los datos **a la vez** que la aprobación (no en dos tandas) o subir el límite para lo que es rutinario |

---

## 9. Cómo ejecutarlo

Tiene su propio README con la instalación completa (Python 3.10+, Ollama con `qwen2.5:7b` o un proveedor en la nube, y `pip install -r requirements.txt`: LangGraph, FastAPI…). Desde `humano-en-el-bucle/`:

```bash
python comprobar_entorno.py               # tiene que terminar con «Todo listo»
python 01_delegar.py                      # Obrador Espiga: se para esperando a Laura
python 02_bandeja.py                      # y abrir http://127.0.0.1:8000 (dejar la terminal abierta)
python 03_historial.py ENC-001 --checkpoints
python 04_plazos.py --dentro-de 5         # recordatorio
python 04_plazos.py --dentro-de 26        # escalado a Carmen
```

En esta máquina lo ejecuté con el entorno del Tema 8 (`08_ia_agentica_automatiz_agentes/tema8-agentes/.venv`, que ya tiene todas las librerías) y `LLM_MODEL=qwen3:4b-instruct` como variable de entorno, sin crear `.env`. Al usar las demos se crean `datos/`, `buzon/` y `entregas/`; para empezar de cero, se borran.

---

## Idea clave

> **Una persona puede ser un miembro más del equipo de agentes.** El equipo le delega lo que no puede o no debe hacer solo (decidir sobre dinero, conseguir datos del cliente), **se para con su estado guardado** y **sigue donde lo dejó** cuando ella responde.
> Y si no responde, **recordatorio y escalado** sin perder nada. Las reglas importantes (cuándo hace falta una persona, qué no se puede hacer sin ella) van **en código**, no en el prompt.

## Resumen

- **Faro Digital**: supervisor, estratega, redactor y **una persona** (Laura). Todos vuelven al supervisor, también ella.
- **Dos tareas para la persona**: **decidir** (planes de más de 1.000 €: aprobar, aprobar otro máximo o rechazar) y **aportar datos** que solo sabe el cliente.
- **Pararse sin perder nada**: el equipo se detiene en el paso de la persona y el estado se guarda tras cada paso. El programa puede terminar; al responder, el **mismo** equipo sigue.
- **Reglas en código**: sin aprobación no se entrega, sin datos no se redacta, dos rechazos cierran el encargo. **En mi máquina** corrigieron 3 de las 5 decisiones del supervisor en ENC-001: las tres veces, el modelo quería volver al estratega.
- **El redactor no inventa**: usa solo los datos confirmados; si falta uno, no lo nombra, y si deja huecos, el código los quita.
- **Huecos que vi**: el plan puso 100 € en TikTok (mínimo 200 €) y 650 € para un cliente de 600 €. Ninguna regla lo mira.
- **Historial**: 14 estados guardados, dos con el equipo esperando a Laura; el estratega gasta casi tres cuartas partes de los tokens.
- **Plazos**: recordatorio a las 4 h y escalado a Carmen a las 24 h, **con el estado intacto**. Si Carmen tampoco responde, no pasa nada más.
- **Tres ideas**: el estado tiene que poder esperar; antes de la pausa, nada de efectos (se repetirían); los agentes deciden, las reglas importantes van en código.
