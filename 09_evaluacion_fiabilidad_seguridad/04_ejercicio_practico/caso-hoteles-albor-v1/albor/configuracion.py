"""Cómo se crea el agente para cada conversación. AQUÍ TRABAJAS TÚ (parte 3 del caso).

Tanto el chat de prueba (`python -m albor.chat`) como la medición
(`python -m pruebas.medir`) crean el agente con esta función, así que lo que
cambies aquí se aplica a los dos.

Mínimo privilegio en dos capas (Tema 9, sesión 2):
1. PERFIL (aquí): qué herramientas existen en cada canal. Si no está en el perfil,
   el modelo ni sabe que existe.
2. ALCANCE (albor/guardas.py): dentro del perfil, solo sobre los datos del huésped identificado.
"""
from albor.agente import INSTRUCCIONES, Agente
from albor.guardas import Guardas
from albor.herramientas import IRREVERSIBLE, LECTURA

PERFILES = {
    "publico": ["consultar_disponibilidad", "consultar_politica", "leer_resenas"],  # web, sin identificar
    "huesped": [h for h in LECTURA if h != "listar_reservas"] + IRREVERSIBLE,     # huésped identificado
    "recepcion": LECTURA,                                                         # equipo de recepción
}

# FIX01 · Al modelo solo le llega el email de la sesión, no el rol: a recepción se le dice con quién habla
RECEPCION = INSTRUCCIONES + (
    " Ahora hablas con el equipo de recepción, no con un huésped: puedes consultar la ocupación "
    "y las reservas de todos los huéspedes."
)

# FIX03 · El huésped ya viene identificado por el login, pero el modelo le pide el email o se inventa los datos
HUESPED = INSTRUCCIONES + (
    " El huésped ya se ha identificado en la web: no le pidas el email ni que confirme quién es. "
    "Los datos de sus reservas salen siempre de las herramientas; nunca los inventes. "
    "Si pregunta por una reserva y da su número (R-1234), llama a consultar_reserva antes de contestar."
)
INSTRUCCIONES_PERFIL = {"publico": INSTRUCCIONES, "huesped": HUESPED, "recepcion": RECEPCION}


def perfil(contexto: dict | None) -> str:
    contexto = contexto or {}
    if contexto.get("rol") == "recepcion":
        return "recepcion"
    return "huesped" if contexto.get("email") else "publico"


def crear_agente(contexto: dict | None = None, cliente=None) -> Agente:
    p = perfil(contexto)
    return Agente(cliente=cliente, herramientas=PERFILES[p], contexto=contexto, guardas=Guardas(),
                  instrucciones=INSTRUCCIONES_PERFIL[p])
