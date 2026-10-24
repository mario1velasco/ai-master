"""Sesión 2 · Demo II: plan-and-execute.

1. Un planificador descompone la tarea en pasos (una sola llamada).
2. Un ejecutor resuelve cada paso con el agente de la sesión 1.
3. Un sintetizador redacta la respuesta final con todos los resultados.

El plan es visible antes de ejecutar nada: se puede auditar o pedir que un
humano lo apruebe. A cambio, si algo falla a mitad, el plan no se adapta
(eso es el reto de los deberes).

Uso:  python -m sesion2.plan_and_execute "Marta (marta.lopez@email.com) quiere repetir su último pedido. ¿Es posible?"
"""
import sys

from comun.herramientas import FUNCIONES, HERRAMIENTAS
from comun.llm import MODELO, crear_cliente
from comun.utilidades import extraer_json
from sesion1.agente_minimo import ejecutar_agente

PLANIFICADOR = (
    "Eres el planificador del equipo de atención al cliente de Lumen Shop. Descompón la tarea en "
    "pasos concretos (máximo 5). Herramientas disponibles para el ejecutor: "
    + ", ".join(h["function"]["name"] for h in HERRAMIENTAS)
    + '. Responde solo con JSON: {"pasos": ["paso 1", "paso 2", ...]}'
)


def llamar(cliente, sistema: str, usuario: str) -> str:
    respuesta = cliente.chat.completions.create(
        model=MODELO, messages=[{"role": "system", "content": sistema}, {"role": "user", "content": usuario}])
    return respuesta.choices[0].message.content or ""


def planificar(tarea: str, cliente) -> list[str]:
    return extraer_json(llamar(cliente, PLANIFICADOR, tarea))["pasos"]


def ejecutar_paso(tarea: str, paso: str, resultados: list[dict], cliente) -> str:
    contexto = "\n".join(f"- {r['paso']}: {r['resultado']}" for r in resultados) or "ninguno"
    consulta = f"Tarea global: {tarea}\nResultados de pasos anteriores:\n{contexto}\n\nResuelve SOLO este paso: {paso}"
    return ejecutar_agente(consulta, cliente=cliente, herramientas=HERRAMIENTAS, funciones=FUNCIONES, verbose=False)


def sintetizar(tarea: str, resultados: list[dict], cliente, indicaciones: str = "") -> str:
    datos = "\n".join(f"- {r['paso']}: {r['resultado']}" for r in resultados)
    sistema = ("Redacta la respuesta final para el cliente de Lumen Shop, en español, breve y amable, "
               "usando solo los resultados obtenidos. " + indicaciones)
    return llamar(cliente, sistema, f"Tarea: {tarea}\nResultados:\n{datos}")


def plan_and_execute(tarea: str, cliente=None, verbose: bool = True) -> str:
    cliente = cliente or crear_cliente()
    pasos = planificar(tarea, cliente)
    if verbose:
        print("📋 Plan:\n" + "\n".join(f"  {i}. {p}" for i, p in enumerate(pasos, 1)))

    resultados = []
    for i, paso in enumerate(pasos, 1):
        resultado = ejecutar_paso(tarea, paso, resultados, cliente)
        resultados.append({"paso": paso, "resultado": resultado})
        if verbose:
            print(f"\n▶ Paso {i}: {paso}\n  {resultado}")

    return sintetizar(tarea, resultados, cliente)


if __name__ == "__main__":
    print("\n✅", plan_and_execute(sys.argv[1] if len(sys.argv) > 1 else input("Tarea: ")))
