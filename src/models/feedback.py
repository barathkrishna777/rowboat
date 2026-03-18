from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PostEventFeedback(BaseModel):
    feedback_id: str
    user_id: str
    event_id: str
    overall_rating: int = Field(ge=1, le=5)
    venue_ratings: dict[str, int] = Field(
        default_factory=dict,
        description="Mapping of venue_id to rating (1-5)",
    )
    would_repeat: bool = False
    liked: list[str] = Field(default_factory=list, description="What the user liked")
    disliked: list[str] = Field(default_factory=list, description="What the user disliked")
    free_text: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class FeedbackSummary(BaseModel):
    event_id: str
    avg_rating: float
    total_responses: int
    common_likes: list[str] = Field(default_factory=list)
    common_dislikes: list[str] = Field(default_factory=list)
    repeat_percentage: float = 0.0
