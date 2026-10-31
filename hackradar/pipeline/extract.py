"""Structured event extraction from page markdown using LLMProvider and Pydantic validation."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from hackradar.providers.base import LLMProvider
from hackradar.schemas import ExtractedEvent, SearchHit

logger = logging.getLogger("hackradar.extract")

EXTRACT_SCHEMA = ExtractedEvent.model_json_schema()

EXTRACTION_PROMPT_TEMPLATE = """You are an expert hackathon data extractor.
Extract all key details of the hackathon described below into strict JSON.
Follow these rules strictly:
1. Return null for any field that is NOT explicitly stated in the text.
2. NEVER invent, hallucinate, or extrapolate any dates, prizes, or eligibility criteria.
3. If eligibility is ambiguous or unstated, set student_only to null and eligibility_text to the exact phrasing from the page.

Page URL: {url}
Page Title: {title}

Page Content:
{content}
"""


async def extract_events_from_pages(
    pages: list[tuple[SearchHit, str]],
    llm: LLMProvider,
    max_concurrency: int = 4,
    max_llm_calls: int = 15,
) -> list[ExtractedEvent]:
    """Extract and validate ExtractedEvent instances from markdown pages in parallel."""
    target_pages = pages[:max_llm_calls]
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _extract_single(hit: SearchHit, markdown: str) -> list[ExtractedEvent]:
        async with semaphore:
            prompt = EXTRACTION_PROMPT_TEMPLATE.format(
                url=hit.url,
                title=hit.title,
                content=markdown[:4000],  # protect against huge documents
            )
            try:
                data = await llm.extract_json(prompt, EXTRACT_SCHEMA)
                # Ensure the url is set to source URL if missing
                if not data.get("url"):
                    data["url"] = hit.url

                # If the LLM returned a list of events on a multi-hackathon page
                if isinstance(data, list):
                    events = []
                    for item in data:
                        try:
                            events.append(ExtractedEvent.model_validate(item))
                        except Exception as e:
                            logger.warning(f"Validation failed for an item in {hit.url}: {e}")
                    return events

                # Single event dictionary
                event = ExtractedEvent.model_validate(data)
                return [event]
            except Exception as e:
                logger.warning(f"Extraction or validation failed for {hit.url}: {e}")
                return []

    tasks = [_extract_single(hit, text) for hit, text in target_pages]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    extracted: list[ExtractedEvent] = []
    for res in results:
        if isinstance(res, list):
            extracted.extend(res)

    logger.info(f"Extracted {len(extracted)} validated events from {len(target_pages)} pages")
    return extracted
