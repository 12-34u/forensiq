"""Gemini embedding client – wraps the text-embedding-004 model."""

from __future__ import annotations

import logging
import time
from typing import Sequence

import numpy as np
from google import genai

from config.settings import settings

logger = logging.getLogger(__name__)


class Embedder:
    """Thin wrapper around the Google GenAI embeddings endpoint."""

    def __init__(
        self,
        model: str | None = None,
        dimensions: int | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or settings.embedding_model
        self.dimensions = dimensions or settings.embedding_dimensions
        self._client = genai.Client(api_key=api_key or settings.gemini_api_key)

    # ── single text ───────────────────────────────────

    def embed(self, text: str) -> np.ndarray:
        resp = self._client.models.embed_content(
            model=self.model,
            contents=text,
        )
        return np.array(resp.embeddings[0].values, dtype=np.float32)

    # ── batch ─────────────────────────────────────────

    def embed_batch(self, texts: Sequence[str], *, batch_size: int = 64) -> np.ndarray:
        """Embed a list of texts, automatically batching to stay within limits.

        Returns an ``(N, dim)`` float32 numpy array.
        """
        all_vecs: list[np.ndarray] = []
        for start in range(0, len(texts), batch_size):
            chunk = list(texts[start : start + batch_size])
            resp = self._client.models.embed_content(
                model=self.model,
                contents=chunk,
            )
            vecs = [np.array(e.values, dtype=np.float32) for e in resp.embeddings]
            all_vecs.extend(vecs)
            logger.debug("Embedded batch %d–%d", start, start + len(chunk))
            if start + batch_size < len(texts):
                time.sleep(0.1)  # gentle rate-limit courtesy
        return np.vstack(all_vecs)
