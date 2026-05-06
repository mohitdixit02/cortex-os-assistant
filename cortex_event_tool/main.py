from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlmodel import Session, select
from cortex_cm.pg import engine, UserEvent, EventStatus
from cortex_cm.pg.req import crud
from cortex_cm.redis.event_tool import save_event_to_redis, delete_event_from_redis

def create_event(
    user_id: UUID,
    session_id: UUID,
    name: str,
    trigger_time: datetime,
    event_info: Optional[str] = None,
    event_description: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> UserEvent:
    """
    Creates a new event in PostgreSQL and persists it in Redis for worker tracking.
    
    Args:
        user_id (UUID): The ID of the user creating the event.
        session_id (UUID): The current session ID.
        name (str): Name of the event.
        trigger_time (datetime): When the event should be triggered.
        event_info (Optional[str]): Additional info for the event.
        event_description (Optional[str]): Description of the event.
        embedding (Optional[List[float]]): Vector embedding of the event description.
        
    Returns:
        UserEvent: The created UserEvent object.
    """
    with Session(engine) as session:
        event = UserEvent(
            user_id=user_id,
            session_id=session_id,
            name=name,
            trigger_time=trigger_time,
            event_info=event_info,
            event_description=event_description,
            embedding=embedding,
            status=EventStatus.CREATED
        )
        db_event = crud.create_one(session, event)
        
        # Save to Redis for worker to track
        redis_data = {
            "event_id": str(db_event.id),
            "user_id": str(db_event.user_id),
            "session_id": str(db_event.session_id),
            "name": db_event.name,
            "trigger_time": db_event.trigger_time.isoformat(),
            "status": db_event.status.value
        }
        save_event_to_redis(str(db_event.id), db_event.trigger_time.isoformat(), redis_data)
        
        return db_event

def get_user_events(
    user_id: UUID,
    session_id: Optional[UUID] = None,
    status: Optional[EventStatus] = None,
    limit: int = 100
) -> List[UserEvent]:
    """
    Fetches events for a specific user and optionally a session and status.
    
    Args:
        user_id (UUID): The user ID.
        session_id (Optional[UUID]): The session ID.
        status (Optional[EventStatus]): The status of events to fetch.
        limit (int): Maximum number of events to return.
        
    Returns:
        List[UserEvent]: A list of matching UserEvent objects.
    """
    with Session(engine) as session:
        filters = {"user_id": user_id}
        if session_id:
            filters["session_id"] = session_id
        if status:
            filters["status"] = status
        
        return crud.get_many(session, UserEvent, limit=limit, **filters)

def update_event_status(event_id: UUID, status: EventStatus) -> Optional[UserEvent]:
    """
    Updates the status of an event in both PostgreSQL and Redis.
    
    Args:
        event_id (UUID): The event ID.
        status (EventStatus): The new status.
        
    Returns:
        Optional[UserEvent]: The updated UserEvent object if found, else None.
    """
    with Session(engine) as session:
        db_event = crud.get_by_id(session, UserEvent, event_id)
        if not db_event:
            return None
        
        old_trigger_time = db_event.trigger_time.isoformat()
        db_event.status = status
        db_event.updated_at = datetime.now(timezone.utc)
        
        updated_event = crud.update_one(session, db_event, db_event)
        
        # Sync with Redis
        if status in [EventStatus.DONE, EventStatus.FAILED, EventStatus.CANCELLED]:
            delete_event_from_redis(str(event_id), old_trigger_time)
        else:
            redis_data = {
                "event_id": str(updated_event.id),
                "user_id": str(updated_event.user_id),
                "session_id": str(updated_event.session_id),
                "name": updated_event.name,
                "trigger_time": updated_event.trigger_time.isoformat(),
                "status": updated_event.status.value
            }
            save_event_to_redis(str(updated_event.id), updated_event.trigger_time.isoformat(), redis_data)
            
        return updated_event

def get_due_events_pg(time_window_minutes: int = 5) -> List[UserEvent]:
    """
    Checks for events in PostgreSQL that are due within a given time window.
    
    Args:
        time_window_minutes (int): The window in minutes from now.
        
    Returns:
        List[UserEvent]: A list of due UserEvent objects.
    """
    now = datetime.now(timezone.utc)
    future_limit = now + timedelta(minutes=time_window_minutes)
    
    with Session(engine) as session:
        statement = select(UserEvent).where(
            UserEvent.status == EventStatus.CREATED,
            UserEvent.trigger_time <= future_limit
        )
        return list(session.exec(statement).all())

def get_similar_events(
    user_id: UUID,
    query_embedding: List[float],
    limit: int = 5,
    threshold: float = 0.55
) -> List[Tuple[UserEvent, float]]:
    """
    Performs semantic search for events based on embedding.
    """
    with Session(engine) as session:
        return crud.get_similar(
            session=session,
            model=UserEvent,
            query_embedding=query_embedding,
            top_k=limit,
            user_id=user_id
        )
