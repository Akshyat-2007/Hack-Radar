"""Parallel search and URL collection with deduplication."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from hackradar.pipeline.dedupe import dedupe_search_hits
from hackradar.providers.base import SearchProvider
from hackradar.schemas import SearchHit, SearchQuery

logger = logging.getLogger("hackradar.search")


async def search_queries(
    queries: list[SearchQuery],
    provider: SearchProvider,
    max_concurrency: int = 5,
) -> list[SearchHit]:
    """Execute search queries in parallel, collect hits, and deduplicate URLs."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_single(sq: SearchQuery) -> list[SearchHit]:
        async with semaphore:
            try:
                hits = await provider.search(sq.query)
                logger.info(f"Query [{sq.intent}] '{sq.query}' -> {len(hits)} hits")
                return hits
            except Exception as e:
                logger.warning(f"Query '{sq.query}' failed: {e}")
                return []

    tasks = [_run_single(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_hits: list[SearchHit] = []
    for res in results:
        if isinstance(res, list):
            all_hits.extend(res)

    deduped = dedupe_search_hits(all_hits)
    logger.info(f"Collected {len(all_hits)} total hits, {len(deduped)} unique URLs after deduplication")
    return deduped
