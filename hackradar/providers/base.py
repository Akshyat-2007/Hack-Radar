"""Abstract provider interfaces. Nothing outside providers/ depends on the
concrete implementation; the factory in providers/__init__.py selects one."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from hackradar.schemas import ExtractedEvent, SearchHit


class SearchProvider(ABC):
    """Search the web for hackathon pages."""

    @abstractmethod
    async def search(self, query: str) -> list[SearchHit]:
        """Return a list of {title, url, snippet} for the given query."""

    @abstractmethod
    async def close(self) -> None:
        """Release any resources (e.g. an httpx client)."""


class FetchProvider(ABC):
    """Fetch a URL and return its content as markdown text."""

    @abstractmethod
    async def fetch(self, url: str) -> str:
        """Return markdown content for url, or empty string on failure."""

    @abstractmethod
    async def close(self) -> None:
        """Release any resources."""


class AgentProvider(ABC):
    """Optional deep-scan agent: visit a page and answer a goal."""

    @abstractmethod
    async def run(self, goal: str, url: str) -> dict[str, Any]:
        """Return a JSON-serialisable dict for the goal on the given url."""

    @abstractmethod
    async def close(self) -> None:
        """Release any resources."""


class LLMProvider(ABC):
    """LLM used for structured extraction and scoring."""

    @abstractmethod
    async def extract_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Return a dict conforming to schema. Raises on unrecoverable failure."""

    @abstractmethod
    async def close(self) -> None:
        """Release any resources."""