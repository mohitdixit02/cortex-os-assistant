from sqlmodel import create_engine, Session
from utility.config import env

from .enums import (
    AIClientType,
    PreferenceLevel,
    RoleType,
    TaskStatus,
    TimeOfDay,
    TraitCategory,
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
)

engine = create_engine(env.DB_URL, echo=True)
session = Session(engine)

__all__ = [
    "RoleType",
    "AIClientType",
    "PreferenceLevel",
    "TimeOfDay",
    "TraitCategory",
    "TaskStatus",
    "User",
    "ChatSession",
    "Message",
    "UserShortTermMemory",
    "UserEmotionalProfile",
    "UserKnowledgeBase",
    "Tool",
    "Task",
    "session",
]
