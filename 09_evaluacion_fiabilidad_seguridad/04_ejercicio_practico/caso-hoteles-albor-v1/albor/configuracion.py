"""Cómo se crea el agente para cada conversación. AQUÍ TRABAJAS TÚ (parte 3 del caso).

Tanto el chat de prueba (`python -m albor.chat`) como la medición
(`python -m pruebas.medir`) crean el agente con esta función, así que lo que
cambies aquí se aplica a los dos.

Configuración actual: la del piloto. Todas las herramientas y sin guardarraíles.
"""
from albor.agente import Agente
from albor.herramientas import TODAS


def crear_agente(contexto: dict | None = None, cliente=None) -> Agente:
    return Agente(cliente=cliente, herramientas=TODAS, contexto=contexto, guardas=None)
