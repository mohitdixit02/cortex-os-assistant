from pydantic import BaseModel, Field, RootModel
from typing import Literal, Optional, Annotated
from cortex_cm.pg.enums import TimeOfDay, PreferenceLevel
from datetime import datetime
from .main import UserSTM, OrchestrationState, UserKnowledge

"""
    Memory State Models
"""
class MemoryEmotionalProfile(BaseModel):
    """Represents the user's emotional profile stored in memory for long-term personalization."""
    emotional_level: Annotated[int, Field(ge=0, le=10)]
    logical_level: Annotated[int, Field(ge=0, le=10)]
    social_level: Annotated[int, Field(ge=0, le=10)]
    context_summary: str

class MemoryUserKnowledge(BaseModel):
    """Represents a piece of user knowledge stored in memory for long-term personalization."""
    action: Annotated[Literal["add", "update"], Field(description="Action to be taken for this knowledge item based on its relevance and importance")]
    trait_id: Optional[str] = Field(default=None, description="Trait id of the user knowledge, required if action is update")
    strictness: Annotated[PreferenceLevel, Field(description="Strictness level of the user knowledge")] = None
    content: Annotated[str, Field(description="Detailed information about the user preference, habit, or fact that can be useful for response generation. Be specific and concise in describing it. If it's a fact, provide clear and relevant information about the user.")]

class MemoryUserKnowledgeList(RootModel[list[MemoryUserKnowledge]]):
    """Root model for a list of long-term memory knowledge items."""
    pass

class MemoryState(BaseModel):
    """Represents the overall memory state for a user, including emotional profile and knowledge items."""
    user_id: str
    session_id: str
    user_timezone: Optional[str] = "UTC"
    query: str
    ai_response: str
    query_emotion: Optional[str] = None
    query_time: Optional[TimeOfDay] = None
    short_term_memory: Optional[UserSTM] = None
    emotional_profile: Optional[MemoryEmotionalProfile] = None
    knowledge_items: Optional[MemoryUserKnowledgeList] = None
    older_knowledge_base: Optional[list[UserKnowledge]] = None
    orchestration_state: Optional[OrchestrationState] = None
    stm_start_update_timestamp: Optional[datetime] = None
    stm_end_update_timestamp: Optional[datetime] = None

__all__ = [
    "MemoryState",
    "MemoryEmotionalProfile",
    "MemoryUserKnowledge",
    "MemoryUserKnowledgeList"
]