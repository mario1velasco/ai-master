# AGENTS.md — 02-mcp

Instrucciones de orientación para cualquier agente (Claude Code u otro) que trabaje en esta carpeta. El contexto completo y la teoría están en [`README.md`](README.md); este archivo es la guía operativa rápida.

## Qué es esta carpeta

Tema 02 del módulo 06 (Integración con herramientas y MCP) del máster de EBIS. Trata sobre **Model Context Protocol (MCP)**: el estándar que permite a un agente descubrir y usar tools servidas por un proceso externo (un servidor MCP), en vez de depender solo de tools locales como en el tema 01. La práctica retoma EBIS-CLI (práctica 1) y le añade un cliente MCP conectado a un servidor MCP de calendario.

Todo el código es Python gestionado con `uv`. Hay **tres proyectos independientes**, cada uno con su propio entorno y su propia versión fijada de `mcp` en `pyproject.toml` — ejecuta `uv sync` en cada uno por separado, no asumas que compartir dependencias funciona.

## Los cuatro componentes de código — no los confundas

| Carpeta | Qué es | Estado |
|---|---|---|
| `ebis-cli-mcp/` | EBIS-CLI con el cliente MCP ya integrado (`mcp.py`, `agent.py`, `mcp_tools.py` completos, sin TODOs). | Código de referencia, funcional tal cual. |
| `Recursos/ebis-calendar-api/` | API REST (FastAPI) de trabajadores/reuniones, en memoria, con validación de horario y solapamientos. | Código de referencia, funcional tal cual. |
| `Recursos/ebis-calendar-api-mcp/` | Servidor MCP de calendario. `client.py` (llamadas HTTP a la API) completo. `server.py` con 4 TODOs. | `client.py` referencia; `server.py` ejercicio. |
| `Recursos/ebis-cli-proyect/` | Copia de la solución de la práctica 1, con 5 TODOs en `mcp.py` y 5 TODOs en `agent.py`. | Incompleto a propósito — es el ejercicio del alumno (Mario). |

Si el usuario pide "explica cómo funciona X" sobre la integración MCP en general, usa `ebis-cli-mcp/` como ejemplo ya resuelto (comparar con `Recursos/ebis-cli-proyect/`, que sigue la misma estructura, es la forma más rápida de ver qué falta).

Si el usuario pide ayuda para **resolver el ejercicio**, el trabajo va en `Recursos/ebis-cli-proyect/` y `Recursos/ebis-calendar-api-mcp/server.py`, nunca en `ebis-cli-mcp/` ni en `Recursos/ebis-calendar-api/` (son material de referencia, no se tocan). No le des la solución literal: apóyate en `ebis-cli-mcp/` como referencia conceptual y en los propios decoradores/ejemplos del PDF de teoría.

## Dónde están los TODOs del ejercicio

Enunciado completo en [`Enunciado_Practica_2_MCP.pdf`](Enunciado_Practica_2_MCP.pdf). Ubicación exacta de cada TODO:

**`Recursos/ebis-cli-proyect/ebis_cli/mcp.py`**
- `TODO_STDIO_PARAMETERS` (línea 19, función `_create_client`): construir `StdioServerParameters(command=..., args=..., env=..., cwd=...)` a partir del diccionario `server`, y pasarlo a `Client(...)`.
- `TODO_ENTER` (línea 58, método `_start`): abrir el cliente con su método de entrada asíncrono.
- `TODO_LIST_TOOLS` (línea 60, método `_start`): pedir al servidor la lista de tools.
- `result.TODO_TOOLS` (línea 62, método `_start`): pasar la lista de tools de la respuesta a `adapt_tools(...)`.
- `TODO_CALL_TOOL` (línea 81, método `call_tool`): invocar la tool en el servidor con el nombre MCP y `arguments`.

**`Recursos/ebis-cli-proyect/ebis_cli/agent.py`**
- Línea 25 (`Agent.__init__`): inicializar `MCPManager()` en `self.mcp`.
- Líneas 27-29 (`start_mcp`): esperar `self.mcp.start()` y devolver su mensaje.
- Líneas 38-39 (`available_tool_schemas`): devolver `TOOLS + self.mcp.tools_for_model`.
- Líneas 93-94 (`run`, llamada a `responses.create`): pasar `self.available_tool_schemas()` como `tools`.
- Líneas 109-110 (`run`, bucle de llamadas): si `call.name` está en `self.mcp.model_tool_name_to_mcp_name`, ejecutar `await self.mcp.call_tool(call.name, arguments)`; si no, `dispatch_tool(call.name, arguments)`.

