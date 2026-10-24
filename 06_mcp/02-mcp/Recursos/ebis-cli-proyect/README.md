# EBIS CLI Práctica 2

Proyecto de la segunda práctica de EBIS-CLI. Parte de la solución de la práctica 1 y contiene huecos guiados para integrar un cliente MCP.

## Antes de empezar

Completa los TODO de `ebis_cli/mcp.py` y `ebis_cli/agent.py` siguiendo el enunciado de `../enunciado_practica_2_mcp.md`. Los módulos `mcp_config.py` y `mcp_tools.py`, la interfaz y las tools locales ya están preparados.

## Preparar el proyecto

Desde esta carpeta, ejecuta:

```bash
uv sync
```

Crea `.env` a partir de `.env.example` y añade tu clave en `OPENAI_API_KEY`. No compartas ni subas `.env`.

El servidor stdio está configurado en `mcp_config.json`; `mcp_config.http.json` se conserva como ejemplo de la alternativa HTTP. En esta práctica, Calendar MCP se inicia por stdio. Las rutas de configuración suponen que los proyectos están juntos dentro de `practica_2/`.

## Iniciar

Deja primero la API de calendario ejecutándose desde la carpeta `ebis-calendar-api`. Después, desde esta carpeta, inicia EBIS-CLI:

```bash
uv run python -m ebis_cli.app
```

Usa `/tools` para consultar las tools locales y MCP disponibles. La interfaz conecta con el servidor MCP al iniciar y cierra la conexión al salir.
