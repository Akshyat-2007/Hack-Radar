"""Event filtering: drops expired deadlines, country mismatches, mode mismatches, and out-of-bounds target dates."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from hackradar.pipeline.dedupe import dedupe_events
from hackradar.schemas import ExtractedEvent, Profile

logger = logging.getLogger("hackradar.filter")


def normalize_mode(mode_val: Optional[str]) -> str:
    """Normalize arbitrary LLM mode strings to 'online', 'in-person', or 'hybrid'."""
    if not mode_val:
        return "online"
    m = mode_val.strip().lower()
    if "hybrid" in m:
        return "hybrid"
    if any(k in m for k in ("in-person", "in person", "offline", "on-site", "onsite", "physical", "venue")):
        return "in-person"
    return "online"


def get_target_date_range(target_date: Optional[str], current_date: date) -> tuple[Optional[date], Optional[date]]:
    """Calculate the expected start and end date bounds for a target timeframe."""
    if not target_date or target_date in ("all", "all-2026"):
        return (current_date, date(current_date.year, 12, 31))

    td = target_date.strip().lower()
    if td == "upcoming-30":
        return (current_date, current_date + timedelta(days=30))
    elif td == "upcoming-60":
        return (current_date, current_date + timedelta(days=60))
    elif td == "this-weekend":
        days_ahead = (4 - current_date.weekday()) % 7  # 4 is Friday
        fri = current_date + timedelta(days=days_ahead)
        sun = fri + timedelta(days=2)
        return (fri, sun)
    elif "november" in td:
        return (date(2026, 11, 1), date(2026, 11, 30))
    elif "december" in td:
        return (date(2026, 12, 1), date(2026, 12, 31))
    return (current_date, None)


def filter_and_dedupe_events(
    events: list[ExtractedEvent],
    profile: Profile,
    current_date: Optional[date] = None,
    allow_travel: bool = False,
) -> list[ExtractedEvent]:
    """Filter out expired, out-of-country, mode-mismatched, and date-mismatched events; deduplicate remaining."""
    if current_date is None:
        current_date = datetime.now().date()

    kept_events: list[ExtractedEvent] = []
    target_start, target_end = get_target_date_range(profile.target_date, current_date)

    pref_mode = (profile.mode or "both").strip().lower()

    for event in events:
        # Normalize event.mode
        event.mode = normalize_mode(event.mode)
        event_mode = event.mode

        # 1. Deadline & Expiration check: drop strictly past events
        effective_deadline = event.registration_deadline or event.end_date
        if effective_deadline and effective_deadline < current_date:
            logger.info(f"Dropped expired event: {event.name} (deadline {effective_deadline} < {current_date})")
            continue

        if event.end_date and event.end_date < current_date:
            logger.info(f"Dropped event whose end date passed: {event.name} ({event.end_date} < {current_date})")
            continue

        # 2. Country check
        if event.country and profile.country:
            same_country = event.country.strip().lower() == profile.country.strip().lower()
            if not same_country:
                # If in-person in another country, drop
                if event_mode == "in-person":
                    logger.info(f"Dropped foreign in-person event: {event.name} ({event.country} != {profile.country})")
                    continue
                # If online/hybrid but eligibility restricts to other country/residents
                elig_text = (event.eligibility_text or "").lower()
                if any(f in elig_text for f in ("european", "us only", "us citizen", "resident of us")):
                    logger.info(f"Dropped foreign eligibility event: {event.name}")
                    continue

        # 3. Strict Mode Preference check
        if pref_mode == "online":
            if event_mode == "in-person":
                logger.info(f"Dropped in-person event due to online preference: {event.name}")
                continue
        elif pref_mode == "in-person":
            if event_mode == "online":
                logger.info(f"Dropped online event due to in-person preference: {event.name}")
                continue
            # If hybrid, allow only if venue is near the user
            if event_mode == "hybrid" and profile.city and not allow_travel:
                user_city = profile.city.strip().lower()
                event_city = (event.city or "").strip().lower()
                user_state = (profile.state or "").strip().lower()
                if event_city and user_city not in event_city and event_city not in user_city:
                    if not (user_state and user_state in event_city):
                        logger.info(f"Dropped distant hybrid event: {event.name} in {event.city} (user in {profile.city})")
                        continue

        # 4. In-person location check: must be in user's city/state unless allow_travel is True
        if event_mode == "in-person" and profile.city and not allow_travel:
            user_city = profile.city.strip().lower()
            event_city = (event.city or "").strip().lower()
            user_state = (profile.state or "").strip().lower()

            if event_city and user_city not in event_city and event_city not in user_city:
                if user_state and user_state in event_city:
                    pass
                else:
                    logger.info(f"Dropped distant in-person event: {event.name} in {event.city} (user in {profile.city})")
                    continue

        # 5. Target Date / Timeframe filter
        # If user explicitly specified a target month or sprint:
        if target_start and target_end:
            ev_start = event.start_date or current_date
            ev_end = event.end_date or event.registration_deadline or ev_start

            # Event must overlap or fall within target timeframe:
            # Not ended before target_start, and not starting after target_end
            if ev_end < target_start or ev_start > target_end:
                logger.info(f"Dropped out-of-timeframe event: {event.name} (dates {ev_start}..{ev_end} outside target {target_start}..{target_end})")
                continue

        # 6. Sanity check: If an ongoing hackathon started in the past, update start_date for display
        # so the calendar tile shows the upcoming date or registration deadline, never a dead past date
        if event.start_date and event.start_date < current_date:
            if event.registration_deadline and event.registration_deadline >= current_date:
                # The next active milestone is registration deadline
                event.start_date = event.registration_deadline
            elif event.end_date and event.end_date >= current_date:
                # Active milestone is finale / end date
                event.start_date = event.end_date

        kept_events.append(event)

    # Deduplicate across sources by normalized name + dates
    deduped = dedupe_events(kept_events)
    logger.info(f"Filtered {len(events)} down to {len(kept_events)} candidates, {len(deduped)} after event deduplication")
    return deduped
