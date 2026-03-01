"""Security dependencies for FastAPI route protection.

Provides:
- ``get_current_user``: JWT verification dependency (use on protected routes)
- ``rate_limit_key``:   Key function for rate limiting by IP
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import settings

logger = logging.getLogger(__name__)

# ── JWT verification ────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """Decode and validate the JWT from the ``Authorization: Bearer <token>`` header.

    Returns the token payload dict on success.
    Raises 401 if the token is missing, expired, or invalid.
    """
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = creds.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired — please log in again")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")

    # Basic sanity checks
    if "sub" not in payload or "email" not in payload:
        raise HTTPException(status_code=401, detail="Malformed token payload")

    return payload


# ── Rate limiting helpers ───────────────────────────────

# Simple in-memory rate limiter (no extra dependency needed)
# Tracks {ip: [(timestamp, ...)] } with a sliding window

from collections import defaultdict
import time
import threading

_lock = threading.Lock()
_attempts: dict[str, list[float]] = defaultdict(list)

# Config
_MAX_AUTH_ATTEMPTS = 5       # max attempts per window
_AUTH_WINDOW_SECONDS = 300   # 5-minute sliding window


def check_rate_limit(request: Request, *, max_attempts: int = _MAX_AUTH_ATTEMPTS, window: int = _AUTH_WINDOW_SECONDS):
    """Raise 429 if the client IP has exceeded the rate limit.

    Call this at the top of login/signup handlers.
    """
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    with _lock:
        # Prune old entries
        _attempts[ip] = [t for t in _attempts[ip] if now - t < window]

        if len(_attempts[ip]) >= max_attempts:
            logger.warning("Rate limit exceeded for IP %s", ip)
            raise HTTPException(
                status_code=429,
                detail=f"Too many attempts. Try again in {window // 60} minutes.",
            )

        _attempts[ip].append(now)
