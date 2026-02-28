"""Centralised application settings loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenAI ──────────────────────────────────────────
    openai_api_key: str = ""

    # ── Neo4j ───────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "forensiq_secret"
    neo4j_database: str = "neo4j"

    # ── FAISS ───────────────────────────────────────────
    faiss_index_dir: Path = _ROOT / "data" / "faiss_index"

    # ── PageIndex ───────────────────────────────────────
    pageindex_store_dir: Path = _ROOT / "data" / "pageindex"

    # ── Upload / data ───────────────────────────────────
    ufdr_upload_dir: Path = _ROOT / "data" / "uploads"

    # ── Embedding (Gemini) ──────────────────────────────
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 3072

    # ── PageIndex tuning ────────────────────────────────
    page_max_tokens: int = 512

    # ── Google Drive ─────────────────────────────────────
    gdrive_credentials_file: Path = _ROOT / "config" / "gdrive_credentials.json"
    gdrive_token_file: Path = _ROOT / "config" / "gdrive_token.json"
    gdrive_download_dir: Path = _ROOT / "data" / "gdrive_downloads"

    # ── Logging ─────────────────────────────────────────
    log_level: str = "INFO"

    # ── Gemini (primary LLM) ─────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # ── OpenRouter (cached reframes) ─────────────────────
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-oss-120b:free"

    # ── Redis ────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 86400  # 24 hours

    # ── MongoDB (user auth) ──────────────────────────────
    mongodb_uri: str = ""
    mongodb_database: str = "forensiq"

    # ── JWT ──────────────────────────────────────────────
    jwt_secret: str = "forensiq-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72


settings = Settings()
