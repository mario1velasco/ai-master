from __future__ import annotations

import os
import platform
from pathlib import Path
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
import numpy as np
import pandas as pd
from retrieval_lab.configuration.settings import PROTOCOL_VERSION
from retrieval_lab.infrastructure.artifacts import write_json


def configure(config):
    from dotenv import load_dotenv

    load_dotenv(Path(".env"), override=False)
    for child in ("embeddings", "indexes", "results"):
        (config.artifacts_dir / child).mkdir(parents=True, exist_ok=True)
    np.random.seed(config.random_seed)
    packages = {}
    for name in ("numpy", "pandas", "pinecone", "google-genai", "langchain-core",
                 "langchain-openai", "langchain-huggingface", "sentence-transformers"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = "no instalado"
    manifest = {"protocolo": PROTOCOL_VERSION, "python": platform.python_version(),
                "config": asdict(config), "paquetes": packages}
    write_json(config.results_dir / "environment.json", manifest)
    return pd.DataFrame([{"Python": platform.python_version(), "Semilla": config.random_seed,
                          "Corpus": str(config.data_dir), "Artefactos": str(config.artifacts_dir)}])


def check_credentials(config):
    required = ["PINECONE_API_KEY"]
    for provider, key in (("openai", "OPENAI_API_KEY"), ("gemini", "GEMINI_API_KEY")):
        if any(m.provider == provider for m in config.active_models):
            required.append(key)
    missing = [key for key in required if not os.getenv(key, "").strip()]
    if missing:
        raise RuntimeError("Completa .env a partir de .env.example. Faltan: " + ", ".join(missing))
    return pd.DataFrame({"Variable": required, "Estado": ["configurada; valor oculto"] * len(required)})
