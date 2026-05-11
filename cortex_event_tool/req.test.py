## Set PYTHON_PATH to include cortex_core and cortex_queue for testing purposes
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# env load
from dotenv import load_dotenv
load_dotenv()

# DB Setup
import os
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_NAME = os.getenv("POSTGRES_DB")
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}"
os.environ["DB_URL"] = DB_URL

# Redis Setup
os.environ["REDIS_HOST"] = os.getenv("REDIS_HOST", "localhost")
os.environ["REDIS_PORT"] = os.getenv("REDIS_PORT", "6379")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from cortex_event_tool.main import create_event, get_user_events
from cortex_cm.pg import EventStatus

"""
## Worker Testing Only
This file can be used only to test worker functionality.
`cortex_event_tool.main` methods are called either by worker or cortex_core and not by this file.

### Example Request Body for Create Event Endpoint
{
    user_id:"11111111-1111-1111-1111-111111111111",
    session_id:"22222222-2222-2222-2222-222222222222",
    name:"Demo Event",
    trigger_time:"2023-10-01T10:00:00Z",
    event_info:"This is a reminder to check the event tool worker functionality.",
    event_description:"Demo event description",
    embedding:null
}
"""
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
