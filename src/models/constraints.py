from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .user import BudgetTier, DietaryRestriction


class HardConstraintType(str, Enum):
    BUDGET = "budget"
    DIETARY = "dietary"
    AVAILABILITY = "availability"
    ACCESSIBILITY = "accessibility"
    DEALBREAKER = "dealbreaker"


class SoftConstraintType(str, Enum):
    CUISINE_MATCH = "cuisine_match"
    RATING = "rating"
    DISTANCE = "distance"
    POPULARITY = "popularity"
    NOVELTY = "novelty"
    GROUP_CONSENSUS = "group_consensus"


class HardConstraint(BaseModel):
    type: HardConstraintType
    description: str
    value: str | float | list[str] = ""


class SoftConstraint(BaseModel):
    type: SoftConstraintType
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    description: str = ""


class ConstraintSet(BaseModel):
    """All constraints for a planning session."""

    group_id: str
    budget_max: BudgetTier = BudgetTier.MEDIUM
    dietary_restrictions: list[DietaryRestriction] = Field(default_factory=list)
    dealbreakers: list[str] = Field(default_factory=list)
    accessibility_needs: list[str] = Field(default_factory=list)
    hard_constraints: list[HardConstraint] = Field(default_factory=list)
    soft_constraints: list[SoftConstraint] = Field(default_factory=list)

    @classmethod
    def from_user_preferences(cls, group_id: str, preferences_list: list) -> ConstraintSet:
        """Aggregate multiple users' preferences into a unified constraint set."""
        all_dietary = set()
        all_dealbreakers = set()
        all_accessibility = set()
        strictest_budget = BudgetTier.LUXURY

        budget_order = [BudgetTier.LOW, BudgetTier.MEDIUM, BudgetTier.HIGH, BudgetTier.LUXURY]

        for prefs in preferences_list:
            all_dietary.update(prefs.dietary_restrictions)
            all_dealbreakers.update(prefs.dealbreakers)
            all_accessibility.update(prefs.accessibility_needs)
            if budget_order.index(prefs.budget_max) < budget_order.index(strictest_budget):
                strictest_budget = prefs.budget_max

        return cls(
            group_id=group_id,
            budget_max=strictest_budget,
            dietary_restrictions=list(all_dietary),
            dealbreakers=list(all_dealbreakers),
            accessibility_needs=list(all_accessibility),
        )
