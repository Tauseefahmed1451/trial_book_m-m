"""Pydantic schemas for API payloads and responses."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookCreate(BaseModel):
    title: str
    notes_on_outline_before: str
    author_name: str | None = None
    audience: str | None = None
    tone: str | None = None
    language: str = "English"
    research_mode: str = "lightweight"


class OutlineReviewRequest(BaseModel):
    review_status: str
    editor_notes: str | None = None


class ChapterReviewRequest(BaseModel):
    review_status: str
    editor_notes: str | None = None


class OutlineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_no: int
    content_text: str
    status: str
    created_at: datetime


class ChapterVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_no: int
    content_text: str
    summary_text: str
    status: str
    created_at: datetime


class ChapterResponse(BaseModel):
    id: uuid.UUID
    chapter_number: int
    chapter_title: str
    current_status: str
    latest_version: ChapterVersionResponse | None


class ArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_type: str
    file_name: str
    storage_path: str


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    channel: str
    recipient: str
    status: str
    created_at: datetime


class WorkflowEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    event_payload: str
    created_at: datetime


class BookListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    current_stage: str
    current_status: str
    created_at: datetime


class BookDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    current_stage: str
    current_status: str
    latest_outline: OutlineResponse | None = None
    chapters: list[ChapterResponse] = Field(default_factory=list)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)
    notifications: list[NotificationResponse] = Field(default_factory=list)
    events: list[WorkflowEventResponse] = Field(default_factory=list)


class CompileResponse(BaseModel):
    artifacts: list[ArtifactResponse]
