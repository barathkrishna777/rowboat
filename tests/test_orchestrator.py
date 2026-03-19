"""Tests for the orchestrator agent models and pipeline."""

import pytest
from datetime import date, timedelta

from src.agents.orchestrator_agent import (
    OrchestratorPlan,
    QuickPlanRequest,
    OrchestratorDeps,
)


def test_quick_plan_request_defaults():
    req = QuickPlanRequest(request="bowling night")
    assert req.request == "bowling night"
    assert req.location == "Pittsburgh, PA"
    assert req.members == []
    assert req.earliest_time == "17:00"
    assert req.latest_time == "23:00"


def test_quick_plan_request_with_members():
    req = QuickPlanRequest(
        request="dinner and arcade",
        group_name="Friday Crew",
        members=[
            {"name": "Alice", "email": "a@test.com"},
            {"name": "Bob", "email": "b@test.com"},
        ],
        location="New York, NY",
        date_range_start="2026-03-20",
        date_range_end="2026-03-25",
    )
    assert req.group_name == "Friday Crew"
    assert len(req.members) == 2
    assert req.location == "New York, NY"


def test_orchestrator_plan_defaults():
    plan = OrchestratorPlan()
    assert plan.group_name == ""
    assert plan.members == []
    assert plan.venues_found == 0
    assert plan.ranked_venues == []
    assert plan.available_slots == []
    assert plan.recommended_venue is None
    assert plan.agent_log == []


def test_orchestrator_plan_with_data():
    plan = OrchestratorPlan(
        group_name="Test Group",
        members=["Alice", "Bob"],
        venues_found=5,
        steps_completed=["search", "calendar", "recommend", "itinerary"],
        agent_log=["[Search] Found 5 venues", "[Calendar] Found 3 slots"],
        recommended_venue={"name": "Pin Mechanical Co.", "score": 85},
        itinerary_summary="Head to Pin Mechanical Co. on Saturday.",
    )
    assert plan.group_name == "Test Group"
    assert len(plan.members) == 2
    assert len(plan.steps_completed) == 4
    assert plan.recommended_venue["score"] == 85


def test_orchestrator_deps():
    req = QuickPlanRequest(request="test")
    deps = OrchestratorDeps(request=req)
    assert deps.preferences == []
    assert deps.search_result is None
    assert deps.recommendation_result is None
    assert deps.available_slots == []
    assert deps.agent_log == []
