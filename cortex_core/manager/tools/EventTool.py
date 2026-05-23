import asyncio
from datetime import datetime
from typing import Type, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from uuid import UUID
from cortex_event_tool.main import create_event

class EventToolInput(BaseModel):
    """Input schema for event tool."""
    message_id: UUID = Field(description="ID of the message associated with the event.")
    name: str = Field(description="Name of the event (required for create).")
    trigger_time: str = Field(description="Trigger time in ISO format (required for create).")
    event_description: str = Field(description="Description of the event.")

class EventToolOutput(BaseModel):
    """Output schema for event tool."""
    status: Literal["success", "error"] = Field(description="Status of the event tool execution.")
    result: str = Field(description="Result message after executing the event tool.")

class EventTool(BaseTool):
    """
    A tool to manage user reminders and events. \n
    Use this tool to create the reminders and events based on user queries. \n
    Note: It only create events and not fetch, edit or delete them. \n
    Input required the details of the event. \n
    """
    name: str = "EventTool"
    description: str = __doc__
    args_schema: Type[BaseModel] = EventToolInput

    def _run(self, input_data: EventToolInput) -> EventToolOutput:
        try:
            if not input_data.name or not input_data.trigger_time:
                return EventToolOutput(status="error", result="Error: 'name' and 'trigger_time' are required for creating an event.")
                        
            res = create_event(
                message_id=input_data.message_id,
                name=input_data.name,
                trigger_time=datetime.fromisoformat(input_data.trigger_time),
                event_description=input_data.event_description,
            )
            return EventToolOutput(status="success", result=f"Event created successfully: {res.id}")
                
        except Exception as e:
            return EventToolOutput(status="error", result=f"Error executing EventTool: {str(e)}")

    async def _arun(self, **kwargs) -> EventToolOutput:
        return await asyncio.to_thread(self._run, **kwargs)
    
    @classmethod
    def create_event(
        cls,
        input: EventToolInput
    ) -> EventToolOutput:
        try:
            return cls()._run(input_data=input)
        except Exception as e:
            return EventToolOutput(status="error", result=f"Error executing EventTool: {str(e)}")

__all__ = ["EventTool", "EventToolInput", "EventToolOutput"]
