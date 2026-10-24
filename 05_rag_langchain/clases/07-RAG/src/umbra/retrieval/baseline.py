import json
from functools import cached_property


class Baseline:
    def __init__(self, settings):
        self.path = settings.session06 / "artifacts/pinecone_v1/results/frozen_decision.json"
        self.payload = json.loads(self.path.read_text())
        self.candidate = self.payload["candidate"]
        if self.candidate["strategy"] != "hibrida" or self.candidate["depth"] != 100:
            raise ValueError("La decisión guardada no es híbrida con 100 candidatos. Revisa el cierre de Sesión 06.")
        models = self.payload["config"]["models"]
        self.model = next(m for m in models if m["key"] == self.candidate["model"])
        if self.model["provider"] != "openai":
            raise ValueError("Esta continuación está preparada para el candidato OpenAI.")

    def location(self, sparse=False):
        key = "bm25" if sparse else self.candidate["model"]
        dimension = 0 if sparse else self.candidate["dimension"]
        return next(r for r in self.payload["remote"]
                    if r["Modelo"] == key and r["Dimensiones"] == dimension)

    def summary(self):
        return {"model": self.model["name"], **self.candidate,
                "dense_index": self.location()["Índice"], "sparse_index": self.location(True)["Índice"]}
