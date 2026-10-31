"""Deduplication and normalization for URLs and hackathon events."""
from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from hackradar.schemas import ExtractedEvent, SearchHit

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "source",
    "fbclid",
    "gclid",
}


def normalize_url(raw_url: str) -> str:
    """Normalize a URL by stripping tracking parameters, www, and trailing slashes."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Filter out tracking query params
        query_pairs = parse_qsl(parsed.query)
        clean_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
        clean_query = urlencode(clean_pairs)

        path = parsed.path.rstrip("/")

        normalized = urlunparse((
            parsed.scheme.lower() or "https",
            netloc,
            path,
            "",
            clean_query,
            "",
        ))
        return normalized
    except Exception:
        return raw_url.strip().rstrip("/")


def dedupe_search_hits(hits: list[SearchHit]) -> list[SearchHit]:
    """Deduplicate a list of SearchHits by normalized URL, preserving order."""
    seen_urls: set[str] = set()
    deduped: list[SearchHit] = []

    for hit in hits:
        norm = normalize_url(hit.url)
        if norm and norm not in seen_urls:
            seen_urls.add(norm)
            deduped.append(hit)

    return deduped


def normalize_event_name(name: str) -> str:
    """Normalize event name for deduplication across platforms (e.g. Devpost vs Unstop mirror)."""
    if not name:
        return ""
    cleaned = name.lower()
    # Remove noise words often added to mirrored listings
    noise_patterns = [
        r"\(devpost mirror\)",
        r"\(unstop mirror\)",
        r"\(official portal\)",
        r"\(mirror\)",
        r"\(expired\)",
        r"official",
        r"portal",
        r"grand finale",
        r"national finale",
        r"finale",
        r"edition",
        r"[^\w\s]",
    ]
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, " ", cleaned)
    # Common hackathon acronym replacements
    cleaned = re.sub(r"\bsih\b", "smart india hackathon", cleaned)
    tokens = [t for t in cleaned.split() if t]
    return " ".join(tokens)


def dedupe_events(events: list[ExtractedEvent]) -> list[ExtractedEvent]:
    """Deduplicate extracted events by normalized name and start date."""
    seen_keys: set[str] = set()
    deduped: list[ExtractedEvent] = []

    for event in events:
        norm_name = normalize_event_name(event.name)
        start_str = str(event.start_date) if event.start_date else "tbd"
        end_str = str(event.end_date) if event.end_date else "tbd"
        key = f"{norm_name}|{start_str}|{end_str}"

        if key in seen_keys:
            continue

        seen_keys.add(key)
        deduped.append(event)

    return deduped
