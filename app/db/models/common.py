"""Shared ORM enums and column types."""

from __future__ import annotations

import enum

from sqlalchemy import JSON, Uuid

JSONType = JSON
UUIDType = Uuid(as_uuid=True)


class ReviewStatus(str, enum.Enum):
    YES = "yes"
    NO = "no"
    NO_NOTES_NEEDED = "no_notes_needed"


class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUPERSEDED = "superseded"


class BookStage(str, enum.Enum):
    INPUT_PENDING = "input_pending"
    OUTLINE_REVIEW = "outline_review"
    CHAPTER_REVIEW = "chapter_review"
    FINAL_REVIEW = "final_review"
    COMPILED = "compiled"
    PAUSED = "paused"


class BookStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    TEAMS = "teams"


class NotificationState(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
