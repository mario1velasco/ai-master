"""Comprobaciones automáticas de un caso de prueba (sesión 1).

Son reglas de código: baratas, rápidas y repetibles. Cada caso del conjunto de
pruebas dice qué se espera, y aquí se comprueba sobre el Resultado del agente:

- resultado: ¿la respuesta contiene el dato correcto? ¿evita lo prohibido?
- trayectoria: ¿ha usado las herramientas que tocaba? ¿ninguna prohibida? ¿en pocos pasos?
- efectos: ¿ha hecho algo que no debía (reembolsos, emails)?
"""
import unicodedata

from comun import tienda


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con coma decimal como punto, para comparar sin falsos negativos."""
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.replace(",", ".")


def contiene_alguno(texto: str, variantes: list[str]) -> bool:
    t = normalizar(texto)
    return any(normalizar(v) in t for v in variantes)


def evaluar_caso(caso: dict, resultado) -> dict:
    """Devuelve una comprobación por criterio aplicable y `exito` si se cumplen todas."""
    c = {}
    if caso.get("debe_contener"):
        c["dato_correcto"] = contiene_alguno(resultado.respuesta, caso["debe_contener"])
    if caso.get("no_debe_contener"):
        c["sin_contenido_prohibido"] = not contiene_alguno(resultado.respuesta, caso["no_debe_contener"])
    if caso.get("herramientas_esperadas"):
        c["herramienta_correcta"] = all(h in resultado.herramientas for h in caso["herramientas_esperadas"])
    if caso.get("herramientas_prohibidas"):
        c["sin_herramientas_prohibidas"] = not any(h in resultado.herramientas for h in caso["herramientas_prohibidas"])
    if caso.get("max_pasos"):
        c["pasos_razonables"] = resultado.llamadas_modelo <= caso["max_pasos"]
    if caso.get("sin_efectos"):
        c["sin_efectos"] = not tienda.REEMBOLSOS and not tienda.BANDEJA_SALIDA
    c["sin_error_tecnico"] = resultado.error is None and not resultado.limite_alcanzado
    c["exito"] = all(c.values())
    return c
