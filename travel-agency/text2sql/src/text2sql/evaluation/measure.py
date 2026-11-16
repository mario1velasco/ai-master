"""Repetir el examen y calcular las métricas de text2sql.

Como `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/medir.py`: `run_cases()` es su
`ejecutar_casos()` (una fila por intento), `compute_metrics()` su `calcular_metricas()` y `print_metrics()` su
`imprimir_metricas()`. Desvío: los tokens y la latencia de cada intento no los devuelve `ask()`; salen de los eventos
de su traza (`trace_id`) en el archivo de hoy de `logs/text2sql/`, como hace el comando `python -m text2sql -q`.
"""

import os
import statistics
from datetime import UTC, datetime
from typing import Any

import duckdb

from contracts.metrics import BaseMetrics, Component, LlmCallMetrics
from contracts.metrics.llm import CostEstimate, CostRate
from contracts.sql import SqlStatus
from telemetry import events_path, read_events
from text2sql.evaluation.evaluate import evaluate_case
from text2sql.loop import ask

# € por millón de tokens, de entrada y de salida (orientativo): `PRECIO_MILLON_TOKENS` de `medir.py`
PRICE_PER_MILLION_TOKENS = float(os.getenv("PRICE_PER_MILLION_TOKENS", "0.5"))
RATE = CostRate(
    reference="PRICE_PER_MILLION_TOKENS",
    input_cost_per_1m_tokens=PRICE_PER_MILLION_TOKENS,
    output_cost_per_1m_tokens=PRICE_PER_MILLION_TOKENS,
    currency="EUR",
)


def percentile(values: list[float], p: float) -> float:
    """El valor por debajo del cual queda el p % de los valores: `percentil()` de `medir.py`, igual."""
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(p / 100 * (len(ordered) - 1)))] if ordered else 0.0


def _trace_events(trace_id: str) -> list[BaseMetrics]:
    """Los eventos de una pregunta (`text2sql.ask` y sus pasos), del archivo de hoy de `logs/text2sql/`."""
    events = read_events(events_path(Component.text2sql, datetime.now(UTC).date()))
    return [event.metrics for event in events if event.metrics.trace_id == trace_id]


def run_cases(
    questions: list[dict[str, Any]], con: duckdb.DuckDBPyConnection, repetitions: int = 1, verbose: bool = True
) -> list[dict[str, Any]]:
    """Devuelve una fila por intento: pregunta, repetición, estado de `ask()`, si aprueba y sus medidas."""
    rows = []
    for question in questions:
        for repetition in range(repetitions):
            result = ask(question["question"], con=con)
            verdict = evaluate_case(question, result)
            events = _trace_events(result.trace_id)
            [asked] = [m for m in events if m.name == "text2sql.ask"]
            llm = [m for m in events if isinstance(m, LlmCallMetrics)]
            row = {
                "id": question["id"],
                "category": question["category"],
                "trap": question["trap"],
                "repetition": repetition,
                "trace_id": result.trace_id,
                "status": result.status.value,
                "sql": result.queries[-1].sql if result.queries else None,  # la que se corrige
                "success": verdict["success"],
                "reason": verdict["reason"],
                "seconds": asked.latency_ms / 1000,  # el span `text2sql.ask`: la pregunta entera
                # Ollama tuvo que cargar el modelo en memoria (`OllamaTimings.cold_start`, ~150 s en el primero)
                "cold_start": any(m.ollama is not None and m.ollama.cold_start for m in llm),
                "input_tokens": sum(m.input_tokens for m in llm),
                "output_tokens": sum(m.output_tokens for m in llm),
                "error": None,
                # El «límite de pasos» de text2sql: 3 llamadas sin un SQL que pase el validador
                "limit_reached": result.status is SqlStatus.sql_error,
            }
            rows.append(row)
            if verbose:
                mark = "✅" if row["success"] else "❌"
                tokens = row["input_tokens"] + row["output_tokens"]
                print(
                    f"  {mark} {row['id']} #{repetition + 1}  {row['seconds']:5.1f} s  {tokens:5} tokens  "
                    f"{row['status']}" + (f"   falla: {row['reason']}" if row["reason"] else "")
                )
    return rows


def _unavailable(row: dict[str, Any]) -> bool:
    """No pudo responder: error técnico de Ollama o límite de pasos (salvo en un adversario, donde es lo esperado)."""
    return bool(row["error"]) or (row["limit_reached"] and row["category"] != "adversarial")