**`Recursos/ebis-calendar-api-mcp/ebis_calendar_api_mcp/server.py`**
- Líneas 19-20: crear la instancia `MCPServer(...)` compartida por los transportes stdio y HTTP.
- Líneas 26-27 (`list_workers`): delegar en `client.list_workers()`.
- Líneas 33-34 (`get_worker_meetings`): delegar en `client.get_worker_meetings(worker_id=..., day=...)`.
- Líneas 46-48 (`schedule_meeting`): delegar en `client.schedule_meeting(worker_id=..., title=..., start=..., end=...)`.

No modifiques `mcp_config.py`, `mcp_tools.py`, `app.py`, `context.py` ni `client.py` — ya están completos y el enunciado los da por buenos. Tampoco `Recursos/ebis-calendar-api/` (API REST, completa).

## Cómo ejecutar cada proyecto

```bash
# API REST (siempre debe estar activa antes de arrancar EBIS-CLI)
cd Recursos/ebis-calendar-api && uv sync && uv run python main.py

# EBIS-CLI (arranca el servidor MCP por stdio automáticamente)
cd Recursos/ebis-cli-proyect  # o ebis-cli-mcp/ para probar la referencia
uv sync
cp .env.example .env   # añadir OPENAI_API_KEY
uv run python -m ebis_cli.app
```

Dentro de la app: `/tools` lista las tools locales + MCP anunciadas al modelo, `/help` la ayuda, `/clear` limpia la vista, `/exit` cierra (y cierra también la conexión MCP).

Para depurar el servidor MCP de forma aislada (sin EBIS-CLI), usa MCP Inspector contra `Recursos/ebis-calendar-api-mcp/` en modo HTTP — ver la sección correspondiente en [`README.md`](README.md).

## Dos discrepancias conocidas del material (no las "corrijas" por tu cuenta)

- El enunciado (p. 8) espera **cinco** tools locales ("las cinco tools locales de la práctica 1", con `count_words` de ejemplo). El código entregado (`ebis-cli-mcp/` y `Recursos/ebis-cli-proyect/`) solo define **tres**: `list_files`, `read_file`, `write_file`. Si el usuario reporta que `/tools` no muestra `count_words`/`calculate_total`, no es un bug suyo: el código base simplemente no las incluye.
- El `README.md` de `ebis-cli-mcp/` afirma que "el servidor de calendario conserva `FastMCP` y SDK v1". El código real de `Recursos/ebis-calendar-api-mcp/ebis_calendar_api_mcp/server.py` importa `from mcp.server import MCPServer` y su `pyproject.toml` fija `mcp>=2.0.0,<3.0.0` — es decir, usa el SDK v2 (`MCPServer`, no `FastMCP`), igual que el cliente. Si citas esa frase del README, aclara que no coincide con el código actual.

Si en algún momento se corrige el código para resolver alguna de estas dos discrepancias, actualiza esta sección y el aviso correspondiente en `README.md`/`explicacion.md` en el mismo cambio.

## Mantenimiento de la documentación

Cada vez que modifiques código en esta carpeta (en cualquiera de los cuatro proyectos), comprueba si `README.md`, este `AGENTS.md` y/o `explicacion.md` se han quedado desactualizados (rutas, TODOs resueltos, cambios en las tools, correcciones de las discrepancias anteriores, etc.) y actualízalos en el mismo cambio.

- Antes de escribir, analiza el alcance real del cambio: si es puntual (un TODO resuelto, un dato concreto que cambió), edita solo esas líneas — no reescribas secciones enteras ni generes ruido innecesario en el diff.
- Si el cambio es lo bastante grande como para que mantener la estructura actual del documento genere más ruido que claridad (se añade un TODO nuevo, cambia la relación entre los cuatro proyectos, se añade un cuarto componente), entonces sí merece la pena replantear esa sección antes de tocarla, en lugar de ir parcheando encima.
- Si no hay nada que actualizar, no toques los docs "porque sí".
