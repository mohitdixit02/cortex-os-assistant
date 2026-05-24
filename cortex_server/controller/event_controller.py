from fastapi import APIRouter, Depends, Query
from typing import List
from cortex_server.service.auth.auth_dependency import get_current_user_id
from cortex_server.service.event_service import event_service
from cortex_server.controller.requestModels import EventResponse
from uuid import UUID
from typing import Optional
router = APIRouter(prefix="/v1/events", tags=["Events"])

@router.get("", response_model=List[EventResponse])
async def list_events(
    user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session_id: Optional[str] = Query(None)
):
    """Retrieve all user events (reminders) with pagination."""
    offset = (page - 1) * limit
    events = event_service.list_events(user_id=UUID(user_id), offset=offset, limit=limit, session_id=session_id)
    return events
