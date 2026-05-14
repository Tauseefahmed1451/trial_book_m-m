"""Outline-related ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import ContentStatus, JSONType, ReviewStatus, UUIDType


class Outline(Base):
    __tablename__ = "outlines"
    __table_args__ = (UniqueConstraint("book_id", "version_no", name="uq_outline_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("books.id"))
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[str] = mapped_column(JSONType, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.PENDING_REVIEW)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    book: Mapped[Book] = relationship(back_populates="outlines")
    review_cycles: Mapped[list[OutlineReviewCycle]] = relationship(back_populates="outline")


class OutlineReviewCycle(Base):
    __tablename__ = "outline_review_cycles"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("books.id"))
    outline_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("outlines.id"))
    review_status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), nullable=False)
    editor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    outline: Mapped[Outline] = relationship(back_populates="review_cycles")


from app.db.models.book import Book
