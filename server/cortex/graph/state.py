from pydantic import BaseModel, Field
from typing import Optional, Annotated
from db.enums import TimeOfDay, Enum, TraitCategory, PreferenceLevel
from datetime import datetime, timezone

UTC_NOW = lambda: datetime.now(timezone.utc)

# ******************** Conversation State Models ********************
class EmotionalProfile(BaseModel):
    """Represents the user's emotional state and personality traits that can influence response generation."""
    mood_type: str
    time_behavior: Enum[TimeOfDay]
    emotional_level: Annotated[int, Field(ge=0, le=10)]
    logical_level: Annotated[int, Field(ge=0, le=10)]
    social_level: Annotated[int, Field(ge=0, le=10)]
    context_summary: str

class UserKnowledge(BaseModel):
    """Represents a piece of knowledge about the user that can be used to personalize responses."""
    category: TraitCategory
    strictness: Optional[PreferenceLevel] = None
    content: str
    score: Optional[float] = None

class UserSTM(BaseModel):
    """Short Term Memory (STM) for the user based on the conversation context and recent interactions."""
    stm_summary: str
    session_preferences: str

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
    query_time: Optional[Enum[TimeOfDay]] = None
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
    
