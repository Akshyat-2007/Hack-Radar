"""Pytest test suite for URL deduplication, event deduplication, and deadline filtering."""
from __future__ import annotations

from datetime import date
import pytest

from hackradar.pipeline.dedupe import (
    dedupe_events,
    dedupe_search_hits,
    normalize_event_name,
    normalize_url,
)
from hackradar.pipeline.filter import filter_and_dedupe_events
from hackradar.schemas import ExtractedEvent, Profile, SearchHit


def test_normalize_url():
    url1 = "https://www.example.com/hackathon/?utm_source=twitter&ref=newsletter"
    url2 = "http://example.com/hackathon"
    
    assert normalize_url(url1) == "https://example.com/hackathon"
    assert normalize_url(url2) == "http://example.com/hackathon"


def test_dedupe_search_hits():
    hits = [
        SearchHit(title="Hack 1", url="https://example.com/hack1?utm_source=google"),
        SearchHit(title="Hack 1 Mirror", url="https://example.com/hack1"),
        SearchHit(title="Hack 2", url="https://example.com/hack2/"),
    ]
    deduped = dedupe_search_hits(hits)
    assert len(deduped) == 2
    assert deduped[0].title == "Hack 1"
    assert deduped[1].title == "Hack 2"


def test_normalize_event_name():
    name1 = "Bengaluru AI Buildathon 2026 (Unstop Mirror)"
    name2 = "Bengaluru AI Buildathon 2026"
    assert normalize_event_name(name1) == normalize_event_name(name2)

    sih1 = "Smart India Hackathon 2026 Grand Finale"
    sih2 = "SIH 2026 Grand Finale (Devpost Mirror)"
    assert normalize_event_name(sih1) == normalize_event_name(sih2)


def test_filter_drops_past_deadline():
    profile = Profile(
        degree="B.Tech",
        stream="CSE",
        country="India",
        mode="both",
    )
    current = date(2026, 10, 31)

    active_event = ExtractedEvent(
        name="Active Hackathon",
        registration_deadline=date(2026, 11, 15),
        end_date=date(2026, 11, 20),
        mode="online",
        country="India",
        url="https://example.com/active",
    )

    expired_event = ExtractedEvent(
        name="Expired Hackathon",
        registration_deadline=date(2026, 10, 15),  # in the past!
        end_date=date(2026, 10, 20),
        mode="online",
        country="India",
        url="https://example.com/expired",
    )

    filtered = filter_and_dedupe_events([active_event, expired_event], profile, current_date=current)
    assert len(filtered) == 1
    assert filtered[0].name == "Active Hackathon"


def test_filter_drops_foreign_event():
    profile = Profile(
        degree="B.Tech",
        stream="CSE",
        country="India",
        mode="both",
    )
    current = date(2026, 10, 31)

    foreign_event = ExtractedEvent(
        name="Munich In-Person Hack",
        registration_deadline=date(2026, 11, 25),
        mode="in-person",
        city="Munich",
        country="Germany",
        eligibility_text="Must be an enrolled student at a European Union university.",
        url="https://example.com/munich",
    )

    filtered = filter_and_dedupe_events([foreign_event], profile, current_date=current)
    assert len(filtered) == 0


def test_dedupe_events_across_platforms():
    event1 = ExtractedEvent(
        name="Bengaluru AI Buildathon 2026",
        start_date=date(2026, 11, 5),
        end_date=date(2026, 11, 6),
        registration_deadline=date(2026, 11, 2),
        mode="in-person",
        city="Bengaluru",
        country="India",
        url="https://techsparks.in/bengaluru-ai-buildathon-2026",
    )

    event2 = ExtractedEvent(
        name="Bengaluru AI Buildathon 2026 (Unstop Mirror)",
        start_date=date(2026, 11, 5),
        end_date=date(2026, 11, 6),
        registration_deadline=date(2026, 11, 2),
        mode="in-person",
        city="Bengaluru",
        country="India",
        url="https://unstop.com/hackathons/bengaluru-ai-buildathon-2026",
    )

    deduped = dedupe_events([event1, event2])
    assert len(deduped) == 1
    assert deduped[0].name == "Bengaluru AI Buildathon 2026"
