"""MongoDB-backed conversation / chat-history storage.

Each conversation belongs to **one user** (``user_id``). Other users have
no access.  Conversations contain an ordered list of messages (user +
assistant).

Collections used:
    conversations  – one document per conversation
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


def _get_db():
    global _client, _db
    if _db is None:
        uri = settings.mongodb_uri
        if not uri:
            raise RuntimeError("MONGODB_URI is not set in .env")
        _client = AsyncIOMotorClient(uri)
        _db = _client[settings.mongodb_database]
    return _db


async def ensure_indexes():
    """Create indexes for conversations (idempotent)."""
    db = _get_db()
    await db.conversations.create_index("user_id")
    await db.conversations.create_index([("user_id", 1), ("updated_at", -1)])


# ── Helpers ──────────────────────────────────────────────

def _doc_to_dict(doc: dict) -> dict:
    """Convert a MongoDB document to a JSON-safe dict."""
    doc["id"] = str(doc.pop("_id"))
    return doc


# ── Public API ───────────────────────────────────────────

async def create_conversation(*, user_id: str, title: str = "New Conversation") -> dict:
    """Create a new empty conversation owned by *user_id*."""
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": user_id,
        "title": title,
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db.conversations.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("Conversation created: %s for user %s", result.inserted_id, user_id)
    return _doc_to_dict(doc)


async def list_conversations(*, user_id: str) -> list[dict]:
    """Return all conversations for *user_id*, newest first.

    Only returns metadata (id, title, timestamps, message count) – NOT the
    full message bodies, to keep the payload small.
    """
    db = _get_db()
    cursor = db.conversations.find(
        {"user_id": user_id},
        {
            "user_id": 1,
            "title": 1,
            "created_at": 1,
            "updated_at": 1,
            "message_count": {"$size": "$messages"},
        },
    ).sort("updated_at", -1)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)
    return results


async def get_conversation(*, conversation_id: str, user_id: str) -> dict | None:
    """Fetch a full conversation (with messages) only if it belongs to *user_id*."""
    db = _get_db()
    doc = await db.conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": user_id,
    })
    if doc is None:
        return None
    return _doc_to_dict(doc)


async def append_message(
    *,
    conversation_id: str,
    user_id: str,
    message: dict[str, Any],
) -> bool:
    """Append a message to a conversation.

    Returns True on success, False if the conversation doesn't exist
    or doesn't belong to the user.
    """
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()

    # Ensure the message has a timestamp
    message.setdefault("timestamp", now)

    result = await db.conversations.update_one(
        {"_id": ObjectId(conversation_id), "user_id": user_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": now},
        },
    )
    return result.modified_count > 0


async def update_title(
    *,
    conversation_id: str,
    user_id: str,
    title: str,
) -> bool:
    """Rename a conversation (must belong to *user_id*)."""
    db = _get_db()
    result = await db.conversations.update_one(
        {"_id": ObjectId(conversation_id), "user_id": user_id},
        {"$set": {"title": title, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return result.modified_count > 0


async def delete_conversation(*, conversation_id: str, user_id: str) -> bool:
    """Delete a conversation (must belong to *user_id*)."""
    db = _get_db()
    result = await db.conversations.delete_one({
        "_id": ObjectId(conversation_id),
        "user_id": user_id,
    })
    return result.deleted_count > 0
