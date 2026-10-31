"""Parallel page fetch with concurrency limit and failure tolerance."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from hackradar.providers.base import FetchProvider
from hackradar.schemas import SearchHit

logger = logging.getLogger("hackradar.fetch")


async def fetch_candidate_pages(
    hits: list[SearchHit],
    provider: FetchProvider,
    max_pages: int = 15,
    max_concurrency: int = 5,
    timeout_seconds: float = 10.0,
) -> list[tuple[SearchHit, str]]:
    """Fetch markdown for top candidate URLs in parallel, skipping failed/empty pages."""
    candidates = hits[:max_pages]
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _fetch_single(hit: SearchHit) -> tuple[SearchHit, str]:
        async with semaphore:
            content = ""
            try:
                # Add timeout protection per page
                content = await asyncio.wait_for(provider.fetch(hit.url), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {hit.url} after {timeout_seconds}s")
            except Exception as e:
                logger.warning(f"Failed to fetch {hit.url}: {e}")

            if not content or not content.strip():
                if hit.snippet and len(hit.snippet.strip()) > 20:
                    logger.info(f"Using search snippet fallback for {hit.url}")
                    return (hit, f"# {hit.title}\n\n{hit.snippet}")
                return (hit, "")

            logger.debug(f"Fetched {len(content)} chars from {hit.url}")
            return (hit, content)

    tasks = [_fetch_single(h) for h in candidates]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_pages: list[tuple[SearchHit, str]] = []
    for res in results:
        if isinstance(res, tuple):
            hit, text = res
            if text:
                valid_pages.append((hit, text))

    logger.info(f"Fetched {len(valid_pages)} successful pages out of {len(candidates)} candidates")
    return valid_pages
