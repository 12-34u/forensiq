"""Page model – the atomic unit of content that flows into Vector RAG and Graph RAG."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from pydantic import BaseModel, Field


class Page(BaseModel):
    """A single indexed page representing a logical chunk of forensic content.

    Pages are the bridge between raw UFDR artefacts and downstream RAGs:
    * **Vector RAG** – each page is embedded for semantic search.
    * **Graph RAG** – entities are extracted from each page for the Neo4j graph.
    """

    page_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    extraction_id: str = ""          # links back to the source UFDR
    artifact_type: str = ""          # e.g. "contact", "chat_message"
    source_section: str = ""         # human-readable section heading
    page_number: int = 0             # sequential within extraction

    # ── Content ───────────────────────────────────────
    title: str = ""                  # short summary line
    body: str = ""                   # full text for embedding
    token_count: int = 0

    # ── Metadata ──────────────────────────────────────
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ── Downstream state (set after processing) ──────
    embedding: list[float] | None = None
    entities: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def content_hash(self) -> str:
        """SHA-256 of the body for deduplication."""
        return hashlib.sha256(self.body.encode()).hexdigest()

    def to_embed_text(self) -> str:
        """Build the string that will be sent to the embedding model."""
        parts = []
        if self.title:
            parts.append(f"[{self.artifact_type.upper()}] {self.title}")
        if self.body:
            parts.append(self.body)
        return "\n".join(parts)

    def summary_line(self) -> str:
        """One-line summary for logs / UI."""
        preview = (self.body[:80] + "…") if len(self.body) > 80 else self.body
        return f"Page #{self.page_number} ({self.artifact_type}): {preview}"
