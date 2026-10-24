"""Sesión 1 · Demo II: la misma tarea como workflow, sin agente.

Aquí el código decide los pasos y el modelo solo hace dos cosas concretas:
extraer el email y redactar la respuesta. Siempre son dos llamadas al modelo,
siempre en el mismo orden. Es más predecible, más barato y más fácil de
auditar, pero solo sabe resolver esta tarea.

Uso:  python -m sesion1.workflow_equivalente "Hola, soy marta.lopez@email.com, ¿cómo van mis pedidos?"
"""
import json
import sys

from comun import tienda
from comun.llm import MODELO, crear_cliente


def preguntar(cliente, instruccion: str, texto: str) -> str:
    respuesta = cliente.chat.completions.create(
        model=MODELO, messages=[{"role": "system", "content": instruccion}, {"role": "user", "content": texto}])
    return respuesta.choices[0].message.content.strip()


def estado_de_pedidos(mensaje_cliente: str, cliente=None) -> str:
    cliente = cliente or crear_cliente()

    # Paso 1 · El modelo extrae un dato concreto
    email = preguntar(cliente, "Extrae el email del mensaje. Responde solo con el email o con NINGUNO.",
                      mensaje_cliente)
    if email == "NINGUNO":
        return "Para consultar tus pedidos necesito el email con el que compraste."

    # Paso 2 · El código consulta los sistemas, siempre igual
    ficha = tienda.buscar_cliente(email)
    if "error" in ficha:
        return f"No encuentro ningún cliente con el email {email}. ¿Puedes comprobarlo?"
    pedidos = [tienda.obtener_pedido(p) for p in ficha["pedidos"]]

    # Paso 3 · El modelo redacta con los datos ya obtenidos
    datos = json.dumps({"cliente": ficha["nombre"], "pedidos": pedidos}, ensure_ascii=False)
    return preguntar(cliente, "Redacta una respuesta breve y amable en español para el cliente de "
                     "Lumen Shop usando solo estos datos.", datos)


if __name__ == "__main__":
    print(estado_de_pedidos(sys.argv[1] if len(sys.argv) > 1 else input("Cliente: ")))
