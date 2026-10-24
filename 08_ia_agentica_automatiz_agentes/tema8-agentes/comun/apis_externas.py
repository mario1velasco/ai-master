"""Herramientas sobre APIs externas reales (sesión 3).

Usamos Frankfurter, una API pública de tipos de cambio del BCE que no requiere
clave. El patrón es el mismo para cualquier API REST: timeout, reintento ante
límite de peticiones y errores que el agente pueda entender.
"""
import time

import httpx
from langchain_core.tools import tool

URL_DIVISAS = "https://api.frankfurter.app/latest"


@tool
def convertir_precio(importe_eur: float, moneda: str) -> dict:
    """Convierte un importe en euros a otra moneda con el tipo de cambio oficial del día.

    Úsala cuando un cliente pregunte cuánto cuesta un producto en su moneda.
    `moneda` es el código ISO de 3 letras: USD, GBP, MXN, CHF...
    """
    moneda = moneda.upper().strip()
    for intento in range(2):
        try:
            respuesta = httpx.get(URL_DIVISAS, params={"from": "EUR", "to": moneda}, timeout=5)
        except httpx.HTTPError:
            return {"error": "El servicio de divisas no responde. Da el precio en euros e indícalo al cliente."}
        if respuesta.status_code == 429 and intento == 0:  # rate limit: esperamos y reintentamos una vez
            time.sleep(int(respuesta.headers.get("Retry-After", 2)))
            continue
        if respuesta.status_code == 404:
            return {"error": f"Moneda '{moneda}' no soportada. Usa un código ISO como USD o MXN."}
        if respuesta.status_code != 200:
            return {"error": f"El servicio de divisas ha fallado (HTTP {respuesta.status_code})."}
        tasa = respuesta.json()["rates"][moneda]
        return {"importe_eur": importe_eur, "moneda": moneda, "tipo_cambio": tasa,
                "importe_convertido": round(importe_eur * tasa, 2), "fecha": respuesta.json()["date"]}
    return {"error": "Límite de peticiones del servicio de divisas superado. Inténtalo más tarde."}
