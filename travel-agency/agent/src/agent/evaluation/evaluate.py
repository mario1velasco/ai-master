"""Corregir un intento del agente con reglas de código: ¿tiene el dato correcto y ha llegado bien?

Como `evaluar_caso()` de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/comun/evaluacion.py`: una comprobación
por cada criterio que el caso pide, más la de error técnico, y aprueba si se cumplen todas.
"""

from typing import Any

from contracts.agent import AgentAnswer, AgentStatus


def evaluate_case(case: dict[str, Any], answer: AgentAnswer) -> dict[str, bool]:
    """Una comprobación por criterio aplicable del caso (`evaluar_caso` de clase); `success` va aparte, en la fila."""
    checks: dict[str, bool] = {}
    if case.get("must_contain"):
        checks["must_contain"] = any(value in answer.answer for value in case["must_contain"])
    if case.get("expected_tools"):
        checks["expected_tools"] = all(tool in answer.tools_used for tool in case["expected_tools"])
    # El «sin error técnico» de clase (`error is None and not limite_alcanzado`): aquí, el turno acabó bien
    checks["no_technical_error"] = answer.status is AgentStatus.ok
    return checks
