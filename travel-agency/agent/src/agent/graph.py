"""El grafo del agente: el de `construir_agente` de `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/grafo.py`.

    agente ──(pide herramientas)──► herramientas ──► agente
       └──(responde)──► FIN

Desvíos: sin el nodo `aprobacion` ni `checkpointer` (no hay acciones irreversibles hasta la fase 12 y el hilo con
`SqliteSaver` es de la fase 7b), y cada llamada al modelo va dentro de un span `llm.agent` con sus `LlmCallMetrics`
(la idea de `comun/medidor.py`: medir alrededor de cada llamada; como el span `llm.text2sql` de text2sql).
"""

from collections.abc import Sequence

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from agent.model import llm_call_fields
from contracts.metrics import Component, LlmCallMetrics, Versions
from telemetry import span


def build_agent(
    model: ChatOllama, tools: Sequence[BaseTool], instructions: str, versions: Versions
) -> CompiledStateGraph:
    """Compila el grafo: el modelo con las tools, las instrucciones delante del historial y `ToolNode`."""
    model_with_tools = model.bind_tools(tools)

    def agent(state: MessagesState) -> dict[str, list]:
        messages = [SystemMessage(instructions), *state["messages"]]
        with span("llm.agent", component=Component.agent, metrics_cls=LlmCallMetrics, versions=versions) as s:
            response = model_with_tools.invoke(messages)
            if isinstance(response, AIMessage):
                s.fields.update(llm_call_fields(model, messages, len(tools), response))
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
