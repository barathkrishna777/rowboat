"""Preference Agent — conducts an adaptive quiz to build user preference profiles."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from src.config import settings
from src.models.user import BudgetTier, DietaryRestriction, UserPreferences


class QuizQuestion(BaseModel):
    """A single question in the adaptive preference quiz."""

    question: str
    options: list[str] = Field(default_factory=list, description="Suggested options (user can also free-text)")
    category: str = Field(description="Which preference area this covers")
    follow_up: bool = Field(default=False, description="Whether this is a follow-up to a prior answer")


class QuizState(BaseModel):
    """Tracks the state of an ongoing quiz session."""

    user_id: str
    questions_asked: list[QuizQuestion] = Field(default_factory=list)
    answers: dict[str, str] = Field(default_factory=dict)
    completed: bool = False
    extracted_preferences: UserPreferences | None = None


class PreferenceExtractionResult(BaseModel):
    """Structured output from the Preference Agent."""

    preferences: UserPreferences
    confidence: float = Field(ge=0.0, le=1.0, description="How confident the agent is in the extraction")
    missing_areas: list[str] = Field(default_factory=list, description="Preference areas not yet covered")
    summary: str = ""


@dataclass
class PreferenceDeps:
    """Dependencies for the preference agent."""

    user_id: str = ""
    quiz_state: QuizState | None = None


SYSTEM_PROMPT = """\
You are a friendly preference quiz conductor for a group outing planner.
Your job is to learn a user's preferences for group activities through conversation.

You need to understand their preferences across these areas:
1. **Food/Cuisine**: What cuisines do they enjoy? Any favorites?
2. **Activities**: What do they like to do for fun? (bowling, concerts, escape rooms, etc.)
3. **Dietary Restrictions**: Any allergies or dietary needs?
4. **Budget**: How much are they comfortable spending per person?
5. **Dealbreakers**: Anything they absolutely won't do or can't tolerate?
6. **Neighborhoods**: Preferred areas/neighborhoods in the city?
7. **Accessibility**: Any accessibility requirements?
8. **Group Size**: What group size are they comfortable with?

Be conversational and adaptive:
- If they mention being vegetarian, ask about vegan vs lacto-ovo
- If they say "any budget", skip budget drill-down
- If they mention a food allergy, probe for severity
- Prioritize the most impactful questions first (dietary, budget, dealbreakers)

