"""Sesión 2 · Demo I: ReAct prompting implementado a mano.

Así se construían los agentes antes del tool calling nativo, y así se siguen
construyendo con modelos que no lo soportan. El modelo escribe texto con un
formato fijo (Pensamiento / Acción / Entrada) y nuestro código lo interpreta,
ejecuta la herramienta y le devuelve la Observación.

Compáralo con sesion1/agente_minimo.py: el bucle es el mismo; lo que cambia es
quién estructura la llamada a la herramienta (nuestro parser o la API).

Uso:  python -m sesion2.react_prompting "Soy marta.lopez@email.com, ¿puedo repetir mi último pedido?"
"""
import json
import re
import sys

from comun.herramientas import FUNCIONES, HERRAMIENTAS
from comun.llm import MODELO, crear_cliente


def describir_herramientas() -> str:
    lineas = []
    for h in HERRAMIENTAS:
        f = h["function"]
        argumentos = {k: "..." for k in f["parameters"]["properties"]}
        lineas.append(f"- {f['name']}: {f['description']} Entrada: {json.dumps(argumentos)}")
    return "\n".join(lineas)


INSTRUCCIONES = f"""Eres el agente de atención al cliente de Lumen Shop. Nunca inventes datos.

Tienes estas herramientas:
{describir_herramientas()}

Responde SIEMPRE con este formato:
Pensamiento: qué necesitas averiguar y por qué
Acción: nombre exacto de una herramienta
Entrada: argumentos en JSON en una sola línea

El sistema te devolverá una línea «Observación:» con el resultado. Repite el ciclo
las veces que necesites. Cuando tengas toda la información, termina con:
Pensamiento: ya tengo lo necesario
Respuesta final: tu respuesta al cliente, en español"""

PATRON_FINAL = re.compile(r"Respuesta final:\s*(.+)", re.DOTALL)
PATRON_ACCION = re.compile(r"Acción:\s*(\w+)\s*\n\s*Entrada:\s*(\{.*?\})", re.DOTALL)


def ejecutar_react(pregunta: str, max_pasos: int = 8, cliente=None, verbose: bool = True) -> str:
    cliente = cliente or crear_cliente()
    mensajes = [{"role": "system", "content": INSTRUCCIONES}, {"role": "user", "content": pregunta}]

    for paso in range(1, max_pasos + 1):
        # ! stop: cortamos la generación antes de que el modelo se invente la Observación
        texto = cliente.chat.completions.create(
            model=MODELO, messages=mensajes, stop=["Observación:"]).choices[0].message.content or ""
        if verbose:
            print(f"\n--- Paso {paso} ---\n{texto.strip()}")
        mensajes.append({"role": "assistant", "content": texto})

        if final := PATRON_FINAL.search(texto):
            return final.group(1).strip()

        if accion := PATRON_ACCION.search(texto):
            nombre, argumentos = accion.groups()
            try:
                resultado = FUNCIONES[nombre](**json.loads(argumentos))
            except KeyError:
                resultado = {"error": f"La herramienta '{nombre}' no existe."}
            except Exception as e:
                resultado = {"error": f"{type(e).__name__}: {e}"}
            observacion = f"Observación: {json.dumps(resultado, ensure_ascii=False)}"
        else:  # el modelo no ha respetado el formato
            observacion = ("Observación: formato incorrecto. Usa «Acción:» y «Entrada:» "
                           "o termina con «Respuesta final:».")
        if verbose:
            print(observacion)
        mensajes.append({"role": "user", "content": observacion})

    return "No he podido completar la consulta en el límite de pasos."


if __name__ == "__main__":
    print("\n✅", ejecutar_react(sys.argv[1] if len(sys.argv) > 1 else input("Cliente: ")))
