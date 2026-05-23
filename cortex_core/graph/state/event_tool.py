from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

"""
    Event Tool State Models
"""
class EventToolState(BaseModel):
    message_id: str
    user_timezone: Optional[str] = "UTC"
    event_name: str
    event_description: str
    trigger_time: datetime
    time_left: int = 5
    user_name: Optional[str] = None
    time_of_query: Optional[str] = None
    final_reminder: Optional[str] = None

__all__ = [
    "EventToolState",
]