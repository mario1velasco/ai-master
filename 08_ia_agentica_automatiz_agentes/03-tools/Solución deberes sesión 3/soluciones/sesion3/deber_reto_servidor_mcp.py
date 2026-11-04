"""Solución · Reto de la sesión 3: exponer herramientas propias por MCP.

Añadimos al servidor una herramienta nueva (la búsqueda flexible del deber base)
y un recurso MCP con la política de devoluciones, que el cliente puede leer
como contexto. Para usarlo, cambia en sesion3/agente_mcp.py el módulo del
servidor por "soluciones.sesion3.deber_reto_servidor_mcp".
"""
from mcp.server.fastmcp import FastMCP

from comun import tienda

servidor = FastMCP("lumen-shop-ampliado")


@servidor.tool()
def consultar_pedido(id_pedido: str) -> dict:
    """[Lectura] Devuelve estado, productos, importe y seguimiento de un pedido (formato ORD-12345)."""
    return tienda.obtener_pedido(id_pedido)


@servidor.tool()
def consultar_stock_flexible(producto: str) -> dict:
    """[Lectura] Precio y stock de un producto. Acepta nombres parciales, p. ej. 'serum' o 'solar'."""
    coincidencias = [n for n in tienda.PRODUCTOS if producto.lower().strip() in n]
    if len(coincidencias) == 1:
        return tienda.consultar_stock(coincidencias[0])
    return {"opciones": coincidencias or list(tienda.PRODUCTOS)}


@servidor.resource("lumen://politica-devoluciones")
def politica_devoluciones() -> str:
    """Política de devoluciones de Lumen Shop."""
    return ("Devoluciones gratuitas en 30 días con el producto sin abrir. Productos dañados en el envío: "
            "reembolso completo con foto del daño. Reembolsos de más de 50 € requieren aprobación de un supervisor.")


if __name__ == "__main__":
    servidor.run(transport="stdio")
