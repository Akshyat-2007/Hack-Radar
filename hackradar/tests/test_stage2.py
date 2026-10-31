"""Stage 2 CLI test: query generation, parallel search, dedupe, and fetch."""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hackradar.pipeline.fetch import fetch_candidate_pages
from hackradar.pipeline.query_gen import generate_search_queries
from hackradar.pipeline.search import search_queries
from hackradar.providers import get_providers
from hackradar.schemas import Profile

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def run_stage2_demo() -> None:
    print("=" * 60)
    print("STAGE 2 PIPELINE DEMO: Query Gen -> Search -> Dedupe -> Fetch")
    print("=" * 60)

    # Sample profile
    profile = Profile(
        degree="B.Tech",
        stream="CSE",
        year="3",
        skills=["Python", "AI", "FastAPI"],
        interests=["Autonomous Agents", "Web3", "Hackathons"],
        city="Bengaluru",
        state="Karnataka",
        country="India",
        mode="both",
    )

    print(f"\n[1] User Profile: {profile.degree} {profile.stream}, Year {profile.year}")
    print(f"    Location: {profile.city}, {profile.state}, {profile.country} | Mode: {profile.mode}")
    print(f"    Skills: {', '.join(profile.skills)} | Interests: {', '.join(profile.interests)}")

    # 1. Query Generation
    queries = generate_search_queries(profile)
    print(f"\n[2] Generated {len(queries)} search queries:")
    for i, q in enumerate(queries, 1):
        print(f"    {i}. [{q.intent}] {q.query}")

    assert len(queries) >= 5, "Should generate at least 5 queries"

    # 2. Search & Dedupe
    providers = get_providers()
    hits = await search_queries(queries, providers.search)
    print(f"\n[3] Search & Dedupe returned {len(hits)} unique URLs:")
    for i, h in enumerate(hits[:8], 1):
        print(f"    {i}. {h.title} -> {h.url}")

    assert len(hits) > 0, "Should have found search hits"

    # 3. Fetch Candidate Pages
    fetched = await fetch_candidate_pages(hits, providers.fetch, max_pages=15)
    print(f"\n[4] Fetched {len(fetched)} candidate pages successfully:")
    for i, (hit, content) in enumerate(fetched[:5], 1):
        first_line = content.strip().split("\n")[0] if content else "Empty"
        print(f"    {i}. [{hit.url}] ({len(content)} chars) -> {first_line}")

    assert len(fetched) > 0, "Should have fetched candidate pages"

    print("\nSTAGE 2 VERIFICATION PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_stage2_demo())
