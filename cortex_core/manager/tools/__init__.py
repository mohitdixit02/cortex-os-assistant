from enum import Enum
from .WebSearchTool import WebSearchTool, WebSearchInput
from .TaskRetrieverTool import TaskRetrieverTool, TaskRetrieverInput, TaskRetrieverResult
from .EventTool import EventTool, EventToolInput

class AvailableToolsType(str, Enum):
    WEB_SEARCH_TOOL = "web_search_01"
    TASK_RETRIEVER_TOOL = "task_retriever_02"
    EVENT_TOOL = "event_tool_03"

AVAILABLE_TOOLS = [
    {
        "tool_id": AvailableToolsType.WEB_SEARCH_TOOL.value,
        "tool_name": WebSearchTool.__name__,
        "tool_description": WebSearchTool.__doc__,
    },
    {
        "tool_id": AvailableToolsType.TASK_RETRIEVER_TOOL.value,
        "tool_name": TaskRetrieverTool.__name__,
        "tool_description": TaskRetrieverTool.__doc__,
    },
    {
        "tool_id": AvailableToolsType.EVENT_TOOL.value,
        "tool_name": EventTool.__name__,
        "tool_description": EventTool.__doc__,
    },
]

__all__ = [
    "AVAILABLE_TOOLS",
    "AvailableToolsType",
    "WebSearchTool",
    "WebSearchInput",
    "EventTool",
    "EventToolInput",
    "TaskRetrieverTool",
    "TaskRetrieverInput",
    "TaskRetrieverResult",
]
