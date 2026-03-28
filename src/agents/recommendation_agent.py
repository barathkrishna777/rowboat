"""Recommendation Agent — combines search results with constraint solving and RAG.

This agent sits between the raw search results and the UI, applying:
1. Constraint-based filtering (hard constraints reject, soft constraints score)
2. RAG-enhanced context (past feedback, venue knowledge base)
3. Final ranking with explanations
"""

from __future__ import annotations

from dataclasses import dataclass
from pydantic import BaseModel, Field

from src.config import settings
from src.models.event import ScoredVenue, Venue
from src.models.user import UserPreferences
from src.models.constraints import ConstraintSet
from src.constraints.solver import rank_venues, DEFAULT_WEIGHTS


class RecommendationResult(BaseModel):
    """Output from the recommendation agent."""
    ranked_venues: list[ScoredVenue] = Field(default_factory=list)
    rejected_venues: list[ScoredVenue] = Field(default_factory=list)
    rag_insights: str = ""
    summary: str = ""


@dataclass
class RecommendationDeps:
    """Dependencies for the recommendation agent."""
    venues: list[Venue]
    all_preferences: list[UserPreferences]
    constraint_set: ConstraintSet
    group_member_names: list[str] = None


_recommendation_agent: Agent | None = None


def get_recommendation_agent():
    """Lazy-initialize the recommendation agent."""
    from pydantic_ai import Agent

    global _recommendation_agent
    if _recommendation_agent is None:
        _recommendation_agent = Agent(
            settings.primary_model,
            output_type=RecommendationResult,
            deps_type=RecommendationDeps,
            system_prompt=(
                "You are a recommendation specialist for group outings. "
                "You have access to tools that score venues against group preferences, "
                "search past feedback, and query a venue knowledge base. "
                "Use these to produce the best possible ranked recommendations. "
                "Always explain WHY venues are ranked the way they are. "
                "Highlight matches with group preferences (cuisine, activities, budget). "
                "If past feedback suggests the group liked similar venues, mention that."
            ),
        )
        _register_recommendation_tools(_recommendation_agent)
    return _recommendation_agent


def _register_recommendation_tools(agent):
    """Register tools on the recommendation agent."""
    from pydantic_ai import RunContext

    @agent.tool
    async def tool_score_and_rank_venues(
        ctx: RunContext[RecommendationDeps],
    ) -> list[dict]:
        """Score all venues against group constraints and preferences.

        Returns a ranked list with scores and explanations.
        Hard constraint violations (budget, dietary, dealbreakers) result in rejection.
        """
        scored = rank_venues(
            venues=ctx.deps.venues,
            constraint_set=ctx.deps.constraint_set,
            all_preferences=ctx.deps.all_preferences,
        )
        return [sv.model_dump() for sv in scored]

    @agent.tool
    async def tool_search_venue_knowledge_base(
        ctx: RunContext[RecommendationDeps],
        query: str,
    ) -> list[dict]:
        """Search the venue knowledge base for similar venues from past searches.

        Args:
            query: What to search for (e.g., "arcade bar in Pittsburgh", "Italian restaurant").
        """
        from src.rag.venue_store import search_similar_venues
        return search_similar_venues(query, n_results=5)

    @agent.tool
    async def tool_get_past_feedback(
        ctx: RunContext[RecommendationDeps],
        query: str,
    ) -> list[dict]:
        """Search past outing feedback to find what the group liked or disliked.

        Args:
            query: What to look for (e.g., "bowling", "expensive restaurants", "loud venues").
        """
        from src.rag.venue_store import get_past_preferences
        return get_past_preferences(query, n_results=5)

    @agent.tool
    async def tool_get_knowledge_base_stats(
        ctx: RunContext[RecommendationDeps],
    ) -> dict:
        """Get stats about the venue knowledge base and feedback history."""
        from src.rag.venue_store import get_venue_history_summary
        return get_venue_history_summary()


async def run_recommendation(
    venues: list[Venue],
    all_preferences: list[UserPreferences],
    constraint_set: ConstraintSet,
    group_member_names: list[str] | None = None,
) -> RecommendationResult:
    """Run the recommendation pipeline: score, rank, and explain venues.

    This is the main entry point for Phase 3 recommendation logic.
    Can be called with or without the LLM agent — falls back to
    pure constraint solving if the agent fails.
    """
    # Always index venues into the knowledge base for future searches
    try:
        from src.rag.venue_store import index_venues
        indexed = index_venues(venues)
    except Exception:
        indexed = 0  # don't block on RAG failures

    # Try the full agent pipeline first
    try:
        agent = get_recommendation_agent()
        deps = RecommendationDeps(
            venues=venues,
            all_preferences=all_preferences,
            constraint_set=constraint_set,
            group_member_names=group_member_names,
        )
        result = await agent.run(
            f"Score and rank these {len(venues)} venues for a group outing. "
            f"The group has {len(all_preferences)} members. "
            f"Budget limit: {constraint_set.budget_max.value}. "
            f"Check the knowledge base for similar past venues and any feedback. "
            f"Return the ranked results with clear explanations.",
            deps=deps,
        )
        return result.output

    except Exception as e:
        # Fallback: pure constraint-based scoring (no LLM needed)
        return _fallback_recommendation(venues, all_preferences, constraint_set)


def _fallback_recommendation(
    venues: list[Venue],
    all_preferences: list[UserPreferences],
    constraint_set: ConstraintSet,
) -> RecommendationResult:
    """Fallback recommendation using only the constraint solver (no LLM)."""
    scored = rank_venues(venues, constraint_set, all_preferences)

    passing = [sv for sv in scored if sv.score > 0]
    rejected = [sv for sv in scored if sv.score == 0]

    # Build a summary
    if passing:
        top = passing[0]
        summary = (
            f"Found {len(passing)} venues matching your group's preferences. "
            f"Top pick: {top.venue.name} (score: {top.score:.0%}). "
            f"{top.explanation}"
        )
    else:
        summary = (
            f"All {len(venues)} venues were filtered out by your group's constraints. "
            "Try relaxing budget or dietary requirements."
        )

    if rejected:
        summary += f" {len(rejected)} venue(s) rejected due to constraint violations."

    return RecommendationResult(
        ranked_venues=passing,
        rejected_venues=rejected,
        rag_insights=f"Indexed {len(venues)} venues into knowledge base.",
        summary=summary,
    )
