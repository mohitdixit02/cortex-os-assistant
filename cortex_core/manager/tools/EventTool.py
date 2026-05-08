import asyncio
from typing import Type, Optional, Annotated, Literal
from pydantic import BaseModel, Field
import json
from langchain_core.tools import BaseTool

class EventToolInput(BaseModel):
    """Input schema for event tool."""
    action: Annotated[Literal["create", "list"], Field(description="Action to perform on the event (create or list)")]
    user_id: str = Field(..., description="The ID of the user.")
    session_id: str = Field(..., description="The session ID.")
    name: Optional[str] = Field(default=None, description="Name of the event (required for create).")
    trigger_time: Optional[str] = Field(default=None, description="Trigger time in ISO format (required for create).")
    event_info: Optional[str] = Field(default=None, description="Additional info for the event.")
    event_description: Optional[str] = Field(default=None, description="Description of the event.")
    fetch_mode: Optional[Annotated[Literal["description", "time", "recent"], Field(description="Mode to fetch events (description, time, or recent)")]] = "recent"
    limit: Optional[int] = Field(default=5, description="Maximum number of events to list.")

class EventTool(BaseTool):
    """
    A tool to manage user reminders and events (analogous to Google Calendar/Tasks). \n
    Use this tool to create or retrieve reminders and events based on user queries. \n
    """
    name: str = "EventTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = EventToolInput

    def _run(self, **kwargs) -> str:
        import requests
        from cortex_cm.utility.config import env
        EVENT_TOOL_URL = env.EVENT_TOOL_URL
        
        try:
            input_data = EventToolInput(**kwargs)
            if input_data.action == "create":
                if not input_data.name or not input_data.trigger_time:
                    return "Error: 'name' and 'trigger_time' are required for creating an event."
                
                from cortex_core.memory.embedding import EmbeddingModel
                model = EmbeddingModel()
                embedding = model.generate_embeddings(input_data.event_description or input_data.name)
                
                response = requests.post(f"{EVENT_TOOL_URL}/create_event", json={
                    "user_id": input_data.user_id,
                    "session_id": input_data.session_id,
                    "name": input_data.name,
                    "trigger_time": input_data.trigger_time,
                    "event_info": input_data.event_info,
                    "event_description": input_data.event_description,
                    "embedding": embedding
                })
                response.raise_for_status()
                return f"Event created successfully: {response.json().get('id')}"

            elif input_data.action == "list":
                if input_data.fetch_mode == "description":
                    from cortex_core.memory.embedding import EmbeddingModel
                    model = EmbeddingModel()
                    embedding = model.generate_embeddings(input_data.event_description or "")
                    response = requests.post(f"{EVENT_TOOL_URL}/get_similar_events", json={
                        "user_id": input_data.user_id,
                        "embedding": embedding,
                        "limit": input_data.limit
                    })
                else:
                    response = requests.get(f"{EVENT_TOOL_URL}/get_events/{input_data.user_id}", params={
                        "session_id": input_data.session_id,
                        "limit": input_data.limit
                    })
                
                response.raise_for_status()
                return json.dumps(response.json())
                
            return f"Unsupported action: {input_data.action}"
        except Exception as e:
            return f"Error executing EventTool: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        return await asyncio.to_thread(self._run, **kwargs)

__all__ = ["EventTool", "EventToolInput"]
