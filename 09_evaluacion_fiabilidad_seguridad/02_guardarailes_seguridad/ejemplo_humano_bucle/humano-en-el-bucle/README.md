# Tema 8 · Un equipo de agentes que delega en una persona

Material complementario del Tema 8 (IA Agéntica y automatización basada en agentes).

En la sesión de sistemas multiagente vimos un equipo de agentes coordinado por un
supervisor. Aquí damos un paso más: **una persona forma parte del equipo**. Cuando los
agentes llegan a algo que no pueden o no deben hacer solos, le delegan una tarea, el
flujo de trabajo **se detiene con su estado guardado** y, cuando la persona termina,
**el mismo equipo retoma el trabajo** donde lo dejó, con lo que ella ha aportado.

El caso es **Faro Digital**, una agencia de marketing para pymes. El equipo prepara
campañas para sus clientes:

```
encargo ─► supervisor ─┬─► estratega ──┐   prepara el plan de medios con herramientas
              ▲        ├─► redactor ───┤   escribe los textos de los anuncios
              │        ├─► persona ────┤   ⏸️ el grafo se pausa hasta que ella responde
              │        └─► entregar ─► propuesta final
              └────────────────────────┘
```

La persona es **Laura Méndez, responsable de cuenta**. El equipo le delega dos tipos de tarea:

- **Decidir:** aprobar el plan cuando supera los 1.000 € que el equipo puede decidir
  solo. Puede aprobarlo, aprobar otro presupuesto máximo o rechazarlo con un comentario.
- **Aportar datos:** confirmar con el cliente lo que los agentes no pueden averiguar
  (precio, fechas, fotos...).

| Demo | Qué aprendes |
|---|---|
| `01_delegar.py` | El equipo trabaja hasta que necesita a la persona, le deja una tarea y se detiene sin perder nada |
| `02_bandeja.py` | La bandeja web de la persona: ve la tarea, la completa y el equipo continúa en segundo plano |
| `03_historial.py` | Qué ha pasado por dentro: quién ha trabajado, cuánto ha esperado el equipo y los estados guardados |
| `04_plazos.py` | Qué hacer si la persona no responde: recordatorios y escalado a otra persona |

> **¿Se usa esto en empresa?** Todavía es poco habitual. Lo normal es derivar a una
> persona por email o por teléfono y que el proceso termine ahí. Pero en startups y
> pymes, donde una misma persona supervisa mucho trabajo automatizado, tener a los
> agentes esperando su decisión y retomando el trabajo solos ahorra mucho tiempo. La
> demo combina las dos cosas: la persona recibe un email (simulado) con el enlace a su bandeja.

## 1. Requisitos

Tiempo estimado: 20 minutos, más la descarga del modelo.

