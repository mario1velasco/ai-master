"""Guardarraíles del agente (TRAVEL-011): el código revisa lo que entra, lo que hace el agente y lo que sale.

Como `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion2/guardarrailes.py` (y `albor/guardas.py` del caso
Hoteles Albor): «lo que no debe pasar se impide en el código, no se pide en el prompt». Son funciones que no dependen
del grafo de LangGraph, para que otra estrategia del agente (el Plan B de TRAVEL-012) las reutilice tal cual.
"""

import duckdb

from contracts.agent import Session
from contracts.errors import ComponentError


def check_client(con: duckdb.DuckDBPyConnection, session: Session) -> None:
    """El cliente de la sesión tiene que existir en la base.

    Desvío: en clase no se comprueba. Aquí sí, porque con el filtro por cliente de la conexión (capa 2) un id
    inventado daría siempre «no tienes reservas» en vez de un error.
    """
    found = con.execute(
        "SELECT 1 FROM v_resumen_clientes WHERE cliente_id = ? LIMIT 1", [session.client_id]
    ).fetchall()
    if not found:
        raise ComponentError("unknown_client", "agent", f"El cliente {session.client_id} no existe.")
