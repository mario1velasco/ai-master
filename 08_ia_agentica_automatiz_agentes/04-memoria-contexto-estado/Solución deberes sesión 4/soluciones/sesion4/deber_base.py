"""Solución · Deber base de la sesión 4: comprimir el historial.

Cuando la conversación supera un umbral de tokens, los mensajes antiguos se
sustituyen por un resumen y se conservan literales los más recientes. Se
aplica antes de cada llamada al modelo. Estimamos tokens como caracteres / 4,
suficiente para decidir cuándo comprimir.
"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

RESUMIDOR = ("Resume esta conversación de atención al cliente en 5 frases como máximo. Conserva emails, "
             "números de pedido, importes y lo que el cliente ha pedido.")


def tokens_aproximados(mensajes) -> int:
    return sum(len(str(m.content)) + len(str(getattr(m, "tool_calls", ""))) for m in mensajes) // 4


def punto_de_corte(mensajes, conservar: int) -> int:
    """Índice desde el que conservar mensajes sin partir una llamada a herramienta de su resultado."""
    corte = max(len(mensajes) - conservar, 0)
    while corte > 0 and isinstance(mensajes[corte], ToolMessage):
        corte -= 1
    return corte


def comprimir_historial(mensajes, modelo, max_tokens: int = 2000, conservar: int = 4):
    if tokens_aproximados(mensajes) <= max_tokens:
        return mensajes
    corte = punto_de_corte(mensajes, conservar)
    if corte == 0:
        return mensajes
    antiguos = "\n".join(f"{m.type}: {m.content}" for m in mensajes[:corte])
    resumen = modelo.invoke([SystemMessage(RESUMIDOR), HumanMessage(antiguos)]).content
    return [AIMessage(f"[Resumen de la conversación anterior] {resumen}")] + list(mensajes[corte:])
