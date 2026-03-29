"""Constraint Solver — scores and ranks venues against group preferences.

Hard constraints (budget, dietary, dealbreakers) apply a heavy penalty
but no longer instantly reject venues — this ensures we always return
results even when no venue perfectly matches all criteria.

Soft constraints (cuisine match, rating, popularity, group consensus)
produce a weighted score between 0 and 1.
"""

from __future__ import annotations

import math
import re
from src.models.event import ScoredVenue, Venue, VenueCategory
from src.models.user import BudgetTier, DietaryRestriction, UserPreferences
from src.models.constraints import ConstraintSet


# Budget tiers mapped to numeric levels for comparison
_BUDGET_LEVEL = {
    BudgetTier.LOW: 1,
    BudgetTier.MEDIUM: 2,
    BudgetTier.HIGH: 3,
    BudgetTier.LUXURY: 4,
}

# Penalty multipliers for hard constraint violations (0-1, lower = harsher)
BUDGET_VIOLATION_PENALTY = 0.5     # 50% score reduction for over-budget
DIETARY_VIOLATION_PENALTY = 0.4    # 60% score reduction for dietary conflict
DEALBREAKER_PENALTY = 0.3          # 70% score reduction for dealbreaker match


def _venue_price_level(venue: Venue) -> int:
    """Return numeric price level for a venue (1-4), defaulting to 2."""
    if venue.price_tier:
        return _BUDGET_LEVEL.get(venue.price_tier, 2)
    return 2  # assume moderate if unknown


def _text_match_score(needles: list[str], haystack: str) -> float:
    """OR-logic match: returns 1.0 if ANY needle appears in haystack, 0.0 if none do.

    Preferences are additive options ("I'm open to Italian OR Japanese OR Mexican"),
    not requirements that all need to be satisfied simultaneously. A venue that
    matches even one selected preference is a good match.
    """
    if not needles:
        return 0.0
    haystack_lower = haystack.lower()
    return 1.0 if any(n.lower() in haystack_lower for n in needles) else 0.0


# ── Hard constraint checks (now return penalty multiplier) ────────


def check_budget(venue: Venue, constraint_set: ConstraintSet) -> tuple[bool, float]:
    """Check budget constraint. Returns (passed, penalty_multiplier).

    If passed, multiplier is 1.0. If violated, multiplier reduces the score.
    """
    max_level = _BUDGET_LEVEL.get(constraint_set.budget_max, 4)
    venue_level = _venue_price_level(venue)
    if venue_level <= max_level:
        return True, 1.0
    # How far over budget? 1 tier over = mild penalty, 2+ = heavier
    overage = venue_level - max_level
    penalty = max(BUDGET_VIOLATION_PENALTY, 1.0 - overage * 0.25)
    return False, penalty


def check_dietary(venue: Venue, constraint_set: ConstraintSet) -> tuple[bool, float]:
    """Check dietary constraint. Returns (passed, penalty_multiplier)."""
    if not constraint_set.dietary_restrictions:
        return True, 1.0

    food_categories = {VenueCategory.RESTAURANT, VenueCategory.BAR, VenueCategory.CAFE}
    if venue.category not in food_categories:
        return True, 1.0  # non-food venues pass dietary checks

    # If venue has no dietary info, give benefit of the doubt
    if not venue.dietary_options:
        return True, 1.0

    required = {d for d in constraint_set.dietary_restrictions if d != DietaryRestriction.NONE}
    if not required:
        return True, 1.0

    if required.issubset(set(venue.dietary_options)):
        return True, 1.0

    # Partial match: some restrictions met, some not
    met = required.intersection(set(venue.dietary_options))
    fraction_met = len(met) / len(required) if required else 1.0
    penalty = DIETARY_VIOLATION_PENALTY + (1.0 - DIETARY_VIOLATION_PENALTY) * fraction_met
    return False, penalty


def check_dealbreakers(venue: Venue, constraint_set: ConstraintSet) -> tuple[bool, float]:
    """Check dealbreaker constraint. Returns (passed, penalty_multiplier)."""
    if not constraint_set.dealbreakers:
        return True, 1.0

    venue_text = " ".join([
        venue.name,
        " ".join(venue.categories),
        venue.address,
        venue.category.value,
    ]).lower()

    for dealbreaker in constraint_set.dealbreakers:
        keywords = dealbreaker.lower().split()
        if all(kw in venue_text for kw in keywords):
            return False, DEALBREAKER_PENALTY

    return True, 1.0


def check_hard_constraints(venue: Venue, constraint_set: ConstraintSet) -> tuple[float, list[str]]:
    """Check all hard constraints. Returns (combined_penalty_multiplier, list_of_violations).

    The multiplier is 1.0 if all constraints pass, < 1.0 if any are violated.
    Violations are logged but no longer cause outright rejection.
    """
    violations = []
    combined_penalty = 1.0

    passed, penalty = check_budget(venue, constraint_set)
    if not passed:
        violations.append(
            f"Over budget: venue is {venue.price_tier or '??'}, "
            f"group max is {constraint_set.budget_max}"
        )
        combined_penalty *= penalty

    passed, penalty = check_dietary(venue, constraint_set)
    if not passed:
        violations.append(
            f"Dietary concern: group needs {', '.join(d.value for d in constraint_set.dietary_restrictions)}"
        )
        combined_penalty *= penalty

    passed, penalty = check_dealbreakers(venue, constraint_set)
    if not passed:
        violations.append("Matches a group dealbreaker")
        combined_penalty *= penalty

    return combined_penalty, violations


