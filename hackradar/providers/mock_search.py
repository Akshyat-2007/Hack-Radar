"""Mock SearchProvider: reads local hackathons fixture and returns realistic hits."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hackradar.providers.base import SearchProvider
from hackradar.schemas import SearchHit


class MockSearchProvider(SearchProvider):
    """Mock search provider that matches keywords against local hackathon fixtures."""

    def __init__(self, fixture_path: Path | None = None) -> None:
        if fixture_path is None:
            fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "hackathons.json"
        self._fixture_path = fixture_path
        self._data: list[dict[str, Any]] = []
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        if self._fixture_path.exists():
            with open(self._fixture_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = []

    async def search(self, query: str) -> list[SearchHit]:
        """Search fixture data by token matching; falls back to broad sample if few matches."""
        terms = [t.lower() for t in query.split() if len(t) > 2]
        scored_hits: list[tuple[int, SearchHit]] = []

        for item in self._data:
            haystack = (
                f"{item.get('name', '')} {item.get('organizer', '')} "
                f"{item.get('city', '')} {item.get('country', '')} "
                f"{item.get('mode', '')} {' '.join(item.get('themes', []))} "
                f"{item.get('eligibility_text', '')} {item.get('snippet', '')}"
            ).lower()

            score = 0
            for term in terms:
                if term in haystack:
                    score += 1

            # Give a base score if query is generic like 'hackathons' or 'india'
            if score > 0 or not terms:
                hit = SearchHit(
                    title=item.get("name", "Hackathon Event"),
                    url=item.get("url", "https://example.com/hackathon"),
                    snippet=item.get("snippet", item.get("eligibility_text", "")),
                )
                scored_hits.append((score, hit))

        scored_hits.sort(key=lambda x: x[0], reverse=True)

        # If strict matching returned few results, include general pool to simulate web search
        results = [hit for _, hit in scored_hits]
        if len(results) < 3:
            for item in self._data:
                url = item.get("url", "")
                if not any(r.url == url for r in results):
                    results.append(
                        SearchHit(
                            title=item.get("name", "Hackathon"),
                            url=url,
                            snippet=item.get("snippet", ""),
                        )
                    )
                if len(results) >= 5:
                    break

        return results[:8]

    async def close(self) -> None:
        pass
