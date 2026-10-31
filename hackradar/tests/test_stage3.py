"""Stage 3 verification: Extraction, Filters, and Scoring with Pydantic validation."""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hackradar.pipeline.extract import extract_events_from_pages
from hackradar.pipeline.fetch import fetch_candidate_pages
from hackradar.pipeline.filter import filter_and_dedupe_events
from hackradar.pipeline.query_gen import generate_search_queries
from hackradar.pipeline.score import score_and_rank_events
from hackradar.pipeline.search import search_queries
from hackradar.providers import get_providers
from hackradar.schemas import Profile

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


async def run_stage3_demo() -> None:
    print("=" * 85)
    print("STAGE 3 DEMO: Extraction -> Filter -> Score -> Ranked Terminal Table")
    print("=" * 85)

    profile = Profile(
        degree="B.Tech",
        stream="CSE",
        year="3",
        skills=["Python", "AI", "Agents", "FastAPI"],
        interests=["Generative AI", "Web3", "Cybersecurity"],
        city="Bengaluru",
        state="Karnataka",
        country="India",
        mode="both",
    )

    print(f"Target User: {profile.degree} {profile.stream} ({profile.city}, {profile.country})")
    print(f"Skills: {', '.join(profile.skills)} | Interests: {', '.join(profile.interests)}\n")

    # 1. Query & Search
    queries = generate_search_queries(profile)
    providers = get_providers()
    hits = await search_queries(queries, providers.search)
    print(f"[1] Searched {len(queries)} queries -> {len(hits)} unique URLs found.")

    # 2. Fetch pages
    pages = await fetch_candidate_pages(hits, providers.fetch, max_pages=15)
    print(f"[2] Fetched {len(pages)} candidate pages.")

    # 3. Extract with LLM & Pydantic validation
    extracted = await extract_events_from_pages(pages, providers.llm, max_llm_calls=15)
    print(f"[3] Extracted {len(extracted)} structured events with Pydantic validation.")
    assert len(extracted) > 0

    # 4. Filter expired, foreign, far-away, and duplicates
    current_date = date(2026, 10, 31)
    filtered = filter_and_dedupe_events(extracted, profile, current_date=current_date)
    print(f"[4] Filtered & Deduped: {len(extracted)} -> {len(filtered)} eligible events.")

    # Verify that expired and foreign events were dropped:
    names = [e.name for e in filtered]
    assert not any("EXPIRED" in n for n in names), "Expired event should have been filtered!"
    assert not any("EuroHacks" in n for n in names), "Foreign non-eligible event should have been filtered!"

    # 5. Score & Rank
    ranked = score_and_rank_events(filtered, profile, current_date=current_date)
    print(f"[5] Scored and ranked {len(ranked)} events.\n")

    # Print Table
    header = f"{'RANK':<5} | {'FIT':<4} | {'NAME':<34} | {'MODE / CITY':<20} | {'DEADLINE':<12} | {'FLAGS'}"
    print("-" * 110)
    print(header)
    print("-" * 110)

    for i, ev in enumerate(ranked, 1):
        loc = f"{ev.mode or 'online'} ({ev.city or 'Remote'})"
        deadline_str = str(ev.registration_deadline or ev.end_date or "TBD")
        flags_str = ", ".join(ev.flags[:2])
        print(f"#{i:<4} | {ev.fit_score:<4} | {ev.name[:34]:<34} | {loc[:20]:<20} | {deadline_str:<12} | {flags_str}")
        print(f"       \\-- Reason: {ev.reason}")
        print()

    print("-" * 110)
    print("STAGE 3 VERIFICATION PASSED SUCCESSFULLY!")
    print("=" * 85)


if __name__ == "__main__":
    asyncio.run(run_stage3_demo())
