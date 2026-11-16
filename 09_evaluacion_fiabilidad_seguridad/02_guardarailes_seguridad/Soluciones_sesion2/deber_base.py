"""Solución · Deber base de la sesión 2: un guardarraíl de salida contra datos inventados.

Aprovecha el detector de la demo de alucinaciones: si la respuesta contiene un
precio, una cantidad, un pedido o un plazo que no aparece en lo que devolvieron
las herramientas, no se envía al cliente. En su lugar sale una respuesta segura
y queda registrado para revisión.

Uso:  python -m soluciones.sesion2.deber_base "¿Tenéis champú? ¿A qué precio?"
"""
import sys

from comun import tienda
from comun.agente import Agente, mostrar
from comun.herramientas import LECTURA
from sesion2.alucinaciones import detectar_alucinaciones
from sesion2.guardarrailes import Guardarrailes

RESPUESTA_SEGURA = ("Prefiero no darte un dato que no tengo confirmado. Te paso con un compañero del equipo "
                    "para que te lo confirme.")


class GuardarrailesSinInventar(Guardarrailes):
    def revisar_salida(self, texto: str, contexto: dict, observaciones: str = ""):
        texto, motivo = super().revisar_salida(texto, contexto, observaciones)
        if motivo:
            return texto, motivo
        sin_respaldo = [a["afirmacion"] for a in detectar_alucinaciones(texto, observaciones) if not a["respaldada"]]
        if sin_respaldo:
            return RESPUESTA_SEGURA, self._anotar("salida", f"datos sin respaldo: {', '.join(sin_respaldo)}")
        return texto, None


if __name__ == "__main__":
    tienda.reiniciar()
    pregunta = sys.argv[1] if len(sys.argv) > 1 else "¿Tenéis champú? ¿A qué precio?"
    mostrar(Agente(herramientas=LECTURA, guardas=GuardarrailesSinInventar()).ejecutar(pregunta))
