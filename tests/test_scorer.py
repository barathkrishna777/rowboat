"""Golden-case tests for the pairwise similarity scorer (Phase 2.3)."""

import pytest

from src.matching.scorer import (
    _budget_compat,
    _group_size_overlap,
    _jaccard,
    score_pair,
)
from src.models.user import BudgetTier, UserPreferences, UserProfile


class TestJaccard:
    def test_both_empty(self):
        assert _jaccard(set(), set()) == 0.0

    def test_identical(self):
        assert _jaccard({"a", "b"}, {"a", "b"}) == 1.0

    def test_disjoint(self):
        assert _jaccard({"a"}, {"b"}) == 0.0

    def test_partial(self):
        assert _jaccard({"a", "b", "c"}, {"b", "c", "d"}) == pytest.approx(0.5)


class TestBudgetCompat:
    def test_same_tier(self):
        assert _budget_compat(BudgetTier.MEDIUM, BudgetTier.MEDIUM) == 1.0

    def test_adjacent(self):
        assert _budget_compat(BudgetTier.LOW, BudgetTier.MEDIUM) == pytest.approx(2 / 3)

    def test_extremes(self):
        assert _budget_compat(BudgetTier.LOW, BudgetTier.LUXURY) == pytest.approx(0.0)


class TestGroupSizeOverlap:
    def test_identical(self):
        assert _group_size_overlap((2, 6), (2, 6)) == 1.0

    def test_disjoint(self):
        assert _group_size_overlap((2, 3), (5, 8)) == 0.0

    def test_partial(self):
        # (2,6) & (4,8) → overlap 4-6=3, span 2-8=7
        assert _group_size_overlap((2, 6), (4, 8)) == pytest.approx(3 / 7)


class TestScorePair:
    def test_identical_users_high_score(self):
        prefs = UserPreferences(
            cuisine_preferences=["italian", "japanese"],
            activity_preferences=["bowling", "hiking"],
            budget_max=BudgetTier.MEDIUM,
            preferred_neighborhoods=["shadyside", "squirrel hill"],
            group_size_comfort=(3, 6),
        )
        profile = UserProfile(interest_tags=["brunch", "live-music"])
        score = score_pair(prefs, prefs, profile, profile)
        assert score == pytest.approx(1.0)

    def test_completely_different_users_low_score(self):
        a = UserPreferences(
            cuisine_preferences=["italian"],
            activity_preferences=["bowling"],
            budget_max=BudgetTier.LOW,
            preferred_neighborhoods=["shadyside"],
            group_size_comfort=(2, 3),
        )
        b = UserPreferences(
            cuisine_preferences=["thai"],
            activity_preferences=["opera"],
            budget_max=BudgetTier.LUXURY,
            preferred_neighborhoods=["downtown"],
            group_size_comfort=(8, 10),
        )
        score = score_pair(a, b)
        assert score < 0.15

    def test_none_prefs_returns_zero(self):
        # Two users with no preferences → all Jaccard = 0, budget = 1 (same default)
        score = score_pair(None, None)
        # budget (1.0*0.15) + group_size (1.0*0.15) = 0.30
        assert score == pytest.approx(0.30)

    def test_dealbreakers_reduce_score(self):
        prefs_base = UserPreferences(
            cuisine_preferences=["italian", "japanese"],
            activity_preferences=["bowling"],
            budget_max=BudgetTier.MEDIUM,
        )
        prefs_with_breakers = UserPreferences(
            cuisine_preferences=["italian", "japanese"],
            activity_preferences=["bowling"],
            budget_max=BudgetTier.MEDIUM,
            dealbreakers=["no loud places"],
        )
        score_clean = score_pair(prefs_base, prefs_base)
        score_shared = score_pair(prefs_with_breakers, prefs_with_breakers)
        assert score_shared < score_clean

    def test_interest_tags_boost_score(self):
        prefs = UserPreferences()
        prof_a = UserProfile(interest_tags=["hiking", "brunch", "dogs"])
        prof_b = UserProfile(interest_tags=["hiking", "brunch", "cats"])
        score_with_tags = score_pair(prefs, prefs, prof_a, prof_b)
        score_no_tags = score_pair(prefs, prefs)
        assert score_with_tags > score_no_tags
