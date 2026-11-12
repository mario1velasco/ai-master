# Tema 4 · Integración de Modelos de IA para la automatización de procesos y LLMOps

Máster en Ingeniería de Automatización con IA Agéntica — EBIS Business Techschool.

## De qué va el temario

Este módulo enseña a integrar modelos generativos (LLMs) vía API dentro de sistemas
automatizados, tratando el modelo como un **componente software** más —configurable,
observable, repetible y mantenible— en lugar de un chatbot manual.

Cinco clases que construyen, paso a paso, el mismo caso: **AI Request Triage**
(clasificar y procesar peticiones de clientes: reembolsos, cambios de entrega,
facturación, soporte técnico).

| Clase | Tema | Idea central | Código |
|---|---|---|---|
| 1 | Integración de modelos vía API desde Python | LLM-as-a-Service: proveedor, modelo y aplicación son capas distintas. Anatomía de una request (API key, modelo, mensajes, parámetros), `temperature`, coste por tokens, latencia, errores (401, 429, timeout) y resiliencia (timeout, retry + backoff, fallback, log, validación) | `Clases/01/` (`llm_client.py`, `benchmark.py`) |
| 2 | Prompt engineering y salidas estructuradas | El prompt es un contrato. Tres niveles: JSON por prompt, Structured Outputs nativos (`messages.parse`) y tool call como schema (`tool_choice`, bloque `tool_use`). Pydantic valida la estructura, no que la decisión sea correcta | `Clases/02/` |
| 3 | Contexto, sesiones y flujos operativos | El LLM es stateless: la aplicación reconstruye el contexto en cada llamada. Historial ≠ estado ≠ resumen ≠ memoria; el estado estructurado es la fuente de verdad. Estrategias: últimos N mensajes, resumen, estado. Las reglas de negocio van en código | `Clases/03/` (`session_manager.py`, `business_rules.py`) |
| 4 | APIs propias con FastAPI | HTTP y LLM son stateless; la app conserva el estado por `case_id`. `POST /cases/{case_id}/events` devuelve `operation` + `state` + `metrics`; el routing es un resultado, no un endpoint. Errores HTTP controlados; streaming solo para UX | `Clases/04/` (`app.py`, `session_store.py`) |
| 5 | LLMOps, observabilidad y despliegue | Una app LLM está lista cuando se puede evaluar, observar, versionar y desplegar. Trazas con versiones, golden dataset y release gates, tests sin LLM (mock), retry / repair / fallback / safe stop, canary y blue-green, Docker y CI/CD | `Clases/05/` (`observability.py`, `run_eval.py`, `tests/`) |

`Clases/06/` es una reconstrucción propia de la clase 5 con la arquitectura en capas de
`app/` (`main` → `services` → `api_clients`), independiente del resto del repo y lista
para desplegar (ver su `README.md`).

Quedan fuera del tema (se ven más adelante): RAG, agentes, bases vectoriales y MCP.

## Estructura del proyecto

```
.
├── app/                    # Paquete Python de la aplicación
│   ├── main.py             # FastAPI app + rutas (capa de "entrada")
│   ├── services/           # Lógica de negocio (capa del "qué hacer")
│   ├── api_clients/        # Llamadas a proveedores externos, ej. Anthropic (capa del "cómo hablar con él")
│   ├── config.py           # Único punto donde se leen variables de entorno
│   ├── scripts/            # Tareas puntuales: cron jobs, scripts manuales
│   ├── utils/              # Código transversal reutilizable (ej. logger.py)
│   └── README.md           # Detalle de la arquitectura en capas
├── requirements.txt
├── Makefile                # Atajos: make install / run / dev
├── .env                    # Claves reales (NO se sube a git, ver .gitignore)
├── .env.example            # Plantilla sin valores, para saber qué variables hacen falta
├── .vscode/                # Configuración de debug de VSCode
├── Clases/                 # Código de cada clase: 01 a 05 (temario) y 06 (versión en capas, desplegable)
├── examples/               # Ejemplos sueltos: chat por terminal con Anthropic, OpenAI y Ollama;
│                           #   entrada multimodal con OpenAI (imagen, PDF, mp3); una API FastAPI de prueba
└── pdfs/                   # Diapositivas de las 5 sesiones en PDF y en .md (no tienen exactamente la misma información)
```

