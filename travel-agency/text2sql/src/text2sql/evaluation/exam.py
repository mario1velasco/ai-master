"""El examen: preguntas escritas a mano, cada una con su SQL de referencia (o la marca de imposible).

Como `cargar()` de `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/04_examen.py` y `cargar_casos()`
de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/medir.py`: un JSON con una lista de preguntas.
Desvío (TRAVEL-007): las respuestas esperadas no se escriben a mano; salen de ejecutar el SQL de referencia con el
mismo validador que el SQL del modelo, así que las filas llegan con el mismo formato (importes a 2 decimales).
"""

import json
from pathlib import Path
from typing import Any

import duckdb

from text2sql.guard import TRUNCATION_NOTE, run_safe_sql


def load_exam(path: Path, con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Las preguntas del examen, cada una con las filas de su SQL de referencia en `expected_rows`."""
    questions: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    for question in questions:
        if question.get("sql"):
            _, text = run_safe_sql(con, question["sql"])
            question["expected_rows"] = json.loads(text.removesuffix(TRUNCATION_NOTE))
    return questions
