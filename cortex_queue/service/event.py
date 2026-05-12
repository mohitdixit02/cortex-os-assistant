from http.client import HTTPException
from typing import Optional
from uuid import UUID as UUIDType

from cortex_queue.dto import AddTaskRequest, TaskItem
from cortex_cm.pg import TaskStatus, engine, TaskOwner, EventStatus, UserEvent
from cortex_cm.pg.req import crud
from cortex_core.memory.saver import MemorySaver
from cortex_core.memory.embedding import EmbeddingModel
from sqlmodel import Session
from datetime import datetime, timezone

from cortex_cm.utility.logger import get_logger
logger = get_logger("TASK_QUEUE")

model = EmbeddingModel()
memory_saver = MemorySaver(engine=engine, model=model)

def _update_event_status(event_id: UUIDType | str, status: EventStatus) -> Optional[UserEvent]:
    """
    Updates the status of an event in PostgreSQL
    """
    with Session(engine) as session:
        normalized_event_id = event_id if isinstance(event_id, UUIDType) else UUIDType(str(event_id))
        db_event = crud.get_by_id(session, UserEvent, normalized_event_id)
        if not db_event:
            return None
        
        db_event.status = status
        db_event.updated_at = datetime.now(timezone.utc)
        
        updated_event = crud.update_one(session, db_event, db_event)
        return updated_event

async def add_event_tool_task_to_queue(request: AddTaskRequest) -> TaskItem:
    message_id = request.metadata.get("message_id")
    if not message_id:
        raise HTTPException(status_code=400, detail="Missing message_id in task metadata for event tool task")
    
    task_obj = memory_saver.add_new_task(
        message_id=message_id,
        tool_id=None,
        task_name=request.task_name,
        task_description=request.task_description,
        status=TaskStatus.QUEUED,
        payload=request.payload,
        task_metadata=dict(request.metadata),
        task_owner=TaskOwner.EVENT_TOOL.value
    )
    
    # Update event status to QUEUED in PostgreSQL
    event_id = request.payload.get("event_id")
    if event_id:
        updated_event = _update_event_status(event_id, EventStatus.QUEUED)
        if not updated_event:
            logger.warning(f"Warning: Event with ID {event_id} not found for status update.")
        else:
            logger.info(f"Event {event_id} status updated to QUEUED in PG.")
    else:
        logger.warning("Warning: Task is queued without event_id in payload")
    
    return task_obj

async def update_submit_event_task_status(request: TaskItem):
    event_id = request.payload.get("event_id")
    if event_id:
        new_status = EventStatus.DONE if request.status == TaskStatus.COMPLETED else EventStatus.FAILED
        _update_event_status(event_id, new_status)
    else:
        logger.warning("Warning: No event_id found in task payload for status update")
