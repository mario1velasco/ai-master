"""Carga y valida la configuración externa de la conexión MCP."""

import json
import os
from pathlib import Path
from typing import Any

from .context import CODE_DIR


def load_mcp_config() -> dict[str, Any]:
    """Lee el JSON MCP, valida sus opciones y resuelve las rutas de stdio."""
    configured_path = os.getenv("MCP_CONFIG_PATH")
    config_path = (
        Path(configured_path).expanduser().resolve()
        if configured_path
        else CODE_DIR / "mcp_config.json"
    )
    if not config_path.is_file():
        raise FileNotFoundError(f"No existe la configuración MCP: {config_path}")

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON MCP no válido ({config_path}): {error}") from error

    if not isinstance(config, dict):
        raise ValueError("La configuración MCP debe ser un objeto JSON")

    enabled = config.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError("'enabled' debe ser true o false")
    config["enabled"] = enabled
    if not enabled:
        return config

    server = config.get("server")
    if not isinstance(server, dict):
        raise ValueError("La configuración habilitada necesita un objeto 'server'")
    if not isinstance(server.get("name"), str) or not server["name"].strip():
        raise ValueError("'server.name' debe ser un texto no vacío")

    transport = server.get("transport")
    if not isinstance(transport, str) or transport not in {"stdio", "http"}:
        raise ValueError("'server.transport' debe ser 'stdio' o 'http'")

    if transport == "http":
        url = server.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ValueError("Para transport=http, 'server.url' debe ser una URL HTTP(S)")
        return config

    _validate_stdio_server(server, config_path)
    return config


def _validate_stdio_server(server: dict[str, Any], config_path: Path) -> None:
    """Comprueba los parámetros stdio y convierte cwd en una ruta absoluta."""
    command = server.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("Para transport=stdio, 'server.command' es obligatorio")

    args = server.get("args", [])
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise ValueError("'server.args' debe ser una lista de textos")

    env = server.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in env.items()
    ):
        raise ValueError("'server.env' debe contener pares texto-texto")

    configured_cwd = server.get("cwd", ".")
    if not isinstance(configured_cwd, str):
        raise ValueError("'server.cwd' debe ser una ruta de texto")
    cwd = Path(configured_cwd).expanduser()
    if not cwd.is_absolute():
        cwd = config_path.parent / cwd

    server["args"] = args
    server["env"] = env
    server["cwd"] = str(cwd.resolve())
