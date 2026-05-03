import asyncio
import time
from datetime import datetime
from typing import Type, Optional, Annotated, Literal
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from pydantic import BaseModel, Field
import json
from contextlib import nullcontext
from sqlalchemy import Float, func
from sqlmodel import Session, select
from cortex_cm.pg import Message, Task, TaskStatus, engine

from cortex_core.graph.state import CortexTool
from cortex_core.memory.embedding import EmbeddingModel
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
    Use it when user query involve information, facts, or any kind of context which required web search. \n
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
    fetch_mode: Annotated[Literal["description", "time", "recent"], Field(description="Mode to fetch tasks (description, time, or recent)")] = "description"
    task_description: Optional[str] = Field(default=None, description="Description or type of tasks to retrieve.")
    time_start_range: Optional[str] = Field(default=None, description="Start of the time range for task creation. (only applicable when fetch_mode is 'time')")
    time_end_range: Optional[str] = Field(default=None, description="End of the time range for task creation. (only applicable when fetch_mode is 'time')")
    recent_count: Optional[int] = Field(default=None, description="Number of recent tasks to retrieve when fetch_mode is 'recent'.")
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
    Tool for retrieving and managing tasks that you have done in the past. \n
    **When to use:** \n
    - User about any past task or task related information, or something he/she has asked to do in the past. \n
    - User ask about the status of any task. \n
    Response will include the tasks that are done in past based on the task description and instructions provided. \n
    Instructions should specify the type, description or nature of task. If provided, it will be used to search for tasks \n. 
    """
    
    name: str = "TaskRetrieverTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = TaskRetrieverInput
    minimum_acceptable_similarity: float = 0.55
    max_results: int = 2
    
    def retrieve_description_based_tasks_statement(
        self, 
        input: TaskRetrieverInput,
        model: EmbeddingModel,
        ) -> str:
        """
        Returns a SQL statement to retrieve tasks based on semantic similarity of task description. \n
        """
        user_id = input.user_id
        session_id = input.session_id
        task_description = input.task_description
        if not task_description:
            raise ValueError("task_description must be provided when fetch_mode is 'description'")
        query_embedding = model.generate_embeddings(task_description)
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
        
        if input.task_id:
            statement = statement.where(Task.task_id != input.task_id)
        
        statement = statement.order_by(similarity_expr.desc()).limit(self.max_results)
        return statement

    def retrieve_time_based_tasks_statement(
        self, 
        input: TaskRetrieverInput
        ) -> str:
        """Retrieve tasks based on recency within a specified time range."""
        user_id = input.user_id
        session_id = input.session_id
        time_start_range = input.time_start_range
        time_end_range = input.time_end_range

        statement = (
            select(
                Task.task_name,
                Task.task_description,
                Task.status,
                Task.status_response,
                Task.created_at,
                func.cast(0.0, Float).label("similarity")
            )
            .join(Message, Task.message_id == Message.message_id)
            .where(Message.user_id == user_id)
            .where(Message.session_id == session_id)
        )
        
        if time_start_range:
            statement = statement.where(Task.created_at >= time_start_range)
        if time_end_range:
            statement = statement.where(Task.created_at <= time_end_range)
        if input.task_id:
            statement = statement.where(Task.task_id != input.task_id)

        statement = statement.order_by(Task.created_at.desc()).limit(self.max_results)

        return statement

    def retrieve_recent_based_tasks_statement(
        self, 
        input: TaskRetrieverInput
        ) -> str:
        """Retrieve recent tasks based on creation time."""
        user_id = input.user_id
        session_id = input.session_id
        recent_count = input.recent_count or self.max_results

        statement = (
            select(
                Task.task_name,
                Task.task_description,
                Task.status,
                Task.status_response,
                Task.created_at,
                func.cast(0.0, Float).label("similarity")
            )
            .join(Message, Task.message_id == Message.message_id)
            .where(Message.user_id == user_id)
            .where(Message.session_id == session_id)
        )

        if input.task_id:
            statement = statement.where(Task.task_id != input.task_id)

        statement = statement.order_by(Task.created_at.desc()).limit(recent_count)
        return statement
    
    @traceable(enabled=False)
    def _run(
        self,
        input: TaskRetrieverInput,
        model: EmbeddingModel,
    ) -> list[dict]:
        """Execute a synchronous task retrieval."""
        with Session(engine) as session:
            if input.fetch_mode == "description":
                statement = self.retrieve_description_based_tasks_statement(input, model)
            elif input.fetch_mode == "time":
                statement = self.retrieve_time_based_tasks_statement(input)
            elif input.fetch_mode == "recent":
                statement = self.retrieve_recent_based_tasks_statement(input)
            else:
                raise ValueError(f"Invalid fetch_mode: {input.fetch_mode}")
            
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

class CalendarInput(BaseModel):
    """Input schema for calendar tool."""
    action: Annotated[Literal["create", "list", "update", "delete", "status"], Field(description="Action to perform on the calendar (create, list, update, delete, or status)")]
    event_summary: Optional[str] = Field(default=None, description="Short summary or title of the event.")
    event_description: Optional[str] = Field(default=None, description="Detailed description of the event.")
    start_time: Optional[str] = Field(default=None, description="Start time of the event in ISO format (e.g., 2023-10-27T10:00:00Z).")
    end_time: Optional[str] = Field(default=None, description="End time of the event in ISO format (e.g., 2023-10-27T11:00:00Z).")
    event_id: Optional[str] = Field(default=None, description="Unique identifier for an existing event (required for update, delete, or status).")
    max_results: Optional[int] = Field(default=5, description="Maximum number of events to list.")

class CalendarTool(BaseTool):
    """
    A tool to manage calendar events, appointments, and schedules. \n
    Use this tool to create, update, delete, or retrieve calendar events based on user queries and instructions. \n
    """
    name: str = "CalendarTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = CalendarInput

    def _get_calendar_service(self):
        """Initialize and return the Google Calendar API service."""
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        import os
        
        creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
        if not creds_json:
            raise ValueError("GOOGLE_CALENDAR_CREDENTIALS environment variable is not set.")
        
        try:
            # Try parsing as JSON string first
            import json
            info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/calendar"]
            )
        except Exception:
            # Fallback to file path
            credentials = service_account.Credentials.from_service_account_file(
                creds_json, scopes=["https://www.googleapis.com/auth/calendar"]
            )
            
        return build("calendar", "v3", credentials=credentials)

    def _run(self, **kwargs) -> str:
        """Execute the calendar tool logic."""
        try:
            input_data = CalendarInput(**kwargs)
            service = self._get_calendar_service()
            calendar_id = "primary" # Or from env

            if input_data.action == "create":
                event = {
                    'summary': input_data.event_summary,
                    'description': input_data.event_description,
                    'start': {'dateTime': input_data.start_time, 'timeZone': 'UTC'},
                    'end': {'dateTime': input_data.end_time, 'timeZone': 'UTC'},
                }
                event = service.events().insert(calendarId=calendar_id, body=event).execute()
                return f"Event created: {event.get('htmlLink')}"

            elif input_data.action == "list":
                now = datetime.utcnow().isoformat() + 'Z'
                events_result = service.events().list(
                    calendarId=calendar_id, timeMin=now,
                    maxResults=input_data.max_results, singleEvents=True,
                    orderBy='startTime'
                ).execute()
                events = events_result.get('items', [])
                if not events:
                    return "No upcoming events found."
                return json.dumps(events)

            elif input_data.action == "status" or (input_data.action == "list" and input_data.event_id):
                if not input_data.event_id:
                    return "Error: event_id is required for status check."
                event = service.events().get(calendarId=calendar_id, eventId=input_data.event_id).execute()
                return json.dumps(event)

            elif input_data.action == "update":
                if not input_data.event_id:
                    return "Error: event_id is required for update."
                event = service.events().get(calendarId=calendar_id, eventId=input_data.event_id).execute()
                if input_data.event_summary: event['summary'] = input_data.event_summary
                if input_data.event_description: event['description'] = input_data.event_description
                if input_data.start_time: event['start']['dateTime'] = input_data.start_time
                if input_data.end_time: event['end']['dateTime'] = input_data.end_time
                updated_event = service.events().update(calendarId=calendar_id, eventId=input_data.event_id, body=event).execute()
                return f"Event updated: {updated_event.get('htmlLink')}"

            elif input_data.action == "delete":
                if not input_data.event_id:
                    return "Error: event_id is required for deletion."
                service.events().delete(calendarId=calendar_id, eventId=input_data.event_id).execute()
                return "Event deleted successfully."

            else:
                return f"Unsupported action: {input_data.action}"

        except Exception as e:
            return f"Error executing CalendarTool: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        """Asynchronous execution (runs the sync version in a thread)."""
        return await asyncio.to_thread(self._run, **kwargs)

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
        "tool_id": AvailableToolsType.CALENDAR_TOOL.value,
        "tool_name": CalendarTool.__name__,
        "tool_description": CalendarTool.__doc__,
    },
]

__all__ = [
    "AVAILABLE_TOOLS",
    "AvailableToolsType",
    "WebSearchTool",
    "WebSearchInput",
    "CalendarTool",
    "CalendarInput",
]
    