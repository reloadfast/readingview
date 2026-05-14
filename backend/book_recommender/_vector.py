"""Vector similarity search backends."""

import logging
import math
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class VectorBackend(Protocol):
    """Interface for vector similarity search."""

    def build(self, ids: list[str], vectors: list[list[float]]) -> None: ...
    def search(self, query: list[float], top_k: int) -> list[tuple[str, float]]: ...


def _l2_norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _normalize(v: list[float]) -> list[float]:
    norm = _l2_norm(v)
    if norm == 0.0:
        return v
    return [x / norm for x in v]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class PythonCosineBackend:
    """Pure-Python cosine similarity (no external dependencies)."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._normed: list[list[float]] = []

    def build(self, ids: list[str], vectors: list[list[float]]) -> None:
        self._ids = list(ids)
        self._normed = [_normalize(v) for v in vectors]

    def search(self, query: list[float], top_k: int) -> list[tuple[str, float]]:
        if not self._ids:
            return []
        q = _normalize(query)
        if _l2_norm(q) == 0.0:
            return []
        scores = [_dot(q, row) for row in self._normed]
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self._ids[i], scores[i]) for i in top_indices]


class FAISSBackend:
    """FAISS-based vector similarity using IndexFlatIP on L2-normalized vectors."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._index: Any = None
        self._dim: int = 0

    def build(self, ids: list[str], vectors: list[list[float]]) -> None:
        import faiss  # type: ignore[import-not-found]
        import numpy as np

        self._ids = list(ids)
        if not vectors:
            self._dim = 0
            self._index = None
            return
        mat = np.array(vectors, dtype=np.float32)
        # Normalize for cosine similarity via inner product
        faiss.normalize_L2(mat)
        self._dim = mat.shape[1]
        self._index = faiss.IndexFlatIP(self._dim)
        self._index.add(mat)

    def search(self, query: list[float], top_k: int) -> list[tuple[str, float]]:
        import faiss  # type: ignore[import-not-found]
        import numpy as np

        if self._index is None or len(self._ids) == 0:
            return []
        q = np.array([query], dtype=np.float32)
        faiss.normalize_L2(q)
        k = min(top_k, len(self._ids))
        scores, indices = self._index.search(q, k)
        results = []
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx >= 0:
                results.append((self._ids[idx], float(score)))
        return results


def create_backend(name: str) -> VectorBackend:
    """Create a vector backend by name. Falls back to Python if FAISS unavailable."""
    if name == "faiss":
        try:
            import faiss  # type: ignore[import-not-found]  # noqa: F401

            return FAISSBackend()
        except ImportError:
            logger.warning("faiss not installed, falling back to Python cosine backend")
            return PythonCosineBackend()
    return PythonCosineBackend()
