"""Chapter routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.books import BookDetailResponse, ChapterReviewRequest
from app.services.workflow import WorkflowService

router = APIRouter()


@router.post("/chapters/{chapter_id}/review", response_model=BookDetailResponse)
def review_chapter(
    chapter_id: uuid.UUID,
    payload: ChapterReviewRequest,
    db: Session = Depends(get_db),
) -> BookDetailResponse:
    workflow = WorkflowService(db)
    book_id = workflow.review_chapter(chapter_id, payload)
    db.commit()
    return workflow.get_book_detail(book_id)