# Legacy API for backward compatibility
def passes_hard_constraints(venue: Venue, constraint_set: ConstraintSet) -> tuple[bool, list[str]]:
    """Check all hard constraints. Returns (passed, list_of_violations).

    Now uses soft penalties internally but returns bool for backward compat.
    A venue "passes" if the penalty multiplier is >= 0.5.
    """
    penalty, violations = check_hard_constraints(venue, constraint_set)
    return (penalty >= 0.5, violations)


# ── Soft constraint scorers ─────────────────────────────────────────


def score_cuisine_match(venue: Venue, all_preferences: list[UserPreferences]) -> float:
    """How well does this venue match the group's cuisine preferences? (0-1)"""
    if not all_preferences:
        return 0.5

    all_cuisines = []
    for p in all_preferences:
        all_cuisines.extend(p.cuisine_preferences)

    if not all_cuisines:
        return 0.5  # no preferences expressed → neutral

    venue_text = " ".join([venue.name] + venue.categories).lower()
    return _text_match_score(all_cuisines, venue_text)


def score_activity_match(venue: Venue, all_preferences: list[UserPreferences]) -> float:
    """How well does this venue match the group's activity preferences? (0-1)"""
    if not all_preferences:
        return 0.5

    all_activities = []
    for p in all_preferences:
        all_activities.extend(p.activity_preferences)

    if not all_activities:
        return 0.5

    venue_text = " ".join([venue.name] + venue.categories).lower()
    return _text_match_score(all_activities, venue_text)


def score_rating(venue: Venue) -> float:
    """Normalize venue rating to 0-1 scale."""
    if venue.rating is None:
        return 0.5  # unknown → neutral
    # Ratings are typically 1-5
    return max(0.0, min(1.0, (venue.rating - 1.0) / 4.0))


def score_popularity(venue: Venue) -> float:
    """Score based on review count (proxy for popularity). 0-1."""
    if venue.review_count is None:
        return 0.3  # unknown → below average
    if venue.review_count <= 0:
        return 0.0
    return min(1.0, math.log10(venue.review_count) / 3.0)


def score_neighborhood_match(venue: Venue, all_preferences: list[UserPreferences]) -> float:
    """How well does the venue location match preferred neighborhoods? (0-1)"""
    if not all_preferences:
        return 0.5

    all_neighborhoods = []
    for p in all_preferences:
        all_neighborhoods.extend(p.preferred_neighborhoods)

    if not all_neighborhoods:
        return 0.5  # no preference → neutral

    venue_location = f"{venue.address} {venue.city}".lower()
    return _text_match_score(all_neighborhoods, venue_location)


def score_group_consensus(venue: Venue, all_preferences: list[UserPreferences]) -> float:
    """How many group members would enjoy this venue? (0-1)

    A venue scores high if it matches preferences of MOST members,
    not just one person.
    """
    if not all_preferences:
        return 0.5

    member_scores = []
    venue_text = " ".join([venue.name] + venue.categories).lower()

    for prefs in all_preferences:
        # Each member's individual match
        interests = prefs.cuisine_preferences + prefs.activity_preferences
        if interests:
            match = _text_match_score(interests, venue_text)
            member_scores.append(match)
        else:
            member_scores.append(0.5)  # no preferences → neutral

    # Average across all members — rewards venues everyone likes
    return sum(member_scores) / len(member_scores) if member_scores else 0.5


# ── Main solver ─────────────────────────────────────────────────────


# Default weights for soft constraints
DEFAULT_WEIGHTS = {
    "cuisine_match": 0.25,
    "activity_match": 0.20,
    "rating": 0.15,
    "popularity": 0.10,
    "neighborhood": 0.10,
    "group_consensus": 0.20,
}


def score_venue(
    venue: Venue,
    constraint_set: ConstraintSet,
    all_preferences: list[UserPreferences],
    weights: dict[str, float] | None = None,
) -> ScoredVenue:
    """Score a single venue against constraints and preferences.

    Hard constraint violations now apply a penalty multiplier instead of
    rejecting outright, so we always return usable results.
    """
    w = weights or DEFAULT_WEIGHTS

    # Check hard constraints — get penalty multiplier
    penalty_multiplier, violations = check_hard_constraints(venue, constraint_set)

    # Calculate soft constraint scores
    breakdown = {
        "cuisine_match": score_cuisine_match(venue, all_preferences),
        "activity_match": score_activity_match(venue, all_preferences),
        "rating": score_rating(venue),
        "popularity": score_popularity(venue),
        "neighborhood": score_neighborhood_match(venue, all_preferences),
        "group_consensus": score_group_consensus(venue, all_preferences),
    }

    # Weighted sum
    total_weight = sum(w.get(k, 0) for k in breakdown)
    if total_weight == 0:
        total_weight = 1.0

    raw_score = sum(breakdown[k] * w.get(k, 0) for k in breakdown) / total_weight

    # Apply hard constraint penalty
    score = raw_score * penalty_multiplier
    score = round(max(0.0, min(1.0, score)), 3)

    # Build explanation
    top_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
    strengths = [f"{k.replace('_', ' ').title()}: {v:.0%}" for k, v in top_factors if v > 0.5]
    explanation = f"Score: {score:.0%}"
    if strengths:
        explanation += f" — Strong in: {', '.join(strengths)}"
    if violations:
        explanation += f" — ⚠️ {'; '.join(violations)}"

    return ScoredVenue(
        venue=venue,
        score=score,
        score_breakdown=breakdown,
        explanation=explanation,
    )


def rank_venues(
    venues: list[Venue],
    constraint_set: ConstraintSet,
    all_preferences: list[UserPreferences],
    weights: dict[str, float] | None = None,
) -> list[ScoredVenue]:
    """Score and rank all venues. All venues get a score — none are rejected outright."""
    scored = [
        score_venue(venue, constraint_set, all_preferences, weights)
        for venue in venues
    ]

    # Sort by score descending
    scored.sort(key=lambda sv: -sv.score)
    return scored
