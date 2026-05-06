from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime

from cortex_event_tool.main import create_event, get_user_events, update_event_status, get_similar_events
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

class EventStatusUpdateRequest(BaseModel):
    event_id: UUID
    status: EventStatus

class EventSimilarityRequest(BaseModel):
    user_id: UUID
    embedding: List[float]
    limit: int = 5
    threshold: float = 0.55

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

@app.post("/update_event_status")
async def update_event_status_endpoint(request: EventStatusUpdateRequest):
    try:
        event = update_event_status(event_id=request.event_id, status=request.status)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_similar_events")
async def get_similar_events_endpoint(request: EventSimilarityRequest):
    try:
        results = get_similar_events(
            user_id=request.user_id,
            query_embedding=request.embedding,
            limit=request.limit,
            threshold=request.threshold
        )
        # Convert Tuple[UserEvent, float] to something JSON serializable
        formatted_results = [
            {
                "event": res[0],
                "similarity": res[1]
            }
            for res in results
        ]
        return formatted_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
