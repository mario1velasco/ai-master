"""Sesión 1 · Demo: un agente desde cero, sin frameworks.

Un agente es un bucle: el modelo decide si llama a una herramienta o responde.
Si llama a una herramienta, la ejecutamos, le devolvemos el resultado y vuelve
a decidir. Todo lo demás (frameworks, memoria, multiagente) se construye sobre
esta idea.

Uso:
    python -m sesion1.agente_minimo "¿Hay stock de crema hidratante?"
    python -m sesion1.agente_minimo --max-iter 30 "¿Dónde está el envío TRK-58873?"
"""
import argparse
import json

from comun import tienda
from comun.llm import MODELO, crear_cliente

INSTRUCCIONES = (
    "Eres el agente de atención al cliente de Lumen Shop, una tienda online de cosmética. "
    "Usa las herramientas para consultar datos; nunca inventes stock, pedidos ni clientes. "
    "Responde en español, de forma breve y amable."
)

# 1. Herramientas: lo que el modelo ve (esquema) y lo que ejecutamos (función)
HERRAMIENTAS = [
    {"type": "function", "function": {
        "name": "consultar_stock",
        "description": "Devuelve precio y unidades disponibles de un producto del catálogo.",
        "parameters": {"type": "object", "properties": {
            "producto": {"type": "string", "description": "Nombre del producto, p. ej. 'serum vitamina c'"}},
            "required": ["producto"]}}},
    {"type": "function", "function": {
        "name": "buscar_cliente",
        "description": "Busca un cliente por su email y devuelve su nombre y sus pedidos.",
        "parameters": {"type": "object", "properties": {
            "email": {"type": "string"}}, "required": ["email"]}}},
    {"type": "function", "function": {
        "name": "consultar_transportista",
        "description": "Consulta la ubicación de un envío a partir de su número de seguimiento.",
        "parameters": {"type": "object", "properties": {
            "numero_seguimiento": {"type": "string"}}, "required": ["numero_seguimiento"]}}},
]
FUNCIONES = {
    "consultar_stock": tienda.consultar_stock,
    "buscar_cliente": tienda.buscar_cliente,
    "consultar_transportista": tienda.consultar_transportista,
}


def ejecutar_herramienta(nombre: str, argumentos: str, funciones: dict) -> str:
    try:
        resultado = funciones[nombre](**json.loads(argumentos or "{}"))
    except Exception as e:  # el error vuelve al modelo para que decida qué hacer
        resultado = {"error": f"{type(e).__name__}: {e}"}
    return json.dumps(resultado, ensure_ascii=False)


# 2. El bucle agéntico
def ejecutar_agente(pregunta: str, max_iteraciones: int = 8, cliente=None,
                    herramientas=None, funciones=None, verbose: bool = True) -> str:
    cliente = cliente or crear_cliente()
    herramientas = herramientas or HERRAMIENTAS
    funciones = funciones or FUNCIONES
    mensajes = [{"role": "system", "content": INSTRUCCIONES},
                {"role": "user", "content": pregunta}]
    tokens = 0

    for paso in range(1, max_iteraciones + 1):
        respuesta = cliente.chat.completions.create(model=MODELO, messages=mensajes, tools=herramientas)
        mensaje = respuesta.choices[0].message
        tokens += getattr(respuesta.usage, "total_tokens", 0) or 0

        if not mensaje.tool_calls:  # el modelo no pide herramientas → respuesta final
            if verbose:
                print(f"\n✅ Respuesta final (paso {paso}, {tokens} tokens)")
            return mensaje.content

        mensajes.append({"role": "assistant", "content": mensaje.content or "",
                         "tool_calls": [llamada.model_dump() for llamada in mensaje.tool_calls]})
        for llamada in mensaje.tool_calls:
            resultado = ejecutar_herramienta(llamada.function.name, llamada.function.arguments, funciones)
            if verbose:
                print(f"\n[Paso {paso}] 🔧 {llamada.function.name}({llamada.function.arguments})")
                print(f"          👁  {resultado}")
            mensajes.append({"role": "tool", "tool_call_id": llamada.id, "content": resultado})

    if verbose:
        print(f"\n⛔ Límite de {max_iteraciones} pasos alcanzado ({tokens} tokens consumidos)")
    return "No he podido completar la consulta. Te paso con un compañero del equipo."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agente mínimo de Lumen Shop")
    parser.add_argument("pregunta", nargs="?", help="Consulta del cliente")
    parser.add_argument("--max-iter", type=int, default=8, help="Límite de pasos del bucle")
    args = parser.parse_args()
    print(ejecutar_agente(args.pregunta or input("Cliente: "), max_iteraciones=args.max_iter))
