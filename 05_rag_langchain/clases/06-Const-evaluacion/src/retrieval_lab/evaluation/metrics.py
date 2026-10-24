from __future__ import annotations

import numpy as np


METRICS = ("nDCG@10", "Precision@10", "MRR@10", "Recall normalizado@k", "MAP@k")


def precision_at_k(ids, grades, k):
    return sum(grades.get(d, 0) > 0 for d in ids[:k]) / k


def recall_at_k(ids, grades, k):
    relevant = sum(g > 0 for g in grades.values())
    return sum(grades.get(d, 0) > 0 for d in ids[:k]) / relevant if relevant else 0.0


def normalized_recall_at_k(ids, grades, k):
    if k <= 0:
        raise ValueError("k debe ser positivo.")
    denominator = min(k, sum(g > 0 for g in grades.values()))
    return sum(grades.get(d, 0) > 0 for d in ids[:k]) / denominator if denominator else 0.0


def reciprocal_rank(ids, grades, k):
    return next((1 / rank for rank, d in enumerate(ids[:k], 1) if grades.get(d, 0) > 0), 0.0)


def average_precision(ids, grades, k):
    relevant = sum(g > 0 for g in grades.values())
    hits, total = 0, 0.0
    for rank, doc_id in enumerate(ids[:k], 1):
        if grades.get(doc_id, 0) > 0:
            hits += 1
            total += hits / rank
    return total / relevant if relevant else 0.0


def dcg(grades):
    gains = np.asarray(grades, dtype=float)
    return float(np.sum(gains / np.log2(np.arange(len(gains)) + 2)))


def ndcg_at_k(ids, grades, k):
    ideal = dcg(sorted((max(0, g) for g in grades.values()), reverse=True)[:k])
    actual = dcg([max(0, grades.get(d, 0)) for d in ids[:k]])
    return actual / ideal if ideal else 0.0


def evaluate_ranking(ranking, grades, k):
    if k <= 0:
        raise ValueError("k debe ser positivo.")
    ids = [d for d, _ in ranking]
    if len(ids) != len(set(ids)):
        raise ValueError("Ranking con documentos duplicados.")
    if len(ids) > k:
        raise ValueError("El ranking excede la profundidad declarada.")
    relevant = sum(g > 0 for g in grades.values())
    return {"nDCG@10": ndcg_at_k(ids, grades, 10),
            "Precision@10": precision_at_k(ids, grades, 10),
            "MRR@10": reciprocal_rank(ids, grades, 10),
            "Recall normalizado@k": normalized_recall_at_k(ids, grades, k),
            "MAP@k": average_precision(ids, grades, k),
            "Relevantes recuperables@k": min(k, relevant),
            "Fracción juzgada@10": sum(d in grades for d in ids[:10]) / 10}
