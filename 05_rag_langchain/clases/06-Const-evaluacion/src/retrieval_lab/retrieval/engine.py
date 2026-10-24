from __future__ import annotations

import time
from langchain_core.runnables import RunnableLambda
from retrieval_lab.representations.vectors import unit_vectors


def reciprocal_rank_fusion(rankings, limit, constant=60):
    scores = {}
    for ranking in rankings:
        for position, (doc_id, _) in enumerate(ranking, 1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (constant + position)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]


def pipeline(self, arm, fresh_embedding=False):
    return RunnableLambda(lambda qid: self.retrieve(arm, qid, fresh_embedding))


def retrieve(self, arm, qid, fresh_embedding=False):
    started = time.perf_counter()
    embedding_ms, rankings, units = 0.0, [], []
    if arm.strategy != "lexica":
        begin = time.perf_counter()
        vector = (self.cache.query(self.specs[arm.model], self.queries[qid], arm.dimension)
                  if fresh_embedding else unit_vectors([self.query_vectors[arm.model][qid]], arm.dimension)[0])
        embedding_ms = (time.perf_counter() - begin) * 1000
        rank, ru = self.remote.search(arm.model, arm.dimension, arm.depth, vector=vector.tolist())
        rankings.append(rank)
        units.append(ru)
    if arm.strategy in ("lexica", "hibrida"):
        vector = self.sparse.query(self.queries[qid])
        rank, ru = self.remote.search("bm25", 0, arm.depth, sparse_vector=vector) if vector["indices"] else ([], 0)
        rankings.append(rank)
        units.append(ru)
    ranking = (reciprocal_rank_fusion(rankings, arm.depth, self.config.rrf_constant)
               if arm.strategy == "hibrida" else rankings[0])
    elapsed = (time.perf_counter() - started) * 1000
    return {"ranking": ranking, "latency_ms": elapsed, "embedding_ms": embedding_ms,
            "read_units": sum(units) if all(u is not None for u in units) else None,
            "candidate_union": len({d for ranking in rankings for d, _ in ranking}),
            "branches": rankings}
