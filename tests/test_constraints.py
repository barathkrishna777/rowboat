"""Tests for the constraint solver."""

import pytest

from src.constraints.solver import (
    check_budget,
    check_dietary,
    check_dealbreakers,
    passes_hard_constraints,
    score_cuisine_match,
    score_activity_match,
    score_rating,
    score_popularity,
    score_group_consensus,
    score_venue,
    rank_venues,
)
from src.models.event import Venue, VenueCategory, VenueSource, ScoredVenue
from src.models.user import BudgetTier, DietaryRestriction, UserPreferences
from src.models.constraints import ConstraintSet


# ── Fixtures ────────────────────────────────────────────────────────


def _make_venue(
    name: str = "Test Venue",
    category: VenueCategory = VenueCategory.RESTAURANT,
    categories: list[str] | None = None,
    price_tier: BudgetTier | None = BudgetTier.MEDIUM,
    rating: float | None = 4.0,
    review_count: int | None = 100,
    dietary_options: list[DietaryRestriction] | None = None,
    address: str = "123 Main St, Pittsburgh, PA",
) -> Venue:
    return Venue(
        id="test-1",
        source=VenueSource.GOOGLE,
        source_id="gp-1",
        name=name,
        category=category,
        categories=categories or [],
        price_tier=price_tier,
        rating=rating,
        review_count=review_count,
        dietary_options=dietary_options or [],
        address=address,
    )


def _make_constraints(
    budget_max: BudgetTier = BudgetTier.MEDIUM,
    dietary: list[DietaryRestriction] | None = None,
    dealbreakers: list[str] | None = None,
) -> ConstraintSet:
    return ConstraintSet(
        group_id="test-group",
        budget_max=budget_max,
        dietary_restrictions=dietary or [],
        dealbreakers=dealbreakers or [],
    )


def _make_prefs(
    cuisines: list[str] | None = None,
    activities: list[str] | None = None,
    budget: BudgetTier = BudgetTier.MEDIUM,
) -> UserPreferences:
    return UserPreferences(
        cuisine_preferences=cuisines or [],
        activity_preferences=activities or [],
        budget_max=budget,
    )


# ── Hard constraint tests ──────────────────────────────────────────


class TestBudgetConstraint:
    def test_venue_within_budget(self):
        venue = _make_venue(price_tier=BudgetTier.LOW)
        cs = _make_constraints(budget_max=BudgetTier.MEDIUM)
        passed, penalty = check_budget(venue, cs)
        assert passed is True
        assert penalty == 1.0

    def test_venue_at_budget(self):
        venue = _make_venue(price_tier=BudgetTier.MEDIUM)
        cs = _make_constraints(budget_max=BudgetTier.MEDIUM)
        passed, penalty = check_budget(venue, cs)
        assert passed is True
        assert penalty == 1.0

    def test_venue_over_budget(self):
        venue = _make_venue(price_tier=BudgetTier.HIGH)
        cs = _make_constraints(budget_max=BudgetTier.MEDIUM)
        passed, penalty = check_budget(venue, cs)
        assert passed is False
        assert penalty < 1.0  # score penalized but not zero

    def test_venue_no_price(self):
        venue = _make_venue(price_tier=None)
        cs = _make_constraints(budget_max=BudgetTier.MEDIUM)
        passed, penalty = check_budget(venue, cs)
        assert passed is True  # default assumes moderate


class TestDietaryConstraint:
    def test_no_restrictions(self):
        venue = _make_venue()
        cs = _make_constraints(dietary=[])
        passed, penalty = check_dietary(venue, cs)
        assert passed is True
        assert penalty == 1.0

    def test_non_food_venue_always_passes(self):
        venue = _make_venue(category=VenueCategory.ACTIVITY)
        cs = _make_constraints(dietary=[DietaryRestriction.VEGAN])
        passed, penalty = check_dietary(venue, cs)
        assert passed is True
        assert penalty == 1.0

    def test_food_venue_no_info_passes(self):
        venue = _make_venue(dietary_options=[])
        cs = _make_constraints(dietary=[DietaryRestriction.VEGETARIAN])
        passed, penalty = check_dietary(venue, cs)
        assert passed is True  # benefit of the doubt
        assert penalty == 1.0

    def test_food_venue_supports_dietary(self):
        venue = _make_venue(dietary_options=[DietaryRestriction.VEGETARIAN, DietaryRestriction.VEGAN])
        cs = _make_constraints(dietary=[DietaryRestriction.VEGETARIAN])
        passed, penalty = check_dietary(venue, cs)
        assert passed is True
        assert penalty == 1.0

    def test_food_venue_missing_dietary(self):
        venue = _make_venue(dietary_options=[DietaryRestriction.VEGETARIAN])
        cs = _make_constraints(dietary=[DietaryRestriction.VEGAN])
        passed, penalty = check_dietary(venue, cs)
        assert passed is False
        assert penalty < 1.0  # penalized but not zero


class TestDealbreakers:
    def test_no_dealbreakers(self):
        venue = _make_venue()
        cs = _make_constraints(dealbreakers=[])
        passed, penalty = check_dealbreakers(venue, cs)
        assert passed is True
        assert penalty == 1.0

    def test_matching_dealbreaker(self):
        venue = _make_venue(name="Loud Sports Bar", categories=["bar", "sports"])
        cs = _make_constraints(dealbreakers=["loud"])
        passed, penalty = check_dealbreakers(venue, cs)
        assert passed is False
        assert penalty < 1.0  # penalized

    def test_non_matching_dealbreaker(self):
        venue = _make_venue(name="Quiet Italian Bistro")
        cs = _make_constraints(dealbreakers=["loud"])
        passed, penalty = check_dealbreakers(venue, cs)
        assert passed is True
        assert penalty == 1.0


