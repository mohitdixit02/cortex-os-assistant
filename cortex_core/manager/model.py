from cortex_core.graph.state import ToolManagerState
from cortex_core.manager.prompts import get_manager_client_prompts, WebQueryPlanResult, TaskPlanResult, EventToolPlanResult
from cortex_cm.utility.logger import get_logger
from cortex_cm.utility.cortex import get_planner_model
from cortex_cm.utility.time_utils import get_local_time
from cortex_cm.utility.time_utils import UTC_NOW
from cortex_cm.utility.main import chunk_to_text

class ManagerModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_MANAGER")
        self.model = get_planner_model()
        
    def get_model(self):
        return self.model
                
    def build_web_search_plan(
        self,
        state: ToolManagerState,
    ) -> WebQueryPlanResult:
        """
        Build the input for web search tool based on the user query and orchestrator instructions using the generation model. \n
        - query: user query for which the web search input is to be generated
        - tool: CortexTool object which may contain instructions from the orchestrator for web search query planning
        
        Returns: WebQueryPlanResult object containing the generated keywords for web search and context to be used for web search query planning.
        """
        formatted_prompt, parser = get_manager_client_prompts(
            type="web_query_planning",
        )
        chain = formatted_prompt | self.model | parser
        
        instructions = state.web_search_tool.instructions if state.web_search_tool.instructions else ""

        res = chain.invoke({
            "user_query": state.query,
            "orchestrator_instructions": instructions
        })
        return res

    def summarize_tool_result(
        self,
        tool_result: str,
        query: str,
        tool_type: str,
    ) -> str:
        """
        Summarize the tool result based on the user query and tool type using the generation model. \n
        - tool_result: The raw result obtained from executing the tool which may contain a large amount of information
        - query: user query for which the tool was executed, to be used as context for summarization
        - tool_type: type of the tool which may be used to condition the summarization (e.g. web search result may be summarized differently than a calculator result)
        
        Returns: A summarized version of the tool result which is concise and relevant to the user query
        """
        formatted_prompt, parser = get_manager_client_prompts(
            type="tool_result_summarization",
            tool_type=tool_type,
        )
        chain = formatted_prompt | self.model | parser
        
        res = chain.invoke({
            "tool_result": tool_result,
            "user_query": query,
            "tool_type": tool_type,
        })
        summary = chunk_to_text(res)
        return summary
    
    def build_task_retrieval_plan(
        self,
        state: ToolManagerState
    ) -> TaskPlanResult:
        """
        Generate a task description based on the user query and orchestrator instructions.
        """
        formatted_prompt, parser = get_manager_client_prompts(
            type="task_retrieval_plan_generation",
        )
        chain = formatted_prompt | self.model | parser

        instructions = state.task_retriever_tool.instructions if state.task_retriever_tool.instructions else ""
        
        timestamp = UTC_NOW()
        user_tz = state.user_timezone or "UTC"
        local_timestamp = get_local_time(timestamp, user_tz).replace(tzinfo=None)

        res = chain.invoke({
            "user_query": state.query,
            "orchestrator_instructions": instructions,
            "current_time": local_timestamp,
        })
        return res

    def build_event_tool_plan(
        self,
        state: ToolManagerState
    ) -> EventToolPlanResult:
        """
        Generate the input for event tool based on the user query and orchestrator instructions. \n
        - query: user query for which the event tool input is to be generated
        - tool: CortexTool object which may contain instructions from the orchestrator for event tool input planning
        
        Returns: An EventToolPlanResult object containing the generated input for event tool which may include event name, description, trigger time and any other relevant information.
        """
        formatted_prompt, parser = get_manager_client_prompts(
            type="event_tool_plan_generation",
        )
        chain = formatted_prompt | self.model | parser

        instructions = state.event_tool.instructions if state.event_tool.instructions else ""
        
        timestamp = UTC_NOW()
        user_tz = state.user_timezone or "UTC"
        local_timestamp = get_local_time(timestamp, user_tz).replace(tzinfo=None)

        res = chain.invoke({
            "user_query": state.query,
            "orchestrator_instructions": instructions,
            "current_time": local_timestamp,
        })
        return res