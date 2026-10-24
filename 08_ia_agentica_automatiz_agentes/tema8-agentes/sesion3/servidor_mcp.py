"""Sesión 3 · Servidor MCP de Lumen Shop.

Expone las herramientas de lectura de la tienda mediante Model Context Protocol
(visto en el Tema 6). Cualquier cliente MCP puede usarlas: nuestro agente,
Claude Desktop, un IDE...

Uso: lo arranca automáticamente sesion3/agente_mcp.py. Para probarlo solo:
     python -m sesion3.servidor_mcp
"""
from mcp.server.fastmcp import FastMCP

from comun import tienda

servidor = FastMCP("lumen-shop")


@servidor.tool()
def consultar_stock(producto: str) -> dict:
    """[Lectura] Devuelve precio y unidades disponibles de un producto del catálogo de Lumen Shop."""
    return tienda.consultar_stock(producto)


@servidor.tool()
def consultar_pedido(id_pedido: str) -> dict:
    """[Lectura] Devuelve estado, productos, importe y seguimiento de un pedido (formato ORD-12345)."""
    return tienda.obtener_pedido(id_pedido)


if __name__ == "__main__":
    servidor.run(transport="stdio")
