from cortex.manager.tools import AvailableToolsType, WebSearchTool, WebSearchInput, TaskRetrieverTool, TaskRetrieverInput, TaskRetrieverResult
from cortex.graph.state import CortexTool, ToolManagerState, WebSearchToolState, TaskRetrieverToolState
from cortex.manager.model import ManagerModel
from utility.logger import get_logger
from langchain_core.documents import Document
from cortex.manager.utility import retrieve_relevant_docs_utility
from cortex.memory.embedding import EmbeddingModel
from typing import Literal, Optional
import json

class ManagerClient():
    """Manages the tool executions based on Orchestrator's plan"""
    def __init__(self):
        self.logger = get_logger("CORTEX_MANAGER")
        self.model = ManagerModel()
        self.embd_model = EmbeddingModel()
        
    def web_search_tool(self, state: ToolManagerState):
        try:
            query = state.query
            if query is None or query.strip() == "":
                self.logger.warning("Empty query provided for web search tool")
                raise ValueError("Query cannot be empty for web search tool")
            res = self.model.build_web_search_plan(
                state=state,
            )
            if not res or not res.query:
                self.logger.warning("No keywords generated for web search tool")
                raise ValueError("Failed to generate keywords for web search tool")

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
                
            state.web_search_tool = state.web_search_tool.model_copy(update={
                "tool_result": result,
                "tool_exec_status": "completed",
            })
        
            return {
                "web_search_tool": state.web_search_tool,
            }
        except Exception as e:
            self.logger.error(f"Error executing web search tool: {str(e)}")
            state.web_search_tool = state.web_search_tool.model_copy(update={
                "tool_result": "Failed to execute web search tool.",
                "tool_exec_status": "failed",
            })
            return {
                "web_search_tool": state.web_search_tool,
            }
    
    def task_retriever_tool(
        self,
        state: ToolManagerState
    ):
        try:
            self.logger.info(f"Task retriever tool: {state.task_retriever_tool}")
            task_plan_res = self.model.build_task_retrieval_plan(state=state)
            self.logger.info(f"Task retrieval plan result: {task_plan_res}")
            task_retriever_tool = TaskRetrieverTool()
            tool_input = TaskRetrieverInput(
                fetch_mode=task_plan_res.fetch_mode,
                task_description=task_plan_res.task_description,
                time_start_range=task_plan_res.time_start_range,
                time_end_range=task_plan_res.time_end_range,
                recent_count=task_plan_res.recent_count,
                task_id=state.task_id,
                user_id=state.user_id,
                session_id=state.session_id,
            )
            task_res = task_retriever_tool.retrieve_tasks(
                input=tool_input,
                model=self.embd_model,
            )
            
            tool_result = [task.model_dump() for task in task_res]
                        
            self.logger.info(f"Retrieved {len(task_res)} tasks from task retriever tool.")
            self.logger.info(f"Task retriever tool results: {task_res}")
                            
            state.task_retriever_tool = TaskRetrieverToolState(
                task_description=task_plan_res.task_description,
                tool_result=json.dumps(tool_result),
                tool_exec_status="completed",
            )
            return {
                "task_retriever_tool": state.task_retriever_tool,
            }
        except Exception as e:
            self.logger.error(e)
            self.logger.error(f"[MANAGER] Error executing task retriever tool: {str(e)}")
            state.task_retriever_tool = state.task_retriever_tool.model_copy(update={
                "tool_result": "Failed to retrieve task.",
                "tool_exec_status": "failed",
            })
            return {
                "task_retriever_tool": state.task_retriever_tool,
            }
    
    def tool_result_aggregator(self, state: ToolManagerState):
        self.logger.info("Aggregating tool results for the current conversation state.")
        return state
        
    def tools_manager(self, state: ToolManagerState):
        """
        Entry Node for Tools Execution Workflow
        """
        self.logger.info("Executing tools manager...")
        return {}
    
    def execute_tools_route(
        self, 
        state: ToolManagerState
    ) -> Literal["web_search_tool", "task_retriever_tool", "tool_result_aggregator"]:
        
        called_tools = []
        if state.web_search_tool is not None:
            self.logger.info("Web search tool selected for execution...")
            called_tools.append("web_search_tool")
        if state.task_retriever_tool is not None:
            self.logger.info("Task retriever tool selected for execution...")
            called_tools.append("task_retriever_tool")
            
        if len(called_tools) == 0:
            self.logger.info("No tools to execute based on the current conversation state.")
            return "tool_result_aggregator"

        return called_tools

    def summarize_tool_results(self, state: ToolManagerState):
        if state.web_search_tool:
            if state.web_search_tool.tool_exec_status == "completed" and state.web_search_tool.tool_result:
                self.logger.info("Summarizing web search tool results.")
                summary = self.model.summarize_tool_result(
                    tool_result = state.web_search_tool.tool_result,
                    query = state.query,
                    tool_type = AvailableToolsType.WEB_SEARCH_TOOL.value
                )
                state.web_search_tool = state.web_search_tool.model_copy(update={
                    "tool_result": summary,
                })
                return {
                    "web_search_tool": state.web_search_tool,
                }
            else:
                self.logger.info("Web search tool did not complete successfully or has no results to summarize.")
                return {
                    "web_search_tool": state.web_search_tool,
                }
        else:
            self.logger.info("No tool results to summarize.")
            return {}
        