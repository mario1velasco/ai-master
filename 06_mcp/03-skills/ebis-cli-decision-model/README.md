# EBIS CLI · Decision Model

Evolución didáctica de `ebis-cli-mcp`, que parte del harness v4 usado en clase. Añade conexiones a varios servidores MCP, subagentes lanzados como procesos hijos, conversaciones persistentes y una interfaz Textual modular. El **Jev Decision Model** vive en `ebis_cli/decision_model/` para poder estudiarlo aparte.

## Inicio rápido

Requisitos: Python 3.11+, `uv`, una clave de OpenAI y una clave de TypeSafe para activar Jev.

```powershell
uv sync
Copy-Item .env.example .env
# Añade OPENAI_API_KEY y TYPESAFE_API_KEY a .env
uv run python -m ebis_cli.app
```

El agente usa como workspace la carpeta actual desde la que se ejecuta. Para lanzar el código desde otra carpeta y mantenerla como workspace:

```powershell
uv run --project "C:\ruta\ebis-cli-decision-model" python -m ebis_cli.app
```

En ese caso, coloca un `.env` con ambas claves en la carpeta actual (el workspace) o expórtalas en el entorno antes de iniciar el comando.

Al primer uso crea `.ebis_cli/` dentro del workspace, con `workspace.json` y `conversations/`. Cada conversación conserva la transcripción visible y el historial necesario para continuar con la Responses API. Los archivos de `.ebis_cli` y `.env` se omiten en las tools de archivos.

## El ciclo de decisiones Jev

El módulo está dividido en dos decisiones pequeñas para facilitar su explicación:

1. `decision_model/choices.py` presenta a Jev el objetivo, el contexto reciente y las acciones disponibles. Jev elige una tool, `build_context` o `final_answer`. Si la tool no requiere argumentos, el harness puede ejecutarla directamente; si requiere datos, el siguiente request de OpenAI recibe solo esa definicion.
2. `decision_model/routing.py` vuelve a consultar Jev para cada request a OpenAI y selecciona un nivel permitido del archivo `routing-llm.json`.
3. `prompts.py` adapta las instrucciones al resultado de Choice: pide una llamada de función, una nota de contexto con hechos y auto-preguntas, o la respuesta final.

El SDK de TypeSafe para Python documenta la primitiva `Choice`; aquí el routing se enseña como una Choice sobre una allowlist local. La lista de modelos no procede de la respuesta de Jev: solo se aceptan las claves ya definidas en el JSON.

La guía de pizarra está en [DECISION_MODEL.md](DECISION_MODEL.md).

```json
{
  "default": "medium_reasoning",
  "models": {
    "cheap_no_reasoning": { "model": "gpt-6-luna", "reasoning_effort": "none" },
    "cheap_reasoning": { "model": "gpt-6-luna", "reasoning_effort": "low" },
    "medium_no_reasoning": { "model": "gpt-6-sol", "reasoning_effort": "none" },
    "medium_reasoning": { "model": "gpt-6.1-sol", "reasoning_effort": "medium" },
    "expensive_no_reasoning": { "model": "gpt-5.6-sol", "reasoning_effort": "none" },
    "expensive_reasoning": { "model": "gpt-6-astra", "reasoning_effort": "high" }
  }
}
```

Cada descripción del JSON indica cuándo conviene elegir la combinación. `reasoning_effort` se envía explícitamente en la request: `none` no solicita razonamiento, `low` permite inferencias sencillas y `medium` se reserva para planificación, diagnóstico y trabajo con varios pasos. GPT-6 Astra y GPT-6.1 Sol no aceptan `none`; por eso la opción medium sin razonamiento usa GPT-6 Sol y la opción cara sin razonamiento usa GPT-5.6 Sol. Edita `routing-llm.json` para cambiar opciones o el modelo predeterminado. Si falta `TYPESAFE_API_KEY`, el agente continúa con function calling automático y el modelo/effort `default`; los mensajes de la interfaz indican cuándo se usa ese fallback.

