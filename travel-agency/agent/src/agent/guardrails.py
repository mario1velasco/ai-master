"""Guardarraíles del agente (TRAVEL-011): el código revisa lo que entra, lo que hace el agente y lo que sale.

Como `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion2/guardarrailes.py` (y `albor/guardas.py` del caso
Hoteles Albor): «lo que no debe pasar se impide en el código, no se pide en el prompt». Son funciones que no dependen
del grafo de LangGraph, para que otra estrategia del agente (el Plan B de TRAVEL-012) las reutilice tal cual.
"""

import re

import duckdb

from contracts.agent import Block, BlockType, Session
from contracts.errors import ComponentError

# Un número de 13 a 19 cifras, con espacios o guiones entre ellas: el patrón de `revisar_entrada` de clase
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
# IBAN español y DNI (8 cifras y la letra de control), los de clase
IBAN = re.compile(r"\bES\d{2}(?:\s?\d{4}){5}\b")
DNI = re.compile(r"\b\d{8}[A-HJ-NP-TV-Z]\b")


def luhn_valid(number: str) -> bool:
    """Comprueba el dígito de control de una tarjeta: evita confundir cualquier número largo con una tarjeta.

    `luhn_valido` de `sesion2/guardarrailes.py`, igual.
    """
    digits = [int(d) for d in number][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return total % 10 == 0


class Guardrails:
    """Los puntos de control de un turno, con el registro de lo bloqueado o modificado (`Guardarrailes` de clase).

    Se crea uno por turno: `log` es lo que acaba en `AgentAnswer.blocks`.
    """

    def __init__(self) -> None:
        self.log: list[Block] = []

    def _note(self, type_: BlockType, reason: str) -> str:
        """Anota el bloqueo y devuelve el motivo (`_anotar` de clase)."""
        self.log.append(Block(type=type_, reason=reason))
        return reason

    # --- 1. Entrada -------------------------------------------------------
    def check_input(self, text: str) -> tuple[str, str | None]:
        """Enmascara los datos sensibles antes de que lleguen al modelo y a los logs (`revisar_entrada` de clase).

        Devuelve el texto limpio y, si el mensaje no debe llegar al modelo, la respuesta para el cliente (o None).
        """

        def card(match: re.Match[str]) -> str:
            number = re.sub(r"\D", "", match.group(0))
            if 13 <= len(number) <= 19 and luhn_valid(number):
                self._note(BlockType.input, "tarjeta enmascarada")
                return f"[TARJETA ****{number[-4:]}]"
            return match.group(0)

        text = CARD.sub(card, text)
        if IBAN.search(text):
            text = IBAN.sub("[IBAN]", text)
            self._note(BlockType.input, "IBAN enmascarado")
        if DNI.search(text):
            text = DNI.sub("[DNI]", text)
            self._note(BlockType.input, "DNI enmascarado")
        return text, None


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
