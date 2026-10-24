# Sesión 3 · Herramientas desde la perspectiva del agente

## Demos

| Archivo | Qué muestra |
|---|---|
| `agente_langgraph.py` | El agente migrado a LangGraph, con herramientas clasificadas por riesgo y pausa para aprobación humana antes de un reembolso |
| `../comun/apis_externas.py` | Una herramienta sobre una API pública real (tipos de cambio), con timeout, rate limit y errores útiles para el agente |
| `../comun/grafo.py` | El constructor del grafo que usaremos hasta la sesión 6 |
| `servidor_mcp.py` + `agente_mcp.py` | Lumen Shop expuesto por MCP y un agente que combina esas herramientas con otras locales |
| `dibujar_grafo.py` | Imprime el grafo en formato Mermaid (pégalo en mermaid.live) |
| `actividad_herramienta.py` | Una herramienta mal diseñada para la actividad de clase |

```bash
python -m sesion3.agente_langgraph
python -m sesion3.agente_mcp "¿Cuánto cuesta el contorno de ojos en dólares y cuántas unidades quedan?"
python -m sesion3.dibujar_grafo
```

En la conversación con `agente_langgraph`, prueba:
- «¿Cuánto cuesta el sérum de vitamina C en dólares?»
- «Soy jorge.ruiz@email.com, el pedido ORD-10598 llegó roto y quiero que me devolváis el dinero» → apruébalo y recházalo.

## Aplicación práctica: el mismo servidor en otros clientes

El servidor MCP de Lumen Shop no es solo para nuestro agente. Por ejemplo, para
usarlo desde Claude Desktop, añade esto a su archivo de configuración
(`claude_desktop_config.json`), ajustando las rutas a tu equipo:

```json
{
  "mcpServers": {
    "lumen-shop": {
      "command": "/ruta/a/tema8-agentes/.venv/bin/python",
      "args": ["-m", "sesion3.servidor_mcp"],
      "env": { "PYTHONPATH": "/ruta/a/tema8-agentes" }
    }
  }
}
```

En Windows, `command` apunta a `.venv\Scripts\python.exe`. Los IDE con soporte de MCP
usan una configuración equivalente.

## Deberes

**Nivel base · Rediseña dos herramientas.**
1. `buscar_cliente` solo devuelve los números de pedido, así que el agente necesita
   una llamada más por pedido. Haz que devuelva un resumen de cada pedido.
2. `consultar_stock` falla si el nombre no coincide exactamente («serum» no encuentra
   «serum vitamina c»). Haz que acepte nombres parciales y, si hay varias
   coincidencias, devuelva las opciones.
Compara cuántas llamadas hace el agente antes y después.

**Reto · Amplía el servidor MCP.** Añade al servidor una herramienta nueva y un
recurso MCP con la política de devoluciones. Conecta el agente a tu servidor.
