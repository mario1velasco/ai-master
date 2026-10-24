"""Sesión 3 · Demo I: el agente de la sesión 1 migrado a LangGraph.

Novedades respecto a la sesión 1:
- Herramientas clasificadas por riesgo (ver comun/herramientas_lc.py).
- Una herramienta sobre una API externa real: convertir_precio.
- emitir_reembolso es irreversible: el grafo se PAUSA y un humano decide.

Uso:  python -m sesion3.agente_langgraph
      (conversación interactiva; prueba «Soy jorge.ruiz@email.com, el pedido ORD-10598
       llegó roto y quiero que me devolváis el dinero»)
"""
import uuid

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from comun.apis_externas import convertir_precio
from comun.grafo import acciones_pendientes, construir_agente
from comun.herramientas_lc import TODAS
from comun.modelo_lc import crear_modelo

INSTRUCCIONES = (
    "Eres el agente de atención al cliente de Lumen Shop, tienda online de cosmética. "
    "Consulta los datos con las herramientas y nunca los inventes. Antes de emitir un reembolso, "
    "comprueba el pedido y que el importe no supera su total. Responde en español, breve y amable."
)
HERRAMIENTAS = TODAS + [convertir_precio]


def crear_agente(modelo=None, checkpointer=None):
    return construir_agente(modelo or crear_modelo(), HERRAMIENTAS, INSTRUCCIONES,
                            requieren_aprobacion=["emitir_reembolso"],
                            checkpointer=checkpointer or InMemorySaver())


def mostrar_traza(mensajes):
    for m in mensajes:
        for ll in getattr(m, "tool_calls", None) or []:
            print(f"   🔧 {ll['name']}({ll['args']})")


def conversar():
    agente = crear_agente()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}, "recursion_limit": 20}
    print("Escribe tu mensaje (o 'salir').")
    while (texto := input("\n👤 Cliente: ")).lower() != "salir":
        resultado = agente.invoke({"messages": [("user", texto)]}, config)
        while acciones := acciones_pendientes(resultado):
            print("\n⏸  El agente quiere ejecutar una acción irreversible:")
            for a in acciones:
                print(f"   {a['herramienta']}({a['argumentos']})")
            aprobar = input("   ¿Aprobar? (s/n): ").strip().lower() == "s"
            motivo = "" if aprobar else input("   Motivo del rechazo: ")
            resultado = agente.invoke(Command(resume={"aprobar": aprobar, "motivo": motivo}), config)
        print(f"🤖 Agente: {resultado['messages'][-1].content}")


if __name__ == "__main__":
    conversar()
