from cortex.manager.tools import AvailableToolsType, WebSearchTool
from cortex.graph.state import ConversationState, CortexTool
from cortex.manager.model import ManagerModel
from utility.logger import get_logger
from langchain_core.documents import Document
from cortex.manager.utility import retrieve_relevant_docs_utility
from cortex.memory.embedding import EmbeddingModel

class ManagerClient():
    """Manages the tool executions based on Orchestrator's plan"""
    def __init__(self):
        self.logger = get_logger("CORTEX_MANAGER")
        self.model = ManagerModel()
        self.embd_model = EmbeddingModel()
        
    def _handle_web_search_tool(self, query: str, tool: CortexTool) -> str:
        if query is None or query.strip() == "":
            self.logger.warning("Empty query provided for web search tool")
            return ""
        res = self.model.build_web_search_plan(
            query=query,
            tool=tool
        )
        if not res or not res.query:
            self.logger.warning("No keywords generated for web search tool")
            return ""

        web_search_tool = WebSearchTool()
        self.logger.info(f"Executing web search tool with query: {res.query}")
        result = web_search_tool.search(input=res)
        docs = []
        for doc in result:
            data = doc.get("data", "")
            doc_obj = Document(
                page_content=data,
                metadata={
                    "source": doc.get("url", "")
                }
            )
            docs.append(doc_obj)

        target_query = " ".join(res.query) if isinstance(res.query, list) else res.query
        relevant_docs = retrieve_relevant_docs_utility(
            target_query=target_query,
            relevant_docs=docs,
            model=self.embd_model,
        )
        self.logger.info(f"Retrieved {len(relevant_docs)} relevant documents for the query.")
        
        result = ""
        for doc in relevant_docs:
            result += doc.page_content + "\n"
        
        return result
        
    def _execute_tool(self, tool: CortexTool, query: str):
        if tool.tool_id == AvailableToolsType.WEB_SEARCH_TOOL.value:
            return self._handle_web_search_tool(query, tool)
        else:
            raise ValueError(f"Unsupported tool id: {tool.tool_id}")

    def execute_tools(
        self,
        state: ConversationState,
    ):
        orchestrator_state = state.orchestration_state
        if orchestrator_state is None:
            self.logger.warning("No orchestration state found in the conversation state. Skipping tool execution.")
            return state
    
        if orchestrator_state.is_tool_required is False:
            self.logger.info("No tool is required for the current query as per the orchestration state. Skipping tool execution.")
            return state
        
        selected_tools = orchestrator_state.selected_tools
        selected_tools_list = selected_tools.root if hasattr(selected_tools, "root") else selected_tools
        for tool in selected_tools_list:
            if isinstance(tool, CortexTool):
                try:
                    res = self._execute_tool(tool, query=state.query)
                    tool.tool_result = res
                    tool.tool_exec_status = "completed"
                except Exception as e:
                    self.logger.error(f"Error occurred while executing tool {tool}: {e}")
                    tool.tool_exec_status = "failed"
                    tool.tool_result = None
            else:
                self.logger.warning(f"Invalid tool format: {tool}. Skipping this tool.")
        
        state.orchestration_state.selected_tools = selected_tools
        return {
            "orchestration_state": state.orchestration_state,
        }
