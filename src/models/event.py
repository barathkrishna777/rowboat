from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from .user import BudgetTier, DietaryRestriction


class VenueSource(str, Enum):
    YELP = "yelp"
    EVENTBRITE = "eventbrite"
    TICKETMASTER = "ticketmaster"
    GOOGLE = "google"
    MANUAL = "manual"


class VenueCategory(str, Enum):
    RESTAURANT = "restaurant"
    BAR = "bar"
    CAFE = "cafe"
    ACTIVITY = "activity"
    CONCERT = "concert"
    SPORTS = "sports"
    THEATER = "theater"
    OUTDOOR = "outdoor"
    OTHER = "other"


class Venue(BaseModel):
    id: str
    source: VenueSource
    source_id: str
    name: str
    category: VenueCategory = VenueCategory.OTHER
    categories: list[str] = Field(default_factory=list, description="Raw category tags from API")
    address: str = ""
    city: str = ""
    lat: float | None = None
    lng: float | None = None
    price_tier: BudgetTier | None = None
    rating: float | None = None
    review_count: int | None = None
    phone: str | None = None
    url: str | None = None
    image_url: str | None = None
    hours: dict[str, str] | None = None
    dietary_options: list[DietaryRestriction] = Field(default_factory=list)
    raw_details: dict | None = None


class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    available_user_ids: list[str] = Field(default_factory=list)

    @property
    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60


class ItineraryItem(BaseModel):
    venue: Venue
    time_slot: TimeSlot
    activity_type: str
    estimated_cost_per_person: float = 0.0
    notes: str = ""


class Itinerary(BaseModel):
    id: str
    group_id: str
    items: list[ItineraryItem] = Field(default_factory=list)
    total_estimated_cost_per_person: float = 0.0
    score: float = 0.0
    explanation: str = ""
    status: Literal["proposed", "accepted", "booked", "completed", "cancelled"] = "proposed"
    created_at: datetime = Field(default_factory=datetime.now)


class ScoredVenue(BaseModel):
    venue: Venue
    score: float = Field(ge=0.0, le=1.0)
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""
