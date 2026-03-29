"""Built-in preset catalog."""

from __future__ import annotations

from src.models.preset import Preset, PresetCriteria, PresetSource

BUILT_IN_PRESETS: list[Preset] = [
    Preset(
        id="built-in-party",
        name="Feeling like Partying",
        description="Upbeat nightlife, social venues, and energetic group-friendly options.",
        source=PresetSource.BUILT_IN,
        criteria=PresetCriteria(
            activity_preferences=["nightlife", "karaoke", "comedy"],
            cuisine_preferences=["bar food", "shared plates"],
            budget_max="$$$",
            dealbreakers=["quiet only venues"],
        ),
        is_built_in=True,
    ),
    Preset(
        id="built-in-hike",
        name="In the mood for a hike",
        description="Trails, outdoor activity, and nearby casual food after the walk.",
        source=PresetSource.BUILT_IN,
        criteria=PresetCriteria(
            activity_preferences=["hiking", "outdoors", "walking"],
            cuisine_preferences=["brunch", "cafe"],
            budget_max="$$",
            dealbreakers=["indoor-only"],
        ),
        is_built_in=True,
    ),
    Preset(
        id="built-in-roast",
        name="Sunday roast?",
        description="Slow-paced comfort cuisine with cozy atmosphere and easy conversation.",
        source=PresetSource.BUILT_IN,
        criteria=PresetCriteria(
            activity_preferences=["brunch", "catch-up"],
            cuisine_preferences=["comfort food", "british", "american"],
            budget_max="$$",
            dealbreakers=["too loud"],
        ),
        is_built_in=True,
    ),
]


def get_built_in_preset(preset_id: str) -> Preset | None:
    for preset in BUILT_IN_PRESETS:
        if preset.id == preset_id:
            return preset
    return None
