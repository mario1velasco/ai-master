# Clase 6 · Triage API — proyecto standalone, listo para AWS/Azure

Reconstrucción de `Clases/05` siguiendo la arquitectura en capas de
[`app/README.md`](../../app/README.md) (`main.py` → `services/` → `api_clients/`),
con dominio propio (`domain/`, `session/`, `llm/`) y **totalmente independiente** del
resto del repo: `.venv`, `Makefile`, `requirements.txt`, `.env` y `Dockerfile` propios.

## Arquitectura

```
app/
├── main.py           # FastAPI: rutas, valida con Pydantic, llama a services/
├── config.py          # único sitio que lee variables de entorno + config.yml
├── dto.py             # DTOs de la API (request/response)
├── domain/             # schemas de negocio + business_rules (puro, sin I/O)
├── session/            # SessionManager + almacén en memoria (sin BBDD)
├── llm/                # prompts.py + mock.py
├── services/
│   ├── llm_service.py   # rotación de las 3 API keys ante 429/529, bypass a mock
│   └── event_service.py # orquesta POST /cases/{id}/events
├── api_clients/
│   └── anthropic_client.py  # única pieza que habla con Anthropic
└── scripts/
    └── check_keys.py    # prueba las 3 keys una a una
```

Si cambia el proveedor de LLM, solo se toca `app/api_clients/`.

## Instalación (venv propio, con `uv`)

```bash
cd Clases/06
make install          # uv venv .venv + uv pip install -r requirements.txt
cp .env.example .env  # y rellena las 3 API keys (o deja placeholders si usas llm.use_mock_llm: true)
```

`config.py` exige las 3 variables `ANTHROPIC_API_KEY_1/2/3` en `.env` incluso en modo
mock — usa valores de relleno si no vas a llamar al proveedor real. El modelo, el
timeout y el toggle de mock viven en `config.yml` (sección `llm:`), no en `.env`:

```yaml
llm:
  temperature: 0.0
  max_tokens: 700
  model: claude-haiku-4-5-20251001
  timeout_seconds: 30
  use_mock_llm: false
```

## Ejecutar

```bash
make dev   # uvicorn --reload, puerto 8100
make run   # sin --reload
```

```text
http://127.0.0.1:8100/docs
```

Puerto **8100** (no 4200 ni 8000, usados por otros proyectos locales del máster).

## Endpoints

```text
GET    /health
GET    /cases
POST   /cases/{case_id}/events
GET    /cases/{case_id}/state
GET    /cases/{case_id}/trace
DELETE /cases/{case_id}
GET    /demo/stream
```

## Comprobar las API keys

```bash
make check-keys
```

## Evaluación offline (golden data)

Vive en `eval/` (`eval/eval_cases.yml` + `eval/run_eval.py`):

```bash
make eval        # modo mock, sin coste
make eval-real   # modo real, contra el proveedor
```

Genera `outputs/eval_results.json`, `outputs/eval_results.csv`, `outputs/eval_summary.json`.

## Tests

```bash
make test
```

## Docker

Build context es **este directorio** (`Clases/06`), no la raíz del repo:

```bash
make docker-build
make docker-run
```

o manualmente:

```bash
docker build -t triage-api-06 .
docker run --rm --env-file .env -p 8100:8100 triage-api-06
```

## Mensaje docente

Esta versión existe para poder desplegarse en AWS/Azure como artefacto
independiente: nada de lo que necesita para instalarse, ejecutarse o construirse
depende de la raíz del repo.
