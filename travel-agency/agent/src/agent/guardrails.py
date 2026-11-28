"""Guardarraíles del agente (TRAVEL-011): el código revisa lo que entra, lo que hace el agente y lo que sale.

Como `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion2/guardarrailes.py` (y `albor/guardas.py` del caso
Hoteles Albor): «lo que no debe pasar se impide en el código, no se pide en el prompt». Son funciones que no dependen
del grafo de LangGraph, para que otra estrategia del agente (el Plan B de TRAVEL-012) las reutilice tal cual.
"""

import re
from collections.abc import Mapping, Sequence

import duckdb

from contracts.agent import Block, BlockType, Session
from contracts.errors import ComponentError
from contracts.sql import SqlResult

# Los mensajes más largos no llegan al modelo; la respuesta es la de clase
MAX_INPUT_CHARS = 2000
TOO_LONG_MESSAGE = "Mensaje demasiado largo. Resume tu consulta, por favor."
# Un número de 13 a 19 cifras, con espacios o guiones entre ellas: el patrón de `revisar_entrada` de clase
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
# IBAN español y DNI (8 cifras y la letra de control), los de clase
IBAN = re.compile(r"\bES\d{2}(?:\s?\d{4}){5}\b")
DNI = re.compile(r"\b\d{8}[A-HJ-NP-TV-Z]\b")
# Capa 1: los ids con dueño que puede nombrar una pregunta (cliente, reserva, incidencia), y dónde está su dueño
OWNED_ID = re.compile(r"\b[CRI]-\d+\b", re.IGNORECASE)
OWNER_QUERIES = {
    "C": "SELECT cliente_id FROM v_resumen_clientes WHERE cliente_id = ?",
    "R": "SELECT cliente_id FROM v_reservas_cliente WHERE reserva_id = ? LIMIT 1",
    "I": "SELECT cliente_id FROM v_incidencias WHERE incidencia_id = ?",
}
NOT_OWN_DATA = "solo puedes consultar los datos del cliente identificado"
# Capa 3: las columnas con dueño que puede traer una fila del resultado (las de las vistas, sin alias)
OWNER_COLUMNS = ("cliente_id", "reserva_id", "incidencia_id")
# Salida: la respuesta para el cliente si la del modelo lleva datos personales de otro (el texto de clase)
OTHER_CLIENT_DATA = "No puedo compartir datos personales de otros clientes. ¿Te ayudo con algo de tu cuenta?"
# El email y el nombre completo de cada cliente; salen de la base, no de una lista a mano. El email solo está en
# `crudo.clientes` (lo lee este código, no el SQL del modelo, que el validador no deja pasar de las vistas)
CLIENTS_PERSONAL_DATA = "SELECT cliente_id, email, nombre || ' ' || apellidos FROM crudo.clientes"