### Arquitectura: `main` → `services` → `api_clients`

Cada funcionalidad atraviesa tres capas, cada una con una única responsabilidad (ver
[app/README.md](app/README.md) para el detalle):

```
main.py  ──▶  services/  ──▶  api_clients/  ──▶  proveedor externo (Anthropic...)
(rutas)       (lógica de      (llamadas HTTP a
               negocio)        APIs externas)
```

Si mañana cambias de proveedor de LLM, solo tocas `api_clients/` — `main.py` y
`services/` no saben ni les importa qué proveedor hay detrás de la interfaz.

## Cómo usar las API Keys

El máster proporciona **3 API keys corporativas** compartidas entre todo el grupo,
habilitadas exclusivamente para los ejercicios prácticos y retos de desarrollo de esta
fase. Actúan como un "sandbox" común: para repartir la carga entre todos los alumnos,
sigue este protocolo:

- **Selección aleatoria**: no uses siempre la primera clave de la lista; elige una al
  azar para evitar cuellos de botella en una sola credencial.
- **Rotación por saturación**: si una llamada devuelve `Rate Limit Exceeded` u
  `Overloaded`, esa clave está muy solicitada en ese momento — prueba con otra de las 3.
- **Modelo por defecto**: usa `claude-haiku-4-5-20251001` (Claude Haiku 4.5) salvo que
  el ejercicio pida explícitamente un modelo superior.
- **Cuidado con los bucles**: revisa la lógica de tus workflows automáticos antes de
  ejecutarlos. Un bucle infinito agota el saldo de la key y perjudica a los compañeros
  que comparten esa misma credencial.

### Configuración local

1. Copia la plantilla y rellena las 3 claves reales (te las facilita el equipo docente):

   ```bash
   cp .env.example .env
   ```

   ```
   ANTHROPIC_API_KEY_1=...
   ANTHROPIC_API_KEY_2=...
   ANTHROPIC_API_KEY_3=...
   ```

2. Instala las dependencias (usa [uv](https://docs.astral.sh/uv/); crea `.venv/` si no existe):

   ```bash
   make install
   ```

   Cada vez que añadas un paquete nuevo a `requirements.txt`, vuelve a ejecutar
   `make install` para sincronizar el entorno — no reinstala lo que ya esté.

3. Importa `app/config.py` en tus scripts. Si falta cualquiera de las 3 variables,
   lanza un error explícito en lugar de fallar en silencio más adelante:

   ```python
   from app.config import ANTHROPIC_API_KEYS, DEFAULT_MODEL
   ```

**Importante:** `.env` contiene credenciales reales y está excluido en `.gitignore`.
Nunca lo subas al repositorio ni pegues las claves en texto plano en el README u otros
ficheros versionados — las claves ya se han retirado de este documento por ese motivo.

## Proyecto FastAPI de ejemplo

`app/main.py` expone una API mínima que ilustra el uso de las keys y el modelo por
defecto:

- `GET /health` — comprueba que las 3 keys están cargadas.
- `POST /chat` — recibe `{"message": "..."}`, llama a Claude con
  `claude-haiku-4-5-20251001` y rota automáticamente de key si recibe un error de
  saturación (429/529).

Arrancar el servidor en local (puerto `4200`, para no chocar con otros proyectos que
usen el `8000` por defecto):

```bash
make dev     # con --reload
make run     # sin --reload
```

Probar el endpoint:

```bash
curl -X POST http://127.0.0.1:4200/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿qué modelo eres?"}'
```

### Debug en VSCode

El repo incluye [.vscode/launch.json](.vscode/launch.json) con la configuración
**"FastAPI: app.main (uvicorn)"**: lanza `uvicorn app.main:app --reload` en el puerto
4200 con el intérprete del `.venv` ([.vscode/settings.json](.vscode/settings.json)) y
carga `.env` automáticamente. Basta con abrir "Run and Debug" en VSCode, seleccionarla y
poner breakpoints en cualquier fichero de `app/` (rutas, servicios o clientes).
