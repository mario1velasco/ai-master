from __future__ import annotations

import json
import os
import re
import time
import numpy as np
import pandas as pd
from retrieval_lab.infrastructure.artifacts import fingerprint, write_json
from retrieval_lab.infrastructure.rate_limits import transient_retry


def as_mapping(value):
    return value.to_dict() if hasattr(value, "to_dict") else value


class PineconeWorkspace:
    def __init__(self, config):
        from pinecone import Pinecone

        self.config = config
        self.client = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        self.prefix = os.getenv("PINECONE_INDEX_PREFIX", "trec-eval")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,25}", self.prefix):
            raise ValueError("PINECONE_INDEX_PREFIX: 1–26 caracteres a-z, 0-9 o guion.")
        self.cloud = os.getenv("PINECONE_CLOUD", "aws")
        self.region = os.getenv("PINECONE_REGION", "us-east-1")
        self.indexes = {}
        self.locations = {}
        from retrieval_lab.infrastructure.rate_limits import RequestLimiter
        self.upload_limiter = RequestLimiter()

    def index(self, dimension, create=True):
        from pinecone import ServerlessSpec

        name = f"{self.prefix}-d{dimension}" if dimension else f"{self.prefix}-sparse"
        if name in self.indexes:
            return self.indexes[name]
        if not self.client.has_index(name):
            if not create:
                raise RuntimeError(f"No existe el índice {name}. La verificación no crea recursos.")
            kwargs = {"dimension": dimension} if dimension else {}
            self.client.create_index(name=name, vector_type="dense" if dimension else "sparse",
                                     metric="cosine" if dimension else "dotproduct",
                                     spec=ServerlessSpec(cloud=self.cloud, region=self.region),
                                     deletion_protection="enabled", **kwargs)
        deadline = time.monotonic() + self.config.readiness_timeout_s
        while time.monotonic() < deadline:
            description = as_mapping(self.client.describe_index(name))
            if description["status"]["ready"]:
                break
            time.sleep(3)
        else:
            raise TimeoutError(f"{name} todavía no está listo; vuelva a ejecutar esta celda.")
        self._validate_index(description, dimension)
        index = self.client.Index(host=description["host"])
        self.indexes[name] = index
        return index

    def _validate_index(self, description, dimension):
        expected = "cosine" if dimension else "dotproduct"
        actual_dimension = description.get("dimension") or 0
        if description.get("metric") != expected or actual_dimension != dimension:
            raise ValueError("Índice existente incompatible. Use otro prefijo; no se borra ni sobrescribe.")
        deployment = description.get("spec", {}).get("serverless", {})
        if deployment.get("cloud") != self.cloud or deployment.get("region") != self.region:
            raise ValueError("La región existente no coincide. Todos los brazos deben usar la misma región.")

    def count(self, index, namespace):
        stats = as_mapping(index.describe_index_stats())
        return stats.get("namespaces", {}).get(namespace, {}).get("vector_count", 0)

    def upload(self, key, dimension, signature, ids, corpus, record_values, verify_only=False):
        from tqdm.auto import tqdm

        index = self.index(dimension, create=not verify_only)
        namespace = f"{key}-{signature[:16]}"
        location = {"index": f"{self.prefix}-d{dimension}" if dimension else f"{self.prefix}-sparse",
                    "namespace": namespace, "dimension": dimension, "expected": len(ids),
                    "signature": signature, "host": index.config.host}
        self.locations[(key, dimension)] = location
        observed_count = self.count(index, namespace)
        if observed_count > len(ids):
            raise ValueError("El namespace contiene más IDs de los esperados. No se reutiliza.")
        marker = self.config.artifacts_dir / "indexes" / f"upload-{fingerprint(location)[:16]}.json"
        if verify_only or observed_count == len(ids):
            if observed_count != len(ids):
                raise RuntimeError(
                    f"Verificación sin escrituras: {namespace} contiene {observed_count:,} de "
                    f"{len(ids):,} registros esperados. Espere y vuelva a verificar; no se ha cargado nada.")
            self._verify_samples(index, namespace, ids, record_values, dimension, signature)
            write_json(marker, location)
            print(f"Pinecone: {key}/{dimension}, namespace existente verificado.")
            return
        size = self.config.upsert_batch_size

        def upload_batch(start):
            records = [{"id": ids[row], **record_values(row),
                        "metadata": {"document_id": ids[row], "title": corpus[ids[row]]["title"][:500],
                                     "text_preview": corpus[ids[row]]["text"][:700],
                                     "model": key, "signature": signature}}
                       for row in range(start, min(start + size, len(ids)))]
            self._upsert_bounded(index, namespace, records)
            return len(records)

        from retrieval_lab.infrastructure.concurrency import bounded_results
        with tqdm(total=len(ids), desc=f"Pinecone · {key}/{dimension}", unit="doc") as bar:
            for count in bounded_results(upload_batch, range(0, len(ids), size),
                                         self.config.upsert_concurrency):
                bar.update(count)
        deadline = time.monotonic() + self.config.readiness_timeout_s
        while self.count(index, namespace) != len(ids):
            if time.monotonic() >= deadline:
                raise TimeoutError("La indexación aún no es visible. Reejecute la celda; el upsert es idempotente.")
            time.sleep(3)
        self._verify_samples(index, namespace, ids, record_values, dimension, signature)
        write_json(marker, location)

    def _upsert_bounded(self, index, namespace, records):
        payload_bytes = len(json.dumps({"vectors": records, "namespace": namespace}).encode("utf-8"))
        if payload_bytes > 1_800_000:
            if len(records) == 1:
                raise ValueError("Un registro excede el límite seguro de tamaño de petición.")
            middle = len(records) // 2
            self._upsert_bounded(index, namespace, records[:middle])
            self._upsert_bounded(index, namespace, records[middle:])
            return
        transient_retry(lambda: index.upsert(vectors=records, namespace=namespace),
                        self.upload_limiter)

    def _fetch_visible_samples(self, index, namespace, sample_ids):
        deadline = time.monotonic() + self.config.readiness_timeout_s
        while True:
            response = transient_retry(lambda: index.fetch(ids=sample_ids, namespace=namespace))
            fetched = as_mapping(response).get("vectors", {})
            missing = [doc_id for doc_id in sample_ids if doc_id not in fetched]
            if not missing:
                return fetched
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"No se pudieron verificar los IDs {missing} en el namespace {namespace}. "
                    "El recuento no garantiza su disponibilidad en fetch. "
                    "No se ha confirmado la integridad de la muestra; esta comprobación no escribe registros. "
                    "Reintente con prepare_lexical(verify_only=True) para BM25; "
                    "si persiste, revise esos IDs y el namespace antes de cargar de nuevo.")
            time.sleep(min(3.0, remaining))

    def _verify_samples(self, index, namespace, ids, values, dimension, signature=None):
        positions = sorted({0, len(ids) // 2, len(ids) - 1})
        fetched = self._fetch_visible_samples(index, namespace, [ids[i] for i in positions])
        for row in positions:
            actual, expected = as_mapping(fetched[ids[row]]), values(row)
            if signature is not None and actual.get("metadata", {}).get("signature") != signature:
                raise ValueError(f"La firma del registro {ids[row]} no coincide. No se reutiliza el namespace.")
            if dimension:
                if not np.allclose(actual["values"], expected["values"], atol=1e-5):
                    raise ValueError("La muestra remota no coincide con los embeddings locales.")
            else:
                actual_sparse = actual.get("sparse_values", actual.get("sparseValues"))
                a = dict(zip(actual_sparse["indices"], actual_sparse["values"]))
                e = dict(zip(expected["sparse_values"]["indices"], expected["sparse_values"]["values"]))
                if set(a) != set(e) or any(not np.isclose(a[k], e[k], atol=1e-5) for k in e):
                    raise ValueError("La muestra sparse remota no coincide.")

    def search(self, key, dimension, depth, vector=None, sparse_vector=None):
        location = self.locations[(key, dimension)]
        index = self.index(dimension)
        kwargs = {"vector": vector} if vector is not None else {"sparse_vector": sparse_vector}
        response = as_mapping(transient_retry(lambda: index.query(
            namespace=location["namespace"], top_k=depth, include_metadata=False,
            include_values=False, **kwargs)))
        ranking = [(str(m["id"]), float(m["score"])) for m in response.get("matches", [])]
        return ranking, response.get("usage", {}).get("read_units")

    def inventory(self):
        rows = []
        for (key, dim), location in self.locations.items():
            rows.append({"Modelo": key, "Dimensiones": dim, "Índice": location["index"],
                         "Namespace": location["namespace"], "Vectores esperados": location["expected"],
                         "Vectores visibles": self.count(self.index(dim), location["namespace"])})
        return pd.DataFrame(rows)
