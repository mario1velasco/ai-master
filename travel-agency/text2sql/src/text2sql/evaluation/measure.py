"""Repetir el examen y calcular las métricas de text2sql.

Como `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/medir.py`: `run_cases()` es su
`ejecutar_casos()` (una fila por intento) y `compute_metrics()` su `calcular_metricas()`.
"""

from typing import Any

import duckdb

from contracts.sql import SqlStatus
from text2sql.evaluation.evaluate import evaluate_case
from text2sql.loop import ask


def run_cases(
    questions: list[dict[str, Any]], con: duckdb.DuckDBPyConnection, repetitions: int = 1
) -> list[dict[str, Any]]:
    """Devuelve una fila por intento: pregunta, repetición, estado de `ask()` y si aprueba."""
    rows = []
    for question in questions:
        for repetition in range(repetitions):
            result = ask(question["question"], con=con)
            verdict = evaluate_case(question, result)
            rows.append(
                {
                    "id": question["id"],
                    "category": question["category"],
                    "repetition": repetition,
                    "status": result.status.value,
                    "success": verdict["success"],
                    "reason": verdict["reason"],
                    "error": None,
                    # El «límite de pasos» de text2sql: 3 llamadas sin un SQL que pase el validador
                    "limit_reached": result.status is SqlStatus.sql_error,
                }
            )
    return rows


def _unavailable(row: dict[str, Any]) -> bool:
    """No pudo responder: error técnico de Ollama o límite de pasos (salvo en un adversario, donde es lo esperado)."""
    return bool(row["error"]) or (row["limit_reached"] and row["category"] != "adversarial")


def compute_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Las métricas del informe a partir de las filas de `run_cases()`."""
    n = len(rows)
    return {
        "attempts": n,
        # Disponibilidad: qué parte de los intentos pudo responder (bien o mal). Como `disponibilidad` de
        # `calcular_metricas()`: 1 - (errores técnicos + límite de pasos) / intentos. Si baja, el fallo no es de
        # SQL sino de Ollama o de que el modelo no consigue un SQL válido en 3 llamadas.
        "availability": 1 - sum(_unavailable(row) for row in rows) / n,
    }
