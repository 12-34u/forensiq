"""Cellebrite archive parser – extracts artefacts from UFDR and CLBE files.

Supports:
* .ufdr archives (ZIP format)
* .clbe archives (Cellebrite backup extraction, ZIP-based)
* Pre-extracted directories containing the same structure

The primary report is ``report.xml`` or ``UFEDReport.xml`` inside the archive.
"""

from __future__ import annotations

import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Iterator

from lxml import etree

from forensiq.ufdr.models import (
    Account,
    ArtifactType,
    CallLog,
    Contact,
    DeviceInfo,
    Email,
    GenericArtifact,
    InstalledApp,
    Location,
    MediaFile,
    Message,
    TimelineEvent,
    UFDRExtraction,
    WebHistory,
)

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────
# Namespace mapping used in Cellebrite XML reports
# ────────────────────────────────────────────────────────
_NS: dict[str, str] = {}  # populated dynamically per-file


def _text(el: etree._Element | None, default: str = "") -> str:
    """Return stripped text content of an element, or *default*."""
    if el is None:
        return default
    return (el.text or "").strip() or default


def _attr(el: etree._Element, name: str, default: str = "") -> str:
    return (el.get(name) or "").strip() or default


# ────────────────────────────────────────────────────────
# Archive / directory handling
# ────────────────────────────────────────────────────────

# Cellebrite file extensions we support
_CELLEBRITE_EXTENSIONS = {".ufdr", ".clbe"}


def _locate_report(root: Path) -> Path | None:
    """Find the main XML report inside an extracted directory."""
    # Standard Cellebrite report names (both UFDR and CLBE use these)
    candidates = [
        "report.xml",
        "UFEDReport.xml",
        "Report.xml",
        "CellebriteReport.xml",
        "ExtractionReport.xml",
    ]
    for name in candidates:
        # Check root level
        p = root / name
        if p.is_file():
            return p
        # Check one level deep
        for child in root.iterdir():
            if child.is_dir():
                p = child / name
                if p.is_file():
                    return p
    # Fallback: any .xml that looks like a report
    for xml_file in root.rglob("*.xml"):
        if xml_file.stat().st_size > 1024:
            return xml_file
    return None


def _extract_ufdr(ufdr_path: Path) -> Path:
    """Extract a .ufdr ZIP archive into a temp directory and return its path."""
    tmp = Path(tempfile.mkdtemp(prefix="forensiq_"))
    logger.info("Extracting UFDR archive to %s", tmp)
    with zipfile.ZipFile(ufdr_path, "r") as zf:
        zf.extractall(tmp)
    return tmp


def _list_all_files(root: Path) -> list[Path]:
    """Recursively list every file under *root*."""
    return [p for p in root.rglob("*") if p.is_file()]


# ────────────────────────────────────────────────────────
# XML section parsers
# ────────────────────────────────────────────────────────

def _parse_device_info(tree: etree._ElementTree) -> DeviceInfo:
    """Extract device metadata from the XML report."""
    info = DeviceInfo()
    root = tree.getroot()
    nsmap = root.nsmap

    # Try multiple XPath patterns common across UFDR versions
    for tag in root.iter():
        if not isinstance(tag.tag, str):
            continue  # skip comments / processing instructions
        tag_local = etree.QName(tag).localname.lower()
        text_val = (tag.text or "").strip()

        if not text_val:
            continue

        if tag_local in ("devicename", "device_name"):
            info.device_name = text_val
        elif tag_local in ("devicemodel", "model"):
            info.model = text_val
        elif tag_local in ("osversion", "os_version"):
            info.os_version = text_val
        elif tag_local in ("imei",):
            info.imei = text_val
        elif tag_local in ("serialnumber", "serial"):
            info.serial_number = text_val
        elif tag_local in ("msisdn", "phonenumber", "phone_number"):
            info.phone_number = text_val
        elif tag_local in ("extractiontype", "extraction_type"):
            info.extraction_type = text_val

    return info


