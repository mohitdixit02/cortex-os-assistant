import os
import httpx
from typing import Any, Dict, Optional
from cortex_queue.dto import TaskItem, TaskStatus
from cortex_cm.pg.enums import TaskOwner

QUEUE_URL = os.getenv("CORTEX_QUEUE_URL")
ADD_TASK_URL = f"{QUEUE_URL}/api/queue/add_task"
SAVE_MESSAGES_URL = f"{QUEUE_URL}/api/queue/save_messages"

async def save_casual_response(
    query: str,
    user_id: str | None = None,
    session_id: str | None = None,
    voice_client_response: str = "",
    original_query: str | None = None,
    is_refined_query: bool = False
):
    """
    Saves casual conversation messages to the remote Task Queue service.
    """
    payload = {
        "query": query,
        "original_query": original_query,
        "is_refined_query": is_refined_query,
    }
    metadata = {
        "user_id": user_id,
        "session_id": session_id,
        "voice_client_response": voice_client_response,
        "task_owner": TaskOwner.VOICE_CLIENT.value
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                SAVE_MESSAGES_URL,
                json={
                    "payload": payload,
                    "task_name": "casual_save",
                    "task_description": "Casual conversation save",
                    "metadata": metadata,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"[CORTEX_VOICE] Failed to save casual response to DB: {e}")
        return None

async def add_voice_task(
    query: str,
    emotion: str,
    task_name: str,
    task_description: str,
    user_id: str | None = None,
    session_id: str | None = None,
    voice_client_response: str = "",
    original_query: str | None = None,
    is_refined_query: bool = False
) -> TaskItem:
    """
    Submit a background voice task to the remote Cortex Task Queue service.
    Constructs the standard payload and metadata, returning a TaskItem.
    """
    payload = {
        "query": query,
        "original_query": original_query,
        "is_refined_query": is_refined_query,
        "emotion": emotion,
    }
    metadata = {
        "user_id": user_id,
        "session_id": session_id,
        "voice_client_response": voice_client_response,
        "task_owner": TaskOwner.VOICE_CLIENT.value
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                ADD_TASK_URL,
                json={
                    "payload": payload,
                    "task_name": task_name,
                    "task_description": task_description,
                    "metadata": metadata,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            
            return TaskItem(
                task_id=str(data.get("task_id")),
                status=TaskStatus(data.get("status", TaskStatus.QUEUED.value)),
                payload=payload,
                metadata=metadata,
                task_name=task_name,
                task_description=task_description,
                result=data.get("result"),
                error=data.get("error")
            )
    except Exception as e:
        print(f"[CORTEX_VOICE] Failed to submit background voice task: {e}")
        return TaskItem(
            task_id="failed",
            status=TaskStatus.FAILED,
            payload=payload,
            metadata=metadata,
            task_name=task_name,
            task_description=task_description,
            error=str(e)
        )
