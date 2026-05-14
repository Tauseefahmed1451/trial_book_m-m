"""Artifact storage abstraction."""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings


class LocalStorageProvider:
    """Persist generated files to a local artifacts directory."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.artifacts_path.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, *, book_id: str, file_name: str, content: bytes) -> str:
        """Write bytes to local disk and return the file path."""
        book_dir = self.settings.artifacts_path / book_id
        book_dir.mkdir(parents=True, exist_ok=True)
        path = book_dir / file_name
        path.write_bytes(content)
        return str(path.resolve())


class SupabaseStorageProvider:
    """Placeholder for Supabase storage compatibility through the same interface."""

    def save_bytes(self, *, book_id: str, file_name: str, content: bytes) -> str:
        raise NotImplementedError("Supabase storage provider is intentionally left as an adapter stub.")
