from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DietaryRestriction(str, Enum):
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    HALAL = "halal"
    KOSHER = "kosher"
    NUT_ALLERGY = "nut_allergy"
    DAIRY_FREE = "dairy_free"
    SHELLFISH_ALLERGY = "shellfish_allergy"


class BudgetTier(str, Enum):
    LOW = "$"
    MEDIUM = "$$"
    HIGH = "$$$"
    LUXURY = "$$$$"


class UserPreferences(BaseModel):
    cuisine_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred cuisine types, e.g. ['italian', 'japanese', 'mexican']",
    )
    activity_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred activity types, e.g. ['bowling', 'concert', 'escape_room']",
    )
    dietary_restrictions: list[DietaryRestriction] = Field(default_factory=list)
    budget_max: BudgetTier = BudgetTier.MEDIUM
    dealbreakers: list[str] = Field(
        default_factory=list,
        description="Free-text dealbreakers, e.g. ['no loud places', 'must have parking']",
    )
    preferred_neighborhoods: list[str] = Field(default_factory=list)
    group_size_comfort: tuple[int, int] = Field(
        default=(2, 10),
        description="(min, max) group size this user is comfortable with",
    )
    accessibility_needs: list[str] = Field(default_factory=list)


class AvailabilityWindow(BaseModel):
    """A recurring weekly availability slot."""
    day: str = Field(description="Day of week, e.g. 'monday', 'saturday'")
    start: str = Field(description="Start time in HH:MM (24h), e.g. '18:00'")
    end: str = Field(description="End time in HH:MM (24h), e.g. '22:00'")


class UserAvailability(BaseModel):
    """Structured availability for matching — editable without calendar OAuth."""
    timezone: str = "America/New_York"
    weekly_windows: list[AvailabilityWindow] = Field(default_factory=list)
    notes: str = Field(default="", description="e.g. 'usually free weekends'")


class UserProfile(BaseModel):
    """Public/social profile surface for discovery and matching."""
    display_name: str | None = None
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None
    interest_tags: list[str] = Field(
        default_factory=list,
        description="Free-form interest tags for matching, e.g. ['live-music', 'hiking', 'brunch']",
    )


class User(BaseModel):
    id: str
    name: str
    email: str
    username: str | None = None
    auth_provider: str | None = None
    google_calendar_token: dict | None = None
    preferences: UserPreferences | None = None
    profile: UserProfile | None = None
    availability: UserAvailability | None = None


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class Friendship(BaseModel):
    id: int | None = None
    requester_id: str
    addressee_id: str
    status: FriendshipStatus = FriendshipStatus.PENDING
    requester: User | None = None
    addressee: User | None = None


class FriendRequest(BaseModel):
    from_user_id: str
    to_email: str


class Group(BaseModel):
    id: str
    name: str
    member_ids: list[str] = Field(default_factory=list)
    created_by: str
