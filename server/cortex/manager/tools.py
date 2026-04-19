import asyncio
import time
from typing import Type, Optional, Annotated
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from pydantic import BaseModel, Field
import json
from contextlib import nullcontext
from sqlalchemy import func
from sqlmodel import Session, select
from db import Message, Task, TaskStatus, engine

from cortex.graph.state import CortexTool
from cortex.memory.embedding import EmbeddingModel
from langchain_core.tools import BaseTool
from langchain_community.document_loaders import WebBaseLoader
from langsmith import traceable
try:
    from langsmith.run_helpers import tracing_context
except Exception:  # pragma: no cover - fallback for environments without this helper
    tracing_context = None

class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: list[str] = Field(..., description="The list of strings where each string has relevant keywords to search for.")

class WebSearchTool(BaseTool):
    """
    Use this tool to search the web for up-to-date information. \n
    Instructions should include specifc keywords or context to search for. \n
    """

    name: str = "WebSearchTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = WebSearchInput
    max_results: int = 2
    max_query_workers: int = 6
    max_url_workers: int = 8
    max_urls_per_query: int = 4
    ddg_timeout_s: int = 8
    scrape_timeout_s: float = 8.0
    overall_search_timeout_s: float = 40.0

    def _no_trace_context(self):
        """Return a context manager that disables LangSmith tracing when available."""
        if tracing_context is None:
            return nullcontext()
        return tracing_context(enabled=False)

    @traceable(enabled=False)
    def _run(
        self,
        query: str,
    ) -> str:
        """Execute a synchronous web search."""
        with self._no_trace_context():
            from ddgs import DDGS

            with DDGS(timeout=self.ddg_timeout_s) as ddgs:
                raw_results = ddgs.text(
                    query,
                    max_results=self.max_results,
                    backend="auto",
                )

            normalized_results = [
                {
                    "snippet": item.get("body", ""),
                    "title": item.get("title", ""),
                    "link": item.get("href", ""),
                }
                for item in raw_results or []
            ]
            return json.dumps(normalized_results)

    async def _arun(
        self,
        query: str,
    ) -> str:
        """Execute an asynchronous web search."""
        return await asyncio.to_thread(self._run, query)

    def _search_single_query(self, query: str) -> list[dict]:
        """Search one query and scrape a small bounded set of result URLs."""
        res = self._run(query)
        parsed = json.loads(res)
        urls = [
            item.get("link")
            for item in parsed
            if item.get("link") and "youtube" not in item.get("link", "")
        ]
        urls = list(dict.fromkeys(urls))[: self.max_urls_per_query]
        return self.web_scrap(urls)
    
    def _load_single_url(self, url: str) -> dict | None:
        try:
            with self._no_trace_context():
                loader = WebBaseLoader(
                    url,
                    requests_kwargs={"timeout": self.scrape_timeout_s},
                    continue_on_failure=True,
                    raise_for_status=False,
                    show_progress=False,
                )
                data = loader.load()
            if not data:
                return None
            formatted_data = " ".join((data[0].page_content or "").split())
            if not formatted_data:
                return None
            return {
                "url": url,
                "data": formatted_data,
            }
        except Exception:
            return None
    
    def web_scrap(self, urls: list[str]) -> list[dict]:
        """Perform web search using the tool."""
        if not urls:
            return []

        results: list[dict] = []
        deadline = time.monotonic() + (self.scrape_timeout_s * max(1, len(urls)))
        executor = ThreadPoolExecutor(max_workers=self.max_url_workers)
        try:
            futures = [executor.submit(self._load_single_url, url) for url in urls]
            while futures:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    completed_iter = as_completed(futures, timeout=remaining)
                    future = next(completed_iter)
                except (FutureTimeoutError, StopIteration):
                    break

                futures.remove(future)
                try:
                    item = future.result()
                    if item is not None:
                        results.append(item)
                except Exception:
                    continue
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        return results

    def search(
        self,
        input: WebSearchInput,
    ) -> list[dict]:
        """Perform web search using the tool."""
        query_value = input.query
        queries = [query_value] if isinstance(query_value, str) else list(query_value)

        cleaned_queries = [str(query).strip() for query in queries if str(query).strip()]
        if not cleaned_queries:
            return []

        results: list[dict] = []
        start_time = time.monotonic()
        executor = ThreadPoolExecutor(max_workers=self.max_query_workers)
        try:
            future_to_query = {
                executor.submit(self._search_single_query, query): query
                for query in cleaned_queries
            }
            pending = list(future_to_query.keys())

            while pending:
                remaining_timeout = self.overall_search_timeout_s - (time.monotonic() - start_time)
                if remaining_timeout <= 0:
                    break
                try:
                    completed_iter = as_completed(pending, timeout=remaining_timeout)
                    future = next(completed_iter)
                except (FutureTimeoutError, StopIteration):
                    break

                pending.remove(future)
                try:
                    docs = future.result()
                    if docs:
                        results.extend(docs)
                except Exception:
                    continue

            for future in pending:
                future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return results
    
