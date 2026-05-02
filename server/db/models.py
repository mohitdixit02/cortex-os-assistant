from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlmodel import Field, Relationship, SQLModel

from db.enums import (
    AIClientType,
    PreferenceLevel,
    RoleType,
    TaskStatus,
    TimeOfDay,
)


UTC_NOW = lambda: datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    user_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    google_id: str = Field(sa_column=Column(String(255), unique=True, index=True, nullable=False))
    email: str = Field(sa_column=Column(String(320), unique=True, index=True, nullable=False))
    full_name: str = Field(sa_column=Column(String(255), nullable=False))
    phone_number: Optional[str] = Field(default=None, sa_column=Column(String(32), nullable=True))
    profile_picture: Optional[str] = Field(default=None, sa_column=Column(String(1024), nullable=True))
    google_refresh_token: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True)) # Store encrypted
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    messages: List["Message"] = Relationship(back_populates="user")
    short_term_memories: List["UserShortTermMemory"] = Relationship(back_populates="user")
    emotional_profiles: List["UserEmotionalProfile"] = Relationship(back_populates="user")
    knowledge_traits: List["UserKnowledgeBase"] = Relationship(back_populates="user")
    tool_subscriptions: List["UserToolSubscription"] = Relationship(back_populates="user")


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    session_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    user_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    summary: Optional[str] = Field(default=None, sa_column=Column(String(2000), nullable=True))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))

    user: "User" = Relationship(back_populates="chat_sessions")
    messages: List["Message"] = Relationship(back_populates="session")
    short_term_memories: List["UserShortTermMemory"] = Relationship(back_populates="session")
    emotional_profiles: List["UserEmotionalProfile"] = Relationship(back_populates="session")


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    message_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    session_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    user_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    content: str = Field(sa_column=Column(Text, nullable=False))
    role: RoleType = Field(sa_column=Column(SAEnum(RoleType, name="role_type"), nullable=False, index=True))
    ai_client: Optional[AIClientType] = Field(
        default=None,
        sa_column=Column(SAEnum(AIClientType, name="ai_client_type"), nullable=True, index=True),
    )
    is_tool_used: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False))
    is_summarized: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False, index=True))
    tool_id: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(), nullable=True))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))

    session: "ChatSession" = Relationship(back_populates="messages")
    user: "User" = Relationship(back_populates="messages")
    tasks: List["Task"] = Relationship(back_populates="message")


class UserShortTermMemory(SQLModel, table=True):
    __tablename__ = "user_short_term_memory"

    stm_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    user_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    session_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    stm_summary: str = Field(sa_column=Column(Text, nullable=False))
    session_preferences: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))

    user: "User" = Relationship(back_populates="short_term_memories")
    session: "ChatSession" = Relationship(back_populates="short_term_memories")


class UserEmotionalProfile(SQLModel, table=True):
    __tablename__ = "user_emotional_profiles"

    __table_args__ = (
        CheckConstraint("emotional_level >= 1 AND emotional_level <= 10", name="ck_emotional_level_1_10"),
        CheckConstraint("logical_level >= 1 AND logical_level <= 10", name="ck_logical_level_1_10"),
        CheckConstraint("social_level >= 1 AND social_level <= 10", name="ck_social_level_1_10"),
    )

    profile_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    user_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    session_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    mood_type: str = Field(sa_column=Column(String(64), nullable=False))
    time_behavior: TimeOfDay = Field(sa_column=Column(SAEnum(TimeOfDay, name="time_of_day"), nullable=False))
    emotional_level: int = Field(sa_column=Column(nullable=False))
    logical_level: int = Field(sa_column=Column(nullable=False))
    social_level: int = Field(sa_column=Column(nullable=False))
    context_summary: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))

    user: "User" = Relationship(back_populates="emotional_profiles")
    session: "ChatSession" = Relationship(back_populates="emotional_profiles")


class UserKnowledgeBase(SQLModel, table=True):
    __tablename__ = "user_knowledge_base"

    trait_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    user_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    strictness: Optional[PreferenceLevel] = Field(
        default=None,
        sa_column=Column(SAEnum(PreferenceLevel, name="preference_level"), nullable=True, index=True),
    )
    content: str = Field(sa_column=Column(Text, nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True, index=True))
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(), nullable=True))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))

    user: "User" = Relationship(back_populates="knowledge_traits")

class UserToolSubscription(SQLModel, table=True):
    __tablename__ = "user_tool_subscriptions"

    user_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )
    tool_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("tools.tool_id", ondelete="CASCADE"), primary_key=True, nullable=False)
    )
    is_subscribed: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))

    user: "User" = Relationship(back_populates="tool_subscriptions")
    tool: "Tool" = Relationship(back_populates="user_subscriptions")


class Tool(SQLModel, table=True):
    __tablename__ = "tools"

    tool_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    tool_name: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    tool_description: str = Field(sa_column=Column(Text, nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, default=True, index=True))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    tasks: List["Task"] = Relationship(back_populates="tool")
    user_subscriptions: List["UserToolSubscription"] = Relationship(back_populates="tool")


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    task_id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    message_id: UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("messages.message_id", ondelete="CASCADE"), nullable=False, index=True)
    )
    tool_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("tools.tool_id", ondelete="RESTRICT"), nullable=True, index=True)
    )
    task_name: str = Field(sa_column=Column(String(255), nullable=False))
    task_description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    status: TaskStatus = Field(sa_column=Column(SAEnum(TaskStatus, name="task_status"), nullable=False, index=True))
    payload: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    status_response: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    task_metadata: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    embedding: Optional[list[float]] = Field(default=None, sa_column=Column(Vector(), nullable=True))
    created_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=UTC_NOW, sa_column=Column(DateTime(timezone=True), nullable=False))

    message: "Message" = Relationship(back_populates="tasks")
    tool: Optional["Tool"] = Relationship(back_populates="tasks")


Index("ix_messages_session_created", Message.__table__.c.session_id, Message.__table__.c.created_at)
Index("ix_tasks_status_updated", Task.__table__.c.status, Task.__table__.c.updated_at)
