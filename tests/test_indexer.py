"""Smoke tests for the PageIndex indexer."""

from forensiq.pageindex.indexer import index_extraction
from forensiq.pageindex.page import Page
from forensiq.ufdr.models import Contact, Message, ArtifactType, UFDRExtraction


def _make_extraction() -> UFDRExtraction:
    return UFDRExtraction(
        source_path="/tmp/test.ufdr",
        contacts=[
            Contact(name="Alice", phone_numbers=["+1-555-0100"], source="Phonebook"),
            Contact(name="Bob", phone_numbers=["+1-555-0199"], emails=["bob@example.com"]),
        ],
        messages=[
            Message(
                direction="outgoing",
                sender="Alice",
                recipients=["Bob"],
                body="Hey Bob, are you coming to the meeting at 3pm?",
                source="WhatsApp",
                artifact_type=ArtifactType.CHAT_MESSAGE,
            ),
            Message(
                direction="incoming",
                sender="Bob",
                recipients=["Alice"],
                body="Yes I'll be there. Bringing the documents.",
                source="WhatsApp",
                artifact_type=ArtifactType.CHAT_MESSAGE,
            ),
        ],
    )


def test_index_extraction_produces_pages():
    ext = _make_extraction()
    pages = index_extraction(ext)
    assert len(pages) > 0
    assert all(isinstance(p, Page) for p in pages)


def test_pages_have_content():
    ext = _make_extraction()
    pages = index_extraction(ext)
    for page in pages:
        assert page.body
        assert page.artifact_type
        assert page.extraction_id


def test_contact_page_contains_names():
    ext = _make_extraction()
    pages = index_extraction(ext)
    contact_pages = [p for p in pages if p.artifact_type == "contact"]
    assert len(contact_pages) >= 1
    combined = " ".join(p.body for p in contact_pages)
    assert "Alice" in combined
    assert "Bob" in combined


def test_message_page_contains_body():
    ext = _make_extraction()
    pages = index_extraction(ext)
    msg_pages = [p for p in pages if p.artifact_type == "message"]
    assert len(msg_pages) >= 1
    combined = " ".join(p.body for p in msg_pages)
    assert "meeting" in combined.lower()
