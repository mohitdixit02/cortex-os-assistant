import asyncio
from datetime import datetime
from typing import Type, Optional, Annotated, Literal
from pydantic import BaseModel, Field
import json
from langchain_core.tools import BaseTool
from uuid import UUID
from cortex_event_tool.main import create_event
from cortex_cm.pg.req import crud

class EventToolInput(BaseModel):
    """Input schema for event tool."""
    message_id: UUID = Field(description="ID of the message associated with the event.")
    name: str = Field(description="Name of the event (required for create).")
    trigger_time: str = Field(description="Trigger time in ISO format (required for create).")
    event_description: str = Field(description="Description of the event.")

class EventTool(BaseTool):
    """
    A tool to manage user reminders and events (analogous to Google Calendar/Tasks). \n
    Use this tool to create or retrieve reminders and events based on user queries. \n
    """
    name: str = "EventTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = EventToolInput

    def _run(self, **kwargs) -> str:
        try:
            input_data = EventToolInput(**kwargs)
            if not input_data.name or not input_data.trigger_time:
                return "Error: 'name' and 'trigger_time' are required for creating an event."
                        
            res = create_event(
                message_id=input_data.message_id,
                name=input_data.name,
                trigger_time=datetime.fromisoformat(input_data.trigger_time),
                event_description=input_data.event_description,
            )
            return f"Event created successfully: {res.id}"
                
        except Exception as e:
            return f"Error executing EventTool: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        return await asyncio.to_thread(self._run, **kwargs)

__all__ = ["EventTool", "EventToolInput"]
