from typing import Type, Optional, Annotated, Literal
from pydantic import BaseModel, Field
from sqlalchemy import Float, func
from sqlmodel import Session, select
from cortex_cm.pg import Message, Task, TaskStatus, engine

from cortex_core.memory.embedding import EmbeddingModel
from langchain_core.tools import BaseTool
from langsmith import traceable

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

__all__ = ["TaskRetrieverTool", "TaskRetrieverInput", "TaskRetrieverResult"]
