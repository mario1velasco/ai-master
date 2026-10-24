from __future__ import annotations

import time
from dataclasses import asdict
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from retrieval_lab.infrastructure.artifacts import fingerprint, write_json
from retrieval_lab.evaluation.metrics import METRICS, evaluate_ranking


def run_experiments(lab, arms, ids, qrels, config, split="development", fresh_embedding=False):
    if len({a.name for a in arms}) != len(arms):
        raise ValueError("Brazos duplicados.")
    experiment_signature = fingerprint({"config": asdict(config), "data": lab.signature,
                                        "queries": {q: lab.queries[q] for q in ids},
                                        "arms": [asdict(a) for a in arms], "split": split,
                                        "fresh_embedding": fresh_embedding})
    directory = config.results_dir / split / experiment_signature[:16]
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "protocol.json", {"signature": experiment_signature, "ids": ids,
               "arms": [asdict(a) for a in arms], "fresh_embedding": fresh_embedding,
               "timestamp_utc": datetime.now(timezone.utc).isoformat()})
    rng = np.random.default_rng(config.random_seed)
    runs = {a.name: {} for a in arms}
    observations = []
    pipelines = {a.name: lab.pipeline(a, fresh_embedding) for a in arms}
    for arm in arms:
        pipelines[arm.name].invoke(ids[0])  # Calentamiento excluido de las medidas.
    from tqdm.auto import tqdm
    total = len(ids) * len(arms) * config.latency_repetitions
    with tqdm(total=total, desc=f"Evaluación · {split}") as progress:
        for repetition in range(config.latency_repetitions):
            for qid in rng.permutation(ids):
                for index in rng.permutation(len(arms)):
                    arm = arms[index]
                    result = pipelines[arm.name].invoke(str(qid))
                    if repetition == 0:
                        runs[arm.name][qid] = result["ranking"]
                    observations.append({"Experimento": arm.name, "Consulta": qid, "Repetición": repetition,
                                         **{k: v for k, v in result.items() if k not in ("ranking", "branches")}})
                    progress.update()
            write_json(directory / "rankings.json", runs)
            pd.DataFrame(observations).to_csv(directory / "latency.csv", index=False)
    return summarize_runs(arms, ids, qrels, runs, observations, directory, fresh_embedding)


def summarize_runs(arms, ids, qrels, runs, observations, directory, fresh_embedding):
    latency = pd.DataFrame(observations)
    results = {}
    for arm in arms:
        per_query = pd.DataFrame([{"Consulta": qid,
                                   **evaluate_ranking(runs[arm.name][qid], qrels[qid], arm.depth)}
                                  for qid in ids]).set_index("Consulta")
        timings = latency[latency["Experimento"] == arm.name]
        summary = {"Experimento": arm.name, "Modelo": arm.model, "Dimensiones": arm.dimension,
                   "Estrategia": arm.strategy, "Candidatos por rama": arm.depth,
                   **per_query.mean().to_dict(),
                   "p50 (ms)": timings["latency_ms"].quantile(.50),
                   "p95 (ms)": timings["latency_ms"].quantile(.95),
                   "RU por consulta": timings["read_units"].mean(),
                   "Latencia incluye embedding API": fresh_embedding,
                   "Muestras de latencia": len(timings)}
        per_query.to_csv(directory / f"{arm.name}-metrics.csv")
        results[arm.name] = {"arm": arm, "summary": summary, "metrics": per_query,
                            "run": runs[arm.name], "latency": timings, "directory": directory}
    table(results).to_csv(directory / "summary.csv", index=False)
    return results


def table(results):
    return pd.DataFrame([r["summary"] for r in results.values()]).sort_values(
        ["nDCG@10", "Experimento"], ascending=[False, True]).reset_index(drop=True)
