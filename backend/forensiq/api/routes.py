"""FastAPI routes for the ForensIQ PageIndex RAG system."""

from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from config.settings import settings
from forensiq.auth.deps import get_current_user, check_rate_limit
from forensiq.gdrive import GDriveClient
from forensiq.orchestrator.pipeline import ForensIQPipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# Singletons (created once, reused across requests)
_pipeline: ForensIQPipeline | None = None
_gdrive: GDriveClient | None = None


def _get_pipeline() -> ForensIQPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ForensIQPipeline()
    return _pipeline


def _get_gdrive() -> GDriveClient:
    global _gdrive
    if _gdrive is None:
        _gdrive = GDriveClient()
    return _gdrive


# ════════════════════════════════════════════════════════
#  Request / Response models
# ════════════════════════════════════════════════════════

class IngestResponse(BaseModel):
    extraction_id: str
    source_path: str
    total_artifacts: int
    total_pages: int
    vector_indexed: int
    graph_entities: int
    graph_relationships: int
    errors: list[str]


class QueryRequest(BaseModel):
    query: str
    k: int = 10
    graph_depth: int = 2
    include_graph: bool = True
    skip_cache: bool = False
    skip_llm: bool = False


class QueryResponse(BaseModel):
    query: str
    answer: str
    source: str  # "gemini" | "cache+openrouter" | "cache" | "rag_only"
    cache_key: str
    vector_hits: list[dict[str, Any]]
    graph_context: list[dict[str, Any]]


class PageOut(BaseModel):
    page_id: str
    extraction_id: str
    artifact_type: str
    source_section: str
    page_number: int
    title: str
    body: str
    token_count: int
    metadata: dict[str, Any]


class StatsResponse(BaseModel):
    extractions: list[str]
    faiss_vectors: int
    neo4j_nodes: int | None = None
    neo4j_relationships: int | None = None


# ── Graph visualization models ──────────────────────

class GraphNode(BaseModel):
    id: str
    label: str  # Node label (Person, PhoneNumber, etc.)
    properties: dict[str, Any]


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str  # Relationship type (MESSAGED, HAS_PHONE, etc.)
    properties: dict[str, Any]


