"""Repetir los casos del examen con el agente y calcular sus métricas.

Como `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/medir.py`: `run_cases()` es su `ejecutar_casos()`
(una fila por intento). El cliente del caso va a la sesión del agente, como el `contexto` de clase.
"""

from typing import Any

import duckdb

from agent.evaluation.evaluate import evaluate_case
from agent.respond import respond
from contracts.agent import Session


def run_cases(
    cases: list[dict[str, Any]],
    con: duckdb.DuckDBPyConnection,
    repetitions: int = 1,
    guardrails: bool = True,
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """Devuelve una fila por intento: caso, repetición, comprobaciones y si aprueba."""
    rows = []
    for case in cases:
        for repetition in range(repetitions):
            session = Session(client_id=case["client_id"])
            answer = respond(case["question"], con=con, session=session, guardrails=guardrails)
            checks = evaluate_case(case, answer)
            row = {
                "id": case["id"],
                "category": case["category"],
                "repetition": repetition,
                "success": all(checks.values()),
                "checks": checks,
                # Llamadas al modelo del agente: los `pasos` de `evaluar_trayectoria()` de `sesion1/evaluar.py`
                "steps": answer.metrics.iterations if answer.metrics else None,
            }
            rows.append(row)
            if verbose:
                mark = "✅" if row["success"] else "❌"
                failed = [name for name, ok in checks.items() if not ok]
                print(f"  {mark} {case['id']} #{repetition + 1}" + (f"   falla: {', '.join(failed)}" if failed else ""))
    return rows
