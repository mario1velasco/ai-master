"""Solución · Deber base de la sesión 2: añadir reflexión al plan-and-execute.

Antes de devolver la síntesis final, el crítico de la demo la revisa. Si no la
aprueba, se vuelve a sintetizar incluyendo sus comentarios. Reutilizamos las
piezas de las demos: planificar, ejecutar_paso, sintetizar y criticar.

Uso:  python -m soluciones.sesion2.deber_base "Marta (marta.lopez@email.com) quiere repetir su último pedido."
"""
import sys

from comun.llm import crear_cliente
from sesion2.plan_and_execute import ejecutar_paso, planificar, sintetizar
from sesion2.reflexion import criticar


def plan_execute_reflexion(tarea: str, max_rondas: int = 2, cliente=None, verbose: bool = True) -> str:
    cliente = cliente or crear_cliente()
    resultados = []
    for paso in planificar(tarea, cliente):
        resultados.append({"paso": paso, "resultado": ejecutar_paso(tarea, paso, resultados, cliente)})

    respuesta = sintetizar(tarea, resultados, cliente)
    for _ in range(max_rondas):
        revision = criticar(tarea, respuesta, cliente)
        if verbose:
            print(f"🔍 {revision}")
        if revision.get("aprobado"):
            break
        respuesta = sintetizar(tarea, resultados, cliente,
                               indicaciones=f"Corrige esto de la versión anterior: {revision.get('comentarios')}")
    return respuesta


if __name__ == "__main__":
    print("\n✅", plan_execute_reflexion(sys.argv[1] if len(sys.argv) > 1 else input("Tarea: ")))
