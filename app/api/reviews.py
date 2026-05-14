"""Notification and auxiliary review routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.notifications import NotificationService

router = APIRouter()


@router.post("/notifications/test/teams")
def test_teams_notification(db: Session = Depends(get_db)) -> dict[str, str]:
    NotificationService(db).send_test_teams_message()
    db.commit()
    return {"status": "queued"}
