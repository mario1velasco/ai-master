"""Conecta hasta diez clientes MCP y unifica las tools de sus servidores."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from mcp import Client, StdioServerParameters

from .config import load_mcp_config
from .schemas import adapt_tools, format_tool_result


def _create_client(server: dict[str, Any]) -> Client:
    if server["transport"] == "http":
        return Client(server["url"])
    return Client(
        StdioServerParameters(
            command=server["command"],
            args=server["args"],
            env=server["env"],
            cwd=server["cwd"],
        )
    )


@dataclass
class MCPConnection:
    name: str
    client: Client
    model_tool_to_remote_tool: dict[str, str] = field(default_factory=dict)


class MCPManager:
    """Mantiene abiertas varias sesiones MCP y resuelve cada tool al servidor."""

    def __init__(self) -> None:
        self.connections: dict[str, MCPConnection] = {}
        self.tools_for_model: list[dict[str, Any]] = []
        self.model_tool_name_to_server: dict[str, tuple[str, str]] = {}
        self.enabled = False

    async def start(self) -> str:
        config = load_mcp_config()
        if not config["enabled"]:
            return "Integración MCP desactivada en la configuración."

        servers = config["servers"]
        results = await asyncio.gather(
            *(self._start_one(server) for server in servers), return_exceptions=True
        )
        statuses: list[str] = []
        for server, result in zip(servers, results):
            if isinstance(result, BaseException):
                statuses.append(f"{server['name']}: error de conexión ({result})")
            else:
                statuses.append(result)

        self.enabled = bool(self.connections)
        connected = len(self.connections)
        total = len(servers)
        header = f"MCP: conectados {connected}/{total} servidores."
        return header + ("\n" + "\n".join(statuses) if statuses else "")

    async def _start_one(self, server: dict[str, Any]) -> str:
        name = server["name"]
        client = _create_client(server)
        entered = False
        try:
            await client.__aenter__()
            entered = True
            result = await client.list_tools()
            tool_schemas, name_map = adapt_tools(
                result.tools,
                server_name=name,
                existing_names={tool["name"] for tool in self.tools_for_model},
            )
            connection = MCPConnection(name=name, client=client, model_tool_to_remote_tool=name_map)
            self.connections[name] = connection
            self.tools_for_model.extend(tool_schemas)
            for model_name, remote_name in name_map.items():
                self.model_tool_name_to_server[model_name] = (name, remote_name)
            return f"{name}: conectados; {len(tool_schemas)} tools descubiertas."
        except BaseException:
            if entered:
                try:
                    await client.__aexit__(None, None, None)
                except Exception:
                    pass
            raise

    async def call_tool(self, model_tool_name: str, arguments: dict[str, Any]) -> str:
        target = self.model_tool_name_to_server.get(model_tool_name)
        if target is None:
            return f"Error de herramienta MCP: tool desconocida '{model_tool_name}'."
        server_name, remote_tool_name = target
        connection = self.connections.get(server_name)
        if connection is None:
            return f"Error de herramienta MCP: '{server_name}' no está conectado."
        try:
            result = await connection.client.call_tool(remote_tool_name, arguments=arguments)
            return format_tool_result(result)
        except Exception as error:
            return f"Error de herramienta MCP ({server_name}.{remote_tool_name}): {error}"

    async def close(self) -> None:
        connections, self.connections = self.connections, {}

        async def close_one(connection: MCPConnection) -> None:
            try:
                await asyncio.wait_for(
                    connection.client.__aexit__(None, None, None), timeout=4
                )
            except Exception:
                pass

        await asyncio.gather(*(close_one(item) for item in connections.values()))
        self.tools_for_model = []
        self.model_tool_name_to_server = {}
        self.enabled = False
