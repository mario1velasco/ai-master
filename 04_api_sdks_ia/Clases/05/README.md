# Clase 5 · LLMOps y despliegue de aplicaciones LLM

Partimos de la API de Clase 4 y añadimos una capa mínima de operación: versionado, observabilidad, coste estimado, evaluación offline, tests y Docker.

## Instalación

```bash
python -m venv .venv
pip install -r requirements.txt
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
copy .env.example .env
```

Mac/Linux:

```bash
source .venv/bin/activate
cp .env.example .env
```

## Modo mock sin coste

En `.env`:

```text
USE_MOCK_LLM=true
LLM_MODEL=mock-triage-model
```

Ejecutar API:

```bash
python -m uvicorn app:app --reload
```

Abrir:

```text
http://127.0.0.1:8000/docs
```

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

## Evaluación offline

```bash
python run_eval.py --mode mock
```

Genera:

```text
outputs/eval_results.json
outputs/eval_results.csv
outputs/eval_summary.json
```

Modo real con proveedor:

```bash
python run_eval.py --mode real
```

## Tests

```bash
pytest
```

## Docker

El `Dockerfile` usa el `requirements.txt` de la raíz del repo, así que el build
context debe ser la raíz (no `Clases/05`):

```bash
cd ../..   # repo root
docker build -f Clases/05/Dockerfile -t ai-triage-api .
docker run --env-file Clases/05/.env -p 8000:8000 ai-triage-api
```

## Mensaje docente

Una aplicación LLM no termina cuando responde en local. Termina cuando puede versionarse, evaluarse, observarse, probarse y desplegarse con control.
