"""Paso 10 · Comprueba la conclusión del notebook (300–500 palabras, tabla por k, caso y mejora).

La conclusión debe estar en una celda markdown que empiece por «### Conclusión».
Uso:  python -m herramientas.validar_conclusion "Recursos /rag_tenerife.ipynb"
"""
import json
import re
import sys
from pathlib import Path

METRICAS = ("hit", "respaldo", "citas", "abstenci")


def extraer(ruta_notebook):
    nb = json.loads(Path(ruta_notebook).read_text(encoding="utf-8"))
    for c in nb["cells"]:
        texto = "".join(c["source"])
        if c["cell_type"] == "markdown" and texto.lstrip().lower().startswith("### conclusi"):
            return texto
    return None


def validar(texto):
    problemas = []
    if texto is None:
        return ["No hay ninguna celda markdown que empiece por '### Conclusión'."]
    palabras = len(re.findall(r"\w+", re.sub(r"\|[-:| ]+\|", " ", texto)))
    if not 300 <= palabras <= 500:
        problemas.append(f"Tiene {palabras} palabras; deben ser entre 300 y 500.")
    bajo = texto.lower()
    filas_tabla = [l for l in texto.splitlines() if l.strip().startswith("|")]
    if len(filas_tabla) < 4:
        problemas.append("Falta la tabla con las cuatro métricas por k.")
    if not all(m in bajo for m in METRICAS):
        problemas.append("La tabla/texto debe mencionar Hit@k, respaldo, citas y abstención.")
    if not ("k = 2" in bajo or "k=2" in bajo) or not ("k = 4" in bajo or "k=4" in bajo):
        problemas.append("Debe comparar k = 2 y k = 4.")
    if not re.search(r"\bQ[1-6]\b", texto):
        problemas.append("Debe citar al menos un caso concreto (Q1–Q6).")
    for clave, nombre in (("recomiend", "recomendación"), ("limitaci", "limitación"), ("mejora", "mejora propuesta")):
        if clave not in bajo:
            problemas.append(f"Falta la {nombre}.")
    return problemas


if __name__ == "__main__":
    p = validar(extraer(sys.argv[1] if len(sys.argv) > 1 else "Recursos /rag_tenerife.ipynb"))
    print("\n".join(p) or "Conclusión válida.")
    sys.exit(1 if p else 0)
