"""Revisión manual de las configuraciones finalistas del barrido de chunks.

Las métricas de chunks.py son automáticas y aproximadas; aquí se exportan las
respuestas finalistas para revisarlas a mano (0/1/NA) igual que en la sección 6.
"""
import csv
import json
from pathlib import Path

FINALISTAS = [(900, 150, 2), (900, 150, 4), (500, 150, 2), (1200, 150, 4)]
SALIDA = Path(__file__).parent / "resultados"
CAMPOS = ["tamaño", "solap", "k", "id", "tipo", "hit_pagina", "respaldo",
          "citas", "abstencion", "observaciones"]
METRICAS = ("hit_pagina", "respaldo", "citas", "abstencion")


def _seleccion(detalle, finalistas):
    """Registros de las finalistas, con tamaño y solapamiento añadidos."""
    filas = []
    for tamaño, solap, k in finalistas:
        for r in detalle[(tamaño, solap)]:
            if r["k"] == k:
                filas.append({"tamaño": tamaño, "solap": solap, **r})
    return filas


def exportar_revision(detalle, finalistas=FINALISTAS, salida=SALIDA):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    registros = _seleccion(detalle, finalistas)
    (salida / "resultados_chunks.json").write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    revision = salida / "revision_chunks.csv"
    if revision.exists():
        print(f"{revision} ya existe y se conserva. Si cambiaste resultados, "
              "guarda copia, bórralo y vuelve a revisar.")
        return registros
    with revision.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        writer.writeheader()
        for r in registros:
            respondible = r["tipo"] == "respondible"
            writer.writerow({
                "tamaño": r["tamaño"], "solap": r["solap"], "k": r["k"],
                "id": r["id"], "tipo": r["tipo"],
                "hit_pagina": "NA" if r["hit_pagina"] is None else r["hit_pagina"],
                "respaldo": "" if respondible else "NA",
                "citas": "" if respondible else "NA",
                "abstencion": "NA" if respondible else "",
                "observaciones": r["error_tecnico"]})
    print(f"Creados {salida / 'resultados_chunks.json'} y {revision} "
          f"({len(registros)} filas por revisar)")
    return registros


def mostrar_revision(detalle, finalistas=FINALISTAS, recorte=300):
    """Imprime cada caso para leer fragmentos y respuesta antes de anotar."""
    # Agrupado por pregunta para comparar las finalistas una tras otra.
    registros = _seleccion(detalle, finalistas)
    ids = list(dict.fromkeys(r["id"] for r in registros))
    for r in sorted(registros, key=lambda r: ids.index(r["id"])):
        if r is next(x for x in registros if x["id"] == r["id"]):
            print("=" * 80)
            print(f"{r['id']} ({r['tipo']}): {r['pregunta']}")
        print("-" * 80)
        print(f"{r['tamaño']}/{r['solap']} k={r['k']}")
        for chunk, pagina, score, texto in zip(r["chunks"], r["paginas"],
                                               r["scores"], r["textos"]):
            texto = " ".join(texto.split())
            print(f"  · {chunk} p.{pagina} ({score:.2f}): {texto[:recorte]}"
                  f"{'…' if len(texto) > recorte else ''}")
        print(f"  RESPUESTA: {r['respuesta'] or '(sin generar)'}")
        print(f"  auto → hit={r['hit_pagina']} evidencia={r['evidencia']} "
              f"citas_validas={r['citas_validas']} abstencion={r['abstencion']}"
              f"{' error=' + r['error_tecnico'] if r['error_tecnico'] else ''}")


def resumen_revision_chunks(ruta=SALIDA / "revision_chunks.csv"):
    """Métricas manuales por configuración: n/N = x.xx (NA y vacíos no cuentan)."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    configs = sorted({(int(f["tamaño"]), int(f["solap"]), int(f["k"])) for f in filas})
    print(f"{'config':>14}  " + "  ".join(f"{m:>16}" for m in METRICAS))
    for t, s, k in configs:
        grupo = [f for f in filas
                 if (int(f["tamaño"]), int(f["solap"]), int(f["k"])) == (t, s, k)]
        celdas = []
        for m in METRICAS:
            valores = [int(f[m]) for f in grupo if f[m].strip() in ("0", "1")]
            n = len(valores)
            celdas.append(f"{sum(valores)}/{n} = {sum(valores) / n:.2f}" if n else "0/0")
        print(f"{f'{t}/{s} k={k}':>14}  " + "  ".join(f"{c:>16}" for c in celdas))
