"""Search Agent — finds venues/events across Google Places, Yelp, Eventbrite, and Ticketmaster.

Uses parallel API calls with per-source timeouts. If ALL external APIs fail,
falls back to Gemini LLM to generate venue recommendations (guaranteed results).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from src.config import settings
from src.models.event import Venue
from src.tools.eventbrite import search_eventbrite
from src.tools.google_places import search_google_places, _search_via_gemini
from src.tools.ticketmaster import search_ticketmaster
from src.tools.yelp import get_yelp_reviews, search_yelp

logger = logging.getLogger(__name__)


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


_search_agent: Agent | None = None


def get_search_agent() -> Agent:
    """Lazy-initialize the search agent (defers API key validation)."""
    global _search_agent
    if _search_agent is None:
        _search_agent = Agent(
            settings.primary_model,
            output_type=SearchResult,
            deps_type=SearchDeps,
            system_prompt=(
                "You are a venue search specialist. Given a user's request for an outing, "
                "use the available tools to find relevant venues and events. "
                "ALWAYS start with tool_search_google_places as it's the most reliable. "
                "Also try Yelp, Eventbrite, and Ticketmaster if relevant. "
                "If a tool returns empty results, that source is unavailable — move on. "
                "Return a curated list of the best matches with a brief summary."
            ),
        )
        _register_search_tools(_search_agent)
    return _search_agent


def _register_search_tools(agent: Agent):
    """Register all tools on the search agent."""

    @agent.tool
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

    @agent.tool
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

    @agent.tool
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

    @agent.tool
    async def tool_search_google_places(
        ctx: RunContext[SearchDeps],
        query: str,
    ) -> list[dict]:
        """Search Google Places for restaurants, bars, activities, and venues. This is the primary search tool.

        Args:
            query: What to search for (e.g., "Italian restaurant with arcade", "bowling alley", "escape room").
        """
        location = ctx.deps.location or settings.default_location
        venues = await search_google_places(
            query=query,
            location=location,
            limit=ctx.deps.max_results_per_source,
        )
        return [v.model_dump(exclude_none=True) for v in venues]


async def _search_source_safe(
    name: str,
    coro,
    timeout: float = 12.0,
) -> tuple[str, list[Venue]]:
    """Run a single search source with its own timeout. Never raises."""
    try:
        venues = await asyncio.wait_for(coro, timeout=timeout)
        logger.info(f"[Search] {name}: returned {len(venues)} venues")
        return name, venues
    except asyncio.TimeoutError:
        logger.warning(f"[Search] {name}: timed out after {timeout}s")
        return name, []
    except Exception as e:
        logger.warning(f"[Search] {name}: failed with {type(e).__name__}: {e}")
        return name, []


async def _run_parallel_search(
    query: str,
    location: str,
    max_results: int = 10,
    per_source_timeout: float = 12.0,
) -> SearchResult:
    """Run all search sources in parallel, returning whatever completes in time.

    This bypasses the LLM agent and calls APIs directly, guaranteeing
    partial results even if some sources are slow or fail.
    """
    loc = location or settings.default_location
    city = loc.split(",")[0].strip()

    # Launch all sources concurrently — each with its own timeout
    tasks = [
        _search_source_safe(
            "Google Places",
            search_google_places(query=query, location=loc, limit=max_results),
            timeout=per_source_timeout,
        ),
        _search_source_safe(
            "Yelp",
            search_yelp(location=loc, term=query, limit=max_results),
            timeout=per_source_timeout,
        ),
        _search_source_safe(
            "Eventbrite",
            search_eventbrite(location=loc, query=query, limit=max_results),
            timeout=per_source_timeout,
        ),
        _search_source_safe(
            "Ticketmaster",
            search_ticketmaster(keyword=query, city=city, limit=max_results),
            timeout=per_source_timeout,
        ),
    ]

    results = await asyncio.gather(*tasks)

    # Collect all venues and track which sources returned data
    all_venues: list[Venue] = []
    sources_searched: list[str] = []
    for source_name, venues in results:
        sources_searched.append(source_name)
        all_venues.extend(venues)

    # Deduplicate by name (case-insensitive)
    seen_names: set[str] = set()
    unique_venues: list[Venue] = []
    for v in all_venues:
        key = v.name.lower().strip()
        if key not in seen_names:
            seen_names.add(key)
            unique_venues.append(v)

    sources_with_results = [
        name for name, venues in results if venues
    ]

    # If ALL sources returned empty, use Gemini LLM as a guaranteed fallback
    if not unique_venues:
        logger.info("[Search] All API sources returned empty — falling back to Gemini LLM")
        try:
            gemini_venues = await asyncio.wait_for(
                _search_via_gemini(query, loc, max_results),
                timeout=per_source_timeout,
            )
            unique_venues = gemini_venues
            sources_searched.append("Gemini LLM")
            sources_with_results.append("Gemini LLM")
            logger.info(f"[Search] Gemini fallback returned {len(gemini_venues)} venues")
        except Exception as e:
            logger.warning(f"[Search] Gemini fallback also failed: {type(e).__name__}: {e}")

    summary = (
        f"Found {len(unique_venues)} unique venues from {', '.join(sources_with_results)}"
        if sources_with_results
        else "No venues found from any source."
    )

    return SearchResult(
        venues=unique_venues,
        summary=summary,
        sources_searched=sources_searched,
    )


async def run_search(
    query: str,
    location: str = "",
    max_results: int = 10,
    timeout_seconds: float = 25.0,
) -> SearchResult:
    """Search for venues across all sources with a hard timeout guarantee.

    Strategy:
    1. Run all API sources in parallel (each with its own 12s timeout)
    2. Collect whatever results come back within the overall timeout
    3. Always return something — never return empty if any source responded

    Args:
        query: What to search for.
        location: Where to search.
        max_results: Max results per source.
        timeout_seconds: Maximum total time allowed (default 25s).
    """
    try:
        result = await asyncio.wait_for(
            _run_parallel_search(query, location, max_results, per_source_timeout=12.0),
            timeout=timeout_seconds,
        )
        return result
    except asyncio.TimeoutError:
        # Even the parallel search hit the outer timeout — return what we can
        return SearchResult(
            venues=[],
            summary=f"Search timed out after {timeout_seconds}s. Try a simpler query.",
            sources_searched=["timeout"],
        )
