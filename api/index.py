"""Vercel serverless entrypoint — re-exports the FastAPI app."""
from forensiq.main import app  # noqa: F401
