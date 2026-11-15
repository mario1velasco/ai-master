"""Corregir un intento: ¿ha devuelto text2sql la misma tabla que el SQL de referencia?

Como `evaluar_caso()` de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/comun/evaluacion.py`: reglas de
código, baratas y repetibles, que devuelven si el intento aprueba y, si no, por qué (el `faltan` de `corregir()` en
`07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/04_examen.py`).
"""

from typing import Any

from contracts.sql import SqlResult


def _row_contains(row: dict[str, Any], expected_row: dict[str, Any]) -> bool:
    """La fila del intento tiene todos los valores de la fila de la referencia (sin mirar nombres de columna)."""
    return all(any(value == expected for value in row.values()) for expected in expected_row.values())


def evaluate_case(question: dict[str, Any], result: SqlResult) -> dict[str, Any]:
    """Aprueba si la última consulta (la que da la respuesta) devuelve la misma tabla que la referencia.

    Los nombres de las columnas no cuentan (el modelo pone sus alias) y puede haber columnas de más u otro orden.
    Cada fila de la referencia se empareja con la primera fila **libre** del intento que contiene todos sus valores:
    el `any()` de `corregir()` del tema 7, aplicado fila a fila, para que los valores no se crucen entre filas
    (MAD 10 y BCN 5 no es lo mismo que MAD 5 y BCN 10).

    Caso raro conocido (opción voraz, acordada en TRAVEL-007): si el intento trae una columna de más cuyo número
    coincide con el de otra fila, esa fila puede quedarse emparejada con la referencia equivocada y un intento
    correcto suspende. Se ve en el informe con su motivo; se prefirió a probar todas las combinaciones, que en el caso
    contrario aprueba un intento malo sin que se note.
    """
    rows = result.queries[-1].rows if result.queries else []
    expected_rows = question["expected_rows"]
    # Mismo número de filas: si no, las filas de más pasarían (p. ej. las tres «Ana López» cuando se pedía una)
    if len(rows) != len(expected_rows):
        return {"success": False, "reason": f"{len(rows)} filas en vez de {len(expected_rows)}"}
    free = list(rows)
    for expected_row in expected_rows:
        match = next((row for row in free if _row_contains(row, expected_row)), None)
        if match is None:
            return {"success": False, "reason": f"ninguna fila del intento tiene {expected_row}"}
        free.remove(match)
    return {"success": True, "reason": None}