def luhn_valid(number: str) -> bool:
    """Comprueba el dígito de control de una tarjeta: evita confundir cualquier número largo con una tarjeta.

    `luhn_valido` de `sesion2/guardarrailes.py`, igual.
    """
    digits = [int(d) for d in number][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return total % 10 == 0


class Guardrails:
    """Los puntos de control de un turno, con el registro de lo bloqueado o modificado (`Guardarrailes` de clase).

    Se crea uno por turno: `log` es lo que acaba en `AgentAnswer.blocks`. `con` es de donde salen los dueños de cada
    id (en clase, los diccionarios de `tienda.py`); la sesión llega en cada llamada, como el `contexto` de clase.
    """

    def __init__(self, con: duckdb.DuckDBPyConnection) -> None:
        self.con = con
        self.log: list[Block] = []
        # El dueño de cada id ya consultado en el turno: la capa 3 mira cada fila y los ids se repiten mucho (con
        # `data/`, 50 filas eran ~1 s de consultas). Vive lo que el turno, así que nunca se queda viejo.
        self._owners: dict[str, str | None] = {}

    # --- 0. Sesión --------------------------------------------------------
    def check_session(self, session: Session | None) -> Session:
        """Con los guardarraíles, el chat es solo para clientes: la sesión tiene que traer un cliente que exista.

        Desvío: en clase no se comprueba que exista. Aquí sí, porque con el filtro por cliente de la conexión (capa 2)
        un id inventado daría siempre «no tienes reservas» en vez de un error.
        """
        if session is None:
            raise ComponentError(
                "missing_client", "agent", "Falta el cliente de la sesión: el chat es solo para clientes."
            )
        if self._owner(session.client_id) is None:
            raise ComponentError("unknown_client", "agent", f"El cliente {session.client_id} no existe.")
        return session

    def _note(self, type_: BlockType, reason: str) -> str:
        """Anota el bloqueo y devuelve el motivo (`_anotar` de clase)."""
        self.log.append(Block(type=type_, reason=reason))
        return reason

    # --- 1. Entrada -------------------------------------------------------
    def check_input(self, text: str) -> tuple[str, str | None]:
        """Enmascara los datos sensibles antes de que lleguen al modelo y a los logs (`revisar_entrada` de clase).

        Devuelve el texto limpio y, si el mensaje no debe llegar al modelo, la respuesta para el cliente (o None).
        """
        if len(text) > MAX_INPUT_CHARS:
            return text, self._note(BlockType.input, TOO_LONG_MESSAGE)

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

    # --- 2. Herramientas --------------------------------------------------
    def check_tool(self, name: str, arguments: dict[str, object], session: Session) -> str | None:
        """Antes de ejecutar una tool: el motivo si se bloquea, o None (`revisar_herramienta` de clase).

        Capa 1. Desvío: en clase se mira el dueño de un argumento (`id_pedido`); aquí el argumento es una pregunta en
        lenguaje natural, así que se buscan en ella los ids de cliente, reserva e incidencia. Un id que no existe pasa,
        como en clase (solo se bloquea si existe y es de otro).
        """
        if name == "query_db":
            for found in OWNED_ID.findall(str(arguments.get("question", ""))):
                if self._belongs_to_other(found.upper(), session):
                    return self._note(BlockType.tool, NOT_OWN_DATA)
        return None

    def check_result(self, result: SqlResult, session: Session) -> str | None:
        """Capa 3 sobre lo que devolvió `query_db`: el motivo si alguna consulta trae filas de otro cliente.

        Como `revisar_resultado` de clase, el punto de control de después de ejecutar y antes de que el modelo lo vea.
        """
        for query in result.queries:
            if (reason := self.check_rows(query.rows, session)) is not None:
                return reason
        return None

    def check_rows(self, rows: Sequence[Mapping[str, object]], session: Session) -> str | None:
        """Capa 3: antes de que el modelo vea el resultado de una tool, el motivo si trae datos de otro cliente.

        La comprobación de dueño de `revisar_herramienta` de clase, aplicada a las filas: si una fila trae el
        `cliente_id`, la `reserva_id` o la `incidencia_id` de otro cliente, se bloquea el resultado entero (como un
        reembolso bloqueado, que no se ejecuta en parte). Con la capa 2 no debería pasar nunca: es la última red.
        """
        for row in rows:
            for column in OWNER_COLUMNS:
                value = row.get(column)
                if (
                    isinstance(value, str)
                    and OWNED_ID.fullmatch(value)
                    and self._belongs_to_other(value.upper(), session)
                ):
                    return self._note(BlockType.tool, NOT_OWN_DATA)
        return None

    # --- 4. Salida --------------------------------------------------------
    def check_output(self, text: str, session: Session) -> tuple[str, str | None]:
        """Antes de enviar la respuesta: sin datos personales de otros clientes (`revisar_salida` de clase).

        Desvío: en clase, el teléfono y la dirección; aquí, el email y el nombre completo (nombre y apellidos), que es
        lo que tiene la base. Si los lleva, se sustituye la respuesta entera. Sin el filtro de «información interna»: el
        prompt no guarda ningún secreto (LLM07).
        """
        lowered_text = text.lower()
        personal_data_by_client = {
            client_id: [value.lower() for value in personal if value]
            for client_id, *personal in self.con.execute(CLIENTS_PERSONAL_DATA).fetchall()
        }
        # Sus propios datos sí, también si otro cliente comparte alguno (dos clientes con el mismo nombre completo)
        own_values = set(personal_data_by_client.get(session.client_id, []))
        other_values = {
            value
            for client_id, personal in personal_data_by_client.items()
            if client_id != session.client_id
            for value in personal
        } - own_values
        if any(value in lowered_text for value in other_values):
            return OTHER_CLIENT_DATA, self._note(BlockType.output, "datos personales de otro cliente")
        return text, None

    def _belongs_to_other(self, owned_id: str, session: Session) -> bool:
        """El id existe y es de otro cliente. Un id que no existe no es de nadie: pasa, como en clase."""
        owner = self._owner(owned_id)
        return owner is not None and owner != session.client_id

    def _owner(self, owned_id: str) -> str | None:
        """El cliente dueño de un id (cliente, reserva o incidencia), o None si no existe. Se recuerda en el turno."""
        if owned_id not in self._owners:
            query = OWNER_QUERIES.get(owned_id[:1])
            rows = self.con.execute(query, [owned_id]).fetchall() if query is not None else []
            self._owners[owned_id] = rows[0][0] if rows else None
        return self._owners[owned_id]
