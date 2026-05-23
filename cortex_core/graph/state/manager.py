from pydantic import BaseModel
from typing import Optional

"""
    Manager State Models
"""
class ToolExecutionState(BaseModel):
    """Represents the execution state of a tool, including its instructions, result, and status."""
    instructions: Optional[str] = None
    tool_result: Optional[str] = None
    tool_exec_status: Optional[str] = None

class ToolManagerState(BaseModel):
    user_id: str
    session_id: str
    task_id: str
    user_timezone: Optional[str] = "UTC"
    message_id: Optional[str] = None
    query: str
    web_search_tool: Optional[ToolExecutionState] = None
    task_retriever_tool: Optional[ToolExecutionState] = None
    event_tool: Optional[ToolExecutionState] = None

__all__ = [
    "ToolExecutionState",
    "ToolManagerState"
]