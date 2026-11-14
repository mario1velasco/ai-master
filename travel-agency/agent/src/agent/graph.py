"""El grafo del agente: el de `construir_agente` de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/grafo.py`.

    agente ──(pide herramientas)──► herramientas ──► agente
       └──(responde)──► FIN

Desvío: sin el nodo `aprobacion` ni `checkpointer` (no hay acciones irreversibles hasta la fase 12 y el hilo con
`SqliteSaver` es de la fase 7b).
"""

from collections.abc import Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode


def build_agent(model: BaseChatModel, tools: Sequence[BaseTool], instructions: str) -> CompiledStateGraph:
    """Compila el grafo: el modelo con las tools, las instrucciones delante del historial y `ToolNode`."""
    model_with_tools = model.bind_tools(tools)

    def agent(state: MessagesState) -> dict[str, list]:
        response = model_with_tools.invoke([SystemMessage(instructions), *state["messages"]])
        return {"messages": [response]}

    def route(state: MessagesState) -> str:
        last = state["messages"][-1]
        calls = last.tool_calls if isinstance(last, AIMessage) else []
        return "tools" if calls else END

    # ty todavía no ve que un TypedDict cumple `StateLike` de LangGraph: falso positivo
    graph = StateGraph(MessagesState)  # ty: ignore[invalid-argument-type]
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route, ["tools", END])
    graph.add_edge("tools", "agent")
    return graph.compile()
