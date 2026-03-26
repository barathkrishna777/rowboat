"""SQLAlchemy table definitions."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    google_calendar_token = Column(Text, nullable=True)  # JSON string
    preferences = Column(Text, nullable=True)  # JSON string
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
