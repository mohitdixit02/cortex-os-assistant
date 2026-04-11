from cortex.manager.tools import AvailableToolsType, WebSearchTool, WebSearchInput
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
        self.logger.info(f"Web search tool context: {res.context}")
        self.logger.info(f"Web search tool diversification flag: {res.is_diversified}")
        search_input = WebSearchInput(query=res.query)
        result = web_search_tool.search(input=search_input)
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
            target_query=target_query + " " + res.context,
            relevant_docs=docs,
            model=self.embd_model,
            is_diversified=res.is_diversified
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
            return {}
    
        if orchestrator_state.is_tool_required is False:
            self.logger.info("No tool is required for the current query as per the orchestration state. Skipping tool execution.")
            return {}
        
        selected_tools = orchestrator_state.selected_tools
        selected_tools_list = selected_tools.root if hasattr(selected_tools, "root") else selected_tools
        updated_tools = []
        for tool in selected_tools_list:
            if isinstance(tool, CortexTool):
                try:
                    res = self._execute_tool(tool, query=state.query)
                    updated_tools.append(
                        tool.model_copy(update={
                            "tool_result": res,
                            "tool_exec_status": "completed",
                        })
                    )
                except Exception as e:
                    self.logger.error(f"Error occurred while executing tool {tool}: {e}")
                    updated_tools.append(
                        tool.model_copy(update={
                            "tool_result": None,
                            "tool_exec_status": "failed",
                        })
                    )
            else:
                self.logger.warning(f"Invalid tool format: {tool}. Skipping this tool.")
        
        state.orchestration_state.selected_tools = selected_tools.model_copy(update={
            "root": updated_tools,
        })
        return {
            "orchestration_state": state.orchestration_state,
        }

    def summarize_tool_results(self, state: ConversationState):
        orchestration_state = state.orchestration_state
        if orchestration_state is None:
            self.logger.warning("No orchestration state found in the conversation state. Cannot summarize tool results.")
            return {}
        
        selected_tools = orchestration_state.selected_tools
        if selected_tools is None:
            self.logger.warning("No selected tools found in the orchestration state. Nothing to summarize.")
            return {}

        selected_tools_list = selected_tools.root if hasattr(selected_tools, "root") else selected_tools
        
        updated_tools = []
        for tool in selected_tools_list:
            if isinstance(tool, CortexTool):
                if tool.tool_id == AvailableToolsType.WEB_SEARCH_TOOL.value:
                    summary = self.model.summarize_tool_result(
                        tool_result = tool.tool_result,
                        query = state.query,
                        tool_type = AvailableToolsType.WEB_SEARCH_TOOL.value
                    )
                    updated_tools.append(
                        tool.model_copy(update={
                            "tool_result": summary,
                            "tool_exec_status": tool.tool_exec_status or "completed",
                        })
                    )
                else:
                    updated_tools.append(tool)
            else:
                self.logger.warning(f"Invalid tool format: {tool}. Skipping this tool in summary.")
        
        state.orchestration_state.selected_tools = selected_tools.model_copy(update={
            "root": updated_tools,
        })
        return {
            "orchestration_state": state.orchestration_state,
        }
