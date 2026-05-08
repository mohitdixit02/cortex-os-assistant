from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime

from cortex_event_tool.main import create_event, get_user_events, update_event_status
from cortex_cm.pg import EventStatus

app = FastAPI(title="Cortex Event Tool Service")

class EventCreateRequest(BaseModel):
    user_id: UUID
    session_id: UUID
    name: str
    trigger_time: datetime
    event_info: Optional[str] = None
    event_description: Optional[str] = None
    embedding: Optional[List[float]] = None

@app.post("/create_event")
async def create_event_endpoint(request: EventCreateRequest):
    try:
        event = create_event(
            user_id=request.user_id,
            session_id=request.session_id,
            name=request.name,
            trigger_time=request.trigger_time,
            event_info=request.event_info,
            event_description=request.event_description,
            embedding=request.embedding
        )
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_events/{user_id}")
async def get_events_endpoint(
    user_id: UUID, 
    session_id: Optional[UUID] = None, 
    status: Optional[EventStatus] = None,
    limit: int = 100
):
    try:
        events = get_user_events(user_id=user_id, session_id=session_id, status=status, limit=limit)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
