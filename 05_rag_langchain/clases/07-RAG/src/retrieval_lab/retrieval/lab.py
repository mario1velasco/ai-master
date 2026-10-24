from __future__ import annotations

from retrieval_lab.retrieval import preparation, engine as retrieval


class RetrievalLab:
    def __init__(self, config, corpus, queries, texts, cache, remote, signature):
        self.config, self.corpus, self.queries = config, corpus, queries
        self.ids, self.texts = sorted(corpus), texts
        self.cache, self.remote, self.signature = cache, remote, signature
        self.sparse = None
        self.query_vectors = {}
        self.specs = {m.key: m for m in config.active_models}

    def prepare_lexical(self, verify_only=False):
        return preparation.prepare_lexical(self, verify_only=verify_only)

    def prepare_dense(self):
        return preparation.prepare_dense(self)

    def pipeline(self, arm, fresh_embedding=False):
        return retrieval.pipeline(self, arm, fresh_embedding)

    def retrieve(self, arm, qid, fresh_embedding=False):
        return retrieval.retrieve(self, arm, qid, fresh_embedding)
