import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import time
import httpx
import os
from uuid import uuid4

from cortex_queue import TaskItem
from cortex_cm.pg import TaskStatus, engine, TaskOwner, EventStatus
from cortex_cm.redis.redis_client import task_redis_client, result_redis_client
from cortex_core.memory.saver import MemorySaver
from cortex_core.memory.embedding import EmbeddingModel
from cortex_cm.pg import RoleType, AIClientType
from sqlmodel import Session, select

from cortex_cm.utility.config import env

app = FastAPI(title="Cortex Task Queue Service")

# Initialize shared components
model = EmbeddingModel()
memory_saver = MemorySaver(engine=engine, model=model)

EVENT_TOOL_URL = env.EVENT_TOOL_URL

class AddTaskRequest(BaseModel):
    payload: Any
    task_name: str
    task_description: str
    metadata: Dict[str, Any]

class SubmitTaskRequest(BaseModel):
    task_id: str
    status: TaskStatus
    status_message: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "ok"}

async def update_event_status_remote(event_id: str, status: EventStatus):
    """Notify event tool about status change."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{EVENT_TOOL_URL}/update_event_status", json={
                "event_id": event_id,
                "status": status.value
            })
    except Exception as e:
        print(f"Error updating event status: {e}")

@app.post("/add_task")
async def add_task(request: AddTaskRequest):
    user_id = request.metadata.get("user_id")
    session_id = request.metadata.get("session_id")
    voice_client_response = request.metadata.get("voice_client_response")
    task_type = request.metadata.get("task_type", "query")
    
    if not user_id or not session_id:
        raise HTTPException(status_code=400, detail="Missing User ID or Session ID in task metadata")
    
    task_owner = request.metadata.get("task_owner")
    if not task_owner:
        if task_type == "query":
            task_owner = TaskOwner.VOICE_CLIENT.value
        elif task_type == "tool_execution":
            task_owner = TaskOwner.EVENT_TOOL.value
        else:
            task_owner = TaskOwner.OTHER.value

    if task_type == "tool_execution":
        # Skip message saving for tool executions (e.g. from event tool)
        # We still need a dummy message_id or handle it in add_new_task
        # For now, let's assume we need a message_id. 
        # Actually, events are linked to sessions, so we might need a dummy message or allow null message_id in Task table?
        # Checking create_tables.sql: message_id UUID NOT NULL REFERENCES messages(message_id)
        # So we MUST have a message_id. I'll create a system message if missing.
        
        with Session(engine) as session:
            # Try to find a recent message in this session to link to, or create a dummy
            from sqlalchemy import select
            from cortex_cm.pg import Message
            stmt = select(Message.message_id).where(Message.session_id == session_id).limit(1)
            msg_id = session.exec(stmt).first()
            
            if not msg_id:
                system_msg = memory_saver.save_message(
                    session_id=session_id,
                    user_id=user_id,
                    content=f"System: Task Execution - {request.task_name}",
                    role=RoleType.AI,
                    ai_client=AIClientType.CORTEX_MAIN_CLIENT
                )
                msg_id = system_msg.message_id
        
        task_obj = memory_saver.add_new_task(
            message_id=msg_id,
            tool_id=None,
            task_name=request.task_name,
            task_description=request.task_description,
            status=TaskStatus.QUEUED,
            payload=request.payload,
            status_response=None,
            task_metadata=dict(request.metadata),
            embedding=model.generate_embeddings(request.task_description),
            task_owner=task_owner
        )
        
        # If it's from event tool, update its status
        if task_owner == TaskOwner.EVENT_TOOL.value and request.payload.get("event_id"):
            await update_event_status_remote(request.payload["event_id"], EventStatus.QUEUED)

    else:
        # Default "query" route
        user_msg = memory_saver.save_message(
            session_id=session_id,
            user_id=user_id,
            content=request.payload.get("query", ""),
            role=RoleType.USER,
            ai_client=None,
            is_tool_used=False,
            tool_id=None
        )
        
        memory_saver.save_message(
            session_id=session_id,
            user_id=user_id,
            content=voice_client_response if voice_client_response else "",
            role=RoleType.AI,
            ai_client=AIClientType.VOICE_CLIENT,
            is_tool_used=False,
            tool_id=None
        )
        
        task_obj = memory_saver.add_new_task(
            message_id=user_msg.message_id,
            tool_id=None,
            task_name=request.task_name,
            task_description=request.task_description,
            status=TaskStatus.QUEUED,
            payload=request.payload,
            status_response=None,
            task_metadata=dict(request.metadata),
            embedding=model.generate_embeddings(request.task_description),
            task_owner=task_owner
        )
    
    item = TaskItem(
        task_id=task_obj.task_id,
        payload=request.payload,
        metadata=dict(request.metadata),
        task_name=request.task_name,
        task_description=request.task_description,
        status=TaskStatus.QUEUED
    )
    # Push to Redis DB 1
    task_redis_client.lpush("pending_tasks", json.dumps({
        "task_id": str(item.task_id),
        "payload": item.payload,
        "metadata": item.metadata,
        "task_name": item.task_name,
        "task_description": item.task_description,
        "status": item.status.value
    }))

    
    return {"task_id": item.task_id, "status": item.status}

@app.post("/submit_task")
async def submit_task(request: SubmitTaskRequest):
    if request.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Status must be either 'completed' or 'failed'")
    
    memory_saver.update_task(
        task_id=request.task_id,
        status=request.status,
        status_response={"result": request.status_message} if request.status == TaskStatus.COMPLETED else {"error": request.status_message}
    )
    
    result_redis_client.set(f"result:{request.task_id}", json.dumps({
        "task_id": request.task_id,
        "status": request.status.value,
        "result": request.status_message if request.status == TaskStatus.COMPLETED else None,
        "error": request.status_message if request.status == TaskStatus.FAILED else None,
        "finished_at": time.time()
    }), ttl=3600)

    # If this task belongs to EVENT_TOOL, update event status
    with Session(engine) as session:
        from cortex_cm.pg import Task
        stmt = select(Task).where(Task.task_id == request.task_id)
        task_obj = session.exec(stmt).first()
        if task_obj and task_obj.task_owner == TaskOwner.EVENT_TOOL.value:
            event_id = task_obj.payload.get("event_id")
            if event_id:
                new_status = EventStatus.DONE if request.status == TaskStatus.COMPLETED else EventStatus.FAILED
                await update_event_status_remote(event_id, new_status)
    
    return {"status": "success"}

@app.get("/get_task")
async def get_task(timeout: int = 0):
    task_data = task_redis_client.brpop("pending_tasks", timeout=timeout)
    if task_data:
        return json.loads(task_data)
    return None

@app.get("/get_result/{task_id}")
async def get_result(task_id: str):
    result_data = result_redis_client.get(f"result:{task_id}")
    if result_data:
        return json.loads(result_data)
    raise HTTPException(status_code=404, detail="Result not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
