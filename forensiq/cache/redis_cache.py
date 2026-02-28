"""Redis-backed response cache with automatic in-memory fallback.

Strategy
--------
1. On ``query(prompt)`` we generate a *cache key* by extracting keywords,
   normalising them, and hashing.
2. If a matching entry exists in Redis → return it (cache **hit**).
3. Otherwise → return ``None`` (cache **miss**); caller will use Gemini to
   generate an answer and then call ``store(prompt, response, rag_context)``
   to persist the result with a configurable TTL.
4. When the caller gets a cache hit, it can optionally use a cheaper LLM
   (OpenRouter gpt-oss-120b) to reframe the cached answer for the new
   prompt's exact wording.

Redis data layout::

    forensiq:cache:<sha256_hash> → JSON {
        "prompt": str,
        "keywords": list[str],
        "response": str,
        "rag_context_summary": str,
        "created_at": str (ISO-8601),
        "hit_count": int,
    }

Falls back to a plain dict when Redis is unreachable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Keyword extraction (lightweight, no spaCy) ──────

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would shall should can could may might must of in to for on "
    "with at by from as into about between through after before above "
    "below up down out off over under again further then once here there "
    "when where why how all each every both few more most some any no "
    "not only own same so than too very it its he she they them their "
    "what which who whom this that these those and but or nor if while "
    "i me my we our you your".split()
)

_WORD_RE = re.compile(r"[a-z0-9+@._-]+", re.IGNORECASE)


def extract_keywords(text: str) -> list[str]:
    """Pull meaningful lowercase keywords from *text*."""
    words = _WORD_RE.findall(text.lower())
    return sorted(set(w for w in words if w not in _STOP_WORDS and len(w) > 1))


def cache_key(keywords: list[str]) -> str:
    """Deterministic hash from sorted keyword list."""
    raw = "|".join(keywords)
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


# ── Cache implementation ─────────────────────────────

class ResponseCache:
    """Redis-first cache with in-memory dict fallback."""

    PREFIX = "forensiq:cache:"
    DEFAULT_TTL = 60 * 60 * 24  # 24 hours

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl: int | None = None,
    ) -> None:
        self._ttl = ttl or self.DEFAULT_TTL
        self._redis = None
        self._fallback: dict[str, dict] = {}  # in-memory fallback

        try:
            import redis
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            logger.info("Redis cache connected → %s", redis_url)
        except Exception as exc:
            logger.warning("Redis unavailable (%s), using in-memory fallback", exc)
            self._redis = None

    @property
    def is_redis(self) -> bool:
        return self._redis is not None

    # ── public API ────────────────────────────────────

    def lookup(self, prompt: str) -> dict | None:
        """Check if a response for *prompt* is cached.

        Returns the cached entry dict (with ``response`` key) or ``None``.
        """
        keywords = extract_keywords(prompt)
        if not keywords:
            return None
        key = self.PREFIX + cache_key(keywords)

        entry = self._get(key)
        if entry is None:
            return None

        # Bump hit count
        entry["hit_count"] = entry.get("hit_count", 0) + 1
        self._set(key, entry, ttl=self._ttl)

        logger.info("Cache HIT (hits=%d) for key %s", entry["hit_count"], key[:30])
        return entry

    def store(
        self,
        prompt: str,
        response: str,
        rag_context_summary: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a generated response. Returns the cache key."""
        keywords = extract_keywords(prompt)
        key = self.PREFIX + cache_key(keywords)
        entry = {
            "prompt": prompt,
            "keywords": keywords,
            "response": response,
            "rag_context_summary": rag_context_summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "hit_count": 0,
            **(metadata or {}),
        }
        self._set(key, entry, ttl=self._ttl)
        logger.info("Cache STORE → %s (%d keywords)", key[:30], len(keywords))
        return key

    def invalidate(self, prompt: str) -> bool:
        """Remove cached entry for *prompt*."""
        keywords = extract_keywords(prompt)
        key = self.PREFIX + cache_key(keywords)
        return self._delete(key)

    def flush_all(self) -> None:
        """Clear all ForensIQ cache entries."""
        if self._redis:
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, match=f"{self.PREFIX}*", count=100)
                if keys:
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
        self._fallback.clear()
        logger.info("Cache flushed")

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        if self._redis:
            cursor, keys = self._redis.scan(0, match=f"{self.PREFIX}*", count=10000)
            count = len(keys)
            backend = "redis"
        else:
            count = len(self._fallback)
            backend = "memory"
        return {"backend": backend, "entries": count, "ttl_seconds": self._ttl}

    # ── internal ──────────────────────────────────────

    def _get(self, key: str) -> dict | None:
        if self._redis:
            raw = self._redis.get(key)
            if raw:
                return json.loads(raw)
            return None
        return self._fallback.get(key)

    def _set(self, key: str, data: dict, ttl: int) -> None:
        if self._redis:
            self._redis.setex(key, ttl, json.dumps(data, default=str))
        else:
            self._fallback[key] = data

    def _delete(self, key: str) -> bool:
        if self._redis:
            return bool(self._redis.delete(key))
        return self._fallback.pop(key, None) is not None
