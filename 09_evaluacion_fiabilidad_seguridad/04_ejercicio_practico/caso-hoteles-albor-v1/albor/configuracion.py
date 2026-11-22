"""Cómo se crea el agente para cada conversación. AQUÍ TRABAJAS TÚ (parte 3 del caso).

Tanto el chat de prueba (`python -m albor.chat`) como la medición
(`python -m pruebas.medir`) crean el agente con esta función, así que lo que
cambies aquí se aplica a los dos.

Mínimo privilegio en dos capas (Tema 9, sesión 2):
1. PERFIL (aquí): qué herramientas existen en cada canal. Si no está en el perfil,
   el modelo ni sabe que existe.
2. ALCANCE (albor/guardas.py): dentro del perfil, solo sobre los datos del huésped identificado.
"""
from albor.agente import Agente
from albor.guardas import Guardas
from albor.herramientas import IRREVERSIBLE, LECTURA

PERFILES = {
    "publico": ["consultar_disponibilidad", "consultar_politica", "leer_resenas"],  # web, sin identificar
    "huesped": [h for h in LECTURA if h != "listar_reservas"] + IRREVERSIBLE,     # huésped identificado
    "recepcion": LECTURA,                                                         # equipo de recepción
}


def perfil(contexto: dict | None) -> str:
    contexto = contexto or {}
    if contexto.get("rol") == "recepcion":
        return "recepcion"
    return "huesped" if contexto.get("email") else "publico"


def crear_agente(contexto: dict | None = None, cliente=None) -> Agente:
    return Agente(cliente=cliente, herramientas=PERFILES[perfil(contexto)], contexto=contexto, guardas=Guardas())
