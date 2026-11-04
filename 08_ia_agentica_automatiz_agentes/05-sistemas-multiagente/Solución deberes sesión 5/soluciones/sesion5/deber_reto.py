"""Solución · Reto de la sesión 5: ¿compensa el equipo frente a un único agente?

Ejecuta el mismo ticket con un agente único (todas las herramientas, un solo
prompt) y con el equipo, y compara tokens y respuestas. No hay una respuesta
universal: depende del ticket, del modelo y de lo que valga la calidad extra.

Uso:  python -m soluciones.sesion5.deber_reto "Soy marta.lopez@email.com. Mi pedido ORD-10544 no llega."
"""
import sys

from comun.grafo import construir_agente
from comun.herramientas_lc import LECTURA
from comun.modelo_lc import crear_modelo
from comun.utilidades import tokens_de
from sesion5.equipo_supervisor import atender_ticket, construir_equipo

PROMPT_UNICO = ("Eres el agente de atención al cliente de Lumen Shop. Clasifica la incidencia, consulta con las "
                "herramientas los datos reales y responde al cliente en español, breve y empático.")


def comparar(ticket: str, modelo=None) -> dict:
    modelo = modelo or crear_modelo()
    mensajes = construir_agente(modelo, LECTURA, PROMPT_UNICO).invoke({"messages": [("user", ticket)]})["messages"]
    unico = {"tokens": tokens_de(*mensajes), "respuesta": mensajes[-1].content}
    resultado_equipo = atender_ticket(ticket, construir_equipo(modelo))
    equipo = {"tokens": sum(resultado_equipo["tokens"].values()), "respuesta": resultado_equipo.get("respuesta")}
    factor = equipo["tokens"] / unico["tokens"] if unico["tokens"] else float("nan")
    print(f"\nAgente único: {unico['tokens']} tokens\nEquipo:       {equipo['tokens']} tokens (×{factor:.1f})")
    return {"unico": unico, "equipo": equipo}


if __name__ == "__main__":
    comparar(sys.argv[1] if len(sys.argv) > 1 else input("Ticket: "))
