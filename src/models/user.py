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


class User(BaseModel):
    id: str
    name: str
    email: str
    google_calendar_token: dict | None = None
    preferences: UserPreferences | None = None


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
