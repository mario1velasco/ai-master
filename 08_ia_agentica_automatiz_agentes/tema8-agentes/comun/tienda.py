"""Datos simulados de Lumen Shop, la tienda online que usamos como caso conductor.

En un sistema real estas funciones llamarían a la API de Shopify, al ERP o al
CRM. Aquí devuelven datos fijos para que las demos sean reproducibles.
"""

PRODUCTOS = {
    "serum vitamina c": {"sku": "LS-001", "precio": 24.90, "stock": 132},
    "crema hidratante": {"sku": "LS-002", "precio": 19.50, "stock": 0},
    "protector solar spf50": {"sku": "LS-003", "precio": 15.90, "stock": 8},
    "contorno de ojos": {"sku": "LS-004", "precio": 21.00, "stock": 47},
}

CLIENTES = {
    "marta.lopez@email.com": {"nombre": "Marta López", "pedidos": ["ORD-10231", "ORD-10544"], "cliente_desde": "2024-03"},
    "jorge.ruiz@email.com": {"nombre": "Jorge Ruiz", "pedidos": ["ORD-10598"], "cliente_desde": "2025-11"},
}

PEDIDOS = {
    "ORD-10231": {"estado": "entregado", "productos": ["serum vitamina c"], "total": 24.90, "seguimiento": "TRK-55120"},
    "ORD-10544": {"estado": "en tránsito", "productos": ["crema hidratante", "contorno de ojos"], "total": 40.50, "seguimiento": "TRK-58873"},
    "ORD-10598": {"estado": "pendiente de envío", "productos": ["protector solar spf50"], "total": 15.90, "seguimiento": None},
}


def consultar_stock(producto: str) -> dict:
    datos = PRODUCTOS.get(producto.lower().strip())
    if datos is None:
        return {"error": f"Producto '{producto}' no encontrado.", "productos_disponibles": list(PRODUCTOS)}
    return {"producto": producto, **datos}


def buscar_cliente(email: str) -> dict:
    datos = CLIENTES.get(email.lower().strip())
    if datos is None:
        return {"error": f"No existe ningún cliente con el email '{email}'."}
    return {"email": email, **datos}


def obtener_pedido(id_pedido: str) -> dict:
    datos = PEDIDOS.get(id_pedido.upper().strip())
    if datos is None:
        return {"error": f"Pedido '{id_pedido}' no encontrado. El formato esperado es ORD-12345."}
    return {"id_pedido": id_pedido.upper(), **datos}


def consultar_transportista(numero_seguimiento: str) -> dict:
    # Simula una API externa caída. Se usa en clase para provocar un bucle.
    raise ConnectionError("Timeout: el servicio del transportista no responde.")
