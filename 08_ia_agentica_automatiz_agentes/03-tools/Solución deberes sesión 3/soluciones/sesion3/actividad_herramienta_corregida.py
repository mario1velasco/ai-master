"""Solución de la actividad de la sesión 3: la misma consulta, bien diseñada.

Cambios: nombre que dice lo que hace, descripción con cuándo usarla, un
parámetro con formato explícito, salida acotada a lo que se pide y errores que
indican cómo corregir la llamada.
"""
from langchain_core.tools import tool

from comun import tienda


@tool
def consultar_precio_y_stock(producto: str) -> dict:
    """[Lectura] Devuelve el precio en euros y las unidades disponibles de UN producto del catálogo.

    Úsala cuando el cliente pregunte por precio o disponibilidad. `producto` es el nombre
    del producto en minúsculas, p. ej. 'serum vitamina c'. No sirve para pedidos ni clientes.
    """
    resultado = tienda.consultar_stock(producto)
    if "error" in resultado:
        resultado["como_corregir"] = "Repite la llamada con uno de los nombres de 'productos_disponibles'."
    return resultado
