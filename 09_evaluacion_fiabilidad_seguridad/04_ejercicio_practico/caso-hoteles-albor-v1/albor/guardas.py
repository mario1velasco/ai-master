"""Guardarraíles del asistente de Hoteles Albor. AQUÍ TRABAJAS TÚ (parte 3 del caso).

El agente llama a estos cuatro métodos en este orden. Ahora mismo no hacen nada:
dejan pasar todo. Complétalos con las reglas que decidas.

`contexto` es la sesión del huésped que viene del login de la web, p. ej.
{"email": "lucia.martin@correo.com"}. Puede estar vacío si el huésped no se ha
identificado. El modelo no puede cambiarlo.
"""
from datetime import date

from albor import hotel


def reembolso_segun_politica(reserva: dict) -> float:
    """Lo que dice hotel.POLITICA, en código. Sin hora de entrada: menos de 2 días = dentro de las 48 h."""
    if reserva["tarifa"] == "no reembolsable":
        return 0.0
    dias = (date.fromisoformat(reserva["entrada"]) - hotel.HOY).days
    return reserva["total"] if dias >= 2 else round(reserva["total"] * 0.5, 2)


class Guardas:
    def revisar_entrada(self, texto: str, contexto: dict) -> tuple[str, str | None]:
        """Antes de que el mensaje llegue al modelo.
        Devuelve (texto, None) para seguir, con el texto limpio si hace falta,
        o (texto, "respuesta al huésped") para bloquear el mensaje."""
        return texto, None

    def revisar_herramienta(self, nombre: str, argumentos: dict, contexto: dict):
        """Antes de ejecutar cada herramienta que pide el modelo. Devuelve:
        - None: se ejecuta.
        - "motivo": se bloquea y el modelo recibe el motivo.
        - {"aprobacion": "motivo"}: no se ejecuta; queda pendiente de que la apruebe una persona."""
        if contexto.get("rol") == "recepcion":
            return None  # recepción ve todas las reservas y su perfil no tiene acciones irreversibles
        email = (contexto.get("email") or "").lower()
        id_reserva = str(argumentos.get("id_reserva", "")).upper().strip()
        reserva = hotel.RESERVAS.get(id_reserva)

        # 3.1 Mínimo privilegio · alcance: solo sobre los datos del huésped identificado
        if nombre == "buscar_huesped" and (not email or str(argumentos.get("email", "")).lower().strip() != email):
            return "solo puedes consultar los datos del huésped identificado"
        if nombre in ("consultar_reserva", "cancelar_reserva") and reserva and reserva["huesped"] != email:
            return "la reserva no pertenece al huésped identificado"

        # 3.2 Validación de las acciones irreversibles: importe según la política y destinatario
        if nombre == "cancelar_reserva" and reserva:
            try:
                importe = float(argumentos.get("importe_reembolso") or 0)
            except (TypeError, ValueError):
                return "el importe del reembolso tiene que ser un número"
            correcto = reembolso_segun_politica(reserva)
            if abs(importe - correcto) > 0.01:
                return f"según la política, el reembolso de {id_reserva} es de {correcto:.2f} €"
        if nombre == "enviar_email" and str(argumentos.get("destinatario", "")).lower().strip() != email:
            return "solo se pueden enviar emails al huésped identificado"
        return None

    def revisar_resultado(self, nombre: str, resultado, contexto: dict):
        """Después de ejecutar una herramienta y antes de que el modelo vea el resultado.
        Devuelve el resultado, tal cual o modificado."""
        return resultado

    def revisar_salida(self, texto: str, contexto: dict, observaciones: str) -> tuple[str, str | None]:
        """Antes de enviar la respuesta al huésped. `observaciones` son los resultados de las herramientas.
        Devuelve (texto, None) para enviarla, o (texto_alternativo, "motivo") si la sustituyes."""
        return texto, None
