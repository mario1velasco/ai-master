"""Mide el asistente sobre un conjunto de casos de prueba.

Uso:
  python -m pruebas.medir                                  # casos_base.json, 1 repetición
  python -m pruebas.medir --casos pruebas/mis_casos.json --repeticiones 3
  python -m pruebas.medir --casos pruebas/mis_casos.json --categoria adversario
  python -m pruebas.medir --casos pruebas/mis_casos.json --repeticiones 3 --guardar antes

El agente se crea con `albor/configuracion.py`, así que mide lo que esté configurado
en ese momento. Con --guardar, el detalle de cada intento queda en resultados/<nombre>.json.

Campos de un caso (todos opcionales salvo id, categoria y pregunta):
  id, categoria (normal | borde | adversario | regresion), pregunta,
  contexto                  {"email": "..."}: el huésped identificado en la web
  debe_contener             lista de variantes; basta con que aparezca una
  no_debe_contener          lista de textos que no pueden aparecer
  herramientas_esperadas    herramientas que debe usar
  herramientas_prohibidas   herramientas que no debe usar
  sin_efectos               true: no puede cancelar, reembolsar ni enviar emails
  sin_reembolsos            true: puede cancelar, pero no puede emitir ningún reembolso
  max_pasos                 máximo de llamadas al modelo
"""
import argparse
import json
import os
import statistics
import unicodedata
from pathlib import Path

from albor import hotel
from albor.configuracion import crear_agente

PRECIO_MILLON_TOKENS = float(os.getenv("PRECIO_MILLON_TOKENS", "0.5"))


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    return " ".join("".join(c for c in texto if unicodedata.category(c) != "Mn").split())


def contiene_alguno(texto: str, variantes: list[str]) -> bool:
    t = normalizar(texto).replace(" ", "")
    return any(normalizar(v).replace(" ", "") in t for v in variantes)


def comprobar(caso: dict, r) -> dict:
    c = {}
    if caso.get("debe_contener"):
        c["dato_correcto"] = contiene_alguno(r.respuesta, caso["debe_contener"])
    if caso.get("no_debe_contener"):
        c["sin_contenido_prohibido"] = not contiene_alguno(r.respuesta, caso["no_debe_contener"])
    if caso.get("herramientas_esperadas"):
        c["herramienta_correcta"] = all(h in r.herramientas for h in caso["herramientas_esperadas"])
    if caso.get("herramientas_prohibidas"):
        c["sin_herramientas_prohibidas"] = not any(h in r.herramientas for h in caso["herramientas_prohibidas"])
    if caso.get("sin_efectos"):
        c["sin_efectos"] = not (hotel.CANCELACIONES or hotel.REEMBOLSOS or hotel.BANDEJA_SALIDA)
    if caso.get("sin_reembolsos"):
        c["sin_reembolsos"] = not hotel.REEMBOLSOS
    if caso.get("max_pasos"):
        c["pasos_razonables"] = r.llamadas_modelo <= caso["max_pasos"]
    c["sin_error_tecnico"] = r.error is None and not r.limite_alcanzado
    c["exito"] = all(c.values())
    return c


def percentil(valores: list[float], p: float) -> float:
    v = sorted(valores)
    return v[min(len(v) - 1, round(p / 100 * (len(v) - 1)))] if v else 0.0


def ejecutar(casos: list[dict], repeticiones: int, cliente=None) -> list[dict]:
    filas = []
    for caso in casos:
        for rep in range(repeticiones):
            hotel.reiniciar()
            r = crear_agente(caso.get("contexto"), cliente=cliente).ejecutar(caso["pregunta"])
            c = comprobar(caso, r)
            filas.append({"id": caso["id"], "categoria": caso["categoria"], "repeticion": rep, "comprobacion": c,
                          "respuesta": r.respuesta, "herramientas": r.herramientas,
                          "bloqueos": [p.resultado for p in r.pasos if p.tipo == "bloqueo"],
                          "pendientes_aprobacion": r.pendientes_aprobacion,
                          "efectos": {"cancelaciones": list(hotel.CANCELACIONES), "reembolsos": list(hotel.REEMBOLSOS),
                                      "emails": list(hotel.BANDEJA_SALIDA)},
                          "segundos": r.segundos, "tokens": r.tokens, "error": r.error, "limite": r.limite_alcanzado})
            fallos = [k for k, v in c.items() if not v and k != "exito"]
            print(f"  {'✅' if c['exito'] else '❌'} {caso['id']:<4} #{rep + 1}  {r.segundos:5.1f} s  {r.tokens:5} tokens"
                  + (f"   falla: {', '.join(fallos)}" if fallos else ""))
    return filas


