from sqlmodel import create_engine, Session
from utility.config import env

from .enums import (
    AIClientType,
    PreferenceLevel,
    RoleType,
    TaskStatus,
    TimeOfDay,
)
from .models import (
    ChatSession,
    Message,
    Task,
    Tool,
    User,
    UserEmotionalProfile,
    UserKnowledgeBase,
    UserShortTermMemory,
    UserToolSubscription,
)

engine = create_engine(env.DB_URL, echo=False)

__all__ = [
    "RoleType",
    "AIClientType",
    "PreferenceLevel",
    "TimeOfDay",
    "TaskStatus",
    "User",
    "ChatSession",
    "Message",
    "UserShortTermMemory",
    "UserEmotionalProfile",
    "UserKnowledgeBase",
    "Tool",
    "Task",
    "UserToolSubscription",
    "engine",
]
