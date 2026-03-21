"""Orchestrator Agent — coordinates all sub-agents to plan an outing end-to-end.

The Orchestrator is the "brain" that takes a high-level user request like
"Plan a bowling night for our group next weekend" and autonomously:
1. Collects/loads group member preferences
2. Searches for matching venues
3. Finds available time slots across all members
4. Scores and ranks venue+slot combinations
5. Produces a recommended itinerary

It demonstrates true multi-agent coordination by delegating to specialist
sub-agents and managing data flow between them.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from src.config import settings
from src.models.event import Venue, TimeSlot, ScoredVenue, Itinerary, ItineraryItem
from src.models.user import UserPreferences, User, BudgetTier, DietaryRestriction
from src.models.constraints import ConstraintSet
from src.agents.search_agent import run_search, SearchResult
from src.agents.recommendation_agent import run_recommendation, RecommendationResult
from src.constraints.solver import rank_venues as direct_rank_venues
from src.tools.google_calendar import find_group_availability


# ── Output Models ──────────────────────────────────────────────────────

class OrchestratorPlan(BaseModel):
    """The orchestrator's complete outing plan."""
    group_name: str = ""
    members: list[str] = Field(default_factory=list)
    request_summary: str = ""

    # Sub-agent results
    venues_found: int = 0
    venues_searched_sources: list[str] = Field(default_factory=list)
    ranked_venues: list[ScoredVenue] = Field(default_factory=list)
    rejected_venues: list[ScoredVenue] = Field(default_factory=list)
    available_slots: list[dict] = Field(default_factory=list)

    # Final recommendation
    recommended_venue: dict | None = None
    recommended_slot: dict | None = None
    estimated_cost_per_person: str = ""
    itinerary_summary: str = ""
    rag_insights: str = ""

    # Orchestration log
    steps_completed: list[str] = Field(default_factory=list)
    agent_log: list[str] = Field(default_factory=list)


class QuickPlanRequest(BaseModel):
    """A natural-language request to plan an outing."""
    request: str = Field(description="What the user wants, e.g. 'Plan a bowling night for us next Saturday'")
    group_name: str = ""
    members: list[dict] = Field(default_factory=list,
                                description="List of {name, email} dicts")
    preferences: list[dict] = Field(default_factory=list,
                                    description="List of UserPreferences dicts")
    location: str = "Pittsburgh, PA"
    date_range_start: str = ""  # ISO date
    date_range_end: str = ""
    earliest_time: str = "17:00"
    latest_time: str = "23:00"


# ── Dependencies ───────────────────────────────────────────────────────

@dataclass
class OrchestratorDeps:
    """Everything the orchestrator needs to coordinate sub-agents."""
    request: QuickPlanRequest
    preferences: list[UserPreferences] = field(default_factory=list)
    search_result: SearchResult | None = None
    recommendation_result: RecommendationResult | None = None
    available_slots: list[dict] = field(default_factory=list)
    agent_log: list[str] = field(default_factory=list)


# ── Agent ──────────────────────────────────────────────────────────────

_orchestrator_agent: Agent | None = None


def get_orchestrator_agent() -> Agent:
    """Lazy-initialize the orchestrator agent."""
    global _orchestrator_agent
    if _orchestrator_agent is None:
        _orchestrator_agent = Agent(
            settings.primary_model,
            output_type=OrchestratorPlan,
            system_prompt=(
                "You are the Orchestrator Agent for a Group Outing Planner. "
                "Your job is to coordinate multiple specialist agents to plan a perfect group outing. "
                "\n\n"
                "You have access to these tools:\n"
                "1. tool_parse_request — Understand what the user wants (activities, preferences, dates)\n"
                "2. tool_search_venues — Find matching venues using the Search Agent\n"
                "3. tool_find_available_times — Find times when all group members are free\n"
                "4. tool_rank_and_recommend — Score and rank venues using the Recommendation Agent\n"
                "5. tool_build_itinerary — Combine the best venue + time slot into a final plan\n"
                "\n"
                "WORKFLOW: Always follow this order:\n"
                "1. First, parse the request to understand what's needed\n"
                "2. Search for venues matching the parsed criteria\n"
                "3. Find available time slots for the group\n"
                "4. Rank venues against group preferences and constraints\n"
                "5. Build the final itinerary with the top venue + best time slot\n"
                "\n"
                "Call ALL tools in sequence. Do not skip steps. "
                "After calling all tools, return a complete OrchestratorPlan."
            ),
        )
        _register_orchestrator_tools(_orchestrator_agent)
    return _orchestrator_agent


