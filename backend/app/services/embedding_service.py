from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import numpy as np

from app.logging_config import get_logger

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = get_logger(__name__)

_MODEL: SentenceTransformer | None = None
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", _MODEL_NAME)
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


class EmbeddingService:
    """Local embedding generation with in-memory cache for a single analysis run."""

    def __init__(self) -> None:
        self._cache: dict[str, list[float]] = {}

    def _cache_key(self, normalized_source: str) -> str:
        return hashlib.sha256(normalized_source.encode("utf-8")).hexdigest()

    def embed(self, normalized_source: str) -> list[float]:
        key = self._cache_key(normalized_source)
        if key in self._cache:
            return self._cache[key]

        model = _get_model()
        vector = model.encode(normalized_source, normalize_embeddings=True)
        embedding = vector.tolist()
        self._cache[key] = embedding
        return embedding

    def embed_batch(self, normalized_sources: list[str]) -> list[list[float]]:
        uncached: list[tuple[int, str, str]] = []
        results: list[list[float] | None] = [None] * len(normalized_sources)

        for index, source in enumerate(normalized_sources):
            key = self._cache_key(source)
            if key in self._cache:
                results[index] = self._cache[key]
            else:
                uncached.append((index, key, source))

        if uncached:
            model = _get_model()
            texts = [item[2] for item in uncached]
            vectors = model.encode(texts, normalize_embeddings=True, batch_size=32)
            for (index, key, _), vector in zip(uncached, vectors, strict=True):
                embedding = vector.tolist()
                self._cache[key] = embedding
                results[index] = embedding

        return [item for item in results if item is not None]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        va = np.asarray(a, dtype=np.float32)
        vb = np.asarray(b, dtype=np.float32)
        dot = float(np.dot(va, vb))
        return max(0.0, min(1.0, dot))

    @property
    def cache_size(self) -> int:
        return len(self._cache)
