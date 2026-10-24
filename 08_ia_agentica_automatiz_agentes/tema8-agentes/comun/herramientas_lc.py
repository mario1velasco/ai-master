"""Herramientas de Lumen Shop para LangGraph (sesiones 3 a 6).

Cada herramienta lleva el nivel de riesgo en su docstring para que se vea en
clase: lectura, escritura reversible o escritura irreversible.
"""
from langchain_core.tools import tool

from comun import tienda

REEMBOLSOS_EMITIDOS: list[dict] = []  # simula el sistema de pagos


@tool
def consultar_stock(producto: str) -> dict:
    """[Lectura] Devuelve precio y unidades disponibles de un producto, p. ej. 'serum vitamina c'."""
    return tienda.consultar_stock(producto)


@tool
def buscar_cliente(email: str) -> dict:
    """[Lectura] Busca un cliente por email. Devuelve su nombre y sus pedidos, del más antiguo al más reciente."""
    return tienda.buscar_cliente(email)


@tool
def consultar_pedido(id_pedido: str) -> dict:
    """[Lectura] Devuelve estado, productos, importe y número de seguimiento de un pedido (formato ORD-12345)."""
    return tienda.obtener_pedido(id_pedido)


@tool
def consultar_transportista(numero_seguimiento: str) -> dict:
    """[Lectura] Consulta la ubicación de un envío por su número de seguimiento (formato TRK-12345)."""
    try:
        return tienda.consultar_transportista(numero_seguimiento)
    except ConnectionError as e:
        return {"error": f"{e} Informa al cliente con el estado del pedido en su lugar."}


@tool
def emitir_reembolso(id_pedido: str, importe: float, motivo: str) -> dict:
    """[Escritura irreversible] Emite un reembolso al cliente. Úsala solo si el cliente tiene derecho a él."""
    reembolso = {"id_pedido": id_pedido, "importe": importe, "motivo": motivo}
    REEMBOLSOS_EMITIDOS.append(reembolso)
    return {"estado": "reembolso emitido", **reembolso}


LECTURA = [consultar_stock, buscar_cliente, consultar_pedido, consultar_transportista]
TODAS = LECTURA + [emitir_reembolso]
