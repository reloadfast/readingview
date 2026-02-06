"""Vector similarity search backends."""

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class VectorBackend(Protocol):
    """Interface for vector similarity search."""

    def build(self, ids: list[str], vectors: list[list[float]]) -> None: ...
    def search(self, query: list[float], top_k: int) -> list[tuple[str, float]]: ...


class PythonCosineBackend:
    """Pure-Python cosine similarity using numpy."""

    def __init__(self):
        self._ids: list[str] = []
        self._matrix = None  # numpy array, lazily typed

    def build(self, ids: list[str], vectors: list[list[float]]) -> None:
        import numpy as np

        self._ids = list(ids)
        if not vectors:
            self._matrix = np.empty((0, 0), dtype=np.float32)
            return
        mat = np.array(vectors, dtype=np.float32)
        # Pre-normalize rows for cosine similarity via dot product
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._matrix = mat / norms

    def search(self, query: list[float], top_k: int) -> list[tuple[str, float]]:
        import numpy as np

        if self._matrix is None or len(self._ids) == 0:
            return []
        q = np.array(query, dtype=np.float32)
        norm = np.linalg.norm(q)
        if norm == 0:
            return []
        q = q / norm
        scores = self._matrix @ q
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self._ids[i], float(scores[i])) for i in top_indices]


class FAISSBackend:
    """FAISS-based vector similarity using IndexFlatIP on L2-normalized vectors."""

    def __init__(self):
        self._ids: list[str] = []
        self._index = None
        self._dim: int = 0

    def build(self, ids: list[str], vectors: list[list[float]]) -> None:
        import faiss
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
        import faiss
        import numpy as np

        if self._index is None or len(self._ids) == 0:
            return []
        q = np.array([query], dtype=np.float32)
        faiss.normalize_L2(q)
        k = min(top_k, len(self._ids))
        scores, indices = self._index.search(q, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append((self._ids[idx], float(score)))
        return results


def create_backend(name: str) -> VectorBackend:
    """Create a vector backend by name. Falls back to Python if FAISS unavailable."""
    if name == "faiss":
        try:
            import faiss  # noqa: F401
            return FAISSBackend()
        except ImportError:
            logger.warning("faiss not installed, falling back to Python cosine backend")
            return PythonCosineBackend()
    return PythonCosineBackend()
