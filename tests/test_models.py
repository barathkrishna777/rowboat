"""Tests for Pydantic data models."""

from datetime import datetime, timedelta

import pytest

from src.models.constraints import ConstraintSet
from src.models.event import Itinerary, ScoredVenue, TimeSlot, Venue, VenueCategory, VenueSource
from src.models.feedback import FeedbackSummary, PostEventFeedback
from src.models.user import BudgetTier, DietaryRestriction, Group, User, UserPreferences


class TestUserModels:
    def test_user_creation(self):
        user = User(id="u1", name="Test User", email="test@example.com")
        assert user.id == "u1"
        assert user.preferences is None

    def test_user_preferences_defaults(self):
        prefs = UserPreferences()
        assert prefs.cuisine_preferences == []
        assert prefs.budget_max == BudgetTier.MEDIUM
        assert prefs.group_size_comfort == (2, 10)

    def test_user_preferences_full(self):
        prefs = UserPreferences(
            cuisine_preferences=["italian", "japanese"],
            dietary_restrictions=[DietaryRestriction.VEGETARIAN],
            budget_max=BudgetTier.HIGH,
            dealbreakers=["no loud places"],
        )
        assert len(prefs.cuisine_preferences) == 2
        assert DietaryRestriction.VEGETARIAN in prefs.dietary_restrictions

    def test_group_creation(self):
        group = Group(id="g1", name="Test Group", member_ids=["u1", "u2"], created_by="u1")
        assert len(group.member_ids) == 2


class TestEventModels:
    def test_venue_creation(self):
        venue = Venue(
            id="v1",
            source=VenueSource.YELP,
            source_id="yelp-123",
            name="Test Venue",
            category=VenueCategory.RESTAURANT,
            rating=4.5,
        )
        assert venue.source == VenueSource.YELP
        assert venue.rating == 4.5

    def test_time_slot_duration(self):
        start = datetime(2026, 4, 15, 18, 0)
        end = datetime(2026, 4, 15, 20, 30)
        slot = TimeSlot(start=start, end=end, available_user_ids=["u1", "u2"])
        assert slot.duration_minutes == 150.0

    def test_scored_venue_bounds(self):
        venue = Venue(id="v1", source=VenueSource.YELP, source_id="x", name="Test")
        sv = ScoredVenue(venue=venue, score=0.85, explanation="Good match")
        assert 0.0 <= sv.score <= 1.0

    def test_scored_venue_invalid_score(self):
        venue = Venue(id="v1", source=VenueSource.YELP, source_id="x", name="Test")
        with pytest.raises(Exception):
            ScoredVenue(venue=venue, score=1.5)

    def test_itinerary_status(self):
        it = Itinerary(id="it1", group_id="g1")
        assert it.status == "proposed"
        assert it.items == []


class TestConstraintModels:
    def test_constraint_set_from_preferences(self):
        prefs = [
            UserPreferences(
                dietary_restrictions=[DietaryRestriction.VEGETARIAN],
                budget_max=BudgetTier.LOW,
                dealbreakers=["no smoking"],
            ),
            UserPreferences(
                dietary_restrictions=[DietaryRestriction.HALAL],
                budget_max=BudgetTier.MEDIUM,
                dealbreakers=["must have parking"],
            ),
        ]
        cs = ConstraintSet.from_user_preferences("g1", prefs)
        # Should use the strictest budget
        assert cs.budget_max == BudgetTier.LOW
        # Should union all dietary restrictions
        assert DietaryRestriction.VEGETARIAN in cs.dietary_restrictions
        assert DietaryRestriction.HALAL in cs.dietary_restrictions
        # Should union all dealbreakers
        assert "no smoking" in cs.dealbreakers
        assert "must have parking" in cs.dealbreakers


class TestFeedbackModels:
    def test_feedback_creation(self):
        fb = PostEventFeedback(
            feedback_id="fb1",
            user_id="u1",
            event_id="e1",
            overall_rating=4,
            would_repeat=True,
        )
        assert fb.overall_rating == 4

    def test_feedback_invalid_rating(self):
        with pytest.raises(Exception):
            PostEventFeedback(
                feedback_id="fb1",
                user_id="u1",
                event_id="e1",
                overall_rating=6,
            )

    def test_feedback_summary(self):
        summary = FeedbackSummary(
            event_id="e1",
            avg_rating=4.2,
            total_responses=5,
            common_likes=["food", "atmosphere"],
            repeat_percentage=80.0,
        )
        assert summary.avg_rating == 4.2


class TestSampleData:
    def test_load_sample_venues(self, sample_venues):
        assert len(sample_venues) == 3
        assert sample_venues[0].name == "Pasta Prima"
        assert sample_venues[0].source == VenueSource.YELP

    def test_load_sample_preferences(self, sample_preferences):
        assert len(sample_preferences) == 3
        assert sample_preferences[0]["name"] == "Anushree"