class TaskRetrieverInput(BaseModel):
    """Input schema for task retriever tool."""
    user_id: str = Field(..., description="The ID of the user for whom to retrieve tasks.")
    session_id: str = Field(..., description="The session ID for which to retrieve tasks.")
    task_description: str = Field(..., description="Description or type of tasks to retrieve.")
    task_id: Optional[str] = Field(default=None, description="Current task ID to exclude from the search results.")
    
class TaskRetrieverResult(BaseModel):
    """Output schema for task retriever tool."""
    task_name: str
    task_description: str
    status: TaskStatus
    status_response: Optional[dict]
    created_at: str
    similarity: float
    
class TaskRetrieverTool(BaseTool):
    """
    Tool for retrieving and managing tasks that are executed in the past by the you (AI Application). \n
    Instructions should specify the type, description or nature of task. If provided, it will be used to search for tasks \n. 
    """
    
    name: str = "TaskRetrieverTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = TaskRetrieverInput
    minimum_acceptable_similarity: float = 0.55
    max_results: int = 2
    
    @traceable(enabled=False)
    def _run(
        self,
        input: TaskRetrieverInput,
        model: EmbeddingModel,
    ) -> list[dict]:
        """Execute a synchronous task retrieval."""
        user_id = input.user_id
        session_id = input.session_id
        task_description = input.task_description
        task_id = input.task_id

        query_embedding = model.generate_embeddings(task_description)

        with Session(engine) as session:
            similarity_expr = (1.0 - Task.embedding.cosine_distance(query_embedding)).label("similarity")
            statement = (
                select(
                    Task.task_name,
                    Task.task_description,
                    Task.status,
                    Task.status_response,
                    Task.created_at,
                    similarity_expr
                )
                .join(Message, Task.message_id == Message.message_id)
                .where(Message.user_id == user_id)
                .where(Message.session_id == session_id)
                .where(Task.embedding.is_not(None))
                .where(func.vector_dims(Task.embedding) == len(query_embedding))
                .where(similarity_expr >= self.minimum_acceptable_similarity)
            )

            if task_id:
                statement = statement.where(Task.task_id != task_id)

            statement = statement.order_by(similarity_expr.desc()).limit(self.max_results)
            rows = session.exec(statement).all()

        results: list[TaskRetrieverResult] = []
        for row in rows:
            task_data = TaskRetrieverResult(
                task_name=row.task_name,
                task_description=row.task_description,
                status=row.status,
                status_response=row.status_response,
                created_at=row.created_at.isoformat(),
                similarity=row.similarity,
            )
            results.append(task_data)
            
        return results
    
    def retrieve_tasks(
        self,
        input: TaskRetrieverInput,
        model: EmbeddingModel,
    ) -> list[TaskRetrieverResult]:
        """
        Retrieve semantically matching tasks based on the input task description and instructions. \n
        if `task_id` is provided, that specific task will be skipped.
        """
        print(f"Retrieving tasks with description: {input.task_description}, user_id: {input.user_id}, session_id: {input.session_id}, excluding task_id: {input.task_id}")
        return self._run(input=input, model=model)
    
class AvailableToolsType(str, Enum):
    WEB_SEARCH_TOOL = "web_search_01"
    TASK_RETRIEVER_TOOL = "task_retriever_02"
    CALENDAR_TOOL = "calendar_03"
    EMAIL_TOOL = "email_04"

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
]

__all__ = [
    "AVAILABLE_TOOLS",
    "AvailableToolsType",
    "WebSearchTool",
    "WebSearchInput",

]
    