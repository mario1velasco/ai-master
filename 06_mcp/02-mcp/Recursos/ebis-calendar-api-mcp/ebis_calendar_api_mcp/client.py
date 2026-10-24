"""Cliente HTTP pequeño para EBIS Calendar API."""

from typing import Any

import httpx

from ebis_calendar_api_mcp.config import API_URL


def _request(method: str, path: str, **kwargs: Any) -> Any:
    with httpx.Client(timeout=10.0) as http:
        response = http.request(method, f"{API_URL}{path}", **kwargs)
        response.raise_for_status()
        return response.json()


def list_workers() -> list[dict[str, Any]]:
    """Obtiene la lista de trabajadores y sus horas de trabajo."""
    return _request("GET", "/workers")


def get_worker_meetings(worker_id: int, day: str | None = None) -> dict[str, Any]:
    """Obtiene las reuniones de un trabajador, opcionalmente de un día."""
    params = {"day": day} if day else None
    return _request("GET", f"/workers/{worker_id}/meetings", params=params)


def schedule_meeting(
    worker_id: int,
    title: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    """Crea una reunión y devuelve la reunión guardada por la API."""
    return _request(
        "POST",
        "/meetings",
        json={"worker_id": worker_id, "title": title, "start": start, "end": end},
    )
