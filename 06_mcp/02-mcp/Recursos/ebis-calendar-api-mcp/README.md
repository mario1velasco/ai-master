# EBIS Calendar API MCP Práctica 2

Este proyecto contiene el cliente HTTP completo y el esqueleto incompleto del servidor MCP. Completa los TODO de `ebis_calendar_api_mcp/server.py` con ayuda de `../enunciado_practica_2_mcp.md`.

## Dependencias

Desde esta carpeta, instala las dependencias del servidor:

```bash
uv sync
```

El proyecto fija su propia versión de la SDK MCP. Mantén su entorno separado del entorno del cliente EBIS-CLI.

## API REST

El servidor MCP llama a EBIS Calendar API en `http://127.0.0.1:8000`. Inicia la API desde la carpeta `../ebis-calendar-api`:

```bash
uv sync
uv run python main.py
```

El modo HTTP permanece en el código como alternativa de referencia. La práctica usa stdio: EBIS-CLI inicia el proceso MCP automáticamente según `mcp_config.json`.
