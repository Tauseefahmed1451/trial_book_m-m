"""Notification dispatch and persistence."""

from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models


class NotificationService:
    """Send and track Teams and email notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def notify_outline_ready(self, book_id: str) -> None:
        self._dispatch(book_id, None, "outline_ready", f"Outline ready for review for book {book_id}")

    def notify_chapter_ready(self, book_id: str, chapter_id: str) -> None:
        self._dispatch(book_id, chapter_id, "chapter_ready", f"Chapter ready for review for book {book_id}")

    def notify_paused(self, book_id: str, message: str) -> None:
        self._dispatch(book_id, None, "workflow_paused", message)

    def notify_final_compiled(self, book_id: str) -> None:
        self._dispatch(book_id, None, "final_compiled", f"Final draft compiled for book {book_id}")

    def send_test_teams_message(self) -> None:
        self._send_teams("Book generation system test notification")

    def _dispatch(self, book_id: str, chapter_id: str | None, event_type: str, message: str) -> None:
        payload = {"message": message}
        if self.settings.teams_webhook_url:
            self._create_notification(book_id, chapter_id, event_type, models.NotificationChannel.TEAMS, self.settings.teams_webhook_url, payload)
            self._send_teams(message)
        if self.settings.notification_email_to and self.settings.smtp_host:
            self._create_notification(book_id, chapter_id, event_type, models.NotificationChannel.EMAIL, self.settings.notification_email_to, payload)
            self._send_email(f"[{event_type}] Book generation update", message)

    def _create_notification(
        self,
        book_id: str,
        chapter_id: str | None,
        event_type: str,
        channel: models.NotificationChannel,
        recipient: str,
        payload: dict[str, str],
    ) -> None:
        notification = models.Notification(
            book_id=book_id,
            chapter_id=chapter_id,
            event_type=event_type,
            channel=channel,
            recipient=recipient,
            payload=json.dumps(payload),
            status=models.NotificationState.SENT,
            attempt_count=1,
        )
        self.db.add(notification)

    def _send_teams(self, message: str) -> None:
        if not self.settings.teams_webhook_url:
            return
        with httpx.Client(timeout=10.0) as client:
            client.post(self.settings.teams_webhook_url, json={"text": message}).raise_for_status()

    def _send_email(self, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_username or "noreply@example.com"
        message["To"] = self.settings.notification_email_to
        message.set_content(body)
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
