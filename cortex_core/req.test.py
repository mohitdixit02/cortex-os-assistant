## Set PYTHON_PATH to include workspace root for testing purposes
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
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from cortex_queue.dto import TaskItem, TaskStatus
from cortex_cm.pg.enums import TaskOwner
from cortex_core.req import submit_task

"""
## Core Task Queue Testing Service
This file starts a test server to submit tasks to the Cortex Task Queue.
It replicates the functionality of `cortex_core/req.py` by hitting the real 
Task Queue endpoint via the `submit_task` function.

### Example Request Body for Submit Voice Task
{
    "user_id": "11111111-1111-1111-1111-111111111111",
    "session_id": "22222222-2222-2222-2222-222222222222",
    "query": "Hello Cortex, how are you today?",
    "emotion": "happy"
}
"""

app = FastAPI(title="Cortex Core Queue Test Service")

class VoiceTaskRequest(BaseModel):
    user_id: UUID
    session_id: UUID
    query: str
    emotion: str = "neutral"
    metadata: Optional[Dict[str, Any]] = None

class EventTaskRequest(BaseModel):
    message_id: UUID
    name: str
    event_description: str
    trigger_time: datetime
    metadata: Optional[Dict[str, Any]] = None

@app.post("/submit_voice_task")
async def submit_voice_task_to_queue(request: VoiceTaskRequest):
    """
    Submit a voice client task to the real Task Queue.
    """
    task_id = str(uuid4())
    
    task_item = TaskItem(
        task_id=task_id,
        task_name="voice_query_task",
        task_description=f"Test voice query: {request.query[:30]}...",
        status=TaskStatus.INITIALIZED,
        payload={
            "query": request.query,
            "emotion": request.emotion
        },
        metadata={
            "user_id": str(request.user_id),
            "session_id": str(request.session_id),
            "task_owner": TaskOwner.VOICE_CLIENT.value,
            **(request.metadata or {})
        }
    )
    
    try:
        response = await submit_task(task_item=task_item)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit_event_task")
async def submit_event_task_to_queue(request: EventTaskRequest):
    """
    Submit an event tool task (e.g. reminder) to the real Task Queue.
    """
    task_id = str(uuid4())
    
    task_item = TaskItem(
        task_id=task_id,
        task_name="event_tool_task",
        task_description=f"Test event: {request.name}",
        status=TaskStatus.INITIALIZED,
        payload={
            "name": request.name,
            "event_description": request.event_description,
            "trigger_time": request.trigger_time
        },
        metadata={
            "message_id": str(request.message_id),
            "task_owner": TaskOwner.EVENT_TOOL.value,
            **(request.metadata or {})
        }
    )
    
    try:
        response = await submit_task(task_item=task_item)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Using port 8003 to avoid conflict with Event Tool (8002) or Server (8000)
    uvicorn.run(app, host="0.0.0.0", port=8003)
