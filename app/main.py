"""FastAPI entrypoint."""

from fastapi import FastAPI

from app.api import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import create_database


settings = get_settings()
configure_logging(settings.environment)

app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    """Initialize durable resources on application startup."""
    create_database()
