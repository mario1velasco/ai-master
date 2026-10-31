"""RAG · examen: ¿encuentra las fuentes correctas? ¿Responde bien y cita bien?

Mismo método que el bloque I: preguntas con su respuesta preparada a mano
(practica/sesion_2/examen/examen_rag.json). Cada pregunta dice qué fuente debería
aparecer y qué hechos debe contener la respuesta.

  --parte recuperacion   ¿Está la fuente esperada entre los k primeros fragmentos?
                         Compara modelos de embeddings y modos de búsqueda (rápido, sin LLM).
  --parte respuesta      Pregunta de verdad (13_preguntar_documentos.py) y puntúa:
                         hechos correctos, cita de una fuente esperada y verificación.

Uso:
  python practica/sesion_2/14_evaluar_rag.py                              # recuperación: todos los modelos y modos
  python practica/sesion_2/14_evaluar_rag.py --parte respuesta            # respuestas con el modelo por defecto
  python practica/sesion_2/14_evaluar_rag.py --parte respuesta --llm qwen3:4b-instruct
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from importlib import import_module
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
indice = import_module("11_indice")
buscar = import_module("12_buscar")

EXAMEN = AQUI / "examen" / "examen_rag.json"
MODELOS = ["bge-m3", "qwen3-embedding:0.6b", "embeddinggemma", "nomic-embed-text"]
MODOS = ["semantica", "palabras", "hibrida"]
NEGACIONES = ["no consta", "no se dispone", "no hay", "no se puede", "no existe", "no disponible", "no contiene",
              "no incluye", "no aparece", "no se registra", "no se indica", "no se especifica", "no se menciona",
              "no se proporciona", "no tenemos", "no figura", "no se sabe", "no permite", "no se incluye"]


def coincide(frag: dict, patron: str) -> bool:
    """«archivo» o «archivo#página»."""
    if "#" in patron:
        archivo, pag = patron.split("#")
        return frag["fuente"] == archivo and str(frag["pagina"]) == pag
    return frag["fuente"] == patron


def posicion(frags: list[dict], patrones: list[str]) -> int | None:
    for n, f in enumerate(frags, 1):
        if any(coincide(f, p) for p in patrones):
            return n
    return None


def evaluar_recuperacion(k: int = 5) -> list[dict]:
    preguntas = json.loads(EXAMEN.read_text(encoding="utf-8"))
    filas = []
    for modelo in MODELOS:
        if not indice.ruta_indice(modelo).exists():
            print(f"(sin índice de {modelo}: se omite)")
            continue
        b = buscar.Buscador(modelo)
        for modo in MODOS:
            t0 = time.time()
            pos = {p["id"]: posicion(b.buscar(p["pregunta"], modo, k, vigentes=False), p["fuentes"]) for p in preguntas}
            aciertos = sum(1 for v in pos.values() if v)
            mrr = sum(1 / v for v in pos.values() if v) / len(pos)
            filas.append({"modelo": modelo, "modo": modo, "aciertos": aciertos, "total": len(pos), "mrr": round(mrr, 3),
                          "fallos": [i for i, v in pos.items() if not v], "posiciones": pos,
                          "ms_por_pregunta": round((time.time() - t0) / len(pos) * 1000)})
    return filas


def hechos_ok(p: dict, texto: str) -> tuple[bool, list]:
    t = buscar.normalizar(texto)
    if p.get("debe_negar"):
        ok = any(n in t for n in NEGACIONES)
        return ok, [] if ok else ["no dice que no consta"]
    faltan = [g[0] for g in p["hechos"] if not any(buscar.normalizar(o) in t for o in g)]
    return not faltan, faltan


def evaluar_respuestas(llm: str, modelo_emb: str, modo: str, k: int) -> list[dict]:
    rag = import_module("13_preguntar_documentos")
    preguntas = json.loads(EXAMEN.read_text(encoding="utf-8"))
    b = buscar.Buscador(modelo_emb)
    filas = []
    for p in preguntas:
        r = rag.preguntar(p["pregunta"], b, llm=llm, modo=modo, k=k)
        ok, faltan = hechos_ok(p, r["respuesta"])
        cita_ok = any(any(coincide(f, pat) for pat in p["fuentes"]) for f in r["citados"])
        filas.append({"id": p["id"], "hechos": ok, "faltan": faltan, "cita_esperada": cita_ok,
                      "verificacion_ok": not r["avisos"], "avisos": r["avisos"], "segundos": r["segundos"],
                      "respuesta": r["respuesta"], "citados": [f["cita"] for f in r["citados"]]})
        print(f"  {p['id']} hechos {'✓' if ok else '✗'} · cita {'✓' if cita_ok else '✗'} · "
              f"verificación {'✓' if not r['avisos'] else '⚠ ' + '; '.join(r['avisos'])[:90]} · {r['segundos']} s"
              + (f" · faltan {faltan}" if faltan else ""))
    return filas


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG · examen de recuperación y de respuesta.")
    ap.add_argument("--parte", choices=["recuperacion", "respuesta"], default="recuperacion")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--llm", default="qwen3:30b-a3b-instruct-2507-q4_K_M")
    ap.add_argument("--modelo", default=indice.MODELO, help="Modelo de embeddings (parte respuesta).")
    ap.add_argument("--modo", default="hibrida")
    ap.add_argument("--guardar", type=Path, help="Guardar el detalle en JSON.")
    a = ap.parse_args()
    if a.parte == "recuperacion":
        filas = evaluar_recuperacion(a.k)
        print(f"\n¿Está la fuente esperada entre los {a.k} primeros? (16 preguntas)\n")
        print(f"{'modelo':24}{'modo':11}{'aciertos':>10}{'MRR':>7}{'ms':>6}  fallos")
        for f in filas:
            print(f"{f['modelo']:24}{f['modo']:11}{f['aciertos']:>6}/{f['total']:<3}{f['mrr']:>7}{f['ms_por_pregunta']:>6}  "
                  + " ".join(f["fallos"]))
    else:
        print(f"Respuestas: {a.llm} · embeddings {a.modelo} · búsqueda {a.modo} · k={a.k}")
        filas = evaluar_respuestas(a.llm, a.modelo, a.modo, a.k)
        n = len(filas)
        print(f"\nHechos correctos {sum(f['hechos'] for f in filas)}/{n} · cita una fuente esperada "
              f"{sum(f['cita_esperada'] for f in filas)}/{n} · verificación limpia {sum(f['verificacion_ok'] for f in filas)}/{n}"
              f" · {sum(f['segundos'] for f in filas) / n:.0f} s por pregunta")
    if a.guardar:
        a.guardar.write_text(json.dumps(filas, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
