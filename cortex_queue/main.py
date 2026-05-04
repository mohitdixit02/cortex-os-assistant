import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import time

from cortex_queue import TaskItem
from cortex_cm.pg import TaskStatus, engine
from cortex_cm.redis.redis_client import task_redis_client, result_redis_client
from cortex_core.memory.saver import MemorySaver
from cortex_core.memory.embedding import EmbeddingModel
from cortex_cm.pg import RoleType, AIClientType

app = FastAPI(title="Cortex Task Queue Service")

# Initialize shared components
model = EmbeddingModel()
memory_saver = MemorySaver(engine=engine, model=model)

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

@app.post("/add_task")
async def add_task(request: AddTaskRequest):
    user_id = request.metadata.get("user_id")
    session_id = request.metadata.get("session_id")
    voice_client_response = request.metadata.get("voice_client_response")
    
    if not user_id or not session_id:
        raise HTTPException(status_code=400, detail="Missing User ID or Session ID in task metadata")
    
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
        embedding=model.generate_embeddings(request.task_description)
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