def _iter_model_elements(tree: etree._ElementTree, tag_hint: str) -> Iterator[etree._Element]:
    """Yield all elements whose local tag name contains *tag_hint* (case-insensitive)."""
    hint = tag_hint.lower()
    for el in tree.iter():
        if not isinstance(el.tag, str):
            continue
        local = etree.QName(el).localname.lower()
        if hint in local:
            yield el


def _child_text(parent: etree._Element, *hints: str) -> str:
    """Return text of the first child whose local name contains any of *hints*."""
    for child in parent:
        if not isinstance(child.tag, str):
            continue
        local = etree.QName(child).localname.lower()
        for h in hints:
            if h in local:
                return (child.text or "").strip()
    return ""


def _child_texts(parent: etree._Element, *hints: str) -> list[str]:
    """Return texts of all children whose local name contains any of *hints*."""
    results = []
    for child in parent:
        if not isinstance(child.tag, str):
            continue
        local = etree.QName(child).localname.lower()
        for h in hints:
            if h in local:
                t = (child.text or "").strip()
                if t:
                    results.append(t)
    return results


def _parse_contacts(tree: etree._ElementTree) -> list[Contact]:
    contacts: list[Contact] = []
    for el in _iter_model_elements(tree, "contact"):
        c = Contact(
            name=_child_text(el, "name", "displayname"),
            phone_numbers=_child_texts(el, "phone", "number"),
            emails=_child_texts(el, "email", "mail"),
            organization=_child_text(el, "org", "company"),
            source=_child_text(el, "source", "app"),
        )
        if c.name or c.phone_numbers:
            contacts.append(c)
    return contacts


def _parse_call_logs(tree: etree._ElementTree) -> list[CallLog]:
    logs: list[CallLog] = []
    for el in _iter_model_elements(tree, "call"):
        cl = CallLog(
            direction=_child_text(el, "direction", "type"),
            phone_number=_child_text(el, "number", "phone"),
            contact_name=_child_text(el, "name", "contact"),
            source=_child_text(el, "source", "app"),
        )
        dur = _child_text(el, "duration")
        if dur.isdigit():
            cl.duration_seconds = int(dur)
        if cl.phone_number or cl.contact_name:
            logs.append(cl)
    return logs


def _parse_messages(tree: etree._ElementTree) -> list[Message]:
    messages: list[Message] = []
    for hint in ("sms", "mms", "chat", "message", "instant"):
        for el in _iter_model_elements(tree, hint):
            msg = Message(
                direction=_child_text(el, "direction", "type"),
                sender=_child_text(el, "from", "sender", "party"),
                recipients=_child_texts(el, "to", "recipient"),
                body=_child_text(el, "body", "text", "content", "snippet"),
                source=_child_text(el, "source", "app"),
                thread_id=_child_text(el, "thread", "conversation"),
                attachments=_child_texts(el, "attachment", "file"),
            )
            if "sms" in hint:
                msg.artifact_type = ArtifactType.SMS
            elif "mms" in hint:
                msg.artifact_type = ArtifactType.MMS
            else:
                msg.artifact_type = ArtifactType.CHAT_MESSAGE
            if msg.body or msg.sender:
                messages.append(msg)
    return messages


def _parse_emails(tree: etree._ElementTree) -> list[Email]:
    emails: list[Email] = []
    for el in _iter_model_elements(tree, "email"):
        em = Email(
            sender=_child_text(el, "from", "sender"),
            recipients=_child_texts(el, "to", "recipient"),
            cc=_child_texts(el, "cc"),
            subject=_child_text(el, "subject"),
            body=_child_text(el, "body", "content"),
            attachments=_child_texts(el, "attachment"),
        )
        if em.subject or em.body:
            emails.append(em)
    return emails