def _register_orchestrator_tools(agent: Agent):
    """Register all orchestrator tools."""

    @agent.tool
    async def tool_parse_request(
        ctx: RunContext[OrchestratorDeps],
        activity_keywords: str,
        parsed_date_hint: str = "",
        budget_hint: str = "$$",
    ) -> dict:
        """Parse the user's natural-language request into structured search parameters.

        Args:
            activity_keywords: Key activities extracted from the request (e.g., "bowling, arcade, pizza").
            parsed_date_hint: Any date/time hints from the request (e.g., "next Saturday", "this weekend").
            budget_hint: Budget level mentioned or implied ($, $$, $$$, $$$$).
        """
        req = ctx.deps.request
        log_entry = f"[Parse] Activities: {activity_keywords}, Date: {parsed_date_hint or 'flexible'}, Budget: {budget_hint}"
        ctx.deps.agent_log.append(log_entry)

        # Build search query from the parsed info
        location = req.location or "Pittsburgh, PA"
        search_query = f"{activity_keywords} in {location}"

        return {
            "search_query": search_query,
            "activity_keywords": activity_keywords,
            "location": location,
            "budget_hint": budget_hint,
            "date_hint": parsed_date_hint,
            "members": [m.get("name", "Member") for m in req.members],
            "member_count": len(req.members),
        }

    @agent.tool
    async def tool_search_venues(
        ctx: RunContext[OrchestratorDeps],
        search_query: str,
        location: str = "Pittsburgh, PA",
    ) -> dict:
        """Search for venues using the Search Agent (Google Places, Yelp, etc.).

        Args:
            search_query: What to search for (e.g., "bowling alley arcade in Pittsburgh, PA").
            location: City/area to search in.
        """
        ctx.deps.agent_log.append(f"[Search] Query: {search_query}")

        try:
            result = await run_search(
                query=search_query,
                location=location,
                max_results=10,
            )
            ctx.deps.search_result = result
            ctx.deps.agent_log.append(
                f"[Search] Found {len(result.venues)} venues from {', '.join(result.sources_searched)}"
            )
            return {
                "venues_found": len(result.venues),
                "sources": result.sources_searched,
                "venue_names": [v.name for v in result.venues[:8]],
                "summary": result.summary,
            }
        except Exception as e:
            ctx.deps.agent_log.append(f"[Search] Error: {e}")
            return {"venues_found": 0, "sources": [], "error": str(e)}

    @agent.tool
    async def tool_find_available_times(
        ctx: RunContext[OrchestratorDeps],
    ) -> dict:
        """Find time slots when all group members are available using the Calendar Agent.

        Uses the date range and time preferences from the original request.
        """
        req = ctx.deps.request
        ctx.deps.agent_log.append("[Calendar] Finding group availability...")

        # Parse dates
        try:
            if req.date_range_start:
                start = date.fromisoformat(req.date_range_start)
            else:
                start = date.today() + timedelta(days=1)

            if req.date_range_end:
                end = date.fromisoformat(req.date_range_end)
            else:
                end = start + timedelta(days=7)
        except (ValueError, TypeError):
            start = date.today() + timedelta(days=1)
            end = start + timedelta(days=7)

        # Parse time constraints
        try:
            eh, em = map(int, req.earliest_time.split(":"))
            lh, lm = map(int, req.latest_time.split(":"))
        except (ValueError, AttributeError):
            eh, em = 17, 0
            lh, lm = 23, 0

        # Build mock busy periods (simulated calendar — no real Google Calendar)
        member_names = [m.get("name", f"Member {i+1}") for i, m in enumerate(req.members)]
        # Simulate some random busy blocks so the calendar isn't trivially all-free
        import random
        busy_periods_by_user = {}
        for name in member_names:
            busy = []
            for d in range((end - start).days + 1):
                day = start + timedelta(days=d)
                # Each member has a ~30% chance of being busy for 1-2 hours on any given day
                if random.random() < 0.3:
                    busy_h = random.randint(eh, max(eh + 1, lh - 2))
                    busy.append({
                        "start": datetime.combine(day, datetime.min.time().replace(hour=busy_h)).isoformat(),
                        "end": datetime.combine(day, datetime.min.time().replace(hour=min(busy_h + 2, 23))).isoformat(),
                    })
            busy_periods_by_user[name] = busy

        lh_eff = lh if lh > eh else 23  # handle overnight

        slots = find_group_availability(
            busy_periods_by_user=busy_periods_by_user,
            date_range_start=datetime.combine(start, datetime.min.time()),
            date_range_end=datetime.combine(end, datetime.min.time()),
            min_duration_minutes=120,
            preferred_hours=(eh, lh_eff),
        )

        # Convert TimeSlot objects to dicts
        slot_dicts = []
        for s in slots:
            slot_dicts.append({
                "date": s.start.strftime("%Y-%m-%d"),
                "day_name": s.start.strftime("%A"),
                "start_time": s.start.strftime("%I:%M %p"),
                "end_time": s.end.strftime("%I:%M %p"),
                "duration_hours": (s.end - s.start).total_seconds() / 3600,
                "is_weekend": s.start.weekday() >= 5,
            })

        ctx.deps.available_slots = slot_dicts
        ctx.deps.agent_log.append(f"[Calendar] Found {len(slot_dicts)} available slots")

        # Format for LLM
        slot_summaries = []
        for s in slot_dicts[:10]:
            slot_summaries.append({
                "date": s.get("date", ""),
                "day": s.get("day_name", ""),
                "start_time": s.get("start_time", ""),
                "end_time": s.get("end_time", ""),
                "duration_hours": s.get("duration_hours", 0),
                "is_weekend": s.get("is_weekend", False),
            })

        return {
            "total_slots": len(slots),
            "slots": slot_summaries,
        }

    @agent.tool
    async def tool_rank_and_recommend(
        ctx: RunContext[OrchestratorDeps],
    ) -> dict:
        """Score and rank venues using the Recommendation Agent (constraint solver + RAG).

        Applies the group's preferences, dietary restrictions, budget constraints,
        and dealbreakers to filter and rank the found venues.
        """
        if not ctx.deps.search_result or not ctx.deps.search_result.venues:
            ctx.deps.agent_log.append("[Recommend] No venues to rank — search not run yet")
            return {"error": "No venues found. Run tool_search_venues first."}

        ctx.deps.agent_log.append("[Recommend] Scoring and ranking venues...")

        # Build preferences list
        preferences = ctx.deps.preferences
        if not preferences and ctx.deps.request.preferences:
            for pref_dict in ctx.deps.request.preferences:
                try:
                    preferences.append(UserPreferences(**pref_dict))
                except Exception:
                    pass

        # Build constraint set
        if preferences:
            constraint_set = ConstraintSet.from_user_preferences(
                group_id=ctx.deps.request.group_name or "orchestrated",
                preferences_list=preferences,
            )
        else:
            # Default constraints
            budget_map = {"$": BudgetTier.LOW, "$$": BudgetTier.MEDIUM,
                          "$$$": BudgetTier.HIGH, "$$$$": BudgetTier.LUXURY}
            constraint_set = ConstraintSet(
                group_id="orchestrated",
                budget_max=budget_map.get("$$", BudgetTier.MEDIUM),
                dietary_restrictions=[],
                dealbreakers=[],
            )

        member_names = [m.get("name", "") for m in ctx.deps.request.members]

        try:
            result = await run_recommendation(
                venues=ctx.deps.search_result.venues,
                all_preferences=preferences,
                constraint_set=constraint_set,
                group_member_names=member_names,
            )
            ctx.deps.recommendation_result = result

            # If LLM-based recommendation returned empty, fall back to direct scoring
            if not result.ranked_venues:
                ctx.deps.agent_log.append("[Recommend] LLM returned empty — using direct constraint solver")
                scored = direct_rank_venues(
                    ctx.deps.search_result.venues, constraint_set, preferences
                )
                ranked = [sv for sv in scored if sv.score > 0]
                rejected = [sv for sv in scored if sv.score == 0]
                result = RecommendationResult(
                    ranked_venues=ranked,
                    rejected_venues=rejected,
                    rag_insights=result.rag_insights,
                    summary=f"Ranked {len(ranked)} venues using constraint scoring.",
                )
                ctx.deps.recommendation_result = result

            ctx.deps.agent_log.append(
                f"[Recommend] Ranked {len(result.ranked_venues)} venues, "
                f"rejected {len(result.rejected_venues)}"
            )
            return {
                "ranked_count": len(result.ranked_venues),
                "rejected_count": len(result.rejected_venues),
                "top_3": [
                    {
                        "name": sv.venue.name,
                        "score": round(sv.score * 100),
                        "explanation": sv.explanation,
                    }
                    for sv in result.ranked_venues[:3]
                ],
                "rag_insights": result.rag_insights,
                "summary": result.summary,
            }
        except Exception as e:
            # Full fallback: use constraint solver directly
            ctx.deps.agent_log.append(f"[Recommend] Agent failed ({e}), using direct solver")
            try:
                scored = direct_rank_venues(
                    ctx.deps.search_result.venues, constraint_set, preferences
                )
                ranked = [sv for sv in scored if sv.score > 0]
                rejected = [sv for sv in scored if sv.score == 0]
                result = RecommendationResult(
                    ranked_venues=ranked,
                    rejected_venues=rejected,
                    summary=f"Ranked {len(ranked)} venues (direct scoring).",
                )
                ctx.deps.recommendation_result = result
                ctx.deps.agent_log.append(f"[Recommend] Direct solver: {len(ranked)} ranked")
                return {
                    "ranked_count": len(ranked),
                    "rejected_count": len(rejected),
                    "top_3": [{"name": sv.venue.name, "score": round(sv.score * 100)} for sv in ranked[:3]],
                }
            except Exception as e2:
                ctx.deps.agent_log.append(f"[Recommend] Direct solver also failed: {e2}")
                return {"error": str(e2)}

    @agent.tool
    async def tool_build_itinerary(
        ctx: RunContext[OrchestratorDeps],
    ) -> dict:
        """Combine the best venue with the best time slot into a final plan.

        Creates the recommended itinerary from the ranking and availability results.
        """
        ctx.deps.agent_log.append("[Itinerary] Building final plan...")

        # Get best venue
        best_venue = None
        if ctx.deps.recommendation_result and ctx.deps.recommendation_result.ranked_venues:
            best_venue = ctx.deps.recommendation_result.ranked_venues[0]

        # Get best slot
        best_slot = None
        if ctx.deps.available_slots:
            # Prefer weekend slots
            weekend_slots = [s for s in ctx.deps.available_slots if s.get("is_weekend")]
            best_slot = weekend_slots[0] if weekend_slots else ctx.deps.available_slots[0]

        result = {
            "venue": None,
            "time_slot": None,
            "cost_estimate": "",
            "summary": "Could not build itinerary — missing venue or time data.",
        }

        if best_venue:
            v = best_venue.venue
            price_map = {"$": 15, "$$": 25, "$$$": 45, "$$$$": 75}
            per_person = price_map.get(v.price_tier or "$$", 25)
            member_count = len(ctx.deps.request.members) or 1

            result["venue"] = {
                "name": v.name,
                "address": v.address,
                "rating": v.rating,
                "price_tier": v.price_tier,
                "categories": [c.value for c in v.categories] if v.categories else [],
                "score": round(best_venue.score * 100),
                "explanation": best_venue.explanation,
            }
            result["cost_estimate"] = f"~${per_person}/person (${per_person * member_count} total)"

        if best_slot:
            result["time_slot"] = {
                "date": best_slot.get("date", ""),
                "day": best_slot.get("day_name", ""),
                "start_time": best_slot.get("start_time", ""),
                "end_time": best_slot.get("end_time", ""),
                "is_weekend": best_slot.get("is_weekend", False),
            }

        if best_venue and best_slot:
            v = best_venue.venue
            result["summary"] = (
                f"Head to {v.name} ({v.address}) on "
                f"{best_slot.get('day_name', '')} {best_slot.get('date', '')} "
                f"from {best_slot.get('start_time', '')} to {best_slot.get('end_time', '')}. "
                f"Score: {round(best_venue.score * 100)}% match. "
                f"Estimated cost: {result['cost_estimate']}."
            )

        ctx.deps.agent_log.append(f"[Itinerary] {result['summary']}")
        return result


