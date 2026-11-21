"""Herramientas del asistente de Hoteles Albor: lo que ve el modelo (esquema) y lo que se ejecuta (función).

Así las dejó el proveedor que hizo el piloto. Nadie ha revisado su diseño ni sus riesgos.
"""
from albor import hotel


def _esquema(nombre, descripcion, propiedades):
    return {"type": "function", "function": {"name": nombre, "description": descripcion, "parameters": {
        "type": "object", "properties": propiedades, "required": list(propiedades)}}}


CATALOGO = {
    "consultar_disponibilidad": {
        "funcion": hotel.consultar_disponibilidad,
        "esquema": _esquema("consultar_disponibilidad", "Habitaciones libres y precios de un hotel.",
                            {"hotel": {"type": "string"}, "fecha_entrada": {"type": "string"},
                             "noches": {"type": "integer"}})},
    "consultar_reserva": {
        "funcion": hotel.consultar_reserva,
        "esquema": _esquema("consultar_reserva", "Datos de una reserva.", {"id_reserva": {"type": "string"}})},
    "buscar_huesped": {
        "funcion": hotel.buscar_huesped,
        "esquema": _esquema("buscar_huesped", "Datos de un huésped.", {"email": {"type": "string"}})},
    "listar_reservas": {
        "funcion": hotel.listar_reservas,
        "esquema": _esquema("listar_reservas", "Lista las reservas.", {"hotel": {"type": "string"}})},
    "leer_resenas": {
        "funcion": hotel.leer_resenas,
        "esquema": _esquema("leer_resenas", "Opiniones de los huéspedes sobre un hotel.",
                            {"hotel": {"type": "string"}})},
    "consultar_politica": {
        "funcion": hotel.consultar_politica,
        "esquema": _esquema("consultar_politica", "Política de cancelación, reembolsos y mascotas.", {})},
    "cancelar_reserva": {
        "funcion": hotel.cancelar_reserva,
        "esquema": _esquema("cancelar_reserva", "Cancela una reserva y reembolsa el importe indicado.",
                            {"id_reserva": {"type": "string"}, "importe_reembolso": {"type": "number"},
                             "motivo": {"type": "string"}})},
    "enviar_email": {
        "funcion": hotel.enviar_email,
        "esquema": _esquema("enviar_email", "Envía un email.",
                            {"destinatario": {"type": "string"}, "asunto": {"type": "string"},
                             "cuerpo": {"type": "string"}})},
}

TODAS = list(CATALOGO)
