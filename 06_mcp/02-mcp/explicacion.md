# Explicación completa — Tema 02: Model Context Protocol (MCP)

Este documento explica **todo** el contenido de esta carpeta (los dos PDFs, los recursos extra y el código de los cuatro proyectos) con un lenguaje sencillo, paso a paso, y sin dar nada por sabido. Todo lo que aquí se afirma viene directamente de `Tema 6_Model Context Protocol (MCP).pdf`, `Enunciado_Practica_2_MCP.pdf`, `recursos_extra_mcp.md`, o del código real de `ebis-cli-mcp/`, `Recursos/ebis-cli-proyect/`, `Recursos/ebis-calendar-api/` y `Recursos/ebis-calendar-api-mcp/`. Cuando se usa un ejemplo propio para aclarar un concepto, se dice explícitamente que es un ejemplo ilustrativo.

Si solo quieres un resumen rápido, lee el [`README.md`](README.md) de esta carpeta. Este documento es la versión larga, pensada para entender el "por qué" de cada pieza — y, si tienes el ejercicio pendiente, para entender el patrón sin que se te dé la solución hecha.

---

## 1. El problema de partida: el límite de las tools locales

En el tema 01 vimos cómo un agente usa **tools** (function calling) para dejar de ser "solo texto" y poder actuar: leer archivos, hacer cálculos, etc. Pero esas tools eran **locales**: funciones Python escritas a mano dentro del propio proyecto del agente.

El material de este tema abre con una pregunta directa:

> "¿Cuál es el límite? ¿Cuántas conexiones podemos hacer para potenciar nuestros agentes?"

Y da una lista de capacidades que un agente real podría necesitar, más allá de gestionar ficheros: ejecutar comandos por terminal, conectarse a una base de datos, conectar un calendario (Google, Outlook), enviar correos automáticos, buscar en una API externa... Cada una de esas capacidades es, en el fondo, un sistema distinto, mantenido por alguien distinto, con su propia forma de autenticarse y de responder.

### El problema M×N

Si no existe un estándar común, cada **agente o CLI agéntico (M)** que quiera usar cada **herramienta externa (N)** necesita su propia integración a medida:

> Agente (M) × Cada Herramienta (N) = Nueva Integración

El material lo dibuja como un grafo completo: varios CLIs/agentes (Cursor, Claude Code, OpenCode, Kimi Code...) conectados, cada uno por su cuenta, a varias herramientas (GitHub API, Jira, PostgreSQL, Slack, Google Drive...). Cada línea de ese grafo es:

> "Nueva Integración = código a medida + Diseño + Seguridad + Mantenimiento"

Si hay 4 agentes y 5 herramientas, eso son potencialmente **20 integraciones distintas** que mantener, cada una con su propio código, su propio diseño y su propia superficie de seguridad. Este es el problema que MCP viene a resolver.

---

## 2. ¿Qué es MCP y por qué existe?

### Definición y origen

> "Protocolo abierto que estandariza cómo las aplicaciones de IA se conectan con fuentes de datos y herramientas externas."

Datos clave que da el material:
- **Origen**: propuesto por Anthropic, noviembre de 2024.
- **Naturaleza**: especificación pública, con SDKs en múltiples lenguajes.
- **Adopción**: actualmente es un estándar, usado por Claude Code, Codex, Cursor, VSCode y otros.

> "Cualquiera puede implementar un servidor o un cliente MCP"

### De M×N a M+N

Si todos los agentes y todas las herramientas hablan el mismo protocolo, cada agente solo necesita implementar **un** cliente MCP (que sabe hablar con cualquier servidor MCP), y cada herramienta solo necesita implementar **un** servidor MCP (que cualquier cliente MCP puede usar). El material lo resume en una fórmula:

> "MCP convierte M×N en M+N"

Y con una frase que se repite como eslogan del protocolo:

> "El USB-C de las aplicaciones de IA"

Es una buena analogía con un matiz importante: un puerto USB-C no sabe nada sobre lo que conecta (un teclado, una pantalla, un disco duro); solo estandariza el conector. MCP hace lo mismo con la conexión entre un agente y una herramienta: estandariza *cómo* se habla, no *qué* hace cada herramienta por dentro.

### ¿Cuándo hace falta MCP y cuándo basta con una tool nativa?

El material da una tabla de criterios muy práctica para no usar MCP "porque sí":

| Pregunta | Si la respuesta es "sí" | Tendencia |
|---|---|---|
| ¿Representa un **sistema externo con identidad propia**? | GitHub, Slack, Stripe | MCP |
| ¿Debe **reutilizarse desde varios agentes o aplicaciones**? | Claude, Codex, Cursor, agente propio | MCP |
| ¿Está **íntimamente ligada al runtime, sandbox o UI del agente**? | Shell, archivos locales, `ask_user` | Tool nativa |
| ¿Es una **operación simple, pura o trivial**? | Calcular, parsear JSON, hacer diff de ficheros | Tool nativa |

Esto explica, de paso, por qué en esta misma práctica `list_files`/`read_file`/`write_file` siguen siendo tools **locales** (son operaciones simples, ligadas a la carpeta de trabajo del agente) mientras que `list_workers`/`get_worker_meetings`/`schedule_meeting` se exponen como tools **MCP** (representan un sistema externo con identidad propia — EBIS Calendar API — pensado para poder reutilizarse desde cualquier agente, no solo desde EBIS-CLI).

---

## 3. Arquitectura general: Host, Cliente MCP, Servidor MCP

El material ilustra la arquitectura con un ejemplo concreto: VSCode (con su Chat/Copilot) conectándose, a través de MCP, a Google Calendar.

```text
Cliente / Host                Contrato MCP                 Herramienta externa
┌─────────────────┐    ┌───────────────────────────┐    ┌──────────────────┐
│ VSCode           │    │ MCP                        │    │ Google Calendar   │
│ Chat/Copilot      │───▶│ 1. Initialize/Capabilities │───▶│ Server MCP        │
│ LLM/Planner       │    │ 2. Tools                   │    │ Google API         │
│ Cliente MCP       │    │ 3. Resources                │    │ Adaptador de dominio│
│                    │    │ 4. Tool call / Result       │    │ OAuth / permisos    │
└─────────────────┘    └───────────────────────────┘    └──────────────────┘
        Transporte: stdio / HTTP
```

Tres piezas, con roles muy distintos:

- **Host**: la aplicación con la que interactúa el usuario (Claude Code, Codex, Cursor, tu propia app...). Gestiona la interfaz de usuario y el bucle agéntico — es, básicamente, el "agente" tal y como lo vimos en el tema 01.
- **Cliente MCP**: vive *dentro* del host y mantiene una **conexión 1:1 con un servidor**. Si el host tiene configurados 5 servidores MCP, levanta 5 clientes MCP internamente — uno por servidor.
- **Servidor MCP**: expone `tools`/`function calls`, `resources` y `prompts` usando un idioma estándar que entiende cualquier cliente MCP. El servidor es quien sabe hablar con el sistema real (en el ejemplo, la API de Google Calendar); el host nunca necesita implementar esa API directamente.

En esta práctica concreta, el mapeo es literal:

