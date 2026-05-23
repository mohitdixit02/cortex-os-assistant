from cortex_core.graph.state import ConversationState
from typing import Optional
import json

def serialize_tool_results(state: ConversationState) -> Optional[str]:
    """Serialize tool results into JSON payload for prompts."""
    orchestration_plan = state.orchestration_state
    if not orchestration_plan or not orchestration_plan.selected_tools:
        return None

    tools_result_list = (
        orchestration_plan.selected_tools.root
        if hasattr(orchestration_plan.selected_tools, "root")
        else orchestration_plan.selected_tools
    )
    if not tools_result_list:
        return None

    serializable_tools = [
        tool.model_dump() if hasattr(tool, "model_dump") else tool
        for tool in tools_result_list
    ]
    return json.dumps(serializable_tools)

__all__ = [
    "serialize_tool_results"
]