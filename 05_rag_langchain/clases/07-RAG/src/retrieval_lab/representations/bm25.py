from __future__ import annotations

import json
import numpy as np
from retrieval_lab.infrastructure.artifacts import fingerprint, write_json


class SparseBM25:
    """BM25 como producto escalar sparse; el ranking se calcula en Pinecone."""

    def __init__(self, texts, config, signature):
        from scipy import sparse
        from sklearn.feature_extraction.text import CountVectorizer

        self.config = config
        self.signature = fingerprint({"data": signature, "k1": config.bm25_k1, "b": config.bm25_b,
                                      "tokenizer": "word-2-plus-lowercase-english-stop-v1"})
        root = config.artifacts_dir / "indexes" / f"bm25-{self.signature[:16]}"
        root.mkdir(parents=True, exist_ok=True)
        ready = root / "ready.json"
        if ready.exists():
            vocabulary = json.loads((root / "vocabulary.json").read_text())
            self.vectorizer = CountVectorizer(vocabulary=vocabulary, stop_words="english")
            self.matrix = sparse.load_npz(root / "weights.npz").tocsr()
            return
        self.vectorizer = CountVectorizer(lowercase=True, stop_words="english", dtype=np.float32)
        counts = self.vectorizer.fit_transform(texts).tocsr()
        lengths = np.asarray(counts.sum(axis=1)).ravel()
        document_frequency = np.bincount(counts.indices, minlength=counts.shape[1])
        idf = np.log1p((len(texts) - document_frequency + .5) / (document_frequency + .5))
        rows = np.repeat(np.arange(len(texts)), np.diff(counts.indptr))
        length_norm = config.bm25_k1 * (1 - config.bm25_b + config.bm25_b * lengths / lengths.mean())
        counts.data = (counts.data * (config.bm25_k1 + 1) /
                       (counts.data + length_norm[rows]) * idf[counts.indices]).astype(np.float32)
        self.matrix = counts
        self.matrix.sort_indices()
        sparse.save_npz(root / "weights.npz", counts)
        write_json(root / "vocabulary.json", {k: int(v) for k, v in self.vectorizer.vocabulary_.items()})
        write_json(ready, {"signature": self.signature, "shape": counts.shape})

    def document(self, row):
        value = self.matrix.getrow(row)
        if value.nnz > 2048:
            raise ValueError("Documento con más de 2048 términos sparse; revise el límite común de texto.")
        if not value.nnz:
            return {"indices": [self.matrix.shape[1]], "values": [1.0]}
        return {"indices": value.indices.tolist(), "values": value.data.tolist()}

    def query(self, text):
        value = self.vectorizer.transform([text]).tocsr()
        return {"indices": value.indices.tolist(), "values": [1.0] * value.nnz}
