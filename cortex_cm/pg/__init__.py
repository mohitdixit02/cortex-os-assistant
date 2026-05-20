from sqlmodel import create_engine, Session
from cortex_cm.utility.config import env

from .enums import (
    AIClientType,
    PreferenceLevel,
    RoleType,
    TaskStatus,
    TimeOfDay,
    TaskOwner,
    EventStatus
)
from .models import (
    ChatSession,
    Message,
    Task,
    User,
    UserEmotionalProfile,
    UserKnowledgeBase,
    UserShortTermMemory,
    UserEvent,
    UserConfig
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
    "Task",
    "engine",
    "TaskOwner",
    "EventStatus",
    "UserEvent",
    "UserConfig"
]