class GraphResponse(BaseModel):
    """Frontend-ready graph structure — plug into D3, vis.js, Cytoscape, React Flow, etc."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    node_count: int
    edge_count: int


class GraphExportResponse(BaseModel):
    """Full graph snapshot for storing in your own DB."""
    exported_at: str
    neo4j_uri: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    summary: dict[str, int]


class ProjectSummary(BaseModel):
    """Summary of a single project/device extraction in the graph."""
    project_id: str
    name: str
    extraction_id: str
    page_count: int
    node_count: int
    created_at: str


# ════════════════════════════════════════════════════════
#  Ingest
# ════════════════════════════════════════════════════════

@router.post("/ingest/upload", response_model=IngestResponse, tags=["Ingest"])
async def ingest_upload(
    file: UploadFile = File(...),
    skip_graph: bool = Query(False, description="Skip Neo4j graph population"),
    current_user: dict = Depends(get_current_user),
):
    """Upload a ``.ufdr`` or ``.clbe`` file and run the full ingest pipeline.

    Validates the file before processing:
    - Must have a valid extension (.ufdr, .clbe, .zip)
    - Must be a valid ZIP archive
    - Must contain a report XML (report.xml, UFEDReport.xml, etc.)
    """
    # ── Validate filename extension ──
    filename = file.filename or "upload.ufdr"
    ext = Path(filename).suffix.lower()
    valid_extensions = {".ufdr", ".clbe", ".zip"}
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Accepted formats: .ufdr, .clbe, .zip",
        )

    # ── Save to disk ──
    upload_dir = settings.ufdr_upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / filename

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # ── Validate it's a real ZIP archive ──
    if not zipfile.is_zipfile(dest):
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="File is not a valid ZIP/UFDR/CLBE archive. The file appears corrupted or is not a Cellebrite extraction.",
        )

    # ── Validate it contains a report XML ──
    try:
        with zipfile.ZipFile(dest, "r") as zf:
            names = zf.namelist()
            report_names = {"report.xml", "UFEDReport.xml", "Report.xml",
                            "CellebriteReport.xml", "ExtractionReport.xml"}
            has_report = any(
                Path(n).name in report_names or n.endswith(".xml")
                for n in names
            )
            if not has_report:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Cellebrite archive: no report XML found inside the file. "
                           "Expected report.xml or UFEDReport.xml inside the archive.",
                )
    except zipfile.BadZipFile:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="Corrupted archive. Could not read the ZIP file contents.",
        )

    # ── Run ingest pipeline ──
    pipeline = _get_pipeline()
    result = pipeline.ingest(dest, skip_graph=skip_graph)

    if not result.extraction_id:
        raise HTTPException(
            status_code=422,
            detail="Ingest produced no pages. The file may be empty or in an unsupported format. "
                   + ("; ".join(result.errors) if result.errors else ""),
        )

    # Link project to the uploading user
    try:
        from forensiq.auth.mongo import link_project
        await link_project(user_id=current_user["sub"], project_id=result.extraction_id)
    except Exception as exc:
        logger.warning("Failed to link project to user: %s", exc)

    return IngestResponse(
        extraction_id=result.extraction_id,
        source_path=result.source_path,
        total_artifacts=result.total_artifacts,
        total_pages=result.total_pages,
        vector_indexed=result.vector_indexed,
        graph_entities=result.graph_entities,
        graph_relationships=result.graph_relationships,
        errors=result.errors,
    )


@router.post("/ingest/path", response_model=IngestResponse, tags=["Ingest"])
async def ingest_path(
    path: str = Query(..., description="Local path to a .ufdr/.clbe file or extracted dir"),
    skip_graph: bool = Query(False),
    current_user: dict = Depends(get_current_user),
):
    """Ingest a Cellebrite source already on disk."""
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    pipeline = _get_pipeline()
    result = pipeline.ingest(p, skip_graph=skip_graph)

    # Link project to the uploading user
    try:
        from forensiq.auth.mongo import link_project
        await link_project(user_id=current_user["sub"], project_id=result.extraction_id)
    except Exception as exc:
        logger.warning("Failed to link project to user: %s", exc)

    return IngestResponse(
        extraction_id=result.extraction_id,
        source_path=result.source_path,
        total_artifacts=result.total_artifacts,
        total_pages=result.total_pages,
        vector_indexed=result.vector_indexed,
        graph_entities=result.graph_entities,
        graph_relationships=result.graph_relationships,
        errors=result.errors,
    )


# ════════════════════════════════════════════════════════
#  Query
# ════════════════════════════════════════════════════════

@router.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(req: QueryRequest, _user: dict = Depends(get_current_user)):
    """Full query pipeline: cache check → RAG retrieval → LLM generation → cache store.

    - **skip_cache**: bypass Redis and always run fresh RAG + Gemini.
    - **skip_llm**: return raw RAG context without LLM polishing.
    """
    pipeline = _get_pipeline()
    result = pipeline.query(
        req.query,
        k=req.k,
        graph_depth=req.graph_depth,
        include_graph=req.include_graph,
        skip_cache=req.skip_cache,
        skip_llm=req.skip_llm,
    )
    return QueryResponse(
        query=result.query,
        answer=result.answer,
        source=result.source,
        cache_key=result.cache_key,
        vector_hits=result.vector_hits,
        graph_context=result.graph_context,
    )


# ════════════════════════════════════════════════════════
#  Pages
# ════════════════════════════════════════════════════════

@router.get("/pages/{extraction_id}", response_model=list[PageOut], tags=["Pages"])
async def list_pages(extraction_id: str, _user: dict = Depends(get_current_user)):
    """List all pages for a given extraction."""
    pipeline = _get_pipeline()
    pages = pipeline.get_pages(extraction_id)
    if not pages:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return [
        PageOut(
            page_id=p.page_id,
            extraction_id=p.extraction_id,
            artifact_type=p.artifact_type,
            source_section=p.source_section,
            page_number=p.page_number,
            title=p.title,
            body=p.body,
            token_count=p.token_count,
            metadata=p.metadata,
        )
        for p in pages
    ]


# ════════════════════════════════════════════════════════
#  Google Drive
# ════════════════════════════════════════════════════════

class GDriveListResponse(BaseModel):
    folder_id: str
    files: list[dict[str, Any]]


class GDriveBatchIngestResponse(BaseModel):
    folder_id: str
    total_files: int
    results: list[IngestResponse]
    errors: list[str]


@router.get("/gdrive/auth", tags=["Google Drive"])
async def gdrive_auth(_user: dict = Depends(get_current_user)):
    """Trigger OAuth2 authentication with Google Drive.
    On first call this opens a browser window for consent.
    """
    try:
        client = _get_gdrive()
        client.authenticate()
        return {"status": "authenticated"}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/gdrive/list/{folder_id}", response_model=GDriveListResponse, tags=["Google Drive"])
async def gdrive_list(folder_id: str, _user: dict = Depends(get_current_user)):
    """List .clbe files inside a Google Drive folder."""
    try:
        client = _get_gdrive()
        files = client.list_clbe_files(folder_id)
        return GDriveListResponse(folder_id=folder_id, files=files)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Drive listing failed: {exc}")


@router.post("/gdrive/ingest/{folder_id}", response_model=GDriveBatchIngestResponse, tags=["Google Drive"])
async def gdrive_ingest(
    folder_id: str,
    skip_graph: bool = Query(False, description="Skip Neo4j graph population"),
    _user: dict = Depends(get_current_user),
):
    """Download all .clbe files from a Drive folder and ingest them.

    This is a batch endpoint — it downloads each .clbe from the CLBE folder,
    parses it through the full pipeline, and returns per-file results.
    """
    client = _get_gdrive()
    pipeline = _get_pipeline()
    batch_errors: list[str] = []

    # 1. List .clbe files
    try:
        files = client.list_clbe_files(folder_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Drive listing failed: {exc}")

    if not files:
        raise HTTPException(status_code=404, detail="No .clbe files found in the folder")

    # 2. Download & ingest each file
    results: list[IngestResponse] = []
    for f in files:
        try:
            local_path = client.download_file(f["id"], f["name"])
            res = pipeline.ingest(local_path, skip_graph=skip_graph)
            results.append(IngestResponse(
                extraction_id=res.extraction_id,
                source_path=res.source_path,
                total_artifacts=res.total_artifacts,
                total_pages=res.total_pages,
                vector_indexed=res.vector_indexed,
                graph_entities=res.graph_entities,
                graph_relationships=res.graph_relationships,
                errors=res.errors,
            ))
        except Exception as exc:
            err = f"Failed to process {f['name']}: {exc}"
            logger.error(err)
            batch_errors.append(err)

    return GDriveBatchIngestResponse(
        folder_id=folder_id,
        total_files=len(files),
        results=results,
        errors=batch_errors,
    )


@router.post("/gdrive/ingest-file", response_model=IngestResponse, tags=["Google Drive"])
async def gdrive_ingest_single(
    file_id: str = Query(..., description="Google Drive file ID of a .clbe file"),
    filename: str = Query("download.clbe", description="Filename to save as"),
    skip_graph: bool = Query(False),
    _user: dict = Depends(get_current_user),
):
    """Download and ingest a single .clbe file from Google Drive."""
    client = _get_gdrive()
    pipeline = _get_pipeline()
    try:
        local_path = client.download_file(file_id, filename)
        res = pipeline.ingest(local_path, skip_graph=skip_graph)
        return IngestResponse(
            extraction_id=res.extraction_id,
            source_path=res.source_path,
            total_artifacts=res.total_artifacts,
            total_pages=res.total_pages,
            vector_indexed=res.vector_indexed,
            graph_entities=res.graph_entities,
            graph_relationships=res.graph_relationships,
            errors=res.errors,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}")


# ════════════════════════════════════════════════════════
#  Graph (for frontend visualization)
# ════════════════════════════════════════════════════════

def _get_neo4j():
    """Lazy-loaded Neo4j client."""
    from forensiq.graphrag.neo4j_client import Neo4jClient
    return Neo4jClient()


def _neo4j_graph_to_json(records, with_rels: bool = True) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Convert raw Cypher result records into GraphNode / GraphEdge lists."""
    nodes_map: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []

    for rec in records:
        # Process node fields
        for key in ("n", "m", "src", "dst", "node"):
            val = rec.get(key)
            if val is None:
                continue
            nid = str(val.element_id)
            if nid not in nodes_map:
                label = next(iter(val.labels), "Unknown")
                nodes_map[nid] = GraphNode(
                    id=nid,
                    label=label,
                    properties=dict(val),
                )
        # Process relationship fields
        if with_rels:
            for key in ("r", "rel"):
                val = rec.get(key)
                if val is None:
                    continue
                edges.append(GraphEdge(
                    source=str(val.start_node.element_id),
                    target=str(val.end_node.element_id),
                    type=val.type,
                    properties=dict(val),
                ))

    return list(nodes_map.values()), edges


