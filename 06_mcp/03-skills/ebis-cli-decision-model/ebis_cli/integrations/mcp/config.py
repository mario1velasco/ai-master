"""Carga una lista validada de servidores MCP (stdio y HTTP)."""

import json
import os
from pathlib import Path
from typing import Any

from ...workspace.context import CODE_DIR
from ...settings import MAX_MCP_SERVERS


def load_mcp_config() -> dict[str, Any]:
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
        raise ValueError("La configuración MCP debe ser un objeto JSON.")

    enabled = config.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError("'enabled' debe ser true o false.")
    config["enabled"] = enabled
    if not enabled:
        config["servers"] = []
        return config

    # Compatibilidad con el archivo antiguo de la v4, que tenía un solo 'server'.
    raw_servers = config.get("servers")
    if raw_servers is None and isinstance(config.get("server"), dict):
        raw_servers = [config["server"]]
    if not isinstance(raw_servers, list) or not raw_servers:
        raise ValueError("La configuración habilitada necesita una lista 'servers'.")
    if len(raw_servers) > MAX_MCP_SERVERS:
        raise ValueError(
            f"Hay {len(raw_servers)} servidores configurados; el límite actual es "
            f"MAX_MCP_SERVERS={MAX_MCP_SERVERS}."
        )

    servers: list[dict[str, Any]] = []
    names: set[str] = set()
    for server in raw_servers:
        if not isinstance(server, dict):
            raise ValueError("Cada elemento de 'servers' debe ser un objeto JSON.")
        _validate_server(server, config_path)
        name = server["name"]
        if name in names:
            raise ValueError(f"El nombre MCP '{name}' está repetido.")
        names.add(name)
        servers.append(server)
    config["servers"] = servers
    return config


def _validate_server(server: dict[str, Any], config_path: Path) -> None:
    if not isinstance(server.get("name"), str) or not server["name"].strip():
        raise ValueError("Cada servidor necesita un 'name' de texto no vacío.")
    transport = server.get("transport")
    if not isinstance(transport, str) or transport not in {"stdio", "http"}:
        raise ValueError(f"{server['name']}.transport debe ser 'stdio' o 'http'.")

    if transport == "http":
        url = server.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ValueError(f"{server['name']}.url debe ser una URL HTTP(S).")
        return

    command = server.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"{server['name']}.command es obligatorio para stdio.")
    args = server.get("args", [])
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise ValueError(f"{server['name']}.args debe ser una lista de textos.")
    env = server.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in env.items()
    ):
        raise ValueError(f"{server['name']}.env debe contener pares texto-texto.")
    configured_cwd = server.get("cwd", ".")
    if not isinstance(configured_cwd, str):
        raise ValueError(f"{server['name']}.cwd debe ser una ruta de texto.")
    cwd = Path(configured_cwd).expanduser()
    if not cwd.is_absolute():
        cwd = config_path.parent / cwd

    server["args"] = args
    server["env"] = env
    server["cwd"] = str(cwd.resolve())
