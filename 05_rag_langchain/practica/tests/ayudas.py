"""Ayudas de test: cargan desde el notebook EXACTAMENTE el código que se entrega.

- No ejecutan celdas que llamen a la API.
- `cargar_funciones` extrae los imports y las constantes de la celda `imports` y las funciones
  pedidas (por nombre) del resto de celdas de código.
"""
import ast
import json
import sys
from pathlib import Path

PRACTICA = Path(__file__).resolve().parents[1]
RECURSOS = PRACTICA / "Recursos "          # ¡el nombre termina en espacio!
NOTEBOOK = RECURSOS / "rag_tenerife.ipynb"
PDF = RECURSOS / "data" / "TENERIFE.pdf"

if str(RECURSOS) not in sys.path:
    sys.path.insert(0, str(RECURSOS))


def leer_notebook():
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def celdas_codigo(nb=None):
    return [c for c in (nb or leer_notebook())["cells"] if c["cell_type"] == "code"]


def fuente(celda):
    return "".join(celda["source"])


def celda_por_etiqueta(etiqueta, nb=None):
    for celda in celdas_codigo(nb):
        if etiqueta in celda.get("metadata", {}).get("tags", []):
            return celda
    raise KeyError(etiqueta)


def _imports_y_constantes(codigo):
    """Solo imports y asignaciones de constantes (no ejecuta cargar_paginas ni imprime nada)."""
    arbol = ast.parse(codigo)
    nodos = [n for n in arbol.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    nodos += [n for n in arbol.body if isinstance(n, ast.Assign)
              and all(isinstance(t, ast.Name) and t.id.isupper() for t in n.targets)]
    return ast.Module(body=nodos, type_ignores=[])


def cargar_funciones(*nombres):
    """Devuelve un namespace con imports/constantes del notebook y las funciones pedidas."""
    espacio = {}
    exec(compile(_imports_y_constantes(fuente(celda_por_etiqueta("imports"))), "<imports>", "exec"), espacio)
    pendientes = set(nombres)
    for celda in celdas_codigo():
        arbol = ast.parse(fuente(celda))
        for nodo in arbol.body:
            if isinstance(nodo, ast.FunctionDef) and nodo.name in pendientes:
                modulo = ast.Module(body=[nodo], type_ignores=[])
                exec(compile(modulo, f"<notebook:{nodo.name}>", "exec"), espacio)
                pendientes.discard(nodo.name)
    if pendientes:
        raise KeyError(f"Funciones no encontradas en el notebook: {sorted(pendientes)}")
    return espacio
