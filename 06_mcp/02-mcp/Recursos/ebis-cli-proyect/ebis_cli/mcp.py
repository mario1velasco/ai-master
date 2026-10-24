"""Conecta el agente con un servidor MCP y ejecuta sus tools."""

from typing import Any

from mcp import Client, StdioServerParameters

from .mcp_config import load_mcp_config
from .mcp_tools import adapt_tools, format_tool_result


def _create_client(server: dict[str, Any]) -> Client:
    """Crea un cliente HTTP o uno que inicia el servidor como proceso stdio."""
    if server["transport"] == "http":
        # Transporte disponible como alternativa; la práctica usa stdio.
        return Client(server["url"])

    # TODO 1: crea StdioServerParameters con command, args, env y cwd de server;
    # después pásalo a Client.
    return Client(TODO_STDIO_PARAMETERS)


class MCPManager:
    """Mantiene la conexión MCP y adapta las tools para el agente."""

    def __init__(self) -> None:
        """Prepara el estado de conexión y las tools descubiertas."""
        self.client: Client | None = None
        self.server_name: str | None = None
        # Esquemas que se envían al modelo para que pueda elegir tools.
        self.tools_for_model: list[dict[str, Any]] = []
        # Nombre que devuelve el modelo -> nombre original que conoce el servidor MCP.
        self.model_tool_name_to_mcp_name: dict[str, str] = {}
        self.enabled = False

    async def start(self) -> str:
        """Lee la configuración y prepara la conexión MCP."""
        config = load_mcp_config()
        if not config["enabled"]:
            self.enabled = False
            return "Integración MCP desactivada en el archivo de configuración."

        server = config["server"]
        self.server_name = server["name"]
        await self._start(server)
        self.enabled = True
        return (
            f"Conectado al servidor MCP '{self.server_name}'; "
            f"tools descubiertas: {len(self.tools_for_model)}."
        )

    async def _start(self, server: dict[str, Any]) -> None:
        """Abre la sesión MCP y carga las tools que ofrece el servidor."""
        client = _create_client(server)
        self.client = client
        try:
            # El contexto mantiene abierta la conexión hasta MCPManager.close().
            # TODO 2: abre el cliente MCP con su método de entrada asíncrono.
            await client.TODO_ENTER()
            # TODO 3: solicita al servidor la lista de tools.
            result = await client.TODO_LIST_TOOLS()
            # TODO 4: adapta la lista de tools que devuelve la respuesta MCP.
            tools_for_model, model_tool_name_to_mcp_name = adapt_tools(result.TODO_TOOLS)
        except BaseException:
            await self.close()
            raise

        self.tools_for_model = tools_for_model
        self.model_tool_name_to_mcp_name = model_tool_name_to_mcp_name

    async def call_tool(self, model_tool_name: str, arguments: dict[str, Any]) -> str:
        """Envía los argumentos al servidor y devuelve el resultado como texto."""
        if self.client is None:
            return "Error de herramienta MCP: no hay una conexión activa."

        mcp_tool_name = self.model_tool_name_to_mcp_name.get(model_tool_name)
        if mcp_tool_name is None:
            return f"Error de herramienta MCP: tool desconocida '{model_tool_name}'."

        try:
            # TODO 5: usa el cliente MCP para ejecutar mcp_tool_name con arguments.
            result = await self.client.TODO_CALL_TOOL(mcp_tool_name, arguments=arguments)
            return format_tool_result(result)
        except Exception as error:
            return f"Error de herramienta MCP: {error}"

    async def close(self) -> None:
        """Cierra la sesión MCP y el proceso stdio asociado, si existe."""
        client, self.client = self.client, None
        try:
            if client is not None:
                await client.__aexit__(None, None, None)
        finally:
            self.tools_for_model = []
            self.model_tool_name_to_mcp_name = {}
            self.enabled = False
