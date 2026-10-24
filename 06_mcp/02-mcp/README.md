# Tema 02 – Model Context Protocol (MCP)

Segundo tema del módulo **06 · Integración con herramientas y MCP** del [Máster en Ingeniería de Automatización con IA Agéntica](https://www.ebiseducation.com/landing-master-en-ingenieria-de-automatizacion-con-ia-agentica) de EBIS Business Techschool.

El tema 01 construyó "a mano" el harness de un agente: bucle ReAct, historial, tools locales con `function calling`. Pero cada tool local vive dentro del propio agente, programada a medida. Este tema resuelve el problema de **conectar un agente a sistemas externos** (una API de calendario, GitHub, una base de datos...) sin tener que escribir una integración distinta para cada combinación de agente y herramienta: el estándar **MCP (Model Context Protocol)**. La práctica de este tema retoma EBIS-CLI (la práctica 1) y le añade la capacidad de descubrir y usar tools servidas por un servidor MCP externo, además de sus tools locales.

## Contenido de la carpeta

```text
02-mcp/
├── Tema 6_Model Context Protocol (MCP).pdf   # Teoría: slides del tema (76 páginas)
├── Enunciado_Practica_2_MCP.pdf              # Enunciado de la práctica guiada
├── recursos_extra_mcp.md                     # Enlaces a recursos complementarios
├── ebis-cli-mcp/                             # Proyecto de referencia: EBIS-CLI + MCP, ya completo
└── Recursos/
    ├── ebis-cli-proyect/                     # Ejercicio práctico (con TODOs por completar)
    ├── ebis-calendar-api/                    # API REST de calendario (completa, no se toca)
    └── ebis-calendar-api-mcp/                # Cliente HTTP (completo) + servidor MCP (con TODOs)
```

## 1. Teoría — `Tema 6_Model Context Protocol (MCP).pdf`

Slides organizadas en los siguientes bloques:

### Limitaciones de las tools y el problema M×N
Un agente puede necesitar conectarse a muchas capacidades externas (gestión de ficheros, ejecución de comandos, bases de datos, calendarios, correo, APIs...). Sin un estándar, cada combinación de **agente/CLI (M)** y **herramienta (N)** exige una integración a medida (código, diseño, seguridad y mantenimiento propios): el problema **M×N**.

### ¿Qué es MCP y por qué existe?
MCP es un **protocolo abierto que estandariza cómo las aplicaciones de IA se conectan con fuentes de datos y herramientas externas** ("el USB-C de las aplicaciones de IA"). Al introducir un contrato común entre agentes y herramientas, MCP convierte el problema **M×N en M+N**: cada agente implementa un cliente MCP una vez, cada herramienta implementa un servidor MCP una vez, y cualquier cliente MCP puede hablar con cualquier servidor MCP. Propuesto por Anthropic en noviembre de 2024, es una especificación pública con SDKs en varios lenguajes, hoy adoptada por Claude Code, Codex, Cursor, VSCode y otros. El material también da un criterio práctico para decidir cuándo conviene MCP y cuándo una tool nativa es suficiente (p. ej., una operación simple y local como parsear JSON no necesita MCP; conectar con un sistema externo con identidad propia como GitHub o Slack, sí).

### Comunicación MCP
Cliente y servidor hablan **JSON-RPC 2.0**: el cliente pide al servidor ejecutar un método por su nombre (`tools/list`, `tools/call`, `resources/read`...) y cada petición lleva un `id` que empareja la respuesta correspondiente. El material cubre dos generaciones del protocolo:
- **Versión 2025-11-25 (con sesión/handshake)**: el cliente abre la conexión con `initialize`, negocia versión y *capabilities*, y confirma con `notifications/initialized`; la sesión queda en memoria mientras dura la conversación.
- **Versión 2026-07-28 (stateless)**: se elimina el handshake; cada petición es autocontenida (lleva su propia versión e identidad del cliente en el campo `_meta`), y el cliente puede usar `server/discover` para preguntar las capacidades del servidor de forma atómica. Esto resuelve el problema de desplegar un servidor MCP en varias réplicas detrás de un balanceador, donde el modelo con sesión se atascaba si la petición `tools/call` llegaba a una réplica distinta de la que atendió el `initialize`.

El tema repasa también los métodos disponibles por categoría (generales, `tools/*`, `resources/*`, `prompts/*`, y otros como `sampling/createMessage` o paginación) y los dos transportes habituales: **stdio** (proceso local, sin red) y **HTTP** (para servidores remotos).

### Arquitectura del servidor MCP
Un servidor MCP no contiene lógica de negocio: es una **capa de adaptación** entre el protocolo MCP y un sistema real (una API, una base de datos...), con responsabilidades de exposición, descripción semántica, descubrimiento, ejecución y estandarización. El SDK `mcp` de Python ofrece una clase (`FastMCP` en la versión 2025-11-25, renombrada a `MCPServer` en la 2026-07-28) con decoradores al estilo FastAPI: `@mcp.tool()` (expone una función como tool, deduciendo su esquema JSON de los tipos de Python), `@mcp.resource("<uri>")` (expone datos legibles por URI) y `@mcp.prompt()` (expone una plantilla de prompt reutilizable).

### Añadir un servidor MCP a un CLI real, y MCP Inspector
El material muestra cómo configurar servidores MCP en herramientas reales (`.vscode/mcp.json` en VSCode, `.codex/config.toml` en Codex), tanto en modo stdio como HTTP, y presenta **MCP Inspector**: un cliente MCP "de laboratorio" (`npx @modelcontextprotocol/inspector`) que permite conectar, descubrir tools/resources y probarlos sin escribir ni un agente ni un cliente propio. Es la herramienta recomendada para depurar un servidor MCP durante el desarrollo (ver [recursos_extra_mcp.md](recursos_extra_mcp.md)).

### Arquitectura del cliente MCP
Distingue **Host** (la aplicación principal — Codex, VSCode, tu propio CLI — que gestiona el bucle agéntico y levanta un cliente MCP por cada servidor configurado) de **Cliente MCP** (el componente que mantiene la conexión 1:1 con un servidor concreto). Muestra el código real de levantar un cliente MCP por stdio y por HTTP en ambas generaciones del SDK: la 2025-11-25 usa `StdioServerParameters` + `stdio_client` + `ClientSession` con `initialize()` explícito; la 2026-07-28 simplifica a una única clase `Client` que gestiona transporte y conexión sin handshake explícito, y que además incorpora un modo `mode="auto"` para negociar automáticamente con servidores que todavía no se hayan actualizado al protocolo stateless.

### MCPs y otras estrategias
Cierra con ejemplos de servidores MCP de uso frecuente (**Context7**, que inyecta documentación oficial y actualizada en el contexto del agente para evitar alucinaciones de código; **Playwright MCP**, que da capacidades de automatización de navegador sin modelos de visión) y con **SKILLS.md**, un formato alternativo de documentación pensado para que un agente aprenda a usar un CLI ya instalado sin necesidad de montar un servidor MCP para ello.

## 2. Recursos extra — `recursos_extra_mcp.md`

Tres enlaces que complementan el tema: la documentación oficial de MCP, el directorio de *skills* [skills.sh](https://www.skills.sh/) (como alternativa a MCP para capacidades reutilizables) y **MCP Inspector**, la herramienta oficial para depurar servidores MCP durante el desarrollo — especialmente útil para esta práctica.

## 3. Proyectos de código

| Carpeta | Qué es | Estado |
|---|---|---|
| `ebis-cli-mcp/` | EBIS-CLI (la práctica 1) ya conectado a un servidor MCP: `mcp.py`, `agent.py` y `mcp_tools.py` completos. | Código de referencia, funcional tal cual. |
| `Recursos/ebis-calendar-api/` | API REST (FastAPI) de ejemplo: trabajadores y reuniones en memoria, con validación de horario laboral y solapamientos. | Código de referencia, funcional tal cual. |
| `Recursos/ebis-calendar-api-mcp/` | Servidor MCP que expone la API de calendario como tools. `client.py` (peticiones HTTP) está completo; `server.py` tiene 4 TODOs. | `client.py` referencia; `server.py` ejercicio. |
| `Recursos/ebis-cli-proyect/` | Copia de la solución de la práctica 1, con 5 TODOs en `mcp.py` y 5 TODOs en `agent.py` para integrar el cliente MCP. | Incompleto a propósito — es el ejercicio. |

`ebis-cli-mcp/` resuelve exactamente la misma integración que pide el ejercicio, así que es el mejor sitio para comparar una vez entendido el patrón (no para copiar directamente la solución).

## 4. El ejercicio — `Recursos/ebis-cli-proyect/` y `Recursos/ebis-calendar-api-mcp/server.py`

Enunciado completo en [`Enunciado_Practica_2_MCP.pdf`](Enunciado_Practica_2_MCP.pdf). Resumen de lo que hay que completar, sin resolverlo:

- **`ebis_cli/mcp.py`** (cliente MCP dentro de EBIS-CLI): crear los parámetros de arranque por stdio (`StdioServerParameters`), abrir la conexión (`__aenter__`), pedir la lista de tools (`list_tools`), adaptar esa lista (`adapt_tools`) y ejecutar una tool concreta (`call_tool`).
- **`ebis_cli/agent.py`**: inicializar el gestor MCP, combinar las tools locales con las descubiertas por MCP, pasar ambas al modelo en la misma petición, y enrutar cada llamada del modelo al dispatcher local o al servidor MCP según corresponda.
- **`ebis_calendar_api_mcp/server.py`** (servidor MCP de calendario): crear la instancia del servidor y hacer que sus tres tools (`list_workers`, `get_worker_meetings`, `schedule_meeting`) deleguen en las funciones ya escritas de `client.py`.

Antes de arrancar, revisa el **orden de estudio recomendado** más abajo: entender la arquitectura general de MCP (teoría) y el código ya resuelto de `ebis-cli-mcp/` ayuda mucho a decidir qué llamada exacta de la SDK va en cada hueco.

> **Nota sobre el material:** el enunciado (p. 8) menciona que `/tools` debe mostrar "las cinco tools locales de la práctica 1" y sugiere probar `count_words`. Sin embargo, tanto `ebis-cli-mcp/` (referencia) como `Recursos/ebis-cli-proyect/` solo definen **tres** tools locales (`list_files`, `read_file`, `write_file`) en `ebis_cli/tools.py` — no incluyen `count_words` ni `calculate_total` de la práctica 1. Es una discrepancia del material tal como se entrega; al comprobar `/tools` espera tres tools locales, no cinco.

### Cómo ejecutarlo

Se necesitan tres procesos, cada uno en su propio entorno `uv` (tienen dependencias y versiones de `mcp` independientes):

```bash
# Terminal 1 — API REST de calendario
cd Recursos/ebis-calendar-api
uv sync
uv run python main.py          # http://127.0.0.1:8000 (docs en /docs)

# Terminal 2 — EBIS-CLI (arranca el servidor MCP automáticamente por stdio)
cd Recursos/ebis-cli-proyect
uv sync
cp .env.example .env            # añade tu OPENAI_API_KEY
uv run python -m ebis_cli.app
```

No hace falta una tercera terminal para el servidor MCP: en modo `stdio` (el usado en esta práctica, configurado en `mcp_config.json`) EBIS-CLI lo arranca y lo cierra como proceso hijo. Dentro de la TUI, `/tools` debe listar las tools locales más `mcp_list_workers`, `mcp_get_worker_meetings` y `mcp_schedule_meeting`.

### Depurar el servidor MCP con MCP Inspector (opcional)

Si algo falla en `ebis-calendar-api-mcp/server.py` y quieres probarlo aislado, sin pasar por EBIS-CLI, el propio PDF de teoría (apartado "MCP Inspector") hace exactamente esta demo con los mismos tres proyectos de esta práctica:

```bash
# Terminal 1: la API REST (igual que arriba)
# Terminal 2: el servidor MCP en modo HTTP
cd Recursos/ebis-calendar-api-mcp
uv sync
export MCP_TRANSPORT=http
uv run python -m ebis_calendar_api_mcp.server   # escucha en 127.0.0.1:8001/mcp

# Terminal 3: MCP Inspector (requiere Node.js 22.19+)
npx -y @modelcontextprotocol/inspector \
  --protocol-era auto \
  --server-url http://127.0.0.1:8001/mcp \
  --transport http
```

Inspector abre una interfaz web donde puedes ver las tools publicadas, su esquema, y ejecutarlas a mano — útil para comprobar que `server.py` responde bien antes de conectarlo a EBIS-CLI.

## Orden de estudio recomendado

1. Leer `Tema 6_Model Context Protocol (MCP).pdf` para entender los conceptos (problema M×N, arquitectura cliente/servidor, JSON-RPC, handshake vs. stateless, decoradores del SDK).
2. Recorrer `ebis-cli-mcp/` (código ya resuelto) y comparar `mcp.py`/`agent.py` con lo explicado en la teoría.
3. Leer `Recursos/ebis-calendar-api/` para entender qué API real se va a exponer como MCP.
4. Completar el ejercicio en `Recursos/ebis-cli-proyect/` y `Recursos/ebis-calendar-api-mcp/server.py` siguiendo `Enunciado_Practica_2_MCP.pdf`.
5. Usar `recursos_extra_mcp.md` (documentación oficial, MCP Inspector) como referencia mientras trabajas.
