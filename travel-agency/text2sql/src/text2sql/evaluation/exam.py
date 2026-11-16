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

from text2sql.guard import TRUNCATION_NOTE, referenced_tables, run_safe_sql


def load_exam(path: Path, con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    """Las preguntas del examen, cada una con las filas de su SQL de referencia en `expected_rows` y sus vistas en
    `expected_views` (las mismas que saca el validador del SQL: así no hay erratas entre las vistas y el SQL).

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
            question["expected_views"] = list(dict.fromkeys(referenced_tables(con, question["sql"])))
    return questions


def _expected(question: dict[str, Any]) -> str:
    """Lo que debe devolver text2sql, legible (el `esperado_legible()` de `04_examen.py`)."""
    if question.get("must_deny"):
        return "imposible: debe decir que el dato no existe"
    if question["category"] == "adversarial":
        return "adversaria: no debe devolver filas"
    rows = question["expected_rows"]
    # PROYECTO.md §6: los resultados vacíos se revisan (¿es lo que se quería o una errata en el SQL?)
    return json.dumps(rows, ensure_ascii=False)[:300] + ("" if rows else " · 0 filas, revisar")


def view(questions: list[dict[str, Any]], exam: str) -> None:
    """Cada pregunta con su categoría, su trampa, sus vistas y su resultado, sin llamar al modelo.

    Como `ver()` de `04_examen.py`, en texto: sirve para revisar el examen antes de medir.
    """
    print(f"Examen «{exam}»: {len(questions)} preguntas con su resultado de referencia, sin modelo")
    for q in questions:
        views = ", ".join(q.get("expected_views", [])) or "—"
        print(f"\n[{q['id']}] {q['category']} · trampa {q['trap'] or '—'} · vistas {views}")
        print(f"     {q['question']}")
        print(f"     → {_expected(q)}")
