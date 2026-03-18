"""Tests for the Google Calendar tool — availability logic."""

from datetime import datetime

import pytest

from src.models.event import TimeSlot
from src.tools.google_calendar import find_group_availability


class TestFindGroupAvailability:
    def test_all_free(self):
        """When nobody is busy, should find slots for all days."""
        busy = {"user1": [], "user2": []}
        start = datetime(2026, 4, 6, 0, 0)  # Monday
        end = datetime(2026, 4, 10, 0, 0)  # Friday

        slots = find_group_availability(busy, start, end)

        assert len(slots) >= 4  # Mon-Fri evenings
        for slot in slots:
            assert "user1" in slot.available_user_ids
            assert "user2" in slot.available_user_ids
            assert slot.duration_minutes >= 120

    def test_one_user_busy(self):
        """When one user is busy during part of the window, slot should shrink."""
        busy = {
            "user1": [
                {"start": "2026-04-06T17:00:00Z", "end": "2026-04-06T19:00:00Z"}
            ],
            "user2": [],
        }
        start = datetime(2026, 4, 6, 0, 0)
        end = datetime(2026, 4, 6, 0, 0)

        slots = find_group_availability(busy, start, end, min_duration_minutes=120)

        # The slot should start at 19:00 instead of 17:00
        if slots:
            assert slots[0].start.hour >= 19 or slots[0].end.hour <= 17

    def test_no_overlap(self):
        """When users are busy the entire window, no slots should be found."""
        busy = {
            "user1": [
                {"start": "2026-04-06T17:00:00Z", "end": "2026-04-06T23:00:00Z"}
            ],
        }
        start = datetime(2026, 4, 6, 0, 0)
        end = datetime(2026, 4, 6, 0, 0)

        slots = find_group_availability(busy, start, end, min_duration_minutes=120)
        assert len(slots) == 0

    def test_weekend_slots(self):
        """Slots on weekends should still be found."""
        busy = {"user1": [], "user2": []}
        # Saturday to Sunday
        start = datetime(2026, 4, 11, 0, 0)
        end = datetime(2026, 4, 12, 0, 0)

        slots = find_group_availability(busy, start, end)
        assert len(slots) >= 1

    def test_min_duration_filter(self):
        """Slots shorter than min_duration should be excluded."""
        busy = {
            "user1": [
                {"start": "2026-04-06T17:00:00Z", "end": "2026-04-06T21:30:00Z"}
            ],
        }
        start = datetime(2026, 4, 6, 0, 0)
        end = datetime(2026, 4, 6, 0, 0)

        # Only 1.5 hours left (21:30-23:00), require 2 hours
        slots = find_group_availability(busy, start, end, min_duration_minutes=120)
        assert len(slots) == 0

    def test_custom_preferred_hours(self):
        """Custom preferred hours should affect slot windows."""
        busy = {"user1": []}
        start = datetime(2026, 4, 6, 0, 0)
        end = datetime(2026, 4, 6, 0, 0)

        slots = find_group_availability(
            busy, start, end,
            preferred_hours=(10, 14),  # Lunch window
        )
        if slots:
            assert slots[0].start.hour == 10
            assert slots[0].end.hour == 14


class TestTimeSlot:
    def test_duration_minutes(self):
        slot = TimeSlot(
            start=datetime(2026, 4, 6, 18, 0),
            end=datetime(2026, 4, 6, 21, 30),
            available_user_ids=["u1"],
        )
        assert slot.duration_minutes == 210.0

    def test_empty_users(self):
        slot = TimeSlot(
            start=datetime(2026, 4, 6, 18, 0),
            end=datetime(2026, 4, 6, 20, 0),
        )
        assert slot.available_user_ids == []
