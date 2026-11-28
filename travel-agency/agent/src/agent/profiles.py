"""Mínimo privilegio, capa de perfil (TRAVEL-011): qué herramientas existen para cada rol con chat.

Como `PERFILES` de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion2/permisos.py` y `perfil(contexto)` de
`04_ejercicio_practico/caso-hoteles-albor-v1/albor/configuracion.py`: el rol sale de la sesión, no del modelo, y si
una herramienta no está en el perfil, el modelo ni sabe que existe. El alcance (solo los datos del cliente) lo ponen
los guardarraíles (`guardrails.py`).

Hoy solo existe el perfil del cliente. Las fases 8 (`search_documents`) y 12 (`manage_cancellation`) añaden
herramientas; el gerente que aprueba cancelaciones (fase 12) no tiene chat: decide en `/aprobaciones`.
"""

from contracts.agent import Session
from contracts.errors import ComponentError

PROFILES: dict[str, list[str]] = {
    "client": ["query_db"],  # cliente identificado: solo consulta sus datos
}

DEFAULT_ROLE = "client"  # sin sesión (guardarraíles apagados, como en TRAVEL-006)


def profile(session: Session | None) -> str:
    """El perfil de la sesión. Un rol que no está en `PROFILES` no tiene chat: `unknown_role`.

    Se aplica siempre, también con los guardarraíles apagados: en clase `PERFILES` no depende de `guardas`.
    """
    role = session.role if session is not None else DEFAULT_ROLE
    if role not in PROFILES:
        raise ComponentError("unknown_role", "agent", f"El rol {role} no tiene chat.")
    return role
