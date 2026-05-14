"""Core book workflow orchestration service."""

from __future__ import annotations

import json
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.schemas.books import (
    ArtifactResponse,
    BookCreate,
    BookDetailResponse,
    ChapterResponse,
    ChapterReviewRequest,
    ChapterVersionResponse,
    NotificationResponse,
    OutlineResponse,
    OutlineReviewRequest,
    WorkflowEventResponse,
)
from app.services.llm import LLMService
from app.services.notifications import NotificationService
from app.services.research import ResearchService


class WorkflowService:
    """Create, review, and advance book generation workflows."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMService()
        self.research = ResearchService()
        self.notifications = NotificationService(db)

    def create_book(
        self,
        payload: BookCreate,
        source_type: str = "manual",
        source_row_ref: str | None = None,
    ) -> models.Book:
        """Create a book, generate its outline, and queue the first review gate."""
        book = models.Book(
            title=payload.title,
            author_name=payload.author_name,
            audience=payload.audience,
            tone=payload.tone,
            language=payload.language,
            research_mode=payload.research_mode,
        )
        self.db.add(book)
        self.db.flush()

        book_input = models.BookInput(
            notes_on_outline_before=payload.notes_on_outline_before,
            source_type=source_type,
            source_row_ref=source_row_ref,
        )
        book.book_input = book_input
        self.db.add(book_input)
        self._event(book.id, None, "book_created", {"title": payload.title})

        if not payload.notes_on_outline_before.strip():
            book.current_stage = models.BookStage.PAUSED
            book.current_status = models.BookStatus.PAUSED
            self.notifications.notify_paused(str(book.id), "Missing notes_on_outline_before")
            return book

        self._generate_outline(book)
        return book

    def review_outline(self, book_id: uuid.UUID, payload: OutlineReviewRequest) -> None:
        """Resolve the latest outline review and optionally continue the workflow."""
        book = self._get_book(book_id)
        outline = self._latest_outline(book)
        if outline is None:
            raise HTTPException(status_code=404, detail="Outline not found")

        cycle = models.OutlineReviewCycle(
            book_id=book.id,
            outline_id=outline.id,
            review_status=models.ReviewStatus(payload.review_status),
            editor_notes=payload.editor_notes,
            resolved=True,
        )
        self.db.add(cycle)

        if payload.review_status == models.ReviewStatus.YES.value:
            if not payload.editor_notes:
                raise HTTPException(status_code=400, detail="editor_notes are required when review_status is yes")
            self._generate_outline(book, revision_notes=payload.editor_notes)
            return

        if payload.review_status == models.ReviewStatus.NO_NOTES_NEEDED.value:
            outline.status = models.ContentStatus.APPROVED
            self._seed_chapters_from_outline(book, outline)
            self._generate_next_pending_chapter(book)
            return

        book.current_stage = models.BookStage.PAUSED
        book.current_status = models.BookStatus.PAUSED
        self.notifications.notify_paused(str(book.id), f"Outline review paused for book '{book.title}'")

    def review_chapter(self, chapter_id: uuid.UUID, payload: ChapterReviewRequest) -> uuid.UUID:
        """Resolve a chapter review and advance the workflow when possible."""
        chapter = self.db.get(models.Chapter, chapter_id)
        if chapter is None:
            raise HTTPException(status_code=404, detail="Chapter not found")
        latest = self._latest_chapter_version(chapter)
        if latest is None:
            raise HTTPException(status_code=404, detail="Chapter version not found")

        cycle = models.ChapterReviewCycle(
            chapter_id=chapter.id,
            chapter_version_id=latest.id,
            review_status=models.ReviewStatus(payload.review_status),
            editor_notes=payload.editor_notes,
            resolved=True,
        )
        self.db.add(cycle)

        book = self._get_book(chapter.book_id)
        if payload.review_status == models.ReviewStatus.YES.value:
            if not payload.editor_notes:
                raise HTTPException(status_code=400, detail="editor_notes are required when review_status is yes")
            self._generate_chapter(book, chapter, payload.editor_notes)
            return book.id

        if payload.review_status == models.ReviewStatus.NO_NOTES_NEEDED.value:
            latest.status = models.ContentStatus.APPROVED
            chapter.current_status = models.ContentStatus.APPROVED
            next_chapter = self._next_pending_chapter(book)
            if next_chapter is not None:
                self._generate_chapter(book, next_chapter)
            else:
                book.current_stage = models.BookStage.FINAL_REVIEW
            return book.id

        book.current_stage = models.BookStage.PAUSED
        book.current_status = models.BookStatus.PAUSED
        self.notifications.notify_paused(str(book.id), f"Chapter review paused for '{chapter.chapter_title}'")
        return book.id

    def get_book_detail(self, book_id: uuid.UUID) -> BookDetailResponse:
        """Build an aggregate response for the Streamlit UI."""
        book = self._get_book(book_id)
        outline = self._latest_outline(book)
        latest_outline = OutlineResponse.model_validate(outline, from_attributes=True) if outline else None

        chapters = []
        for chapter in sorted(book.chapters, key=lambda item: item.chapter_number):
            latest_version = self._latest_chapter_version(chapter)
            chapters.append(
                ChapterResponse(
                    id=chapter.id,
                    chapter_number=chapter.chapter_number,
                    chapter_title=chapter.chapter_title,
                    current_status=chapter.current_status.value,
                    latest_version=(
                        ChapterVersionResponse.model_validate(latest_version, from_attributes=True)
                        if latest_version
                        else None
                    ),
                )
            )

        artifacts = [ArtifactResponse.model_validate(item, from_attributes=True) for item in book.artifacts]
        notifications = [
            NotificationResponse(
                id=item.id,
                event_type=item.event_type,
                channel=item.channel.value,
                recipient=item.recipient,
                status=item.status.value,
                created_at=item.created_at,
            )
            for item in sorted(book.notifications, key=lambda entry: entry.created_at, reverse=True)
        ]
        events = [
            WorkflowEventResponse(
                id=item.id,
                event_type=item.event_type,
                event_payload=item.event_payload,
                created_at=item.created_at,
            )
            for item in sorted(book.events, key=lambda entry: entry.created_at, reverse=True)
        ]
        return BookDetailResponse(
            id=book.id,
            title=book.title,
            current_stage=book.current_stage.value,
            current_status=book.current_status.value,
            latest_outline=latest_outline,
            chapters=chapters,
            artifacts=artifacts,
            notifications=notifications,
            events=events,
        )

    def _generate_outline(self, book: models.Book, revision_notes: str | None = None) -> None:
        book.current_stage = models.BookStage.OUTLINE_REVIEW
        book.current_status = models.BookStatus.ACTIVE
        notes = revision_notes or book.book_input.notes_on_outline_before
        draft = self.llm.generate_outline(book.title, notes)

        previous = self._latest_outline(book)
        if previous is not None:
            previous.status = models.ContentStatus.SUPERSEDED

        outline = models.Outline(
            version_no=(previous.version_no + 1 if previous else 1),
            content_json=json.dumps(draft.outline),
            content_text=draft.text,
            model_name=draft.model_name,
            status=models.ContentStatus.PENDING_REVIEW,
        )
        outline.book = book
        self.db.add(outline)
        self.db.flush()
        self._event(book.id, None, "outline_generated", {"outline_id": str(outline.id)})
        self.notifications.notify_outline_ready(str(book.id))

    def _seed_chapters_from_outline(self, book: models.Book, outline: models.Outline) -> None:
        if book.chapters:
            return
        outline_items = json.loads(outline.content_json)
        for item in outline_items:
            chapter = models.Chapter(
                chapter_number=int(item["chapter_number"]),
                chapter_title=str(item["chapter_title"]),
                current_status=models.ContentStatus.DRAFT,
            )
            chapter.book = book
            self.db.add(chapter)
        self.db.flush()
        self._event(book.id, None, "chapters_seeded", {"count": len(outline_items)})

    def _generate_next_pending_chapter(self, book: models.Book) -> None:
        chapter = self._next_pending_chapter(book)
        if chapter is not None:
            self._generate_chapter(book, chapter)

    def _generate_chapter(
        self,
        book: models.Book,
        chapter: models.Chapter,
        chapter_notes: str | None = None,
    ) -> None:
        book.current_stage = models.BookStage.CHAPTER_REVIEW
        book.current_status = models.BookStatus.ACTIVE

        previous = self._latest_chapter_version(chapter)
        if previous is not None:
            previous.status = models.ContentStatus.SUPERSEDED

        latest_outline = self._latest_outline(book)
        outline_text = latest_outline.content_text if latest_outline else ""
        previous_summaries = self._previous_summaries(book, chapter.chapter_number)
        query = f"{book.title} {chapter.chapter_title}"
        snippets = self.research.fetch_snippets(query)
        for item in snippets:
            self.db.add(
                models.ResearchSource(
                    book_id=book.id,
                    chapter_id=chapter.id,
                    query=query,
                    title=item.get("title"),
                    url=item.get("url"),
                    snippet=str(item.get("snippet") or ""),
                    rank=int(item.get("rank") or 0),
                    provider="serper",
                )
            )

        draft = self.llm.generate_chapter(
            title=book.title,
            chapter_title=chapter.chapter_title,
            chapter_number=chapter.chapter_number,
            outline_text=outline_text,
            previous_summaries=previous_summaries,
            chapter_notes=chapter_notes,
            research_snippets=[str(item.get("snippet") or "") for item in snippets],
        )
        version = models.ChapterVersion(
            version_no=(previous.version_no + 1 if previous else 1),
            content_text=draft.content,
            summary_text=draft.summary,
            context_used=previous_summaries,
            model_name=draft.model_name,
            status=models.ContentStatus.PENDING_REVIEW,
            word_count=len(draft.content.split()),
        )
        version.chapter = chapter
        chapter.current_status = models.ContentStatus.PENDING_REVIEW
        self.db.add(version)
        self.db.flush()
        self._event(book.id, chapter.id, "chapter_generated", {"chapter_version_id": str(version.id)})
        self.notifications.notify_chapter_ready(str(book.id), str(chapter.id))

    def _previous_summaries(self, book: models.Book, chapter_number: int) -> str:
        summaries: list[str] = []
        for chapter in sorted(book.chapters, key=lambda item: item.chapter_number):
            if chapter.chapter_number >= chapter_number:
                break
            latest = self._latest_chapter_version(chapter)
            if latest is not None:
                summaries.append(f"Chapter {chapter.chapter_number}: {latest.summary_text}")
        return "\n".join(summaries)

    def _latest_outline(self, book: models.Book) -> models.Outline | None:
        if not book.outlines:
            return None
        return max(book.outlines, key=lambda item: item.version_no)

    def _latest_chapter_version(self, chapter: models.Chapter) -> models.ChapterVersion | None:
        if not chapter.versions:
            return None
        return max(chapter.versions, key=lambda item: item.version_no)

    def _next_pending_chapter(self, book: models.Book) -> models.Chapter | None:
        for chapter in sorted(book.chapters, key=lambda item: item.chapter_number):
            if not chapter.versions or chapter.current_status != models.ContentStatus.APPROVED:
                return chapter
        return None

    def _event(
        self,
        book_id: uuid.UUID,
        chapter_id: uuid.UUID | None,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        self.db.add(
            models.WorkflowEvent(
                book_id=book_id,
                chapter_id=chapter_id,
                event_type=event_type,
                event_payload=json.dumps(payload),
            )
        )

    def _get_book(self, book_id: uuid.UUID) -> models.Book:
        book = self.db.get(models.Book, book_id)
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        return book
