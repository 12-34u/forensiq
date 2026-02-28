"""FAISS index wrapper – stores and searches page embeddings."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import faiss
import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)

_META_FILENAME = "page_ids.json"
_INDEX_FILENAME = "index.faiss"


class FAISSStore:
    """Manages a FAISS flat-IP index alongside a page-ID mapping.

    The mapping ``_page_ids[i]`` gives the ``page_id`` that corresponds to
    vector row *i* in the FAISS index.
    """

    def __init__(self, index_dir: Path | None = None, dimension: int | None = None) -> None:
        self.index_dir = index_dir or settings.faiss_index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension or settings.embedding_dimensions

        self._index: faiss.IndexFlatIP | None = None
        self._page_ids: list[str] = []

        self._load_or_create()

    # ── persistence ───────────────────────────────────

    def _index_path(self) -> Path:
        return self.index_dir / _INDEX_FILENAME

    def _meta_path(self) -> Path:
        return self.index_dir / _META_FILENAME

    def _load_or_create(self) -> None:
        if self._index_path().exists() and self._meta_path().exists():
            logger.info("Loading existing FAISS index from %s", self.index_dir)
            self._index = faiss.read_index(str(self._index_path()))
            with self._meta_path().open() as f:
                self._page_ids = json.load(f)
        else:
            logger.info("Creating new FAISS index (dim=%d)", self.dimension)
            self._index = faiss.IndexFlatIP(self.dimension)
            self._page_ids = []

    def save(self) -> None:
        """Write index + metadata to disk."""
        faiss.write_index(self._index, str(self._index_path()))
        with self._meta_path().open("w") as f:
            json.dump(self._page_ids, f)
        logger.info("FAISS index saved (%d vectors)", self._index.ntotal)

    # ── add ───────────────────────────────────────────

    def add(self, page_ids: list[str], vectors: np.ndarray) -> None:
        """Add vectors to the index. ``vectors`` shape must be ``(N, dim)``."""
        assert vectors.ndim == 2 and vectors.shape[1] == self.dimension
        # L2-normalise so inner-product ≈ cosine similarity
        faiss.normalize_L2(vectors)
        self._index.add(vectors)
        self._page_ids.extend(page_ids)

    # ── search ────────────────────────────────────────

    def search(self, query_vec: np.ndarray, k: int = 10) -> list[tuple[str, float]]:
        """Return the top-*k* ``(page_id, score)`` pairs."""
        if self._index.ntotal == 0:
            return []
        qv = query_vec.reshape(1, -1).copy()
        faiss.normalize_L2(qv)
        scores, indices = self._index.search(qv, min(k, self._index.ntotal))
        results: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append((self._page_ids[idx], float(score)))
        return results

    # ── info ──────────────────────────────────────────

    @property
    def size(self) -> int:
        return self._index.ntotal if self._index else 0

    def clear(self) -> None:
        """Reset the index."""
        self._index = faiss.IndexFlatIP(self.dimension)
        self._page_ids = []
        self.save()
