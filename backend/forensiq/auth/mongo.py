"""MongoDB-backed user authentication for ForensIQ."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone

import bcrypt
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None


def _get_db():
    """Lazy-initialise the Motor client and return the database handle."""
    global _client, _db
    if _db is None:
        uri = settings.mongodb_uri
        if not uri:
            raise RuntimeError("MONGODB_URI is not set in .env")
        _client = AsyncIOMotorClient(uri)
        _db = _client[settings.mongodb_database]
        logger.info("Connected to MongoDB database: %s", settings.mongodb_database)
    return _db


async def ensure_indexes():
    """Create unique index on email (idempotent)."""
    db = _get_db()
    await db.users.create_index("email", unique=True)
    await db.user_projects.create_index("user_id")
    await db.user_projects.create_index([("user_id", 1), ("project_id", 1)], unique=True)
    await db.password_resets.create_index("email")
    await db.password_resets.create_index("token", unique=True)


# ── Helpers ─────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _user_to_session(doc: dict) -> dict:
    """Convert a MongoDB user document to a safe session dict (no password)."""
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc.get("role", "Investigator"),
        "department": doc.get("department", ""),
        "avatar": doc.get("avatar", doc["name"][:2].upper()),
        "created_at": doc.get("created_at", ""),
    }


# ── Public API ──────────────────────────────────────────

async def signup(
    *,
    name: str,
    email: str,
    password: str,
    role: str = "Investigating Officer",
    department: str = "",
) -> dict:
    """Create a new user. Raises ValueError if email already exists."""
    db = _get_db()

    existing = await db.users.find_one({"email": email.lower().strip()})
    if existing:
        raise ValueError("A user with this email already exists")

    doc = {
        "name": name.strip(),
        "email": email.lower().strip(),
        "password_hash": _hash_password(password),
        "role": role.strip() or "Investigating Officer",
        "department": department.strip(),
        "avatar": name.strip()[:2].upper() if name.strip() else "??",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    logger.info("New user created: %s (%s)", name, email)
    return _user_to_session(doc)


async def login(*, email: str, password: str) -> dict | None:
    """Verify credentials. Returns session dict on success, None on failure."""
    db = _get_db()
    user = await db.users.find_one({"email": email.lower().strip()})
    if not user:
        return None
    if not _verify_password(password, user["password_hash"]):
        return None
    logger.info("User logged in: %s", email)
    return _user_to_session(user)


# ── User–Project association ─────────────────────────────

async def link_project(*, user_id: str, project_id: str) -> None:
    """Associate a project/extraction with a user (idempotent)."""
    db = _get_db()
    await db.user_projects.update_one(
        {"user_id": user_id, "project_id": project_id},
        {"$setOnInsert": {
            "user_id": user_id,
            "project_id": project_id,
            "linked_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )
    logger.info("Linked project %s → user %s", project_id, user_id)


async def get_user_project_ids(user_id: str) -> list[str]:
    """Return the list of project_ids owned/uploaded by this user."""
    db = _get_db()
    cursor = db.user_projects.find({"user_id": user_id}, {"project_id": 1})
    return [doc["project_id"] async for doc in cursor]


async def get_all_claimed_project_ids() -> set[str]:
    """Return the set of project_ids that are linked to ANY user."""
    db = _get_db()
    cursor = db.user_projects.find({}, {"project_id": 1})
    return {doc["project_id"] async for doc in cursor}


async def bulk_link_projects(*, user_id: str, project_ids: list[str]) -> int:
    """Link multiple projects to a user at once (idempotent). Returns count linked."""
    if not project_ids:
        return 0
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    ops = [
        {
            "user_id": user_id,
            "project_id": pid,
            "linked_at": now,
        }
        for pid in project_ids
    ]
    # Use ordered=False so duplicates silently skip
    from pymongo.errors import BulkWriteError
    try:
        result = await db.user_projects.insert_many(ops, ordered=False)
        count = len(result.inserted_ids)
    except BulkWriteError as bwe:
        count = bwe.details.get("nInserted", 0)
    logger.info("Bulk-linked %d orphan projects → user %s", count, user_id)
    return count


# ── Forgot / Reset Password ─────────────────────────────

async def create_password_reset(email: str) -> str | None:
    """Generate a reset token for the given email.

    Returns the token string on success, or None if the email is not found.
    """
    db = _get_db()
    user = await db.users.find_one({"email": email.lower().strip()})
    if not user:
        return None

    token = secrets.token_urlsafe(32)
    await db.password_resets.insert_one({
        "email": email.lower().strip(),
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "used": False,
    })
    logger.info("Password reset token created for %s", email)
    return token


async def reset_password(token: str, new_password: str) -> bool:
    """Reset the user password using a reset token.

    Returns True on success, False if the token is invalid/already used.
    """
    db = _get_db()
    reset_doc = await db.password_resets.find_one({"token": token, "used": False})
    if not reset_doc:
        return False

    email = reset_doc["email"]
    new_hash = _hash_password(new_password)

    result = await db.users.update_one(
        {"email": email},
        {"$set": {"password_hash": new_hash}},
    )
    if result.modified_count == 0:
        return False

    # Mark token as used
    await db.password_resets.update_one(
        {"_id": reset_doc["_id"]},
        {"$set": {"used": True}},
    )
    logger.info("Password reset for %s", email)
    return True
