"""Pydantic models representing forensic artefacts extracted from a UFDR archive."""

from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────────
# Artefact categories mirroring Cellebrite report sections
# ────────────────────────────────────────────────────────

class ArtifactType(str, Enum):
    CONTACT = "contact"
    CALL_LOG = "call_log"
    SMS = "sms"
    MMS = "mms"
    CHAT_MESSAGE = "chat_message"
    EMAIL = "email"
    WEB_HISTORY = "web_history"
    WEB_BOOKMARK = "web_bookmark"
    LOCATION = "location"
    INSTALLED_APP = "installed_app"
    WIRELESS_NETWORK = "wireless_network"
    BLUETOOTH_DEVICE = "bluetooth_device"
    CALENDAR_EVENT = "calendar_event"
    NOTE = "note"
    SOCIAL_MEDIA = "social_media"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    DEVICE_INFO = "device_info"
    ACCOUNT = "account"
    COOKIE = "cookie"
    SEARCHED_ITEM = "searched_item"
    USER_ACTIVITY = "user_activity"
    TIMELINE_EVENT = "timeline_event"
    UNKNOWN = "unknown"


# ────────────────────────────────────────────────────────
# Individual artefact models
# ────────────────────────────────────────────────────────

class DeviceInfo(BaseModel):
    device_name: str = ""
    model: str = ""
    os_version: str = ""
    imei: str = ""
    serial_number: str = ""
    phone_number: str = ""
    extraction_type: str = ""
    extraction_date: dt.datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Contact(BaseModel):
    name: str = ""
    phone_numbers: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    organization: str = ""
    source: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class CallLog(BaseModel):
    direction: str = ""          # incoming / outgoing / missed
    phone_number: str = ""
    contact_name: str = ""
    timestamp: dt.datetime | None = None
    duration_seconds: int = 0
    source: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """Covers SMS, MMS, chat messages."""
    direction: str = ""
    sender: str = ""
    recipients: list[str] = Field(default_factory=list)
    body: str = ""
    timestamp: dt.datetime | None = None
    source: str = ""            # e.g. WhatsApp, iMessage
    thread_id: str = ""
    attachments: list[str] = Field(default_factory=list)
    artifact_type: ArtifactType = ArtifactType.CHAT_MESSAGE
    extra: dict[str, Any] = Field(default_factory=dict)


class Email(BaseModel):
    sender: str = ""
    recipients: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    timestamp: dt.datetime | None = None
    attachments: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class WebHistory(BaseModel):
    url: str = ""
    title: str = ""
    visit_count: int = 0
    last_visited: dt.datetime | None = None
    source: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class Location(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float | None = None
    timestamp: dt.datetime | None = None
    source: str = ""
    address: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class InstalledApp(BaseModel):
    name: str = ""
    package_name: str = ""
    version: str = ""
    install_date: dt.datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class MediaFile(BaseModel):
    """Image / video / audio / document artefact."""
    filename: str = ""
    file_path: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    created: dt.datetime | None = None
    modified: dt.datetime | None = None
    exif: dict[str, Any] = Field(default_factory=dict)
    artifact_type: ArtifactType = ArtifactType.IMAGE
    extra: dict[str, Any] = Field(default_factory=dict)


class Account(BaseModel):
    service: str = ""
    username: str = ""
    email: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    """Generic timeline entry."""
    event_type: str = ""
    description: str = ""
    timestamp: dt.datetime | None = None
    source: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)


class GenericArtifact(BaseModel):
    """Catch-all for artefact types we haven't modelled yet."""
    artifact_type: ArtifactType = ArtifactType.UNKNOWN
    raw_fields: dict[str, Any] = Field(default_factory=dict)
    source: str = ""


# ────────────────────────────────────────────────────────
# Extraction result — everything from one UFDR
# ────────────────────────────────────────────────────────

class UFDRExtraction(BaseModel):
    """Complete parsed result of a single UFDR archive."""
    source_path: str = ""
    device_info: DeviceInfo = Field(default_factory=DeviceInfo)
    contacts: list[Contact] = Field(default_factory=list)
    call_logs: list[CallLog] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    emails: list[Email] = Field(default_factory=list)
    web_history: list[WebHistory] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    installed_apps: list[InstalledApp] = Field(default_factory=list)
    media_files: list[MediaFile] = Field(default_factory=list)
    accounts: list[Account] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    generic: list[GenericArtifact] = Field(default_factory=list)

    @property
    def total_artifacts(self) -> int:
        return (
            len(self.contacts)
            + len(self.call_logs)
            + len(self.messages)
            + len(self.emails)
            + len(self.web_history)
            + len(self.locations)
            + len(self.installed_apps)
            + len(self.media_files)
            + len(self.accounts)
            + len(self.timeline)
            + len(self.generic)
        )
