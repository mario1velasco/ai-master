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
    """Las preguntas del examen, cada una con las filas de su SQL de referencia en `expected_rows`.

    Un examen mal escrito se para aquí, antes de llamar al modelo (`ValueError` con el id y el motivo): un id
    repetido mezclaría los intentos de dos preguntas, y una referencia que no pasa el validador no da respuesta.
    """
    questions: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    ids = [question["id"] for question in questions]
    for question in questions:
        if ids.count(question["id"]) > 1:
            raise ValueError(f"{question['id']}: id repetido")
        if question.get("sql"):
            ok, text = run_safe_sql(con, question["sql"])
            if not ok:
                raise ValueError(f"{question['id']}: el SQL de referencia no pasa el validador. {text}")
            question["expected_rows"] = json.loads(text.removesuffix(TRUNCATION_NOTE))
    return questions
