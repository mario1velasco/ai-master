"""Solución · Deber base de la sesión 3: rediseñar dos herramientas.

1. buscar_cliente devolvía solo los IDs de los pedidos, lo que obligaba al
   agente a hacer una llamada más por pedido. Ahora devuelve un resumen de cada
   pedido: menos pasos, menos tokens y menos ocasiones de equivocarse.
2. consultar_stock fallaba si el nombre no coincidía exactamente. Ahora busca
   por coincidencia parcial y, si hay varias, devuelve las opciones.
"""
from langchain_core.tools import tool

from comun import tienda


@tool
def buscar_cliente_con_pedidos(email: str) -> dict:
    """[Lectura] Busca un cliente por email y devuelve su nombre y un resumen de cada pedido
    (estado, productos e importe), del más antiguo al más reciente."""
    ficha = tienda.buscar_cliente(email)
    if "error" in ficha:
        return ficha
    return {"nombre": ficha["nombre"], "pedidos": [tienda.obtener_pedido(p) for p in ficha["pedidos"]]}


@tool
def consultar_stock_flexible(producto: str) -> dict:
    """[Lectura] Precio y stock de un producto. Acepta nombres parciales, p. ej. 'serum' o 'solar'."""
    busqueda = producto.lower().strip()
    coincidencias = [n for n in tienda.PRODUCTOS if busqueda in n]
    if len(coincidencias) == 1:
        return tienda.consultar_stock(coincidencias[0])
    if not coincidencias:
        return {"error": f"Ningún producto contiene '{producto}'.", "productos_disponibles": list(tienda.PRODUCTOS)}
    return {"aviso": "Hay varios productos que coinciden; pregunta al cliente cuál quiere.", "opciones": coincidencias}
