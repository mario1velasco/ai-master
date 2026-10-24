from __future__ import annotations

import numpy as np


def paired_bootstrap(a, b, iterations=3000, seed=42):
    if set(a.index) != set(b.index) or len(a) < 2:
        raise ValueError("La comparación exige los mismos IDs y al menos dos consultas.")
    delta = (b.reindex(a.index) - a).to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    samples = delta[rng.integers(0, len(delta), (iterations, len(delta)))].mean(axis=1)
    return {"Delta B−A": float(delta.mean()), "IC95 inferior": float(np.quantile(samples, .025)),
            "IC95 superior": float(np.quantile(samples, .975)), "Consultas": len(delta)}
