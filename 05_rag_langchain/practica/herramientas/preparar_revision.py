"""Paso 9 · Ayuda a la revisión MANUAL de las 12 ejecuciones y valida revision.csv.

- `python -m herramientas.preparar_revision "Recursos /resultados.json"` imprime, por caso, la pregunta,
  la respuesta esperada según la guía, las páginas/fragmentos recuperados y la respuesta del modelo.
- `python -m herramientas.preparar_revision --validar "Recursos /revision.csv"` comprueba que la
  revisión esté completa (0/1/NA, sin celdas vacías). La revisión en sí la hace la persona.
"""
import csv
import json
import sys
from pathlib import Path

# Verificado con pdftotext sobre TENERIFE.pdf. Solo para la persona que revisa: NO se pasa al modelo.
ESPERADAS = {
    "Q1": "Mirador de La Jardina (p. 5: «diría que es mi mirador favorito»).",
    "Q2": "Carretera TF-24 (de La Esperanza) desde la rotonda de Padre Anchieta; parar en el Mirador de La Tarta (p. 15).",
    "Q3": "La Fogalera y Reina Pepiada (p. 25); de entrante, degustación de cachapitas.",
    "Q4": "Playa de Los Cristianos y Playa de Las Vistas (p. 23).",
    "Q5": "La guía NO trata la meteorología: debe abstenerse.",
    "Q6": "La guía menciona el Siam Park (p. 21) pero NO da precio: debe abstenerse.",
}
CAMPOS = ("hit_pagina", "respaldo", "citas", "abstencion")


def bloques(ruta_resultados):
    datos = json.loads(Path(ruta_resultados).read_text(encoding="utf-8"))
    salida = []
    for r in datos:
        frags = "\n".join(f"    - {f['id']} (p. {f['page']}): {f['texto'][:160].replace(chr(10), ' ')}…" for f in r["fragmentos"])
        salida.append(
            f"=== {r['id']} · k={r['k']} · tipo={r['tipo']} · hit_pagina={r['hit_pagina']}\n"
            f"Pregunta:  {r['pregunta']}\n"
            f"Esperado:  {ESPERADAS[r['id']]}\n"
            f"Páginas recuperadas: {[f['page'] for f in r['fragmentos']]} · citadas: {r['paginas_citadas']}\n"
            f"Fragmentos:\n{frags}\n"
            f"Respuesta del modelo:\n{r['respuesta']}\n")
    return salida


def validar_revision(ruta_csv):
    """Devuelve la lista de problemas (vacía = revisión completa)."""
    problemas = []
    with open(ruta_csv, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    if len(filas) != 12 or len({(r["id"], r["k"]) for r in filas}) != 12:
        problemas.append("La revisión debe tener 12 filas distintas (id, k).")
    for r in filas:
        et = f"{r['id']} k={r['k']}"
        respondible = r["tipo"] == "respondible"
        for campo in CAMPOS:
            aplica = (campo in ("hit_pagina", "respaldo", "citas")) == respondible
            valor = (r.get(campo) or "").strip()
            if not valor:
                problemas.append(f"{et}: '{campo}' está vacío (pendiente).")
            elif aplica and valor not in ("0", "1"):
                problemas.append(f"{et}: '{campo}' debe ser 0 o 1 (es {valor!r}).")
            elif not aplica and valor != "NA":
                problemas.append(f"{et}: '{campo}' no aplica y debe ser NA (es {valor!r}).")
    return problemas


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--validar":
        problemas = validar_revision(sys.argv[2] if len(sys.argv) > 2 else "Recursos /revision.csv")
        print("\n".join(problemas) or "Revisión completa.")
        sys.exit(1 if problemas else 0)
    print("\n".join(bloques(sys.argv[1] if len(sys.argv) > 1 else "Recursos /resultados.json")))
