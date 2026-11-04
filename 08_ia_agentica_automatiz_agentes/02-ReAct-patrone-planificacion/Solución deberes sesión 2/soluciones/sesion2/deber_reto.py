"""Solución · Reto de la sesión 2: replanificación ante fallos.

Tras cada paso, un verificador decide si el paso se ha completado. Si no, el
planificador recibe lo hecho hasta ahora y el fallo, y genera nuevos pasos
para lo que queda. Limitamos el número de replanificaciones para no entrar en
bucle.

Uso:  python -m soluciones.sesion2.deber_reto "¿Dónde está el último pedido de marta.lopez@email.com?"
"""
import sys

from comun.llm import crear_cliente
from comun.utilidades import extraer_json
from sesion2.plan_and_execute import PLANIFICADOR, ejecutar_paso, llamar, planificar, sintetizar

VERIFICADOR = ('Indica si el resultado completa el paso. Responde solo con JSON: '
               '{"completado": true/false, "motivo": "..."}')


def paso_completado(paso: str, resultado: str, cliente) -> dict:
    return extraer_json(llamar(cliente, VERIFICADOR, f"Paso: {paso}\nResultado: {resultado}"))


def replanificar(tarea: str, resultados: list[dict], fallo: str, cliente) -> list[str]:
    hecho = "\n".join(f"- {r['paso']}: {r['resultado']}" for r in resultados)
    consulta = (f"Tarea: {tarea}\nYa hecho:\n{hecho}\nEl último paso ha fallado: {fallo}\n"
                "Propón los pasos que quedan, buscando una alternativa al paso fallido. "
                "Si no hay alternativa, el último paso debe ser informar al cliente del problema.")
    return extraer_json(llamar(cliente, PLANIFICADOR, consulta))["pasos"]


def plan_execute_replan(tarea: str, max_replanes: int = 2, cliente=None, verbose: bool = True) -> str:
    cliente = cliente or crear_cliente()
    pendientes, resultados, replanes = planificar(tarea, cliente), [], 0
    while pendientes:
        paso = pendientes.pop(0)
        resultado = ejecutar_paso(tarea, paso, resultados, cliente)
        resultados.append({"paso": paso, "resultado": resultado})
        verificacion = paso_completado(paso, resultado, cliente)
        if verbose:
            print(f"▶ {paso}\n  {resultado}\n  {'✅' if verificacion['completado'] else '❌'} {verificacion['motivo']}")
        if not verificacion["completado"] and replanes < max_replanes:
            replanes += 1
            pendientes = replanificar(tarea, resultados, verificacion["motivo"], cliente)
            if verbose:
                print("🔄 Nuevo plan:", pendientes)
    return sintetizar(tarea, resultados, cliente)


if __name__ == "__main__":
    print("\n✅", plan_execute_replan(sys.argv[1] if len(sys.argv) > 1 else input("Tarea: ")))
