"""Evaluar text2sql con un examen: `uv run python -m text2sql.evaluation --exam battery --repetitions 3`.

Como el `__main__` de `09_evaluacion_fiabilidad_seguridad/codigo_ejercicios/sesion1/medir.py` (`--repeticiones`) y
`main()` de `07_llm_open_source/clase_03/DropLab_sesion_3/practica/sesion_2/04_examen.py` (`--examen`, `--preguntas`,
`--ver`). La base es siempre la de `data/`, la que se mide.
"""

import argparse
import sys
from pathlib import Path

from database.semantic_layer import DATA_DIR, open_db
from text2sql.evaluation.exam import load_exam, view
from text2sql.evaluation.measure import compute_metrics, print_breakdown, print_metrics, run_cases

EXAMS_DIR = Path(__file__).with_name("exams")
EXAMS = ["battery", "final_test"]  # batería (para ajustar) y prueba final (reservada: solo para medir)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Examen de text2sql: repite, corrige y mide.")
    parser.add_argument("--exam", choices=EXAMS, default="battery")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--questions", nargs="*", help="Solo estas preguntas (ids).")
    parser.add_argument("--view", action="store_true", help="Enseñar el examen y sus resultados, sin llamar al modelo.")
    args = parser.parse_args(argv)

    con = open_db(DATA_DIR)
    try:
        questions = load_exam(EXAMS_DIR / f"{args.exam}.json", con)
    except ValueError as exc:  # Como el «[ERROR] …» de `python -m text2sql`: qué pregunta y por qué, sin traza
        print(f"[ERROR] examen {args.exam}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    if args.questions:
        questions = [q for q in questions if q["id"] in args.questions]
    if args.view:
        view(questions, args.exam)
        return
    print(f"🧪 Examen «{args.exam}»: {len(questions)} preguntas × {args.repetitions} repeticiones")
    rows = run_cases(questions, con, args.repetitions)
    print_metrics(compute_metrics(rows), args.repetitions)
    print_breakdown(rows, "category", "Por categoría")
    print_breakdown(rows, "trap", "Por trampa")


if __name__ == "__main__":
    main()
