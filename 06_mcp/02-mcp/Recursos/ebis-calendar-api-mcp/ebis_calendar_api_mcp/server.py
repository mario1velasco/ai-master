"""Tools MCP para la API EBIS Calendar, con stdio activo por defecto."""

import json
import os
from typing import Any

import httpx

from mcp.server import MCPServer

from ebis_calendar_api_mcp import client
from ebis_calendar_api_mcp.config import API_URL


MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()
if MCP_TRANSPORT not in {"stdio", "http"}:
    raise ValueError("MCP_TRANSPORT debe ser 'stdio' o 'http'")

# TODO 1: crea una instancia MCPServer compartida por los dos transportes.
mcp = TODO_MCPSERVER


@mcp.tool()
def list_workers() -> list[dict[str, Any]]:
    """Lista trabajadores y su horario laboral habitual."""
    # TODO 2: delega en la función equivalente de client.py.
    return client.TODO_LIST_WORKERS()


@mcp.tool()
def get_worker_meetings(worker_id: int, day: str | None = None) -> dict[str, Any]:
    """Consulta las reuniones de un trabajador. day es opcional (AAAA-MM-DD)."""
    # TODO 3: delega en client.py pasando el identificador y el día.
    return client.TODO_GET_MEETINGS(worker_id=worker_id, day=day)


@mcp.tool()
def schedule_meeting(worker_id: int, title: str, start: str, end: str) -> dict[str, Any]:
    """Agenda una reunión para un trabajador.

    start y end deben ser fechas ISO locales sin zona horaria
    (AAAA-MM-DDTHH:MM:SS), del mismo día laborable, entre las 09:00 y las
    17:00. end debe ser posterior a start y no puede haber solapamientos.
    Consulta get_worker_meetings antes de proponer un horario.
    """
    # TODO 4: delega en client.py pasando todos los argumentos recibidos.
    try:
        return client.TODO_SCHEDULE_MEETING(
            worker_id=worker_id,
            title=title,
            start=start,
            end=end,
        )
    except httpx.HTTPStatusError as error:
        try:
            body = error.response.json()
        except ValueError:
            detail = error.response.text or str(error)
        else:
            detail = body.get("detail", body) if isinstance(body, dict) else body
            if not isinstance(detail, str):
                detail = json.dumps(detail, ensure_ascii=False)

        return {
            "error": (
                f"La API rechazó la reunión (HTTP {error.response.status_code}): "
                f"{detail}"
            )
        }
    except httpx.RequestError as error:
        return {"error": f"No se pudo conectar con la API de calendario: {error}"}
    except Exception as error:
        return {"error": f"No se pudo agendar la reunión: {error}"}


@mcp.resource("ebis-calendar://config")
def get_config() -> str:
    """Describe la API y las tools disponibles en este servidor MCP."""
    return (
        "Servidor MCP conectado a EBIS Calendar API\n"
        f"API_URL: {API_URL}\n"
        f"Transport: {MCP_TRANSPORT}\n"
        "Tools: list_workers, get_worker_meetings, schedule_meeting\n"
    )


def main() -> None:
    if MCP_TRANSPORT == "http":
        # HTTP alternativa: Streamable HTTP en /mcp, puerto 8001.
        mcp.run(
            transport="streamable-http",
            host="127.0.0.1",
            port=8001,
            stateless_http=True,
            json_response=True,
        )
    else:
        # Configuración utilizada por ebis-cli-proyect/mcp_config.json.
        mcp.run()


if __name__ == "__main__":
    main()
