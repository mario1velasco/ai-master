"""Sesión 2 · Demo II (continuación): reflexión.

El agente genera un borrador, un crítico lo revisa contra unos criterios
explícitos y, si no lo aprueba, el agente lo rehace con esas observaciones.
Funciona mejor cuanto más concretos son los criterios: un crítico que solo
«opina» aporta poco.

Uso:  python -m sesion2.reflexion "Quiero comprar 10 protectores solares, ¿me los enviáis?"
"""
import sys

from comun.herramientas import FUNCIONES, HERRAMIENTAS
from comun.llm import MODELO, crear_cliente
from comun.utilidades import extraer_json
from sesion1.agente_minimo import ejecutar_agente

CRITERIOS = [
    "Responde a todo lo que pregunta el cliente.",
    "Si un producto no tiene stock suficiente, lo dice claramente y ofrece una alternativa.",
    "No promete plazos, descuentos ni acciones que no puede garantizar.",
    "Es breve (máximo 5 frases) y amable.",
]

CRITICO = (
    "Eres revisor de calidad de atención al cliente en Lumen Shop. Evalúa la respuesta según estos criterios:\n"
    + "\n".join(f"- {c}" for c in CRITERIOS)
    + '\nResponde solo con JSON: {"aprobado": true/false, "comentarios": "qué hay que corregir"}'
)


def criticar(pregunta: str, respuesta: str, cliente) -> dict:
    texto = cliente.chat.completions.create(model=MODELO, messages=[
        {"role": "system", "content": CRITICO},
        {"role": "user", "content": f"Pregunta del cliente: {pregunta}\n\nRespuesta propuesta: {respuesta}"},
    ]).choices[0].message.content
    return extraer_json(texto)


def responder_con_reflexion(pregunta: str, max_rondas: int = 2, cliente=None, verbose: bool = True) -> str:
    cliente = cliente or crear_cliente()
    respuesta = ejecutar_agente(pregunta, cliente=cliente, herramientas=HERRAMIENTAS,
                                funciones=FUNCIONES, verbose=False)
    for ronda in range(1, max_rondas + 1):
        revision = criticar(pregunta, respuesta, cliente)
        if verbose:
            print(f"\n📝 Borrador {ronda}: {respuesta}\n🔍 Crítica: {revision}")
        if revision.get("aprobado"):
            return respuesta
        respuesta = ejecutar_agente(
            f"{pregunta}\n\nTu respuesta anterior fue: «{respuesta}»\n"
            f"El revisor indica: {revision.get('comentarios')}\nRedacta una respuesta corregida.",
            cliente=cliente, herramientas=HERRAMIENTAS, funciones=FUNCIONES, verbose=False)
    return respuesta


if __name__ == "__main__":
    print("\n✅", responder_con_reflexion(sys.argv[1] if len(sys.argv) > 1 else input("Cliente: ")))
