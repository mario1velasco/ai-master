from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
from retrieval_lab.infrastructure.artifacts import fingerprint, write_json


@dataclass(frozen=True)
class Arm:
    model: str
    dimension: int
    strategy: str
    depth: int

    @property
    def name(self):
        return f"{self.model}-d{self.dimension}-{self.strategy}-k{self.depth}"


def experiment_arms(config):
    arms = [Arm("bm25", 0, "lexica", config.comparison_depth)]
    for model in config.active_models:
        arms += [Arm(model.key, dim, strategy, k) for dim in model.dimensions
                 for strategy in ("densa", "hibrida") for k in config.candidate_depths]
    return arms


def make_query_split(queries, qrels, config):
    from sklearn.model_selection import train_test_split

    ids = sorted(set(queries) & set(qrels))
    counts = pd.Series({q: sum(g > 0 for g in qrels[q].values()) for q in ids})
    strata = pd.qcut(counts.rank(method="first"), q=5, labels=False)
    dev, holdout = train_test_split(ids, test_size=config.evaluation_query_count,
                                    stratify=strata, random_state=config.random_seed)
    payload = {"development": sorted(dev), "holdout": sorted(holdout),
               "qrels": fingerprint(qrels), "seed": config.random_seed}
    write_json(config.results_dir / f"split-{fingerprint(payload)[:12]}.json", payload)
    return sorted(dev), sorted(holdout)


def model_plan(config, n_documents):
    return pd.DataFrame([{"Modelo": m.key, "Identificador": m.name, "Dimensiones": d,
                          "Vectores": n_documents, "Vectores brutos (GiB)": n_documents * d * 4 / 2**30}
                         for m in config.active_models for d in m.dimensions])