Use the tools to generate questions and extract preferences from the conversation.
"""


# ── Standalone tool functions (registered on lazy agent) ───────────────

async def _generate_next_question(
    ctx: RunContext[PreferenceDeps],
    category: str,
    context: str = "",
) -> dict:
    """Generate the next quiz question based on what we've learned so far.

    Args:
        category: Which area to ask about — one of: cuisine, activities, dietary, budget, dealbreakers, neighborhoods, accessibility, group_size.
        context: Any context from prior answers that should inform this question.
    """
    question_templates = {
        "cuisine": QuizQuestion(
            question="What types of food do you enjoy? Pick your favorites or tell us in your own words!",
            options=["Italian", "Japanese", "Mexican", "Indian", "Thai", "Korean", "Chinese", "American", "Mediterranean"],
            category="cuisine",
        ),
        "activities": QuizQuestion(
            question="What activities do you enjoy doing with friends?",
            options=["Bowling", "Escape Room", "Concert", "Movie", "Hiking", "Karaoke", "Board Games", "Museum", "Comedy Show"],
            category="activities",
        ),
        "dietary": QuizQuestion(
            question="Do you have any dietary restrictions or food allergies?",
            options=["None", "Vegetarian", "Vegan", "Gluten Free", "Halal", "Kosher", "Nut Allergy", "Dairy Free"],
            category="dietary",
        ),
        "budget": QuizQuestion(
            question="What's your comfortable budget per person for an outing?",
            options=["Under $15", "$15-40", "$40-80", "$80+"],
            category="budget",
        ),
        "dealbreakers": QuizQuestion(
            question="Is there anything you absolutely don't want for an outing? (e.g., 'no loud places', 'no smoking areas')",
            options=[],
            category="dealbreakers",
        ),
        "neighborhoods": QuizQuestion(
            question="Are there any neighborhoods or areas you prefer?",
            options=[],
            category="neighborhoods",
        ),
        "accessibility": QuizQuestion(
            question="Do you have any accessibility needs we should consider?",
            options=["None", "Wheelchair accessible", "Elevator access", "Hearing assistance"],
            category="accessibility",
        ),
        "group_size": QuizQuestion(
            question="What group size are you most comfortable with?",
            options=["2-4 people", "4-6 people", "6-10 people", "10+ people"],
            category="group_size",
        ),
    }

    q = question_templates.get(category)
    if q:
        if context:
            q.follow_up = True
            q.question = f"Based on what you told us ({context}), {q.question.lower()}"
        return q.model_dump()

    return QuizQuestion(
        question=f"Tell us about your {category} preferences.",
        category=category,
    ).model_dump()


async def _extract_preferences_from_answers(
    ctx: RunContext[PreferenceDeps],
    cuisine_preferences: list[str],
    activity_preferences: list[str],
    dietary_restrictions: list[str],
    budget_level: str,
    dealbreakers: list[str],
    preferred_neighborhoods: list[str],
    accessibility_needs: list[str],
    group_size_min: int = 2,
    group_size_max: int = 10,
) -> dict:
    """Extract structured preferences from the user's quiz answers.

    Args:
        cuisine_preferences: List of preferred cuisines (e.g., ["italian", "japanese"]).
        activity_preferences: List of preferred activities (e.g., ["bowling", "concert"]).
        dietary_restrictions: List of dietary restrictions (e.g., ["vegetarian", "nut_allergy"]).
        budget_level: Budget tier — one of "$", "$$", "$$$", "$$$$".
        dealbreakers: List of dealbreakers (e.g., ["no loud places"]).
        preferred_neighborhoods: List of preferred neighborhoods.
        accessibility_needs: List of accessibility needs.
        group_size_min: Minimum comfortable group size.
        group_size_max: Maximum comfortable group size.
    """
    dietary_map = {
        "none": DietaryRestriction.NONE,
        "vegetarian": DietaryRestriction.VEGETARIAN,
        "vegan": DietaryRestriction.VEGAN,
        "gluten_free": DietaryRestriction.GLUTEN_FREE,
        "gluten free": DietaryRestriction.GLUTEN_FREE,
        "halal": DietaryRestriction.HALAL,
        "kosher": DietaryRestriction.KOSHER,
        "nut_allergy": DietaryRestriction.NUT_ALLERGY,
        "nut allergy": DietaryRestriction.NUT_ALLERGY,
        "dairy_free": DietaryRestriction.DAIRY_FREE,
        "dairy free": DietaryRestriction.DAIRY_FREE,
        "shellfish_allergy": DietaryRestriction.SHELLFISH_ALLERGY,
        "shellfish allergy": DietaryRestriction.SHELLFISH_ALLERGY,
    }
    budget_map = {"$": BudgetTier.LOW, "$$": BudgetTier.MEDIUM, "$$$": BudgetTier.HIGH, "$$$$": BudgetTier.LUXURY}

    prefs = UserPreferences(
        cuisine_preferences=[c.lower().strip() for c in cuisine_preferences],
        activity_preferences=[a.lower().strip() for a in activity_preferences],
        dietary_restrictions=[
            dietary_map[d.lower().strip()]
            for d in dietary_restrictions
            if d.lower().strip() in dietary_map and d.lower().strip() != "none"
        ],
        budget_max=budget_map.get(budget_level, BudgetTier.MEDIUM),
        dealbreakers=dealbreakers,
        preferred_neighborhoods=preferred_neighborhoods,
        accessibility_needs=accessibility_needs,
        group_size_comfort=(group_size_min, group_size_max),
    )

    return prefs.model_dump()


# ── Lazy agent initialization ─────────────────────────────────────────

_preference_agent: Agent | None = None


def get_preference_agent() -> Agent:
    """Lazy-initialize the preference agent (defers API key validation)."""
    global _preference_agent
    if _preference_agent is None:
        _preference_agent = Agent(
            settings.primary_model,
            output_type=PreferenceExtractionResult,
            deps_type=PreferenceDeps,
            system_prompt=SYSTEM_PROMPT,
        )
        _preference_agent.tool(_generate_next_question)
        _preference_agent.tool(_extract_preferences_from_answers)
    return _preference_agent


async def run_preference_quiz(user_id: str, answers_text: str) -> PreferenceExtractionResult:
    """Run the preference agent to extract preferences from free-text answers.

    Args:
        user_id: The user's ID.
        answers_text: Free-text description of the user's preferences,
                      or structured answers from the quiz UI.
    """
    agent = get_preference_agent()
    deps = PreferenceDeps(user_id=user_id)
    prompt = (
        f"The user (ID: {user_id}) has provided the following information about their preferences:\n\n"
        f"{answers_text}\n\n"
        "Please extract their structured preferences using the extract_preferences_from_answers tool. "
        "If any information is missing, note it in missing_areas."
    )
    result = await agent.run(prompt, deps=deps)
    return result.output