Referencias: [TypeSafe Python SDK](https://docs.typesafe.ai/sdk/python), [Choice](https://docs.typesafe.ai/primitives/choice), [modelos de OpenAI](https://platform.openai.com/docs/models), [precios de modelos](https://platform.openai.com/pricing).

## Varios servidores MCP

`settings.py` define `MAX_MCP_SERVERS = 10`. `mcp_config.json` admite hasta diez entradas en `servers`; cada conexión descubre y conserva sus tools mientras la interfaz está abierta. Se pueden mezclar servidores stdio y HTTP, y un fallo individual se muestra sin descartar las conexiones correctas.

```json
{
  "enabled": true,
  "servers": [
    {
      "name": "calendario",
      "transport": "stdio",
      "command": "uv",
      "args": ["--directory", "../ebis-calendar-api-mcp", "run", "python", "-m", "ebis_calendar_api_mcp.server"],
      "env": {"EBIS_CALENDAR_API_URL": "http://127.0.0.1:8000"}
    },
    {
      "name": "documentos",
      "transport": "http",
      "url": "http://127.0.0.1:9000/mcp"
    }
  ]
}
```

El nombre expuesto al modelo incorpora el servidor (`mcp_calendario_...`) para evitar colisiones entre tools con el mismo nombre. La configuración antigua con la clave singular `server` sigue siendo válida como entrada de migración.

## Subagentes como procesos

`delegate_task` crea un proceso Python independiente (`python -m ebis_cli.agent.subagent`). El subproceso recibe la tarea por stdin, usa las tools locales del workspace y envía eventos JSON Lines al proceso principal. La TUI muestra el lanzamiento y cada avance; el comando `/agents` lista identificador, estado y PID, y `/agents sa-001` muestra el detalle.

### Organización del código

- `ebis_cli/agent/`: runtime principal, eventos y proceso de subagente.
- `ebis_cli/app/`: interfaz Textual, pantallas y widgets.
- `ebis_cli/decision_model/`: selección discreta de acciones y modelos.
- `ebis_cli/integrations/mcp/`: cliente, configuración y adaptación de herramientas MCP.
- `ebis_cli/tools/`: herramientas locales del workspace.
- `ebis_cli/workspace/`: contexto e historial persistente de conversaciones.
- `ebis_cli/settings.py` y `ebis_cli/prompts.py`: configuración y prompts compartidos.

## Comparar el Decision Model y consultar estadísticas

- `/decision` alterna Jev; `/decision on`, `/decision off` y `/decision status` permiten fijar o consultar el estado. Al desactivarlo, Choice usa selección automática de tools y Routing utiliza el modelo `default` del JSON. El cambio se aplica en las siguientes decisiones; los subagentes nuevos heredan el estado.
- `/stats` presenta el uso acumulado del workspace y separa las llamadas realizadas con Decision Model activado y desactivado. Registra entrada, salida, tokens de razonamiento reportados por Responses API, caché y coste estimado por modelo y nivel en `.ebis_cli/usage.json`. Los tokens de razonamiento forman parte de los tokens de salida facturados; se muestran aparte para poder comparar su peso.
- El ahorro de Routing es una estimación contrafactual: aplica los mismos tokens observados al precio del nivel `savings_baseline` (por defecto `expensive_reasoning`) y compara con el coste real configurado. Las tarifas por millón de tokens se pueden editar en `routing-llm.json`.
- Choice cuenta las tools preseleccionadas. Si la tool no requiere argumentos, el harness la ejecuta sin una request OpenAI y suma una llamada evitada. Para tools con argumentos, el LLM aún los genera y esa request se cuenta normalmente. El contador de llamadas evitadas no estima los tokens que habría usado la request omitida.

Las tarifas iniciales se basan en la documentación oficial de [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol), [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) y [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra). Actualiza el JSON si OpenAI modifica los precios o las opciones de razonamiento.

## Interfaz y comandos

- Barra de progreso que avanza en cada fase del bucle.
- Los resultados extensos de tools, routing, contexto y subagentes aparecen plegados; pulsa su encabezado para desplegarlos.
- La respuesta final se transmite token a token mientras se genera.
- El scroll sigue los mensajes mientras estás al final. Si subes para leer, conserva tu posición aunque el agente siga trabajando.
- Puedes consultar `/agents` mientras hay una tarea en marcha; el campo de entrada sigue disponible para comandos.

| Comando / tecla | Acción |
| --- | --- |
| `/new`, `Ctrl+N` | Crear conversación |
| `/history`, `Ctrl+H` | Abrir y cargar una conversación anterior |
| `/agents [id]`, `Ctrl+A` | Consultar subagentes |
| `/decision [on|off|toggle|status]` | Activar, desactivar o consultar Jev Decision Model |
| `/stats` | Ver tokens, costes por modelo y ahorros estimados de routing o tools directas |
| `/tools`, `F2` | Ver tools locales y MCP |
| `/clear`, `Ctrl+L` | Limpiar solo la vista |
| `/help`, `F1` | Mostrar ayuda |
| `/exit` | Cerrar la aplicación |

## Tools locales

Incluye `list_files`, `read_file`, `write_file`, `search_files`, `make_directory`, `count_words` y `run_command`. Esta última ejecuta comandos de desarrollo desde el workspace, con tiempo límite configurable en la llamada y tope de 120 segundos.

## Estructura para la clase

```text
ebis_cli/
├── agent/                  # Runtime, eventos y subprocesos de agentes
├── app/                    # Interfaz Textual, pantallas y widgets
├── decision_model/         # Choice, Routing y adaptador TypeSafe
├── integrations/mcp/       # Cliente y configuración MCP
├── tools/                  # Tools locales de programación
├── workspace/              # Contexto, conversaciones y estadísticas
├── prompts.py              # Prompts compartidos
├── settings.py             # Rutas, límites y valores por defecto
└── style.tcss              # Estilos Textual
```
