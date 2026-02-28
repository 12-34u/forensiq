"""PageIndex Indexer – converts a UFDRExtraction into a list of Page objects.

Each artefact category gets its own serialisation strategy so the downstream
embeddings are maximally useful for forensic search.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Sequence

import tiktoken

from config.settings import settings
from forensiq.pageindex.page import Page
from forensiq.ufdr.models import (
    Account,
    CallLog,
    Contact,
    Email,
    InstalledApp,
    Location,
    MediaFile,
    Message,
    UFDRExtraction,
    WebHistory,
)

logger = logging.getLogger(__name__)

# Tokeniser for page-size estimation (cl100k_base works for OpenAI models)
_enc = tiktoken.get_encoding("cl100k_base")


def _token_count(text: str) -> int:
    return len(_enc.encode(text))


def _extraction_id(extraction: UFDRExtraction) -> str:
    return hashlib.sha256(extraction.source_path.encode()).hexdigest()[:16]


# ────────────────────────────────────────────────────────
# Per-artefact serialisers → plain-text representation
# ────────────────────────────────────────────────────────

def _serialise_contact(c: Contact) -> str:
    lines = [f"Contact: {c.name}"]
    if c.phone_numbers:
        lines.append(f"  Phone(s): {', '.join(c.phone_numbers)}")
    if c.emails:
        lines.append(f"  Email(s): {', '.join(c.emails)}")
    if c.organization:
        lines.append(f"  Org: {c.organization}")
    if c.source:
        lines.append(f"  Source: {c.source}")
    return "\n".join(lines)


def _serialise_call(c: CallLog) -> str:
    parts = [f"Call ({c.direction}): {c.phone_number or c.contact_name}"]
    if c.duration_seconds:
        parts.append(f"  Duration: {c.duration_seconds}s")
    if c.timestamp:
        parts.append(f"  Time: {c.timestamp.isoformat()}")
    if c.source:
        parts.append(f"  Source: {c.source}")
    return "\n".join(parts)


def _serialise_message(m: Message) -> str:
    lines = [f"{m.artifact_type.value.upper()} ({m.direction})"]
    if m.sender:
        lines.append(f"  From: {m.sender}")
    if m.recipients:
        lines.append(f"  To: {', '.join(m.recipients)}")
    if m.timestamp:
        lines.append(f"  Time: {m.timestamp.isoformat()}")
    if m.source:
        lines.append(f"  App: {m.source}")
    if m.body:
        lines.append(f"  Body: {m.body}")
    if m.attachments:
        lines.append(f"  Attachments: {', '.join(m.attachments)}")
    return "\n".join(lines)


def _serialise_email(e: Email) -> str:
    lines = [f"Email: {e.subject}"]
    if e.sender:
        lines.append(f"  From: {e.sender}")
    if e.recipients:
        lines.append(f"  To: {', '.join(e.recipients)}")
    if e.timestamp:
        lines.append(f"  Time: {e.timestamp.isoformat()}")
    if e.body:
        lines.append(f"  Body: {e.body}")
    return "\n".join(lines)


def _serialise_web(w: WebHistory) -> str:
    parts = [f"Web: {w.title or w.url}"]
    if w.url:
        parts.append(f"  URL: {w.url}")
    if w.last_visited:
        parts.append(f"  Visited: {w.last_visited.isoformat()}")
    if w.visit_count:
        parts.append(f"  Visits: {w.visit_count}")
    return "\n".join(parts)


def _serialise_location(loc: Location) -> str:
    parts = [f"Location: {loc.address or f'{loc.latitude}, {loc.longitude}'}"]
    if loc.latitude or loc.longitude:
        parts.append(f"  Coords: {loc.latitude}, {loc.longitude}")
    if loc.timestamp:
        parts.append(f"  Time: {loc.timestamp.isoformat()}")
    if loc.source:
        parts.append(f"  Source: {loc.source}")
    return "\n".join(parts)


def _serialise_app(a: InstalledApp) -> str:
    parts = [f"App: {a.name}"]
    if a.package_name:
        parts.append(f"  Package: {a.package_name}")
    if a.version:
        parts.append(f"  Version: {a.version}")
    return "\n".join(parts)


def _serialise_account(a: Account) -> str:
    parts = [f"Account: {a.username or a.email} @ {a.service}"]
    return "\n".join(parts)


def _serialise_media(m: MediaFile) -> str:
    parts = [f"Media ({m.artifact_type.value}): {m.filename}"]
    if m.file_path:
        parts.append(f"  Path: {m.file_path}")
    if m.mime_type:
        parts.append(f"  Type: {m.mime_type}")
    if m.size_bytes:
        parts.append(f"  Size: {m.size_bytes} bytes")
    if m.exif:
        parts.append(f"  EXIF: {m.exif}")
    return "\n".join(parts)


# ────────────────────────────────────────────────────────
# Batching: group serialised items into token-limited pages
# ────────────────────────────────────────────────────────

def _batch_into_pages(
    items: Sequence[str],
    *,
    artifact_type: str,
    section: str,
    ext_id: str,
    start_page: int,
    max_tokens: int,
) -> list[Page]:
    """Group *items* (serialised artefact strings) into pages respecting *max_tokens*."""
    pages: list[Page] = []
    current_lines: list[str] = []
    current_tokens = 0
    page_num = start_page

    def _flush():
        nonlocal current_lines, current_tokens, page_num
        if not current_lines:
            return
        body = "\n\n".join(current_lines)
        page = Page(
            extraction_id=ext_id,
            artifact_type=artifact_type,
            source_section=section,
            page_number=page_num,
            title=f"{section} (page {page_num})",
            body=body,
            token_count=current_tokens,
        )
        pages.append(page)
        page_num += 1
        current_lines = []
        current_tokens = 0

    for item in items:
        tc = _token_count(item)
        if current_tokens + tc > max_tokens and current_lines:
            _flush()
        current_lines.append(item)
        current_tokens += tc

    _flush()
    return pages


# ────────────────────────────────────────────────────────
# Device info → single page
# ────────────────────────────────────────────────────────

def _device_info_page(extraction: UFDRExtraction, ext_id: str, page_num: int) -> Page | None:
    di = extraction.device_info
    lines = ["Device Information"]
    for label, val in [
        ("Name", di.device_name),
        ("Model", di.model),
        ("OS", di.os_version),
        ("IMEI", di.imei),
        ("Serial", di.serial_number),
        ("Phone", di.phone_number),
        ("Extraction", di.extraction_type),
    ]:
        if val:
            lines.append(f"  {label}: {val}")
    body = "\n".join(lines)
    if len(lines) <= 1:
        return None
    return Page(
        extraction_id=ext_id,
        artifact_type="device_info",
        source_section="Device Information",
        page_number=page_num,
        title="Device Information",
        body=body,
        token_count=_token_count(body),
    )


# ────────────────────────────────────────────────────────
# Main indexer entry-point
# ────────────────────────────────────────────────────────

def index_extraction(extraction: UFDRExtraction) -> list[Page]:
    """Convert a :class:`UFDRExtraction` into a flat list of :class:`Page` objects.

    Each page is bounded by ``settings.page_max_tokens`` tokens so it can be
    embedded in a single call to the embedding model.
    """
    ext_id = _extraction_id(extraction)
    max_tok = settings.page_max_tokens
    pages: list[Page] = []
    page_counter = 1

    # Device info
    dip = _device_info_page(extraction, ext_id, page_counter)
    if dip:
        pages.append(dip)
        page_counter += 1

    # Artefact groups
    _groups: list[tuple[str, str, list[str]]] = [
        ("contact", "Contacts", [_serialise_contact(c) for c in extraction.contacts]),
        ("call_log", "Call Logs", [_serialise_call(c) for c in extraction.call_logs]),
        ("message", "Messages", [_serialise_message(m) for m in extraction.messages]),
        ("email", "Emails", [_serialise_email(e) for e in extraction.emails]),
        ("web_history", "Web History", [_serialise_web(w) for w in extraction.web_history]),
        ("location", "Locations", [_serialise_location(l) for l in extraction.locations]),
        ("installed_app", "Installed Apps", [_serialise_app(a) for a in extraction.installed_apps]),
        ("account", "Accounts", [_serialise_account(a) for a in extraction.accounts]),
        ("media", "Media Files", [_serialise_media(m) for m in extraction.media_files]),
    ]

    for art_type, section, items in _groups:
        if not items:
            continue
        batch = _batch_into_pages(
            items,
            artifact_type=art_type,
            section=section,
            ext_id=ext_id,
            start_page=page_counter,
            max_tokens=max_tok,
        )
        pages.extend(batch)
        page_counter += len(batch)

    logger.info("Indexed %d pages from extraction %s", len(pages), ext_id)
    return pages
