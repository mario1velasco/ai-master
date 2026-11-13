"""Sesión 2 · Demo I: detectar alucinaciones comprobando la respuesta contra los datos.

Una alucinación es un dato que el agente afirma y que no viene de ninguna
herramienta. La forma más fiable de detectarla en un agente es mirar su
trayectoria: todo precio, cantidad, pedido o seguimiento que aparezca en la
respuesta tiene que estar en lo que devolvieron las herramientas.

El detector extrae esas afirmaciones con reglas y las busca en las
observaciones. Es barato, se puede ejecutar en todas las conversaciones y no
depende de otro modelo. Lo que no detecta (afirmaciones sin cifras) se deja a
un juez LLM o a la revisión humana.

Uso:
    python -m sesion2.alucinaciones                       # cuatro preguntas que suelen provocar invenciones
    python -m sesion2.alucinaciones "¿Cuánto cuesta el champú?"
"""
import re
import sys

from comun import tienda
from comun.agente import Agente, mostrar
from comun.herramientas import LECTURA

PATRONES = {
    "precio": r"\d+(?:[.,]\d{1,2})?\s?(?:€|euros?|eur\b|\$|dólares)",
    "cantidad": r"\d+\s(?:unidades|uds)",
    "pedido": r"ORD-\d+",
    "seguimiento": r"TRK-\d+",
    "plazo": r"\d+\s?(?:-|a)\s?\d+\s?(?:h\b|horas|días)|\d+\s(?:horas|días)",
}

PREGUNTAS_DEMO = [
    "¿Cuánto cuesta el serum de vitamina C?",            # control: debería salir limpia
    "¿Tenéis champú? ¿A qué precio?",                    # producto que no existe
    "¿Dónde está mi envío TRK-58873?",                   # el transportista falla: ¿se inventa la ubicación?
    "¿Qué me recomendáis para el sol y en cuánto me llega?",  # plazo de envío
]


def _numeros(texto: str) -> set[str]:
    """Todas las cifras del texto, normalizadas (24,90 → 24.9) para comparar sin falsos positivos."""
    return {str(float(n.replace(",", "."))).rstrip("0").rstrip(".") for n in re.findall(r"\d+(?:[.,]\d+)?", texto)}


def extraer_afirmaciones(respuesta: str) -> list[tuple[str, str]]:
    return [(tipo, m.group(0)) for tipo, patron in PATRONES.items()
            for m in re.finditer(patron, respuesta, flags=re.IGNORECASE)]


def detectar_alucinaciones(respuesta: str, observaciones: str) -> list[dict]:
    """Devuelve cada afirmación verificable con su veredicto: respaldada o sin respaldo."""
    datos = observaciones.upper()
    cifras_datos = _numeros(observaciones)
    informe = []
    for tipo, texto in extraer_afirmaciones(respuesta):
        if tipo in ("pedido", "seguimiento"):
            respaldada = texto.upper() in datos
        else:
            respaldada = _numeros(texto) <= cifras_datos
        informe.append({"tipo": tipo, "afirmacion": texto, "respaldada": respaldada})
    return informe


def analizar(pregunta: str, cliente=None, contexto=None, verbose: bool = True) -> list[dict]:
    tienda.reiniciar()
    resultado = Agente(cliente=cliente, herramientas=LECTURA, contexto=contexto).ejecutar(pregunta)
    informe = detectar_alucinaciones(resultado.respuesta, resultado.observaciones)
    if verbose:
        print(f"\n━━ {pregunta}")
        mostrar(resultado)
        if not informe:
            print("   🔎 Sin afirmaciones verificables (cifras, pedidos o plazos)")
        for a in informe:
            print(f"   {'✅ respaldada  ' if a['respaldada'] else '🚩 SIN RESPALDO'}  {a['tipo']:<11} «{a['afirmacion']}»")
    return informe


if __name__ == "__main__":
    for p in sys.argv[1:] or PREGUNTAS_DEMO:
        analizar(p)
