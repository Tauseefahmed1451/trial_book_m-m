"""Serper-backed research snippet retrieval with graceful fallback."""

from __future__ import annotations

import json

import httpx

from app.core.config import get_settings


class ResearchService:
    """Retrieve normalized snippets for outline or chapter generation."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_snippets(self, query: str, limit: int = 5) -> list[dict[str, str | int | None]]:
        """Fetch web search snippets from Serper or return a deterministic fallback."""
        if not self.settings.serper_api_key:
            return self._fallback(query, limit)

        headers = {
            "X-API-KEY": self.settings.serper_api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query}
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post("https://google.serper.dev/search", headers=headers, json=payload)
                response.raise_for_status()
                organic = response.json().get("organic", [])
            snippets = []
            for index, item in enumerate(organic[:limit], start=1):
                snippets.append(
                    {
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "snippet": item.get("snippet") or "",
                        "rank": index,
                    }
                )
            return snippets or self._fallback(query, limit)
        except Exception:
            return self._fallback(query, limit)

    def _fallback(self, query: str, limit: int) -> list[dict[str, str | int | None]]:
        return [
            {
                "title": f"Fallback source {index}",
                "url": None,
                "snippet": f"Fallback snippet for query '{query}' to keep the workflow runnable without external dependencies.",
                "rank": index,
            }
            for index in range(1, limit + 1)
        ]
