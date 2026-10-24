"""Sesión 5 · Demo: equipo de agentes coordinado por un supervisor.

    ticket ─► supervisor ─► clasificador ─┐
                 ▲   ├────► logistica ────┤
                 │   └────► redactor ─────┤
                 └────────────────────────┘   (hasta que el supervisor decide FIN)

- Clasificador: tipo de incidencia y urgencia. Sin herramientas.
- Logística: consulta pedidos, stock y transportista. Es un agente con herramientas.
- Redactor: escribe la respuesta al cliente con lo que han averiguado los demás.

Cada agente tiene su propio prompt y su propio contexto: el redactor no ve las
llamadas a herramientas de logística, solo su conclusión. Al final se muestran
los tokens que ha gastado cada uno.

Uso:  python -m sesion5.equipo_supervisor "Soy marta.lopez@email.com. Mi pedido ORD-10544 no llega y lo necesito para un regalo el viernes."
"""
import operator
import sys
from typing import Annotated, Callable, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from comun.grafo import construir_agente
from comun.herramientas_lc import LECTURA
from comun.modelo_lc import crear_modelo
from comun.utilidades import extraer_json, tokens_de

MAX_PASOS = 6  # protección frente a bucles entre agentes


def sumar_dicts(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) + b.get(k, 0) for k in a.keys() | b.keys()}


class EstadoEquipo(TypedDict, total=False):
    ticket: str
    notas: Annotated[dict, operator.or_]       # lo que aporta cada agente
    tokens: Annotated[dict, sumar_dicts]       # coste por agente
    historial: Annotated[list, operator.add]   # orden en que han trabajado
    siguiente: str
    respuesta: str


def resumen_notas(estado: EstadoEquipo) -> str:
    return "\n".join(f"[{agente}] {nota}" for agente, nota in estado.get("notas", {}).items()) or "(sin notas todavía)"


# --- Agentes especializados -------------------------------------------------
def crear_clasificador(modelo):
    prompt = ("Clasifica la incidencia de un cliente de Lumen Shop. Responde solo con JSON: "
              '{"tipo": "retraso|producto_danado|stock|devolucion|otro", "urgencia": "alta|media|baja", '
              '"email": "... o null", "pedido": "... o null"}')

    def clasificador(estado: EstadoEquipo):
        respuesta = modelo.invoke([SystemMessage(prompt), HumanMessage(estado["ticket"])])
        return {"notas": {"clasificador": extraer_json(respuesta.content)}, "tokens": {"clasificador": tokens_de(respuesta)},
                "historial": ["clasificador"]}
    return clasificador


def crear_logistica(modelo):
    agente = construir_agente(modelo, LECTURA, (
        "Eres el especialista de logística de Lumen Shop. Averigua con las herramientas el estado real de "
        "pedidos, envíos y stock. Termina con un resumen de hechos en 3 frases, sin redactar para el cliente."))

    def logistica(estado: EstadoEquipo):
        consulta = f"Ticket: {estado['ticket']}\nNotas del equipo:\n{resumen_notas(estado)}"
        mensajes = agente.invoke({"messages": [("user", consulta)]}, {"recursion_limit": 15})["messages"]
        return {"notas": {"logistica": mensajes[-1].content}, "tokens": {"logistica": tokens_de(*mensajes)},
                "historial": ["logistica"]}
    return logistica


def crear_redactor(modelo):
    prompt = ("Eres el redactor de atención al cliente de Lumen Shop. Escribe la respuesta final al cliente "
              "usando SOLO los hechos de las notas del equipo. Español, breve, empático. Si la urgencia es alta, "
              "ofrece una solución concreta sin prometer lo que no está confirmado.")

    def redactor(estado: EstadoEquipo):
        respuesta = modelo.invoke([SystemMessage(prompt), HumanMessage(
            f"Ticket: {estado['ticket']}\nNotas del equipo:\n{resumen_notas(estado)}")])
        return {"respuesta": respuesta.content, "notas": {"redactor": "respuesta redactada"},
                "tokens": {"redactor": tokens_de(respuesta)}, "historial": ["redactor"]}
    return redactor


AGENTES: dict[str, tuple[str, Callable]] = {
    "clasificador": ("identifica tipo de incidencia, urgencia, email y pedido", crear_clasificador),
    "logistica": ("consulta pedidos, envíos y stock con herramientas", crear_logistica),
    "redactor": ("redacta la respuesta final al cliente; siempre es el último", crear_redactor),
}


# --- Supervisor ---------------------------------------------------------------
def crear_supervisor(modelo, agentes: dict):
    catalogo = "\n".join(f"- {nombre}: {descripcion}" for nombre, (descripcion, _) in agentes.items())
    prompt = (f"Eres el supervisor del equipo de atención al cliente de Lumen Shop. Tu equipo:\n{catalogo}\n"
              "Decide quién trabaja a continuación. No llames dos veces al mismo agente sin motivo. "
              'Responde solo con JSON: {"siguiente": "<agente> o FIN", "motivo": "..."}')

    def supervisor(estado: EstadoEquipo):
        if estado.get("respuesta") or len(estado.get("historial", [])) >= MAX_PASOS:
            return {"siguiente": "FIN"}
        respuesta = modelo.invoke([SystemMessage(prompt), HumanMessage(
            f"Ticket: {estado['ticket']}\nTrabajo hecho: {estado.get('historial', [])}\n"
            f"Notas:\n{resumen_notas(estado)}")])
        try:
            decision = extraer_json(respuesta.content)
        except ValueError:  # si el supervisor no responde en JSON, que el redactor cierre el ticket
            decision = {"siguiente": "redactor" if "redactor" in agentes else "FIN", "motivo": "respuesta no válida"}
        siguiente = decision.get("siguiente") if decision.get("siguiente") in agentes else "FIN"
        print(f"🧭 Supervisor → {siguiente}: {decision.get('motivo', '')}")
        return {"siguiente": siguiente, "tokens": {"supervisor": tokens_de(respuesta)}}
    return supervisor


def construir_equipo(modelo=None, agentes: dict = AGENTES):
    modelo = modelo or crear_modelo()
    grafo = StateGraph(EstadoEquipo)
    grafo.add_node("supervisor", crear_supervisor(modelo, agentes))
    for nombre, (_, fabrica) in agentes.items():
        grafo.add_node(nombre, fabrica(modelo))
        grafo.add_edge(nombre, "supervisor")
    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges("supervisor", lambda e: END if e["siguiente"] == "FIN" else e["siguiente"],
                                list(agentes) + [END])
    return grafo.compile()


def atender_ticket(ticket: str, equipo=None) -> EstadoEquipo:
    resultado = (equipo or construir_equipo()).invoke({"ticket": ticket, "notas": {}, "tokens": {}, "historial": []},
                                                      {"recursion_limit": 30})
    print("\n📊 Tokens por agente:", resultado["tokens"], "· total:", sum(resultado["tokens"].values()))
    return resultado


if __name__ == "__main__":
    resultado = atender_ticket(sys.argv[1] if len(sys.argv) > 1 else input("Ticket: "))
    print("\n✉️ ", resultado.get("respuesta", "(sin respuesta)"))