| Pieza genérica | En esta práctica |
|---|---|
| Host | EBIS-CLI (`ebis_cli/app.py` + `agent.py`) |
| Cliente MCP | `MCPManager` (`ebis_cli/mcp.py`) |
| Servidor MCP | Calendar MCP (`ebis_calendar_api_mcp/server.py`) |
| Sistema real detrás del servidor | EBIS Calendar API (`ebis-calendar-api/api.py`, una API REST) |

---

## 4. Cómo hablan cliente y servidor: JSON-RPC y el ciclo de vida de la conexión

### JSON-RPC 2.0

> "Cliente y Servidor MCP se comunican siguiendo un lenguaje universal común utilizando el protocolo JSON-RPC 2.0."
>
> "Es un protocolo para comunicar sistemas donde el cliente le pide al servidor ejecutar una función específica por su nombre, enviándole los datos en formato JSON a través de una única ruta HTTP (usualmente un POST a /api). A diferencia de REST, que se organiza en torno a "recursos", JSON-RPC se enfoca en "acciones"."

Ejemplo del material:

```text
POST /api/v1/rpc HTTP/1.1          →          HTTP/1.1 200 OK
Content-Type: application/json                Content-Type: application/json
{                                              {
  "jsonrpc": "2.0",                              "jsonrpc": "2.0",
  "method": "sumarNumeros",                      "result": 65,
  "params": { ... },                             "id": 1
  "id": 1                                      }
}
```

El campo `id` es clave:

> "JSON-RPC está diseñado para funcionar de manera asíncrona, desordenada o masiva, el "id" es la etiqueta que le permite al cliente saber a qué pregunta corresponde cada respuesta del servidor."

### Dos generaciones del protocolo: con sesión (handshake) y sin sesión (stateless)

El material cubre explícitamente dos versiones fechadas del protocolo MCP, porque cambian una pieza central de cómo se conectan cliente y servidor.

#### Versión 2025-11-25 — con handshake

Antes de poder pedir nada, cliente y servidor negocian una sesión:

1. **Petición**: el cliente envía `initialize`, detallando sus capacidades y versión del protocolo.
2. **Respuesta**: el servidor confirma la versión y expone sus propias capacidades.
3. **Confirmación**: el cliente envía `notifications/initialized` para confirmar el acuerdo.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": { "tools": {}, "resources": {}, "prompts": {} },
    "serverInfo": { "name": "mi-servidor-completo", "version": "1.0.0" }
  }
}
```

> "Dentro del objeto `capabilities` no se envían las herramientas ni los datos, sino únicamente indicadores sobre las `tools`/`resources`/`prompts`."

¿Por qué existe este handshake? El material da tres razones:

1. **Negociación de versiones**: cliente y servidor pueden evolucionar a velocidades distintas; antes de hablar, acuerdan qué versión común del protocolo van a usar.
2. **Capabilities**: cliente y servidor se anuncian mutuamente qué tools/resources ofrecen, a modo de "discovery".
3. **Sincronización en local**: en MCPs locales (como el de esta práctica), el agente arranca el servidor como un subproceso; el handshake asegura que todo está listo antes de recibir órdenes. Al ser una conexión privada entre dos procesos, tener la sesión en memoria es "la arquitectura más simple, limpia y eficiente".

#### Versión 2026-07-28 — stateless (sin handshake)

La siguiente revisión del protocolo elimina la sesión en memoria:

1. **Sin sesión previa**: se eliminan `initialize` y `notifications/initialized`. Ya no se abre una sesión en memoria; cualquier petición puede ser la primera.
2. **Metadatos por petición**: el cliente adjunta en *cada* llamada su "carta de presentación" (versión del protocolo y capacidades) dentro del campo `_meta`.
3. **Descubrimiento bajo demanda**: si el cliente necesita conocer qué ofrece el servidor antes de llamarlo, invoca el método directo `server/discover`.

```json
// server/discover
{ "jsonrpc": "2.0", "id": 1, "result": {
    "protocolVersion": "2026-07-28",
    "capabilities": { "tools": {}, "resources": {}, "prompts": {} },
    "serverInfo": { "name": "mi-servidor-completo", "version": "1.0.0" } } }

// tools/call, ya con _meta en cada petición
{ "jsonrpc": "2.0", "id": "msg-042", "method": "tools/call",
  "params": { "name": "sumar", "arguments": { "a": 5, "b": 10 } },
  "_meta": { "protocolVersion": "2026-07-28",
             "clientInfo": { "name": "Cursor", "version": "1.2.0" } } }
```

¿Por qué eliminar el handshake? El motivo que da el material es un problema real de despliegue a gran escala: cuando una empresa despliega su propio servidor MCP, lo normal es ejecutarlo con varias réplicas detrás de un balanceador de carga. Con el modelo de sesión, esto se vuelve un cuello de botella:

```text
Cliente → initialize (handshake) → Load Balancer → Pod A (guarda la sesión)
Cliente → tools/call              → Load Balancer → Pod B (¡no conoce la sesión!) → Fallo de sesión
```

La "solución parche" tradicional (*sticky sessions* o una base de datos de sesión centralizada) añade complejidad. Por eso, hasta esta actualización, muchos servidores MCP —incluso integraciones de grandes proveedores— se ejecutaban directamente en el ordenador del usuario (MCP local), como en el ejemplo del material:

```toml
[mcpServers.google-workspace]
type = "stdio"
command = "gws"
args = ["mcp", "-s", "drive,gmail,calendar"]
```

Con el modelo **sin handshake**, cada petición es autocontenida: lleva su propia versión y su propia identidad de cliente en `_meta`, así que **cualquier réplica puede atenderla**, sin depender de dónde se guardó una sesión anterior. Esto es justo lo que hace viable ofrecer un servidor MCP como servicio remoto detrás de un balanceador, como en el ejemplo de GitHub del material:

```toml
[servers.github]
type = "http"
url = "https://api.githubcopilot.com/mcp/"
```

### El ciclo genérico de una llamada a tool

Independientemente de la versión del protocolo, el ciclo para usar una tool concreta es siempre el mismo patrón de tres pasos:

1. **Tool List**: el cliente solicita la lista de tools disponibles (`tools/list`).
2. **Tool Call**: el cliente envía un método (`tools/call`) con la tool a ejecutar, sus `params` y un `id` único.
3. **Tool Result**: el servidor ejecuta y devuelve el `result` con ese mismo `id`.

Ejemplo del material, con una tool `obtener_clima`:

```json
// tools/list → el servidor anuncia la tool y su esquema
{ "name": "obtener_clima", "description": "Obtiene las condiciones meteorológicas actuales.",
  "inputSchema": { "type": "object",
    "properties": { "ciudad": {"type": "string"}, "unidades": {"type": "string", "enum": ["celsius","fahrenheit"]} },
    "required": ["ciudad"] } }

// tools/call
{ "jsonrpc": "2.0", "id": "msg-002", "method": "tools/call",
  "params": { "name": "obtener_clima", "arguments": { "ciudad": "Madrid", "unidades": "celsius" } } }

// Response
{ "jsonrpc": "2.0", "id": "msg-002",
  "result": { "content": [{ "type": "text", "text": "{\"temperatura\": \"35.6\"}" }], "isError": false } }
