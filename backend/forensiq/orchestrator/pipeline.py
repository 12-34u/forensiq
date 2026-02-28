"""Orchestration pipeline – ties together UFDR parsing, PageIndex, Vector RAG,
Graph RAG, LLM generation (Gemini / OpenRouter), and Redis caching into a
single ingest + query workflow.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forensiq.cache.redis_cache import ResponseCache
from forensiq.graphrag.extractor import populate_graph
from forensiq.graphrag.neo4j_client import Neo4jClient
from forensiq.llm.client import ForensIQLLM
from forensiq.pageindex.indexer import index_extraction
from forensiq.pageindex.page import Page
from forensiq.pageindex.store import PageStore
from forensiq.ufdr.parser import parse_ufdr
from forensiq.vectorrag.embedder import Embedder
from forensiq.vectorrag.faiss_store import FAISSStore
from forensiq.vectorrag.retriever import VectorRetriever

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Summary returned after ingesting a UFDR source."""
    extraction_id: str = ""
    source_path: str = ""
    total_artifacts: int = 0
    total_pages: int = 0
    vector_indexed: int = 0
    graph_entities: int = 0
    graph_relationships: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Combined result from Vector RAG + Graph RAG + LLM."""
    query: str = ""
    answer: str = ""
    source: str = ""  # "gemini" | "cache+openrouter" | "cache" | "rag_only"
    vector_hits: list[dict[str, Any]] = field(default_factory=list)
    graph_context: list[dict[str, Any]] = field(default_factory=list)
    cache_key: str = ""


class ForensIQPipeline:
    """Top-level orchestrator.

    Usage::

        pipeline = ForensIQPipeline()
        result = pipeline.ingest("/path/to/case.ufdr")
        answer = pipeline.query("Who called +1-555-0199?")
    """

    def __init__(
        self,
        *,
        page_store: PageStore | None = None,
        embedder: Embedder | None = None,
        faiss_store: FAISSStore | None = None,
        neo4j_client: Neo4jClient | None = None,
        llm: ForensIQLLM | None = None,
        cache: ResponseCache | None = None,
    ) -> None:
        from config.settings import settings

        self.page_store = page_store or PageStore()
        self._embedder = embedder or Embedder()
        self._faiss = faiss_store or FAISSStore()
        self._neo4j: Neo4jClient | None = neo4j_client
        self._retriever = VectorRetriever(
            embedder=self._embedder,
            store=self._faiss,
            page_store=self.page_store,
        )
        self._llm = llm or ForensIQLLM(
            gemini_api_key=settings.gemini_api_key,
            openrouter_api_key=settings.openrouter_api_key,
            gemini_model=settings.gemini_model,
            openrouter_model=settings.openrouter_model,
        )
        self._cache = cache or ResponseCache(
            redis_url=settings.redis_url,
            ttl=settings.cache_ttl,
        )

    # ── lazy Neo4j (so app can start without it) ─────

    @property
    def neo4j(self) -> Neo4jClient:
        if self._neo4j is None:
            self._neo4j = Neo4jClient()
        return self._neo4j

    # ── ingest ────────────────────────────────────────

    def ingest(self, source: str | Path, *, skip_graph: bool = False) -> IngestResult:
        """Full ingest pipeline: UFDR → PageIndex → Vector RAG → Graph RAG."""
        result = IngestResult(source_path=str(source))

        # 1. Parse UFDR
        logger.info("▸ Parsing UFDR source: %s", source)
        extraction = parse_ufdr(source)
        result.total_artifacts = extraction.total_artifacts

        # 2. Build pages
        logger.info("▸ Building PageIndex …")
        pages = index_extraction(extraction)
        result.total_pages = len(pages)
        if not pages:
            result.errors.append("No pages generated from extraction")
            return result
        result.extraction_id = pages[0].extraction_id

        # 3. Persist pages
        self.page_store.save_pages(pages)

        # 4. Vector RAG — embed & index
        logger.info("▸ Embedding %d pages for Vector RAG …", len(pages))
        try:
            result.vector_indexed = self._retriever.index_pages(pages)
        except Exception as exc:
            logger.error("Vector indexing failed: %s", exc)
            result.errors.append(f"Vector indexing error: {exc}")

        # 5. Graph RAG — extract entities & build graph
        if not skip_graph:
            logger.info("▸ Populating Neo4j knowledge graph …")
            try:
                stats = populate_graph(self.neo4j, pages)
                result.graph_entities = stats["entities"]
                result.graph_relationships = stats["relationships"]
            except Exception as exc:
                logger.error("Graph population failed: %s", exc)
                result.errors.append(f"Graph error: {exc}")

        logger.info("✓ Ingest complete – %d pages, %d vectors, %d entities",
                     result.total_pages, result.vector_indexed, result.graph_entities)
        return result

    # ── query ─────────────────────────────────────────

    def query(
        self,
        text: str,
        *,
        k: int = 10,
        graph_depth: int = 2,
        include_graph: bool = True,
        skip_cache: bool = False,
        skip_llm: bool = False,
    ) -> QueryResult:
        """Full query pipeline: cache check → RAG retrieval → LLM → cache store.

        Flow:
        1. Check Redis cache for this prompt's keywords.
        2a. If **hit** → reframe cached answer via OpenRouter (cheap/free).
        2b. If **miss** → run Vector RAG + Graph RAG → build context →
            send to Gemini → cache the answer in Redis.
        """
        qr = QueryResult(query=text)

        # ── Step 1: Check cache ──────────────────────────
        if not skip_cache:
            cached = self._cache.lookup(text)
            if cached:
                qr.cache_key = cached.get("cache_key", "")
                qr.source = "cache+openrouter"
                if skip_llm:
                    qr.answer = cached["response"]
                    qr.source = "cache"
                else:
                    qr.answer = self._llm.reframe(text, cached["response"])
                return qr

        # ── Step 2: Vector RAG retrieval ─────────────────
        hits: list = []
        try:
            hits = self._retriever.query(text, k=k)
            for page, score in hits:
                qr.vector_hits.append({
                    "page_id": page.page_id,
                    "score": round(score, 4),
                    "artifact_type": page.artifact_type,
                    "title": page.title,
                    "body": page.body,
                    "metadata": page.metadata,
                })
        except Exception as exc:
            logger.warning("Vector RAG unavailable (likely no OPENAI_API_KEY): %s", exc)

        # ── Step 3: Graph RAG expansion ──────────────────
        if include_graph and hits:
            try:
                seen_keys: set[str] = set()
                for page, _ in hits[:3]:
                    from forensiq.graphrag.extractor import extract_entities
                    entities = extract_entities(page)
                    for ent in entities:
                        key = f"{ent['label']}:{ent['key_value']}"
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        neighbours = self.neo4j.get_neighbours(
                            ent["label"], ent["key_field"], ent["key_value"], depth=graph_depth
                        )
                        if neighbours:
                            qr.graph_context.append({
                                "entity": ent,
                                "neighbours": neighbours,
                            })
            except Exception as exc:
                logger.error("Graph expansion failed: %s", exc)

        # ── Step 3b: Direct Graph search (when vector RAG unavailable) ──
        if include_graph and not hits:
            try:
                # Extract key terms from the query and search the graph directly
                import re
                words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
                stop = {"the","and","what","who","where","how","when","are","was","were",
                        "from","with","about","that","this","have","does","did","for",
                        "any","all","between","which","into","than","been"}
                terms = [w for w in words if w not in stop]

                for term in terms[:3]:
                    neighbours = self.neo4j.run_read(
                        "MATCH (n)-[r]-(m) "
                        "WHERE toLower(n.name) CONTAINS $term "
                        "   OR toLower(n.text) CONTAINS $term "
                        "RETURN labels(n) AS src_labels, properties(n) AS src_props, "
                        "       type(r) AS rel_type, "
                        "       labels(m) AS tgt_labels, properties(m) AS tgt_props "
                        "LIMIT 10",
                        term=term,
                    )
                    for rec in neighbours:
                        qr.graph_context.append({
                            "entity": {
                                "label": (rec.get("src_labels") or ["Unknown"])[0],
                                "key_value": (rec.get("src_props") or {}).get("name", term),
                            },
                            "neighbours": [{
                                "relationship": rec.get("rel_type", "RELATED"),
                                "labels": rec.get("tgt_labels", []),
                                "props": rec.get("tgt_props", {}),
                            }],
                        })
            except Exception as exc:
                logger.error("Direct graph search failed: %s", exc)

        # ── Step 3c: Hydrate graph context with page bodies from PageStore ──
        if qr.graph_context:
            try:
                page_ids_to_fetch: set[str] = set()
                for ctx in qr.graph_context:
                    for nbr in ctx.get("neighbours", []):
                        props = nbr.get("props", {})
                        pid = props.get("page_id", "")
                        if pid and "Page" in nbr.get("labels", []):
                            page_ids_to_fetch.add(pid)
                    # Also check the entity itself
                    ent_key = ctx.get("entity", {}).get("key_value", "")
                    if len(ent_key) == 16 and ent_key.isalnum():  # looks like a page_id
                        page_ids_to_fetch.add(ent_key)

                if page_ids_to_fetch:
                    hydrated: list[dict] = []
                    all_store_pages = []
                    for eid in self.page_store.list_extractions():
                        all_store_pages.extend(self.page_store.load_pages(eid))
                    pages_by_id = {p.page_id: p for p in all_store_pages}

                    for pid in list(page_ids_to_fetch)[:15]:
                        page = pages_by_id.get(pid)
                        if page:
                            hydrated.append({
                                "page_id": pid,
                                "artifact_type": page.artifact_type,
                                "title": page.title,
                                "body": page.body[:1200],
                            })
                    if hydrated:
                        qr.graph_context.append({
                            "entity": {"label": "_HydratedPages", "key_value": "page_content"},
                            "neighbours": hydrated,
                        })
            except Exception as exc:
                logger.warning("Page hydration failed: %s", exc)

        # ── Step 4: Build RAG context string ─────────────
        rag_context = self._format_rag_context(qr)

        # ── Step 5: Generate answer via LLM ──────────────
        has_evidence = bool(qr.vector_hits or qr.graph_context)
        if not has_evidence:
            qr.answer = "No matching records found in the ingested device data."
            qr.source = "system"
        elif skip_llm:
            qr.answer = rag_context
            qr.source = "rag_only"
        else:
            qr.answer = self._llm.generate(text, rag_context)
            qr.source = "gemini"

        # ── Step 6: Cache the answer ─────────────────────
        if not skip_cache and qr.answer:
            qr.cache_key = self._cache.store(
                prompt=text,
                response=qr.answer,
                rag_context_summary=rag_context[:500],
            )

        return qr

    # ── helpers ───────────────────────────────────────

    def _format_rag_context(self, qr: QueryResult) -> str:
        """Compile vector hits + graph context + hydrated pages into an LLM-ready text block."""
        parts: list[str] = []

        if qr.vector_hits:
            parts.append("### Retrieved Pages (semantic search)")
            for i, hit in enumerate(qr.vector_hits[:8], 1):
                parts.append(
                    f"\n**Page {i}** ({hit['artifact_type']}, score={hit['score']})\n"
                    f"{hit['body'][:800]}"
                )

        # Separate hydrated pages from graph context
        hydrated_pages: list[dict] = []
        graph_entries: list[dict] = []
        for ctx in qr.graph_context:
            if ctx.get("entity", {}).get("label") == "_HydratedPages":
                hydrated_pages.extend(ctx.get("neighbours", []))
            else:
                graph_entries.append(ctx)

        if hydrated_pages:
            parts.append("\n### Forensic Evidence (page content from related entities)")
            for i, hp in enumerate(hydrated_pages[:12], 1):
                parts.append(
                    f"\n**Evidence {i}** [{hp.get('artifact_type', '?')}] "
                    f"{hp.get('title', '')}\n{hp.get('body', '')}"
                )

        if graph_entries:
            parts.append("\n### Graph Context (entity relationships)")
            for ctx in graph_entries[:15]:
                ent = ctx["entity"]
                parts.append(f"\n**{ent['label']}** = {ent.get('key_value', '?')}")
                for nbr in ctx["neighbours"][:5]:
                    parts.append(f"  → {nbr.get('labels', ['?'])} : {nbr.get('props', {})}")

        return "\n".join(parts) if parts else "(No relevant evidence found in RAG systems.)"

    def cache_stats(self) -> dict:
        """Return cache statistics."""
        return self._cache.stats()

    def llm_status(self) -> dict:
        """Return LLM backend status."""
        return self._llm.status()

    # ── utility ───────────────────────────────────────

    def list_extractions(self) -> list[str]:
        return self.page_store.list_extractions()

    def get_pages(self, extraction_id: str) -> list[Page]:
        return self.page_store.load_pages(extraction_id)
