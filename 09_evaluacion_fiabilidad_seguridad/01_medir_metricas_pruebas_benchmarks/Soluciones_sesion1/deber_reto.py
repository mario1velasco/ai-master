"""Solución · Reto de la sesión 1: calibrar el juez LLM con etiquetas humanas.

Un juez LLM también se equivoca. Antes de fiarse de él, se compara con un
pequeño conjunto etiquetado por personas (sesion1/etiquetas_humanas.json) y
se calcula:
- acuerdo: porcentaje de veces que el juez coincide con la persona.
- falsos positivos: respuestas MALAS que el juez aprueba. Es el error más
  peligroso, porque deja pasar fallos a producción.
- falsos negativos: respuestas buenas que el juez rechaza (falsas alarmas).

Uso:  python -m soluciones.sesion1.deber_reto
"""
import json
from pathlib import Path
from types import SimpleNamespace

from sesion1.evaluar import juez_llm

RUTA = Path(__file__).resolve().parents[2] / "sesion1" / "etiquetas_humanas.json"


def calibrar(etiquetas: list[dict], cliente=None, verbose: bool = True) -> dict:
    vp = vn = fp = fn = 0
    for e in etiquetas:
        resultado = SimpleNamespace(respuesta=e["respuesta"], observaciones=e["observaciones"])
        veredicto = juez_llm(e["pregunta"], resultado, cliente)
        aprueba = "error" not in veredicto and all(veredicto.values())
        if aprueba and e["correcta"]:
            vp += 1
        elif not aprueba and not e["correcta"]:
            vn += 1
        elif aprueba:
            fp += 1
        else:
            fn += 1
        if verbose:
            marca = "✅" if aprueba == e["correcta"] else "❌"
            print(f"  {marca} humano: {'buena' if e['correcta'] else 'mala ':<5} · juez: {'aprueba ' if aprueba else 'rechaza'} · {e['respuesta'][:60]}")
    n = len(etiquetas)
    return {"acuerdo": (vp + vn) / n, "falsos_positivos": fp, "falsos_negativos": fn,
            "tasa_falsos_positivos": fp / max(1, fp + vn)}


if __name__ == "__main__":
    m = calibrar(json.loads(RUTA.read_text(encoding="utf-8")))
    print(f"\n⚖️  Acuerdo con las personas: {m['acuerdo']:.0%}")
    print(f"   Respuestas malas que el juez aprueba: {m['falsos_positivos']} ({m['tasa_falsos_positivos']:.0%} de las malas)")
    print(f"   Respuestas buenas que el juez rechaza: {m['falsos_negativos']}")
