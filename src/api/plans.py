"""Plan generation API endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from src.agents.search_agent import SearchResult, run_search
from src.agents.recommendation_agent import RecommendationResult, run_recommendation
from src.agents.orchestrator_agent import (
    OrchestratorPlan, QuickPlanRequest, run_orchestrator,
)
from src.models.event import Venue
from src.models.user import UserPreferences, BudgetTier, DietaryRestriction
from src.models.constraints import ConstraintSet

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(description="What kind of outing to search for")
    location: str = Field(default="Pittsburgh, PA", description="Location to search")
    max_results: int = Field(default=10, ge=1, le=50)


class RecommendRequest(BaseModel):
    """Request to score and rank venues against group preferences."""
    venues: list[Venue]
    preferences: list[UserPreferences] = Field(default_factory=list)
    group_id: str = ""
    budget_max: str = "$$"
    dietary_restrictions: list[str] = Field(default_factory=list)
    dealbreakers: list[str] = Field(default_factory=list)
    member_names: list[str] = Field(default_factory=list)


@router.post("/search", response_model=SearchResult)
async def search_venues(request: SearchRequest):
    """Search for venues and events using the AI search agent."""
    try:
        result = await run_search(
            query=request.query,
            location=request.location,
            max_results=request.max_results,
        )
        return result
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Search error: {tb}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@router.post("/recommend", response_model=RecommendationResult)
async def recommend_venues(request: RecommendRequest):
    """Score, rank, and explain venue recommendations for a group.

    Applies constraint solving (hard + soft) and RAG-enhanced context.
    """
    try:
        # Parse budget tier
        budget_map = {"$": BudgetTier.LOW, "$$": BudgetTier.MEDIUM,
                      "$$$": BudgetTier.HIGH, "$$$$": BudgetTier.LUXURY}
        budget = budget_map.get(request.budget_max, BudgetTier.MEDIUM)

        # Parse dietary restrictions
        dietary = []
        for d in request.dietary_restrictions:
            try:
                dietary.append(DietaryRestriction(d))
            except ValueError:
                pass

        # Build constraint set
        constraint_set = ConstraintSet(
            group_id=request.group_id or "default",
            budget_max=budget,
            dietary_restrictions=dietary,
            dealbreakers=request.dealbreakers,
        )

        # If preferences provided, also merge into constraint set
        if request.preferences:
            constraint_set = ConstraintSet.from_user_preferences(
                group_id=request.group_id or "default",
                preferences_list=request.preferences,
            )

        result = await run_recommendation(
            venues=request.venues,
            all_preferences=request.preferences,
            constraint_set=constraint_set,
            group_member_names=request.member_names,
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrate", response_model=OrchestratorPlan)
async def orchestrate_outing(request: QuickPlanRequest):
    """Plan an outing end-to-end using the Orchestrator Agent.

    The orchestrator coordinates all sub-agents autonomously:
    1. Parses the natural-language request
    2. Searches for matching venues (Search Agent)
    3. Finds available time slots (Calendar Agent)
    4. Ranks venues against constraints (Recommendation Agent)
    5. Builds a final itinerary

    This is the "one-click planning" endpoint.
    """
    try:
        plan = await run_orchestrator(request)
        return plan
    except Exception as e:
        import traceback
        print(f"Orchestrator error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
