"""Preset parsing and ranking helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.models.hangout import Hangout
from src.models.preset import PresetCriteria, PresetParseResponse


KEYWORDS = {
    "activity_preferences": {
        "hike": "hiking",
        "hiking": "hiking",
        "trail": "hiking",
        "party": "nightlife",
        "club": "nightlife",
        "karaoke": "karaoke",
        "comedy": "comedy",
        "museum": "museum",
        "brunch": "brunch",
        "bowling": "bowling",
        "board game": "board games",
        "live music": "live music",
    },
    "cuisine_preferences": {
        "sushi": "japanese",
        "ramen": "japanese",
        "pizza": "italian",
        "pasta": "italian",
        "taco": "mexican",
        "roast": "comfort food",
        "brunch": "brunch",
        "bbq": "barbecue",
        "coffee": "cafe",
    },
    "dietary_restrictions": {
        "vegan": "vegan",
        "vegetarian": "vegetarian",
        "gluten": "gluten_free",
        "halal": "halal",
        "kosher": "kosher",
        "dairy": "dairy_free",
    },
}

BUDGET_HINTS = {
    "cheap": "$",
    "budget": "$",
    "affordable": "$$",
    "moderate": "$$",
    "nice": "$$$",
    "fancy": "$$$$",
    "luxury": "$$$$",
}


@dataclass
class RankedCard:
    card: Hangout
    score: int
    reason: str


def parse_natural_language_preset(text: str) -> PresetParseResponse:
    lower = text.lower().strip()
    criteria = PresetCriteria()

    for key, mapping in KEYWORDS.items():
        values: list[str] = []
        for needle, normalized in mapping.items():
            if needle in lower and normalized not in values:
                values.append(normalized)
        setattr(criteria, key, values)

    for needle, tier in BUDGET_HINTS.items():
        if needle in lower:
            criteria.budget_max = tier
            break

    negatives = re.findall(r"(?:no|avoid|not)\s+([a-zA-Z\s]{3,30})", lower)
    criteria.dealbreakers = [n.strip() for n in negatives if n.strip()]

    tokens = [t for t in re.split(r"[^a-zA-Z]+", lower) if t]
    suggested_name = " ".join(tokens[:4]).title() or "Custom preset"
    suggested_description = text.strip()[:180]

    non_empty = sum(bool(getattr(criteria, field)) for field in [
        "cuisine_preferences", "activity_preferences", "dietary_restrictions", "dealbreakers",
    ]) + (1 if criteria.budget_max else 0)
    confidence = min(0.95, 0.35 + 0.12 * non_empty)

    return PresetParseResponse(
        name_suggestion=suggested_name,
        description_suggestion=suggested_description,
        criteria=criteria,
        confidence=confidence,
    )


def rank_hangouts_for_preset(cards: list[Hangout], criteria: PresetCriteria) -> list[RankedCard]:
    ranked: list[RankedCard] = []

    for card in cards:
        haystack = " ".join([
            card.title.lower(),
            (card.description or "").lower(),
            " ".join(t.lower() for t in card.tags),
        ])
        score = 0
        reasons: list[str] = []

        for keyword in criteria.activity_preferences:
            if keyword in haystack:
                score += 4
                reasons.append(f"matches activity '{keyword}'")

        for keyword in criteria.cuisine_preferences:
            if keyword in haystack:
                score += 3
                reasons.append(f"matches cuisine '{keyword}'")

        for blocked in criteria.dealbreakers:
            if blocked and blocked in haystack:
                score -= 5
                reasons.append(f"contains dealbreaker '{blocked}'")

        if not reasons:
            reasons = ["general relevance"]

        ranked.append(RankedCard(card=card, score=score, reason="; ".join(reasons[:2])))

    ranked.sort(key=lambda x: x.score, reverse=True)
    return ranked
