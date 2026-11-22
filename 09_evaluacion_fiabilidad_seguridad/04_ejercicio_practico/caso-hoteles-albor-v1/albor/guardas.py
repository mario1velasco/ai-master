"""Guardarraíles del asistente de Hoteles Albor. AQUÍ TRABAJAS TÚ (parte 3 del caso).

El agente llama a estos cuatro métodos en este orden. Ahora mismo no hacen nada:
dejan pasar todo. Complétalos con las reglas que decidas.

`contexto` es la sesión del huésped que viene del login de la web, p. ej.
{"email": "lucia.martin@correo.com"}. Puede estar vacío si el huésped no se ha
identificado. El modelo no puede cambiarlo.
"""
from albor import hotel


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

        # 3.1 Mínimo privilegio · alcance: solo sobre los datos del huésped identificado
        if nombre == "buscar_huesped" and (not email or str(argumentos.get("email", "")).lower().strip() != email):
            return "solo puedes consultar los datos del huésped identificado"
        if nombre in ("consultar_reserva", "cancelar_reserva"):
            reserva = hotel.RESERVAS.get(str(argumentos.get("id_reserva", "")).upper().strip())
            if reserva and reserva["huesped"] != email:
                return "la reserva no pertenece al huésped identificado"
        return None

    def revisar_resultado(self, nombre: str, resultado, contexto: dict):
        """Después de ejecutar una herramienta y antes de que el modelo vea el resultado.
        Devuelve el resultado, tal cual o modificado."""
        return resultado

    def revisar_salida(self, texto: str, contexto: dict, observaciones: str) -> tuple[str, str | None]:
        """Antes de enviar la respuesta al huésped. `observaciones` son los resultados de las herramientas.
        Devuelve (texto, None) para enviarla, o (texto_alternativo, "motivo") si la sustituyes."""
        return texto, None
