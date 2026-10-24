from __future__ import annotations

import json
import threading
from dataclasses import asdict, replace
from datetime import datetime, timezone
import numpy as np
from retrieval_lab.infrastructure.artifacts import fingerprint, write_json
from retrieval_lab.infrastructure.concurrency import bounded_results
from retrieval_lab.infrastructure.rate_limits import RequestLimiter, transient_retry
from retrieval_lab.representations.vectors import unit_vectors
from retrieval_lab.representations.providers import build_embedder


class EmbeddingCache:
    def __init__(self, config):
        self.config = config
        self.clients = {}
        self.limiters = {}
        self.lock = threading.Lock()

    def client(self, spec):
        key = (spec.key, spec.provider, spec.name, spec.native_dimension, spec.revision)
        with self.lock:
            if spec.key in self.clients:
                return self.clients[spec.key]
            if key not in self.clients:
                self.clients[key] = build_embedder(spec)
            return self.clients[key]

    def limiter(self, spec):
        with self.lock:
            if spec.provider not in self.limiters:
                self.limiters[spec.provider] = RequestLimiter(spec.provider)
            return self.limiters[spec.provider]

    def output_spec(self, spec, dimension=None):
        requested = dimension or max(spec.dimensions)
        if spec.provider in ("openai", "gemini"):
            return replace(spec, native_dimension=requested)
        return spec

    def encode(self, spec, texts, role):
        client = self.client(spec)
        if role == "document" or spec.provider == "openai":
            function = lambda: client.embed_documents(texts)
        elif hasattr(client, "embed_queries"):
            function = lambda: client.embed_queries(texts)
        else:
            function = lambda: [client.embed_query(text) for text in texts]
        tokens = sum(len(text.encode("utf-8")) + 128 for text in texts)
        requests = len(texts) if spec.provider == "gemini" else 1
        values = transient_retry(function, self.limiter(spec), tokens, requests=requests)
        array = unit_vectors(values)
        if array.shape != (len(texts), spec.native_dimension):
            raise ValueError("Dimensión devuelta distinta de la declarada.")
        return array

    def _identity(self, spec, ids, texts, role):
        model = {k: v for k, v in asdict(spec).items() if k != "dimensions"}
        signature = fingerprint({"model": model, "ids": ids, "texts": texts, "role": role,
                                 "format_version": "retrieval-prefixes-v1"})
        root = self.config.artifacts_dir / "embeddings" / f"{spec.key}-{role}-{signature[:16]}"
        return model, signature, root

    def matrix(self, spec, ids, texts, role):
        if role not in ("document", "query") or len(ids) != len(texts) or not ids:
            raise ValueError("Entradas del caché no válidas.")
        model, signature, root = self._identity(spec, ids, texts, role)
        if not (root / "manifest.json").exists():
            spec = self.output_spec(spec)
            model, signature, root = self._identity(spec, ids, texts, role)
        root.mkdir(parents=True, exist_ok=True)
        path, state_path = root / "vectors.npy", root / "manifest.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        if state and state["signature"] != signature:
            raise ValueError("Caché incompatible.")
        shape = (len(ids), spec.native_dimension)
        if path.exists() and state:
            matrix = np.load(path, mmap_mode="r+")
            if matrix.shape != shape or matrix.dtype != np.float32:
                raise ValueError("Matriz de caché dañada o incompatible.")
        elif path.exists() or state:
            raise ValueError("Caché incompleta: falta la matriz o su manifiesto.")
        else:
            matrix = np.lib.format.open_memmap(path, mode="w+", dtype=np.float32, shape=shape)
            state = {"signature": signature, "model": model, "role": role, "ids": ids,
                     "normalization": "L2", "completed": 0, "shape": shape,
                     "created_utc": datetime.now(timezone.utc).isoformat()}
            write_json(state_path, state)
        progress_path = root / "progress.json"
        progress = json.loads(progress_path.read_text()) if progress_path.exists() else {
            "signature": signature, "ranges": [[0, state["completed"]]] if state["completed"] else []}
        if progress["signature"] != signature:
            raise ValueError("Progreso de caché incompatible.")
        completed = np.zeros(len(ids), dtype=bool)
        for left, right in progress["ranges"]:
            if not 0 <= left < right <= len(ids):
                raise ValueError("Progreso de caché fuera de rango.")
            completed[left:right] = True
        if completed.all():
            print(f"{spec.key}: {len(ids):,} embeddings de {role} recuperados de caché.")
            return np.load(path, mmap_mode="r"), signature
        self._complete(spec, texts, role, matrix, completed, progress_path, signature)
        return np.load(path, mmap_mode="r"), signature

    def _batches(self, spec, texts, role, completed):
        size = 1 if spec.provider == "huggingface" and role == "query" else self.config.embedding_batch_size
        limit = self.config.embedding_batch_token_limit
        quota = self.limiter(spec).tpm
        if spec.provider == "gemini" and self.limiter(spec).rpm:
            size = min(size, self.limiter(spec).rpm)
        limit = min(limit, quota) if quota else limit
        left, tokens, count = None, 0, 0
        for row, text in enumerate(texts):
            cost = len(text.encode("utf-8")) + 128
            if completed[row]:
                if left is not None:
                    yield left, row
                    left, tokens, count = None, 0, 0
                continue
            if cost > limit:
                raise ValueError("Una entrada excede el límite de tokens por lote o la cuota TPM.")
            if left is not None and (count == size or tokens + cost > limit):
                yield left, row
                left, tokens, count = None, 0, 0
            if left is None:
                left = row
            tokens += cost
            count += 1
        if left is not None:
            yield left, len(texts)

    def _complete(self, spec, texts, role, matrix, completed, progress_path, signature):
        from tqdm.auto import tqdm

        def process(bounds):
            left, right = bounds
            return left, right, self.encode(spec, texts[left:right], role)

        workers = 1 if spec.provider == "huggingface" else self.config.embedding_concurrency
        batches = list(self._batches(spec, texts, role, completed))
        with tqdm(total=len(texts), initial=int(completed.sum()), desc=f"{spec.key} · {role}",
                  unit="doc" if role == "document" else "query") as bar:
            for left, right, array in bounded_results(process, batches, workers):
                matrix[left:right] = array
                matrix.flush()
                completed[left:right] = True
                changes = np.flatnonzero(np.diff(np.r_[False, completed, False]))
                ranges = changes.reshape(-1, 2).tolist()
                write_json(progress_path, {"signature": signature, "completed": int(completed.sum()),
                                           "ranges": ranges})
                bar.update(right - left)

    def query(self, spec, text, dimension):
        request = self.output_spec(spec, dimension)
        return unit_vectors(self.encode(request, [text], "query"), dimension)[0]