- **Python 3.10 o superior.** Compruébalo con `python3 --version` (Windows: `python --version`).
  Si no lo tienes, descárgalo de [python.org](https://www.python.org/downloads/).
- **Un modelo de lenguaje** que admita *tool calling*, con una de estas dos opciones:
    - **Opción A, modelo local con Ollama (recomendada).** Gratis y sin enviar datos
      fuera. Necesita unos 6 GB libres en disco y 8 GB de RAM.
    - **Opción B, proveedor en la nube** compatible con la API de OpenAI. Útil si tu
      equipo no llega. Necesitas una cuenta y una clave de API del proveedor.

Si ya montaste el repositorio `tema8-agentes` del tema, ya tienes Python y Ollama:
salta al paso 2.

### Opción A: instalar Ollama y descargar el modelo

1. Descarga Ollama desde [ollama.com/download](https://ollama.com/download) e instálalo.
2. Ábrelo. Tiene que estar abierto mientras uses las demos.
3. En una terminal, descarga el modelo (unos 4,7 GB):

```bash
ollama pull qwen2.5:7b
```

### Opción B: proveedor en la nube

No instales Ollama. En el paso 2, rellena en el `.env` la URL de la API del proveedor
(`LLM_BASE_URL`), tu clave (`LLM_API_KEY`) y el nombre del modelo (`LLM_MODEL`). El
`.env.example` incluye un ejemplo comentado. No compartas nunca tu clave.

## 2. Instalación

Descomprime `tema8-humano-en-el-bucle.zip`, abre una terminal en la carpeta y ejecuta:

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Al activar el entorno verás `(.venv)` al principio de la línea de la terminal. Cada
vez que abras una terminal nueva para las demos, actívalo de nuevo con la segunda línea.

## 3. Comprobar que todo funciona

```bash
python comprobar_entorno.py
```

Tiene que terminar con «Todo listo». Revisa Python, las librerías, la conexión con el
modelo, que el modelo sabe usar herramientas y que un grafo de LangGraph se puede
pausar y reanudar.

## 4. Las demos

Ejecútalas en orden desde la carpeta del proyecto. Con un modelo local, cada paso del
equipo tarda entre unos segundos y un minuto: es normal.

### Demo 1 · Delegar y esperar

```bash
python 01_delegar.py
```

El encargo es de **Obrador Espiga**, una panadería que lanza un roscón de Reyes sin
gluten con un presupuesto de unos 1.500 €. Verás al equipo trabajar en la terminal:

```
🧭 supervisor: → estratega: hay que preparar el plan de medios...
📊 estratega: Plan v1: instagram_ads 1.000 €, google_ads_local 500 € · total 1.500 €
🧭 supervisor: → persona (proponía estratega; regla: el plan supera 1.000 € y tiene que aprobarlo una persona)
⏸️  El equipo espera a Laura Méndez: Aprobar el plan v1 (1.500 €)
```

**El programa termina, pero el trabajo no se pierde.** El estado del equipo está
guardado en `datos/faro.sqlite` y Laura tiene un email en la carpeta `buzon/`.

Fíjate en la línea de la regla: **el supervisor decide, pero hay cosas que no puede
saltarse**. Un plan de más de 1.000 € pasa siempre por una persona, lo proponga o no
el modelo. Esa regla está en código (`aplicar_reglas` en `faro/equipo.py`).

Cómo se pausa el grafo, en `faro/equipo.py`:

```python
def persona(estado):
    tarea = preparar_tarea(estado)    # lo que verá la persona en su bandeja
    respuesta = interrupt(tarea)      # ⏸️ aquí se detiene y se guarda el estado
    ...                               # al reanudar, interrupt() devuelve la respuesta
```

### Demo 2 · La bandeja de la persona

```bash
python 02_bandeja.py
```

Abre <http://127.0.0.1:8000> y deja esa terminal abierta: la página solo funciona
mientras se esté ejecutando. Entra en el encargo y **haz de Laura**:

1. **Aprueba un presupuesto distinto:** elige «Aprobar con otro presupuesto máximo»,
   pon 1200 y un comentario. En la terminal verás cómo **el mismo equipo** continúa:
   el estratega rehace el plan para no pasar de 1.200 € y vuelve a pararse, ahora para
   pedirte los datos del cliente. La página se actualiza sola.
2. **Aporta los datos:** escribe el precio y la fecha, y deja algún campo vacío a propósito.
3. El redactor escribe los textos y aparece la propuesta. También queda en `entregas/`.

Desde la bandeja puedes crear encargos nuevos. Prueba **Taller Radios** (600 €): como
no pasa del límite, el equipo no pide aprobación y solo te pide los datos.

Cómo vuelve el trabajo al equipo, en `faro/flujo.py`:

```python
config = {"configurable": {"thread_id": "ENC-001"}}     # el encargo identifica al equipo
equipo.invoke(Command(resume=respuesta), config)       # continúa donde se quedó
```

### Demo 3 · Qué ha pasado por dentro

```bash
python 03_historial.py ENC-001
python 03_historial.py ENC-001 --checkpoints
```

La línea temporal muestra quién ha trabajado y cuánto: compara el **tiempo de trabajo
de los agentes** con el **tiempo que el equipo ha esperado a la persona**. Con
`--checkpoints` verás cada estado guardado y en cuáles el grafo estaba pausado.

### Demo 4 · ¿Y si la persona no responde?

```bash
python 04_plazos.py --dentro-de 5      # como si hubieran pasado 5 horas
python 04_plazos.py --dentro-de 26     # como si hubieran pasado 26 horas
```

Deja un encargo esperando (lanza `01_delegar.py` y no respondas). Con 5 horas se envía
un recordatorio a Laura; con 26, la tarea se escala a **Carmen Ibáñez, directora de
cuentas**. Mira los emails en `buzon/` y abre la bandeja: la tarea ahora es de Carmen.
En una empresa, este script se ejecutaría cada hora con una tarea programada.

## 5. Tres ideas para llevarse

1. **El estado tiene que poder esperar.** Sin un *checkpointer*, `interrupt()` no
   funciona: no habría dónde guardar el trabajo mientras la persona tarda horas o días.
2. **Antes de `interrupt()` no debe haber efectos.** Al reanudar, el nodo se ejecuta
   otra vez desde el principio. Por eso el email a la persona se envía fuera del grafo
   (`faro/flujo.py`): dentro del nodo se enviaría dos veces.
3. **Los agentes deciden; las reglas importantes, en código.** El supervisor elige el
   orden, pero no puede entregar un plan sin aprobación ni redactar sin datos. Al
   probar la demo, el estratega ignoró una vez el máximo aprobado y la regla lo paró
   (lo verás comentado con 🐞 en `faro/equipo.py`).

## 6. Ejercicios propuestos

1. **Otro límite.** Cambia `LIMITE_AUTONOMIA` en `faro/agencia.py` a 500 € y lanza
   Taller Radios. ¿Qué cambia en el flujo?
2. **Una tercera tarea para la persona.** Añade un tipo de tarea «revisar textos»:
   antes de entregar, la persona aprueba o corrige lo que ha escrito el redactor.
   Pista: añade el caso en `preparar_tarea` y `persona`, y una regla en `aplicar_reglas`.
3. **Rechazar.** Rechaza un plan con un comentario («nada de Facebook») y comprueba en
   la demo 3 que el estratega lo ha tenido en cuenta. ¿Qué pasa si lo rechazas dos veces?
4. **Coste de la espera.** Con `03_historial.py`, mide qué parte del tiempo total es
   espera humana. ¿Qué cambiarías en el diseño para que la persona tarde menos?

## 7. Si algo falla

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'dotenv'` (o `langgraph`) | El entorno no está activado: `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`) |
| Safari o Chrome «no puede conectarse al servidor» | La bandeja no está en marcha: `python 02_bandeja.py` y deja la terminal abierta |
| `Address already in use` | Ya hay algo en el puerto 8000 (¿otra bandeja o el servidor de la sesión 6?). Ciérralo con Ctrl+C en su terminal |
| `Connection refused` al lanzar una demo | Ollama no está abierto, o `LLM_BASE_URL` del `.env` está mal |
| El modelo responde, pero no usa herramientas | Usa `qwen2.5:7b` u otro modelo con *tool calling* |
| La página se queda en «El equipo está trabajando» | Mira la terminal de la bandeja: el modelo local puede tardar un minuto. Si sale un error, el encargo queda en estado «Error» |
| Quiero empezar de cero | Borra las carpetas `datos/`, `buzon/` y `entregas/` |
| `pip install` no encuentra los paquetes (red de empresa) | `PIP_CONFIG_FILE=/dev/null pip install --index-url https://pypi.org/simple -r requirements.txt` |

## Estructura

```
tema8-humano-en-el-bucle/
├── 01_delegar.py          Demo 1
├── 02_bandeja.py          Demo 2 (bandeja web con FastAPI)
├── 03_historial.py        Demo 3
├── 04_plazos.py           Demo 4
├── comprobar_entorno.py   Comprueba la instalación (paso 3)
├── faro/
│   ├── agencia.py         Datos simulados: clientes, tarifas, personas y límite de autonomía
│   ├── equipo.py          El equipo: supervisor, estratega, redactor, persona y reglas
│   ├── flujo.py           Encargos, pausas, avisos por email y reanudación
│   ├── config.py          Modelo y rutas (lee el .env)
│   └── utilidades.py
├── .env.example
└── requirements.txt
```

Se crean al usar las demos: `datos/` (estado del equipo), `buzon/` (emails simulados)
y `entregas/` (propuestas terminadas). Todo es simulado: ningún email sale de tu ordenador.
