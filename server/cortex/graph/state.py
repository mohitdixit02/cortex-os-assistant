from pydantic import BaseModel, Field, RootModel
from typing import Any, Optional, Annotated
from enum import Enum
from db.enums import TimeOfDay, TraitCategory, PreferenceLevel
from datetime import datetime, timezone

UTC_NOW = lambda: datetime.now(timezone.utc)

# ******************** Conversation State Models ********************
class EmotionalProfile(BaseModel):
    """Represents the user's emotional state and personality traits that can influence response generation."""
    mood_type: str
    time_behavior: TimeOfDay
    emotional_level: Annotated[int, Field(ge=0, le=10)]
    logical_level: Annotated[int, Field(ge=0, le=10)]
    social_level: Annotated[int, Field(ge=0, le=10)]
    context_summary: str

class UserKnowledge(BaseModel):
    """Represents a piece of knowledge about the user that can be used to personalize responses."""
    category: TraitCategory
    strictness: PreferenceLevel
    content: str
    score: Optional[float] = None

class UserSTM(BaseModel):
    """Short Term Memory (STM) for the user based on the conversation context and recent interactions."""
    stm_summary: str
    session_preferences: Optional[dict[str, Any]] = None

class MessageHistory(BaseModel):
    """Relevant Message History for the current conversation"""
    messages: list[dict[str, str]]

class ConversationState(BaseModel):
    """
    All relevant information about the user's current state in the conversation \n
    Used for state management in graph workflow
    """
    user_id: str
    session_id: str
    query: str
    query_emotion: Optional[str] = None
    query_timestamp: datetime = Field(default_factory=UTC_NOW)
    query_time: Optional[TimeOfDay] = None
    emotional_profile: Optional[EmotionalProfile] = None
    knowledge_base: Optional[list[UserKnowledge]] = None
    short_term_memory: Optional[UserSTM] = None
    message_history: Optional[MessageHistory] = None
    final_response: Optional[str] = None
    
# ******************** Memory State Models ********************
class MemoryEmotionalProfile(BaseModel):
    """Represents the user's emotional profile stored in memory for long-term personalization."""
    emotional_level: Annotated[int, Field(ge=0, le=10)]
    logical_level: Annotated[int, Field(ge=0, le=10)]
    social_level: Annotated[int, Field(ge=0, le=10)]
    context_summary: str

class MemoryUserKnowledge(BaseModel):
    """Represents a piece of user knowledge stored in memory for long-term personalization."""
    category: Annotated[TraitCategory, Field(description="Category of the user knowledge")]
    strictness: Annotated[PreferenceLevel, Field(description="Strictness level of the user knowledge")] = None
    content: Annotated[str, Field(description="Detailed information about the user preference, habit, or fact that can be useful for response generation. Be specific and concise in describing it. If it's a fact, provide clear and relevant information about the user.")]


class MemoryUserKnowledgeList(RootModel[list[MemoryUserKnowledge]]):
    """Root model for a list of long-term memory knowledge items."""
    pass
