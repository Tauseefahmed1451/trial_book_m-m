"""API router package."""

from fastapi import APIRouter

from app.api.artifacts import router as artifacts_router
from app.api.books import router as books_router
from app.api.chapters import router as chapters_router
from app.api.outlines import router as outlines_router
from app.api.reviews import router as reviews_router

router = APIRouter()
router.include_router(books_router)
router.include_router(outlines_router)
router.include_router(chapters_router)
router.include_router(reviews_router)
router.include_router(artifacts_router)

__all__ = ["router"]
