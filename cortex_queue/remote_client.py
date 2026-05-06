import httpx
import json
import asyncio
from typing import Any, Dict, Optional
from cortex_cm.pg import TaskStatus
from cortex_queue import TaskItem
from cortex_cm.utility.config import env

class RemoteTaskQueue:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or env.CORTEX_QUEUE_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def add_task(
        self, 
        payload: Any,
        task_name: str,
        task_description: str,
        **metadata: Any
        ) -> TaskItem:
        response = await self.client.post("/add_task", json={
            "payload": payload,
            "task_name": task_name,
            "task_description": task_description,
            "metadata": metadata
        })
        response.raise_for_status()
        data = response.json()
        
        return TaskItem(
            task_id=data["task_id"],
            payload=payload,
            metadata=metadata,
            task_name=task_name,
            task_description=task_description,
            status=TaskStatus(data["status"])
        )

    async def submit_task(
        self,
        task_id: str,
        status: TaskStatus,
        status_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        response = await self.client.post("/submit_task", json={
            "task_id": str(task_id),
            "status": status.value,
            "status_message": status_message
        })
        response.raise_for_status()
        return response.json()

    async def get_task_snapshot(self, task_id: str) -> Optional[TaskItem]:
        try:
            response = await self.client.get(f"/get_result/{task_id}")
            if response.status_code == 200:
                data = response.json()
                return TaskItem(
                    task_id=data["task_id"],
                    payload={}, # Payload might not be returned by result API for efficiency
                    metadata={},
                    task_name="",
                    task_description="",
                    status=TaskStatus(data["status"]),
                    result=data.get("result"),
                    error=data.get("error")
                )
        except:
            pass
        return None

    async def wait_completed_task(self, timeout: Optional[float] = None) -> Optional[TaskItem]:
        # This one is tricky because original wait_completed_task picks ANY completed task.
        # But in the new setup, cortex_server only cares about ITS OWN tasks.
        # voice/__init__.py uses get_task_snapshot, so we might not need this.
        await asyncio.sleep(timeout or 1.0)
        return None

import os

# Singleton instance for remote access
# In a real setup, we might want to replace the import of MainTaskQueue with this
