"""Constructor de agentes con LangGraph (sesiones 3 a 6).

Es el mismo bucle de la sesión 1, pero como grafo de estados:

    agente ──(pide herramientas)──► herramientas ──► agente
       │  └─(pide una sensible)──► aprobacion ──(sí)─► herramientas
       │                              └──(no)──► agente
       └──(responde)──► FIN

Ganamos tres cosas: el estado se guarda en cada paso (checkpointing), la
ejecución se puede pausar para que un humano apruebe, y el flujo se puede
dibujar, ampliar y depurar.
"""
from typing import Literal

from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt


def construir_agente(modelo, herramientas, instrucciones: str, requieren_aprobacion=(), checkpointer=None):
    modelo_con_herramientas = modelo.bind_tools(herramientas)
    sensibles = set(requieren_aprobacion)

    def agente(estado: MessagesState):
        respuesta = modelo_con_herramientas.invoke([SystemMessage(instrucciones)] + estado["messages"])
        return {"messages": [respuesta]}

    def enrutar(estado: MessagesState) -> str:
        llamadas = estado["messages"][-1].tool_calls
        if not llamadas:
            return END
        return "aprobacion" if any(ll["name"] in sensibles for ll in llamadas) else "herramientas"

    def aprobacion(estado: MessagesState) -> Command[Literal["herramientas", "agente"]]:
        llamadas = estado["messages"][-1].tool_calls
        # interrupt() pausa el grafo y guarda el estado; se reanuda con Command(resume=...)
        decision = interrupt({"acciones": [{"herramienta": ll["name"], "argumentos": ll["args"]} for ll in llamadas]})
        if decision.get("aprobar"):
            return Command(goto="herramientas")
        rechazo = f"Acción rechazada por un supervisor humano. Motivo: {decision.get('motivo', 'no indicado')}"
        return Command(goto="agente", update={"messages": [
            ToolMessage(content=rechazo, tool_call_id=ll["id"]) for ll in llamadas]})

    # ! Esta basicamente es la definición del agente
    grafo = StateGraph(MessagesState)
    grafo.add_node("agente", agente)
    grafo.add_node("herramientas", ToolNode(herramientas))
    grafo.add_node("aprobacion", aprobacion)
    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", enrutar, ["herramientas", "aprobacion", END])
    grafo.add_edge("herramientas", "agente")
    return grafo.compile(checkpointer=checkpointer)


def acciones_pendientes(resultado: dict) -> list[dict] | None:
    """Si el grafo está pausado esperando aprobación, devuelve las acciones a aprobar."""
    interrupciones = resultado.get("__interrupt__")
    return interrupciones[0].value["acciones"] if interrupciones else None
