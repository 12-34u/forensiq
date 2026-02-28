"""ForensIQ FastAPI application entry-point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from forensiq.api.routes import router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)

app = FastAPI(
    title="ForensIQ",
    version="0.1.0",
    description=(
        "PageIndex RAG for UFDR forensic analysis.\n\n"
        "Ingest Cellebrite UFDR archives → page-indexed artefacts → "
        "FAISS vector search + Neo4j entity graph."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "0.1.0"}