def compute_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Las métricas del informe a partir de las filas de `run_cases()`.

    Cada métrica lleva al lado qué mide, cómo se calcula y para qué sirve (la tabla completa, en `text2sql/AGENTS.md`).
    """
    n = len(rows)
    by_question: dict[str, list[bool]] = {}
    for row in rows:
        by_question.setdefault(row["id"], []).append(row["success"])
    passed = sum(row["success"] for row in rows)
    measured = [row for row in rows if row["seconds"] is not None]  # con traza: sin error de Ollama
    # Sin el arranque en frío: cargar el modelo no es lo que tarda una pregunta (como restar `segundos_carga` en
    # `04_examen.py`). Ese intento sí cuenta para el resto de métricas
    seconds = [row["seconds"] for row in measured if not row["cold_start"]]
    tokens = sum(row["input_tokens"] + row["output_tokens"] for row in measured)
    cost = CostEstimate.from_tokens(
        sum(row["input_tokens"] for row in measured), sum(row["output_tokens"] for row in measured), RATE
    ).total_cost
    return {
        "attempts": n,
        # Tasa de éxito (calidad): aprobados / intentos. ¿Responde bien? Es la nota del examen
        "success_rate": passed / n,
        # pass^k (fiabilidad): preguntas que aprueban sus k intentos / preguntas. ¿Responde bien SIEMPRE? Es la
        # que importa en producción: una pregunta que a veces falla, falla a algún cliente
        "pass_k": sum(all(v) for v in by_question.values()) / len(by_question),
        # pass@k: preguntas con al menos un intento aprobado / preguntas. ¿Sabe hacerlo alguna vez? Si es alta y
        # pass^k baja, el modelo sabe pero es inestable (más ejemplos o temperatura); si es baja, no sabe
        "pass_at_k": sum(any(v) for v in by_question.values()) / len(by_question),
        # Latencia (segundos del span `text2sql.ask`): mediana (p50, lo normal) y p95 (lo que tarda en los peores
        # casos, 1 de cada 20). Se mira el p95: es lo que espera el cliente cuando va mal
        "latency_p50": statistics.median(seconds) if seconds else None,
        "latency_p95": percentile(seconds, 95) if seconds else None,
        # Disponibilidad: qué parte de los intentos pudo responder (bien o mal). Como `disponibilidad` de
        # `calcular_metricas()`: 1 - (errores técnicos + límite de pasos) / intentos. Si baja, el fallo no es de
        # SQL sino de Ollama o de que el modelo no consigue un SQL válido en 3 llamadas
        "availability": 1 - sum(_unavailable(row) for row in rows) / n,
        # Tokens medios por pregunta (entrada + salida de todas sus llamadas al modelo): el tamaño del prompt y
        # de los reintentos. Sube con el esquema en el prompt o si el modelo necesita corregirse
        "tokens_mean": tokens / len(measured) if measured else None,
        # Coste por pregunta: los tokens con la tarifa de referencia (en local es 0; sirve para comparar)
        "cost_per_question": cost / len(measured) if measured else None,
        # Coste por caso resuelto: todo lo gastado entre los aprobados. Lo que de verdad cuesta una respuesta
        # buena: un modelo barato que falla mucho sale caro
        "cost_per_success": cost / passed if passed else None,
    }


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.0%}"


def _seconds(x: float | None) -> str:
    return "—" if x is None else f"{x:.1f} s"


def _per_thousand(x: float | None) -> str:
    return "—" if x is None else f"{x * 1000:.3f} €"


def print_metrics(m: dict[str, Any], k: int) -> None:
    """El informe en pantalla, como `imprimir_metricas()` de `medir.py`."""
    tokens = "—" if m["tokens_mean"] is None else f"{m['tokens_mean']:.0f}"
    print(f"\n📊 {m['attempts']} intentos")
    print(f"   Calidad         tasa de éxito {_pct(m['success_rate'])}")
    print(f"   Fiabilidad      pass^{k} {_pct(m['pass_k'])} · pass@{k} {_pct(m['pass_at_k'])}")
    print(f"   Latencia        mediana {_seconds(m['latency_p50'])} · p95 {_seconds(m['latency_p95'])}")
    print(f"   Disponibilidad  {_pct(m['availability'])}")
    print(
        f"   Coste           {tokens} tokens/pregunta · {_per_thousand(m['cost_per_question'])} por 1.000 preguntas"
        f" · {_per_thousand(m['cost_per_success'])} por 1.000 casos resueltos"
    )


def print_breakdown(rows: list[dict[str, Any]], key: str, title: str) -> None:
    """Aciertos por grupo: `por_categoria()` de `medir.py`, para la categoría y para la trampa.

    Dice dónde falla: por categoría (¿las de borde?, ¿los adversarios?) y por trampa de los datos (`PROYECTO.md`
    §3), que apunta a qué regla del prompt o qué vista hay que mejorar. Las preguntas sin trampa no salen por trampa.
    """
    print(f"\n   {title}:")
    for group in dict.fromkeys(row[key] for row in rows if row[key] is not None):
        sub = [row for row in rows if row[key] == group]
        print(f"   · {group:<11} {sum(row['success'] for row in sub)}/{len(sub)} aciertos")
