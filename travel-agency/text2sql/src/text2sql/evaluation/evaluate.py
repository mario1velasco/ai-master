"""Corregir un intento: ¿ha devuelto text2sql la misma tabla que el SQL de referencia?

Como `evaluar_caso()` de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/comun/evaluacion.py`: reglas de
código, baratas y repetibles, que devuelven si el intento aprueba y, si no, por qué (el `faltan` de `corregir()` en
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/04_examen.py`).
"""

from typing import Any

from contracts.sql import SqlResult


def evaluate_case(question: dict[str, Any], result: SqlResult) -> dict[str, Any]:
    """Aprueba si la última consulta (la que da la respuesta) devuelve las filas de la referencia."""
    rows = result.queries[-1].rows if result.queries else []
    success = rows == question["expected_rows"]
    return {"success": success, "reason": None if success else "filas distintas de la referencia"}
