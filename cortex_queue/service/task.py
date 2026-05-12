import json
from fastapi import HTTPException
import time
from cortex_queue.dto import AddTaskRequest, TaskItem
from cortex_queue.service.event import add_event_tool_task_to_queue, update_submit_event_task_status
from cortex_cm.pg import TaskStatus, engine, TaskOwner
from cortex_cm.redis.redis_client import RedisClient, RedisModeType
from cortex_core.memory.saver import MemorySaver
from cortex_core.memory.embedding import EmbeddingModel
from cortex_cm.pg import RoleType, AIClientType

from cortex_cm.utility.logger import get_logger
logger = get_logger("TASK_QUEUE")

# Initialize shared components
model = EmbeddingModel()
memory_saver = MemorySaver(engine=engine, model=model)

# Redis Clients
task_redis_client = RedisClient.get_client(RedisModeType.TASK)
result_redis_client = RedisClient.get_client(RedisModeType.RESULT)

async def _add_vc_task_to_queue(request: AddTaskRequest) -> TaskItem:
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
        embedding=model.generate_embeddings(request.task_description),
        task_owner=TaskOwner.VOICE_CLIENT.value
    )
    return task_obj

async def add_task_to_queue(request: AddTaskRequest):
    task_owner = request.metadata.get("task_owner")
    logger.info(f"Task owner: {task_owner}, Task name: {request.task_name}, User ID: {request.metadata.get('user_id')}, Session ID: {request.metadata.get('session_id')}")
    if task_owner == TaskOwner.EVENT_TOOL.value:
        task_obj = await add_event_tool_task_to_queue(request)
    elif task_owner == TaskOwner.VOICE_CLIENT.value:
        task_obj = await _add_vc_task_to_queue(request)
    else:
        raise HTTPException(status_code=400, detail="Invalid task owner specified in metadata")

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
        "status": item.status.value,
    }))
    
    return {"task_id": item.task_id, "status": item.status}

async def submit_task_to_queue(request: TaskItem):
    if request.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Status must be either 'completed' or 'failed'")
    
    memory_saver.update_task(
        task_id=request.task_id,
        status=request.status,
        status_response={"result": request.result} if request.status == TaskStatus.COMPLETED else {"error": request.error}
    )
    
    result_redis_client.set(f"result:{request.task_id}", json.dumps({
        "task_id": request.task_id,
        "status": request.status.value,
        "result": request.result,
        "error": request.error,
        "finished_at": time.time()
    }), ttl=3600)
    
    task_owner = request.metadata.get("task_owner")
    if task_owner == TaskOwner.EVENT_TOOL.value:
        await update_submit_event_task_status(request)
    
    return {"status": "success"}

async def get_task_from_queue(timeout: int = 0):
    task_data = task_redis_client.brpop("pending_tasks", timeout=timeout)
    if task_data:
        return json.loads(task_data)
    return None

async def get_result_from_redis(task_id: str):
    result_data = result_redis_client.get(f"result:{task_id}")
    if result_data:
        return json.loads(result_data)
    raise HTTPException(status_code=404, detail="Result not found")
