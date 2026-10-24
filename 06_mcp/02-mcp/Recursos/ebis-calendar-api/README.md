# EBIS Calendar API

API de ejemplo, sin autenticación ni base de datos, para el ejercicio de tools y MCP. Guarda trabajadores y reuniones en memoria y ofrece un horario laboral común de lunes a viernes, de 09:00 a 17:00.

## Iniciar

Desde esta carpeta:

```powershell
uv sync
uv run python main.py
```

Para desarrollo con recarga automática, puedes usar `uv run uvicorn api:app --reload`.

La API queda en `http://127.0.0.1:8000`; la documentación interactiva está en `http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /health`: estado de la API.
- `GET /workers`: trabajadores y horario.
- `GET /workers/{worker_id}`: ficha de un trabajador.
- `GET /workers/{worker_id}/meetings`: reuniones de un trabajador; admite `?day=AAAA-MM-DD`.
- `POST /meetings`: crea una reunión con `worker_id`, `title`, `start` y `end`.

Ejemplo de petición:

```json
{
  "worker_id": 1,
  "title": "Revisión semanal",
  "start": "2026-10-01T14:00:00",
  "end": "2026-10-01T14:30:00"
}
```

Las horas se interpretan como hora local sin zona horaria. Se validan el trabajador, el horario laboral, los días laborables y los solapamientos. La información de reuniones es temporal: se reinicia al parar el proceso.

## Módulos

- `main.py`: arranque del servidor Uvicorn.
- `api.py`: creación de la aplicación FastAPI, modelo de entrada y endpoints.
- `db.py`: trabajadores y reuniones de ejemplo con operaciones en memoria.