```

### El catálogo de métodos MCP

El material organiza los métodos disponibles del protocolo por categorías. No hace falta memorizarlos, pero conviene saber que existen (y cuáles son nuevos de la versión *stateless*):

**Generales**

| Método | Descripción | Estado |
|---|---|---|
| `initialize` | El cliente lo envía al arrancar (versión, capacidades...). | De la versión con sesión (2025-11-25); eliminado en la versión stateless, como ya vimos en la sección anterior |
| `notifications/initialized` | El cliente avisa al servidor de que la sesión está activa. | De la versión con sesión (2025-11-25); eliminado en la versión stateless |
| `ping` | Comprobar que la conexión sigue viva y el servidor responde. | El material lo marca con un icono de aviso (⚠️), sin explicar el motivo por escrito |
| `server/discover` | Permite al cliente preguntar al servidor qué versión habla, cómo se llama y qué capacidades tiene, de forma atómica y **sin abrir ninguna sesión**. | Nuevo en 2026-07-28 |
| `notifications/progress` | Permite al servidor o al cliente reportar el avance (porcentaje o pasos) de una tarea que tarda tiempo en completarse. | Nuevo en 2026-07-28 |
| `cancelled` | Se utiliza para abortar una petición. | — |

**Tools**

| Método | Descripción |
|---|---|
| `tools/list` | El cliente solicita la lista de tools y sus esquemas. |
| `tools/call` | El cliente solicita la invocación de una herramienta. |
| `notifications/tools/list_changed` | El servidor anuncia un cambio en las tools disponibles. |

**Resources**

| Método | Descripción |
|---|---|
| `resources/list` | El cliente solicita la lista de recursos. |
| `resources/templates/list` | Devuelve plantillas de URIs dinámicas (p. ej. `mcp://logs/{fecha}`). |
| `resources/read` | Solicitud de leer el contenido de un recurso. |
| `notifications/resources/list_changed` | El servidor anuncia un cambio en los recursos. |

Ejemplo de uso natural desde un chat: `Lee mi base de datos en @mcp://proyecto/database_schema y dime cómo optimizarla`.

**Prompts**

| Método | Descripción |
|---|---|
| `prompt/list` | Devuelve la lista de plantillas de prompts disponibles y qué variables requieren. |
| `prompts/get` | El cliente solicita el contenido de un prompt concreto. |

Ejemplo de uso: invocar directamente `/prompt_review_codigo_v5` desde el cliente.

**Y algo más**

| Método | Descripción |
|---|---|
| `sampling/createMessage` | Intercambio de roles: el servidor se convierte temporalmente en el "usuario" para pedirle razonamiento interno al modelo. |
| (paginación) | Permite paginar listados largos de elementos. |

### Transportes: stdio vs. HTTP

> **stdio**: "Comunicación local y privada donde dos programas en el mismo ordenador interactúan directamente entre ellos, sin usar internet ni puertos de red."
>
> **HTTP (con SSE)**: "Un protocolo de comunicación por red (lo habitual cuando MCPs externos)."

Dos ejemplos de configuración del material:

```toml
# stdio: el host arranca el proceso del servidor
[mcpServers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
enabled = true
[mcpServers.context7.env]
CONTEXT7_API_KEY = "tu_api_key_aqui"

# http: el host se conecta a un servidor que ya está levantado
[mcp_servers.stitch]
url = "https://stitch.googleapis.com/mcp"
[mcp_servers.stitch.http_headers]
"X-Goog-Api-Key" = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Esta práctica usa **stdio** por defecto (`ebis-cli-proyect/mcp_config.json`, con `transport: "stdio"`): EBIS-CLI arranca `ebis_calendar_api_mcp.server` como proceso hijo. También se entrega `mcp_config.http.json` como comparación, apuntando a `http://127.0.0.1:8001/mcp`, para el caso en que el servidor ya esté levantado aparte (ver sección 11).

---

## 5. Arquitectura del servidor MCP

### Responsabilidades

> "El servidor MCP no contiene la lógica de negocio; simplemente es la capa estándar de adaptación."

El material desglosa esa capa de adaptación en cinco responsabilidades:

- **Exposición**: decide qué funcionalidades estarán disponibles (p. ej. `create_user`).
- **Descripción**: explica semánticamente qué hace cada función, para que el LLM entienda cuándo usarla.
- **Descubrimiento**: permite al cliente preguntar por herramientas y recursos (`tools/list`, `resources/list`...).
- **Ejecución**: transforma `tools/call` en llamadas reales al servicio subyacente (una API, una base de datos...).
- **Estandarización**: convierte formatos propietarios al estándar MCP.

Y remata con una idea importante para no confundirse:

> "MCP no reemplaza tu API, construye una interfaz estándar para IA sobre ella."

En esta práctica, eso es literal: `ebis_calendar_api_mcp/server.py` no reimplementa la lógica de agendar reuniones (validar horario laboral, solapamientos...); esa lógica sigue viviendo en `ebis-calendar-api/api.py` y `db.py`. El servidor MCP solo **traduce** `tools/call` a peticiones HTTP contra esa API ya existente.

### La librería `mcp` de Python

> "La librería `mcp` es el SDK que usamos para crear servers MCP en Python sin tener que desarrollar todo el protocolo desde cero" (`pip install mcp`).

El material muestra la evolución de la clase principal entre las dos versiones del protocolo:

```python
# Versión 2025-11-25: la clase se llama FastMCP
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo MCP")

@mcp.tool()
def saludar(nombre: str) -> str:
    """Devuelve un saludo."""
    return f"Hola, {nombre}"

mcp.run()  # stdio por defecto
```

```python
# Versión 2026-07-28: FastMCP se renombra a MCPServer;
# la configuración (host, puertos...) se mueve al método run(...)
from mcp.server import MCPServer

mcp = MCPServer("Demo MCP")

@mcp.tool()
def saludar(nombre: str) -> str:
    """Devuelve un saludo."""
    return f"Hola, {nombre}"

mcp.run(
    transport="streamable-http",
    host="127.0.0.1",
    port=8001,
    stateless_http=True,
    json_response=True,
)
```

Esto coincide exactamente con lo que hace el código de esta práctica: `ebis_calendar_api_mcp/server.py` importa `from mcp.server import MCPServer` (la clase de la versión 2026-07-28) y en `main()` elige entre `mcp.run()` (stdio, usado en la práctica) o `mcp.run(transport="streamable-http", host="127.0.0.1", port=8001, stateless_http=True, json_response=True)` (HTTP, alternativa ilustrativa).

> **Nota de precisión:** el `README.md` de `ebis-cli-mcp/` (el proyecto de referencia) dice que "el servidor de calendario conserva `FastMCP` y SDK v1 para que coincida con el ejemplo de clase". Al leer el código real, eso no es así: `server.py` importa `MCPServer` (no `FastMCP`) y `pyproject.toml` fija `mcp>=2.0.0,<3.0.0` — el mismo SDK v2 que usa el cliente. Es una frase del README que no coincide con el código entregado.

### Los tres decoradores

Al igual que en FastAPI, el SDK usa decoradores para declarar capacidades sin escribir el protocolo a mano.

**`@mcp.tool()`** — expone una función como acción invocable:

