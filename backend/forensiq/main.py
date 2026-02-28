"""ForensIQ FastAPI application entry-point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from forensiq.api.routes import router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)

logger = logging.getLogger(__name__)


# ── Allowed CORS origins ────────────────────────────────
_CORS_ORIGINS: list[str] = [
    "https://forensiq.vercel.app",
    "https://forensiq-theta.vercel.app",
    "http://localhost:8080",       # local vite dev
    "http://localhost:5173",
    "http://localhost:3000",
]
# Regex covers all Vercel preview deploys (*.vercel.app)
_CORS_ORIGIN_REGEX = r"https://.*\.vercel\.app"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # ── Startup ─────────────────────────────────────────
    logger.info("ForensIQ starting up …")

    # Ensure MongoDB indexes (idempotent)
    if settings.mongodb_uri:
        try:
            from forensiq.auth.mongo import ensure_indexes
            await ensure_indexes()
            logger.info("MongoDB indexes ensured")
        except Exception as exc:
            logger.warning("MongoDB index setup skipped: %s", exc)

    yield

    # ── Shutdown ────────────────────────────────────────
    logger.info("ForensIQ shutting down …")


app = FastAPI(
    title="ForensIQ",
    version="0.1.0",
    description=(
        "PageIndex RAG for UFDR forensic analysis.\n\n"
        "Ingest Cellebrite UFDR archives → page-indexed artefacts → "
        "FAISS vector search + Neo4j entity graph."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_origin_regex=_CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health():
    """Dependency-aware health check for Render."""
    checks: dict = {"api": "ok"}

    # ── MongoDB ─────────────────────────────────────────
    if settings.mongodb_uri:
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            c = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
            await c.admin.command("ping")
            checks["mongodb"] = "ok"
        except Exception as exc:
            checks["mongodb"] = f"error: {exc}"
    else:
        checks["mongodb"] = "not_configured"

    # ── Redis ───────────────────────────────────────────
    try:
        import redis as _redis
        r = _redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=3)
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" or v == "not_configured" for v in checks.values()) else "degraded"
    return {"status": overall, "version": "0.1.0", "checks": checks}
