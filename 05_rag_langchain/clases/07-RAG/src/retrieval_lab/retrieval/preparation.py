from __future__ import annotations

from retrieval_lab.representations.bm25 import SparseBM25
from retrieval_lab.representations.vectors import unit_vectors
from retrieval_lab.infrastructure.artifacts import fingerprint


def prepare_lexical(self, verify_only=False):
    self.sparse = SparseBM25(self.texts, self.config, self.signature)
    self.remote.upload("bm25", 0, self.sparse.signature, self.ids, self.corpus,
                       lambda row: {"sparse_values": self.sparse.document(row)},
                       verify_only=verify_only)
    return self.remote.inventory()


def prepare_dense(self):
    for spec in self.config.active_models:
        request = self.cache.output_spec(spec)
        self.cache.encode(request, self.texts[:2], "document")
        self.cache.encode(request, [next(iter(self.queries.values()))], "query")
    for dimension in sorted({d for spec in self.config.active_models for d in spec.dimensions}):
        self.remote.index(dimension)
    query_ids = sorted(self.queries)

    def prepare_model(spec):
        matrix, signature = self.cache.matrix(spec, self.ids, self.texts, "document")
        queries, _ = self.cache.matrix(spec, query_ids, [self.queries[q] for q in query_ids], "query")
        self.query_vectors[spec.key] = dict(zip(query_ids, queries))
        for dimension in spec.dimensions:
            namespace_signature = fingerprint({"embeddings": signature, "dimension": dimension, "L2": True})
            self.remote.upload(spec.key, dimension, namespace_signature, self.ids, self.corpus,
                               lambda row, d=dimension, a=matrix:
                               {"values": unit_vectors(a[row:row + 1], d)[0].tolist()})

    from retrieval_lab.infrastructure.concurrency import bounded_results
    for _ in bounded_results(prepare_model, self.config.active_models,
                             self.config.provider_concurrency):
        pass
    return self.remote.inventory()
