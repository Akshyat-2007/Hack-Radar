"""Production AgentProvider powered by TinyFish Agent API."""
from __future__ import annotations

import logging
from typing import Any
import httpx

from hackradar.providers.base import AgentProvider

logger = logging.getLogger("hackradar.agent.tinyfish")


class RealAgentProvider(AgentProvider):
    """Production autonomous agent provider calling TinyFish Agent API."""

    def __init__(self, api_key: str = "", endpoint: str = "") -> None:
        self.api_key = api_key
        self.endpoint = endpoint or "https://agent.tinyfish.ai/v1/automation/run"
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=45.0)
        return self._client

    async def run(self, goal: str, url: str) -> dict[str, Any]:
        """Run an autonomous agent task against a URL via TinyFish."""
        if not self.api_key:
            return {"error": "No TinyFish API key configured"}

        client = self._get_client()
        try:
            res = await client.post(
                self.endpoint,
                headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
                json={"url": url, "goal": goal},
            )
            if res.status_code == 200:
                return res.json()
            return {"error": f"HTTP {res.status_code}: {res.text[:200]}"}
        except Exception as e:
            logger.error(f"TinyFish Agent run failed for {url}: {e}")
            return {"error": str(e)}

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
