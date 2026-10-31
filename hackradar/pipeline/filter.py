"""Event filtering: drops expired deadlines, country mismatches, and far in-person events."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from hackradar.pipeline.dedupe import dedupe_events
from hackradar.schemas import ExtractedEvent, Profile

logger = logging.getLogger("hackradar.filter")


def filter_and_dedupe_events(
    events: list[ExtractedEvent],
    profile: Profile,
    current_date: Optional[date] = None,
    allow_travel: bool = False,
) -> list[ExtractedEvent]:
    """Filter out expired, out-of-country, and location-mismatched events; deduplicate remaining."""
    if current_date is None:
        current_date = datetime.now().date()

    kept_events: list[ExtractedEvent] = []

    for event in events:
        # 1. Deadline check: drop past deadlines
        if event.registration_deadline and event.registration_deadline < current_date:
            logger.info(f"Dropped expired deadline: {event.name} ({event.registration_deadline} < {current_date})")
            continue
        if event.end_date and event.end_date < current_date:
            logger.info(f"Dropped expired end date: {event.name} ({event.end_date} < {current_date})")
            continue

        # 2. Country check
        if event.country and profile.country:
            same_country = event.country.strip().lower() == profile.country.strip().lower()
            if not same_country:
                # If in-person in another country, drop
                if event.mode == "in-person":
                    logger.info(f"Dropped foreign in-person event: {event.name} ({event.country} != {profile.country})")
                    continue
                # If online/hybrid but eligibility restricts to other country/residents
                elig_text = (event.eligibility_text or "").lower()
                if "european" in elig_text or "us only" in elig_text or "resident" in elig_text:
                    logger.info(f"Dropped foreign eligibility event: {event.name}")
                    continue

        # 3. Mode preference & location check
        pref_mode = (profile.mode or "both").lower()
        event_mode = (event.mode or "online").lower()

        if pref_mode == "online" and event_mode == "in-person":
            logger.info(f"Dropped in-person event due to online preference: {event.name}")
            continue

        if pref_mode == "in-person" and event_mode == "online":
            logger.info(f"Dropped online event due to in-person preference: {event.name}")
            continue

        # If in-person event, check if in user's city/state unless allow_travel is True
        if event_mode == "in-person" and profile.city and not allow_travel:
            user_city = profile.city.strip().lower()
            event_city = (event.city or "").strip().lower()
            user_state = (profile.state or "").strip().lower()

            # If event city is stated and doesn't match user's city
            if event_city and user_city not in event_city and event_city not in user_city:
                # Keep if state matches or if hybrid / national finale
                if user_state and user_state in event_city:
                    pass
                else:
                    logger.info(f"Dropped distant in-person event: {event.name} in {event.city} (user in {profile.city})")
                    continue

        kept_events.append(event)

    # 4. Deduplicate across sources by normalized name + dates
    deduped = dedupe_events(kept_events)
    logger.info(f"Filtered {len(events)} down to {len(kept_events)} candidates, {len(deduped)} after event deduplication")
    return deduped
