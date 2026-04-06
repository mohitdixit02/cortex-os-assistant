from pydantic import BaseModel, Field, RootModel
from typing import Any, Dict, Literal, Optional, Annotated
from enum import Enum
from db.enums import TimeOfDay, PreferenceLevel, RoleType, AIClientType
from datetime import datetime, timezone

UTC_NOW = lambda: datetime.now(timezone.utc)

def prefer_latest_non_none(current, incoming):
    """Reducer for LangGraph concurrent updates: keep newest non-None value."""
    return incoming if incoming is not None else current

"""
    Conversation State Models
"""                           
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
    
class MessageState(BaseModel):
    """Represents the state of a single message in the conversation"""
    message_id: str
    session_id: str
    user_id: str
    content: str
    role: RoleType
    ai_client: Optional[AIClientType] = None
    is_tool_used: Optional[bool] = None
    tool_id: Optional[str] = None
    embedding: Optional[list[float]] = None

class MessageStateList(RootModel[list[MessageState]]):
    """Root model for a list of message states."""
    pass
    

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
    query: str
    ai_response: str
    query_emotion: Optional[str] = None
    query_time: Optional[TimeOfDay] = None
    short_term_memory: Optional[UserSTM] = None
    emotional_profile: Optional[MemoryEmotionalProfile] = None
    knowledge_items: Optional[MemoryUserKnowledgeList] = None
    older_knowledge_base: Optional[list[UserKnowledge]] = None
    

"""
    Orchestration State Models
"""
# class UserKnowledgeRetrievalState(BaseModel):
#     """Represents the state of user knowledge retrieval process  decided by the Orchestartor based on the user query and context."""
#     selected_categories: Annotated[list[TraitCategory], Field(description="List of categories for which to retrieve knowledge")]

# class MessageRetrievalState(BaseModel):
#     """Represents the state of message retrieval process decided by the Orchestartor based on the user query and context."""
#     is_referred: Annotated[bool, Field(description="Whether the user query is referring to any past message in the conversation or not")]
#     referred_message_keywords: Annotated[Optional[str], Field(description="Keywords from the referred message")] = None

class CortexTool(BaseModel):
    """Represents a tool that can be used by the Cortex Main Client to process user queries and generate responses."""
    tool_id: str
    tool_name: str
    tool_description: str
    tool_input_format: Optional[dict[str, Any]] = None
    tool_output_format: Optional[dict[str, Any]] = None

# class ToolSelectionState(BaseModel):
#     """Represents the state of tool selection process decided by the Orchestartor based on the user query and context."""
#     is_tool_required: Annotated[bool, Field(description="Whether any tool is required to process the user query or not")]
#     selected_tools: Annotated[Optional[Dict[str, str]], Field(description="Dict of selected tool Id as keys and one line reason of why it is required as values")] = None

class PlanEvaluationState(BaseModel):
    """Represents the state of Plan evaluation done by Evaluator over Orchestrator's plan"""
    is_feedback_required: Annotated[bool, Field(description="Whether user feedback is required for the current response or plan or not")]
    user_knowledge_retrieval_feedback: Annotated[Optional[str], Field(description="Feedback on the user knowledge retrieval part of the plan")] = None
    message_retrieval_feedback: Annotated[Optional[str], Field(description="Feedback on the message retrieval part of the plan")] = None
    iteration_count: Annotated[Optional[int], Field(description="Number of iterations or attempts made to generate the response")] = 0

class OrchestrationState(BaseModel):
    """
    Represents the overall `orchestration state` decided by the `Orchestartor` based on the user query and context. \n
    Includes: \n
    - User knowledge retrieval state
    - Message retrieval state
    - Tool selection state
    """
    # user_knowledge_retrieval_state: Optional[UserKnowledgeRetrievalState] = None
    # message_retrieval_state: Optional[MessageRetrievalState] = None
    # tool_selection_state: Optional[ToolSelectionState] = None
    # feedback_by_evaluator: Optional[PlanEvaluationState] = None
    user_knowledge_retrieval_keywords: Annotated[list[str], Field(description="List of keywords relevant enough to retrieve user knowledge base for the current query")] = []
    is_message_referred: Annotated[bool, Field(description="Whether the user query is referring to any past message in the conversation or not")]
    referred_message_keywords: Annotated[Optional[str], Field(description="Keywords from the referred message")] = None
    is_tool_required: Annotated[bool, Field(description="Whether any tool is required to process the user query or not")]
    selected_tools: Annotated[Optional[Dict[str, str]], Field(description="Dict of selected tool Id as keys and one line reason of why it is required as values")] = None
    
class FinalResponseGenerationState(BaseModel):
    """Represents the state of final response generation done by Response Generator based on the orchestration plan and evaluation"""
    response: Annotated[Optional[str], Field(description="The final response generated for the user query")] = None

class FinalResponseFeedbackState(BaseModel):
    """Represents the state of final response evaluation done by Evaluator based on user feedback"""
    is_feedback_required: Annotated[bool, Field(description="Whether feedback is required for the current response or not")]
    feedback: Annotated[Optional[list[str]], Field(description="Feedback for the response generator")] = None
    iteration_count: Annotated[Optional[int], Field(description="Number of iterations or attempts made to generate the response")] = 0

"""
    Main Conversation State Model
"""
class ConversationState(BaseModel):
    """
    All relevant information about the user's current state in the conversation \n
    Used for state management in graph workflow
    """
    # Available Before Orchestartor Decision
    user_id: str
    session_id: str
    query: str
    query_emotion: Optional[str] = None
    query_timestamp: datetime = Field(default_factory=UTC_NOW)
    query_time: Optional[TimeOfDay] = None
    emotional_profile: Optional[EmotionalProfile] = None
    short_term_memory: Optional[UserSTM] = None
    knowledge_base: Optional[list[UserKnowledge]] = None
    message_history: Optional[MessageStateList] = None
    orchestration_state: Optional[OrchestrationState] = None
    plan_feedback: Optional[PlanEvaluationState] = None
    final_response: Optional[FinalResponseGenerationState] = None
    final_response_feedback: Optional[FinalResponseFeedbackState] = None
