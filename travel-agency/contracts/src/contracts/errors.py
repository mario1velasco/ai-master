"""Errores con código que cruzan entre paquetes: quien llama sabe qué pieza falló y por qué, sin leer la traza."""


class ComponentError(Exception):
    """Un error que dice qué pieza ha fallado. Como `ErrorComponente` de
    `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_3/asistente/ollama.py`, con el código en inglés.

    Vive en `contracts` y no en `text2sql` porque lo lanzan varios paquetes (text2sql, el agente y, más adelante, rag)
    y la API lo convertirá en su respuesta de error.
    """

    def __init__(self, code: str, component: str, message: str) -> None:
        super().__init__(message)
        self.code, self.component, self.message = code, component, message

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "component": self.component, "message": self.message}
