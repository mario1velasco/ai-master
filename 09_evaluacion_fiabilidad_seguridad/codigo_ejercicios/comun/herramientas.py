"""Herramientas de Lumen Shop: lo que ve el modelo (esquema), lo que se ejecuta (función) y su riesgo.

El riesgo sigue la clasificación de la sesión 3 del Tema 8:
- lectura: sin efectos
- irreversible: tiene efectos que no se pueden deshacer (dinero, emails)
"""
from comun import tienda


def _esquema(nombre, descripcion, propiedades):
    return {"type": "function", "function": {"name": nombre, "description": descripcion, "parameters": {
        "type": "object", "properties": propiedades, "required": list(propiedades)}}}


CATALOGO = {
    "consultar_stock": {
        "funcion": tienda.consultar_stock, "riesgo": "lectura",
        "esquema": _esquema("consultar_stock", "[Lectura] Precio en euros y unidades disponibles de un producto. "
                            "Acepta nombres parciales, p. ej. 'serum' o 'solar'.",
                            {"producto": {"type": "string"}})},
    "buscar_cliente": {
        "funcion": tienda.buscar_cliente, "riesgo": "lectura",
        "esquema": _esquema("buscar_cliente", "[Lectura] Datos de un cliente por su email: nombre, contacto y "
                            "pedidos (del más antiguo al más reciente).",
                            {"email": {"type": "string", "description": "Email exacto, copiado tal cual"}})},
    "consultar_pedido": {
        "funcion": tienda.obtener_pedido, "riesgo": "lectura",
        "esquema": _esquema("consultar_pedido", "[Lectura] Estado, productos, importe en euros y número de "
                            "seguimiento de un pedido.",
                            {"id_pedido": {"type": "string", "description": "Formato ORD-12345"}})},
    "consultar_transportista": {
        "funcion": tienda.consultar_transportista, "riesgo": "lectura",
        "esquema": _esquema("consultar_transportista", "[Lectura] Ubicación de un envío por su número de "
                            "seguimiento.", {"numero_seguimiento": {"type": "string", "description": "Formato TRK-12345"}})},
    "leer_resenas": {
        "funcion": tienda.leer_resenas, "riesgo": "lectura",
        "esquema": _esquema("leer_resenas", "[Lectura] Reseñas que otros clientes han escrito sobre un producto.",
                            {"producto": {"type": "string"}})},
    "consultar_politica": {
        "funcion": tienda.consultar_politica, "riesgo": "lectura",
        "esquema": _esquema("consultar_politica", "[Lectura] Política de devoluciones, reembolsos y envíos.", {})},
    "emitir_reembolso": {
        "funcion": tienda.emitir_reembolso, "riesgo": "irreversible",
        "esquema": _esquema("emitir_reembolso", "[Escritura irreversible] Emite un reembolso en euros a un pedido.",
                            {"id_pedido": {"type": "string"}, "importe": {"type": "number"},
                             "motivo": {"type": "string"}})},
    "enviar_email": {
        "funcion": tienda.enviar_email, "riesgo": "irreversible",
        "esquema": _esquema("enviar_email", "[Escritura irreversible] Envía un email.",
                            {"destinatario": {"type": "string"}, "asunto": {"type": "string"},
                             "cuerpo": {"type": "string"}})},
}

LECTURA = [n for n, h in CATALOGO.items() if h["riesgo"] == "lectura"]
TODAS = list(CATALOGO)
