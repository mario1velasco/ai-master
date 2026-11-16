import json
import re
from datetime import datetime


def extraer_json(texto: str):
    """Extrae el primer objeto JSON de un texto (los modelos a veces añaden texto alrededor)."""
    texto = re.sub(r"```(?:json)?", "", texto or "")
    inicio = texto.find("{")
    if inicio == -1:
        raise ValueError(f"No hay JSON en la respuesta: {texto[:200]}")
    profundidad = 0
    for i, caracter in enumerate(texto[inicio:], start=inicio):
        profundidad += {"{": 1, "}": -1}.get(caracter, 0)
        if profundidad == 0:
            return json.loads(texto[inicio:i + 1])
    raise ValueError("JSON incompleto en la respuesta del modelo")


def tokens_de(*mensajes) -> int:
    """Suma los tokens de mensajes de LangChain (los que traigan metadatos de uso)."""
    return sum((getattr(m, "usage_metadata", None) or {}).get("total_tokens", 0) for m in mensajes)


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def euros(importe: float) -> str:
    return f"{importe:,.0f} €".replace(",", ".")
