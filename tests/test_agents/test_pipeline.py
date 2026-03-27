"""Integration tests for the AI agent pipeline.

These tests make LIVE API calls (Claude / Gemini) and are skipped automatically
when no LLM key is configured.  Run them explicitly with:

    pytest tests/test_agents/test_pipeline.py -v

or as part of the full suite whenever an API key is present (they are
automatically collected — the skip decorators handle the rest).

Each test is kept deliberately simple so it acts as a smoke test:
  - Does the agent return results at all?
  - Does the pipeline complete the expected steps?
  - Is the output structurally valid?
"""

from __future__ import annotations

import pytest

from src.config import settings

# Skip the entire module if no LLM key is available
_no_llm = not (settings.anthropic_api_key or settings.gemini_api_key or settings.google_api_key)
pytestmark = pytest.mark.skipif(_no_llm, reason="No LLM API key configured")


# ── Search Agent ───────────────────────────────────────────────────────


async def test_search_returns_venues():
    """Search agent should return at least one venue for a common query."""
    from src.agents.search_agent import run_search

    result = await run_search("bowling alley", location="Pittsburgh, PA", max_results=5)

    assert result is not None
    assert len(result.venues) > 0, "Expected at least one venue"
    assert result.summary != ""


async def test_search_populates_sources_searched():
    """Sources searched list should be populated even if some sources return 0 results."""
    from src.agents.search_agent import run_search

    result = await run_search("restaurant", location="Pittsburgh, PA", max_results=3)

    assert len(result.sources_searched) > 0


async def test_search_venues_have_names():
    """Every returned venue must have a non-empty name."""
    from src.agents.search_agent import run_search

    result = await run_search("coffee shop", location="Pittsburgh, PA", max_results=5)

    for venue in result.venues:
        assert venue.name, f"Venue missing name: {venue}"


async def test_search_ai_fallback_returns_venues():
    """LLM-based AI search (_search_via_llm) should return venues when called directly."""
    from src.tools.google_places import _search_via_llm

    venues = await _search_via_llm("arcade bar", "Pittsburgh, PA", limit=3)

    assert len(venues) > 0, "AI fallback returned no venues"
    assert all(v.name for v in venues), "All venues must have names"


# ── Recommendation Agent ───────────────────────────────────────────────


async def test_recommendation_ranks_venues():
    """Recommendation agent should return a non-empty ranked list."""
    from src.agents.search_agent import run_search
    from src.agents.recommendation_agent import run_recommendation
    from src.models.constraints import ConstraintSet
    from src.models.user import BudgetTier, UserPreferences

    venues = (await run_search("restaurant Pittsburgh, PA", max_results=5)).venues
    assert venues, "Precondition: search must return venues"

    prefs = [UserPreferences(
        user_id="u1",
        cuisines=["Italian", "American"],
        budget_tier=BudgetTier.MEDIUM,
    )]
    cs = ConstraintSet.from_user_preferences("g1", prefs)

    result = await run_recommendation(venues, prefs, cs, ["Alice"])

    total = len(result.ranked_venues) + len(result.rejected_venues)
    assert total == len(venues), "All venues must be ranked or rejected"
    assert len(result.ranked_venues) > 0, "Expected at least one ranked venue"


async def test_recommendation_venues_have_scores():
    """Every ranked venue must have a score between 0 and 1."""
    from src.agents.search_agent import run_search
    from src.agents.recommendation_agent import run_recommendation
    from src.models.constraints import ConstraintSet
    from src.models.user import BudgetTier, UserPreferences

    venues = (await run_search("bar Pittsburgh, PA", max_results=4)).venues
    prefs = [UserPreferences(user_id="u1", budget_tier=BudgetTier.MEDIUM)]
    cs = ConstraintSet.from_user_preferences("g1", prefs)

    result = await run_recommendation(venues, prefs, cs)

    for sv in result.ranked_venues:
        assert 0.0 <= sv.score <= 1.0, f"Score out of range: {sv.score}"


# ── Orchestrator Pipeline ──────────────────────────────────────────────


async def test_orchestrator_completes_all_steps():
    """Full orchestrator should complete search, calendar, recommend, and itinerary."""
    from src.agents.orchestrator_agent import run_orchestrator, QuickPlanRequest

    req = QuickPlanRequest(
        request="Plan a bowling night for our group",
        group_name="Test Group",
        members=[
            {"name": "Alice", "email": "alice@test.com"},
            {"name": "Bob", "email": "bob@test.com"},
        ],
        location="Pittsburgh, PA",
        earliest_time="18:00",
        latest_time="22:00",
    )

    plan = await run_orchestrator(req)

    assert "search" in plan.steps_completed, "Search step must complete"
    assert "calendar" in plan.steps_completed, "Calendar step must complete"
    assert "recommend" in plan.steps_completed, "Recommend step must complete"
    assert "itinerary" in plan.steps_completed, "Itinerary step must complete"


async def test_orchestrator_returns_venues():
    """Orchestrator must find at least one venue."""
    from src.agents.orchestrator_agent import run_orchestrator, QuickPlanRequest

    req = QuickPlanRequest(
        request="dinner and drinks",
        members=[{"name": "Alice", "email": "a@test.com"}],
        location="Pittsburgh, PA",
    )

    plan = await run_orchestrator(req)

    assert plan.venues_found > 0, "Orchestrator must find venues"


async def test_orchestrator_produces_recommendation():
    """Orchestrator must produce a top venue and time slot recommendation."""
    from src.agents.orchestrator_agent import run_orchestrator, QuickPlanRequest

    req = QuickPlanRequest(
        request="bowling night",
        group_name="Friends",
        members=[
            {"name": "Alice", "email": "a@test.com"},
            {"name": "Bob", "email": "b@test.com"},
        ],
        location="Pittsburgh, PA",
        earliest_time="17:00",
        latest_time="23:00",
    )

    plan = await run_orchestrator(req)

    assert plan.recommended_venue is not None, "Must produce a recommended venue"
    assert plan.recommended_venue.get("name"), "Recommended venue must have a name"
    assert plan.recommended_slot is not None, "Must produce a recommended time slot"


async def test_orchestrator_agent_log_is_populated():
    """Agent log entries should be present and non-empty."""
    from src.agents.orchestrator_agent import run_orchestrator, QuickPlanRequest

    req = QuickPlanRequest(
        request="escape room outing",
        members=[{"name": "Alice", "email": "a@test.com"}],
        location="Pittsburgh, PA",
    )

    plan = await run_orchestrator(req)

    assert len(plan.agent_log) > 0, "Agent log must have entries"
    assert all(isinstance(entry, str) for entry in plan.agent_log)
