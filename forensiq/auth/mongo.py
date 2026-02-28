"""MongoDB-backed user authentication for ForensIQ."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import bcrypt
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