# ── Entry Point ────────────────────────────────────────────────────────

async def run_orchestrator(request: QuickPlanRequest) -> OrchestratorPlan:
    """Run the full orchestration pipeline.

    This is the main entry point. The LLM orchestrator calls all sub-agent
    tools in sequence and produces a complete OrchestratorPlan.

    Falls back to a deterministic pipeline if the LLM fails.
    """
    # Build preferences from request
    preferences = []
    for pref_dict in request.preferences:
        try:
            preferences.append(UserPreferences(**pref_dict))
        except Exception:
            pass

    deps = OrchestratorDeps(
        request=request,
        preferences=preferences,
    )

    # Use the deterministic pipeline directly — it runs search, calendar,
    # recommendation, and itinerary in sequence without an extra LLM layer.
    # This avoids Gemini API contention (the LLM orchestrator's own calls
    # compete with the search agent's Gemini calls, causing timeouts).
    return await _fallback_orchestration(request, preferences, deps)


async def _fallback_orchestration(
    request: QuickPlanRequest,
    preferences: list[UserPreferences],
    deps: OrchestratorDeps,
) -> OrchestratorPlan:
    """Deterministic fallback if the LLM orchestrator fails.

    Runs the same pipeline without LLM decision-making.
    """
    plan = OrchestratorPlan(
        group_name=request.group_name,
        members=[m.get("name", "") for m in request.members],
        request_summary=request.request,
        agent_log=["[Fallback] Running deterministic pipeline (LLM orchestrator unavailable)"],
    )

    # 1. Search
    try:
        search_query = request.request
        if request.location and request.location not in search_query:
            search_query += f" in {request.location}"

        result = await run_search(
            query=search_query,
            location=request.location or "Pittsburgh, PA",
            max_results=10,
        )
        plan.venues_found = len(result.venues)
        plan.venues_searched_sources = result.sources_searched
        plan.steps_completed.append("search")
        plan.agent_log.append(f"[Search] Found {len(result.venues)} venues")
    except Exception as e:
        plan.agent_log.append(f"[Search] Failed: {e}")
        return plan

    # 2. Calendar
    try:
        start = date.fromisoformat(request.date_range_start) if request.date_range_start else date.today() + timedelta(days=1)
        end = date.fromisoformat(request.date_range_end) if request.date_range_end else start + timedelta(days=7)
        eh, em = map(int, request.earliest_time.split(":"))
        lh, lm = map(int, request.latest_time.split(":"))

        member_names = [m.get("name", f"M{i}") for i, m in enumerate(request.members)]
        import random
        busy_periods_by_user = {}
        for name in member_names:
            busy = []
            for d in range((end - start).days + 1):
                day = start + timedelta(days=d)
                if random.random() < 0.3:
                    busy_h = random.randint(eh, max(eh + 1, lh - 2))
                    busy.append({
                        "start": datetime.combine(day, datetime.min.time().replace(hour=busy_h)).isoformat(),
                        "end": datetime.combine(day, datetime.min.time().replace(hour=min(busy_h + 2, 23))).isoformat(),
                    })
            busy_periods_by_user[name] = busy

        lh_eff = lh if lh > eh else 23

        slots = find_group_availability(
            busy_periods_by_user=busy_periods_by_user,
            date_range_start=datetime.combine(start, datetime.min.time()),
            date_range_end=datetime.combine(end, datetime.min.time()),
            min_duration_minutes=120,
            preferred_hours=(eh, lh_eff),
        )
        # Convert TimeSlot objects to dicts for JSON serialization
        slot_dicts = []
        for s in slots:
            slot_dicts.append({
                "date": s.start.strftime("%Y-%m-%d"),
                "day_name": s.start.strftime("%A"),
                "start_time": s.start.strftime("%I:%M %p"),
                "end_time": s.end.strftime("%I:%M %p"),
                "duration_hours": (s.end - s.start).total_seconds() / 3600,
                "is_weekend": s.start.weekday() >= 5,
            })
        plan.available_slots = slot_dicts
        plan.steps_completed.append("calendar")
        plan.agent_log.append(f"[Calendar] Found {len(slots)} available slots")
    except Exception as e:
        plan.agent_log.append(f"[Calendar] Failed: {e}")

    # 3. Recommend
    try:
        if preferences:
            constraint_set = ConstraintSet.from_user_preferences(
                group_id=request.group_name or "fallback",
                preferences_list=preferences,
            )
        else:
            constraint_set = ConstraintSet(
                group_id="fallback",
                budget_max=BudgetTier.MEDIUM,
                dietary_restrictions=[],
                dealbreakers=[],
            )

        rec_result = await run_recommendation(
            venues=result.venues,
            all_preferences=preferences,
            constraint_set=constraint_set,
            group_member_names=[m.get("name", "") for m in request.members],
        )
        # If LLM recommendation returned empty, use direct constraint solver
        if not rec_result.ranked_venues:
            plan.agent_log.append("[Recommend] LLM returned empty — using direct solver")
            scored = direct_rank_venues(result.venues, constraint_set, preferences)
            ranked = [sv for sv in scored if sv.score > 0]
            rejected = [sv for sv in scored if sv.score == 0]
            rec_result = RecommendationResult(
                ranked_venues=ranked,
                rejected_venues=rejected,
                summary=f"Ranked {len(ranked)} venues using constraint scoring.",
            )

        plan.ranked_venues = rec_result.ranked_venues
        plan.rejected_venues = rec_result.rejected_venues
        plan.rag_insights = rec_result.rag_insights
        plan.steps_completed.append("recommend")
        plan.agent_log.append(f"[Recommend] Ranked {len(rec_result.ranked_venues)} venues")
    except Exception as e:
        # Full fallback: direct constraint solver
        plan.agent_log.append(f"[Recommend] Agent failed ({e}), using direct solver")
        try:
            scored = direct_rank_venues(result.venues, constraint_set, preferences)
            plan.ranked_venues = [sv for sv in scored if sv.score > 0]
            plan.rejected_venues = [sv for sv in scored if sv.score == 0]
            plan.steps_completed.append("recommend")
            plan.agent_log.append(f"[Recommend] Direct solver: {len(plan.ranked_venues)} ranked")
        except Exception as e2:
            plan.agent_log.append(f"[Recommend] Direct solver also failed: {e2}")

    # 4. Build itinerary
    if plan.ranked_venues and plan.available_slots:
        best_v = plan.ranked_venues[0]
        weekend_slots = [s for s in plan.available_slots if s.get("is_weekend")]
        best_s = weekend_slots[0] if weekend_slots else plan.available_slots[0]

        price_map = {"$": 15, "$$": 25, "$$$": 45, "$$$$": 75}
        pp = price_map.get(best_v.venue.price_tier or "$$", 25)
        n = len(request.members) or 1

        tier = best_v.venue.price_tier
        plan.recommended_venue = {
            "name": best_v.venue.name,
            "address": best_v.venue.address,
            "rating": best_v.venue.rating,
            "price_tier": tier.value if tier else "$$",
            "score": round(best_v.score * 100),
        }
        plan.recommended_slot = best_s
        plan.estimated_cost_per_person = f"~${pp}/person (${pp * n} total)"
        plan.itinerary_summary = (
            f"Head to {best_v.venue.name} on "
            f"{best_s.get('day_name', '')} {best_s.get('date', '')} "
            f"from {best_s.get('start_time', '')} to {best_s.get('end_time', '')}. "
            f"Match score: {round(best_v.score * 100)}%."
        )
        plan.steps_completed.append("itinerary")
        plan.agent_log.append(f"[Itinerary] {plan.itinerary_summary}")

    return plan
