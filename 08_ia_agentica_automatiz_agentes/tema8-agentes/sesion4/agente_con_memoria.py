"""Sesión 4 · Demo I: un agente que recuerda a cada cliente entre conversaciones.

Uso, en dos «días» distintos:
  python -m sesion4.agente_con_memoria marta.lopez@email.com "Hola, tengo la piel muy sensible y me salen rojeces con algunos productos. ¿Qué tal es el sérum?"
  python -m sesion4.agente_con_memoria marta.lopez@email.com "¿Qué me recomendáis para el sol este verano?"
  python -m sesion4.agente_con_memoria marta.lopez@email.com --olvidar
"""
import argparse

from comun.grafo import construir_agente
from comun.herramientas_lc import LECTURA
from comun.modelo_lc import crear_modelo
from sesion4.memoria import MemoriaClientes

INSTRUCCIONES = ("Eres el agente de atención al cliente de Lumen Shop. Usa las herramientas y no inventes datos. "
                 "Responde en español, breve y amable.")


def atender(email: str, mensaje: str, memoria: MemoriaClientes, modelo=None) -> str:
    # 1. Leer: recuperamos lo relevante para ESTE mensaje, no todo lo que sabemos
    recuerdos = memoria.recuperar(email, mensaje)
    contexto = "\n".join(f"- {r}" for r in recuerdos) or "- (primera conversación con este cliente)"
    print("🧠 Recuerdos recuperados:\n" + contexto)
    instrucciones = f"{INSTRUCCIONES}\n\nCliente: {email}\nLo que sabemos de conversaciones anteriores:\n{contexto}"

    agente = construir_agente(modelo or crear_modelo(), LECTURA, instrucciones)
    respuesta = agente.invoke({"messages": [("user", mensaje)]})["messages"][-1].content

    # 2. Escribir: al terminar, decidimos qué merece recordarse
    nuevas = memoria.recordar_conversacion(email, f"Cliente: {mensaje}\nAgente: {respuesta}")
    print("💾 Memorias guardadas:", [m["texto"] for m in nuevas] or "ninguna")
    return respuesta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("mensaje", nargs="?")
    parser.add_argument("--olvidar", action="store_true", help="Borra todo lo que se recuerda del cliente")
    args = parser.parse_args()
    memoria = MemoriaClientes()
    if args.olvidar:
        print(f"🗑  {memoria.olvidar(args.email)} memorias borradas de {args.email}")
    else:
        print("🤖", atender(args.email, args.mensaje or input("Cliente: "), memoria))
