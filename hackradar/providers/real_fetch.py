"""Production FetchProvider powered by TinyFish Fetch API."""
from __future__ import annotations

import logging
from typing import Any
import httpx

from hackradar.providers.base import FetchProvider

logger = logging.getLogger("hackradar.fetch.tinyfish")


class RealFetchProvider(FetchProvider):
    """Production fetch provider reading live web pages as markdown via TinyFish Fetch API."""

    def __init__(self, api_key: str = "", endpoint: str = "") -> None:
        self.api_key = api_key
        self.endpoint = endpoint or "https://api.fetch.tinyfish.ai"
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=25.0)
        return self._client

    async def fetch(self, url: str) -> str:
        """Fetch page content and return clean markdown text."""
        client = self._get_client()

        # 1. Primary: TinyFish Fetch API
        if self.api_key:
            try:
                response = await client.post(
                    self.endpoint,
                    json={"urls": [url]},
                    headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                )
                if response.status_code == 200:
                    data: dict[str, Any] = response.json()
                    results = data.get("results", [])
                    if results and results[0].get("text"):
                        text = results[0]["text"].strip()
                        if text:
                            logger.info(f"TinyFish Fetch extracted {len(text)} chars from {url}")
                            return text
                else:
                    logger.warning(f"TinyFish Fetch returned HTTP {response.status_code} for {url}")
            except Exception as e:
                logger.warning(f"TinyFish Fetch call failed for {url}: {e}")

        # 2. Resilient fallback: direct fetch if page scraper has transient issue
        try:
            direct_res = await client.get(
                url,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HackRadar/1.0"},
            )
            if direct_res.status_code == 200:
                text = direct_res.text[:8000].strip()
                if text:
                    logger.info(f"Direct fallback fetch extracted {len(text)} chars from {url}")
                    return text
        except Exception as e:
            logger.debug(f"Direct fetch fallback failed for {url}: {e}")

        return ""

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
