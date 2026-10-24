# EBIS CLI MCP

Copia didáctica de `ebis-cli-harness-v4` que conserva sus tools locales y añade conexión a **un servidor MCP**. `ebis_cli/mcp.py` muestra el ciclo del cliente MCP: conecta por stdio o HTTP, descubre tools, las invoca y cierra la sesión al terminar el agente. La lectura y validación del JSON está en `mcp_config.py`; la conversión de tools al formato de OpenAI y el mapeo de nombres, en `mcp_tools.py`.

## Configuración incluida

`mcp_config.json` queda activo por defecto y carga `ebis-calendar-api-mcp` por stdio. El proceso MCP se inicia y se cierra junto con el agente. La ruta `../ebis-calendar-api-mcp` se interpreta desde la carpeta del proyecto del agente.

`mcp_config.http.json` contiene la versión HTTP alternativa. Para usarla, inicia el servidor MCP en otra terminal con `MCP_TRANSPORT=http` y selecciona el archivo alternativo con `MCP_CONFIG_PATH`:

```powershell
cd ..\ebis-calendar-api-mcp
$env:MCP_TRANSPORT = "http"
uv run python -m ebis_calendar_api_mcp.server
```

En otra terminal:

```powershell
cd ..\ebis-cli-mcp
$env:MCP_CONFIG_PATH = ".\mcp_config.http.json"
uv run python -m ebis_cli.app
```

También puedes copiar el contenido HTTP a `mcp_config.json`. Si `enabled` es `false`, el agente usa solo sus tools locales. El archivo puede contener `cwd` opcional para fijar la carpeta de trabajo del proceso stdio; por defecto se usa la carpeta que contiene el archivo de configuración.

## Ejecutar con stdio (opción predeterminada)

Primero inicia la API de calendario en una terminal:

```powershell
cd ..\ebis-calendar-api
uv run uvicorn main:app --reload
```

En otra terminal, desde esta carpeta:

```powershell
uv sync
uv run python -m ebis_cli.app
```

El agente lanza automáticamente el servidor MCP por stdio. El servidor MCP llama a la API en `http://127.0.0.1:8000`.

## Qué observar en el código

- `MCPManager.start()` carga la configuración y delega en `_start()`, donde `_create_client()` elige HTTP o stdio, se abre el contexto del cliente y se llama a `list_tools()`. Con stdio, `StdioServerParameters` indica el comando del servidor que se inicia como proceso hijo.
- `mcp_config.py` lee y valida el archivo; así, el código de conexión queda separado de los detalles de configuración.
- `mcp_tools.py` convierte los esquemas MCP al formato de función de Responses API y normaliza los nombres de las tools.
- En el loop del agente, las llamadas `mcp_*` se envían al servidor; las demás van a `dispatch_tool`.
- Al cerrar la TUI se cierra también el proceso stdio.

El cliente de este proyecto usa el SDK MCP v2. El servidor de calendario conserva `FastMCP` y SDK v1 para que coincida con el ejemplo de clase; el cliente v2 negocia también con servidores de la generación anterior.
