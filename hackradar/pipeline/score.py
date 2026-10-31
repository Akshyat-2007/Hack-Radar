"""Deterministic heuristic scorer: computes fit_score (0-100), reasons, and flags."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from hackradar.schemas import ExtractedEvent, Profile, ScoredEvent


def score_event(
    event: ExtractedEvent,
    profile: Profile,
    current_date: Optional[date] = None,
) -> ScoredEvent:
    """Score a single hackathon event against the user profile."""
    if current_date is None:
        current_date = datetime.now().date()

    score = 0
    reasons: list[str] = []
    flags: list[str] = []

    # --- 1. Stream / Academic overlap ---
    user_stream = (profile.stream or "").lower()
    user_degree = (profile.degree or "").lower()
    allowed_streams = [s.lower() for s in (event.allowed_streams or [])]

    is_stream_matched = False
    if not event.allowed_streams:
        # Open to all streams or not restricted
        score += 15
        is_stream_matched = True
    else:
        for s in allowed_streams:
            if user_stream in s or s in user_stream or "engineering" in s or "tech" in s:
                score += 25
                is_stream_matched = True
                reasons.append(f"open to {profile.stream} students")
                break
        if not is_stream_matched:
            # Check if degree matches
            if any(user_degree in s for s in allowed_streams):
                score += 20
                is_stream_matched = True
                reasons.append(f"accepts {profile.degree} students")

    # --- 2. Skills and Themes overlap ---
    user_keywords = set()
    for s in profile.skills:
        user_keywords.update(re.findall(r"\w+", s.lower()))
    for i in profile.interests:
        user_keywords.update(re.findall(r"\w+", i.lower()))

    event_text = " ".join([
        event.name or "",
        " ".join(event.themes or []),
        event.eligibility_text or "",
    ]).lower()

    matched_themes: list[str] = []
    for theme in (event.themes or []):
        theme_words = set(re.findall(r"\w+", theme.lower()))
        if theme_words & user_keywords:
            matched_themes.append(theme)

    if matched_themes:
        theme_bonus = min(35, len(matched_themes) * 12 + 10)
        score += theme_bonus
        reasons.append(f"matches your interests in {', '.join(matched_themes[:2])}")
    elif user_keywords:
        # Check raw text overlap
        raw_overlap = [w for w in user_keywords if len(w) > 2 and w in event_text]
        if raw_overlap:
            score += 15
            reasons.append(f"aligns with your {', '.join(raw_overlap[:2])} background")

    # --- 3. Location and Mode Fit ---
    user_city = (profile.city or "").lower()
    event_city = (event.city or "").lower()
    mode = (event.mode or "online").lower()

    if mode == "in-person":
        if user_city and (user_city in event_city or event_city in user_city):
            score += 25
            reasons.append(f"in-person right in {profile.city}")
        else:
            score += 10
    elif mode == "hybrid":
        if user_city and user_city in event_city:
            score += 25
            reasons.append(f"hybrid with in-person venue in {profile.city}")
        else:
            score += 20
            reasons.append("hybrid with flexible online participation")
    else:  # online
        score += 20
        reasons.append("fully online and accessible from anywhere")

    # --- 4. Flags Generation ---
    # Deadline urgency flag
    deadline = event.registration_deadline or event.end_date
    if deadline:
        days_left = (deadline - current_date).days
        if 0 <= days_left <= 3:
            if days_left == 0:
                flags.append("Closes today!")
            elif days_left == 1:
                flags.append("Closes tomorrow!")
            else:
                flags.append(f"Closes in {days_left} days")
        elif days_left < 0:
            flags.append("Deadline passed")

    # Student only flag
    if event.student_only is True:
        flags.append("Students only")
    elif event.student_only is False:
        flags.append("Open to all")

    # Team size flag
    if event.team_size_min and event.team_size_max:
        if event.team_size_min == event.team_size_max:
            flags.append(f"Strict team of {event.team_size_min}")
        else:
            flags.append(f"Needs a team of {event.team_size_min}-{event.team_size_max}")

    # Eligibility clarity flag
    is_ambiguous = (
        event.student_only is None
        or (not event.allowed_streams and event.eligibility_text and "details revealed" in event.eligibility_text.lower())
        or (event.eligibility_text and "unclear" in event.eligibility_text.lower())
    )
    if is_ambiguous:
        flags.append("Eligibility unclear - check the page")

    # Build single one-line reason
    if not reasons:
        reasons.append("Broadly relevant hackathon matching your general technical background")
    reason_str = "Great fit: " + "; ".join(reasons) + "."

    # Clamp fit score between 0 and 100
    final_score = max(0, min(100, score))

    return ScoredEvent(
        **event.model_dump(),
        fit_score=final_score,
        reason=reason_str,
        flags=flags,
        source_urls=[event.url],
    )


def score_and_rank_events(
    events: list[ExtractedEvent],
    profile: Profile,
    current_date: Optional[date] = None,
) -> list[ScoredEvent]:
    """Score all events and sort by fit_score descending and deadline urgency."""
    if current_date is None:
        current_date = datetime.now().date()

    scored = [score_event(ev, profile, current_date=current_date) for ev in events]

    def _sort_key(item: ScoredEvent) -> tuple[int, int]:
        # Primary: fit score descending
        # Secondary: closest deadline (positive days first)
        deadline = item.registration_deadline or item.end_date
        days = 999
        if deadline:
            diff = (deadline - current_date).days
            days = diff if diff >= 0 else 9999
        return (-item.fit_score, days)

    scored.sort(key=_sort_key)
    return scored
