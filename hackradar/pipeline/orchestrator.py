"""Pipeline orchestrator: coordinates search, fetch, extract, filter, and score with SSE streaming."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator

from hackradar.pipeline.extract import extract_events_from_pages
from hackradar.pipeline.fetch import fetch_candidate_pages
from hackradar.pipeline.filter import filter_and_dedupe_events
from hackradar.pipeline.query_gen import generate_search_queries
from hackradar.pipeline.score import score_and_rank_events
from hackradar.pipeline.search import search_queries
from hackradar.providers import get_providers
from hackradar.schemas import Profile, ScoredEvent

logger = logging.getLogger("hackradar.orchestrator")


async def run_search_pipeline(profile: Profile) -> AsyncGenerator[dict, None]:
    """Run the end-to-end hackathon search pipeline and yield SSE events."""
    now = datetime.now()
    providers = get_providers()

    try:
        # Step 1: Query generation
        yield {"type": "progress", "message": f"Analyzing profile & generating targeted search queries ({now.strftime('%B %Y')})..."}
        queries = generate_search_queries(profile, now=now)
        await asyncio.sleep(0.1)

        # Step 2: Search in parallel & dedupe URLs
        yield {"type": "progress", "message": f"Searching web with {len(queries)} parallel queries..."}
        hits = await search_queries(queries, providers.search)
        if not hits:
            yield {"type": "progress", "message": "No candidates found from initial queries."}
            yield {"type": "done", "total": 0}
            return

        yield {"type": "progress", "message": f"Found {len(hits)} unique URLs. Fetching top pages in parallel..."}
        await asyncio.sleep(0.1)

        # Step 3: Fetch candidate pages
        pages = await fetch_candidate_pages(hits, providers.fetch, max_pages=15)
        if not pages:
            yield {"type": "progress", "message": "Failed to fetch candidate pages."}
            yield {"type": "done", "total": 0}
            return

        # Step 4: Extract structured JSON via LLM
        yield {"type": "progress", "message": f"Extracting structured event criteria from {len(pages)} pages via LLM..."}
        extracted = await extract_events_from_pages(pages, providers.llm, max_llm_calls=15)

        # Step 5: Filter expired, country mismatch, and far-away events
        yield {"type": "progress", "message": f"Verifying registration deadlines and eligibility rules..."}
        filtered = filter_and_dedupe_events(extracted, profile, current_date=now.date())

        # Step 6: Score and rank events
        yield {"type": "progress", "message": f"Scoring profile fit and ranking {len(filtered)} verified hackathons..."}
        ranked = score_and_rank_events(filtered, profile, current_date=now.date())
        await asyncio.sleep(0.15)

        # Step 7: Stream results one by one to UI
        for event in ranked:
            yield {"type": "result", "event": event.model_dump(mode="json")}
            await asyncio.sleep(0.08)  # visually pleasant streaming rhythm

        yield {"type": "progress", "message": f"Search complete! Ranked {len(ranked)} eligible hackathons."}
        yield {"type": "done", "total": len(ranked)}

    except Exception as e:
        logger.exception("Pipeline execution failed")
        yield {"type": "error", "message": f"Pipeline error: {str(e)}"}
