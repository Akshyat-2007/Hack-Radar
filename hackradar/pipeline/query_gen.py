"""Query generation from user profile using system date."""
from __future__ import annotations

from datetime import datetime
from hackradar.schemas import Profile, SearchQuery


def generate_search_queries(profile: Profile, now: datetime | None = None) -> list[SearchQuery]:
    """Generate 5-6 targeted search queries from a user profile.
    
    Covers:
    - Online events in user's country
    - In-person events in user's city/state
    - Stream-specific hackathons
    - Skill/theme-specific hackathons
    - Major national hackathons
    """
    if now is None:
        now = datetime.now()

    month_name = now.strftime("%B")  # e.g., "October" or "November"
    year = str(now.year)             # e.g., "2026"

    country = profile.country or "India"
    city = profile.city or ""
    state = profile.state or ""
    stream = profile.stream or profile.degree or "engineering"
    skills_slice = " ".join(profile.skills[:2]) if profile.skills else "AI tech"
    interests_slice = " ".join(profile.interests[:2]) if profile.interests else "hackathons"

    target_date = (profile.target_date or "").lower()
    if "weekend" in target_date:
        date_keyword = "this weekend"
    elif "november" in target_date:
        date_keyword = f"November {year}"
    elif "december" in target_date:
        date_keyword = f"December {year}"
    elif "60" in target_date:
        date_keyword = f"upcoming {year}"
    else:
        date_keyword = f"{month_name} {year}"

    queries: list[SearchQuery] = []

    # 1. Online hackathons in country + date
    queries.append(
        SearchQuery(
            query=f"online hackathons {country} {date_keyword}",
            intent="online",
        )
    )

    # 2. City / State hackathons if city specified
    if city:
        loc = f"{city} {state}".strip()
        queries.append(
            SearchQuery(
                query=f"hackathons in {loc} {year}",
                intent="city",
            )
        )
    else:
        queries.append(
            SearchQuery(
                query=f"in-person tech hackathons {country} {year}",
                intent="city",
            )
        )

    # 3. Stream-specific query
    queries.append(
        SearchQuery(
            query=f"hackathons for {stream} students {country} {year}",
            intent="stream",
        )
    )

    # 4. Skills and interest themes
    queries.append(
        SearchQuery(
            query=f"{skills_slice} {interests_slice} hackathon {country} {year}",
            intent="skills",
        )
    )

    # 5. Major national hackathons
    queries.append(
        SearchQuery(
            query=f"national student hackathon {country} {year}",
            intent="national",
        )
    )

    # 6. Mode preference specific query
    if profile.mode == "online":
        queries.append(
            SearchQuery(
                query=f"virtual open online developer hackathon {year}",
                intent="online_mode",
            )
        )
    elif profile.mode == "in-person" and city:
        queries.append(
            SearchQuery(
                query=f"upcoming offline coding competition {city} {year}",
                intent="in_person_mode",
            )
        )
    else:
        queries.append(
            SearchQuery(
                query=f"upcoming college hackathons {country} {year}",
                intent="general",
            )
        )

    return queries
