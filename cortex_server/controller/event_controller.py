from fastapi import APIRouter, Depends, Query
from typing import List
from service.auth.auth_dependency import get_current_user_id
from service.event_service import event_service
from controller.requestModels import EventResponse
from uuid import UUID

router = APIRouter(prefix="/v1/events", tags=["Events"])

@router.get("", response_model=List[EventResponse])
async def list_events(
    user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Retrieve all user events (reminders) with pagination."""
    offset = (page - 1) * limit
    events = event_service.list_events(user_id=UUID(user_id), offset=offset, limit=limit)
    return events
