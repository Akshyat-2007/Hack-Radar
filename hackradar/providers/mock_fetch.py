"""Mock FetchProvider: returns markdown representation of hackathon pages."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hackradar.providers.base import FetchProvider


class MockFetchProvider(FetchProvider):
    """Mock fetch provider that returns markdown content from local fixtures or generated from json."""

    def __init__(self, fixture_dir: Path | None = None) -> None:
        base = Path(__file__).resolve().parent.parent / "fixtures"
        self._pages_dir = base / "pages"
        self._json_path = base / "hackathons.json"
        self._data_by_url: dict[str, dict[str, Any]] = {}
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        if self._json_path.exists():
            with open(self._json_path, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    self._data_by_url[item.get("url", "")] = item

    async def fetch(self, url: str) -> str:
        # Check if URL matches a static markdown file
        clean_name = url.rstrip("/").split("/")[-1].replace(".html", "").replace(".md", "")
        candidate_file = self._pages_dir / f"{clean_name}.md"
        if candidate_file.exists():
            return candidate_file.read_text(encoding="utf-8")

        # Fallback to json item
        item = self._data_by_url.get(url)
        if not item:
            # Check for partial URL match
            for k, v in self._data_by_url.items():
                if url in k or k in url:
                    item = v
                    break

        if not item:
            return ""

        # Format markdown page
        themes_str = ", ".join(item.get("themes", []))
        streams_str = ", ".join(item.get("allowed_streams") or ["Open to all"])
        years_str = ", ".join(item.get("allowed_years") or ["Any"])

        return f"""# {item.get('name')}

- **Organizer**: {item.get('organizer', 'N/A')}
- **Start Date**: {item.get('start_date', 'TBD')}
- **End Date**: {item.get('end_date', 'TBD')}
- **Registration Deadline**: {item.get('registration_deadline', 'TBD')}
- **Mode**: {item.get('mode', 'online')}
- **Location**: {item.get('city') or 'Online'}, {item.get('country') or 'Global'}
- **Prize**: {item.get('prize', 'Certificates & Swag')}
- **Team Size**: Min {item.get('team_size_min', 1)}, Max {item.get('team_size_max', 4)}

## Eligibility
{item.get('eligibility_text', 'Open to all participants')}
- Student Only: {item.get('student_only')}
- Allowed Streams: {streams_str}
- Allowed Years: {years_str}

## Themes & Tracks
{themes_str}

## Official Link
{item.get('url')}
"""

    async def close(self) -> None:
        pass
