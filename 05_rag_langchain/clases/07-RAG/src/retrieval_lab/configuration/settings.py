from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROTOCOL_VERSION = "pinecone-v1"


@dataclass(frozen=True)
class ModelSpec:
    key: str
    provider: str
    name: str
    native_dimension: int
    dimensions: tuple[int, ...]
    revision: str = "main"


DEFAULT_MODELS = (
    ModelSpec("openai-large", "openai", "text-embedding-3-large", 3072, (256, 512, 768)),
)


QWEN = ModelSpec("qwen-06b", "huggingface", "Qwen/Qwen3-Embedding-0.6B", 1024, (256, 512, 768))


@dataclass(frozen=True)
class ExperimentConfig:
    random_seed: int = 42
    data_dir: Path = Path("data")
    artifacts_dir: Path = Path("artifacts/pinecone_v1")
    models: tuple[ModelSpec, ...] = DEFAULT_MODELS
    include_qwen: bool = False
    candidate_depths: tuple[int, ...] = (20, 50, 100)
    comparison_depth: int = 50
    reference_dimension: int = 768
    final_k: int = 10
    evaluation_query_count: int = 20
    text_max_bytes: int = 6000
    embedding_batch_size: int = 64
    embedding_concurrency: int = 4
    embedding_batch_token_limit: int = 250000
    provider_concurrency: int = 2
    upsert_batch_size: int = 200
    upsert_concurrency: int = 4
    rrf_constant: int = 60
    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    bootstrap_iterations: int = 3000
    latency_repetitions: int = 2
    latency_budget_ms: float = 1500.0
    quality_tolerance: float = 0.01
    readiness_timeout_s: float = 300.0

    def __post_init__(self):
        if self.final_k != 10 or self.comparison_depth not in self.candidate_depths:
            raise ValueError("El protocolo requiere final_k=10 y una profundidad de referencia incluida.")
        if any(k < self.final_k or k > 1000 for k in self.candidate_depths):
            raise ValueError("Las profundidades deben estar entre 10 y 1000.")
        if not 1 <= self.text_max_bytes <= 6000:
            raise ValueError("El límite común de texto debe estar entre 1 y 6000 bytes UTF-8.")
        if not 1 <= self.embedding_batch_size <= 100 or not 1 <= self.upsert_batch_size <= 1000:
            raise ValueError("Lotes: embeddings 1–100; upsert 1–1000.")
        if any(not 1 <= n <= 16 for n in (self.embedding_concurrency, self.upsert_concurrency,
                                         self.provider_concurrency)):
            raise ValueError("La concurrencia debe estar entre 1 y 16.")
        if not 1 <= self.embedding_batch_token_limit <= 250000:
            raise ValueError("El límite de tokens por lote debe estar entre 1 y 250000.")
        if self.latency_repetitions < 2 or self.bootstrap_iterations < 100:
            raise ValueError("Se requieren al menos dos repeticiones y 100 réplicas bootstrap.")
        for model in self.active_models:
            if self.reference_dimension not in model.dimensions:
                raise ValueError("Cada modelo debe incluir la dimensión común de comparación.")
            if any(d < 1 or d > model.native_dimension for d in model.dimensions):
                raise ValueError("Dimensiones incompatibles con el modelo.")

    @property
    def active_models(self):
        return self.models + ((QWEN,) if self.include_qwen else ())

    @property
    def results_dir(self):
        return self.artifacts_dir / "results"
