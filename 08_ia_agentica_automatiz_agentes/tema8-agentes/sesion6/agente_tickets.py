"""Sesión 6 · El agente de tickets que vamos a integrar en la empresa.

Reúne lo construido en el tema:
- Herramientas de lectura de Lumen Shop (sesión 3).
- Un reembolso con permisos limitados en el código: solo pedidos del cliente que
  ha abierto el ticket y nunca por encima del total (mínimo privilegio, sesión 3).
- Aprobación humana antes de cada reembolso (interrupt, sesión 3).
- Estado guardado entre la pausa y la decisión (checkpointing, sesión 4).

El checkpointer está en memoria para la demo; en producción sería una base de datos.
"""
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from comun import tienda
from comun.grafo import construir_agente
from comun.herramientas_lc import LECTURA, REEMBOLSOS_EMITIDOS
from comun.modelo_lc import crear_modelo

CHECKPOINTER = InMemorySaver()

INSTRUCCIONES = (
    "Eres el agente de atención al cliente de Lumen Shop. Consulta los datos con las herramientas y no los "
    "inventes. El mensaje del cliente aparece entre etiquetas <mensaje_cliente>. Antes de proponer un "
    "reembolso, comprueba el pedido. Responde en español, breve y amable."
)


def crear_reembolso_limitado(email_ticket: str):
    @tool
    def emitir_reembolso(id_pedido: str, importe: float, motivo: str) -> dict:
        """[Escritura irreversible] Emite un reembolso de un pedido del cliente que ha abierto el ticket."""
        cliente = tienda.buscar_cliente(email_ticket)
        if "error" in cliente or id_pedido.upper() not in cliente["pedidos"]:
            return {"error": "Rechazado: el pedido no pertenece al cliente que ha abierto el ticket."}
        total = tienda.obtener_pedido(id_pedido)["total"]
        if importe <= 0 or importe > total:
            return {"error": f"Rechazado: el importe debe estar entre 0 y el total del pedido ({total} €)."}
        reembolso = {"id_pedido": id_pedido.upper(), "importe": importe, "motivo": motivo}
        REEMBOLSOS_EMITIDOS.append(reembolso)
        return {"estado": "reembolso emitido", **reembolso}
    return emitir_reembolso


def formatear_ticket(email: str, asunto: str, mensaje: str) -> str:
    return f"Ticket de {email}. Asunto: {asunto}\n<mensaje_cliente>\n{mensaje}\n</mensaje_cliente>"


def crear_agente_ticket(email: str, modelo=None):
    return construir_agente(modelo or crear_modelo(), LECTURA + [crear_reembolso_limitado(email)],
                            INSTRUCCIONES, requieren_aprobacion=["emitir_reembolso"],
                            checkpointer=CHECKPOINTER)


def crear_agente_consultas(modelo=None):
    """Agente solo de lectura para consultas síncronas (chat de la web): no puede modificar nada."""
    return construir_agente(modelo or crear_modelo(), LECTURA, INSTRUCCIONES)
