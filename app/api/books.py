"""Book and import routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas.books import BookCreate, BookDetailResponse, BookListItem
from app.services.imports import ImportService
from app.services.workflow import WorkflowService

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/books", response_model=BookDetailResponse)
def create_book(payload: BookCreate, db: Session = Depends(get_db)) -> BookDetailResponse:
    workflow = WorkflowService(db)
    book = workflow.create_book(payload)
    db.commit()
    db.refresh(book)
    return workflow.get_book_detail(book.id)


@router.get("/books", response_model=list[BookListItem])
def list_books(db: Session = Depends(get_db)) -> list[BookListItem]:
    books = db.query(models.Book).order_by(models.Book.created_at.desc()).all()
    return [BookListItem.model_validate(book) for book in books]


@router.get("/books/{book_id}", response_model=BookDetailResponse)
def get_book(book_id: uuid.UUID, db: Session = Depends(get_db)) -> BookDetailResponse:
    workflow = WorkflowService(db)
    return workflow.get_book_detail(book_id)


@router.post("/imports/excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, object]:
    content = await file.read()
    service = ImportService(db)
    result = service.import_excel_bytes(file.filename or "uploaded.xlsx", content)
    db.commit()
    return result
