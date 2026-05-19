from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlmodel import Session
from cortex_cm.pg import engine, UserEvent, EventStatus, Message
from cortex_cm.pg.req import crud
from cortex_cm.redis.event_tool import (
    save_event_to_redis,
    get_due_events_from_redis,
    delete_event_from_redis
)
from cortex_cm.redis.config_helper import get_reminder_window_minutes

def create_event(
    message_id: UUID,
    name: str,
    trigger_time: datetime,
    event_description: Optional[str] = None,
    is_test: Optional[bool] = False
) -> UserEvent:
    """
    Creates a new event in PostgreSQL and persists it in Redis for fast retrieval and worker tracking.
    """
    with Session(engine) as session:
        event = UserEvent(
            message_id=message_id,
            name=name,
            trigger_time=trigger_time,
            event_description=event_description,
            status=EventStatus.CREATED
        )
        db_event = crud.create_one(session, event)
        
        # Fetch user_id from message to get reminder window
        message = crud.get_by_id(session, Message, message_id)
        user_id = message.user_id if message else None
        
        # Calculate Effective Trigger Time (Actual - Window)
        reminder_window = get_reminder_window_minutes(user_id) if user_id else 5
        effective_trigger_time = trigger_time - timedelta(minutes=reminder_window)

        # Save to Redis for fast retrieval and worker to track
        redis_data = {
            "id": str(db_event.id),
            "message_id": str(db_event.message_id),
            "user_id": str(user_id) if user_id else None,
            "name": db_event.name,
            "event_description": db_event.event_description,
            "trigger_time": db_event.trigger_time.isoformat(),
            "reminder_window": reminder_window,
            "status": db_event.status.value,
            "created_at": db_event.created_at.isoformat()
        }
        save_event_to_redis(str(db_event.id), effective_trigger_time, redis_data, is_test=is_test)
        
        return db_event

def get_user_events(
    user_id: UUID,
    session_id: Optional[UUID] = None,
    status: Optional[EventStatus] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetches events for a specific user primarily from Redis for speed.
    Falls back to PG if needed or if complex filtering is required.
    
    Args:
        user_id (UUID): The user ID.
        session_id (Optional[UUID]): Optional session ID filter.
        status (Optional[EventStatus]): Optional status filter.
        limit (int): Maximum number of events to return.
        
    Returns:
        List[Dict[str, Any]]: A list of matching event data.
    """
    with Session(engine) as session:
        filters = {"user_id": user_id}
        if session_id:
            filters["session_id"] = session_id
        if status:
            filters["status"] = status
        
        db_events = crud.get_many(session, UserEvent, limit=limit, **filters)
        return [e.model_dump() for e in db_events]

def get_due_events(time_window_minutes: int = 5) -> List[Dict[str, Any]]:
    """
    Checks for due events using Redis global ZSET.
    """
    return get_due_events_from_redis(time_window_seconds=time_window_minutes * 60)

def remove_event(event_id: str):
    """
    Removes an event from Redis after processing to prevent re-processing.
    """
    delete_event_from_redis(event_id)

__all__ = [
    "create_event",
    "get_user_events",
    "get_due_events",
    "remove_event"
]