import asyncio
from typing import Type
from enum import Enum
from pydantic import BaseModel, Field
import json

from cortex.graph.state import CortexTool
from langchain_core.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.document_loaders import WebBaseLoader

web_search_tool = CortexTool(
    tool_id="web_search_01",
    tool_name="web_search",
    tool_description="Use this tool to search the web for up-to-date information. Input should be a search query. Output will be a list of relevant search results.",
)

email_tool = CortexTool(
        tool_id="email_02",
        tool_name="email",
        tool_description="Use this tool to send emails. Input should be the recipient, subject, and body of the email.",
    )

calendar_tool = CortexTool(
    tool_id="calendar_03",
    tool_name="calendar",
    tool_description="Use this tool to manage calendar events. Input should specify the action (create, update, delete) and the event details.",
)

# class TasksLoaderTool(CortexTool):
#     """
#     Tool for loading and managing tasks in the Cortex Main Client. \n 
#     """
    
#     def __init__(self):
#         super().__init__(
#             tool_id="task_loader_01",
#             tool_name="Task Loader",
#             tool_description="Handles the tasks submitted by the Task Queue",
#         )

#     @tool("tasks_loader_00")
#     def load_tasks(self, *args, **kwargs):
#         """
#         Load the list of task items based on the similarity wih the task name.
#         """
        
class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: list[str] = Field(..., description="The list of strings where each string has relevant keywords to search for.")

class WebSearchTool(BaseTool):
    """LangChain BaseTool implementation backed by DuckDuckGoSearchResults."""

    name: str = "web_search"
    description: str = (
        "Use this tool to search the web for up-to-date information. "
        "Input must be a list of search queries."
    )
    args_schema: Type[BaseModel] = WebSearchInput
    max_results: int = 5

    def _run(
        self,
        query: str,
    ) -> str:
        """Execute a synchronous web search."""
        search_tool = DuckDuckGoSearchResults(
            num_results=self.max_results,
            output_format="json"
        )
        return search_tool.run(query)

    async def _arun(
        self,
        query: str,
    ) -> str:
        """Execute an asynchronous web search."""
        return await asyncio.to_thread(self._run, query)
    
    def web_scrap(self, urls: list[str]) -> list[dict]:
        """Perform web search using the tool."""
        res = []
        for url in urls:
            loader = WebBaseLoader(url)
            data = loader.load()
            formatted_data = " ".join(data[0].page_content.split())
            res.append(
                {
                    "url": url,
                    "data": formatted_data
                }
            )
        return res
    
    def _clean_output(self, output: str) -> str:
        """Clean the output from the web search."""
        return output.strip()

    def search(
        self,
        input: WebSearchInput,
    ) -> list[dict]:
        """Perform web search using the tool."""
        query_value = input.query
        queries = [query_value] if isinstance(query_value, str) else list(query_value)

        results = []
        for query in queries:
            cleaned_query = str(query).strip()
            if not cleaned_query:
                continue
            try:
                res = self._run(cleaned_query)
                res = json.loads(res)
                urls = [item["link"] for item in res if not "youtube" in item.get("link")]
                docs = self.web_scrap(urls)
                results.extend(docs)
                
            except Exception:
                # Keep partial success if one provider call fails.
                continue

        return results
    
class AvailableToolsType(str, Enum):
    WEB_SEARCH_TOOL = "web_search_01"
    EMAIL_TOOL = "email_02"
    CALENDAR_TOOL = "calendar_03"

AVAILABLE_TOOLS = [
    {
        "tool_id": AvailableToolsType.WEB_SEARCH_TOOL.value,
        "tool_name": WebSearchTool.__name__,
        "tool_description": WebSearchTool.__doc__,
    }
]

__all__ = [
    "AVAILABLE_TOOLS",
    "AvailableToolsType",
    "WebSearchTool",
    "WebSearchInput",

]
    