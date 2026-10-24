from __future__ import annotations

import numpy as np


def unit_vectors(values, dimension=None):
    matrix = np.asarray(values, dtype=np.float32)
    if matrix.ndim != 2 or (dimension is not None and dimension > matrix.shape[1]):
        raise ValueError("Forma de embeddings no válida.")
    matrix = matrix[:, :dimension] if dimension else matrix
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if not np.isfinite(matrix).all() or np.any(norms == 0):
        raise ValueError("El proveedor devolvió un vector nulo o no finito.")
    return matrix / norms
