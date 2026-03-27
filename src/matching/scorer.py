"""Pure-Python pairwise similarity scorer for user matching.

Computes a 0–1 score between two users based on preferences, profile tags,
budget compatibility, neighborhood overlap, group-size fit, and dealbreaker
penalties.  All inputs are explicit (no side effects or DB access).
"""

from __future__ import annotations

from src.models.user import BudgetTier, UserPreferences, UserProfile

# Budget tiers ordered by cost for distance calculation.
_BUDGET_ORDER: dict[BudgetTier, int] = {
    BudgetTier.LOW: 0,
    BudgetTier.MEDIUM: 1,
    BudgetTier.HIGH: 2,
    BudgetTier.LUXURY: 3,
}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity: |intersection| / |union|, 0 when both empty."""
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _budget_compat(a: BudgetTier, b: BudgetTier) -> float:
    """1.0 when identical, decreases linearly with distance (max gap = 3)."""
    dist = abs(_BUDGET_ORDER[a] - _BUDGET_ORDER[b])
    return 1.0 - dist / 3.0


def _group_size_overlap(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Fraction of overlap between two (min, max) ranges, 0 if disjoint."""
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    overlap = max(0, hi - lo + 1)
    span = max(a[1], b[1]) - min(a[0], b[0]) + 1
    return overlap / span if span > 0 else 0.0


def _dealbreaker_penalty(a_breakers: list[str], b_breakers: list[str]) -> float:
    """Soft penalty: 0.15 per shared dealbreaker keyword (capped at 1.0).

    Compares lowercased tokens for partial overlap.
    """
    if not a_breakers and not b_breakers:
        return 0.0
    a_tokens = {w.lower() for phrase in a_breakers for w in phrase.split()}
    b_tokens = {w.lower() for phrase in b_breakers for w in phrase.split()}
    shared = len(a_tokens & b_tokens)
    return min(shared * 0.15, 1.0)


def score_pair(
    prefs_a: UserPreferences | None,
    prefs_b: UserPreferences | None,
    profile_a: UserProfile | None = None,
    profile_b: UserProfile | None = None,
    *,
    w_cuisine: float = 0.20,
    w_activity: float = 0.20,
    w_tags: float = 0.15,
    w_budget: float = 0.15,
    w_neighborhood: float = 0.15,
    w_group_size: float = 0.15,
) -> float:
    """Return a 0–1 similarity score for a pair of users.

    Weights must sum to 1.0.  Components:
      - cuisine overlap (Jaccard)
      - activity overlap (Jaccard)
      - interest-tag overlap (Jaccard, from profile)
      - budget compatibility (linear distance)
      - neighborhood overlap (Jaccard)
      - group-size range overlap
      - dealbreaker penalty (subtracted at the end)
    """
    pa = prefs_a or UserPreferences()
    pb = prefs_b or UserPreferences()
    pra = profile_a or UserProfile()
    prb = profile_b or UserProfile()

    cuisine = _jaccard(
        {c.lower() for c in pa.cuisine_preferences},
        {c.lower() for c in pb.cuisine_preferences},
    )
    activity = _jaccard(
        {a.lower() for a in pa.activity_preferences},
        {a.lower() for a in pb.activity_preferences},
    )
    tags = _jaccard(
        {t.lower() for t in pra.interest_tags},
        {t.lower() for t in prb.interest_tags},
    )
    budget = _budget_compat(pa.budget_max, pb.budget_max)
    neighborhood = _jaccard(
        {n.lower() for n in pa.preferred_neighborhoods},
        {n.lower() for n in pb.preferred_neighborhoods},
    )
    group_size = _group_size_overlap(pa.group_size_comfort, pb.group_size_comfort)

    raw = (
        w_cuisine * cuisine
        + w_activity * activity
        + w_tags * tags
        + w_budget * budget
        + w_neighborhood * neighborhood
        + w_group_size * group_size
    )

    penalty = _dealbreaker_penalty(pa.dealbreakers, pb.dealbreakers)
    return max(0.0, min(1.0, raw - penalty))
