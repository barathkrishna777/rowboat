"""Search Agent — finds venues/events across Yelp, Eventbrite, and Ticketmaster."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from src.config import settings
from src.models.event import Venue
from src.tools.eventbrite import search_eventbrite
from src.tools.ticketmaster import search_ticketmaster
from src.tools.yelp import get_yelp_reviews, search_yelp


class SearchResult(BaseModel):
    """Structured output from the Search Agent."""

    venues: list[Venue] = Field(default_factory=list)
    summary: str = ""
    sources_searched: list[str] = Field(default_factory=list)


@dataclass
class SearchDeps:
    """Dependencies injected into the search agent."""

    location: str = ""
    max_results_per_source: int = 10


search_agent = Agent(
    settings.primary_model,
    result_type=SearchResult,
    deps_type=SearchDeps,
    system_prompt=(
        "You are a venue search specialist. Given a user's request for an outing, "
        "use the available tools to find relevant venues and events. "
        "Search multiple sources (Yelp for restaurants/bars/activities, "
        "Eventbrite for events, Ticketmaster for concerts/shows) as appropriate. "
        "Return a curated list of the best matches with a brief summary."
    ),
)


@search_agent.tool
async def tool_search_yelp(
    ctx: RunContext[SearchDeps],
    term: str,
    categories: str = "",
    price: str = "",
) -> list[dict]:
    """Search Yelp for restaurants, bars, and local businesses.

    Args:
        term: What to search for (e.g., "Italian dinner", "bowling alley").
        categories: Yelp categories to filter (e.g., "restaurants", "bars", "active").
        price: Price filter — comma-separated levels 1-4 (e.g., "1,2" for $ and $$).
    """
    location = ctx.deps.location or settings.default_location
    venues = await search_yelp(
        location=location,
        term=term,
        categories=categories or None,
        price=price or None,
        limit=ctx.deps.max_results_per_source,
    )
    return [v.model_dump(exclude_none=True) for v in venues]


@search_agent.tool
async def tool_search_eventbrite(
    ctx: RunContext[SearchDeps],
    query: str,
    start_date: str = "",
    price: str = "",
) -> list[dict]:
    """Search Eventbrite for events and experiences.

    Args:
        query: What to search for (e.g., "food festival", "art class").
        start_date: Filter events starting from this date (ISO format, e.g., "2026-04-01T00:00:00Z").
        price: "free" or "paid" to filter by price.
    """
    location = ctx.deps.location or settings.default_location
    venues = await search_eventbrite(
        location=location,
        query=query,
        start_date=start_date or None,
        price=price or None,
        limit=ctx.deps.max_results_per_source,
    )
    return [v.model_dump(exclude_none=True) for v in venues]


@search_agent.tool
async def tool_search_ticketmaster(
    ctx: RunContext[SearchDeps],
    keyword: str,
    classification: str = "",
    start_date: str = "",
) -> list[dict]:
    """Search Ticketmaster for concerts, sports, and shows.

    Args:
        keyword: What to search for (e.g., "jazz concert", "basketball").
        classification: Genre filter (e.g., "Music", "Sports", "Arts & Theatre").
        start_date: Filter events starting from this date (ISO format).
    """
    location = ctx.deps.location or settings.default_location
    city = location.split(",")[0].strip()
    venues = await search_ticketmaster(
        keyword=keyword,
        classification=classification or None,
        start_date=start_date or None,
        city=city,
        limit=ctx.deps.max_results_per_source,
    )
    return [v.model_dump(exclude_none=True) for v in venues]


async def run_search(query: str, location: str = "", max_results: int = 10) -> SearchResult:
    """Convenience function to run the search agent."""
    deps = SearchDeps(location=location or settings.default_location, max_results_per_source=max_results)
    result = await search_agent.run(query, deps=deps)
    return result.data
