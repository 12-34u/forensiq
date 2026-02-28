"""Vector RAG retriever – embeds a query and returns matching pages."""

from __future__ import annotations

import logging

from forensiq.pageindex.page import Page
from forensiq.pageindex.store import PageStore
from forensiq.vectorrag.embedder import Embedder
from forensiq.vectorrag.faiss_store import FAISSStore

logger = logging.getLogger(__name__)


class VectorRetriever:
    """High-level semantic search over the PageIndex.

    Workflow
    --------
    1. ``index_pages(pages)`` – embed all pages and add to FAISS.
    2. ``query(text, k)``     – embed query, search FAISS, return Page objects.
    """

    def __init__(
        self,
        embedder: Embedder | None = None,
        store: FAISSStore | None = None,
        page_store: PageStore | None = None,
    ) -> None:
        self.embedder = embedder or Embedder()
        self.store = store or FAISSStore()
        self.page_store = page_store or PageStore()
        self._id_to_page: dict[str, Page] = {}

    # ── indexing ──────────────────────────────────────

    def index_pages(self, pages: list[Page]) -> int:
        """Embed *pages* and add them to the FAISS index. Returns count added."""
        if not pages:
            return 0

        texts = [p.to_embed_text() for p in pages]
        vectors = self.embedder.embed_batch(texts)

        page_ids = [p.page_id for p in pages]
        self.store.add(page_ids, vectors)
        self.store.save()

        # Cache for quick lookup after search
        for p in pages:
            self._id_to_page[p.page_id] = p

        logger.info("Indexed %d pages into FAISS (total: %d)", len(pages), self.store.size)
        return len(pages)

    # ── search ────────────────────────────────────────

    def query(self, text: str, k: int = 10) -> list[tuple[Page, float]]:
        """Semantic search: embed *text* and return top-*k* pages with scores."""
        qvec = self.embedder.embed(text)
        hits = self.store.search(qvec, k=k)

        results: list[tuple[Page, float]] = []
        for page_id, score in hits:
            page = self._id_to_page.get(page_id)
            if page is None:
                # Try loading from disk
                for p in self.page_store.load_all_pages():
                    self._id_to_page[p.page_id] = p
                page = self._id_to_page.get(page_id)
            if page:
                results.append((page, score))
        return results

    # ── utility ───────────────────────────────────────

    def rebuild_cache(self) -> None:
        """Reload the page ID → Page mapping from disk."""
        self._id_to_page.clear()
        for page in self.page_store.load_all_pages():
            self._id_to_page[page.page_id] = page
        logger.info("Rebuilt in-memory cache: %d pages", len(self._id_to_page))
