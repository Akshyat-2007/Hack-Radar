"""Pydantic models shared across the pipeline."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str
    intent: str  # e.g. "online", "city", "stream", "national"


class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str = ""


class ExtractedEvent(BaseModel):
    """Structured data extracted from a single hackathon page (or a single entry
    on a listing page). Any field not stated by the source is null — never invented."""

    name: str
    organizer: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_deadline: Optional[date] = None
    mode: Optional[str] = None  # online | in-person | hybrid
    city: Optional[str] = None
    country: Optional[str] = None
    eligibility_text: Optional[str] = None
    student_only: Optional[bool] = None
    allowed_streams: Optional[list[str]] = None
    allowed_years: Optional[list[str]] = None
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    themes: list[str] = Field(default_factory=list)
    prize: Optional[str] = None
    url: str


class ScoredEvent(ExtractedEvent):
    fit_score: int = 0
    reason: str = ""
    flags: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    degree: str
    stream: str
    year: Optional[str] = None  # e.g. "3" or "2027"
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    mode: str = "both"  # online | in-person | both
    target_date: Optional[str] = "upcoming-30"  # e.g. upcoming-30, this-weekend, november-2026