> "El decorador tiene 2 usos: no se escribe JSON schema a mano (la librería lo deduce de los parámetros tipados de la función); ejecuta dicha función en caso de que la tool sea llamada (la función realizará la llamada correspondiente al servidor real)."

```python
@mcp.tool()
def sumar(a: int, b: int) -> int:
    """Suma dos numeros."""
    return a + b
```

genera automáticamente este esquema (sin que el autor lo escriba a mano):

```json
{ "name": "sumar", "description": "Suma dos numeros.",
  "inputSchema": { "type": "object",
    "properties": { "a": {"type": "integer"}, "b": {"type": "integer"} },
    "required": ["a", "b"] } }
```

> "El decorador registra la función dentro del servidor MCP."

**`@mcp.resource("<uri>")`** — expone datos legibles por una URI (no una acción, sino información):

```python
@mcp.resource("config://app")
def get_app_config() -> str:
    """Devuelve la configuracion publica de la aplicacion."""
    return "APP_NAME=Inventory Demo\nENVIRONMENT=development\nAPI_URL=http://127.0.0.1:8000"
```

> "El decorador tiene 2 usos: declara un recurso que el cliente MCP puede leer usando una URI (ejemplo: `config://app`); ejecuta la función decorada cuando ese recurso es consultado."

Esto es exactamente lo que hace `ebis_calendar_api_mcp/server.py` con `ebis-calendar://config`: un recurso (no una tool) que describe la URL de la API y las tools disponibles, pensado para que un cliente lo lea como información, no como una acción a ejecutar.

**`@mcp.prompt()`** — expone una plantilla de prompt reutilizable:

```python
@mcp.prompt()
def crear_plan_estudio(tema: str, nivel: str) -> str:
    """Crea un prompt para generar un plan de estudio."""
    return (
        f"Quiero aprender sobre {tema}.\n"
        f"Mi nivel actual es {nivel}.\n"
        "Genera un plan de estudio de 5 pasos, con ejemplos practicos."
    )
```

> "El decorador tiene 2 usos: declara una plantilla de prompt que el cliente MCP puede reutilizar con parámetros; ejecuta la función decorada cuando el prompt es solicitado."

El servidor de esta práctica no usa `@mcp.prompt()` (solo tools y un resource), pero conviene conocerlo porque es parte del mismo mecanismo de decoradores.

---

## 6. Añadir un servidor MCP a un CLI real

El material muestra cómo clientes reales leen su configuración de servidores MCP desde un archivo, no desde código:

```json
// VSCode → .vscode/mcp.json (stdio)
{ "servers": { "miServer": { "type": "stdio", "command": "uv",
  "args": ["--directory", "C:\\ruta\\a\\mi-server-mcp", "run", "python", "main.py"],
  "env": { "API_URL": "http://127.0.0.1:8000", "API_TOKEN": "Bearer mi-token" } } } }
```

```toml
# Codex → .codex/config.toml (stdio)
[mcp_servers.mi-server]
command = "uv"
args = ["--directory", "C:\\ruta\\a\\mi-server-mcp", "run", "python", "main.py"]
[mcp_servers.mi-server.env]
SERVICE_API_URL = "http://127.0.0.1:8000"
MCP_SERVER_API_TOKEN = "Bearer mi-token"
```

Y sus equivalentes en modo HTTP (con un token inyectado como variable de entorno o pedido interactivamente). La idea general, remarcada por el material:

> "El Host lee la configuración y por cada server: 1. Crea un cliente MCP. 2. Abre una sesión. 3. Descubre tools/resources/prompts. 4. Mantiene esa conexión durante la conversación."

Esto es exactamente lo que hace `mcp_config.json` en esta práctica (sección 11) y lo que `ebis_cli/mcp_config.py` valida antes de arrancar el cliente.

---

## 7. MCP Inspector

### Qué es

> "Un cliente MCP de laboratorio: prueba servidores reales sin montar un agente ni escribir tu propio cliente."

Tres capacidades:
- **Conectar**: abre una sesión con un servidor usando el transporte MCP elegido.
- **Descubrir**: muestra las capacidades publicadas — tools, resources y sus esquemas.
- **Probar y observar**: ejecuta llamadas y permite inspeccionar los mensajes entre cliente y servidor.

> "Idea clave: Inspector es una interfaz visual para actuar como cliente MCP."

### La demo del material usa exactamente los proyectos de esta práctica

El material hace una demo completa con tres procesos — y son, literalmente, los tres mismos proyectos que trae esta carpeta:

```text
MCP INSPECTOR  --Streamable HTTP-->  EBIS CALENDAR  --HTTP-->  CALENDAR API
(cliente de pruebas con interfaz web)  (servidor MCP, traduce tools a REST)   (API REST, 127.0.0.1:8000)
```

> "MCP estandariza el acceso: el Inspector descubre y llama tools con mensajes MCP."
>
> "La API conserva la lógica: el servidor MCP actúa como adaptador; no reemplaza la API."

Pasos de la demo (adaptados a los nombres reales de esta práctica — ver también el `README.md` de esta carpeta):

1. **Arranca la API de calendario**: `cd Recursos/ebis-calendar-api && uv sync && uv run python main.py` → queda activa en `http://127.0.0.1:8000` (comprobable con `curl http://127.0.0.1:8000/health`).
2. **Arranca el servidor MCP en modo HTTP**: `cd Recursos/ebis-calendar-api-mcp && uv sync && export MCP_TRANSPORT=http && uv run python -m ebis_calendar_api_mcp.server` → escucha en `http://127.0.0.1:8001/mcp`. "Deja esta terminal y la de la API abiertas. El servidor MCP llamará a la API REST."
3. **Conecta el Inspector oficial** (requiere Node.js 22.19+): `npx -y @modelcontextprotocol/inspector --protocol-era auto --server-url http://127.0.0.1:8001/mcp --transport http`. Se abre una URL local con un token temporal (no se comparte); el estado debe pasar a "Connected".
4. **Descubre tools y revisa sus esquemas**: la pestaña *Tools* muestra `list_workers` (sin argumentos), `get_worker_meetings` (`worker_id` requerido, `day` opcional en formato AAAA-MM-DD) y `schedule_meeting` (`worker_id`, `title`, `start`, `end`).
5. **Ejecuta `tools/call` y lee el resultado**: pulsas *Execute Tool* → Inspector envía `tools/call` → el servidor consulta la API REST → Inspector muestra la respuesta (en la demo del material, con `list_workers`, aparecen Ana García, Luis Martín y Marta López — los mismos trabajadores de ejemplo de `db.py` en esta práctica).
6. **Lee un resource**: en la pestaña *Resources*, seleccionar `get_config` hace que Inspector lea y muestre el contenido de `ebis-calendar://config`. El material lo resume así: *"Tool = acción: se invoca para realizar una operación (ej. `list_workers`). Resource = información: se lee desde una URI (ej. `ebis-calendar://config`)."*
7. **Prueba una tool con argumentos**: `get_worker_meetings` es una consulta de solo lectura; `schedule_meeting` crea una reunión real en la API — "elige un hueco futuro entre semana (09:00–17:00) y sin solapamientos. Los datos viven en memoria y se pierden al parar la API."