@router.get("/graph/full", response_model=GraphResponse, tags=["Graph"])
async def graph_full(
    limit: int = Query(500, description="Max number of relationships to return"),
    project_id: str = Query(None, description="Filter to a specific project (extraction_id)"),
    current_user: dict = Depends(get_current_user),
):
    """Return the knowledge graph scoped to the current user's projects.

    Pass ``project_id`` to see only one project/device — omit it for all
    of the user's projects.
    Plug this directly into **vis.js**, **Cytoscape.js**, **D3**, **React Flow**, etc.
    """
    from forensiq.auth.mongo import get_user_project_ids

    try:
        # Determine which project IDs to include
        if project_id:
            pids = [project_id]
        else:
            pids = await get_user_project_ids(current_user["sub"])
            if not pids:
                return GraphResponse(nodes=[], edges=[], node_count=0, edge_count=0)

        client = _get_neo4j()
        results = client._driver.execute_query(
            "MATCH (n)-[r]->(m) "
            "WHERE n.project_id IN $pids AND m.project_id IN $pids "
            "RETURN n, r, m LIMIT $limit",
            pids=pids, limit=limit,
            database_=client._database,
        )
        nodes, edges = _neo4j_graph_to_json([dict(rec) for rec in results.records])
        client.close()
        return GraphResponse(nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {exc}")


@router.get("/graph/entity/{label}", response_model=GraphResponse, tags=["Graph"])
async def graph_by_entity(
    label: str,
    depth: int = Query(1, ge=1, le=5, description="Hops from matching nodes"),
    limit: int = Query(200, description="Max relationships"),
    current_user: dict = Depends(get_current_user),
):
    """Get subgraph around all nodes of a given label, scoped to user's projects."""
    from forensiq.auth.mongo import get_user_project_ids

    allowed = {
        "Project", "Person", "PhoneNumber", "EmailAddress", "Device", "App",
        "Account", "Location", "URL", "Page", "Organization", "File",
    }
    if label not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid label. Choose from: {sorted(allowed)}")
    try:
        pids = await get_user_project_ids(current_user["sub"])
        if not pids:
            return GraphResponse(nodes=[], edges=[], node_count=0, edge_count=0)

        client = _get_neo4j()
        results = client._driver.execute_query(
            f"MATCH (n:{label})-[r]-(m) "
            f"WHERE n.project_id IN $pids AND m.project_id IN $pids "
            f"RETURN n, r, m LIMIT $limit",
            pids=pids, limit=limit,
            database_=client._database,
        )
        nodes, edges = _neo4j_graph_to_json([dict(rec) for rec in results.records])
        if depth > 1:
            results2 = client._driver.execute_query(
                f"MATCH (n:{label})-[*1..{depth}]-(hop)-[r2]-(m2) "
                f"WHERE n.project_id IN $pids "
                f"RETURN hop AS n, r2 AS r, m2 AS m LIMIT $limit",
                pids=pids, limit=limit,
                database_=client._database,
            )
            nodes2, edges2 = _neo4j_graph_to_json([dict(rec) for rec in results2.records])
            existing_ids = {n.id for n in nodes}
            nodes.extend(n for n in nodes2 if n.id not in existing_ids)
            edges.extend(edges2)
        client.close()
        return GraphResponse(nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {exc}")


@router.get("/graph/search/{name}", response_model=GraphResponse, tags=["Graph"])
async def graph_search(
    name: str,
    depth: int = Query(2, ge=1, le=5, description="Hops from matching node"),
    current_user: dict = Depends(get_current_user),
):
    """Search for a person/entity by name, scoped to the user's projects.

    Example: ``/api/v1/graph/search/Vikram?depth=2``
    """
    from forensiq.auth.mongo import get_user_project_ids

    try:
        pids = await get_user_project_ids(current_user["sub"])
        if not pids:
            return GraphResponse(nodes=[], edges=[], node_count=0, edge_count=0)

        client = _get_neo4j()
        results = client._driver.execute_query(
            "MATCH (n)-[r]-(m) "
            "WHERE n.project_id IN $pids "
            "AND any(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($name)) "
            "RETURN n, r, m LIMIT 300",
            name=name, pids=pids,
            database_=client._database,
        )
        nodes, edges = _neo4j_graph_to_json([dict(rec) for rec in results.records])
        if depth > 1:
            results2 = client._driver.execute_query(
                "MATCH (seed)-[*1..{depth}]-(hop)-[r2]-(m2) "
                "WHERE seed.project_id IN $pids "
                "AND any(prop IN keys(seed) WHERE toLower(toString(seed[prop])) CONTAINS toLower($name)) "
                "RETURN hop AS n, r2 AS r, m2 AS m LIMIT 300".replace("{depth}", str(depth)),
                name=name, pids=pids,
                database_=client._database,
            )
            nodes2, edges2 = _neo4j_graph_to_json([dict(rec) for rec in results2.records])
            existing_ids = {n.id for n in nodes}
            nodes.extend(n for n in nodes2 if n.id not in existing_ids)
            edges.extend(edges2)
        client.close()
        return GraphResponse(nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph search failed: {exc}")


# ── Project management ────────────────────────────────

@router.get("/graph/my-projects", response_model=list[ProjectSummary], tags=["Graph"])
async def list_my_projects(current_user: dict = Depends(get_current_user)):
    """List projects uploaded by the current user.

    Automatically claims orphan projects (present in Neo4j but not linked
    to any user) so that legacy/pre-linking uploads still appear.
    """
    from forensiq.auth.mongo import (
        get_user_project_ids,
        get_all_claimed_project_ids,
        bulk_link_projects,
    )

    user_id = current_user["sub"]

    # ── Auto-claim orphan projects ────────────────────
    try:
        client = _get_neo4j()
        all_neo4j = client.run_read(
            "MATCH (pr:Project) RETURN pr.project_id AS pid"
        )
        client.close()
        all_neo4j_ids = {r["pid"] for r in all_neo4j if r["pid"]}
    except Exception:
        all_neo4j_ids = set()

    if all_neo4j_ids:
        claimed = await get_all_claimed_project_ids()
        orphans = list(all_neo4j_ids - claimed)
        if orphans:
            await bulk_link_projects(user_id=user_id, project_ids=orphans)

    owned_ids = await get_user_project_ids(user_id)

    if not owned_ids:
        return []

    try:
        client = _get_neo4j()
        rows = client.run_read(
            "MATCH (pr:Project) "
            "WHERE pr.project_id IN $pids "
            "OPTIONAL MATCH (n)-[:PART_OF]->(pr) "
            "WHERE NOT 'Page' IN labels(n) "
            "RETURN pr.project_id AS project_id, "
            "       pr.name AS name, "
            "       pr.extraction_id AS extraction_id, "
            "       pr.page_count AS page_count, "
            "       pr.created_at AS created_at, "
            "       count(n) AS node_count "
            "ORDER BY pr.created_at DESC",
            pids=owned_ids,
        )
        client.close()
        return [
            ProjectSummary(
                project_id=r["project_id"],
                name=r.get("name") or r["project_id"],
                extraction_id=r.get("extraction_id") or r["project_id"],
                page_count=r.get("page_count") or 0,
                node_count=r.get("node_count") or 0,
                created_at=r.get("created_at") or "",
            )
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {exc}")


@router.get("/graph/projects", response_model=list[ProjectSummary], tags=["Graph"])
async def list_projects(_user: dict = Depends(get_current_user)):
    """List all projects (device extractions) in the graph.

    Each project groups the nodes from one .clbe/.ufdr ingestion.
    """
    try:
        client = _get_neo4j()
        rows = client.run_read(
            "MATCH (pr:Project) "
            "OPTIONAL MATCH (n)-[:PART_OF]->(pr) "
            "WHERE NOT 'Page' IN labels(n) "
            "RETURN pr.project_id AS project_id, "
            "       pr.name AS name, "
            "       pr.extraction_id AS extraction_id, "
            "       pr.page_count AS page_count, "
            "       pr.created_at AS created_at, "
            "       count(n) AS node_count "
            "ORDER BY pr.created_at DESC"
        )
        client.close()
        return [
            ProjectSummary(
                project_id=r["project_id"],
                name=r.get("name") or r["project_id"],
                extraction_id=r.get("extraction_id") or r["project_id"],
                page_count=r.get("page_count") or 0,
                node_count=r.get("node_count") or 0,
                created_at=r.get("created_at") or "",
            )
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {exc}")


@router.get("/graph/project/{project_id}", response_model=GraphResponse, tags=["Graph"])
async def graph_project(
    project_id: str,
    limit: int = Query(500, description="Max relationships"),
    _user: dict = Depends(get_current_user),
):
    """Return the subgraph for a **single project** (device extraction).

    Only shows nodes and relationships that belong to this project.
    """
    try:
        client = _get_neo4j()
        results = client._driver.execute_query(
            "MATCH (n)-[r]->(m) "
            "WHERE n.project_id = $pid AND m.project_id = $pid "
            "RETURN n, r, m LIMIT $limit",
            pid=project_id, limit=limit,
            database_=client._database,
        )
        nodes, edges = _neo4j_graph_to_json([dict(rec) for rec in results.records])
        # Also include the Project hub node
        results2 = client._driver.execute_query(
            "MATCH (pr:Project {project_id: $pid}) RETURN pr AS n",
            pid=project_id,
            database_=client._database,
        )
        for rec in results2.records:
            val = rec["n"]
            nid = str(val.element_id)
            nodes.append(GraphNode(
                id=nid,
                label="Project",
                properties=dict(val),
            ))
        client.close()
        if not nodes:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
        return GraphResponse(nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {exc}")


@router.delete("/graph/project/{project_id}", tags=["Graph"])
async def delete_project(project_id: str, _user: dict = Depends(get_current_user)):
    """Delete all graph data belonging to a specific project.

    This removes the Project node and all nodes/relationships tagged
    with this project_id. Other projects remain untouched.
    """
    try:
        client = _get_neo4j()
        # Delete all nodes with this project_id (cascades relationships)
        result = client.run_write(
            "MATCH (n {project_id: $pid}) DETACH DELETE n RETURN count(n) AS deleted",
            pid=project_id,
        )
        # Also delete the project node itself
        client.run_write(
            "MATCH (pr:Project {project_id: $pid}) DETACH DELETE pr",
            pid=project_id,
        )
        deleted = result[0]["deleted"] if result else 0
        client.close()
        return {"project_id": project_id, "deleted_nodes": deleted}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Delete failed: {exc}")


@router.get("/graph/export", response_model=GraphExportResponse, tags=["Graph"])
async def graph_export(_user: dict = Depends(get_current_user)):
    """Export the entire graph as a JSON snapshot you can store in your own DB.

    Returns all nodes and edges with full properties — save this as-is into
    MongoDB, PostgreSQL (JSONB), SQLite, or any document store.
    """
    from datetime import datetime, timezone
    try:
        client = _get_neo4j()
        results = client._driver.execute_query(
            "MATCH (n)-[r]->(m) RETURN n, r, m",
            database_=client._database,
        )
        nodes, edges = _neo4j_graph_to_json([dict(rec) for rec in results.records])

        # Summary by label
        from collections import Counter
        node_summary = dict(Counter(n.label for n in nodes))
        edge_summary = dict(Counter(e.type for e in edges))

        client.close()
        return GraphExportResponse(
            exported_at=datetime.now(timezone.utc).isoformat(),
            neo4j_uri=settings.neo4j_uri,
            nodes=nodes,
            edges=edges,
            summary={**{f"node_{k}": v for k, v in node_summary.items()},
                     **{f"rel_{k}": v for k, v in edge_summary.items()},
                     "total_nodes": len(nodes),
                     "total_edges": len(edges)},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph export failed: {exc}")


# ════════════════════════════════════════════════════════
#  Stats
# ════════════════════════════════════════════════════════

@router.get("/stats", response_model=StatsResponse, tags=["Stats"])
async def stats(_user: dict = Depends(get_current_user)):
    """Return high-level system statistics."""
    pipeline = _get_pipeline()
    resp = StatsResponse(
        extractions=pipeline.list_extractions(),
        faiss_vectors=pipeline._faiss.size,
    )
    try:
        resp.neo4j_nodes = pipeline.neo4j.count_nodes()
        resp.neo4j_relationships = pipeline.neo4j.count_relationships()
    except Exception:
        pass  # Neo4j might not be running
    return resp


# ════════════════════════════════════════════════════════
#  Cache management
# ════════════════════════════════════════════════════════

@router.get("/cache/stats", tags=["Cache"])
async def cache_stats(_user: dict = Depends(get_current_user)):
    """Return Redis cache statistics (backend, entry count, TTL)."""
    pipeline = _get_pipeline()
    return pipeline.cache_stats()


@router.delete("/cache/flush", tags=["Cache"])
async def cache_flush(_user: dict = Depends(get_current_user)):
    """Clear all cached query responses."""
    pipeline = _get_pipeline()
    pipeline._cache.flush_all()
    return {"status": "flushed"}


@router.delete("/cache/invalidate", tags=["Cache"])
async def cache_invalidate(prompt: str = Query(..., description="The prompt to invalidate"), _user: dict = Depends(get_current_user)):
    """Remove a specific cached response by prompt."""
    pipeline = _get_pipeline()
    removed = pipeline._cache.invalidate(prompt)
    return {"prompt": prompt, "removed": removed}


# ════════════════════════════════════════════════════════
#  LLM status
# ════════════════════════════════════════════════════════

@router.get("/llm/status", tags=["LLM"])
async def llm_status(_user: dict = Depends(get_current_user)):
    """Return which LLM backends (Gemini, OpenRouter) are available."""
    pipeline = _get_pipeline()
    return pipeline.llm_status()


# ════════════════════════════════════════════════════════
#  Anomaly Detection (LLM-powered)
# ════════════════════════════════════════════════════════

class AnomalyItem(BaseModel):
    id: str
    category: str          # temporal | linguistic | data | network
    severity: str          # critical | high | medium | low
    title: str
    finding: str
    whySuspicious: str
    nextSteps: list[str]
    timestamp: str
    evidence: list[str]
    baselineDeviation: str


class AnomalyResponse(BaseModel):
    project_id: str
    baseline: dict[str, Any]
    riskSummary: dict[str, Any]
    anomalies: list[AnomalyItem]


# ── Risk Intel models ─────────────────────────────────

class RiskHitOut(BaseModel):
    rule_id: str
    category: str
    severity: str
    title: str
    description: str
    evidence_excerpt: str
    page_id: str
    artifact_type: str
    source_device: str
    matched_pattern: str
    confidence: float


class RiskIntelResponse(BaseModel):
    project_id: str
    total_pages_scanned: int
    total_hits: int
    summary: dict[str, Any]
    hits: list[RiskHitOut]


@router.get("/riskintel/{project_id}", response_model=RiskIntelResponse, tags=["Risk Intel"])
async def risk_intel(project_id: str, _user: dict = Depends(get_current_user)):
    """Run rule-based risk intelligence detection on a project's page data.

    Scans all pages for indicators of counter-intelligence, evidence fabrication,
    anti-forensic activity, obfuscation, financial fraud, and evidence tampering.
    Returns scored hits with evidence excerpts.
    """
    from forensiq.riskintel.detector import RiskIntelDetector

    pipeline = _get_pipeline()

    # Gather all pages for this project
    pages_dicts: list[dict] = []
    for eid in pipeline.page_store.list_extractions():
        for page in pipeline.page_store.load_pages(eid):
            if hasattr(page, "metadata") and page.metadata.get("project_id") == project_id:
                pages_dicts.append({
                    "page_id": page.page_id,
                    "body": page.body,
                    "artifact_type": page.artifact_type,
                    "extraction_id": page.extraction_id,
                    "title": page.title,
                })

    # If no pages match by project_id metadata, try matching by extraction_id
    if not pages_dicts:
        for eid in pipeline.page_store.list_extractions():
            for page in pipeline.page_store.load_pages(eid):
                if page.extraction_id == project_id:
                    pages_dicts.append({
                        "page_id": page.page_id,
                        "body": page.body,
                        "artifact_type": page.artifact_type,
                        "extraction_id": page.extraction_id,
                        "title": page.title,
                    })

    # Last resort — scan ALL pages if project matching fails
    if not pages_dicts:
        for eid in pipeline.page_store.list_extractions():
            for page in pipeline.page_store.load_pages(eid):
                pages_dicts.append({
                    "page_id": page.page_id,
                    "body": page.body,
                    "artifact_type": page.artifact_type,
                    "extraction_id": page.extraction_id,
                    "title": page.title,
                })

    if not pages_dicts:
        raise HTTPException(status_code=404, detail=f"No page data found for project: {project_id}")

    detector = RiskIntelDetector()
    report = detector.scan_pages(pages_dicts, project_id)

    return RiskIntelResponse(
        project_id=project_id,
        total_pages_scanned=report.total_pages_scanned,
        total_hits=len(report.hits),
        summary=report.summary,
        hits=[
            RiskHitOut(
                rule_id=h.rule_id,
                category=h.category,
                severity=h.severity,
                title=h.title,
                description=h.description,
                evidence_excerpt=h.evidence_excerpt,
                page_id=h.page_id,
                artifact_type=h.artifact_type,
                source_device=h.source_device,
                matched_pattern=h.matched_pattern,
                confidence=h.confidence,
            )
            for h in report.hits
        ],
    )


@router.get("/anomalies/{project_id}", response_model=AnomalyResponse, tags=["Anomalies"])
async def detect_anomalies(project_id: str, _user: dict = Depends(get_current_user)):
    """Run LLM-powered anomaly detection on a project's graph data.

    Analyzes entity relationships, communication patterns, and metadata
    to identify behavioural anomalies and suspicious patterns.
    """
    import json as _json
    from datetime import datetime, timezone

    pipeline = _get_pipeline()

    # 1. Gather project graph data
    try:
        client = _get_neo4j()
        results = client._driver.execute_query(
            "MATCH (n)-[r]->(m) "
            "WHERE n.project_id = $pid AND m.project_id = $pid "
            "RETURN n, r, m LIMIT 300",
            pid=project_id,
            database_=client._database,
        )
        nodes, edges = _neo4j_graph_to_json([dict(rec) for rec in results.records])

        # Get project info
        proj_rows = client.run_read(
            "MATCH (pr:Project {project_id: $pid}) RETURN pr",
            pid=project_id,
        )
        client.close()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {exc}")

    if not nodes:
        raise HTTPException(status_code=404, detail=f"No data for project: {project_id}")

    # 2. Build a summary for the LLM
    node_summary = {}
    for n in nodes:
        label = n.label
        node_summary[label] = node_summary.get(label, 0) + 1

    edge_summary = {}
    for e in edges:
        edge_summary[e.type] = edge_summary.get(e.type, 0) + 1

    # Sample some node details
    sample_nodes = []
    for n in nodes[:30]:
        sample_nodes.append({
            "label": n.label,
            "properties": {k: str(v)[:100] for k, v in n.properties.items()
                           if k not in ("project_id", "extraction_id")},
        })

    sample_edges = []
    for e in edges[:30]:
        src_node = next((n for n in nodes if n.id == e.source), None)
        tgt_node = next((n for n in nodes if n.id == e.target), None)
        sample_edges.append({
            "type": e.type,
            "from": (src_node.properties.get("name") or src_node.label) if src_node else "?",
            "to": (tgt_node.properties.get("name") or tgt_node.label) if tgt_node else "?",
            "properties": {k: str(v)[:60] for k, v in e.properties.items()
                           if k not in ("project_id",)},
        })

    context = _json.dumps({
        "node_counts": node_summary,
        "edge_counts": edge_summary,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "sample_nodes": sample_nodes,
        "sample_edges": sample_edges,
    }, indent=2)

    # 3. Ask the LLM to generate anomalies
    prompt = f"""You are a digital forensics anomaly detection engine analyzing data extracted from a seized device.

Below is a summary and sample of the entity graph for this device extraction:

{context}

Based on this data, identify 4-8 behavioural anomalies or suspicious patterns. For each anomaly, provide:
- category: one of "temporal", "linguistic", "data", "network"
- severity: one of "critical", "high", "medium", "low"
- title: short anomaly title (max 60 chars)
- finding: detailed description of what was found (2-3 sentences)
- whySuspicious: why this is suspicious in a forensic context (2-3 sentences)
- nextSteps: array of 2-4 recommended investigative actions
- evidence: array of 1-3 evidence source references
- baselineDeviation: one-line description of how this deviates from normal

Also provide:
- baseline: object with keys activeHours, primaryLanguage, avgDailyMessages, typicalContacts, avgMediaPerDay (estimated from the data)
- riskSummary: object with keys overallRisk (string like "HIGH"), critical (int count), high (int count), medium (int count), low (int count), recommendation (string)

Return ONLY valid JSON matching this exact structure:
{{
  "baseline": {{ ... }},
  "riskSummary": {{ ... }},
  "anomalies": [ {{ "category": "...", "severity": "...", "title": "...", "finding": "...", "whySuspicious": "...", "nextSteps": [...], "evidence": [...], "baselineDeviation": "..." }} ]
}}"""

    try:
        llm_answer = pipeline._llm.generate(prompt)
        # Extract JSON from the response (strip markdown fences if present)
        json_text = llm_answer.strip()
        if json_text.startswith("```"):
            json_text = json_text.split("\n", 1)[1]  # remove ```json
            if json_text.endswith("```"):
                json_text = json_text[:-3]
        parsed = _json.loads(json_text)
    except Exception as exc:
        logger.error("Anomaly LLM parse failed: %s", exc)
        # Return a minimal fallback
        parsed = {
            "baseline": {
                "activeHours": "Unknown", "primaryLanguage": "Unknown",
                "avgDailyMessages": 0, "typicalContacts": 0, "avgMediaPerDay": 0,
            },
            "riskSummary": {
                "overallRisk": "UNKNOWN", "critical": 0, "high": 0,
                "medium": 0, "low": 0,
                "recommendation": f"LLM analysis failed: {exc}",
            },
            "anomalies": [],
        }

    # 4. Build response
    anomalies = []
    for i, a in enumerate(parsed.get("anomalies", [])):
        anomalies.append(AnomalyItem(
            id=f"a{i+1}",
            category=a.get("category", "network"),
            severity=a.get("severity", "medium"),
            title=a.get("title", "Unknown Anomaly"),
            finding=a.get("finding", ""),
            whySuspicious=a.get("whySuspicious", ""),
            nextSteps=a.get("nextSteps", []),
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence=a.get("evidence", []),
            baselineDeviation=a.get("baselineDeviation", ""),
        ))

    return AnomalyResponse(
        project_id=project_id,
        baseline=parsed.get("baseline", {}),
        riskSummary=parsed.get("riskSummary", {}),
        anomalies=anomalies,
    )


# ════════════════════════════════════════════════════════
#  Authentication (MongoDB Atlas)
# ════════════════════════════════════════════════════════

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "Investigating Officer"
    department: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user: dict[str, Any]
    token: str


@router.post("/auth/signup", response_model=AuthResponse, tags=["Auth"])
async def auth_signup(req: SignupRequest, request: Request):
    """Register a new user account.

    Stores credentials in MongoDB Atlas with bcrypt-hashed password.
    Returns user session data + JWT token.
    """
    from forensiq.auth.mongo import signup, ensure_indexes
    import re

    # Rate limit signup attempts
    check_rate_limit(request, max_attempts=10, window=600)

    # Validation
    if not req.name or len(req.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    if not req.password or len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not re.search(r'[A-Z]', req.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', req.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', req.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")

    await ensure_indexes()
    try:
        user = await signup(
            name=req.name,
            email=req.email,
            password=req.password,
            role=req.role,
            department=req.department,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.error("Signup failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Signup failed: {exc}")

    token = _create_jwt(user)
    return AuthResponse(user=user, token=token)


@router.post("/auth/login", response_model=AuthResponse, tags=["Auth"])
async def auth_login(req: LoginRequest, request: Request):
    """Authenticate with email + password.

    Verifies credentials against MongoDB Atlas.
    Returns user session data + JWT token.
    """
    from forensiq.auth.mongo import login

    # Rate limit login attempts: 5 per 5 minutes per IP
    check_rate_limit(request, max_attempts=5, window=300)

    try:
        user = await login(email=req.email, password=req.password)
    except Exception as exc:
        logger.error("Login failed unexpectedly: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login error: {exc}")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_jwt(user)
    return AuthResponse(user=user, token=token)


# ── Forgot / Reset Password ────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/auth/forgot-password", tags=["Auth"])
async def auth_forgot_password(req: ForgotPasswordRequest, request: Request):
    """Request a password reset token for the given email.

    In production this would send an email; for now the token is returned
    in the response so the frontend can proceed to the reset page.
    """
    from forensiq.auth.mongo import create_password_reset

    check_rate_limit(request, max_attempts=5, window=600)

    token = await create_password_reset(req.email)

    # Always return 200 to avoid email enumeration
    if not token:
        return {"message": "If an account with that email exists, a reset link has been generated.", "token": None}

    return {
        "message": "If an account with that email exists, a reset link has been generated.",
        "token": token,
    }


@router.post("/auth/reset-password", tags=["Auth"])
async def auth_reset_password(req: ResetPasswordRequest, request: Request):
    """Reset password using a reset token."""
    from forensiq.auth.mongo import reset_password
    import re

    check_rate_limit(request, max_attempts=5, window=300)

    # Password validation
    if not req.new_password or len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not re.search(r'[A-Z]', req.new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r'[a-z]', req.new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not re.search(r'[0-9]', req.new_password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")

    success = await reset_password(req.token, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    return {"message": "Password has been reset successfully. You can now log in."}


def _create_jwt(user: dict) -> str:
    """Create a JWT token for the authenticated user."""
    import jwt
    from datetime import datetime, timezone, timedelta

    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user["name"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# ════════════════════════════════════════════════════════
#  Conversations (per-user chat history)
# ════════════════════════════════════════════════════════

class ConversationOut(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class ConversationDetail(BaseModel):
    id: str
    user_id: str
    title: str
    messages: list[dict[str, Any]]
    created_at: str
    updated_at: str


class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"


class AppendMessageRequest(BaseModel):
    message: dict[str, Any]


class RenameConversationRequest(BaseModel):
    title: str


@router.post("/conversations", response_model=ConversationDetail, tags=["Conversations"])
async def create_conversation(
    req: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new conversation for the authenticated user."""
    from forensiq.auth.conversations import create_conversation as _create

    conv = await _create(user_id=current_user["sub"], title=req.title)
    return ConversationDetail(**conv)


@router.get("/conversations", response_model=list[ConversationOut], tags=["Conversations"])
async def list_conversations(current_user: dict = Depends(get_current_user)):
    """List all conversations for the authenticated user (newest first)."""
    from forensiq.auth.conversations import list_conversations as _list

    convs = await _list(user_id=current_user["sub"])
    return [ConversationOut(**c) for c in convs]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail, tags=["Conversations"])
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a conversation with full message history. Only accessible by the owner."""
    from forensiq.auth.conversations import get_conversation as _get

    conv = await _get(conversation_id=conversation_id, user_id=current_user["sub"])
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetail(**conv)


@router.post("/conversations/{conversation_id}/messages", tags=["Conversations"])
async def append_message(
    conversation_id: str,
    req: AppendMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    """Append a message to a conversation. Only the owner can add messages."""
    from forensiq.auth.conversations import append_message as _append

    ok = await _append(
        conversation_id=conversation_id,
        user_id=current_user["sub"],
        message=req.message,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "ok"}


@router.patch("/conversations/{conversation_id}", tags=["Conversations"])
async def rename_conversation(
    conversation_id: str,
    req: RenameConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Rename a conversation. Only the owner can rename."""
    from forensiq.auth.conversations import update_title

    ok = await update_title(
        conversation_id=conversation_id,
        user_id=current_user["sub"],
        title=req.title,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "ok"}


@router.delete("/conversations/{conversation_id}", tags=["Conversations"])
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a conversation. Only the owner can delete."""
    from forensiq.auth.conversations import delete_conversation as _delete

    ok = await _delete(conversation_id=conversation_id, user_id=current_user["sub"])
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "ok"}
