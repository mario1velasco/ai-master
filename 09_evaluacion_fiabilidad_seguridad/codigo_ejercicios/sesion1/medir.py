"""Sesión 1 · Demo I: las métricas de un agente.

Ejecuta el agente sobre el conjunto de pruebas (sesion1/casos.json) varias
veces y calcula cuatro familias de métricas:

- Calidad:        ¿responde bien? (tasa de éxito, acierto de herramienta)
- Fiabilidad:     ¿responde bien SIEMPRE? (pass^k: los k intentos de un caso aciertan)
- Latencia:       ¿cuánto tarda? (mediana y percentil 95)
- Disponibilidad: ¿cuántas veces no puede responder? (errores técnicos y límite de pasos)
Y el coste: tokens y euros estimados por caso.

Uso:
    python -m sesion1.medir                         # cada caso 1 vez
    python -m sesion1.medir --repeticiones 3        # fiabilidad: pass^3
    python -m sesion1.medir --categoria adversario  # solo un tipo de casos
"""
import argparse
import json
import os
import statistics
from pathlib import Path

from comun import tienda
from comun.agente import Agente
from comun.evaluacion import evaluar_caso
from comun.herramientas import TODAS

RUTA_CASOS = Path(__file__).with_name("casos.json")
PRECIO_MILLON_TOKENS = float(os.getenv("PRECIO_MILLON_TOKENS", "0.5"))  # € por millón de tokens (orientativo)


def cargar_casos(categoria: str | None = None, ruta: Path = RUTA_CASOS) -> list[dict]:
    casos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return [c for c in casos if not categoria or c["categoria"] == categoria]


def percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, round(p / 100 * (len(ordenados) - 1)))] if ordenados else 0.0


def ejecutar_casos(casos: list[dict], repeticiones: int = 1, cliente=None, crear_agente=None, verbose: bool = True):
    """Devuelve una fila por intento: caso, repetición, comprobaciones y medidas."""
    crear_agente = crear_agente or (lambda caso: Agente(cliente=cliente, herramientas=TODAS,
                                                        contexto=caso.get("contexto")))
    filas = []
    for caso in casos:
        for rep in range(repeticiones):
            tienda.reiniciar()
            resultado = crear_agente(caso).ejecutar(caso["pregunta"])
            comprobacion = evaluar_caso(caso, resultado)
            filas.append({"id": caso["id"], "categoria": caso["categoria"], "repeticion": rep,
                          "comprobacion": comprobacion, "respuesta": resultado.respuesta,
                          "herramientas": resultado.herramientas, "segundos": resultado.segundos,
                          "tokens": resultado.tokens, "error": resultado.error, "limite": resultado.limite_alcanzado})
            if verbose:
                marca = "✅" if comprobacion["exito"] else "❌"
                fallos = [k for k, v in comprobacion.items() if not v and k != "exito"]
                print(f"  {marca} {caso['id']} #{rep + 1}  {resultado.segundos:5.1f} s  {resultado.tokens:5} tokens"
                      + (f"   falla: {', '.join(fallos)}" if fallos else ""))
    return filas


def calcular_metricas(filas: list[dict]) -> dict:
    n = len(filas)
    por_caso: dict[str, list[bool]] = {}
    for f in filas:
        por_caso.setdefault(f["id"], []).append(f["comprobacion"]["exito"])
    herramienta = [f["comprobacion"]["herramienta_correcta"] for f in filas if "herramienta_correcta" in f["comprobacion"]]
    tokens = sum(f["tokens"] for f in filas)
    return {
        "intentos": n,
        "tasa_exito": sum(f["comprobacion"]["exito"] for f in filas) / n,
        "pass_k": sum(all(v) for v in por_caso.values()) / len(por_caso),        # todos los intentos aciertan
        "pass_at_k": sum(any(v) for v in por_caso.values()) / len(por_caso),     # al menos uno acierta
        "acierto_herramienta": sum(herramienta) / len(herramienta) if herramienta else None,
        "latencia_p50": statistics.median(f["segundos"] for f in filas),
        "latencia_p95": percentil([f["segundos"] for f in filas], 95),
        "disponibilidad": 1 - sum(bool(f["error"]) or f["limite"] for f in filas) / n,
        "tokens_medios": tokens / n,
        "coste_por_caso": tokens / n * PRECIO_MILLON_TOKENS / 1_000_000,
    }


def imprimir_metricas(m: dict, k: int) -> None:
    pct = lambda x: "—" if x is None else f"{x:.0%}"
    print(f"\n📊 {m['intentos']} intentos")
    print(f"   Calidad         tasa de éxito {pct(m['tasa_exito'])} · acierto de herramienta {pct(m['acierto_herramienta'])}")
    print(f"   Fiabilidad      pass^{k} {pct(m['pass_k'])} · pass@{k} {pct(m['pass_at_k'])}")
    print(f"   Latencia        mediana {m['latencia_p50']:.1f} s · p95 {m['latencia_p95']:.1f} s")
    print(f"   Disponibilidad  {pct(m['disponibilidad'])}")
    print(f"   Coste           {m['tokens_medios']:.0f} tokens/caso · {m['coste_por_caso'] * 1000:.3f} € por 1.000 casos")


def por_categoria(filas: list[dict]) -> None:
    print("\n   Por categoría:")
    for cat in dict.fromkeys(f["categoria"] for f in filas):
        sub = [f for f in filas if f["categoria"] == cat]
        print(f"   · {cat:<11} {sum(f['comprobacion']['exito'] for f in sub)}/{len(sub)} aciertos")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Métricas del agente de Lumen Shop")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--categoria", choices=["normal", "borde", "adversario"])
    args = parser.parse_args()
    casos = cargar_casos(args.categoria)
    print(f"🧪 {len(casos)} casos × {args.repeticiones} repeticiones")
    filas = ejecutar_casos(casos, args.repeticiones)
    metricas = calcular_metricas(filas)
    imprimir_metricas(metricas, args.repeticiones)
    por_categoria(filas)
    Path("datos").mkdir(exist_ok=True)
    Path("datos/metricas_sesion1.json").write_text(json.dumps({"metricas": metricas, "filas": filas},
                                                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n💾 Detalle guardado en datos/metricas_sesion1.json")
