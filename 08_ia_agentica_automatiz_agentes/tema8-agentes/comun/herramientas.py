"""Herramientas de Lumen Shop en formato OpenAI (sesiones 1 y 2).

Incluye ya `consultar_pedido`, que es el deber base de la sesión 1.
"""
from comun import tienda


def _herramienta(nombre, descripcion, propiedades, requeridos):
    return {"type": "function", "function": {"name": nombre, "description": descripcion, "parameters": {
        "type": "object", "properties": propiedades, "required": requeridos}}}


HERRAMIENTAS = [
    _herramienta("consultar_stock", "Devuelve precio y unidades disponibles de un producto del catálogo.",
                 {"producto": {"type": "string", "description": "Nombre del producto, p. ej. 'serum vitamina c'"}},
                 ["producto"]),
    _herramienta("buscar_cliente", "Busca un cliente por su email y devuelve su nombre y la lista de sus pedidos, "
                 "del más antiguo al más reciente.", {"email": {"type": "string"}}, ["email"]),
    _herramienta("consultar_pedido", "Devuelve estado, productos, importe y número de seguimiento de un pedido.",
                 {"id_pedido": {"type": "string", "description": "Formato ORD-12345"}}, ["id_pedido"]),
    _herramienta("consultar_transportista", "Consulta la ubicación de un envío a partir de su número de seguimiento.",
                 {"numero_seguimiento": {"type": "string"}}, ["numero_seguimiento"]),
]

FUNCIONES = {
    "consultar_stock": tienda.consultar_stock,
    "buscar_cliente": tienda.buscar_cliente,
    "consultar_pedido": tienda.obtener_pedido,
    "consultar_transportista": tienda.consultar_transportista,
}
