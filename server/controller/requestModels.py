from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from uuid import UUID

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatThreadCreate(BaseModel):
    # Optional initial message or just empty
    pass

class ChatThreadResponse(BaseModel):
    session_id: UUID
    user_id: UUID
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    message_id: UUID
    session_id: UUID
    user_id: UUID
    content: str
    role: str
    created_at: datetime

class TaskResponse(BaseModel):
    task_id: UUID
    task_name: str
    task_description: Optional[str]
    status: str
    created_at: datetime

class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    reminders: Optional[List[dict]] = None

class CalendarEventResponse(BaseModel):
    id: str
    summary: str
    start_time: datetime
    end_time: datetime

class ReminderCreate(BaseModel):
    title: str
    notes: Optional[str] = None
    due: Optional[datetime] = None

class CalendarStatusResponse(BaseModel):
    linked: bool
    token_valid: bool

class ToolSubscriptionRequest(BaseModel):
    is_subscribed: bool