El material también muestra la variante **stdio** del Inspector (sin arrancar el servidor a mano en otra terminal): `npx -y @modelcontextprotocol/inspector --protocol-era auto uv --directory ./ebis-calendar-api-mcp run python -m ebis_calendar_api_mcp.server`. Aquí es el propio Inspector quien arranca el proceso del servidor y habla con él por `stdio` — el mismo patrón que usa EBIS-CLI en esta práctica.

Usar Inspector contra `Recursos/ebis-calendar-api-mcp/` es, en la práctica, la forma más rápida de comprobar si el `server.py` del ejercicio (sección 11) está bien resuelto *antes* de conectarlo a EBIS-CLI — aísla el problema a un único componente.

---

## 8. Arquitectura del cliente MCP

### Host vs. Cliente MCP

> **Host**: "Es la aplicación principal (Codex, VSCode, Cursor o tu CLI). Gestiona la interfaz de usuario y el bucle agéntico. Es el responsable de levantar un Cliente MCP por cada MCP que exista configurado."
>
> **Cliente MCP**: "Es una componente del HOST que permite levantar una instancia MCP que mantiene una conexión 1:1 con un servidor MCP. Si configuras en Codex 5 MCPs, se iniciarán 5 clientes MCP dentro de él."

La misma librería `mcp` que sirve para escribir servidores también sirve para escribir clientes.

### Levantando un cliente MCP por stdio: dos generaciones del SDK

**Versión 2025-11-25** (con handshake explícito):

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["--directory", "C:/ruta/a/mi-server-mcp", "run", "python", "main.py"],
        env={"API_URL": "http://127.0.0.1:8000", "API_TOKEN": "Bearer mi-token"},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(tools)
```

- `StdioServerParameters` "es un molde que guarda la config para ejecutar el Server MCP por STDIO".
- `stdio_client(server_params)` inicia el proceso del servidor MCP (recuerda: en un servidor MCP por stdio es el **host** quien lo "arranca", no al revés).
- `ClientSession(read, write)` abre una sesión MCP para la comunicación.
- `session.initialize()` + `session.list_tools()` inician la comunicación (handshake) y piden el listado de tools.

**Versión 2026-07-28** (sin handshake):

```python
from mcp import Client, StdioServerParameters

async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["--directory", "C:/ruta/a/mi-server-mcp", "run", "python", "main.py"],
        env={"API_URL": "http://127.0.0.1:8000"},
    )
    async with Client(server_params) as client:
        tools = await client.list_tools()
        print(tools)
```

> "El nuevo cliente `Client` gestiona internamente el transporte y la conexión con el servidor MCP." / "YA NO HAY HANDSHAKE. Se pide directamente el listado de tools."

**Este es exactamente el patrón que usa el código real de esta práctica.** `ebis-cli-mcp/ebis_cli/mcp.py` (la referencia ya resuelta) hace:

```python
from mcp import Client, StdioServerParameters

return Client(
    StdioServerParameters(
        command=server["command"], args=server["args"],
        env=server["env"], cwd=server["cwd"],
    )
)
# ...
await client.__aenter__()
result = await client.list_tools()
```

Es decir: el agente de este proyecto usa directamente la clase `Client` de la versión 2026-07-28, sin pasar por `ClientSession`/`initialize()`. `__aenter__()`/`__aexit__()` son los métodos que usa Python para los gestores de contexto asíncronos (`async with`); `MCPManager` los llama a mano porque necesita mantener la conexión abierta durante toda la vida del agente, no solo dentro de un único `async with`.

### Levantando un cliente MCP por HTTP

El mismo patrón, pero conectándose a un servidor que ya existe en vez de arrancar un proceso nuevo:

```python
# 2025-11-25
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
async with streamable_http_client(url) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()

# 2026-07-28
from mcp import Client
async with Client(url) as client:
    tools = await client.list_tools()
```

> "Se conecta a un MCP server que ya existe. No arranca nada." / "No requiere de HANDSHAKE."

Esto corresponde a la rama HTTP de `_create_client` en `ebis_cli/mcp.py`, ya resuelta en ambos proyectos: `return Client(server["url"])`.

### ¿Y si el servidor no habla todavía el protocolo stateless?

El SDK v2 incorpora un modo automático pensado justo para la transición entre versiones del protocolo:

```python
async with Client(url, mode="auto") as client:
    tools = await client.list_tools()
```

> "Ahora el nuevo cliente incorpora un modo automático (`mode="auto"`) que detecta si el servidor usa MCP moderno y, si es legacy, hace por sí solo el fallback y ejecuta `initialize()`."

Esto explica por qué, aunque el servidor de calendario de esta práctica ya usa el SDK v2 (`MCPServer`, ver sección 5), el cliente `Client` seguiría funcionando igual contra un servidor más antiguo que todavía necesitara el handshake explícito — es el propio SDK quien negocia la diferencia, sin que el código de `MCPManager` tenga que distinguir casos.

### Ejecutar una tool concreta desde el cliente

Con el estilo basado en `ClientSession` (más verboso pero más explícito sobre lo que ocurre):

```python
tools = await session.list_tools()
# ListToolsResult(tools=[Tool(name="sumar", description="Suma dos numeros.",
#     inputSchema={"type": "object", "properties": {"a": {...}, "b": {...}}, "required": ["a", "b"]})])

result = await session.call_tool("sumar", arguments={"a": 2, "b": 3})
```

> "En un Agente, el LLM es quien genera el diccionario de argumentos gracias a haberle pasado el schema de la tool."

Esa última frase es la bisagra entre MCP y lo que vimos en el tema 01 sobre *function calling*: el esquema que el servidor MCP publica en `tools/list` es, para el modelo, indistinguible de un esquema de tool local — por eso se puede mezclar ambos tipos de tools en la misma petición al modelo (ver sección 9).

---

## 9. Cómo un agente combina tools locales y tools MCP

El material compara, en pseudocódigo, un agente "sin MCP" (como el del tema 01) con uno "con MCP":

```python
# AGENTE SIN MCP
tools = get_local_tool_schemas()
for _step in range(5):
    response = llm.chat(messages=messages, tools=tools)
    ...
    for tool_call in tool_calls:
        result = execute_local_tool(name=tool_call.function.name, arguments=tool_call.function.arguments)
```

```python
# AGENTE CON MCP
mcp_clients = [MCPClient(name="math")]
local_tools = get_local_tool_schemas()

mcp_tools = []
for mcp_client in mcp_clients:
    discovered_tools = await mcp_client.list_tools()
    mcp_tools.extend(discovered_tools)

tools = local_tools + mcp_tools
for _step in range(5):
    response = llm.chat(messages=messages, tools=tools)
    ...
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        if is_mcp_tool(tool_name):
            result = await call_mcp_tool(clients=mcp_clients, name=tool_name, arguments=arguments)
        else:
            result = execute_local_tool(name=tool_name, arguments=arguments)
