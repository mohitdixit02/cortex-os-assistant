from pydantic import BaseModel, Field, RootModel
from typing import Any, Optional, Annotated
from enum import Enum
from cortex_cm.pg.enums import TimeOfDay, PreferenceLevel, RoleType, AIClientType
from datetime import datetime
from cortex_cm.utility.time_utils import UTC_NOW
"""
    Reducers
"""
def merge_orchestration_state(current, incoming):
    """Merge orchestration updates from parallel branches without overwriting untouched fields."""
    if incoming is None:
        return current
    if current is None:
        return incoming
    current_data = current.model_dump(exclude_unset=True)
    incoming_data = incoming.model_dump(exclude_unset=True)
    merged = {**current_data, **incoming_data}
    return OrchestrationState(**merged)

def merge_plan_feedback(current, incoming):
    """Merge plan feedback by applying only explicitly-set incoming fields."""
    if incoming is None:
        return current
    if current is None:
        return incoming

    current_data = current.model_dump()
    incoming_data = incoming.model_dump()
    explicit_fields = getattr(incoming, "model_fields_set", set())

    for key in explicit_fields:
        current_data[key] = incoming_data[key]

    # iteration_count should change only when explicitly set by the aggregator.
    if "iteration_count" in explicit_fields:
        current_data["iteration_count"] = incoming_data["iteration_count"]
    else:
        current_data["iteration_count"] = current.iteration_count

    return PlanEvaluationState(**current_data)

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
    trait_id: str
    strictness: PreferenceLevel
    content: str
    score: Optional[float] = None

class UserSTM(BaseModel):
    """Short Term Memory (STM) for the user based on the conversation context and recent interactions."""
    stm_summary: str
    session_preferences: Optional[dict[str, Any]] = None
    recent_conversation: Optional[str] = None

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
    is_summarized: Optional[bool] = None
    tool_id: Optional[str] = None
    embedding: Optional[list[float]] = None

class MessageStateList(RootModel[list[MessageState]]):
    """Root model for a list of message states."""
    pass


"""
    Orchestration State Models
"""
class CortexTool(BaseModel):
    """Represents a tool that can be used by the Cortex Main Client to process user queries and generate responses."""
    tool_id: str
    instructions: Optional[str] = None
    tool_result: Optional[Any] = None
    tool_exec_status: Optional[str] = None

class CortexToolList(RootModel[list[CortexTool]]):
    """Root model for a list of Cortex tools."""
    pass

class PlanEvaluationState(BaseModel):
    """Represents the state of Plan evaluation done by Evaluator over Orchestrator's plan"""
    is_knowledge_feedback_required: Annotated[bool, Field(description="Whether user feedback is required for the knowledge retrieval part of the plan or not")] = False
    is_message_feedback_required: Annotated[bool, Field(description="Whether user feedback is required for the message retrieval part of the plan or not")] = False
    is_tool_selection_feedback_required: Annotated[bool, Field(description="Whether user feedback is required for the tool selection part of the plan or not")] = False
    user_knowledge_retrieval_feedback: Annotated[Optional[str], Field(description="Feedback on the user knowledge retrieval part of the plan")] = None
    message_retrieval_feedback: Annotated[Optional[str], Field(description="Feedback on the message retrieval part of the plan")] = None
    tool_selection_feedback: Annotated[Optional[str], Field(description="Feedback on the tool selection part of the plan")] = None
    iteration_count: Annotated[Optional[int], Field(description="Number of iterations or attempts made to generate the response")] = 0

class OrchestrationState(BaseModel):
    """
    Represents the overall `orchestration state` decided by the `Orchestartor` based on the user query and context. \n
    Includes: \n
    - User knowledge retrieval state
    - Message retrieval state
    - Tool selection state
    """
    user_knowledge_retrieval_keywords: Annotated[list[str], Field(description="List of keywords relevant enough to retrieve user knowledge base for the current query")] = []
    is_message_referred: Annotated[bool, Field(description="Whether the user query is referring to any past message in the conversation or not")] = False
    referred_message_keywords: Annotated[Optional[str], Field(description="Keywords from the referred message")] = None
    is_tool_required: Annotated[bool, Field(description="Whether any tool is required to process the user query or not")] = False
    selected_tools: Annotated[Optional[CortexToolList], Field(description="List of selected tools")] = None
    user_knowledge_acceptance_threshold: Annotated[float, Field(le=0.6, ge=0.2, description="Similarity threshold for accepting user knowledge items retrieved based on the keywords")] = 0.35
    
class FinalResponseGenerationState(BaseModel):
    """Represents the state of final response generation done by Response Generator based on the orchestration plan and evaluation"""
    reasoning: Annotated[Optional[str], Field(description="Reasoning for how you generate the response based on the provided context. Not more than 100 words.")] = None
    response: Annotated[Optional[str], Field(description="The final response generated for the user query")] = None

class FinalResponseFeedbackState(BaseModel):
    """Represents the state of final response evaluation done by Evaluator based on user feedback"""
    reasoning: Annotated[Optional[str], Field(description="Reasoning for how you approach at this evaluation. Not more than 100 words.")] = None
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
    user_id: str
    session_id: str
    task_id: str
    query: str
    user_message_id: Optional[str] = None
    user_timezone: Optional[str] = "UTC"
    voice_client_response: Optional[str] = None
    query_emotion: Optional[str] = None
    query_timestamp: datetime = Field(default_factory=UTC_NOW)
    query_time: Optional[TimeOfDay] = None
    emotional_profile: Optional[EmotionalProfile] = None
    short_term_memory: Optional[UserSTM] = None
    knowledge_base: Optional[list[UserKnowledge]] = None
    message_history: Optional[MessageStateList] = None
    orchestration_state: Annotated[Optional[OrchestrationState], merge_orchestration_state] = None
    plan_feedback: Annotated[Optional[PlanEvaluationState], merge_plan_feedback] = None
    final_response: Optional[FinalResponseGenerationState] = None
    final_response_feedback: Optional[FinalResponseFeedbackState] = None

__all__ = [
    "EmotionalProfile",
    "UserKnowledge",
    "UserSTM",
    "MessageState",
    "MessageStateList",
    "CortexTool",
    "CortexToolList",
    "PlanEvaluationState",
    "OrchestrationState",
    "FinalResponseGenerationState",
    "FinalResponseFeedbackState",
    "ConversationState",
]