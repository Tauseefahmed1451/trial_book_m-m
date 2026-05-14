"""Book-related ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import BookStage, BookStatus, JSONType, UUIDType


class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(Text, default="English")
    research_mode: Mapped[str] = mapped_column(Text, default="lightweight")
    current_stage: Mapped[BookStage] = mapped_column(Enum(BookStage), default=BookStage.INPUT_PENDING)
    current_status: Mapped[BookStatus] = mapped_column(Enum(BookStatus), default=BookStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    book_input: Mapped[BookInput | None] = relationship(back_populates="book", uselist=False)
    outlines: Mapped[list[Outline]] = relationship(back_populates="book")
    chapters: Mapped[list[Chapter]] = relationship(back_populates="book")
    artifacts: Mapped[list[BookArtifact]] = relationship(back_populates="book")
    notifications: Mapped[list[Notification]] = relationship(back_populates="book")
    events: Mapped[list[WorkflowEvent]] = relationship(back_populates="book")


class BookInput(Base):
    __tablename__ = "book_inputs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("books.id"), unique=True)
    notes_on_outline_before: Mapped[str] = mapped_column(Text, nullable=False)
    notes_on_outline_after: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(Text, default="manual")
    source_row_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    book: Mapped[Book] = relationship(back_populates="book_input")


class InputFile(Base):
    __tablename__ = "input_files"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, default="excel")
    status: Mapped[str] = mapped_column(Text, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rows: Mapped[list[InputRow]] = relationship(back_populates="input_file")


class InputRow(Base):
    __tablename__ = "input_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    input_file_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("input_files.id"))
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_payload: Mapped[str] = mapped_column(JSONType, nullable=False)
    validation_status: Mapped[str] = mapped_column(Text, default="valid")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("books.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    input_file: Mapped[InputFile] = relationship(back_populates="rows")


from app.db.models.chapter import Chapter
from app.db.models.outline import Outline
from app.db.models.system import BookArtifact, Notification, WorkflowEvent
