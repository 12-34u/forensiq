"""Tests for the entity extractor (Graph RAG)."""

from forensiq.graphrag.extractor import extract_entities
from forensiq.graphrag.schema import NodeLabel
from forensiq.pageindex.page import Page


def _make_contact_page() -> Page:
    return Page(
        page_id="test001",
        extraction_id="ext001",
        artifact_type="contact",
        source_section="Contacts",
        page_number=1,
        title="Contacts (page 1)",
        body=(
            "Contact: Alice Smith\n"
            "  Phone(s): +1-555-0100\n"
            "  Email(s): alice@example.com\n"
            "  Org: Acme Corp\n"
            "\n"
            "Contact: Bob Jones\n"
            "  Phone(s): +1-555-0199\n"
        ),
    )


def _make_message_page() -> Page:
    return Page(
        page_id="test002",
        extraction_id="ext001",
        artifact_type="message",
        source_section="Messages",
        page_number=2,
        title="Messages (page 2)",
        body=(
            "CHAT_MESSAGE (outgoing)\n"
            "  From: Alice\n"
            "  To: Bob\n"
            "  App: WhatsApp\n"
            "  Body: Check out https://example.com/docs for the report\n"
        ),
    )


def test_extract_phone_numbers():
    page = _make_contact_page()
    entities = extract_entities(page)
    phones = [e for e in entities if e["label"] == NodeLabel.PHONE_NUMBER]
    assert len(phones) >= 2


def test_extract_emails():
    page = _make_contact_page()
    entities = extract_entities(page)
    emails = [e for e in entities if e["label"] == NodeLabel.EMAIL_ADDRESS]
    assert any(e["key_value"] == "alice@example.com" for e in emails)


def test_extract_persons():
    page = _make_contact_page()
    entities = extract_entities(page)
    persons = [e for e in entities if e["label"] == NodeLabel.PERSON]
    names = [e["props"].get("name", "") for e in persons]
    assert "Alice Smith" in names
    assert "Bob Jones" in names


def test_extract_org():
    page = _make_contact_page()
    entities = extract_entities(page)
    orgs = [e for e in entities if e["label"] == NodeLabel.ORGANIZATION]
    assert any(e["key_value"] == "Acme Corp" for e in orgs)


def test_extract_urls():
    page = _make_message_page()
    entities = extract_entities(page)
    urls = [e for e in entities if e["label"] == NodeLabel.URL]
    assert any("example.com" in e["key_value"] for e in urls)


def test_extract_app():
    page = _make_message_page()
    entities = extract_entities(page)
    apps = [e for e in entities if e["label"] == NodeLabel.APP]
    assert any("whatsapp" in e["key_value"].lower() for e in apps)