```

> "El Host define sus propias tools locales. El Host descubre tools desde servidores MCP. El LLM puede usar tools que viven dentro y fuera de la app."

La diferencia clave respecto al tema 01 son solo dos líneas: `tools = local_tools + mcp_tools` (combinar ambos catálogos antes de llamar al modelo) y la rama `if is_mcp_tool(tool_name)` al despachar una llamada (decidir *quién* ejecuta la tool: el dispatcher local o el servidor MCP). El resto del bucle ReAct es idéntico al del tema anterior.

Esto es exactamente lo que hace `ebis_cli/agent.py` en el proyecto de referencia (`ebis-cli-mcp/`):

```python
def available_tool_schemas(self):
    return TOOLS + self.mcp.tools_for_model          # local_tools + mcp_tools

...
for call in calls:
    arguments = json.loads(call.arguments)
    if call.name in self.mcp.model_tool_name_to_mcp_name:    # is_mcp_tool(...)
        result = await self.mcp.call_tool(call.name, arguments)
    else:
        result = dispatch_tool(call.name, arguments)
```

Dos detalles de la implementación real que el pseudocódigo del material no cubre, y que vale la pena entender porque son justo las piezas que conecta `MCPManager`:

- **Los nombres se normalizan con un prefijo.** `ebis_cli/mcp_tools.py::custom_unique_tool_name` antepone `mcp_` a cada nombre de tool descubierta (p. ej. `list_workers` → `mcp_list_workers`) y evita colisiones añadiendo `_2`, `_3`... si dos nombres distintos quedaran iguales tras sanear caracteres no válidos. El modelo solo ve nombres con el prefijo `mcp_`; `MCPManager.model_tool_name_to_mcp_name` guarda el mapa inverso para traducirlos de vuelta al nombre que de verdad entiende el servidor cuando hay que invocarlo.
- **El resultado de una tool MCP no siempre es texto plano.** `ebis_cli/mcp_tools.py::format_tool_result` decide cómo convertir la respuesta MCP (que puede traer `structured_content`, bloques de `content` de tipo texto, o un `is_error`) en la cadena de texto que espera `function_call_output`. Si el servidor marca el resultado como error, antepone `"Error de herramienta MCP: "` para que el agente (y el modelo) puedan distinguirlo de una respuesta normal.

---

## 10. MCPs recomendados y otras estrategias

El material cierra con ejemplos de servidores MCP de uso frecuente y una alternativa a MCP para cierto tipo de capacidades.

### Context7

> "Context7 es un servidor MCP que inyecta documentación oficial y actualizada directamente en el contexto de tu asistente de IA, eliminando alucinaciones y el uso de código obsoleto."

Configuración típica (stdio):

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
[mcp_servers.context7.env]
CONTEXT7_API_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

En la demo del material, al preguntar por el changelog de FastAPI y el decorador `@app.<verbo>`, el agente llama a `context7.query-docs(...)` y responde con información verificada contra la documentación real del proyecto, en vez de "recordar" (y posiblemente alucinar) una versión desactualizada.

### Playwright MCP

> "A Model Context Protocol server that provides browser automation capabilities using Playwright. Enables LLMs to interact with web pages through structured accessibility snapshots — no vision models required."

```toml
[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest"]
```

En la demo, el agente navega a una web real (el buscador de diputados del Congreso), rellena un formulario y lee los resultados mediante *snapshots* de accesibilidad (listas de elementos de la página con su rol y texto), sin necesidad de "ver" la página como una imagen.

### SKILLS.md: una alternativa a MCP para ciertos casos

> "Documentación automática diseñada específicamente para que agentes de IA entiendan capacidades, flujos de trabajo y restricciones."

Tres propiedades: **contexto bajo demanda** (elimina la necesidad de repetir instrucciones en cada conversación), **estándar técnico** (formato Markdown estructurado) y **guía operativa** (define "cómo" debe actuar la IA ante herramientas externas). El directorio [skills.sh](https://www.skills.sh/) (mencionado también en `recursos_extra_mcp.md`) funciona como catálogo de *skills* reutilizables.

La relación con MCP es interesante: si un `SKILLS.md` describe cómo usar un **CLI** (un comando) ya instalado en el ordenador, el agente puede aprender a usarlo ejecutando ese comando directamente —gracias a su capacidad general de ejecutar comandos—, **asimilando capacidades equivalentes a las de un MCP sin necesidad de montar un servidor MCP para ello**. El propio Playwright, por ejemplo, se puede instalar como *skill* (`playwright-cli install --skills`) para que un agente lo use por línea de comandos, como alternativa a conectarlo como servidor MCP.

---

## 11. De la teoría al código real de esta práctica

### Los cuatro proyectos y su papel

| Proyecto | Rol | Equivalente en la arquitectura MCP |
|---|---|---|
| `ebis-cli-mcp/` | EBIS-CLI con el cliente MCP ya integrado (referencia completa) | Host + Cliente MCP |
| `Recursos/ebis-cli-proyect/` | La misma integración, con 5+5 TODOs (el ejercicio) | Host + Cliente MCP (incompleto) |
| `Recursos/ebis-calendar-api-mcp/` | Servidor MCP de calendario; `client.py` completo, `server.py` con 4 TODOs | Servidor MCP |
| `Recursos/ebis-calendar-api/` | API REST de trabajadores y reuniones, en memoria | El "sistema real" detrás del servidor MCP |

### `mcp_config.json`: cómo EBIS-CLI sabe qué servidor arrancar

```json
{
  "enabled": true,
  "server": {
    "name": "ebis-calendar-api-mcp",
    "transport": "stdio",
    "command": "uv",
    "args": ["--directory", "../ebis-calendar-api-mcp", "run", "python", "-m", "ebis_calendar_api_mcp.server"],
    "env": { "EBIS_CALENDAR_API_URL": "http://127.0.0.1:8000" }
  }
}
```

Cada campo responde una pregunta distinta (tal como explica el enunciado de la práctica):

- `enabled: true` permite que el agente intente conectar con el servidor configurado; en `false`, EBIS-CLI conserva solo sus tools locales.
- `server.name` es una etiqueta para el mensaje de estado del agente — no es un nombre de paquete Python.
- `transport: "stdio"` elige entrada/salida estándar: no hace falta reservar un puerto, EBIS-CLI inicia el servidor como proceso hijo.
- `command`/`args` son, literalmente, el comando de terminal que lanzaría el servidor a mano, partido en una lista: `uv --directory ../ebis-calendar-api-mcp run python -m ebis_calendar_api_mcp.server`. `--directory ../ebis-calendar-api-mcp` le dice a `uv` que use las dependencias (y la versión de `mcp`) del `pyproject.toml` del servidor, no las del cliente, aunque sea el cliente quien lo arranque.
- `env.EBIS_CALENDAR_API_URL` es la variable que `ebis_calendar_api_mcp/config.py` lee para saber dónde está la API REST (puerto 8000 — un puerto completamente distinto del transporte MCP, que aquí ni siquiera usa red).

`ebis_cli/mcp_config.py` (ya completo, no se toca) valida estos campos y convierte `cwd` en una ruta absoluta relativa a la carpeta donde vive el propio `mcp_config.json`.

También se entrega `mcp_config.http.json`, con `transport: "http"` y `url: "http://127.0.0.1:8001/mcp"`, como comparación: apunta a un servidor que ya está levantado aparte (como en la sección 7 de este documento), así que no necesita `command`/`args`/`env`. La práctica y sus comprobaciones usan `mcp_config.json` (stdio).

### `MCPManager`: el cliente MCP de EBIS-CLI, ya resuelto (`ebis-cli-mcp/ebis_cli/mcp.py`)

```python
from mcp import Client, StdioServerParameters

def _create_client(server: dict) -> Client:
    if server["transport"] == "http":
        return Client(server["url"])
    return Client(StdioServerParameters(
        command=server["command"], args=server["args"],
        env=server["env"], cwd=server["cwd"],
    ))

class MCPManager:
    async def _start(self, server):
        client = _create_client(server)
        self.client = client
        await client.__aenter__()
        result = await client.list_tools()
        tools_for_model, model_tool_name_to_mcp_name = adapt_tools(result.tools)
        ...

    async def call_tool(self, model_tool_name, arguments):
        mcp_tool_name = self.model_tool_name_to_mcp_name.get(model_tool_name)
        result = await self.client.call_tool(mcp_tool_name, arguments=arguments)
        return format_tool_result(result)
```

Cada pieza de esta clase es una aplicación directa de lo visto en la sección 8: `_create_client` decide stdio vs. HTTP (sección "Levantando un cliente MCP"), `_start` abre la conexión y descubre tools (`__aenter__` + `list_tools`), y `call_tool` traduce el nombre público del modelo al nombre MCP real antes de invocar `client.call_tool(...)`.

### El ejercicio: `Recursos/ebis-cli-proyect/ebis_cli/mcp.py` — cómo pensarlo (sin dártelo resuelto)

El esqueleto del ejercicio es el mismo fichero, con las llamadas de la SDK sustituidas por marcadores `TODO_*`. Por ejemplo, en `_create_client`:

```python
def _create_client(server: dict) -> Client:
    if server["transport"] == "http":
        return Client(server["url"])
    # TODO 1: crea StdioServerParameters con command, args, env y cwd de server;
    # después pásalo a Client.
    return Client(TODO_STDIO_PARAMETERS)
```

El patrón general para esto —instanciar un objeto de parámetros con varios campos nombrados, y pasarlo a un constructor— es exactamente el que vimos en la sección 8 con `StdioServerParameters(command=..., args=..., env=...)`. Lo único que añade este ejercicio respecto al ejemplo genérico del material es un cuarto campo, `cwd` (la carpeta de trabajo del proceso hijo), que `mcp_config.py` ya resuelve como ruta absoluta antes de que `_create_client` lo reciba.

Para `_start` (TODOs 2-4) y `call_tool` (TODO 5), el patrón es, letra por letra, el del cliente `Client` de la sección 8: abrir con `__aenter__()`, pedir `list_tools()`, pasar `result.tools` a `adapt_tools(...)`, y en `call_tool` invocar `self.client.call_tool(nombre, arguments=...)`. Para practicar exactamente ese patrón sin copiar la solución del ejercicio, aquí tienes un ejemplo *ilustrativo* y distinto (una tool `cancelar_reunion`, que no existe en este proyecto), tomando como base el propio ejemplo `sumar` del material:

```python
# Ejemplo ilustrativo, no es parte de este ejercicio
async def ejemplo_de_conexion(server_params):
    client = Client(server_params)         # 1. crear el cliente (como TODO 1)
    await client.__aenter__()              # 2. abrir la conexión (como TODO 2)
    result = await client.list_tools()     # 3. pedir las tools (como TODO 3)
    tools, name_map = adapt_tools(result.tools)   # 4. adaptarlas (como TODO 4)

    # más tarde, para invocar una tool concreta (como TODO 5):
    resultado = await client.call_tool("cancelar_reunion", arguments={"meeting_id": 7})
    return resultado
```

El enunciado completo, con la ubicación exacta de cada `TODO` en `mcp.py`, `agent.py` y `server.py`, está en [`Enunciado_Practica_2_MCP.pdf`](Enunciado_Practica_2_MCP.pdf) y resumido en el [`AGENTS.md`](AGENTS.md) de esta carpeta.

### El ejercicio: `Recursos/ebis-calendar-api-mcp/server.py` — mismo patrón, lado servidor

```python
mcp = TODO_MCPSERVER   # TODO 1

@mcp.tool()
def list_workers() -> list[dict]:
    """Lista trabajadores y su horario laboral habitual."""
    return client.TODO_LIST_WORKERS()   # TODO 2
```

El TODO 1 es, literalmente, la instanciación `MCPServer("algún-nombre")` de la sección 5 (el nombre exacto no afecta al funcionamiento, solo aparece en los mensajes de estado). Los TODOs 2-4 piden delegar cada tool en la función equivalente de `client.py`, que ya está completo y expone exactamente las firmas que necesitan (`client.list_workers()`, `client.get_worker_meetings(worker_id=..., day=...)`, `client.schedule_meeting(worker_id=..., title=..., start=..., end=...)`). El patrón, aplicado a una tool que no es parte de este ejercicio:

```python
# Ejemplo ilustrativo, no es parte de este ejercicio
@mcp.tool()
def cancel_meeting(meeting_id: int) -> dict:
    """Cancela una reunión existente."""
    return client.cancel_meeting(meeting_id=meeting_id)
```

Es importante no duplicar en `server.py` ninguna validación que ya hace la API REST (horario laboral, solapamientos, trabajador existente...): el servidor MCP solo traduce la llamada y devuelve el resultado — ver la cita de la sección 5 ("MCP no reemplaza tu API"). Esas validaciones viven en `ebis-calendar-api/api.py` (ver sección siguiente) y ya llegan al agente como el resultado (o el error) de la tool, sin que el servidor MCP tenga que repetirlas.

### La API REST que hay detrás: `Recursos/ebis-calendar-api/`

Para entender qué es lo que el servidor MCP está adaptando, conviene leer la API REST en sí (completa, no se toca). Es una API FastAPI con datos en memoria:

- `GET /health`, `GET /workers`, `GET /workers/{id}`, `GET /workers/{id}/meetings?day=...`, `POST /meetings`.
- Tres trabajadores de ejemplo (`db.py`): Ana García, Luis Martín, Marta López, con horario laboral común de 09:00 a 17:00, lunes a viernes.
- `POST /meetings` valida, en este orden: que el trabajador exista, que las fechas no lleven zona horaria (deben ser hora local ISO, p. ej. `2026-10-01T14:00:00`), que `start` sea anterior a `end`, que ambas estén el mismo día, que el día sea laborable, que el horario esté entre las 09:00 y las 17:00, y que no haya solapamiento con otra reunión del mismo trabajador — devolviendo un `422` o un `409` con un mensaje de error si alguna falla.

Esas comprobaciones son justo el "error de calendario" que menciona la sección de "Problemas frecuentes" del enunciado: si `schedule_meeting` falla, el mensaje de error de la API (p. ej. *"El horario laboral es de 09:00 a 17:00"*) llega sin cambios hasta el agente, pasando por `client.py` → `server.py` → `MCPManager.call_tool` → `format_tool_result`.

### Una discrepancia a tener en cuenta: las tools locales

El enunciado de la práctica (p. 8) da por hecho que `/tools` mostrará "las cinco tools locales de la práctica 1" y sugiere probar `count_words`. Al leer `ebis_cli/tools.py` —tanto en `ebis-cli-mcp/` como en `Recursos/ebis-cli-proyect/`— el `TOOLS` declarado solo contiene **tres** funciones: `list_files`, `read_file`, `write_file`. No hay `count_words` ni `calculate_total` (las tools que sí se añadían en el ejercicio del tema 01). Es una discrepancia del material tal como se entrega, no un error de configuración: si sigues la comprobación guiada del enunciado al pie de la letra, ajusta la expectativa a tres tools locales, no cinco.

---

## 12. Glosario

- **MCP (Model Context Protocol)**: protocolo abierto, propuesto por Anthropic en noviembre de 2024, que estandariza cómo las aplicaciones de IA se conectan con fuentes de datos y herramientas externas.
- **Problema M×N**: el coste de integrar M agentes con N herramientas sin un estándar común, que crece como el producto de ambos números (cada par necesita su propia integración).
- **Host**: la aplicación principal con la que interactúa el usuario (Claude Code, Codex, Cursor, EBIS-CLI...), responsable de levantar un cliente MCP por cada servidor configurado.
- **Cliente MCP**: componente que vive dentro del host y mantiene una conexión 1:1 con un servidor MCP concreto.
- **Servidor MCP**: proceso que expone tools, resources y prompts usando el protocolo MCP, actuando como capa de adaptación hacia un sistema real (una API, una base de datos...).
- **JSON-RPC 2.0**: protocolo sobre el que se construye MCP; el cliente pide ejecutar un método por su nombre, con parámetros en JSON, y un `id` que empareja cada respuesta con su petición.
- **Handshake (`initialize`)**: negociación inicial entre cliente y servidor (versión del protocolo, capacidades) que existía en la versión 2025-11-25 del protocolo y se elimina en la versión stateless (2026-07-28).
- **Stateless (sin sesión)**: modelo en el que cada petición MCP es autocontenida (lleva su propia versión y datos del cliente en `_meta`), de forma que cualquier réplica del servidor puede atenderla sin depender de una sesión previa.
- **`server/discover`**: método que permite al cliente preguntar al servidor qué versión y capacidades tiene, sin abrir sesión (versión stateless).
- **`tools/list` / `tools/call`**: métodos MCP para descubrir las tools de un servidor y para invocar una de ellas.
- **Resource**: dato o información expuesta por un servidor MCP y accesible mediante una URI (p. ej. `config://app`), a diferencia de una tool (que es una acción).
- **Prompt (MCP)**: plantilla de texto reutilizable, con parámetros, expuesta por un servidor MCP y obtenible mediante `prompts/get`.
- **Transporte stdio**: comunicación local y privada entre dos procesos del mismo ordenador, sin red; el host arranca el servidor como proceso hijo.
- **Transporte HTTP**: comunicación por red con un servidor MCP que ya está en ejecución en otra parte (local o remota).
- **`FastMCP` / `MCPServer`**: la clase principal del SDK `mcp` de Python para construir un servidor; se llamaba `FastMCP` en la versión 2025-11-25 del SDK y se renombró a `MCPServer` en la versión 2.0 (2026-07-28).
- **`@mcp.tool()` / `@mcp.resource()` / `@mcp.prompt()`**: decoradores del SDK que registran, respectivamente, una tool, un resource o un prompt en el servidor, deduciendo su esquema de las anotaciones de tipo y el docstring de la función decorada.
- **`StdioServerParameters`**: estructura del SDK que guarda el comando, argumentos, variables de entorno y carpeta de trabajo necesarios para arrancar un servidor MCP por stdio.
- **`ClientSession` / `Client`**: clases del SDK para actuar como cliente MCP; `ClientSession` (versión 2025-11-25) requiere un handshake explícito (`initialize()`), mientras que `Client` (versión 2026-07-28) gestiona transporte y conexión internamente, sin handshake.
- **`mode="auto"`**: opción del cliente `Client` (SDK v2) que detecta automáticamente si un servidor usa el protocolo moderno (stateless) o uno anterior, y hace el fallback a `initialize()` si hace falta.
- **MCP Inspector**: cliente MCP oficial de laboratorio (`npx @modelcontextprotocol/inspector`), con interfaz web, para conectar, descubrir y probar servidores MCP sin escribir un agente ni un cliente propio.
- **`is_mcp_tool` / enrutamiento de tools**: la comprobación, dentro del bucle del agente, de si una llamada del modelo corresponde a una tool local (se ejecuta con el dispatcher local) o a una tool MCP (se envía al servidor conectado).
- **Normalización de nombres (`mcp_` + nombre)**: convención de esta práctica (`ebis_cli/mcp_tools.py`) para anteponer `mcp_` a cada tool descubierta por MCP antes de presentarla al modelo, evitando colisiones con las tools locales y permitiendo distinguir el origen de cada llamada.
- **Context7**: servidor MCP que inyecta documentación oficial y actualizada en el contexto de un agente, para reducir alucinaciones sobre APIs y librerías.
- **Playwright MCP**: servidor MCP que da capacidades de automatización de navegador (navegar, hacer clic, escribir) mediante snapshots de accesibilidad, sin modelos de visión.
- **SKILLS.md**: formato de documentación en Markdown, pensado para que un agente aprenda a usar un CLI ya instalado (capacidades, flujos, restricciones) sin necesidad de un servidor MCP dedicado.

---

## 13. Fuentes usadas en este documento

Todo el contenido anterior procede de:
- `Tema 6_Model Context Protocol (MCP).pdf` (76 páginas, teoría completa del tema).
- `Enunciado_Practica_2_MCP.pdf` (enunciado de la práctica, 9 páginas).
- `recursos_extra_mcp.md` (enlaces a documentación oficial de MCP, skills.sh y MCP Inspector).
- El código real, leído completo, de:
  - `ebis-cli-mcp/ebis_cli/{mcp.py, agent.py, mcp_tools.py, mcp_config.py, tools.py, app.py, context.py}` y su `README.md`.
  - `Recursos/ebis-cli-proyect/ebis_cli/{mcp.py, agent.py, mcp_tools.py, tools.py}` y su `README.md`.
  - `Recursos/ebis-calendar-api-mcp/ebis_calendar_api_mcp/{server.py, client.py, config.py}` y su `README.md`.
  - `Recursos/ebis-calendar-api/{api.py, db.py, main.py}` y su `README.md`.
  - Los archivos de configuración `mcp_config.json` y `mcp_config.http.json` de ambos proyectos de EBIS-CLI.

No se ha añadido ninguna afirmación técnica sobre el protocolo MCP, la arquitectura cliente/servidor o el código de este repositorio que no esté respaldada por alguna de estas fuentes. Los únicos añadidos que no vienen literalmente del material son los ejemplos marcados explícitamente como ilustrativos: la función `ejemplo_de_conexion` y la tool `cancelar_reunion`/`cancel_meeting` en la sección 11, usados solo para practicar el patrón de los TODOs sin desvelar la solución del ejercicio. Las dos discrepancias señaladas (tools locales del enunciado vs. código entregado, y la frase sobre `FastMCP`/SDK v1 en el README de `ebis-cli-mcp/`) se han verificado leyendo directamente el código fuente correspondiente, citado en cada caso.
