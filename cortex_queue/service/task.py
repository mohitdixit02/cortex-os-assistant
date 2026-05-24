import json
from fastapi import HTTPException
import time
from cortex_queue.dto import AddTaskRequest, TaskItem
from cortex_queue.service.event import add_event_tool_task_to_queue, update_submit_event_task_status
from cortex_cm.pg import TaskStatus, TaskOwner
from cortex_cm.redis.redis_client import RedisClient, RedisModeType
from cortex_cm.pg import RoleType, AIClientType
from cortex_queue.service.utility import _get_memory_saver, _get_model

from cortex_cm.utility.logger import get_logger
logger = get_logger("TASK_QUEUE")

# Redis Clients
task_redis_client = RedisClient.get_client(RedisModeType.TASK)
result_redis_client = RedisClient.get_client(RedisModeType.RESULT)

async def _add_vc_task_to_queue(request: AddTaskRequest) -> TaskItem:
    memory_saver = _get_memory_saver()
    model = _get_model()
    user_id = request.metadata.get("user_id")
    session_id = request.metadata.get("session_id")
    voice_client_response = request.metadata.get("voice_client_response")
    
    if not user_id or not session_id:
        raise HTTPException(status_code=400, detail="Missing User ID or Session ID in task metadata")
    
    query = request.payload.get("query", "")
    original_query = request.payload.get("original_query")
    is_refined_query = request.payload.get("is_refined_query", False)
    
    # - - - Self Note - - -
    # If refined, content is the original spoken text, refined_query is the AI-refined version.
    # If not refined, content is just the query.
    content_to_save = original_query if is_refined_query and original_query else query
    refined_query_to_save = query if is_refined_query else None

    user_msg = memory_saver.save_message(
        session_id=session_id,
        user_id=user_id,
        content=content_to_save,
        role=RoleType.USER,
        ai_client=None,
        is_tool_used=False,
        tool_id=None,
        is_refined_query=is_refined_query,
        refined_query=refined_query_to_save
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
    
    item.metadata["message_id"] = str(task_obj.message_id)
    
    # Push - Redis DB 1
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
    memory_saver = _get_memory_saver()
    if request.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Status must be either 'completed' or 'failed'")
    
    task_owner = request.metadata.get("task_owner")
    logger.info(f"Submitting task: {request.task_name} (ID: {request.task_id}), Owner: {task_owner}, Status: {request.status}")

    # Tools check
    tool_ids_res = None
    tool_ids = request.metadata.get("used_tools", [])
    logger.info(f"Tools used for task {request.task_id}: {tool_ids}")
    if tool_ids:
        tool_ids_res = ", ".join(tool_ids)

    memory_saver.update_task(
        task_id=request.task_id,
        tool_id=tool_ids_res,
        status=request.status,
        status_response={"result": request.result} if request.status == TaskStatus.COMPLETED else {"error": request.error}
    )
    
    if task_owner == TaskOwner.EVENT_TOOL.value:
        await update_submit_event_task_status(request)

    user_id = request.metadata.get("user_id")
    logger.info(f"Publishing result for task {request.task_id}. User ID: {user_id}")

    result_payload = json.dumps({
        "task_id": request.task_id,
        "status": request.status.value,
        "result": request.result,
        "error": request.error,
        "metadata": request.metadata,
        "task_name": request.task_name,
        "task_description": request.task_description,
        "finished_at": time.time()
    })
    
    if user_id:
        channel = f"user_stream:{user_id}"
        logger.info(f"Publishing to Redis channel: {channel}")
        result_redis_client.client.publish(channel, result_payload)
    else:
        logger.warning(f"No user_id found in metadata for task {request.task_id}. Cannot publish to user_stream.")
    
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
