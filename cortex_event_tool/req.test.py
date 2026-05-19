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
os.environ["REDIS_HOST"] = "localhost"
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
    message_id:"11111111-1111-1111-1111-111111111111",
    name:"Demo Event",
    trigger_time:"2023-10-01T10:00:00Z",
    event_description:"Demo event description",
    embedding:null
}

Mark is_test=True when creating events through this endpoint to ensure redis is connected locally outside of Docker.
"""
app = FastAPI(title="Cortex Event Tool Service")

@app.get("/")
async def root():
    return {"message": "Cortex Event Tool Service is running", "endpoints": ["/health", "/create_event", "/get_events/{user_id}"]}

@app.get("/health")
async def health():
    return {"status": "ok"}

class EventCreateRequest(BaseModel):
    message_id: UUID
    name: str
    trigger_time: datetime
    event_description: Optional[str] = None

@app.post("/create_event")
async def create_event_endpoint(request: EventCreateRequest):
    try:
        event = create_event(
            message_id=request.message_id,
            name=request.name,
            trigger_time=request.trigger_time,
            event_description=request.event_description,
            is_test=True  # Mark this event as a test event
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
