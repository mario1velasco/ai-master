import json
import os
import time
from functools import cached_property
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from retrieval_lab.retrieval.engine import reciprocal_rank_fusion
from retrieval_lab.representations.vectors import unit_vectors
from umbra.domain.models import SearchResult
from umbra.retrieval.baseline import Baseline


class HybridRetriever:
    """Adaptador de solo lectura: no crea índices ni sube el corpus."""

    def __init__(self, settings, corpus, client=None, pinecone=None):
        self.settings, self.corpus = settings, corpus
        self.baseline = Baseline(settings)
        self._client, self._pinecone = client, pinecone
        self._indexes = {}

    @cached_property
    def client(self):
        from openai import OpenAI
        return self._client or OpenAI(timeout=self.settings.request_timeout, max_retries=2)

    @cached_property
    def pinecone(self):
        from pinecone import Pinecone
        return self._pinecone or Pinecone(api_key=os.environ["PINECONE_API_KEY"])

    @cached_property
    def vectorizer(self):
        namespace = self.baseline.location(True)["Namespace"]
        folder = self.settings.session06 / "artifacts/pinecone_v1/indexes" / namespace
        metadata = json.loads((folder / "ready.json").read_text())
        if namespace != "bm25-" + metadata["signature"][:16]:
            raise ValueError("La caché BM25 no corresponde al namespace seleccionado.")
        vocabulary = json.loads((folder / "vocabulary.json").read_text())
        return CountVectorizer(vocabulary=vocabulary, stop_words="english")

    def index(self, sparse):
        location = self.baseline.location(sparse)
        name = location["Índice"]
        if name not in self._indexes:
            info = self.pinecone.describe_index(name)
            metric = "dotproduct" if sparse else "cosine"
            dim = 0 if sparse else self.baseline.candidate["dimension"]
            if info.metric != metric or (info.dimension or 0) != dim or not info.status["ready"]:
                raise ValueError("Índice remoto incompatible o no disponible.")
            index = self.pinecone.Index(host=info.host)
            stats = index.describe_index_stats(_request_timeout=self.settings.request_timeout)
            count = stats.namespaces.get(location["Namespace"], {}).get("vector_count", 0)
            if count != location["Vectores esperados"]:
                raise ValueError("El namespace no contiene el corpus completo esperado. No se modifica.")
            self._indexes[name] = index
        return self._indexes[name]

    def search(self, query):
        query = query.strip()
        if not query or len(query) > 2000:
            raise ValueError("La búsqueda debe tener entre 1 y 2000 caracteres.")
        started = time.perf_counter()
        embedding = self.client.embeddings.create(model=self.baseline.model["name"],
            input=[query], dimensions=self.baseline.candidate["dimension"])
        vector = unit_vectors([embedding.data[0].embedding])[0].tolist()
        encoded = self.vectorizer.transform([query]).tocsr()
        sparse = {"indices": encoded.indices.tolist(), "values": [1.0] * encoded.nnz}
        rankings, units = [], 0
        for is_sparse, values in [(False, {"vector": vector}), (True, {"sparse_vector": sparse})]:
            if is_sparse and not sparse["indices"]:
                rankings.append([])
                continue
            result = self.index(is_sparse).query(namespace=self.baseline.location(is_sparse)["Namespace"],
                top_k=self.settings.candidate_depth, include_metadata=False, include_values=False,
                _request_timeout=self.settings.request_timeout, **values)
            rankings.append([(str(m.id), float(m.score)) for m in result.matches])
            usage = getattr(result, "usage", None)
            units += (getattr(usage, "read_units", 0) or 0)
        ranking = reciprocal_rank_fusion(rankings, self.settings.candidate_depth,
                                         self.baseline.payload["config"]["rrf_constant"])
        documents = [self.corpus.document(identifier, score) for identifier, score in ranking]
        return SearchResult(query, documents, {"query": query, "dense_candidates": len(rankings[0]),
            "lexical_candidates": len(rankings[1]), "fused_candidates": len(ranking), "read_units": units,
            "embedding_tokens": embedding.usage.total_tokens,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1)})
