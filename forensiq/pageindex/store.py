"""Persistent page store – keeps the PageIndex on disk as JSON-lines.

This acts as the single source of truth for all pages. Both Vector RAG and
Graph RAG consume pages from this store.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from config.settings import settings
from forensiq.pageindex.page import Page

logger = logging.getLogger(__name__)


class PageStore:
    """JSON-lines–backed page storage.

    Each extraction gets its own ``.jsonl`` file inside ``PAGEINDEX_STORE_DIR``.
    """

    def __init__(self, store_dir: Path | None = None) -> None:
        self.store_dir = store_dir or settings.pageindex_store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)

    # ── helpers ────────────────────────────────────────

    def _file_for(self, extraction_id: str) -> Path:
        return self.store_dir / f"{extraction_id}.jsonl"

    # ── write ─────────────────────────────────────────

    def save_pages(self, pages: list[Page]) -> Path | None:
        """Persist *pages* to disk. All pages must share the same ``extraction_id``."""
        if not pages:
            return None
        ext_id = pages[0].extraction_id
        out = self._file_for(ext_id)
        with out.open("w", encoding="utf-8") as f:
            for page in pages:
                f.write(page.model_dump_json(exclude={"embedding"}) + "\n")
        logger.info("Saved %d pages to %s", len(pages), out)
        return out

    # ── read ──────────────────────────────────────────

    def load_pages(self, extraction_id: str) -> list[Page]:
        """Load all pages for a given extraction."""
        fp = self._file_for(extraction_id)
        if not fp.exists():
            return []
        pages: list[Page] = []
        with fp.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    pages.append(Page.model_validate_json(line))
        return pages

    def load_all_pages(self) -> list[Page]:
        """Load pages from every extraction in the store."""
        pages: list[Page] = []
        for fp in sorted(self.store_dir.glob("*.jsonl")):
            with fp.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        pages.append(Page.model_validate_json(line))
        return pages

    def list_extractions(self) -> list[str]:
        """Return extraction IDs that have stored pages."""
        return [fp.stem for fp in sorted(self.store_dir.glob("*.jsonl"))]

    # ── delete ────────────────────────────────────────

    def delete_extraction(self, extraction_id: str) -> bool:
        fp = self._file_for(extraction_id)
        if fp.exists():
            fp.unlink()
            logger.info("Deleted page store for extraction %s", extraction_id)
            return True
        return False
