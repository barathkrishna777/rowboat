"""Constraint Solver — scores and ranks venues against group preferences.

Hard constraints (budget, dietary, dealbreakers) instantly reject venues.
Soft constraints (cuisine match, rating, popularity, group consensus) produce
a weighted score between 0 and 1.
"""

from __future__ import annotations

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


def _venue_price_level(venue: Venue) -> int:
    """Return numeric price level for a venue (1-4), defaulting to 2."""
    if venue.price_tier:
        return _BUDGET_LEVEL.get(venue.price_tier, 2)
    return 2  # assume moderate if unknown


def _text_match_score(needles: list[str], haystack: str) -> float:
    """Fuzzy match: what fraction of needles appear in haystack (case-insensitive)?"""
    if not needles:
        return 0.0
    haystack_lower = haystack.lower()
    matches = sum(1 for n in needles if n.lower() in haystack_lower)
    return matches / len(needles)


# ── Hard constraint checks ──────────────────────────────────────────


def check_budget(venue: Venue, constraint_set: ConstraintSet) -> bool:
    """Return True if venue passes the budget constraint."""
    max_level = _BUDGET_LEVEL.get(constraint_set.budget_max, 4)
    venue_level = _venue_price_level(venue)
    return venue_level <= max_level


def check_dietary(venue: Venue, constraint_set: ConstraintSet) -> bool:
    """Return True if venue doesn't violate dietary restrictions.

    For restaurants/cafes/bars, we check if the venue explicitly supports
    the required dietary options. If no dietary info is available,
    we give it the benefit of the doubt (pass).
    """
    if not constraint_set.dietary_restrictions:
        return True

    food_categories = {VenueCategory.RESTAURANT, VenueCategory.BAR, VenueCategory.CAFE}
    if venue.category not in food_categories:
        return True  # non-food venues pass dietary checks

    # If venue has no dietary info, give benefit of the doubt
    if not venue.dietary_options:
        return True

    # Check if venue supports all required dietary restrictions
    # (except NONE which means no restrictions)
    required = {d for d in constraint_set.dietary_restrictions if d != DietaryRestriction.NONE}
    if not required:
        return True

    return required.issubset(set(venue.dietary_options))


def check_dealbreakers(venue: Venue, constraint_set: ConstraintSet) -> bool:
    """Return True if venue doesn't trigger any dealbreakers.

    Checks venue name, categories, and address against dealbreaker keywords.
    """
    if not constraint_set.dealbreakers:
        return True

    venue_text = " ".join([
        venue.name,
        " ".join(venue.categories),
        venue.address,
        venue.category.value,
    ]).lower()

    for dealbreaker in constraint_set.dealbreakers:
        # Simple keyword matching — if the dealbreaker keyword appears
        # in the venue description, it fails
        keywords = dealbreaker.lower().split()
        if all(kw in venue_text for kw in keywords):
            return False

    return True


def passes_hard_constraints(venue: Venue, constraint_set: ConstraintSet) -> tuple[bool, list[str]]:
    """Check all hard constraints. Returns (passed, list_of_violations)."""
    violations = []

    if not check_budget(venue, constraint_set):
        violations.append(
            f"Over budget: venue is {venue.price_tier or '??'}, "
            f"group max is {constraint_set.budget_max}"
        )

    if not check_dietary(venue, constraint_set):
        violations.append(
            f"Dietary conflict: group needs {', '.join(d.value for d in constraint_set.dietary_restrictions)}"
        )

    if not check_dealbreakers(venue, constraint_set):
        violations.append("Matches a group dealbreaker")

    return (len(violations) == 0, violations)


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
    # Log scale: 0 reviews = 0, 10 = 0.3, 100 = 0.6, 1000+ = 1.0
    import math
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

    Returns a ScoredVenue with score=0.0 if hard constraints are violated.
    """
    w = weights or DEFAULT_WEIGHTS

    # Check hard constraints first
    passed, violations = passes_hard_constraints(venue, constraint_set)
    if not passed:
        return ScoredVenue(
            venue=venue,
            score=0.0,
            score_breakdown={"hard_constraint_violations": 1.0},
            explanation=f"❌ Rejected: {'; '.join(violations)}",
        )

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

    score = sum(breakdown[k] * w.get(k, 0) for k in breakdown) / total_weight
    score = round(max(0.0, min(1.0, score)), 3)

    # Build explanation
    top_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
    strengths = [f"{k.replace('_', ' ').title()}: {v:.0%}" for k, v in top_factors if v > 0.5]
    explanation = f"Score: {score:.0%}"
    if strengths:
        explanation += f" — Strong in: {', '.join(strengths)}"

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
    """Score and rank all venues. Rejected venues are at the bottom with score=0."""
    scored = [
        score_venue(venue, constraint_set, all_preferences, weights)
        for venue in venues
    ]

    # Sort: passing venues by score descending, then rejected ones
    scored.sort(key=lambda sv: (-1 if sv.score > 0 else 0, -sv.score))
    return scored
