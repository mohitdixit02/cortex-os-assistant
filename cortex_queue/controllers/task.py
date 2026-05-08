import json
from fastapi import HTTPException
import time

from cortex_queue.dto import TaskItem, AddTaskRequest
from cortex_cm.pg import TaskStatus, engine
from cortex_cm.redis.redis_client import task_redis_client, result_redis_client
from cortex_core.memory.saver import MemorySaver
from cortex_core.memory.embedding import EmbeddingModel
from fastapi import APIRouter
from cortex_queue.service.task import (
    add_task_to_queue,
    submit_task_to_queue
)

task_router = APIRouter()

# Initialize shared components
model = EmbeddingModel()
memory_saver = MemorySaver(engine=engine, model=model)

@task_router.post("/add_task")
async def add_task(request: AddTaskRequest):
    user_id = request.metadata.get("user_id")
    session_id = request.metadata.get("session_id")
    if not user_id or not session_id:
        raise HTTPException(status_code=400, detail="Missing User ID or Session ID in task metadata")
    return add_task_to_queue(request)

@task_router.post("/submit_task")
async def submit_task(request: TaskItem):
    if request.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Status must be either 'completed' or 'failed'")
    return submit_task_to_queue(request)

@task_router.get("/get_task")
async def get_task(timeout: int = 0):
    task_data = task_redis_client.brpop("pending_tasks", timeout=timeout)
    if task_data:
        return json.loads(task_data)
    return None

@task_router.get("/get_result/{task_id}")
async def get_result(task_id: str):
    result_data = result_redis_client.get(f"result:{task_id}")
    if result_data:
        return json.loads(result_data)
    raise HTTPException(status_code=404, detail="Result not found")

__all__ = [
    "task_router"
]
