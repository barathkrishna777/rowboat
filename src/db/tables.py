"""SQLAlchemy table definitions."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=True, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    auth_provider = Column(String, nullable=True)  # "email" | "google"
    google_id = Column(String, nullable=True, unique=True, index=True)
    google_calendar_token = Column(Text, nullable=True)  # JSON string
    preferences = Column(Text, nullable=True)  # JSON string
    profile = Column(Text, nullable=True)  # JSON string (UserProfile)
    availability = Column(Text, nullable=True)  # JSON string (UserAvailability)
    created_at = Column(DateTime, default=datetime.now)


class GroupTable(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    members = relationship("GroupMemberTable", back_populates="group")


class GroupMemberTable(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.now)

    group = relationship("GroupTable", back_populates="members")


class EventTable(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    itinerary = Column(Text, nullable=True)  # JSON string
    status = Column(String, default="proposed")
    created_at = Column(DateTime, default=datetime.now)


class FriendshipTable(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requester_id = Column(String, ForeignKey("users.id"), nullable=False)
    addressee_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending | accepted | declined
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FeedbackTable(Base):
    __tablename__ = "feedback"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    overall_rating = Column(Integer, nullable=False)
    venue_ratings = Column(Text, nullable=True)  # JSON string
    would_repeat = Column(Integer, default=0)  # SQLite boolean
    free_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


# ── Hangouts + Swipe + Matching ────────────────────────────────────────


class HangoutTable(Base):
    """A discoverable hangout proposal — the card users swipe on."""
    __tablename__ = "hangouts"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    time_window = Column(Text, nullable=True)  # JSON: {"start": iso, "end": iso}
    location_area = Column(String, nullable=True)
    tags = Column(Text, nullable=True)  # JSON list of strings
    source = Column(String, default="user_created")  # ai_suggested | user_created | template
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class SwipeTable(Base):
    """A user's swipe (pass/interested) on a hangout card. Idempotent."""
    __tablename__ = "swipes"
    __table_args__ = (
        UniqueConstraint("user_id", "hangout_id", name="uq_swipe_user_hangout"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    hangout_id = Column(String, ForeignKey("hangouts.id"), nullable=False)
    action = Column(String, nullable=False)  # "pass" | "interested"
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SuggestedMatchTable(Base):
    """A suggested group formed by the matching engine."""
    __tablename__ = "suggested_matches"

    id = Column(String, primary_key=True)
    hangout_id = Column(String, ForeignKey("hangouts.id"), nullable=False)
    member_user_ids = Column(Text, nullable=False)  # JSON list of user IDs
    score = Column(Integer, default=0)  # match quality 0-100
    status = Column(String, default="pending")  # pending | accepted | dismissed
    group_id = Column(String, ForeignKey("groups.id"), nullable=True)  # set after "Plan this outing"
    created_at = Column(DateTime, default=datetime.now)
