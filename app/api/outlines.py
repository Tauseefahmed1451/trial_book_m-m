"""Outline routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.books import BookDetailResponse, OutlineReviewRequest
from app.services.workflow import WorkflowService

router = APIRouter()


@router.post("/books/{book_id}/outline/review", response_model=BookDetailResponse)
def review_outline(
    book_id: uuid.UUID,
    payload: OutlineReviewRequest,
    db: Session = Depends(get_db),
) -> BookDetailResponse:
    workflow = WorkflowService(db)
    workflow.review_outline(book_id, payload)
    db.commit()
    return workflow.get_book_detail(book_id)
