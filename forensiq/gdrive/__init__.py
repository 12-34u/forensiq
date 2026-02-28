"""Google Drive client – OAuth2 browser-based auth + file/folder download.

Usage:
    1. Place your OAuth2 client credentials JSON at ``config/gdrive_credentials.json``
       (download from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client ID)
    2. The first call to ``authenticate()`` opens a browser for consent.
       A token is cached at ``config/gdrive_token.json`` for subsequent runs.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config.settings import settings

logger = logging.getLogger(__name__)

# Read-only scope is sufficient — we only download files
_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class GDriveClient:
    """Download files / folders from Google Drive via OAuth2."""

    def __init__(
        self,
        credentials_file: Path | None = None,
        token_file: Path | None = None,
        download_dir: Path | None = None,
    ) -> None:
        self._creds_file = credentials_file or settings.gdrive_credentials_file
        self._token_file = token_file or settings.gdrive_token_file
        self._download_dir = download_dir or settings.gdrive_download_dir
        self._download_dir.mkdir(parents=True, exist_ok=True)
        self._service = None

    # ────────────────────────────────────────────────────
    # Auth
    # ────────────────────────────────────────────────────

    def authenticate(self) -> None:
        """Run the OAuth2 flow (opens browser on first use, then caches token)."""
        creds: Credentials | None = None

        if self._token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_file), _SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired Google Drive token …")
                creds.refresh(Request())
            else:
                if not self._creds_file.exists():
                    raise FileNotFoundError(
                        f"OAuth2 credentials not found at {self._creds_file}. "
                        "Download them from Google Cloud Console → APIs & Services → Credentials."
                    )
                logger.info("Starting OAuth2 browser flow …")
                flow = InstalledAppFlow.from_client_secrets_file(str(self._creds_file), _SCOPES)
                creds = flow.run_local_server(port=0)

            # Save token for next run
            self._token_file.parent.mkdir(parents=True, exist_ok=True)
            self._token_file.write_text(creds.to_json())
            logger.info("Token saved to %s", self._token_file)

        self._service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive service authenticated")

    @property
    def service(self):
        if self._service is None:
            self.authenticate()
        return self._service

    # ────────────────────────────────────────────────────
    # Listing
    # ────────────────────────────────────────────────────

    def list_folder(self, folder_id: str) -> list[dict[str, Any]]:
        """List all files inside a Drive folder by its ID.

        Returns list of dicts with keys: ``id``, ``name``, ``mimeType``, ``size``.
        """
        items: list[dict[str, Any]] = []
        page_token = None
        while True:
            resp = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    fields="nextPageToken, files(id, name, mimeType, size)",
                    pageSize=100,
                    pageToken=page_token,
                )
                .execute()
            )
            items.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        logger.info("Listed %d items in folder %s", len(items), folder_id)
        return items

    def list_clbe_files(self, folder_id: str) -> list[dict[str, Any]]:
        """List only ``.clbe`` files inside a Drive folder."""
        all_files = self.list_folder(folder_id)
        clbe = [f for f in all_files if f["name"].lower().endswith(".clbe")]
        logger.info("Found %d .clbe files in folder %s", len(clbe), folder_id)
        return clbe

    # ────────────────────────────────────────────────────
    # Downloading
    # ────────────────────────────────────────────────────

    def download_file(self, file_id: str, filename: str) -> Path:
        """Download a single file from Drive. Returns the local path."""
        dest = self._download_dir / filename
        if dest.exists():
            logger.info("File already downloaded: %s", dest)
            return dest

        logger.info("Downloading %s → %s", filename, dest)
        request = self.service.files().get_media(fileId=file_id)
        with dest.open("wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug("  %d%%", int(status.progress() * 100))
        logger.info("Download complete: %s (%d bytes)", dest, dest.stat().st_size)
        return dest

    def download_folder_clbe(self, folder_id: str) -> list[Path]:
        """Download every ``.clbe`` file from a Drive folder. Returns local paths."""
        files = self.list_clbe_files(folder_id)
        paths: list[Path] = []
        for f in files:
            p = self.download_file(f["id"], f["name"])
            paths.append(p)
        return paths
