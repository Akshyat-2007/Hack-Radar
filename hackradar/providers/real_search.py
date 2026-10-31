"""Production SearchProvider powered by TinyFish Search API."""
from __future__ import annotations

import logging
from typing import Any
import httpx

from hackradar.providers.base import SearchProvider
from hackradar.schemas import SearchHit

logger = logging.getLogger("hackradar.search.tinyfish")


class RealSearchProvider(SearchProvider):
    """Production search provider calling TinyFish Search API."""

    def __init__(self, api_key: str = "", endpoint: str = "") -> None:
        self.api_key = api_key
        self.endpoint = endpoint or "https://api.search.tinyfish.ai"
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=20.0)
        return self._client

    async def search(self, query: str) -> list[SearchHit]:
        """Execute web search query via TinyFish Search API."""
        if not self.api_key:
            logger.warning("RealSearchProvider: No TinyFish API key configured.")
            return []

        client = self._get_client()
        try:
            response = await client.get(
                self.endpoint,
                params={"query": query},
                headers={"X-API-Key": self.api_key, "Accept": "application/json"},
            )
            if response.status_code != 200:
                logger.error(
                    f"TinyFish Search API failed with HTTP {response.status_code}: {response.text[:200]}"
                )
                return []

            data: dict[str, Any] = response.json()
            raw_results = data.get("results", [])
            hits: list[SearchHit] = []
            for item in raw_results:
                title = item.get("title") or item.get("site_name") or "Hackathon Event"
                url = item.get("url") or ""
                snippet = item.get("snippet") or ""
                if url:
                    hits.append(SearchHit(title=title, url=url, snippet=snippet))

            logger.info(f"TinyFish Search for '{query}' returned {len(hits)} hits.")
            return hits
        except Exception as e:
            logger.error(f"Error querying TinyFish Search API for '{query}': {e}")
            return []

    async def close(self) -> None:
        """Release HTTP clients / connections."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
