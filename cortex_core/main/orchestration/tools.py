from cortex_core.graph.state import (
    ConversationState,
    CortexToolList, 
    CortexTool,
    ToolManagerState,
    ToolExecutionState
)
from cortex_core.manager.tools import AvailableToolsType
from cortex_core.graph.manager import tool_manager_workflow
from cortex_cm.utility.logger import get_logger

class ToolsOrchestrator:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")

    def execute_tools(
        self,
        state: ConversationState,
    ):
        orchestration_state = state.orchestration_state
        
        if orchestration_state is None:
            self.logger.warning("No orchestration state found in the conversation state. Skipping tool execution.")
            return {}
    
        if orchestration_state.is_tool_required is False:
            self.logger.info("No tool is required for the current query as per the orchestration state. Skipping tool execution.")
            return {}
        
        selected_tools = orchestration_state.selected_tools
        selected_tools_list = selected_tools.root if hasattr(selected_tools, "root") else selected_tools
        
        tool_manager_state = ToolManagerState(
            user_id=state.user_id,
            session_id=state.session_id,
            task_id=state.task_id,
            user_timezone=state.user_timezone,
            message_id=state.user_message_id if state.user_message_id else None,
            query=state.query,
        )
        
        for tool in selected_tools_list:
            if isinstance(tool, CortexTool):
                if tool.tool_id == AvailableToolsType.WEB_SEARCH_TOOL.value:
                    tool_manager_state.web_search_tool = ToolExecutionState(
                        instructions=tool.instructions,
                    )
                if tool.tool_id == AvailableToolsType.TASK_RETRIEVER_TOOL.value:
                    tool_manager_state.task_retriever_tool = ToolExecutionState(
                        instructions=tool.instructions,
                    )
                if tool.tool_id == AvailableToolsType.EVENT_TOOL.value:
                    tool_manager_state.event_tool = ToolExecutionState(
                        instructions=tool.instructions,
                    )
            else:
                self.logger.warning(f"Invalid tool format: {tool}. Skipping this tool.")
        
        #  manager execute tools workflow
        res = tool_manager_workflow.invoke(tool_manager_state)
        res = ToolManagerState.model_validate(res)
        self.logger.info("[ORCHESTRATOR] Tools execution completed with results: %s", res)
        tools_result = []
        if res.web_search_tool:
            tools_result.append(CortexTool(
                tool_id=AvailableToolsType.WEB_SEARCH_TOOL.value,
                instructions=res.web_search_tool.instructions,
                tool_result=res.web_search_tool.tool_result,
                tool_exec_status=res.web_search_tool.tool_exec_status
            ))
        if res.task_retriever_tool:
            tools_result.append(CortexTool(
                tool_id=AvailableToolsType.TASK_RETRIEVER_TOOL.value,
                instructions=res.task_retriever_tool.instructions,
                tool_result=res.task_retriever_tool.tool_result,
                tool_exec_status=res.task_retriever_tool.tool_exec_status
            ))
        if res.event_tool:
            tools_result.append(CortexTool(
                tool_id=AvailableToolsType.EVENT_TOOL.value,
                instructions=res.event_tool.instructions,
                tool_result=res.event_tool.tool_result,
                tool_exec_status=res.event_tool.tool_exec_status
            ))
            
        orchestration_state.selected_tools = CortexToolList(root=tools_result)
        return {
            "orchestration_state": orchestration_state,
        }

__all__ = [
    "ToolsOrchestrator"
]