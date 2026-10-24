"""Sesión 3 · Muestra la estructura del grafo del agente en formato Mermaid.

Uso:  python -m sesion3.dibujar_grafo
Pega el resultado en https://mermaid.live para verlo dibujado.
"""
from sesion3.agente_langgraph import crear_agente

if __name__ == "__main__":
    print(crear_agente().get_graph().draw_mermaid())
