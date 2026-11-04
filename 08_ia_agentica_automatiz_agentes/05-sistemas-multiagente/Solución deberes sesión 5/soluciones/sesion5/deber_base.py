"""Solución · Deber base de la sesión 5: añadir un cuarto agente.

El agente de devoluciones aplica la política de la tienda y propone (no emite)
un reembolso. Para incorporarlo basta con crear su fábrica y añadirlo al
registro de agentes: el supervisor lo descubre por su descripción.

Uso:  python -m soluciones.sesion5.deber_base "Soy jorge.ruiz@email.com, el protector solar del pedido ORD-10598 llegó roto."
"""
import sys

from langchain_core.messages import HumanMessage, SystemMessage

from comun.utilidades import tokens_de
from sesion5.equipo_supervisor import AGENTES, atender_ticket, construir_equipo, resumen_notas

POLITICA = ("Devoluciones gratuitas en 30 días con el producto sin abrir. Producto dañado en el envío: reembolso "
            "completo con foto del daño. Reembolsos de más de 50 € requieren aprobación de un supervisor humano.")


def crear_devoluciones(modelo):
    prompt = (f"Eres el especialista en devoluciones de Lumen Shop. Política:\n{POLITICA}\nIndica si procede "
              "devolución o reembolso, por qué importe y qué necesita aportar el cliente. No emitas nada.")

    def devoluciones(estado):
        respuesta = modelo.invoke([SystemMessage(prompt), HumanMessage(
            f"Ticket: {estado['ticket']}\nNotas:\n{resumen_notas(estado)}")])
        return {"notas": {"devoluciones": respuesta.content}, "tokens": {"devoluciones": tokens_de(respuesta)},
                "historial": ["devoluciones"]}
    return devoluciones


AGENTES_AMPLIADOS = {**AGENTES, "devoluciones": (
    "aplica la política de devoluciones y propone reembolsos; consúltalo en productos dañados o devoluciones",
    crear_devoluciones)}

if __name__ == "__main__":
    resultado = atender_ticket(sys.argv[1] if len(sys.argv) > 1 else input("Ticket: "),
                               construir_equipo(agentes=AGENTES_AMPLIADOS))
    print("\n✉️ ", resultado.get("respuesta"))