def _parse_web_history(tree: etree._ElementTree) -> list[WebHistory]:
    items: list[WebHistory] = []
    for el in _iter_model_elements(tree, "web"):
        wh = WebHistory(
            url=_child_text(el, "url", "address"),
            title=_child_text(el, "title", "name"),
            source=_child_text(el, "source", "browser"),
        )
        vc = _child_text(el, "visit", "count")
        if vc.isdigit():
            wh.visit_count = int(vc)
        if wh.url:
            items.append(wh)
    return items


def _parse_locations(tree: etree._ElementTree) -> list[Location]:
    locations: list[Location] = []
    for el in _iter_model_elements(tree, "location"):
        loc = Location(
            source=_child_text(el, "source", "app"),
            address=_child_text(el, "address", "name"),
        )
        lat = _child_text(el, "lat")
        lon = _child_text(el, "lon", "lng", "long")
        try:
            loc.latitude = float(lat)
            loc.longitude = float(lon)
        except (ValueError, TypeError):
            pass
        if loc.latitude or loc.longitude or loc.address:
            locations.append(loc)
    return locations


def _parse_installed_apps(tree: etree._ElementTree) -> list[InstalledApp]:
    apps: list[InstalledApp] = []
    for el in _iter_model_elements(tree, "application"):
        app = InstalledApp(
            name=_child_text(el, "name", "label"),
            package_name=_child_text(el, "package", "identifier", "bundle"),
            version=_child_text(el, "version"),
        )
        if app.name or app.package_name:
            apps.append(app)
    return apps


def _parse_accounts(tree: etree._ElementTree) -> list[Account]:
    accounts: list[Account] = []
    for el in _iter_model_elements(tree, "account"):
        acc = Account(
            service=_child_text(el, "service", "source", "app"),
            username=_child_text(el, "user", "name", "login"),
            email=_child_text(el, "email", "mail"),
        )
        if acc.username or acc.email:
            accounts.append(acc)
    return accounts


# ────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────

def parse_ufdr(path: str | Path) -> UFDRExtraction:
    """Parse a Cellebrite archive (``.ufdr``, ``.clbe``) **or** an extracted directory.

    Parameters
    ----------
    path:
        Path to a ``.ufdr`` / ``.clbe`` file (ZIP) or a directory containing
        the already-extracted contents.

    Returns
    -------
    UFDRExtraction
        A fully populated extraction model.
    """
    path = Path(path)
    extraction = UFDRExtraction(source_path=str(path))

    # 1. Resolve to a directory
    is_archive = (
        path.is_file()
        and (path.suffix.lower() in _CELLEBRITE_EXTENSIONS or zipfile.is_zipfile(path))
    )
    if is_archive:
        root_dir = _extract_ufdr(path)
    elif path.is_dir():
        root_dir = path
    else:
        raise FileNotFoundError(f"Not a valid Cellebrite archive or directory: {path}")

    # 2. Locate the XML report
    report = _locate_report(root_dir)
    if report is None:
        logger.warning("No XML report found in %s – returning empty extraction", root_dir)
        return extraction

    logger.info("Parsing XML report: %s", report)

    # 3. Parse XML
    try:
        tree = etree.parse(str(report))  # noqa: S320 – trusted local file
    except etree.XMLSyntaxError:
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        tree = etree.parse(str(report), parser)

    # 4. Extract structured artefacts
    extraction.device_info = _parse_device_info(tree)
    extraction.contacts = _parse_contacts(tree)
    extraction.call_logs = _parse_call_logs(tree)
    extraction.messages = _parse_messages(tree)
    extraction.emails = _parse_emails(tree)
    extraction.web_history = _parse_web_history(tree)
    extraction.locations = _parse_locations(tree)
    extraction.installed_apps = _parse_installed_apps(tree)
    extraction.accounts = _parse_accounts(tree)

    logger.info(
        "Extraction complete – %d total artefacts from %s",
        extraction.total_artifacts,
        path.name,
    )
    return extraction