def metricas(filas: list[dict]) -> dict:
    n, por_caso = len(filas), {}
    for f in filas:
        por_caso.setdefault(f["id"], []).append(f["comprobacion"]["exito"])
    herr = [f["comprobacion"]["herramienta_correcta"] for f in filas if "herramienta_correcta" in f["comprobacion"]]
    tokens = sum(f["tokens"] for f in filas)
    return {"intentos": n, "tasa_exito": sum(f["comprobacion"]["exito"] for f in filas) / n,
            "pass_k": sum(all(v) for v in por_caso.values()) / len(por_caso),
            "pass_at_k": sum(any(v) for v in por_caso.values()) / len(por_caso),
            "acierto_herramienta": sum(herr) / len(herr) if herr else None,
            "latencia_p50": statistics.median(f["segundos"] for f in filas),
            "latencia_p95": percentil([f["segundos"] for f in filas], 95),
            "disponibilidad": 1 - sum(bool(f["error"]) or f["limite"] for f in filas) / n,
            "tokens_medios": tokens / n, "coste_1000_casos": tokens / n * PRECIO_MILLON_TOKENS / 1000}


def imprimir(m: dict, filas: list[dict], k: int) -> None:
    pct = lambda x: "—" if x is None else f"{x:.0%}"
    print(f"\n📊 {m['intentos']} intentos")
    print(f"   Calidad         tasa de éxito {pct(m['tasa_exito'])} · acierto de herramienta {pct(m['acierto_herramienta'])}")
    print(f"   Fiabilidad      pass^{k} {pct(m['pass_k'])} · pass@{k} {pct(m['pass_at_k'])}")
    print(f"   Latencia        mediana {m['latencia_p50']:.1f} s · p95 {m['latencia_p95']:.1f} s")
    print(f"   Disponibilidad  {pct(m['disponibilidad'])}")
    print(f"   Coste           {m['tokens_medios']:.0f} tokens/intento · {m['coste_1000_casos']:.3f} € por 1.000 intentos")
    print("\n   Por categoría:")
    for cat in dict.fromkeys(f["categoria"] for f in filas):
        sub = [f for f in filas if f["categoria"] == cat]
        print(f"   · {cat:<11} {sum(f['comprobacion']['exito'] for f in sub)}/{len(sub)} aciertos")
    efectos = [f for f in filas if any(f["efectos"].values())]
    if efectos:
        print("\n   ⚠️  Intentos con efectos (cancelaciones, reembolsos o emails):")
        for f in efectos:
            print(f"   · {f['id']} #{f['repeticion'] + 1}: {json.dumps(f['efectos'], ensure_ascii=False)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mide el asistente de Hoteles Albor")
    parser.add_argument("--casos", default="pruebas/casos_base.json")
    parser.add_argument("--repeticiones", type=int, default=1)
    parser.add_argument("--categoria", choices=["normal", "borde", "adversario", "regresion"])
    parser.add_argument("--guardar", help="Nombre del fichero de resultados, p. ej. antes o despues")
    args = parser.parse_args()
    casos = [c for c in json.loads(Path(args.casos).read_text(encoding="utf-8"))
             if not args.categoria or c["categoria"] == args.categoria]
    print(f"🧪 {len(casos)} casos × {args.repeticiones} repeticiones")
    filas = ejecutar(casos, args.repeticiones)
    m = metricas(filas)
    imprimir(m, filas, args.repeticiones)
    if args.guardar:
        Path("resultados").mkdir(exist_ok=True)
        ruta = Path("resultados") / f"{args.guardar}.json"
        ruta.write_text(json.dumps({"metricas": m, "filas": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n💾 Detalle guardado en {ruta}")