class TestHardConstraints:
    def test_all_pass(self):
        venue = _make_venue(price_tier=BudgetTier.LOW)
        cs = _make_constraints(budget_max=BudgetTier.MEDIUM)
        passed, violations = passes_hard_constraints(venue, cs)
        assert passed is True
        assert violations == []

    def test_budget_violation(self):
        venue = _make_venue(price_tier=BudgetTier.LUXURY)
        cs = _make_constraints(budget_max=BudgetTier.LOW)
        passed, violations = passes_hard_constraints(venue, cs)
        # With soft penalties, venue still "passes" (penalty >= 0.5) but has violations logged
        assert len(violations) >= 1


# ── Soft constraint tests ──────────────────────────────────────────


class TestSoftScores:
    def test_cuisine_match_full(self):
        venue = _make_venue(name="Italian Pizza Place", categories=["italian", "pizza"])
        prefs = [_make_prefs(cuisines=["italian"])]
        score = score_cuisine_match(venue, prefs)
        assert score > 0.0

    def test_cuisine_match_none(self):
        venue = _make_venue(name="Bowling Alley", categories=["bowling", "activity"])
        prefs = [_make_prefs(cuisines=["japanese"])]
        score = score_cuisine_match(venue, prefs)
        assert score == 0.0

    def test_activity_match(self):
        venue = _make_venue(name="Escape Room Mania", categories=["escape room", "entertainment"])
        prefs = [_make_prefs(activities=["escape room"])]
        score = score_activity_match(venue, prefs)
        assert score > 0.0

    def test_rating_high(self):
        venue = _make_venue(rating=5.0)
        assert score_rating(venue) == 1.0

    def test_rating_low(self):
        venue = _make_venue(rating=1.0)
        assert score_rating(venue) == 0.0

    def test_rating_none(self):
        venue = _make_venue(rating=None)
        assert score_rating(venue) == 0.5  # neutral

    def test_popularity_high(self):
        venue = _make_venue(review_count=1000)
        assert score_popularity(venue) == 1.0

    def test_popularity_zero(self):
        venue = _make_venue(review_count=0)
        assert score_popularity(venue) == 0.0


class TestGroupConsensus:
    def test_consensus_high(self):
        """All members like Italian, venue is Italian → high score."""
        venue = _make_venue(name="Italian Kitchen", categories=["italian", "restaurant"])
        prefs = [
            _make_prefs(cuisines=["italian"]),
            _make_prefs(cuisines=["italian"]),
            _make_prefs(cuisines=["italian"]),
        ]
        score = score_group_consensus(venue, prefs)
        assert score > 0.5

    def test_consensus_mixed(self):
        """Only one member likes Italian → lower score."""
        venue = _make_venue(name="Italian Kitchen", categories=["italian"])
        prefs = [
            _make_prefs(cuisines=["italian"]),
            _make_prefs(cuisines=["japanese"]),
            _make_prefs(cuisines=["mexican"]),
        ]
        score = score_group_consensus(venue, prefs)
        assert score < 0.5


# ── Full scoring and ranking ────────────────────────────────────────


class TestFullScoring:
    def test_score_venue_passing(self):
        venue = _make_venue(
            name="Great Italian Place",
            categories=["italian", "restaurant"],
            price_tier=BudgetTier.MEDIUM,
            rating=4.5,
        )
        cs = _make_constraints(budget_max=BudgetTier.HIGH)
        prefs = [_make_prefs(cuisines=["italian"])]
        scored = score_venue(venue, cs, prefs)
        assert scored.score > 0
        assert "cuisine_match" in scored.score_breakdown

    def test_score_venue_penalized(self):
        """Over-budget venues get penalized but still receive a non-zero score."""
        venue = _make_venue(price_tier=BudgetTier.LUXURY)
        cs = _make_constraints(budget_max=BudgetTier.LOW)
        scored = score_venue(venue, cs, [])
        assert scored.score > 0.0  # no longer hard-rejected
        assert scored.score < 0.5  # but significantly penalized
        assert "⚠️" in scored.explanation

    def test_rank_venues(self):
        v1 = _make_venue(name="Italian Kitchen", categories=["italian"], rating=4.5, price_tier=BudgetTier.MEDIUM)
        v2 = _make_venue(name="Bowling Fun", categories=["bowling"], rating=3.0, price_tier=BudgetTier.LOW)
        v3 = _make_venue(name="Luxury Club", categories=["club"], rating=5.0, price_tier=BudgetTier.LUXURY)

        cs = _make_constraints(budget_max=BudgetTier.MEDIUM)
        prefs = [_make_prefs(cuisines=["italian"])]

        ranked = rank_venues([v1, v2, v3], cs, prefs)
        assert len(ranked) == 3

        # v3 should be penalized (over budget) and rank last
        assert ranked[-1].venue.name == "Luxury Club"
        assert ranked[-1].score < ranked[0].score  # lowest score

        # v1 should rank higher than v2 (cuisine match + higher rating)
        assert ranked[0].venue.name == "Italian Kitchen"
