"""Mock LLMProvider: deterministic rule/fixture-based extraction conforming to JSON schema."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from hackradar.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Offline mock LLM that extracts structured hackathon fields from markdown."""

    def __init__(self, fixture_path: Path | None = None) -> None:
        if fixture_path is None:
            fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "hackathons.json"
        self._fixture_path = fixture_path
        self._items: list[dict[str, Any]] = []
        if self._fixture_path.exists():
            with open(self._fixture_path, "r", encoding="utf-8") as f:
                self._items = json.load(f)

    async def extract_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Extract hackathon fields from prompt using fixture lookup or regex parser."""
        # 1. Try matching an existing fixture by URL or Name inside the prompt
        for item in self._items:
            url = item.get("url", "")
            name = item.get("name", "")
            if (url and url in prompt) or (name and name.lower() in prompt.lower()):
                # Return exact fixture data filtered to valid fields
                return {
                    "name": item.get("name"),
                    "organizer": item.get("organizer"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "registration_deadline": item.get("registration_deadline"),
                    "mode": item.get("mode"),
                    "city": item.get("city"),
                    "country": item.get("country"),
                    "eligibility_text": item.get("eligibility_text"),
                    "student_only": item.get("student_only"),
                    "allowed_streams": item.get("allowed_streams"),
                    "allowed_years": item.get("allowed_years"),
                    "team_size_min": item.get("team_size_min"),
                    "team_size_max": item.get("team_size_max"),
                    "themes": item.get("themes", []),
                    "prize": item.get("prize"),
                    "url": item.get("url"),
                }

        # 2. Rule-based heuristic parser if not in fixture directly
        name_match = re.search(r"^#\s+(.+)$", prompt, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else "Community Hackathon"

        url_match = re.search(r"https?://[^\s\)\>]+", prompt)
        url = url_match.group(0).rstrip(".,;") if url_match else "https://hackradar.local/event"

        mode = "online"
        if "in-person" in prompt.lower():
            mode = "in-person"
        elif "hybrid" in prompt.lower():
            mode = "hybrid"

        student_only = None
        if "student only: true" in prompt.lower() or "undergraduate students" in prompt.lower():
            student_only = True
        elif "open to all" in prompt.lower():
            student_only = False

        return {
            "name": name,
            "organizer": "Community Organizer",
            "start_date": "2026-11-20",
            "end_date": "2026-11-22",
            "registration_deadline": "2026-11-15",
            "mode": mode,
            "city": "Bengaluru" if "bengaluru" in prompt.lower() else None,
            "country": "India",
            "eligibility_text": "Check page for detailed rules",
            "student_only": student_only,
            "allowed_streams": ["CSE", "IT"] if student_only else None,
            "allowed_years": None,
            "team_size_min": 1,
            "team_size_max": 4,
            "themes": ["AI", "Web Development"],
            "prize": "₹1,00,000",
            "url": url,
        }

    async def close(self) -> None:
        pass
