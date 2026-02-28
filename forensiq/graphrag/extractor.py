"""Entity extractor – pulls structured entities from Page objects and writes them
into the Neo4j knowledge graph.

Extraction is rule-based (regex + artefact-type heuristics) so it works offline
without an LLM.  A future version can swap in an LLM-based NER step.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from forensiq.graphrag.neo4j_client import Neo4jClient
from forensiq.graphrag.schema import NodeLabel, RelType
from forensiq.pageindex.page import Page

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────
# Regex patterns for common forensic entities
# ────────────────────────────────────────────────────────

_PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s]{7,}\d)")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_URL_RE = re.compile(r"https?://[^\s\"'<>]+")
_COORDS_RE = re.compile(r"(-?\d{1,3}\.\d{3,}),\s*(-?\d{1,3}\.\d{3,})")


def _uid(*parts: str) -> str:
    """Deterministic short UID from string components."""
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ────────────────────────────────────────────────────────
# Entity extraction from page text
# ────────────────────────────────────────────────────────

def extract_entities(page: Page) -> list[dict[str, Any]]:
    """Return a list of entity dicts extracted from *page*.

    Each dict has keys: ``label``, ``key_field``, ``key_value``, ``props``.
    """
    text = page.body
    entities: list[dict[str, Any]] = []

    # Phone numbers
    for match in _PHONE_RE.finditer(text):
        number = re.sub(r"[\s\-]", "", match.group())
        entities.append({
            "label": NodeLabel.PHONE_NUMBER,
            "key_field": "number",
            "key_value": number,
            "props": {"raw": match.group().strip()},
        })

    # Email addresses
    for match in _EMAIL_RE.finditer(text):
        entities.append({
            "label": NodeLabel.EMAIL_ADDRESS,
            "key_field": "address",
            "key_value": match.group().lower(),
            "props": {},
        })

    # URLs
    for match in _URL_RE.finditer(text):
        entities.append({
            "label": NodeLabel.URL,
            "key_field": "address",
            "key_value": match.group(),
            "props": {},
        })

    # Coordinates → Location
    for match in _COORDS_RE.finditer(text):
        lat, lon = match.group(1), match.group(2)
        uid = _uid(lat, lon)
        entities.append({
            "label": NodeLabel.LOCATION,
            "key_field": "uid",
            "key_value": uid,
            "props": {"latitude": float(lat), "longitude": float(lon)},
        })

    # ── Artefact-type-specific heuristics ──────────────

    if page.artifact_type == "contact":
        _extract_contact_entities(text, entities)
    elif page.artifact_type in ("message", "chat_message", "sms", "mms"):
        _extract_message_entities(text, entities)
    elif page.artifact_type == "call_log":
        _extract_call_entities(text, entities)
    elif page.artifact_type == "installed_app":
        _extract_app_entities(text, entities)
    elif page.artifact_type == "account":
        _extract_account_entities(text, entities)

    return entities


# ────────────────────────────────────────────────────────
# Artefact-specific helpers
# ────────────────────────────────────────────────────────

def _extract_contact_entities(text: str, entities: list[dict]) -> None:
    for line in text.splitlines():
        if line.startswith("Contact:"):
            name = line.split(":", 1)[1].strip()
            if name:
                entities.append({
                    "label": NodeLabel.PERSON,
                    "key_field": "uid",
                    "key_value": _uid("person", name.lower()),
                    "props": {"name": name},
                })
        if "Org:" in line:
            org = line.split("Org:", 1)[1].strip()
            if org:
                entities.append({
                    "label": NodeLabel.ORGANIZATION,
                    "key_field": "name",
                    "key_value": org,
                    "props": {},
                })


def _extract_message_entities(text: str, entities: list[dict]) -> None:
    for line in text.splitlines():
        for prefix in ("From:", "To:"):
            if prefix in line:
                val = line.split(prefix, 1)[1].strip()
                for part in val.split(","):
                    part = part.strip()
                    if part and not _PHONE_RE.fullmatch(part):
                        entities.append({
                            "label": NodeLabel.PERSON,
                            "key_field": "uid",
                            "key_value": _uid("person", part.lower()),
                            "props": {"name": part},
                        })
        if "App:" in line:
            app = line.split("App:", 1)[1].strip()
            if app:
                entities.append({
                    "label": NodeLabel.APP,
                    "key_field": "package",
                    "key_value": app.lower(),
                    "props": {"name": app},
                })


def _extract_call_entities(text: str, entities: list[dict]) -> None:
    for line in text.splitlines():
        if line.startswith("Call"):
            # Try to extract name after the number
            for prefix in ("Call (incoming):", "Call (outgoing):", "Call (missed):"):
                if line.startswith(prefix):
                    val = line.split(prefix, 1)[1].strip()
                    if val and not _PHONE_RE.fullmatch(val):
                        entities.append({
                            "label": NodeLabel.PERSON,
                            "key_field": "uid",
                            "key_value": _uid("person", val.lower()),
                            "props": {"name": val},
                        })


def _extract_app_entities(text: str, entities: list[dict]) -> None:
    for line in text.splitlines():
        if line.startswith("App:"):
            name = line.split(":", 1)[1].strip()
            if name:
                entities.append({
                    "label": NodeLabel.APP,
                    "key_field": "package",
                    "key_value": name.lower(),
                    "props": {"name": name},
                })
        if "Package:" in line:
            pkg = line.split("Package:", 1)[1].strip()
            if pkg:
                # update the last app entity
                for e in reversed(entities):
                    if e["label"] == NodeLabel.APP:
                        e["key_value"] = pkg
                        e["props"]["package_name"] = pkg
                        break


def _extract_account_entities(text: str, entities: list[dict]) -> None:
    for line in text.splitlines():
        if line.startswith("Account:"):
            parts = line.split(":", 1)[1].strip()
            if "@" in parts:
                # "username @ service"
                pieces = parts.split("@")
                username = pieces[0].strip()
                service = pieces[1].strip() if len(pieces) > 1 else ""
                uid = _uid("account", username.lower(), service.lower())
                entities.append({
                    "label": NodeLabel.ACCOUNT,
                    "key_field": "uid",
                    "key_value": uid,
                    "props": {"username": username, "service": service},
                })


# ────────────────────────────────────────────────────────
# Relationship builder
# ────────────────────────────────────────────────────────

def _infer_relationships(page: Page, entities: list[dict]) -> list[dict[str, Any]]:
    """Produce relationship dicts from a page's entities.

    Returns list of dicts with keys matching ``Neo4jClient.merge_relationship``.
    """
    rels: list[dict[str, Any]] = []

    # Every entity → MENTIONED_IN → Page
    for ent in entities:
        rels.append({
            "src_label": ent["label"],
            "src_key": ent["key_field"],
            "src_val": ent["key_value"],
            "rel_type": RelType.MENTIONED_IN,
            "dst_label": NodeLabel.PAGE,
            "dst_key": "page_id",
            "dst_val": page.page_id,
        })

    # Person ↔ PhoneNumber / EmailAddress (if on same page)
    persons = [e for e in entities if e["label"] == NodeLabel.PERSON]
    phones = [e for e in entities if e["label"] == NodeLabel.PHONE_NUMBER]
    emails = [e for e in entities if e["label"] == NodeLabel.EMAIL_ADDRESS]
    orgs = [e for e in entities if e["label"] == NodeLabel.ORGANIZATION]

    for person in persons:
        for phone in phones:
            rels.append({
                "src_label": NodeLabel.PERSON,
                "src_key": person["key_field"],
                "src_val": person["key_value"],
                "rel_type": RelType.HAS_PHONE,
                "dst_label": NodeLabel.PHONE_NUMBER,
                "dst_key": phone["key_field"],
                "dst_val": phone["key_value"],
            })
        for email in emails:
            rels.append({
                "src_label": NodeLabel.PERSON,
                "src_key": person["key_field"],
                "src_val": person["key_value"],
                "rel_type": RelType.HAS_EMAIL,
                "dst_label": NodeLabel.EMAIL_ADDRESS,
                "dst_key": email["key_field"],
                "dst_val": email["key_value"],
            })
        for org in orgs:
            rels.append({
                "src_label": NodeLabel.PERSON,
                "src_key": person["key_field"],
                "src_val": person["key_value"],
                "rel_type": RelType.BELONGS_TO_ORG,
                "dst_label": NodeLabel.ORGANIZATION,
                "dst_key": org["key_field"],
                "dst_val": org["key_value"],
            })

    # Communication relationships
    if page.artifact_type in ("message", "chat_message", "sms", "mms") and len(persons) >= 2:
        rels.append({
            "src_label": NodeLabel.PERSON,
            "src_key": persons[0]["key_field"],
            "src_val": persons[0]["key_value"],
            "rel_type": RelType.MESSAGED,
            "dst_label": NodeLabel.PERSON,
            "dst_key": persons[1]["key_field"],
            "dst_val": persons[1]["key_value"],
        })

    if page.artifact_type == "call_log" and len(persons) >= 2:
        rels.append({
            "src_label": NodeLabel.PERSON,
            "src_key": persons[0]["key_field"],
            "src_val": persons[0]["key_value"],
            "rel_type": RelType.CALLED,
            "dst_label": NodeLabel.PERSON,
            "dst_key": persons[1]["key_field"],
            "dst_val": persons[1]["key_value"],
        })

    return rels


# ────────────────────────────────────────────────────────
# Public: process pages into the graph
# ────────────────────────────────────────────────────────

def populate_graph(client: Neo4jClient, pages: list[Page], *, project_name: str = "") -> dict[str, int]:
    """Extract entities from *pages* and write them + relationships to Neo4j.

    Each ingest is grouped under a **Project** node so different device
    extractions stay visually and logically separate in the graph.

    Uses batched UNWIND operations so cloud (Aura) targets are fast.
    Returns a summary dict with counts.
    """
    from collections import defaultdict
    from datetime import datetime, timezone

    client.ensure_schema()

    if not pages:
        return {"entities": 0, "relationships": 0, "pages": 0, "project_id": ""}

    # ── Derive project identity from the pages ──
    extraction_id = pages[0].extraction_id
    project_id = extraction_id  # deterministic – same source always gets same project

    # Derive a human-friendly project name
    if not project_name:
        # Try to extract device name from the first page (device_info page)
        for pg in pages:
            if pg.artifact_type == "device_info":
                for line in pg.body.splitlines():
                    if line.strip().startswith("Name:"):
                        project_name = line.split(":", 1)[1].strip()
                        break
                break
        if not project_name:
            # Fallback: use source file basename
            import os
            first_page = pages[0]
            project_name = first_page.metadata.get("source_file", extraction_id)

    total_entities = 0
    total_rels = 0

    # ── Clean old data for this project (makes re-ingest idempotent) ──
    try:
        # Delete Page nodes owned by this project (they have random UUIDs so MERGE won't match)
        client.run_write(
            "MATCH (n:Page {project_id: $pid}) DETACH DELETE n",
            pid=project_id,
        )
        # Delete the old Project node itself (will be re-created below)
        client.run_write(
            "MATCH (pr:Project {project_id: $pid}) DETACH DELETE pr",
            pid=project_id,
        )
        logger.debug("Cleaned old graph data for project %s", project_id)
    except Exception as exc:
        logger.warning("Could not clean old project data: %s", exc)

    # ── Collect all nodes and relationships first ──
    node_groups: dict[str, dict] = defaultdict(lambda: {"key_field": "", "items": []})
    all_rels: list[dict] = []

    # 1. Create the Project node
    proj_group = node_groups[NodeLabel.PROJECT]
    proj_group["key_field"] = "project_id"
    proj_group["items"].append({
        "key_value": project_id,
        "props": {
            "name": project_name,
            "extraction_id": extraction_id,
            "page_count": len(pages),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    })

    for page in pages:
        # Page node — tagged with project_id
        page_group = node_groups[NodeLabel.PAGE]
        page_group["key_field"] = "page_id"
        page_group["items"].append({
            "key_value": page.page_id,
            "props": {
                "artifact_type": page.artifact_type,
                "title": page.title,
                "extraction_id": page.extraction_id,
                "page_number": page.page_number,
                "project_id": project_id,
            },
        })

        # Page → PART_OF → Project
        all_rels.append({
            "src_label": NodeLabel.PAGE,
            "src_key": "page_id",
            "src_val": page.page_id,
            "rel_type": RelType.PART_OF,
            "dst_label": NodeLabel.PROJECT,
            "dst_key": "project_id",
            "dst_val": project_id,
        })

        # Extract entities
        entities = extract_entities(page)
        page.entities = entities
        total_entities += len(entities)

        for ent in entities:
            grp = node_groups[ent["label"]]
            grp["key_field"] = ent["key_field"]
            # Tag every entity node with project_id
            ent_props = {**(ent.get("props") or {}), "project_id": project_id}
            grp["items"].append({
                "key_value": ent["key_value"],
                "props": ent_props,
            })

            # Entity → PART_OF → Project
            all_rels.append({
                "src_label": ent["label"],
                "src_key": ent["key_field"],
                "src_val": ent["key_value"],
                "rel_type": RelType.PART_OF,
                "dst_label": NodeLabel.PROJECT,
                "dst_key": "project_id",
                "dst_val": project_id,
            })

        # Other relationships (MENTIONED_IN, MESSAGED, etc.)
        rels = _infer_relationships(page, entities)
        total_rels += len(rels)
        all_rels.extend(rels)

    # Count PART_OF rels
    part_of_count = sum(1 for r in all_rels if r["rel_type"] == RelType.PART_OF)
    total_rels += part_of_count

    # ── Batch write all nodes ──
    for label, grp in node_groups.items():
        client.batch_merge_nodes(label, grp["key_field"], grp["items"])

    # ── Batch write all relationships ──
    client.batch_merge_relationships(all_rels)

    logger.info(
        "Graph populated: %d entities, %d relationships from %d pages (project=%s)",
        total_entities,
        total_rels,
        len(pages),
        project_name,
    )
    return {
        "entities": total_entities,
        "relationships": total_rels,
        "pages": len(pages),
        "project_id": project_id,
        "project_name": project_name,
    }
