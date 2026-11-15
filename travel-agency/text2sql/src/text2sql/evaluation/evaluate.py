"""Corregir un intento: ¿ha devuelto text2sql la misma tabla que el SQL de referencia?

Como `evaluar_caso()` de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/comun/evaluacion.py`: reglas de
código, baratas y repetibles, que devuelven si el intento aprueba y, si no, por qué (el `faltan` de `corregir()` en
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/04_examen.py`).
"""

from typing import Any

from contracts.sql import SqlResult


def evaluate_case(question: dict[str, Any], result: SqlResult) -> dict[str, Any]:
    """Aprueba si la última consulta (la que da la respuesta) contiene los valores de la referencia.

    Los nombres de las columnas no cuentan (el modelo pone sus alias) y puede haber columnas de más: se busca cada
    valor esperado entre los del intento, como el `any()` de `corregir()` en el tema 7.
    """
    rows = result.queries[-1].rows if result.queries else []
    expected_rows = question["expected_rows"]
    # Mismo número de filas: si no, las filas de más pasarían (p. ej. las tres «Ana López» cuando se pedía una)
    if len(rows) != len(expected_rows):
        return {"success": False, "reason": f"{len(rows)} filas en vez de {len(expected_rows)}"}
    values = [value for row in rows for value in row.values()]
    missing = [
        expected for row in expected_rows for expected in row.values() if not any(v == expected for v in values)
    ]
    if missing:
        return {"success": False, "reason": f"faltan valores de la referencia: {missing}"}
    return {"success": True, "reason": None}
