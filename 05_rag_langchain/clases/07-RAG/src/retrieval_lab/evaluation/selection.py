from __future__ import annotations

import json
from dataclasses import asdict
from retrieval_lab.infrastructure.artifacts import write_json
from retrieval_lab.evaluation.runner import table
from retrieval_lab.evaluation.statistics import paired_bootstrap


def candidate_shortlist(results, config, corpus_size, sparse_bytes):
    frame = table(results)
    frame["Vectores brutos (GiB)"] = [
        (corpus_size * row["Dimensiones"] * 4 + (sparse_bytes if row["Estrategia"] != "densa" else 0)) / 2**30
        for _, row in frame.iterrows()]
    eligible = frame[frame["p95 (ms)"] <= config.latency_budget_ms]
    if eligible.empty:
        raise RuntimeError("Ninguna configuración cumple el presupuesto. No hay ganador viable.")
    best = eligible["nDCG@10"].max()
    shortlist = eligible[eligible["nDCG@10"] >= best - config.quality_tolerance]
    chosen = shortlist.sort_values(["Vectores brutos (GiB)", "p95 (ms)", "Experimento"]).iloc[0]
    return frame, shortlist, chosen


def freeze_decision(reference, candidate, lab, dev_ids, holdout_ids, config):
    payload = {"reference": asdict(reference), "candidate": asdict(candidate),
               "development": dev_ids, "holdout": holdout_ids, "data": lab.signature,
               "config": asdict(config), "remote": lab.remote.inventory().to_dict(orient="records")}
    normalized = json.loads(json.dumps(payload, default=str))
    path = config.results_dir / "frozen_decision.json"
    if path.exists() and json.loads(path.read_text()) != normalized:
        raise RuntimeError("Ya hay otra decisión congelada. No reutilice la reserva final para retocar el ganador; "
                           "use otro directorio de artefactos y declare la nueva evaluación como exploratoria.")
    write_json(path, normalized)
    return path

def conclude_evaluation(results, reference, candidate, config):
    a, b = results[reference.name], results[candidate.name]
    delta = paired_bootstrap(a["metrics"]["nDCG@10"], b["metrics"]["nDCG@10"],
                             config.bootstrap_iterations, config.random_seed)
    within_latency = b["summary"]["p95 (ms)"] <= config.latency_budget_ms
    if candidate.name == reference.name:
        verdict = "La selección conserva la referencia; no existe una mejora A/B que afirmar."
    elif delta["IC95 inferior"] > 0:
        verdict = "La reserva aporta evidencia de mejora media de nDCG@10 para B en este conjunto."
    elif delta["IC95 superior"] < 0:
        verdict = "B empeora nDCG@10 en la reserva; no se recomienda sustituir A basándose en desarrollo."
    else:
        verdict = "La diferencia no es concluyente con estas consultas: el intervalo incluye cero."
    latency_text = ("El candidato cumple" if within_latency else "El candidato NO cumple")
    conclusion = (verdict + " " + latency_text + " el presupuesto con embedding en vivo. "
                  "La memoria estimada no equivale a la factura de Pinecone y el resultado no demuestra impacto online.")
    write_json(config.results_dir / "final_report.json",
               {"reference": asdict(reference), "candidate": asdict(candidate), "paired_ndcg": delta,
                "end_to_end_latency_ok": bool(within_latency), "conclusion": conclusion,
                "results": table(results).to_dict(orient="records")})
    return delta, conclusion
