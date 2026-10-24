"""Convierte tools y resultados MCP a los formatos que consume el agente."""

import json
import re
from typing import Any


def custom_unique_tool_name(
    remote_name: str, existing_names: set[str] | None = None
) -> str:
    """Genera un nombre seguro y único para exponer una tool MCP al modelo.

    Los nombres originales del servidor pueden incluir caracteres que no queremos
    usar en los nombres de funciones enviados a Responses API. Esta función los
    sustituye por guiones bajos, añade el prefijo ``mcp_`` y limita el resultado a
    64 caracteres. Como dos nombres distintos pueden quedar iguales tras esos
    cambios, añade ``_2``, ``_3`` y sucesivos hasta encontrar uno libre.

    Args:
        remote_name: Nombre original de la tool en el servidor MCP.
        existing_names: Nombres ya asignados a otras tools expuestas al modelo.

    Returns:
        El nombre normalizado, de hasta 64 caracteres, que se puede usar en el
        esquema de función. No modifica ``existing_names``.

    Example:
        ``custom_unique_tool_name("list workers")`` devuelve
        ``"mcp_list_workers"``. Si ese nombre ya existe, devuelve
        ``"mcp_list_workers_2"``.
    """
    if existing_names is None:
        existing_names = set()
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", remote_name)
    base_name = f"mcp_{safe_name}"[:64]
    if base_name not in existing_names:
        return base_name

    suffix_number = 2
    while True:
        suffix = f"_{suffix_number}"
        candidate = f"{base_name[:64 - len(suffix)]}{suffix}"
        if candidate not in existing_names:
            return candidate
        suffix_number += 1


def adapt_tools(tools: list[Any]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Prepara las tools descubiertas para que el modelo pueda invocarlas.

    Cada tool MCP se convierte en una definición de función de Responses API con
    su nombre público normalizado, descripción y esquema de argumentos. También
    crea el mapa inverso necesario para traducir el nombre que devuelva el modelo
    al nombre original que entiende el servidor MCP.

    Args:
        tools: Tools devueltas por ``Client.list_tools()``. Cada elemento debe
            tener ``name`` y puede tener ``description`` e ``input_schema``.

    Returns:
        Una pareja ``(tools_for_model, model_tool_name_to_mcp_name)``:

        - ``tools_for_model`` es la lista de esquemas ``type=function`` que se
          pasa a Responses API. Si falta descripción o esquema, usa valores por
          defecto sencillos.
        - ``model_tool_name_to_mcp_name`` relaciona el nombre visible para el
          modelo con el nombre original de la tool en MCP.

    Example:
        Para una tool MCP llamada ``list workers``, el esquema puede exponer
        ``mcp_list_workers`` y el mapa contendrá
        ``{"mcp_list_workers": "list workers"}``.
    """
    tools_for_model = []
    model_tool_name_to_mcp_name = {}

    for tool in tools:
        model_tool_name = custom_unique_tool_name(
            tool.name, set(model_tool_name_to_mcp_name)
        )
        schema = tool.input_schema or {
            "type": "object",
            "properties": {},
            "required": [],
        }
        tools_for_model.append(
            {
                "type": "function",
                "name": model_tool_name,
                "description": tool.description or f"Tool MCP {tool.name}",
                "parameters": schema,
                "strict": False,
            }
        )
        model_tool_name_to_mcp_name[model_tool_name] = tool.name

    return tools_for_model, model_tool_name_to_mcp_name


def format_tool_result(result: Any) -> str:
    """Convierte la respuesta de ``Client.call_tool()`` en texto para el agente.

    Prefiere el contenido estructurado cuando el servidor lo proporciona y lo
    serializa como JSON legible. Si no hay contenido estructurado, concatena los
    bloques de texto en el orden recibido. Cuando MCP marca el resultado como
    error, antepone ``"Error de herramienta MCP: "`` para que el agente pueda
    distinguirlo de una respuesta normal.

    Args:
        result: Resultado MCP con ``structured_content``, ``content`` e
            ``is_error``.

    Returns:
        Una cadena lista para incluir como salida de la llamada de función. Si
        no hay datos estructurados ni bloques de texto, devuelve un mensaje
        indicando que la tool no produjo texto.
    """
    if result.structured_content is not None:
        output = json.dumps(result.structured_content, ensure_ascii=False, default=str)
    else:
        output = "\n".join(
            block.text for block in result.content if hasattr(block, "text")
        ) or "La tool no devolvió contenido de texto."

    return f"Error de herramienta MCP: {output}" if result.is_error else output
