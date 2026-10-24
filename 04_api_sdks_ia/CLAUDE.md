# CLAUDE.md

Guía para trabajar en este repo. Lee esto antes de tocar código.

## Qué es este proyecto

Material y ejercicios del **Tema 4** del Máster en Ingeniería de Automatización con IA
Agéntica (EBIS Business Techschool): *Integración de Modelos de IA para la
automatización de procesos y LLMOps*. Clase 1: integración de modelos generativos vía
API desde Python (LLM-as-a-Service, salida estructurada, contexto/sesiones, FastAPI +
streaming, LLMOps + despliegue). Las diapositivas de la sesión están en `pdfs/`.

Incluye un mini-backend FastAPI de ejemplo que demuestra cómo usar las API keys
corporativas del máster (rotación, modelo por defecto) siguiendo la arquitectura en
capas descrita más abajo.

## API keys — muy importante

El máster reparte **3 API keys corporativas compartidas** entre todo el grupo, para
ejercicios de esta fase únicamente. Viven en `.env` (gitignored) y **nunca** deben
volver a texto plano en el README ni en ningún fichero versionado — ya ocurrió una vez
(estaban pegadas en el README original) y se corrigió moviéndolas a `.env` +
`.env.example` como plantilla.

Protocolo de uso (ver detalle en [README.md](README.md)):
- Selección aleatoria entre las 3 keys para repartir carga.
- Si una llamada da `429`/`Overloaded` (`529`), rotar a otra key — no reintentar la
  misma.
- Modelo por defecto: `claude-haiku-4-5-20251001` (Claude Haiku 4.5), salvo que el
  ejercicio pida uno superior explícitamente.
- Evitar bucles automáticos sin control: consumen el saldo compartido.

`app/config.py` es el único sitio que lee estas variables de entorno, y falla con
`RuntimeError` si falta alguna — nunca deben leerse `os.environ` desde otro módulo.

## Arquitectura: `main` → `services` → `api_clients`

Patrón en capas, cada una con una única responsabilidad (detalle en
[app/README.md](app/README.md)):

```
app/main.py  ──▶  app/services/  ──▶  app/api_clients/  ──▶  proveedor externo (Anthropic...)
(rutas)            (lógica de          (llamadas HTTP a
                     negocio)           APIs externas)
```

- `app/main.py` — solo define endpoints, valida con Pydantic y llama al service.
- `app/services/chat_service.py` — decide *qué hacer*: aquí vive la rotación de keys
  ante saturación (429/529), no en `main.py` ni en el cliente HTTP.
- `app/api_clients/anthropic_client.py` — solo sabe *hablar con Anthropic*: construye
  la request, autentica con una key dada, parsea la respuesta (filtra `TextBlock` de
  `response.content`, ya que puede haber otros tipos de bloque).
- `app/config.py` — único punto de lectura de variables de entorno.
- `app/scripts/` — tareas puntuales ejecutables a mano (ej. `check_keys.py`, que
  prueba las 3 keys una a una: `python -m app.scripts.check_keys`).
- `app/utils/logger.py` — logger reutilizable para código transversal.

Regla práctica: si cambia el proveedor de LLM, solo se toca `app/api_clients/`.

## Cómo ejecutar

Usa **`uv`** para el entorno virtual (preferencia explícita del usuario, no `pip`/`venv`
a secas):

```bash
make install   # uv venv .venv + uv pip install -r requirements.txt
make dev       # uvicorn app.main:app --reload, puerto 4200
make run       # sin --reload
```

Tras añadir un paquete a `requirements.txt`, volver a correr `make install` (sincroniza,
no reinstala todo).

**Puerto 4200, no 8000**: el 8000 suele estar ocupado por otro proyecto del usuario
(`ai-linkedin-job-searcher`) corriendo en modo debug en VSCode. Todos los scripts,
`Makefile` y `.vscode/launch.json` de este repo usan 4200 para no chocar.

Debug en VSCode: usar la configuración **"FastAPI: app.main (uvicorn)"** de
`.vscode/launch.json` (breakpoints en cualquier fichero de `app/`).

## Convenciones

- No usar `pip install` suelto; todo pasa por `uv` + `requirements.txt` + `Makefile`.
- No añadir claves ni secretos reales a ficheros versionados (README, código, commits).
  Solo `.env` (gitignored). `.env.example` documenta qué variables hacen falta, sin
  valores.
- Mantener la separación de capas: lógica de rotación/orquestación en `services/`,
  nunca en `main.py` ni mezclada dentro de `api_clients/`.
