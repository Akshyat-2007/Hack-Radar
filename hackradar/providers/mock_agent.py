"""Mock AgentProvider: simulates an autonomous scan of a hackathon page."""
from __future__ import annotations

from typing import Any

from hackradar.providers.base import AgentProvider


class MockAgentProvider(AgentProvider):
    """Mock agent provider that returns structured answers for deep verification."""

    async def run(self, goal: str, url: str) -> dict[str, Any]:
        return {
            "status": "success",
            "url": url,
            "goal": goal,
            "findings": {
                "verified": True,
                "notes": "Verified against official terms and schedule.",
            },
        }

    async def close(self) -> None:
        pass
