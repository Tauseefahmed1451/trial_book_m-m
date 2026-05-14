"""Artifact routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas.books import CompileResponse
from app.services.compilation import CompilationService
from app.services.notifications import NotificationService

router = APIRouter()


@router.post("/books/{book_id}/compile", response_model=CompileResponse)
def compile_book(book_id: uuid.UUID, db: Session = Depends(get_db)) -> CompileResponse:
    compilation = CompilationService(db)
    artifacts = compilation.compile_book(book_id)
    NotificationService(db).notify_final_compiled(book_id)
    db.commit()
    return CompileResponse(artifacts=artifacts)


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: uuid.UUID, db: Session = Depends(get_db)) -> FileResponse:
    artifact = db.get(models.BookArtifact, artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path=artifact.storage_path, filename=artifact.file_name)
